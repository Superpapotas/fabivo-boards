# Owner review notes

The owner explicitly requested public GitHub/Hugging Face release after content checks. This applies only to `fabivo-boards`, `fabivo-boards-image-lora`, `fabivo-boards-vlm-9b` and `fabivo-furniture-boards`. The separate `fabivo-photos` repository and raw original-photo training data remain private/withheld.

## License decisions

Code is Apache-2.0. Copyright is Superpapotas, the GitHub account name. TODO: replace that name if the owner wants a legal name.

The image LoRA is under the full Qwen RESEARCH LICENSE AGREEMENT. It is for non-commercial research or evaluation only. The base and Viggle Turbo terms are not Apache-2.0. The image card says Built with Qwen. Its NOTICE carries the exact section 3c attribution and identifies the fine-tuned adapter modification. The primary product name is Fabivo, not Qwen. Future m11 weights need the same license and notices.

Commercial production use of the Qwen-Image LoRA in Fabivo needs a commercial license from Qwen. Contact model-business@notice.qwencloud.com. Private repository visibility does not remove that requirement.

The Qwen3.5-9B base is Apache-2.0. Its board-list LoRA is Apache-2.0. The checkpoint config records the Unsloth base loader. Taichu's base license is unknown. No Taichu weights are released.

## Dataset review

Original internet photos are included only inside comparison composites at the owner's explicit request. They retain third-party rights and are excluded from the software/annotation license. No permission or non-infringement claim is made. Missing source/author provenance and unresolved photo rights are documented review gaps, not resolved by the owner’s publication request. No standalone original-photo training dataset is released. Labels and our board drawings are CC BY 4.0. Approved procedural render families use the owner's scenes and CC0 Poly Haven assets. Generated-photo families remain labels-only where generator terms were not established. This is conservative; it does not assert that their output is prohibited.

The dataset manifest records the exact used-image SHA-256, size, family and original split. Missing source URLs are marked, not invented. URL recovery is not complete. This gap remains after the owner-authorized public release; recover source/author credits and review photo rights. Source recovery alone is not a redistribution license. Original downloads and resized training copies can have different hashes. A changed-hash report is not permission to redistribute a photo.

open028 and u100 are excluded. Exact image SHA-256 checks cannot rule out near-duplicate scenes or crops. Review those separately. The reused gold split remains development data.

## Reproduction and pending work

m11 completed-run results and actual photo/drawing/CAD comparisons are included as experimental evidence. The released image weights remain m10; no m11 weights replace them. No running job was changed.

CPU checks and upload integrity checks are separate from GPU reproduction. No training or model inference was run for this release. Minimal inference examples were syntax-checked, not GPU-tested. Exact m10 training still needs the earlier soup and private sampler modules.

Keep this owner-facing file out of the eventual public package if desired. Git history must then be reviewed too; deleting a file does not remove its history. No credential values are intended in this repository.
