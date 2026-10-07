# Reproduction notes

## Included code

The scripts are a prepared subset of `hf/ft/`, not a new training framework.

| File | Scope and preparation |
|---|---|
| `metrics.py` | Label-to-label board and structural scores unchanged. Document conversion and its private renderer import removed. |
| `consensus.py` | Original medoid and private-input reporting CLI. |
| `m10_step_schedules.py` | Original sigma schedules. |
| `test_m10_step_schedules.py` | Original CPU regression tests. |
| `test_metrics.py` | New synthetic CPU smoke checks. No private labels. |
| `train_qwen21.py` | Original training/evaluation logic; private Hub code fetch replaced by required local `DATA_CODE_DIR`; data and checkpoint roots use environment variables. |
| `infer_m10_steps.py` | Original fixed Gold19 step study; paths use environment variables and schedule import is local. |

Hashes are in `code-provenance.json`. No source files were modified. Training uses the original private `synth`, `synth3d`, `synth4`, `augment`, `fabivo_data`, `policy_fix2` modules. Supply reviewed copies through `DATA_CODE_DIR`. They are not silently replaced with a different sampler. The scripts remain runnable with these inputs, but this package is not a self-contained training release.

## Training inputs

The inline script metadata lists Python and library dependencies, including a pinned Diffusers commit. Use a suitable CUDA GPU and a separate environment. No dependency installation or GPU job was run for this preparation.

Required environment for `train_qwen21.py`:

- `DATA_CODE_DIR`: directory containing the private sampler/render modules above.
- `DATA_ROOT`: parent of `<DATA>/train`, test, gold and optional evaluation directories. Alternatively `DATA_TAR` is a trusted private archive; the historical extraction logic must not be used on untrusted archives.
- `CHECKPOINT_ROOT`: root containing the relative `RESUME` and `EVAL_CKPTS` paths.
- `RESULTS_ROOT`: private output mirror root if `VOL_RESULTS=1`.
- Original hyperparameters in `results/m10-settings.json`. These are a reference, not an automatically loaded configuration.
- `RESUME`: relative path to the earlier rank-96 soup. This is required to reproduce m10 initialization.

`OUTPUT` selects a temporary output directory. Checkpoints and generated images are sensitive artifacts. Store them outside this repository. `VOL_RESULTS` means a local filesystem copy in this prepared version, not a named cloud volume. No Hub upload code is included.

## Step study inputs

Set `OUTPUT`, `RESULTS_ROOT`, `DATA_TAR`, `CHECKPOINT`, `BASE_REVISION`, `TURBO_REVISION` and `PROMPT_B64`. `DATA_TAR` must contain exactly 19 authorized `mix10/gold/*.jpg` files. Inference extracts photos only; labels are not loaded by this script. `CHECKPOINT` is the private 1430-EMA safetensors file. `PROMPT_B64` is the UTF-8 prompt from `results/m10-settings.json`, base64 encoded.

Archived revision IDs: base `d26bb61231c349cf6b7896fa83353113880e1ba3`; Turbo `009a44a895ef85f7e643c80fdca9543795248867`.

```sh
uv run src/infer_m10_steps.py
```

The script performs 57 image generations and writes private reference copies. It is inference-only, not a metrics runner. Feed drawings to the existing Fabivo production reader in the app checkout, then convert its documents to canonical board labels. This reader is not included. Do not substitute raster-only similarity for the reported reader structural F1.

## Figure reproduction (CPU only)

Score plots: `python3 scripts/build_figures.py --archive "$ARCHIVE_ROOT" --dataset-stage "$DATASET_STAGE"`. It checks source means, actual inference iterations, timings and case order. It does not run inference.

For actual CAD pixels, use an authorized Fabivo checkout and archived medoid documents. Copy `scripts/render_fabivo.test.ts` into that checkout as `src/tmpcheck/render_fabivo.test.ts`, set `SHOWCASE_ARCHIVE` to the directory containing `cons-10.json` and `SHOWCASE_RGBA` to a local output directory, then run `npx vitest run src/tmpcheck/render_fabivo.test.ts`. Remove the temporary copied test afterward. The adapter calls the app's real depth-buffer renderer and asserts that geometry/features are unchanged by the display-material override.

Then compose the 19 comparison figures:

```sh
python3 scripts/build_showcase.py --archive "$SHOWCASE_ARCHIVE" \
  --photos "$AUTHORIZED_GOLD_PHOTOS" --rendered "$SHOWCASE_RGBA" \
  --manifest "$DATASET_STAGE/manifest.jsonl"
```

The compositor checks original reference hashes and uses the actual selected generated PNG, not a redraw. No standalone photo file is emitted. Original-photo rights remain third-party, even though the owner requested publication of the composites. These inputs are not bundled, so a fresh clone cannot regenerate the complete photo/CAD gallery without them. Reference-free metric figures are separate.

## Verification scope

CPU tests and syntax compilation can run without weights. Full benchmark reproduction needs private data, the initial soup, trained adapter and the app reader. Their release is an owner decision. No new benchmark result is claimed by this draft.
