"""Build a static saved-result gallery. No live inference or external requests."""
import argparse
import html
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--generated', type=Path, required=True)
    args = ap.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    for folder in ['gpt-comparison', 'demo-examples']:
        shutil.copytree(ROOT/'assets'/folder, out/'assets'/folder, dirs_exist_ok=True)
    generated = json.loads(args.generated.read_text())
    downloads = out/'documents'
    downloads.mkdir(exist_ok=True)
    for row in generated:
        if row['status'] == 'ok':
            source = args.generated.parent/row['document_path']
            assert json.loads(source.read_text())['panels']
            shutil.copyfile(source, downloads/(row['id']+'.json'))
    examples = json.loads((ROOT/'assets/demo-examples/manifest.json').read_text())
    cards = []
    for row in examples:
        case = html.escape(row['id'], quote=True)
        name = html.escape(row['name'])
        status = 'Saved m11 prediction / Turbo10 / seed 0' if row['status'] == 'ok' else 'Reference only / not generated'
        links = f'<a href="assets/demo-examples/{case}-comparison.jpg" target="_blank" rel="noopener">View result</a> · <a href="documents/{case}.json" download>Download CAD JSON</a>' if row['status'] == 'ok' else 'ZeroGPU hosting unavailable; no result substituted.'
        cards.append(f'<article><img src="assets/demo-examples/{case}.jpg" alt="{name}" loading="lazy" width="480" height="320"><h3>{name}</h3><p class="status">{status}</p><p>{links}</p></article>')
    page = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fabivo / From furniture photos to editable boards</title>
