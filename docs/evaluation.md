# Evaluation protocol

## Split discipline

The reviewed `hf/ft/fabivo_data.py` sampler reads static pairs only from `<DATA>/train/*.jpg`. Procedural samples are generated separately. Evaluation reads test, gold, holdout, rate and probe directories. Holdout/u100 are not sampler inputs. The Taichu v4 archive also records a train filename audit with no u100/open028 case found. These checks support file-level split separation; they do not prove that every historical scene is separate. Release checks found four Blender training cases with exact labels matching four Three.js test cases. The input image bytes differ, but the board geometry is the same. The release removes those four training cases and keeps evaluation unchanged. Historical results used the original splits and were not recomputed.

Select checkpoints with test structural F1. Report gold without using it to choose the checkpoint. Do not call reused gold an unseen benchmark. Repeated inspection and schedule experiments on gold can cause development bias even without gradient training on it.

Qwen3.5 m10 is a useful warning: `best_by_test` is 800. Its EMA has a higher gold score but a lower test score. Report both roles rather than using 0.9284 as the test-selected result.

## Metrics

`src/metrics.py` retains the research label scoring functions. Canonical labels begin with `box W H`, followed by `h` or `v` and four rectangle coordinates. Board scoring normalizes each label to its own box, merges touching collinear segments and uses greedy one-to-one coordinate matching. Default board tolerance is 40 in a 1000-axis frame. `f1_abs` also retains frame-scale sensitivity. Invalid predictions receive zero.

Structural scoring clusters horizontal and vertical center lines, uses order-preserving alignment and compares board endpoints. Its default alignment tolerance is 250; direct center and endpoint checks use 40 and 60. It is deliberately less sensitive to proportions. It does not prove hidden construction, support, material strength or cutting accuracy. Greedy matching is not an exact maximum matching algorithm.

For drawing models, score the production reader's output, not only the raster. An untraced candidate cannot win the medoid. `src/consensus.py` chooses the candidate with highest mean symmetric structural agreement to other valid candidates. Ties use the first candidate. Labels enter reporting after choice. Oracle scores in its console output are diagnostics only, not a deployable selection method.

## Source register

These are source paths in the private research workspace. They are not public links. Raw per-case data and labels were not copied.

| ID | Archive source | Fields checked |
|---|---|---|
| S1 | `archive/qwen21-m10/cons-1430-ema.json`; `archive/qwen21-m10-gold-two-stage-v2/results.json` | Mean of 19 gold `f1_pick` entries equals `historical_direct_struct`; historical board mean |
| S2 | `archive/qwen21-m10-steps61015-gold/results.json`; `run-manifest.json` in the same directory | `n`, seed, each arm's scores and actual steps; revisions, sigma nodes |
| S3 | `archive/qwen21-m10-gold-two-stage-v2/results.json`; `README.md` | Two-stage scores, medoid policy, runtime caveat, date |
| S4 | `archive/q35-9b-m10/summary.json` | Checkpoint gold/test scores and `best_by_test` |
| S5 | `archive/qwen21-m10/run-env.json` | Rank, optimizer steps, resolution phases, accumulation, resume and EMA settings |
| S6 | `archive/q35-9b-m10-thinking-gold-kaggle/results.json`; `run-manifest.json` | Partial CUDA OOM; two T4 GPUs; zero completed thinking rows |
| S7 | `archive/taichu/kaggle-v4-report.md`; `kaggle-v5-report.md` | Missing processor dependency; platform error with no training evidence |

| S8 | `archive/qwen21-m11-r64/selection.json`; `run-env.json` | Selected 3000-EMA, three candidates, m10 reference; rank64 and training phases |
| S9 | `archive/qwen21-m11-steps61015-gold/results.json`; `run-manifest.json` | All19 medoid and seed scores, timings, seeds0–3, actual sigma steps |
| S10 | `archive/qwen21-m11-standard28-gold/results.json`; `run-manifest.json` | Seed0 all19 means, trace failures, common17 secondary analysis |
| S11 | `archive/q35-9b-m10-thinking-gold/results.json` | Completed H100 arms, validity flags, forced stops and scores |

[The m11 study](m11-study.md) gives exact setup and limitations. The thinking figure reports the archive's `struct_f1`, which can score a partially parsed invalid-format answer; the archive's stricter `valid_struct_f1` for thinking is 0.6941 rather than 0.7911. Both keep all19 in the denominator. This archive-specific distinction does not change the canonical metric functions.

`results/m11-verified.json` includes sanitized aggregates, per-case scores and source hashes, not raw labels. `results/thinking-verified.json` contains checked thinking aggregates and its source hash. `results/verified-aggregates.json` contains only aggregate numbers and source references. `docs/code-provenance.json` records hashes of original and prepared scripts. No claim of independent reproduction is made.
