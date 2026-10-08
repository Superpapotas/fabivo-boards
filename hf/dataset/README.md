---
license: cc-by-4.0
language: en
task_categories:
- image-to-text
- image-to-image
---
# Fabivo furniture boards

Front-view board annotations for reconstructing furniture from photographs. Each example pairs a board-coordinate list with a black-and-white drawing. Procedural furniture renders provide a subset of the input images; the original-photo training set is not included.

[Code, experiments and photo-to-CAD examples](https://github.com/Superpapotas/fabivo-boards)

## GPT Image 2.5 vs the fine-tuned image model

![Same source photograph, GPT Image 2.5 board drawing and CAD, and Fabivo m11 drawing and CAD.](../../assets/gpt-comparison/photo-staggered-console.jpg)

These are **actual saved model predictions, not dataset labels**. GPT Image 2.5 uses a frontal edit followed by a drawing edit; m11 predicts a drawing directly. The same Fabivo reader compiles both, without manual board repairs. This is an illustrative comparison, not a controlled benchmark: prompts, resolution and budgets differ. GPT uses low quality and candidate 1; m11 uses Turbo10 and seed 0. The GPT console uses a saved rerun after the first provider response failed. CAD dimensions are defaults. Third-party reference photos are excluded from this dataset's CC BY 4.0 grant.

[Three paired cases and protocol](../../docs/gpt-image-comparison.md) · [Ten requested references](../../docs/demo-examples.md) · [m11 weights](https://huggingface.co/Superpapotas1/fabivo-boards-image-lora-m11) · [Saved gallery; no live inference](https://huggingface.co/spaces/Superpapotas1/fabivo-boards-demo)

## Contents and format

The release contains 2,486 board-list labels, 2,486 board drawings and 1,243 procedural input renders. The other 1,243 input images are not included. Drawings are new black-on-white renders of our board-face annotations, not copies of source photographs.

Each label starts with `box W H`. The longer side is normalized to 1000. Each board row is `h x0 y0 x1 y1` or `v x0 y0 x1 y1`. Coordinates describe front-face rectangles. The origin is upper left, with y increasing downward. Vertical rows precede horizontal rows. Labels do not specify depth, measured cut sizes, joints or hidden construction.

`manifest.jsonl` records case, family, split, exact used-image SHA-256, image size, paths and source page/image URLs where recovered. Null URLs mean not recovered. `source_file_sha256`, when present, checks an original download rather than a resized training copy. `audit.json` records decisions and counts. `PROVENANCE.md` lists source scripts and reasons.

## Annotation and reader examples

![Staggered console reference, actual experimental m11 selected drawing and actual compiled Fabivo CAD.](../../assets/comparisons/05-photo-staggered-console.png)

The stepped outline and partial shelf runs carry through to CAD, but the reconstruction is not exact (structural F1 0.889). The CAD comes from the archived reader document, with no repaired geometry. Width 1200 mm, depth 350 mm, thickness 18 mm and finish are assigned defaults, not recovered measurements.

[Photo-to-CAD gallery and full 19-case score table](../../docs/m11-gallery.md). Two visual examples were removed at the owner's request; the benchmark is unchanged. Prediction images are experimental m11, not ground truth or VLM output. **Reference photos are third-party material, all original rights retained; they are NOT CC BY 4.0 or Apache-2.0.** [Source pages and missing credits](../../docs/comparison-sources.md), [figure provenance](../../docs/figure-provenance.md). This documentation update does not change training/evaluation files or splits.

## Split and family counts

| Family | Train | Test | Gold | Holdout | Input images |
|---|---:|---:|---:|---:|---|
| blend1 | 853 | 15 | 0 | 0 | Included |
| cf1 | 193 | 0 | 0 | 0 | Included |
| three1 | 48 | 8 | 0 | 0 | Included |
| orph7t | 126 | 0 | 0 | 0 | Included |
| codex5 | 550 | 30 | 0 | 0 | Withheld |
| codex6 | 208 | 0 | 0 | 0 | Withheld |
| codex7s | 285 | 0 | 0 | 0 | Withheld |
| orph7 | 16 | 0 | 0 | 0 | Withheld |
| photoclean | 8 | 0 | 0 | 0 | Withheld |
| sdxl | 2 | 0 | 0 | 0 | Withheld |
| real | 59 | 0 | 13 | 0 | Withheld |
| pl | 54 | 0 | 0 | 0 | Withheld |
| photo | 0 | 0 | 5 | 0 | Withheld |
| boxed | 0 | 0 | 1 | 0 | Withheld |
| h48 | 0 | 0 | 0 | 12 | Withheld |
| Total | 2402 | 53 | 19 | 12 | 1243 included |

syn3d, flat and stagger have no static files in these mix10 splits. Online procedural samples are not included. open028 and u100 are excluded from this release. No matching static files were found. Original split names are preserved. No exact input-image SHA-256 occurs in both train and evaluation. This does not rule out near-duplicate scenes or crops.

## Licensing by part

Our labels, board drawings and included procedural renders: CC BY 4.0, attribution Superpapotas, Fabivo furniture boards. Credit the dataset, link its license, and state changes. The included render scenes use Poly Haven CC0 assets. No standalone web-photo training files or texture assets are redistributed. Comparison composites contain third-party references with separate rights labels. The license does not grant rights to third-party photos.

`download_verify.py`: Apache-2.0. License texts are separate. Generated-photo families are withheld because full generator terms or per-file provenance were not established. This is not a claim that output sharing is forbidden.

## Download verification

Run `python download_verify.py manifest.jsonl authorized-local-photos`. Obtain permission for photo use first. The script fetches only original URLs. It checks SHA-256, reports missing URLs, unavailable files and changed files, and does not store mismatches. A verified original can differ from the resized/re-encoded training copy; the script states that difference. It cannot reconstruct missing source URLs or certify image rights.

## Limits

Gold is a repeatedly inspected 19-case development set. Test was used for checkpoint selection. Pseudo-labels are human-approved model proposals, not measured construction drawings. Hidden shelves may be guessed. Board proportions can be wrong even with a high structural score. Generator families and archetypes are not an unbiased furniture sample. This dataset is not a construction-safety benchmark.