<meta name="description" content="Actual saved GPT Image 2.5 and Fabivo m11 board drawings, compiled CAD and public research code.">
<style>
:root{color-scheme:light;--ink:#262824;--muted:#63665e;--paper:#faf9f6;--line:#d6d3cb}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 system-ui,sans-serif}main{max-width:1120px;margin:auto;padding:32px 24px 60px}header{border-bottom:1px solid var(--line);padding-bottom:24px}.eyebrow{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}h1{font-size:clamp(28px,4vw,44px);line-height:1.15;max-width:900px;font-weight:600;letter-spacing:-.02em;margin:12px 0}h2{font-size:25px;line-height:1.3;margin:32px 0 12px}h3{font-size:17px;line-height:1.35;font-weight:600}p{max-width:940px}a{color:#345447;text-underline-offset:3px}nav{display:flex;gap:12px 24px;flex-wrap:wrap}.status{color:var(--muted);font-size:13px}.notice{border-left:3px solid var(--line);padding-left:14px;font-size:14px;color:var(--muted)}select{font:inherit;color:inherit;background:var(--paper);padding:10px 12px;max-width:100%;border:1px solid var(--line);border-radius:4px}label{display:block;margin-bottom:6px;font-weight:500}figure{margin:16px 0}figure img{display:block;width:100%;height:auto}figcaption{color:var(--muted);font-size:14px;margin-top:10px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,280px),1fr));gap:24px}.grid article{border-top:1px solid var(--line);padding-top:18px}.grid img{display:block;width:100%;height:270px;object-fit:contain}.grid p{font-size:14px}footer{margin-top:38px;border-top:1px solid var(--line);padding-top:20px;font-size:13px;color:var(--muted)}:focus-visible{outline:3px solid #527965;outline-offset:4px}
</style></head><body><main>
<header><div class="eyebrow">Fabivo / image-to-CAD research</div><h1>From furniture photos to editable boards</h1><p>Predict a structural drawing. Read its boards. Compile actual CAD panels.</p><nav aria-label="Project links"><a href="https://github.com/Superpapotas/fabivo-boards">Code and experiments</a><a href="https://huggingface.co/Superpapotas1/fabivo-boards-image-lora-m11">m11 weights</a><a href="https://huggingface.co/datasets/Superpapotas1/fabivo-furniture-boards">Annotations</a><a href="https://fabivo.com">Fabivo</a></nav><p class="status">Saved results / no live inference / no GPU calls</p></header>
<section aria-labelledby="compare-heading"><h2 id="compare-heading">GPT Image 2.5 vs Fabivo m11</h2><p>Two GPT image edits versus one direct fine-tuned drawing. Both real drawings enter the same Fabivo reader; no boards are manually repaired.</p><label for="case">Reference photograph</label><select id="case"><option value="boxed-centre-photo">Wall display with projecting centre box</option><option value="photo-built-in-display">Built-in display with unequal openings</option><option value="photo-staggered-console" selected>White staggered console</option></select><figure><a id="full" href="assets/gpt-comparison/photo-staggered-console.jpg" target="_blank" rel="noopener" aria-label="Open full-size comparison"><img id="comparison" src="assets/gpt-comparison/photo-staggered-console.jpg" width="1800" height="1250" alt="White staggered console: reference photograph, GPT Image 2.5 drawing and compiled CAD, and m11 drawing and compiled CAD."></a><figcaption id="caption" aria-live="polite">White staggered console. GPT uses a saved rerun after the first provider response failed. Select the figure to view it at full size.</figcaption></figure><p class="notice">Illustrative archived cases, not a controlled benchmark. Prompts, resolution and budgets differ. GPT: Azure gpt-image-2.5-sunburst, low quality, frontal candidate 1, two-step-v5. m11: published rank64 3000-EMA, Turbo10, 768 pixels, seed 0. CAD defaults: 1200 mm width, 350 mm depth, 18 mm boards. Not measured dimensions or a safety-approved cutting plan.</p><p><a href="https://github.com/Superpapotas/fabivo-boards/blob/main/docs/gpt-image-comparison.md">All three cases and exact protocol</a></p></section>
<section aria-labelledby="examples-heading"><h2 id="examples-heading">The ten requested references</h2><p>Four cases have real saved m11 drawings and compiled documents. Six files have no new prediction. Example 04 repeats the staggered console with different encoding; it is not an independent unseen case.</p><p class="notice">Hugging Face refused ZeroGPU hosting for this account (HTTP 402). No paid fallback was used. This static gallery does not accept uploads or generate new images.</p><div class="grid">CARDS</div></section>
<footer>Built with Qwen. Qwen-Image 2.1 and its adapter are non-commercial research assets under the Qwen RESEARCH LICENSE AGREEMENT. Third-party reference photos retain all original rights and are excluded from code and dataset license grants. Source authors are not verified for these ten references. <a href="https://github.com/Superpapotas/fabivo-boards/blob/main/docs/demo-examples.md">Rights and result status</a>.</footer>
</main><script>
const select=document.getElementById('case');
select.addEventListener('change',()=>{
 const id=select.value;
 const name=select.selectedOptions[0].textContent;
 const src='assets/gpt-comparison/'+id+'.jpg';
 document.getElementById('comparison').src=src;
 document.getElementById('comparison').alt=name+': reference photograph, GPT Image 2.5 drawing and compiled CAD, and m11 drawing and compiled CAD.';
 document.getElementById('full').href=src;
 document.getElementById('caption').textContent=name+'. '+(id==='photo-staggered-console'?'GPT uses a saved rerun after the first provider response failed. ':'GPT uses candidate 1 of the saved production run. ')+'Select the figure to view it at full size.';
});
</script></body></html>'''
    (out/'index.html').write_text(page.replace('CARDS', '\n'.join(cards)))
    shutil.copyfile(ROOT/'LICENSE-APACHE-2.0', out/'LICENSE-CODE') if (ROOT/'LICENSE-APACHE-2.0').exists() else shutil.copyfile(ROOT/'LICENSE', out/'LICENSE-CODE')
    (out/'README.md').write_text('''---
title: Fabivo photo to CAD / saved comparisons
colorFrom: gray
colorTo: green
sdk: static
app_file: index.html
pinned: false
models:
- Superpapotas1/fabivo-boards-image-lora-m11
---
# Fabivo saved photo-to-CAD gallery

Public saved examples, including GPT Image 2.5 versus m11. This Space is static: it does not run live inference, allocate GPUs, accept uploads or call paid APIs. ZeroGPU hosting was refused for the account with HTTP 402. No paid fallback was used.

[Code and experiments](https://github.com/Superpapotas/fabivo-boards) · [m11 weights](https://huggingface.co/Superpapotas1/fabivo-boards-image-lora-m11) · [comparison protocol](https://github.com/Superpapotas/fabivo-boards/blob/main/docs/gpt-image-comparison.md)

Real saved drawings enter the actual Fabivo reader and CAD renderer. No geometry is manually repaired. Width/depth/thickness are assigned defaults, not image measurements. The downloadable JSON files contain compiled documents, not safety-approved cutting plans.

Static presentation code: Apache-2.0 (`LICENSE-CODE`). **Built with Qwen.** Qwen-Image 2.1 and m11: non-commercial Qwen RESEARCH LICENSE AGREEMENT; see the model's LICENSE and NOTICE. Reference photographs: third-party rights retained; no Apache-2.0 or CC BY grant. Original sources/authors are not verified for all ten references. The Space license does not grant rights to these photos or to upstream model derivatives.
''')
    print('Built static gallery; four compiled downloads, ten references, three GPT comparisons.')


if __name__ == '__main__':
    main()
