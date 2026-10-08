---
language:
- en
license: other
license_name: qwen-research
license_link: LICENSE
base_model: Qwen/Qwen-Image-2.1
library_name: diffusers
pipeline_tag: image-to-image
tags:
- lora
- furniture
- research
- non-commercial
---
# Fabivo boards image LoRA m11

**Built with Qwen. Research and evaluation only, non-commercial.**

This is the rank64 EMA adapter from `qwen21-m11-r64/ckpt-3000-ema`. It redraws a furniture carcass as an orthographic front elevation: solid black boards and white openings. It is an adapter, not a complete model. It does not infer real width, depth, thickness, hardware, hidden joints or safe construction.

[Research and code](https://github.com/Superpapotas/fabivo-boards) · [Released m10](https://huggingface.co/Superpapotas1/fabivo-boards-image-lora) · [Annotations / approved procedural renders](https://huggingface.co/datasets/Superpapotas1/fabivo-furniture-boards) · [Fabivo](https://fabivo.com)

## GPT Image 2.5 vs Fabivo m11

![The same photo, GPT Image 2.5 drawing and compiled CAD, and this m11 adapter's drawing and compiled CAD.](../../assets/gpt-comparison/photo-staggered-console.jpg)

**GPT Image 2.5: frontal edit → board drawing. m11: photo → board drawing.** Both actual drawings are compiled by the same Fabivo reader with no repaired boards. Three saved examples compare these different pipelines, not matched inference budgets or independent unseen accuracy. GPT uses low quality and frontal candidate 1; m11 uses Turbo10, seed 0, 768 pixels. The GPT console uses a saved rerun after its first provider response failed. Dimensions are assigned CAD defaults, not recovered measurements.

[All three paired examples and protocol](../../docs/gpt-image-comparison.md) · [Ten requested references and available results](../../docs/demo-examples.md) · [Browse the saved gallery](https://huggingface.co/spaces/Superpapotas1/fabivo-boards-demo)

The gallery is static and has no live inference. ZeroGPU hosting was denied for this account; no paid fallback or GPU quota was used. Six requested inputs remain ungenerated.

## Exact weights and training

- Base: `Qwen/Qwen-Image-2.1`, revision `d26bb61231c349cf6b7896fa83353113880e1ba3`.
- Turbo: `Viggle/Qwen-Image-2.1-viggle-turbo`, revision `009a44a895ef85f7e643c80fdca9543795248867`, `peft_v0.3/adapter_model.safetensors`.
- Adapter rank/alpha: **64/64**, dropout 0. Target modules: `to_q`, `to_k`, `to_v`, `to_out.0`, `img_mlp.proj`, `img_mlp.out`, `img_mlp.gate_layer`.
- Both adapters have weight **1.0**. Base BF16; m11 adapter masters FP32. Keep this load contract; do not assume the raw checkpoint is a Diffusers pipeline.
- 3000 optimizer updates: 2520 at 512 pixels, 480 at 768. Initialized by SVD reduction of an earlier rank96 adapter soup. EMA decay `0.995`, reset at the resolution phase change.
- 2402 static pairs plus online procedural samples. AdamW, learning rate `8e-5`, weight decay 0, accumulation 8, phase cosine decay.
- Checkpoint selected using the development test among three m11 checkpoints. Rank, initialization, training duration and resolution changed together. This is not a rank-only ablation.

`lora.safetensors`: 335,598,896 bytes; 448 tensors. All LoRA A/B shapes were checked for rank64.

SHA256: `776a9b8c897337449e65441866123b3a58e6f1ee12515b589e09e705c96e4b40`

## Results and limits

Six-step, four-seed medoid development test structural F1: **m11 0.9137**, **m10 0.9235**. m11 is not universally better. Later reused-gold Turbo10 diagnostics: medoid **0.9393**, seed0 **0.9503**. These are different selection policies. Gold was reused for development; it is not independent evidence of generalization. A single-seed demo does not run medoid selection.

The deterministic Fabivo reader can compile a wrong drawing faithfully. Width/depth/thickness are user measurements or assigned defaults (1200/350/18 mm), not dimensions measured from an image. Inspect every board and connection before further use. The output is not a safety-approved cutting plan.

## Exact inference example

Use the included `infer.py`. It contains the fixed carcass prompt, exact adapter targets, revision pins and sigma schedules. Turbo10 means ten real denoising steps, seed0, 768 pixels, one candidate.

```sh
python3 -m pip install torch pillow accelerate peft safetensors huggingface_hub 'transformers>=4.57' 'diffusers @ https://github.com/huggingface/diffusers/archive/c60830ee365d520ab52b110dda562dd26f7b4d7f.zip'
python3 infer.py authorized-photo.jpg boards.png --steps 10
sha256sum lora.safetensors
```

The code needs compatible CUDA hardware and sufficient model memory. No external paid API is needed. This release was verified by public download and hash, not by a new GPU run. Free ZeroGPU hosting was requested for `Superpapotas1/fabivo-boards-demo`, but the server refused creation with HTTP 402 and an account-age/PRO/community-grant message. The linked gallery shows saved results only; there is **no verified live GPU inference**. No paid fallback was used.

## License, changes and rights

The exact base **Qwen RESEARCH LICENSE AGREEMENT** is included in `LICENSE`; read it before use. Qwen is licensed under the Qwen RESEARCH LICENSE AGREEMENT, Copyright (c) 2026 Hangzhou Tongyi Laboratory Technology Co., Ltd. All Rights Reserved.

Modification notice: Fabivo trained and EMA-averaged this rank64 LoRA for carcass drawings, using an SVD-reduced adapter soup initialization. `lora.safetensors` is a modified derivative adapter; no base model weights are redistributed. `infer.py` adds the fixed prompt and inference contract. See `NOTICE` for attributions.

No raw photo training dataset is released here. Third-party internet reference photographs retain all original rights; no CC BY grant is made for them. Owner annotations and approved procedural renders have separate terms in the dataset repository. User photos must be authorized. The base-model license, code license and image rights are not interchangeable.
