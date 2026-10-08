# From a furniture photo to editable boards

**Fabivo research: teach a model to describe the carcass, then let CAD code build it.**

A product photograph shows perspective, books, doors and shadows. A furniture editor needs boards with explicit ends and connections. This project tests two ways to cross that gap: an image model draws the boards; a vision-language model writes their coordinates. The output enters Fabivo’s existing feature graph, rather than stopping at a plausible-looking image.

![The staggered console reference, the generated board drawing and its actual Fabivo CAD panels.](assets/comparisons/05-photo-staggered-console.png)

*The stepped outline and partial shelf runs carry through to CAD. The reconstruction is not exact: this case scores 0.889 structural F1. Width, depth, thickness and finish are assigned defaults, not measurements from the photo. m11, Turbo10, four-seed medoid. [m11 weights are now released separately](https://huggingface.co/Superpapotas1/fabivo-boards-image-lora-m11); the m10 release is unchanged.*

**Read in depth:** [all 19 photo comparisons](docs/m11-gallery.md) · [method and code](docs/method.md) · [training / experiments](docs/experiments.md) · [scores](docs/m11-study.md) · [reproduction](docs/reproduction.md)

## GPT Image 2.5 vs our fine-tuned model

![The same console photograph, GPT Image 2.5 board drawing and compiled CAD, and Fabivo m11 drawing and compiled CAD.](assets/gpt-comparison/photo-staggered-console.jpg)

**Two edits with GPT Image 2.5; one direct drawing with Fabivo m11.** Both real drawings pass through the same Fabivo reader. These saved examples show what each pipeline preserves or changes; they do not establish general superiority. GPT uses low quality and frontal candidate 1; m11 uses Turbo10, seed 0 and 768 pixels. The GPT console is a saved rerun after its first provider response failed. Prompts, resolution and budgets differ. CAD dimensions are defaults, not photo measurements.

[All three paired examples and exact protocol](docs/gpt-image-comparison.md) · [the ten requested references and available m11 results](docs/demo-examples.md) · [browse the saved gallery](https://huggingface.co/spaces/Superpapotas1/fabivo-boards-demo)

The gallery runs without GPU inference. Live ZeroGPU hosting was refused for this account (HTTP 402); no paid fallback was used. Six requested inputs have no new generation and are marked accordingly.

## The engineering problem

A mask tells you which pixels belong to visible wood. It does not directly say where a shelf ends behind a book, or whether two dark edges form one board. The tested hypothesis is that a generative model can remove contents and perspective and produce a useful *structural drawing*. This is a representation choice, not evidence that generation beats a trained mask detector: no matched detector baseline was run.

The drawing is deliberately simple: solid black bars, white openings, no texture. That gives the reader a fixed contract to test.

1. **Predict the front structure.** Qwen-Image 2.1 with an image LoRA outputs a board drawing. The alternative Qwen3.5-9B LoRA outputs `box W H` plus horizontal and vertical board rectangles directly.
2. **Read, do not redraw.** The raster path extracts solid bars, fills outlined boards, preserves free ends and snaps touching ends. Recognition turns those spans into ordinary Fabivo features. Compilation produces panels and their cut dimensions.
3. **Choose by agreement.** Generate four seeds, trace each valid candidate, then select the medoid: the one with greatest structural agreement with the others. Gold labels do not enter this choice. Agreement can still select a shared mistake.

The reader is part of the experiment. A reasonable-looking image with doubled outlines or broken junctions can fail conversion. A valid CAD document can also faithfully compile the *wrong* picture. Those are different failures and need different fixes. [Reader modules and scoring code](docs/method.md#code-to-inspect).

**This is not calibrated 3D reconstruction.** The reader sets width to 1200 mm, depth to 350 mm and boards to 18 mm. It estimates front proportions, not measured millimetres. Hardware, backs, fronts and hidden joints are outside the target. The cut list follows assigned geometry; it is not a measured or safety-approved cutting plan.

## Where it fails

![The photo has a lower left top; the actual prediction and CAD flatten it into one level top.](assets/comparisons/03-photo-bookcase-run.png)

*The left cabinet is shorter in the reference. The selected drawing raises it to the right cabinet’s height and aligns shelf levels. The CAD preserves that error; it does not repair it. This is a vision/topology failure, not a rendering defect. Structural F1 is 0.800 for this case: a high average does not mean every important board is right.*

All 19 cases remain visible, in alphabetical order, with actual source photos, selected drawings and compiled documents. [Small per-case figures and full score table](docs/m11-gallery.md); [static HTML case page](docs/cases.html) can be opened locally.

## What the results establish

| Four-seed medoid | Test (53) structural / board F1 | Reused gold (19) structural / board F1 |
|---|---:|---:|
| Released m10, rank96, six inference steps | 0.9235 / 0.2721 | 0.9225 / 0.2111 |
| Released m11, rank64, six inference steps | 0.9137 / 0.2762 | 0.9141 / 0.2395 |
| m11, later ten-step gold diagnostic | Not tested in this study | 0.9393 / 0.2524 |

**Structural F1 asks whether the board arrangement agrees. Board F1 is stricter about position and proportion.** Move a shelf vertically but retain its order and endpoints: structural matching can still credit it while coordinate matching rejects it. Neither score checks unseen joints or real dimensions. The gap between the two scores is a limitation, not a detail to hide.

m11 was selected by test score among three m11 checkpoints; it did not beat m10’s test medoid score. Test was used for development. Gold was reused for diagnostics. Ten inference steps was explored on gold, not selected on independent test data. The ten-step seed-0 score is **0.9503**; it is not the four-seed medoid’s **0.9393**. [Clear charts, holdout results, full precision and protocol](docs/m11-study.md).

## Decisions that did not work

| Hypothesis | Experiment and outcome | Decision / next test |
|---|---|---|
| A frontal edit first will make structure easier | Frontal → m10: gold structural F1 0.7720 vs direct 0.9225. The edit changed gaps and lengths. | Keep direct prediction as the baseline; compare any new frontal stage against it. |
| More VLM reasoning will help | Thinking: 0.7911 vs off-greedy 0.9045; 16/19 forced stops, two invalid outputs. | Disable thinking for this adapter; inspect valid-format scores too. |
| Remove Turbo and take more steps | Standard28 seed0: 17/19 traced, 0.8143; Turbo10: 19/19, 0.9503. Weights **and** schedule changed. | Do not attribute the difference to step count alone. |
| A different VLM base may help | Taichu completed only 431 steps: test/gold 0.7062/0.8551. Base license not established. | No matched-budget conclusion; no weight release. |

[Full experiment notes](docs/experiments.md) distinguish completed runs from OOM and setup failures. The next useful evaluation is fresh, source-licensed furniture with fixed checkpoint and inference policy, plus a detector baseline—not another sweep on these 19 gold cases.

## My notes

I think the results could improve a lot with a cleaner dataset. Before this, I was trying a two-step pipeline with GPT Image 2.5. In my own tests, this fine-tune gives me better results. I have not run a controlled comparison between the two.

I suspect some examples in my dataset are wrong or inconsistent. I have checked some of them by hand, but there is still more manual review to do, both on the labels and on the model outputs. That is where I would put more work next. Even with those issues, I am happy with the results so far.

## Training and reproduction

m11 used **2402 static training pairs plus online procedural samples**, with test 53, gold 19 and holdout 12. It trained on an H100 for **9855 seconds** (2 h 44 min, training only), using rank64 LoRA initialized by SVD reduction of an earlier rank96 adapter soup. The schedule was 2520 optimizer updates at 512 pixels, then 480 at 768. AdamW: learning rate `8e-5`, weight decay 0, accumulation 8; phase cosine decay, EMA `0.995`, reset at the resolution change. m10 used rank96 and 1430 updates. Rank, duration, resolution schedule and initialization changed together: this is **not a rank-only ablation**. Six/ten/fifteen *inference denoising steps* are not training updates.

The repository provides the actual [trainer](src/train_qwen21.py), [sigma schedules](src/m10_step_schedules.py), [metrics](src/metrics.py) and [medoid selection](src/consensus.py), not only result screenshots. AI tools assisted code and documentation preparation; this is not a claim of unaided implementation or authorship of Qwen base models.

```sh
python3 -m unittest discover -s src -p 'test_*.py'  # six CPU tests, no weights
```

Inference needs the licensed base, adapter, Turbo adapter for that path, dependencies and an authorized photo. Exact retraining still needs private sampler modules and the earlier soup; end-to-end scoring also needs the Fabivo reader. The included examples were not GPU-tested during this release. [Prerequisites and what cannot yet be reproduced](docs/reproduction.md).

## Assets and rights

[m11 image adapter](https://huggingface.co/Superpapotas1/fabivo-boards-image-lora-m11) · [m10 image adapter](https://huggingface.co/Superpapotas1/fabivo-boards-image-lora) · [VLM adapter](https://huggingface.co/Superpapotas1/fabivo-boards-vlm-9b) · [Annotations / approved procedural renders](https://huggingface.co/datasets/Superpapotas1/fabivo-furniture-boards)

Software: Apache-2.0. Owner annotations and approved procedural renders: CC BY 4.0. Qwen-Image 2.1 and its LoRA: **non-commercial Qwen RESEARCH LICENSE AGREEMENT. Built with Qwen.** Qwen3.5-9B and its VLM adapter: Apache-2.0. These grants are not interchangeable.

Comparison figures contain **third-party reference photographs, all original rights retained**. They are not Apache-2.0 or CC BY 4.0 assets. Sources/credits are recorded when known; missing provenance is explicit. No original-photo training dataset is released. Publication at the owner’s request does not establish permission or commercial rights. [Comparison sources](docs/comparison-sources.md) · [dataset audit](docs/dataset-provenance.md) · [release limits](NOTES.md).
