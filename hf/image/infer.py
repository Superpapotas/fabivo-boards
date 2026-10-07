"""Single-image m10 example. Non-commercial research only. GPU execution not tested here."""
import argparse
from pathlib import Path
import torch
from PIL import Image
from diffusers import QwenImage21Pipeline, FlowMatchEulerDiscreteScheduler
from huggingface_hub import hf_hub_download
from peft import LoraConfig, set_peft_model_state_dict
from safetensors.torch import load_file

BASE = 'Qwen/Qwen-Image-2.1'
TURBO = 'Viggle/Qwen-Image-2.1-viggle-turbo'
BASE_REVISION = 'd26bb61231c349cf6b7896fa83353113880e1ba3'
TURBO_REVISION = '009a44a895ef85f7e643c80fdca9543795248867'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('image')
    ap.add_argument('output')
    ap.add_argument('--seed', type=int, default=0)
    args = ap.parse_args()
    checkpoint = hf_hub_download('Superpapotas1/fabivo-boards-image-lora', 'lora.safetensors')
    prompt_file = hf_hub_download('Superpapotas1/fabivo-boards-image-lora', 'prompt.txt')
    pipe = QwenImage21Pipeline.from_pretrained(BASE, revision=BASE_REVISION, torch_dtype=torch.bfloat16).to('cuda')
    transformer = pipe.transformer
    transformer.add_adapter(LoraConfig(r=96, lora_alpha=96, lora_dropout=0.,
        target_modules=['to_q','to_k','to_v','to_out.0','img_mlp.proj','img_mlp.out','img_mlp.gate_layer']), adapter_name='m10')
    for name, parameter in transformer.named_parameters():
        if '.m10.' in name: parameter.data = parameter.data.float()
    result = set_peft_model_state_dict(transformer, load_file(checkpoint), adapter_name='m10')
    if result.unexpected_keys or any('.m10.' in key for key in result.missing_keys):
        raise RuntimeError('Adapter checkpoint mismatch')
    transformer.load_lora_adapter(TURBO, revision=TURBO_REVISION, subfolder='peft_v0.3',
        weight_name='adapter_model.safetensors', prefix=None, adapter_name='turbo')
    transformer.set_adapters(['m10','turbo'], [1.,1.])
    transformer.eval()
    pipe.scheduler = FlowMatchEulerDiscreteScheduler.from_pretrained(TURBO, revision=TURBO_REVISION, subfolder='scheduler')
    with torch.inference_mode():
        output = pipe(prompt=Path(prompt_file).read_text(), image=Image.open(args.image).convert('RGB'),
            output_resolution=768, num_inference_steps=6, sigmas=[1.,.9375,.875,.75,.5,.25],
            true_cfg_scale=1., generator=torch.Generator('cuda').manual_seed(args.seed)).images[0]
    output.save(args.output)

if __name__ == '__main__':
    main()
