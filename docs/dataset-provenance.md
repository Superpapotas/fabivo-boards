# Dataset image decisions

The dataset release keeps original split names. Standalone third-party input photos are withheld. Documentation comparisons include original source photos at the owner’s request; they retain third-party rights and are not covered by the dataset license. [Comparison sources and credit gaps](comparison-sources.md). Labels and newly rendered board-face drawings are the owner's annotations. Their license is CC BY 4.0. Procedural image files are decoded and saved as new RGB images without EXIF or GPS metadata.

| Family | Image decision | Evidence and reason |
|---|---|---|
| blend1 | Included | `hf/ft/blender_job.py`, `blender/bgen.py`, `blender/assets.py`: procedural Cycles scenes, Poly Haven assets. Not photo blending. |
| cf1 | Included | `real/tools/build_mix8.py`: same Blender scenes without doors or legs. No web-photo composite. |
| three1 | Included | `hf/ft/pack_mix.py`, `three/gen.html`: procedural Three.js scenes and the same asset library. |
| orph7t | Included | `real/tools/build_mix8.py`: Three.js renders of orphan archetypes. |
| codex5 | Labels only | `hf/ft/pack_mix.py`: photos generated from plans. Generator terms not established here. |
| codex6 | Labels only | `hf/ft/prerender6.py`: plan-to-photo prompts. Generator terms not established here. |
| codex7s | Labels only | `real/tools/add_c7s.py`: symmetric generated plans. Generator terms not established here. |
| orph7 | Labels only | `real/tools/build_mix8.py`: Gateway/Codex generation. Generator terms not established here. |
| photoclean | Labels only | Earlier generated collection in `hf/ft/pack_mix.py`. Full per-file provenance not established. |
| sdxl | Labels only | `hf/ft/sdxl_gen.py`: RealVisXL with depth/canny ControlNet. All component terms not established here. |
| real, pl | Labels only | Web photos and pseudo-labels on web photos. Owner confirmed internet origin. |
| photo, boxed | Labels only | Benchmark reference photos. No redistribution rights established. |
| h48 | Labels only | `real/tools/add_holdout.py`: separate web-photo holdout. |
| syn3d, flat, stagger | Excluded | No static image files with these prefixes in the inspected mix10 splits. No online samples were generated. |
| open028, u100 | Excluded | Owner exclusion. No matching files in the static mix10 inventory. |

Unknown generator terms do not mean a generator forbids output sharing. We withhold those images rather than guess. No licensed third-party texture asset itself is redistributed.

Poly Haven permits use and redistribution of its CC0 assets: https://polyhaven.com/license. This does not cover gallery examples or arbitrary web images.

Source page and image URLs are recovered by exact file hashes or a unique low-error pixel match after resizing. The manifest states the method. Of 144 third-party cases, 26 source URLs were recovered and 118 remain missing. Missing URLs are explicit nulls. This is a release blocker for full photo provenance. The download script reports them. It also reports changed hashes and transformed training copies. It does not accept a mismatch or redistribute downloaded photos.

The original image bytes had no exact train/evaluation SHA-256 overlap. Four Blender training labels nevertheless matched four Three.js test labels exactly. Those four training cases are removed from the release. The filtered input images, labels and drawings have no exact train/evaluation SHA-256 overlap. This does not establish separation of near-duplicate scenes or alternate crops. Generated variants of one scene can still resemble each other. Gold was repeatedly used during development.
