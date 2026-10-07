# /// script
# requires-python = ">=3.11"
# dependencies = ["torch", "torchvision", "diffusers @ https://github.com/huggingface/diffusers/archive/c60830ee365d520ab52b110dda562dd26f7b4d7f.zip",
#                 "transformers>=4.57", "peft", "accelerate", "safetensors", "pillow", "numpy", "huggingface_hub"]
# ///
"""BF16 image-edit LoRA of Qwen-Image-2.1 (7B DiT, Qwen Research License: NON-COMMERCIAL, research only):
furniture photo -> the orthographic carcass elevation the production tracer reads.

Same Fabivo sampler / augmentation / targets / eval as train_flux2_klein.py (fabivo_data.py, synth.py), so
results are comparable by construction; only the model changes. Differences that matter:
  * The condition photo goes through the Qwen3-VL text encoder TOGETHER with the prompt (vision slots), so
    prompt embeddings depend on the (augmented) photo: they are computed per sample under no_grad, with the
    encoder resident on the GPU, instead of being cached once.
  * Latents are the 64-channel 16x VAE, RGBA in (4 ch), unpatched tokens; the sequence is [condition | target]
    with one VL slot per 2x2 condition tokens; condition and prompt tokens modulate at t=0 (causal_condition).
  * Timesteps: logit-normal u, then the SAME exponential time-shift the scheduler applies at inference for this
    token count (SIGMA_SHIFT=0 disables), so training sees the sigma distribution sampling will use.
Base weights stay bf16 (an FP8/INT8 base shifts the weights themselves: Unsloth reports LPIPS 0.112 FP8 / 0.064
INT8 against bf16) with fp32 LoRA masters under bf16 autocast. Memory: bf16 transformer + bf16 text encoder fit a
48 GB card; gradient checkpointing turns on by itself after the first CUDA OOM.
Env: as train_flux2_klein.py (DATA DATA_TAR STEPS ACCUM LR RANK RESOLUTION CKPTS SEED W_* PROMPT EVAL_SEEDS
EVAL_TEST_SEEDS SKIP_BASE SMOKE VOL_RESULTS NO_HUB_UPLOAD) + INFER_STEPS (default 28) GRAD_CKPT (0|1|auto).
Checkpoints are PEFT state dicts in safetensors (ckpt-N/lora.safetensors); loaded back with set_peft_model_state_dict.
Optional (defaults keep the historical behaviour exactly):
  LR_SCHEDULE=cosine WARMUP=N LR_MIN_FRAC=f   warmup then cosine decay to f*LR (default: constant after a 20-step warmup)
  EMA_DECAY=d        fp32 EMA of the LoRA weights (warmup min(d,(1+n)/(10+n))); every checkpoint also saves ckpt-N-ema
  RES_SCHEDULE=512x1400+768x400   progressive training resolution (resolution x optimizer steps, in order)
  EVAL_SELECT=1400-ema@512+1800-ema@768   evaluate only these checkpoint labels, each at its own resolution
"""
import os, sys, json, time, math, gc
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
import torch
import numpy as np
from PIL import Image, ImageOps

# Supply reviewed sampler/render modules locally. No private Hub repository is used.
CODE_DIR = os.environ['DATA_CODE_DIR']
sys.path.insert(0, CODE_DIR)
import synth
from fabivo_data import Sampler, eval_sets, summarize, W, apply_policy
from diffusers import QwenImage21Pipeline
from diffusers.pipelines.qwenimage21.pipeline_qwenimage21 import calculate_dimensions, calculate_shift
from peft import LoraConfig, set_peft_model_state_dict
from peft.utils import get_peft_model_state_dict
from safetensors.torch import save_file, load_file

