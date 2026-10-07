"""Minimal inference example. Requires a CUDA GPU and current Transformers/PEFT."""
import argparse
from PIL import Image
import torch
from transformers import AutoProcessor, Qwen3_5ForConditionalGeneration
from peft import PeftModel

PROMPT = (
    "Draw the front elevation of this furniture as a board list. First line: `box W H`, the furniture's "
    "front size with its longer side = 1000. Then one board per line: `h` (horizontal) or `v` (vertical) "
    "and its front face x0 y0 x1 y1 in that frame (y down). Vertical boards left to right, then horizontal "
    "boards top to bottom. Output only the list."
)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('image')
    ap.add_argument('--adapter', default='Superpapotas1/fabivo-boards-vlm-9b')
    args = ap.parse_args()
    base = 'Qwen/Qwen3.5-9B'
    processor = AutoProcessor.from_pretrained(base)
    model = Qwen3_5ForConditionalGeneration.from_pretrained(base, dtype=torch.bfloat16, device_map='auto')
    model = PeftModel.from_pretrained(model, args.adapter).eval()
    image = Image.open(args.image).convert('RGB')
    image.thumbnail((640, 640))
    messages = [{'role': 'user', 'content': [{'type': 'image', 'image': image}, {'type': 'text', 'text': PROMPT}]}]
    inputs = processor.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
                                          enable_thinking=False, return_dict=True, return_tensors='pt').to(model.device)
    with torch.inference_mode():
        output = model.generate(**inputs, max_new_tokens=2048, do_sample=False)
    print(processor.decode(output[0, inputs['input_ids'].shape[-1]:], skip_special_tokens=True))

if __name__ == '__main__':
    main()
