# Release checks and limits

## Content checks for the photo-to-CAD presentation

- Six CPU unit tests pass. No GPU inference, training, paid compute or Klein job was started or changed.
- `build_figures.py` verifies all19 study means, timings,228 actual denoising iteration counts, sorted case order and the19 selected documents. Medoid picks also match `cons-10.json`.
- A CPU Vitest adapter calls Fabivo’s actual `renderModelObservationIsoPane` on all19 archived selected documents. The renderer test passes. Only material color changes for display; geometry/features are unchanged.
- `build_showcase.py` verifies all19 original-photo hashes against the prepared manifest. The figures use raw selected generated PNGs, not regenerated or corrected board drawings. Each reference is separately labeled third-party; case IDs, source-page records and missing-credit statuses are available.
- The hero and failure figures were opened. The README and static HTML gallery were rendered in a local browser; screenshots were opened and checked. Browser errors/console were empty. The failure shows the lost stepped top, not a repaired output.
- Credential-pattern/forbidden-filename scan and Python parsing pass. The scan prints no matched secrets and does not prove absence of every possible secret encoding. No auth files, raw original-photo dataset or standalone reference photos are included.
- The old manually projected CAD sheets are replaced. Reference-free score charts remain separate from third-party-photo composites.

## Remote update boundary

Only the existing research GitHub repository and three existing HF release repositories are authorized for publication. The unrelated raw-photo repository stays private. Normal Git commits/pushes only; no force push or history rewrite. Documentation upload uses an explicit allowlist; adapter weights, labels and dataset contents must retain their existing file identities. Uploaded README/assets must be downloaded and compared by SHA-256, and anonymous access/visibility must be checked after publication. The documentation uploader never changes visibility; already-public uploads require an explicit flag.

## Unresolved limits after publication

Photo provenance remains incomplete:118 of144 third-party dataset cases lack source URLs. Source links are not redistribution licenses. The owner requested publication of comparison composites, but permission and third-party rights are not established or guaranteed. Original-photo training files and unverified generated-photo input families remain withheld.

Exact reproduction needs private samplers, data, the initial soup and the Fabivo reader. Historical scores were not recomputed after four known train/test scene-label overlaps were removed from the prepared dataset. Reused gold and test development limit generalization claims. Commercial use of Qwen-Image derivatives needs the applicable Qwen license and any required separate agreement. No measured-geometry or construction-safety claim is made.