BASE = os.environ.get("BASE_MODEL", "Qwen/Qwen-Image-2.1")
SMOKE = os.environ.get("SMOKE") == "1"
DATA = os.environ.get("DATA", "mix8"); OUTPUT = os.environ.get("OUTPUT", "qwen21")
STEPS = int(os.environ.get("SMOKE_STEPS", "6")) if SMOKE else int(os.environ.get("STEPS", "1000"))
ACCUM = int(os.environ.get("ACCUM", "4")); LR = float(os.environ.get("LR", "1e-4")); RES = int(os.environ.get("RESOLUTION", "512"))
RANK = int(os.environ.get("RANK", "16")); INFER_STEPS = int(os.environ.get("INFER_STEPS", "28"))
CKPTS = [STEPS // 2, STEPS] if SMOKE else [int(s) for s in os.environ.get("CKPTS", "500,750,1000").split(",")]
SIGMA_SHIFT = os.environ.get("SIGMA_SHIFT", "1") == "1"
OUT = f"/tmp/{OUTPUT}"; os.makedirs(OUT, exist_ok=True)
PROMPT = os.environ.get("PROMPT", "Redraw only the furniture carcass as an orthographic front elevation. Draw each structural board as a solid black bar "
                        "at its thickness on a plain white background, no perspective, no shading, no objects.")
dev, bf16 = "cuda", torch.bfloat16
log = open(f"{OUT}/log.txt", "a")
def say(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); log.write(s + "\n"); log.flush()
def upload(note):
    """Incremental copy of OUT to the volume: a file is copied only if the destination is missing or differs in size/mtime
    (re-copying every 500 MB rank-96 checkpoint after each eval directory would cost minutes of GPU time)."""
    if not os.environ.get("VOL_RESULTS"): return
    try:
        n = 0; dst_root = os.path.join(os.environ["RESULTS_ROOT"], OUTPUT)
        for dirpath, _, files in os.walk(OUT):
            rel = os.path.relpath(dirpath, OUT); ddir = os.path.join(dst_root, rel); os.makedirs(ddir, exist_ok=True)
            for fn in files:
                s, d = os.path.join(dirpath, fn), os.path.join(ddir, fn); st = os.stat(s)
                if os.path.exists(d):
                    dt = os.stat(d)
                    if dt.st_size == st.st_size and dt.st_mtime >= st.st_mtime: continue
                shutil.copy2(s, d); n += 1
        say("volume copy", note, n, "files")
    except Exception as e: say("volume copy failed", repr(e)[:200])
if os.environ.get("DATA_TAR"):
    import tarfile
    _d = "/tmp/dataroot"; os.makedirs(_d, exist_ok=True)
    with tarfile.open(os.environ["DATA_TAR"]) as _t: _t.extractall(_d)
    root = _d
else:
    root = os.environ["DATA_ROOT"]
say("diffusers", __import__("diffusers").__version__, "torch", torch.__version__, "gpu", torch.cuda.get_device_name(0))

# ---- pairs: the pipeline's own size rule (area ~RES^2, multiples of 32), so training == inference geometry ----
RES_PHASES = [(int(r), int(n)) for r, n in (x.split("x") for x in os.environ.get("RES_SCHEDULE", "").split("+") if x)]
CUR_RES = RES_PHASES[0][0] if RES_PHASES else RES
def res_at(step):
    """Training resolution of optimizer step `step` (1-based); the last phase extends past its end."""
    if not RES_PHASES: return RES
    end = 0
    for r, n in RES_PHASES:
        end += n
        if step <= end: return r
    return RES_PHASES[-1][0]
def canvas(w, h):
    cw, ch, _ = calculate_dimensions(CUR_RES * CUR_RES, w / h); return max(64, cw), max(64, ch)
def target_drawing(label, size):
    d = synth.label_drawing(label, edge=1024, pad=0.06).convert("L")
    f = min(size[0] / d.width, size[1] / d.height); d = d.resize((max(1, round(d.width * f)), max(1, round(d.height * f))), Image.LANCZOS)
    d = d.point(lambda v: 0 if v < 128 else 255)
    out = Image.new("L", size, 255); out.paste(d, ((size[0] - d.width) // 2, (size[1] - d.height) // 2))
    return out.convert("RGB")
def pair(img, label):
    size = canvas(*img.size)
    return img.convert("RGB").resize(size, Image.BICUBIC), target_drawing(label, size)

pipe = QwenImage21Pipeline.from_pretrained(BASE, torch_dtype=bf16).to(dev)
tr, vae = pipe.transformer, pipe.vae
tr.requires_grad_(False); vae.requires_grad_(False); pipe.text_encoder.requires_grad_(False)
GC = os.environ.get("GRAD_CKPT", "auto")
if GC == "1": tr.enable_gradient_checkpointing()
torch.manual_seed(int(os.environ.get("TORCH_SEED", "1")))
LORA_TARGETS = ["to_q", "to_k", "to_v", "to_out.0", "img_mlp.proj", "img_mlp.out", "img_mlp.gate_layer"]
tr.add_adapter(LoraConfig(r=RANK, lora_alpha=RANK, lora_dropout=0.0, init_lora_weights="gaussian", target_modules=LORA_TARGETS))
n_lora = sum(1 for n, _ in tr.named_modules() if n.endswith("lora_A"))
if n_lora != len(tr.transformer_blocks) * len(LORA_TARGETS): raise SystemExit(f"unexpected LoRA module count {n_lora}")
params = [p for n, p in tr.named_parameters() if p.requires_grad]
for p in params: p.data = p.data.float()
say(f"lora modules {n_lora} trainable {sum(p.numel() for p in params) / 1e6:.1f}M  mem {torch.cuda.memory_allocated() / 1e9:.1f}GB  grad_ckpt {GC}")
if os.environ.get("RESUME"):
    sd = load_file(os.path.join(os.environ["CHECKPOINT_ROOT"], os.environ["RESUME"].strip("/"), "lora.safetensors"))
    bad = set_peft_model_state_dict(tr, sd, adapter_name="default")
    if getattr(bad, "unexpected_keys", None): raise SystemExit(f"resume failed {bad.unexpected_keys[:3]}")
    say("resumed", os.environ["RESUME"], len(sd), "tensors")
# DPO_PAIRS=<private-data-root>/<x>.tar (dpo/<case>__k.{jpg,txt,lose.png}): Diffusion-DPO (Wallace et al. 2023) on flow matching. The policy
# starts from RESUME; the frozen reference is a SECOND adapter ("ref") holding the same RESUME weights. Winner = the label drawing,
# loser = a model sample the production tracer scored wrong. DPO_MIX = share of plain SFT micro-steps (anchor against drift).
DPO = os.environ.get("DPO_PAIRS")
if DPO:
    if not os.environ.get("RESUME"): raise SystemExit("DPO_PAIRS needs RESUME=<the SFT checkpoint>")
    tr.add_adapter(LoraConfig(r=RANK, lora_alpha=RANK, lora_dropout=0.0, init_lora_weights="gaussian", target_modules=LORA_TARGETS), adapter_name="ref")
    bad = set_peft_model_state_dict(tr, sd, adapter_name="ref")
    if getattr(bad, "unexpected_keys", None): raise SystemExit(f"reference adapter load failed {bad.unexpected_keys[:3]}")
    tr.set_adapter("default")
    for p in params: p.requires_grad_(True)
    say("dpo reference adapter loaded")

def enc_prompt(photo):
    """Prompt+photo through Qwen3-VL; returns (embeds, mask, image_pad_mask) with the slot count asserted."""
    with torch.no_grad():
        pe, pm, ipm = pipe.encode_prompt(prompt=PROMPT, image=[photo], device=dev)
    slots = (photo.width // 32) * (photo.height // 32)
    if int(ipm[0].sum()) != slots: raise RuntimeError(f"vision slots {int(ipm[0].sum())} != {slots} for {photo.size}")
    return pe, pm, ipm

@torch.no_grad()
def latents(img):
    x = pipe.image_processor.preprocess(img.convert("RGBA"), height=img.height, width=img.width).to(dev, bf16).unsqueeze(2)
    return pipe._encode_vae_image(image=x, generator=None)   # (1,64,1,h,w), mean/std normalised

def pack(z): return z.view(z.shape[0], z.shape[1], -1).transpose(1, 2)

def forward(xt, c, sigma, photo, enc=None):
    pe, pm, ipm = enc if enc is not None else enc_prompt(photo)
    hc, wc, ht, wt = c.shape[3], c.shape[4], xt.shape[3], xt.shape[4]
    mask = torch.cat([ipm, ipm.new_ones(ipm.shape[0], ht * wt // 4)], 1)
    with torch.autocast("cuda", dtype=bf16):
        out = tr(hidden_states=torch.cat([pack(c), pack(xt)], 1), timestep=sigma.view(1).to(bf16), encoder_hidden_states=pe, encoder_hidden_states_mask=pm,
                 img_shapes=[[(1, hc, wc), (1, ht, wt)]], img_mask=mask, return_dict=False)[0]
    return out[:, -ht * wt:]

def sample_sigma(n_tokens):
    u = torch.sigmoid(torch.randn((), device=dev))
    if not SIGMA_SHIFT: return u
    mu = calculate_shift(n_tokens, 256, 8192, 0.5, 0.9)
    return math.exp(mu) / (math.exp(mu) + (1 / u - 1))

def loss_of(photo, drawing):
    x0, c = latents(drawing), latents(photo)
    sigma = sample_sigma(x0.shape[3] * x0.shape[4])
    noise = torch.randn_like(x0); xt = (1 - sigma) * x0 + sigma * noise
    pred = forward(xt, c, sigma, photo)
    return torch.nn.functional.mse_loss(pred.float(), pack(noise - x0).float())

DPO_BETA = float(os.environ.get("DPO_BETA", "1000")); DPO_SFT = float(os.environ.get("DPO_SFT", "1.0")); DPO_MIX = float(os.environ.get("DPO_MIX", "0.5"))
def dpo_loss(photo, win, lose):
    """Same sigma and noise for winner and loser; reference errors under no_grad with the "ref" adapter active; the prompt
    (photo through Qwen3-VL) is encoded ONCE per pair. Returns (loss, accuracy, d_win, d_lose)."""
    c, xw, xl = latents(photo), latents(win), latents(lose)
    if xw.shape != xl.shape: raise RuntimeError(f"winner/loser latent shapes differ {tuple(xw.shape)} {tuple(xl.shape)}")
    enc = enc_prompt(photo); sigma = sample_sigma(xw.shape[3] * xw.shape[4]); noise = torch.randn_like(xw)
    xtw, xtl = (1 - sigma) * xw + sigma * noise, (1 - sigma) * xl + sigma * noise
    tw, tl = pack(noise - xw).float(), pack(noise - xl).float()
    mse = lambda p, t: ((p.float() - t) ** 2).mean()
    with torch.no_grad():
        tr.set_adapter("ref")
        try: rw, rl = mse(forward(xtw, c, sigma, photo, enc), tw), mse(forward(xtl, c, sigma, photo, enc), tl)
        finally: tr.set_adapter("default")
    for p in params: p.requires_grad_(True)
    pw, pl = mse(forward(xtw, c, sigma, photo, enc), tw), mse(forward(xtl, c, sigma, photo, enc), tl)
    inside = -0.5 * DPO_BETA * ((pw - rw) - (pl - rl))
    return -torch.nn.functional.logsigmoid(inside) + DPO_SFT * pw, float(inside.item() > 0), (pw - rw).item(), (pl - rl).item()

def save_lora(step):
    d = f"{OUT}/ckpt-{step}"; os.makedirs(d, exist_ok=True)
    save_file({k: v.detach().to(bf16).contiguous().cpu() for k, v in get_peft_model_state_dict(tr, adapter_name="default").items()}, f"{d}/lora.safetensors")
    return d

sample = Sampler(root, DATA, seed=int(os.environ.get("SEED", "1")))
if not sample.static: raise SystemExit(f"no static training data under {root}/{DATA}/train")
say("static train:", {k: len(v) for k, v in sample.static.items()}, "weights", W)
opt = torch.optim.AdamW(params, lr=LR, weight_decay=0.0)
LR_SCHEDULE = os.environ.get("LR_SCHEDULE", "constant"); WARMUP = int(os.environ.get("WARMUP", "20")); LR_MIN_FRAC = float(os.environ.get("LR_MIN_FRAC", "0.05"))
_START0 = int(os.environ.get("START", "0")); _TOTAL = max(1, STEPS - _START0)
LR_PHASE_PEAKS = [float(x) for x in os.environ.get("LR_PHASE_PEAKS", "").split("+") if x]
def lr_mult(i):
    if LR_SCHEDULE == "cosine_phase":   # one warmup+cosine per RES_SCHEDULE phase, phase p peaking at LR*LR_PHASE_PEAKS[p]
        s, start = _START0 + i + 1, _START0
        for p, (_, n_p) in enumerate(RES_PHASES):
            if s <= start + n_p or p == len(RES_PHASES) - 1: break
            start += n_p
        peak = LR_PHASE_PEAKS[p] if p < len(LR_PHASE_PEAKS) else 1.0
        j, warm = s - start - 1, min(WARMUP, max(1, n_p // 10))
        if j < warm: return peak * (j + 1) / warm
        t = min(1.0, (j - warm) / max(1, n_p - warm))
        return peak * (LR_MIN_FRAC + (1 - LR_MIN_FRAC) * 0.5 * (1 + math.cos(math.pi * t)))
    if i < WARMUP: return (i + 1) / WARMUP
    if LR_SCHEDULE != "cosine": return 1.0
    t = min(1.0, (i - WARMUP) / max(1, _TOTAL - WARMUP))
    return LR_MIN_FRAC + (1 - LR_MIN_FRAC) * 0.5 * (1 + math.cos(math.pi * t))
if LR_SCHEDULE not in ("constant", "cosine", "cosine_phase"): raise SystemExit(f"unknown LR_SCHEDULE {LR_SCHEDULE}")
if LR_SCHEDULE == "cosine_phase" and not RES_PHASES: raise SystemExit("cosine_phase needs RES_SCHEDULE")
sched = torch.optim.lr_scheduler.LambdaLR(opt, lr_mult)
EMA_DECAY = float(os.environ.get("EMA_DECAY", "0")); ema_n = 0
shadow = [p.detach().clone() for p in params] if EMA_DECAY > 0 else None
def ema_update():
    global ema_n
    ema_n += 1; d = min(EMA_DECAY, (1 + ema_n) / (10 + ema_n))
    torch._foreach_mul_(shadow, d); torch._foreach_add_(shadow, [p.detach() for p in params], alpha=1 - d)
def save_ema(step):
    """Swap the EMA tensors into the live parameters, save, swap back (no extra copy)."""
    for p, s in zip(params, shadow): p.data, s.data = s.data, p.data
    try: return save_lora(f"{step}-ema")
    finally:
        for p, s in zip(params, shadow): p.data, s.data = s.data, p.data
os.makedirs(f"{OUT}/pairs", exist_ok=True)
for i in range(4): a, b = pair(*sample()); a.save(f"{OUT}/pairs/{i}-in.jpg"); b.save(f"{OUT}/pairs/{i}-out.png")
say(f"steps {STEPS} accum {ACCUM} res {RES} lr {LR} rank {RANK} ckpts {CKPTS} sigma_shift {SIGMA_SHIFT} prompt: {PROMPT}")
START = int(os.environ.get("START", "0")); saved = []; ema = None; src_sum, src_n, SRC_LOG = {}, {}, []
for _rp in [x for x in os.environ.get("EVAL_CKPTS", "").split(",") if x]:   # inference-only snapshot of a finished checkpoint: STEPS=0 EVAL_CKPTS=results/<run>/ckpt-<n>
    _tail = _rp.rstrip("/").split("-")[-1]
    saved.append((int(_tail) if _tail.isdigit() else 1000, os.path.join(os.environ["CHECKPOINT_ROOT"], _rp.strip("/"))))   # non-numeric names (soups) report as step 1000
tr.train(); t0 = time.time()
from concurrent.futures import ThreadPoolExecutor
_pool = ThreadPoolExecutor(1)   # ONE worker: the sampler is not thread-safe and the draw order stays deterministic
def _make():
    img, lab = sample(); src = sample.last; ph, dr = pair(img, lab); return ph, dr, src
_next = _pool.submit(_make)
DPO_ITEMS, DPO_STAT = [], []
import random as _random
_rdpo = _random.Random(int(os.environ.get("SEED", "1")) + 777)
if DPO:
    import tarfile as _tf, glob as _glob
    _tf.open(DPO).extractall("/tmp/dpo")
    for _p in sorted(_glob.glob("/tmp/dpo/**/*.lose.png", recursive=True)):
        _b = _p[:-len(".lose.png")]; DPO_ITEMS.append((_b + ".jpg", open(_b + ".txt").read(), _p))
    if not DPO_ITEMS: raise SystemExit("no DPO pairs in " + DPO)
    say("dpo pairs", len(DPO_ITEMS), "beta", DPO_BETA, "sft", DPO_SFT, "mix(sft share)", DPO_MIX)
def dpo_triplet(photo_path, label, lose_path):
    ph, win = pair(Image.open(photo_path).convert("RGB"), apply_policy(label))
    return ph, win, Image.open(lose_path).convert("RGB").resize(ph.size, Image.BICUBIC)
def micro():
    global _next
    if DPO and _rdpo.random() >= DPO_MIX:
        loss, a, dw, dl = dpo_loss(*dpo_triplet(*DPO_ITEMS[_rdpo.randrange(len(DPO_ITEMS))]))
        (loss / ACCUM).backward(); DPO_STAT.append((a, dw, dl)); micro.src = "dpo"; return loss
    ph, dr, src = _next.result(); _next = _pool.submit(_make)
    loss = loss_of(ph, dr); (loss / ACCUM).backward(); micro.src = src; return loss
phase_t0, phase_res, phase_n = time.time(), None, 0
for step in range(START + 1, STEPS + 1):
    if res_at(step) != CUR_RES or phase_res is None:
        if phase_res is not None: say(f"[phase] res {phase_res} done: {phase_n} steps {(time.time() - phase_t0) / max(1, phase_n):.2f}s/step")
        if phase_res is not None and shadow is not None and os.environ.get("EMA_RESET_ON_PHASE") == "1":
            with torch.no_grad():
                for s_, p_ in zip(shadow, params): s_.copy_(p_.detach())
            ema_n = 0; say("[phase] EMA restarted from the live weights")
        CUR_RES = res_at(step); phase_res, phase_t0, phase_n = CUR_RES, time.time(), 0
        say(f"[phase] step {step}: training resolution {CUR_RES}")
    phase_n += 1
    for _ in range(ACCUM):
        loss, oom = None, False
        try: loss = micro()
        except torch.OutOfMemoryError:
            if GC != "auto" or tr.gradient_checkpointing: raise
            oom = True
        if oom:   # retry OUTSIDE the except block: inside it the traceback still pins the failed graph's activations
            say("CUDA OOM -> enabling gradient checkpointing"); opt.zero_grad(set_to_none=True); gc.collect(); torch.cuda.empty_cache()
            tr.enable_gradient_checkpointing(); loss = micro()
        ema = loss.item() if ema is None else 0.98 * ema + 0.02 * loss.item()
        src_sum[micro.src] = src_sum.get(micro.src, 0.0) + loss.item(); src_n[micro.src] = src_n.get(micro.src, 0) + 1
    torch.nn.utils.clip_grad_norm_(params, 1.0); opt.step(); sched.step(); opt.zero_grad(set_to_none=True)
    if shadow is not None: ema_update()
    if DPO and DPO_STAT and (step % 10 == 0 or step == 1 or SMOKE):
        say("[dpo]", json.dumps({"step": step, "acc": round(sum(s[0] for s in DPO_STAT) / len(DPO_STAT), 3), "d_win": round(sum(s[1] for s in DPO_STAT) / len(DPO_STAT), 6),
                                 "d_lose": round(sum(s[2] for s in DPO_STAT) / len(DPO_STAT), 6), "n": len(DPO_STAT)})); DPO_STAT.clear()
    if step % 10 == 0 or step == 1 or SMOKE:
        say(f"step {step} res {CUR_RES} lr {sched.get_last_lr()[0]:.2e} loss {loss.item():.4f} ema {ema:.4f} {(time.time() - phase_t0) / phase_n:.2f}s/step(phase) mem {torch.cuda.max_memory_allocated() / 1e9:.1f}GB ckpt {int(tr.gradient_checkpointing)} drawn {sample.drawn}")
    if step % 50 == 0 or step == STEPS:
        SRC_LOG.append({"step": step, **{k: round(src_sum[k] / src_n[k], 5) for k in sorted(src_sum)}, "n": dict(src_n)})
        json.dump(SRC_LOG, open(f"{OUT}/src_loss.json", "w"), indent=0); say("[srcloss]", json.dumps(SRC_LOG[-1])); src_sum, src_n = {}, {}
    if step in CKPTS:
        saved.append((step, save_lora(step)))
        if shadow is not None: saved.append((f"{step}-ema", save_ema(step)))
        upload(f"lora {step}")
if phase_res is not None and STEPS > START: say(f"[phase] res {phase_res} done: {phase_n} steps {(time.time() - phase_t0) / max(1, phase_n):.2f}s/step")
_pool.shutdown(wait=False, cancel_futures=True)
say("train done", round(time.time() - t0))

# ---- inference on test + gold with the same pipeline (KV cache on, no CFG: the model is meant to run guidance-free) ----
del opt; gc.collect(); torch.cuda.empty_cache(); tr.eval()
# TURBO=1: stack the Viggle few-step distillation LoRA (Qwen research licence, inference only) on top of ours:
# 6 steps, its scheduler config and sigma nodes, no CFG. Our adapter keeps the name "default".
SIGMAS = None
if os.environ.get("TURBO") == "1":
    from diffusers import FlowMatchEulerDiscreteScheduler
    tr.load_lora_adapter("Viggle/Qwen-Image-2.1-viggle-turbo", subfolder="peft_v0.3", weight_name="adapter_model.safetensors", prefix=None, adapter_name="turbo")
    pipe.scheduler = FlowMatchEulerDiscreteScheduler.from_pretrained("Viggle/Qwen-Image-2.1-viggle-turbo", subfolder="scheduler")
    INFER_STEPS, SIGMAS = 6, [1.0, 0.9375, 0.875, 0.75, 0.5, 0.25]
    say("turbo adapter loaded; 6 steps")
EVAL = eval_sets(root, DATA, SMOKE); results = []
if os.environ.get("EVAL_GOLD_ONLY"): EVAL = [e for e in EVAL if e[0] == "gold"]
TEST_SEEDS = [int(x) for x in os.environ["EVAL_TEST_SEEDS"].split(",")] if os.environ.get("EVAL_TEST_SEEDS") else None
plan = [(step, d, RES) for step, d in ([] if os.environ.get("SKIP_BASE") else [(0, None)]) + saved]
if os.environ.get("EVAL_SELECT"):   # label@res entries, evaluated in the given order; an unknown label is an error, not a skip
    by_label = {str(s): d for s, d in saved}; plan = []
    for item in os.environ["EVAL_SELECT"].split("+"):
        lab, r = item.split("@")
        if lab not in by_label: raise SystemExit(f"EVAL_SELECT {lab} not among saved {sorted(by_label)}")
        plan.append((lab, by_label[lab], int(r)))
for step, d, eres in plan:
    ctx = tr.disable_adapter() if d is None else None
    if d: set_peft_model_state_dict(tr, load_file(f"{d}/lora.safetensors"), adapter_name="default")
    if SIGMAS: tr.set_adapters(["default", "turbo"], [1.0, 1.0])
    if ctx: ctx.__enter__()
    # EVAL_VARIANTS=plain,flip: "flip" mirrors the photo left-right, generates, and mirrors the drawing BACK
    # (test-time augmentation; the traced flip and plain drawings are then compared/merged offline).
    variants = [v for v in os.environ.get("EVAL_VARIANTS", "plain").split("+") if v]
    assert set(variants) <= {"plain", "flip"}, variants
    for seed, variant in [(s, v) for s in [int(x) for x in os.environ.get("EVAL_SEEDS", "0").split(",")] for v in variants]:
        tag = f"{step}" if eres == RES else f"{step}-r{eres}"
        gdir = (f"gen-{tag}" if seed == 0 else f"gen-{tag}-s{seed}") + ("-flip" if variant == "flip" else "")
        rows = []; t1 = time.time(); os.makedirs(f"{OUT}/{gdir}", exist_ok=True)
        for split, src, case, p, gold in [e for e in EVAL if e[0] != "test" or (TEST_SEEDS is None or seed in TEST_SEEDS)]:
            photo = Image.open(p).convert("RGB")
            if variant == "flip": photo = ImageOps.mirror(photo)
            img = pipe(prompt=PROMPT, image=photo, output_resolution=eres, num_inference_steps=INFER_STEPS, sigmas=SIGMAS, generator=torch.Generator(dev).manual_seed(seed)).images[0]
            if variant == "flip": img = ImageOps.mirror(img)
            img.save(f"{OUT}/{gdir}/{case}.png")
            f1, aerr = synth.consistency(gold, img) if gold else (-1.0, -1.0)   # unlabeled (rate) photos: no score
            rows.append({"split": split, "source": src, "case": case, "consistency": float(f1), "aspect_err": float(aerr)})
        json.dump(rows, open(f"{OUT}/{gdir}/eval.json", "w"), indent=1)
        results.append({"step": step, "res": eres, "seed": seed, "variant": variant, "prompt": "train", "consistency": summarize(rows, "consistency"), "gen_s": round(time.time() - t1)})
        say("[eval]", json.dumps(results[-1]))
        json.dump({"checkpoints": results, "model": BASE, "infer_steps": INFER_STEPS, "note": "step 0 = Qwen-Image-2.1 without LoRA; consistency = chamfer F1 vs the PHYSICAL bars"}, open(f"{OUT}/summary.json", "w"), indent=1)
        upload(f"gen {step}")
    if ctx: ctx.__exit__(None, None, None)
say("done", round(time.time() - t0))
