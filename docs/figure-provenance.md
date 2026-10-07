# Figure provenance and rights by part

## Photo comparisons

`assets/comparisons/` contains 19 figures in fixed alphabetical case order. Each uses three actual artifacts:

1. The original case reference photo, with its SHA-256 checked against the prepared dataset manifest.
2. The raw generated PNG at the Turbo10 medoid pick recorded in `cons-10.json`, not a redrawing of traced labels.
3. The actual archived `document-prod.json` rendered by Fabivo’s `renderModelObservationIsoPane` in `modelObservationSheet.ts`. This uses a depth buffer, not the old portfolio's polygon approximation. A CPU Vitest adapter calls the app renderer and emits RGBA pixels; Pillow composes those pixels with the first two images.

Only the render's material color is changed to a neutral finish. Panel positions, dimensions, counts and feature graph stay unchanged. No hidden back is added, no failed geometry is repaired. Defaults width1200 mm, depth350 mm and thickness18 mm are assigned by the reader, not measured from the reference.

The hero is the fixed `photo-asymmetric-bookcase` case to explain partial shelf ends. The failure is `photo-bookcase-run` to show the lost step between the left and right tops. These are presentation choices, not best/worst-score selection policies. Every other case remains in the gallery. The generation itself is the label-free four-seed medoid, not a manually selected seed.

[Per-case source hashes, chosen seeds and panel counts](../results/comparison-provenance.json). [Source pages, credit gaps and reference rights](comparison-sources.md).

## Separate reference-free figures

`assets/figures/checkpoint-comparison`, `m11-step-study`, `m11-standard-turbo` and `vlm-thinking` are score plots from archive JSON. Their SVGs contain text, lines and rectangles only. They contain no source photographs. `scripts/build_figures.py` verifies means, actual step counts, timing means and all-case order before rendering. The old target/traced/polygon-CAD gallery sheets have been replaced by the actual comparison figures.

These score plots are suitable for a presentation that must omit source photographs. This is not a blanket legal guarantee for model-derived assets.

## License boundaries

- Software and composition/plot code: Apache-2.0.
- Owner annotations and approved procedural render dataset files: CC BY4.0, attribution Superpapotas.
- **Original reference photographs: third-party material, all original rights retained. No license is granted by this repository.** They are not covered by the code or annotation license. Source credit identifies origin, not permission. Missing credits/URLs remain explicit. No standalone original-photo dataset is released.
- Qwen-Image2.1 and its image adapters: Qwen RESEARCH LICENSE AGREEMENT, non-commercial. **Built with Qwen.** Model-output figures do not establish unrestricted commercial rights. Commercial use needs the applicable terms and any required separate Qwen agreement.

The owner explicitly requested publication of the comparison composites. That request does not resolve third-party rights. No permission, non-infringement or legal safety is asserted. The separate `fabivo-photos` repository is not published or changed.
