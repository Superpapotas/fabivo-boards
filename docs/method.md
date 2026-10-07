# Method notes

## Targets and model paths

The target is a carcass elevation, not a photorealistic image. The m10 prompt preserves stepped tops, partial shelves and dividers. It keeps openings white even behind opaque fronts and keeps shelves visible through glass. It omits legs, plinths, backs, worktops, fronts, handles and contents.

Qwen-Image training uses flow-matching loss with BF16 base weights and FP32 LoRA parameters. The condition photo is encoded with the prompt. LoRA targets attention projections and image MLP projections. m10 starts from an earlier rank-96 adapter soup. Its resolution phases are 1200 steps at 512 and 230 at 768. Phase cosine scheduling uses peaks 1 and 0.5, a 50-step warmup and minimum fraction 0.05. EMA decay is 0.995 with a phase reset. These are recorded settings, not an assertion that the released code alone can reconstruct the withheld initialization.

Turbo inference combines two adapters. The six raw sigma nodes are 1, 0.9375, 0.875, 0.75, 0.5 and 0.25. The longer schedules add high-noise nodes while preserving the last four. Callbacks verify actual denoising iterations. Passing six sigma nodes with a larger nominal count would still perform six steps.

The VLM alternative emits a text board list directly. It avoids raster decoding but can still invent or omit boards. The private release includes the historical m10 800-EMA adapter and a separately filtered dataset. Missing photo source URLs remain an owner review item.

## Why this representation

The input has furniture, contents, perspective and shadows in the same pixels. A visible-surface mask alone does not specify the intended carcass behind contents. A generative model was tested to remove that clutter and express an orthographic board arrangement. No matched mask-detector baseline was run, so this is a hypothesis under test, not a detector comparison result.

Solid bars are an interface between prediction and code. Their direction, thickness and endpoints carry enough structure for deterministic reading. Outlined boards, doubled edges or small gaps can make a plausible image unreadable. That is why the evaluation traces the output and scores the compiled geometry, not raster similarity alone.

The direct VLM route avoids that raster interface by emitting canonical rectangles. It trades raster ambiguity for parsing errors and possible invented coordinates. Both routes can omit or invent structure. Neither calibrates dimensions from a camera.

## Code to inspect

- [metrics.py](../src/metrics.py): merges collinear segments, matches normalized board rectangles and separately aligns structural line order/endpoints. This separation exposes topology/coordinate disagreement.
- [consensus.py](../src/consensus.py): chooses one valid candidate by pairwise structural agreement; labels enter only later reporting. It never averages pictures or picks the best gold score.
- [train_qwen21.py](../src/train_qwen21.py): weighted source sampling, phase resolution/LR schedules, LoRA training and EMA checkpoints. Private sampler modules are required, not replaced with different code.
- [m10_step_schedules.py](../src/m10_step_schedules.py): actual sigma-node schedules with CPU tests. A nominal step argument alone does not prove how many iterations executed.
- [build_showcase.py](../scripts/build_showcase.py): source-photo hash checks and literal photo/drawing/CAD composition. It does not repair geometry.

## App context

Fabivo is a furniture CAD and cut-list web app. Its photo pipeline performs a frontal edit, lets a person choose a candidate, performs a board-line edit, then reads the drawing deterministically. That app workflow is separate from the direct m10 research path. The rejected two-stage experiment used Qwen for the frontal stage.

Relevant app-relative paths, provided as a navigation map rather than copied source:

- `src/features/modeler/photoFurniturePipeline.ts`: raster reading, recognition and feature compilation.
- `src/features/modeler/photoBoardTrace.ts`: solid-bar extraction, outline filling and endpoint handling.
- `src/features/modeler/modelerSketchDrafts.ts`: recognition-to-draft conversion.
- `src/features/modeler/modelerFurnitureSketchCompiler.ts`: existing feature-graph compilation.
- `src/benchmark/agent/approvedVisionBenchmark.test.ts`: separate agent image benchmark.
- `src/benchmark/agent/photoGoldMetrics.ts`: separate app document comparison.

The tracer keeps free board ends and snaps touching ends to perpendicular bars. Literal recognition seeks to preserve drawn boards rather than invent closures. Compilation can fail even when a drawing appears plausible.

The app agent benchmark has bundled reference examples. It is not the 19-case LoRA benchmark. Claims about agent generalization require its holdout mode. The app source repository URL was verified as `https://github.com/Superpapotas/cutlistmaker-ai-engine`; it remains private and is not part of this public release. These paths are a source-navigation map, not a claim that the reader is shipped here.

The comparison CAD images call the app's `renderModelObservationIsoPane` in `src/features/modeler/agent/modelObservationSheet.ts`. It rasterizes panel cuboids with a per-pixel depth buffer and visible edges. This is the real observation renderer used by Fabivo, not a new hand-drawn isometric approximation. The input is each medoid's archived `document-prod.json`. Only material color changes for display; positions, dimensions, panel count and features do not.
