# /// script
# requires-python = ">=3.11"
# dependencies = ["torch", "torchvision", "diffusers @ https://github.com/huggingface/diffusers/archive/c60830ee365d520ab52b110dda562dd26f7b4d7f.zip", "transformers>=4.57", "peft", "accelerate", "safetensors", "pillow", "numpy", "huggingface_hub"]
# ///
"""INFERENCE ONLY: matched m10+Turbo at 6,10,15 REAL steps, all 19 gold photos.
No training, targets, gold-driven choice, first-stage edit, or human ratings.
Only the node count changes. Required low-noise nodes remain fixed.
"""
import os,time,json,tarfile,shutil,base64,tempfile,sys
from pathlib import Path
os.environ.setdefault('PYTORCH_CUDA_ALLOC_CONF','expandable_segments:True')
import torch
from PIL import Image
from diffusers import QwenImage21Pipeline,FlowMatchEulerDiscreteScheduler
from peft import LoraConfig,set_peft_model_state_dict
from safetensors.torch import load_file
from m10_step_schedules import turbo_sigmas
RUN=os.environ['OUTPUT'];OUT=Path('/tmp')/RUN;OUT.mkdir(exist_ok=True);DEST=Path(os.environ['RESULTS_ROOT'])/RUN
START=time.monotonic();LIMIT=int(os.environ.get('SOFT_LIMIT_SECONDS','1050'));LOG=open(OUT/'log.txt','a')
def say(*xs):
 s=' '.join(map(str,xs));print(s,flush=True);LOG.write(s+'\n');LOG.flush()
def sync():
 DEST.mkdir(parents=True,exist_ok=True)
 for p in OUT.rglob('*'):
  if p.is_file():
   d=DEST/p.relative_to(OUT);d.parent.mkdir(parents=True,exist_ok=True)
   if not d.exists() or d.stat().st_size!=p.stat().st_size or d.stat().st_mtime<p.stat().st_mtime:shutil.copy2(p,d)
PHOTO=Path('/tmp/m10-step-photos');PHOTO.mkdir(exist_ok=True)
with tarfile.open(os.environ['DATA_TAR']) as t:
 m=[x for x in t.getmembers() if x.isfile() and x.name.startswith('mix10/gold/') and x.name.endswith('.jpg')]
 if len(m)!=19:raise RuntimeError('Expected all 19 gold photos, no labels')
 for x in m:t.extract(x,PHOTO,filter='data')
photos=sorted((PHOTO/'mix10/gold').glob('*.jpg'))
BASE='Qwen/Qwen-Image-2.1';TURBO='Viggle/Qwen-Image-2.1-viggle-turbo';RES=768;SEED=0;COUNTS=[6,10,15]
CKPT=Path(os.environ['CHECKPOINT'])
if not CKPT.is_file():raise FileNotFoundError(CKPT)
PROMPT=base64.b64decode(os.environ['PROMPT_B64']).decode()
say('INFERENCE ONLY','all19','steps',COUNTS,'seed',SEED,'resolution',RES)
pipe=QwenImage21Pipeline.from_pretrained(BASE,revision=os.environ['BASE_REVISION'],torch_dtype=torch.bfloat16).to('cuda')
pipe.set_progress_bar_config(disable=True);tr=pipe.transformer
tr.add_adapter(LoraConfig(r=96,lora_alpha=96,lora_dropout=0.,target_modules=['to_q','to_k','to_v','to_out.0','img_mlp.proj','img_mlp.out','img_mlp.gate_layer']),adapter_name='m10')
for name,p in tr.named_parameters():
 if '.m10.' in name:p.data=p.data.float()
r=set_peft_model_state_dict(tr,load_file(str(CKPT)),adapter_name='m10')
if r.unexpected_keys or any('.m10.' in k for k in r.missing_keys):raise RuntimeError('m10 adapter checkpoint mismatch')
tr.load_lora_adapter(TURBO,revision=os.environ['TURBO_REVISION'],subfolder='peft_v0.3',weight_name='adapter_model.safetensors',prefix=None,adapter_name='turbo')
tr.set_adapters(['m10','turbo'],[1.,1.]);tr.eval();tr.requires_grad_(False);pipe.text_encoder.requires_grad_(False);pipe.vae.requires_grad_(False)
manifest={'mode':'inference_only','arms':COUNTS,'photo_count':19,'seed':SEED,'resolution':RES,'checkpoint':str(CKPT),'model':BASE,
 'base_revision':os.environ['BASE_REVISION'],'turbo_revision':os.environ['TURBO_REVISION'],'adapters':['m10','turbo'],'weights':[1.,1.],
 'prompt':PROMPT,'samplers':{str(n):turbo_sigmas(n) for n in COUNTS},'scheduler':'Viggle shipped config (shift_terminal=None)',
 'warning':'10/15 steps are experimental high-noise refinement; not a uniform schedule or the separate 9-step base-tail mode. One fixed seed, no medoid or gold selection.',
 'torch':torch.__version__,'diffusers':__import__('diffusers').__version__,'dtype':'BF16 base, FP32 m10 masters','completed':[]}
def persist():
 (OUT/'run-manifest.json').write_text(json.dumps(manifest,indent=1));sync()
(OUT/'reference').mkdir(exist_ok=True)
for p in photos:shutil.copyfile(p,OUT/'reference'/p.name)
persist()
for count in COUNTS:
 folder=OUT/f'gen-turbo{count}';folder.mkdir(exist_ok=True)
 # A fresh scheduler removes state from the preceding arm. Only the raw nodes differ.
 pipe.scheduler=FlowMatchEulerDiscreteScheduler.from_pretrained(TURBO,revision=os.environ['TURBO_REVISION'],subfolder='scheduler')
 for i,p in enumerate(photos,1):
  if time.monotonic()-START>LIMIT:persist();raise TimeoutError('Soft time cap; partial output is not a completed step comparison')
  actual=[]
  def on_step(_pipe,index,_t,kw):actual.append(index);return kw
  t0=time.monotonic()
  with torch.inference_mode():
   im=pipe(prompt=PROMPT,image=Image.open(p).convert('RGB'),output_resolution=RES,num_inference_steps=count,
    sigmas=turbo_sigmas(count),true_cfg_scale=1.,callback_on_step_end=on_step,
    generator=torch.Generator('cuda').manual_seed(SEED)).images[0]
  if actual!=list(range(count)):raise RuntimeError(f'Expected {count} real denoising steps; observed {actual}')
  im.save(folder/f'{p.stem}.png');manifest['completed'].append({'case':p.stem,'steps':count,'actual_steps':len(actual),'seconds':round(time.monotonic()-t0,3)})
  persist();say('GENERATED',count,i,'/19',p.stem,manifest['completed'][-1]['seconds'],'s')
if len(manifest['completed'])!=57:raise RuntimeError('Incomplete 6/10/15 inference')
manifest['status']='completed';manifest['total_s']=round(time.monotonic()-START,2);persist();say('COMPLETE','57 images','all19 x6/10/15',manifest['total_s'],'s')
