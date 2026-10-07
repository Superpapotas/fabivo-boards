# Experiment log

Dates are stated only when an archive note confirms them. File modification dates are not treated as run dates.

## 2026-10-05: frontal-first Qwen test

Source: `archive/qwen21-m10-gold-two-stage-v2/README.md` and `results.json`.

Inference only. The first stage used base Qwen-Image 2.1 plus Turbo and seed 0, with m10 disabled. The second stage used rank-96 m10 1430-EMA at resolution 768, six sigma steps and seeds 0 to 3. A medoid selected without gold labels. Structural F1 fell from the historical direct 0.9225 to 0.7720. Objects, gaps and board lengths changed in some frontal edits. Reject this version as the current benchmark path. The direct baseline used another runtime.

## 2026-10-06: local portfolio preparation

Aggregate values were checked against archive JSON. Later private-release preparation downloaded completed checkpoints from Modal volumes using read-only file operations. No model inference, training or paid compute was started. The initial preparation kept targets private. The owner later requested public release of the research repository and three adapter/annotation repositories; the separate raw-photo repository remains private.

## Experiments without a verified calendar date

These cannot be placed in calendar order without owner confirmation. They are not assigned invented dates.

| Experiment | Verified outcome | Source |
|---|---|---|
| m10 image LoRA | Rank 96, 1430 steps, earlier soup initialization; four-seed medoid gold structural F1 0.9225 | S1, S5 |
| Turbo 6/10/15 | One seed; structural F1 0.6954/0.8497/0.9151; board F1 not monotonic | S2 |
| Qwen3.5-9B m10 | 800 chosen by test; 800-EMA historical gold 0.9284 is not that selected checkpoint | S4 |
| Thinking on two T4 GPUs | CUDA OOM; no completed thinking answer; no thinking score for this failed attempt | S6 |
| Later thinking on H100 | Off-greedy structural/board F1 0.9045/0.2018; thinking 0.7911/0.1664; off-sampled 0.9278/0.1894. Two invalid thinking outputs; 16/19 forced stops at 6144 thinking tokens | `archive/q35-9b-m10-thinking-gold/results.json`, `run-env.json` |
| Taichu on H100 | 431 completed steps; 2886 training seconds. Test structural F1 0.7062, gold 0.8551, test board F1 0.1432. Weights withheld; base license unknown | completed run `summary.json` |
| Taichu Kaggle v4 | Missing `decord` while loading processor; no verified backward pass or checkpoint | S7 |
| Taichu Kaggle v5, after v4 | Platform ERROR with empty logs; no verified training steps; cause unknown | S7 |

## m11 training recipe

The completed run log records 2402 static train pairs and weighted online procedural samples. Evaluation splits: test53, gold19, holdout12. Static train families mix procedural renders, generated photos, third-party photos and human-approved pseudo-labels; they are not 2402 independent real furniture scenes.

| Setting | m10 | m11 |
|---|---|---|
| Base | Qwen-Image 2.1 | Same base |
| LoRA rank | 96 | 64 |
| Initialization | Earlier rank96 adapter soup | Rank96 soup reduced to rank64 by SVD |
| Optimizer updates | 1430 | 3000 |
| Pixel schedule | 512×1200 updates + 768×230 | 512×2520 + 768×480 |
| Optimizer | AdamW, LR8e-5, weight decay0 | Same |
| Accumulation / seed | 8 / 3 | 8 / 3 |
| LR / EMA | Phase cosine; phase peaks1/0.5, warmup50, floor0.05; EMA0.995 reset per phase | Same settings |
| Recorded m11 training time | — | 9855 seconds on H100 (2h44m); excludes evaluation |

Base BF16; trainable LoRA parameters FP32. Loss is flow matching. Attention projections and image MLP projections are adapted. Static source probabilities and online samplers are part of the recipe, not interchangeable with uniform sampling. Exact source weights are preserved in the archived run environment and the prepared trainer settings. Initialization and private sampler code are not released.

Rank, duration, initialization and resolution schedule changed together. m11 is not a rank-only experiment. Denoising steps6/10/15 at inference are separate from optimizer updates1430/3000. Four-seed medoid inference adds four generations plus tracing and selection.

## m11 completed archive studies

m11 rank64 completed 3000 steps with `512x2520+768x480`. Test selected 3000-EMA among three m11 candidates: test/gold medoid structural F1 0.9137/0.9141. The historical m10 reference remains 0.9235/0.9225. This is not a rank-only comparison. No m11 weights replace the released m10 adapter.

The later four-seed gold step study scored medoid structural F1 0.9214/0.9393/0.9359 at 6/10/15 actual sigma steps. The standard28 comparison uses seed0 only and includes failures in its all19 average. See [exact setup](m11-study.md), [all19 gallery](m11-gallery.md) and [figure provenance](figure-provenance.md). Run dates are not inferred from file timestamps.

The completed thinking archive also reports `valid_struct_f1`: 0.6941 for thinking, versus its partially parsed `struct_f1` 0.7911. The figure reports the latter and states the stricter alternative in the card. This distinction matters when counting invalid-format answers.

Source IDs refer to [evaluation notes](evaluation.md#source-register). GPU allocation or a submitted configuration is not evidence of training.
