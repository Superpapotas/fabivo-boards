---
license: other
license_name: qwen-research
license_link: LICENSE
base_model: Qwen/Qwen-Image-2.1
pipeline_tag: image-to-image
language: en
---
# Fabivo boards — image LoRA

**Photo → structural board drawing → editable CAD panels. Built with Qwen. Non-commercial research or evaluation only.**

This repository ships **m10 rank96, 1430-EMA**, fine-tuned from Qwen-Image 2.1. It does not ship m11 or the base weights. The drawing describes front-facing carcass boards, not measured cutting dimensions or a safety-approved plan.

![The staggered console reference, actual experimental m11 drawing and actual Fabivo CAD.](../../assets/comparisons/05-photo-staggered-console.png)

*Why a drawing? A visible-wood mask does not specify shelf ends behind books. The tested representation asks the image model to remove perspective and contents and leave solid board bars. A deterministic reader then preserves their endpoints and compiles existing Fabivo features. No matched detector comparison was run. This preview uses experimental m11, not the adapter shipped here; CAD uses default width1200/depth350/thickness18 mm and a display finish, not measured photo dimensions.*

## GPT Image 2.5 vs Fabivo m11

![Same photograph, GPT Image 2.5 drawing and compiled CAD, and m11 drawing and compiled CAD.](../../assets/gpt-comparison/photo-staggered-console.jpg)

GPT Image 2.5 uses two edits; the separately released [m11 adapter](https://huggingface.co/Superpapotas1/fabivo-boards-image-lora-m11) predicts the board drawing directly. Both actual drawings are compiled by the same Fabivo reader, without manual board repairs. These saved examples are not a controlled benchmark: prompts, resolution and budgets differ. GPT uses low quality and frontal candidate 1; m11 uses Turbo10, seed 0. The GPT console uses a saved rerun after the first provider response failed. CAD dimensions are defaults, not photo measurements. **This comparison uses m11, not the m10 weights in this repository.**

[Three paired examples and protocol](../../docs/gpt-image-comparison.md) · [Ten requested references](../../docs/demo-examples.md) · [Saved gallery; no live GPU inference](https://huggingface.co/spaces/Superpapotas1/fabivo-boards-demo)

## Released m10 evidence

| Four-seed medoid | Structural F1 | Board F1 |
|---|---:|---:|
| Test53 | 0.9235 | 0.2721 |
| Reused gold19 | 0.9225 | 0.2111 |

The medoid selects a valid drawing by agreement between seeds, without gold labels. Structural scoring tolerates some proportion changes; board scoring checks coordinates more strictly. Neither checks hidden construction. The low coordinate score is a real limitation.

A single-seed m10 study scored structural F1 0.6954/0.8497/0.9151 at six/ten/fifteen inference steps. Frontal-first Qwen processing scored 0.7720 and was rejected because the intermediate edit changed gaps and lengths. Test was used for development; gold was repeatedly inspected.

## Released m11, kept separate

m11 rank64, 3000-EMA was selected among three m11 checkpoints by test medoid F1: test/gold 0.9137/0.9141. It did not beat m10's test medoid. Rank, duration, initialization and resolution schedule changed together; no isolated rank benefit is established.

A later **gold-only** Turbo10 study scored medoid structural/board F1 **0.9393/0.2524**. Seed0 alone scored **0.9503**, not the medoid score. Mean time was6.22 seconds per drawing on L40S; the medoid needs four drawings plus tracing. Ten inference steps was not a test-selected policy. Standard28 without Turbo traced17/19 and scored0.8143 vs Turbo10 seed0 19/19 and0.9503; weights and schedule both changed.

![A lower left cabinet in the photo becomes a level-top prediction and CAD.](../../assets/comparisons/03-photo-bookcase-run.png)

*The left top should be lower. Generation flattens it; the reader faithfully compiles the mistake. Valid CAD does not mean correct reconstruction.*

[Photo-to-CAD gallery and full 19-case scores](../../docs/m11-gallery.md) · [exact study](../../docs/m11-study.md) · [code and engineering decisions](https://github.com/Superpapotas/fabivo-boards)

## My notes

I think the results could improve a lot with a cleaner dataset. Before this, I was trying a two-step pipeline with GPT Image 2.5. In my own tests, this fine-tune gives me better results. I have not run a controlled comparison between the two.

I suspect some examples in my dataset are wrong or inconsistent. I have checked some of them by hand, but there is still more manual review to do, both on the labels and on the model outputs. That is where I would put more work next. Even with those issues, I am happy with the results so far.

## Training and inference

m10 starts from an earlier rank96 adapter soup. It used1430 optimizer updates (512×1200 then768×230), AdamW LR8e-5, accumulation8 and EMA0.995 reset per phase. Exact retraining needs private sampler modules and the earlier soup. The [research notes](../../docs/experiments.md) distinguish this from m11's3000-update recipe.

Accept the base and Turbo license terms. Install the dependencies in the research repository's `src/infer_m10_steps.py`, including its pinned Diffusers revision. Authenticate with the normal Hugging Face client; do not put tokens in code. Run `python infer.py authorized-photo.jpg boards.png`. The example uses one seed and was syntax-checked, not GPU-tested for this release. It does not reproduce the four-seed score. Full evaluation also needs the private Fabivo reader.

`lora.safetensors` modifies effective parameters when loaded; it is not an upstream checkpoint. Base and Viggle Turbo weights are not included. `NOTICE` identifies the adapter modification and upstream attribution; `LICENSE` contains the full Qwen RESEARCH LICENSE AGREEMENT.

## Rights and limits

Qwen-Image and this adapter are non-commercial; commercial use needs a separate Qwen license. Source photos appear only in comparison figures, not as a raw training dataset. **Third-party references retain all original rights and are not Apache-2.0 or CC BY4.0.** [Sources and missing credits](../../docs/comparison-sources.md). Publication does not establish permission. Predictions can invent hidden shelves or remove real boards. Width, depth, hardware and joints need human decisions. [Reproduction limits](../../docs/reproduction.md), [asset terms](../../docs/figure-provenance.md).
