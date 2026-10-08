"""Compose real saved GPT Image 2.5 and m11 outputs. CPU only.

Private manifest fields: id, name, reference_path, gpt_drawing_path,
gpt_result_path, m11_drawing_path, m11_document_path, m11_cad_path,
gpt_run, gpt_rerun. No inference or gold geometry is used.
--bridge points to the authorized Fabivo CPU bridge, not included here.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BG = '#faf9f6'
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
ORDER = ['boxed-centre-photo', 'photo-built-in-display', 'photo-staggered-console']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def text(draw, xy, value, size=24, color='#262824'):
    draw.text(xy, value, fill=color, font=ImageFont.truetype(FONT, size))


def place(canvas, image, x, y, w, h):
    image = image.convert('RGBA')
    image.thumbnail((w, h), Image.Resampling.LANCZOS)
    canvas.paste(image, (x + (w-image.width)//2, y + (h-image.height)//2), image)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--manifest', type=Path, required=True)
    ap.add_argument('--bridge', type=Path, required=True)
    args = ap.parse_args()
    sys.path.insert(0, str(args.bridge))
    from cad import compile_drawing
    rows = json.loads(args.manifest.read_text())
    assert [r['id'] for r in rows] == ORDER
    out = ROOT/'assets/gpt-comparison'
    out.mkdir(parents=True, exist_ok=True)
    published = []
    docs = ['# GPT Image 2.5 and Fabivo m11: saved visual examples', '',
            'The same source photographs enter two different pipelines. GPT Image 2.5 uses a frontal edit, then a board-drawing edit. Fabivo m11 predicts the drawing directly. The same current Fabivo reader compiles both drawings into panels. No boards were manually repaired.', '',
            '**These are three illustrative archived cases, not a controlled benchmark or proof of general superiority.** Prompts, resolution, inference budget and execution hardware differ. The GPT run uses Azure `gpt-image-2.5-sunburst`, low quality, prompt version `two-step-v5`, frontal candidate 1. m11 uses the published rank64 3000-EMA adapter, Turbo10, 768 pixels and seed 0. No four-seed selection is used in these figures.', '',
            'The cases are three requested references with saved outputs on both sides. They are not a complete GPT evaluation set or new unseen tests. The first GPT attempt on the staggered console failed with `invalid-provider-response`; the figure explicitly uses its saved rerun, not the failed call. No best-of selection was made between successful candidates.', '',
            'Width 1200 mm, depth 350 mm, thickness 18 mm and finish are assigned defaults for both CAD renders, not measurements recovered from the photo. Hidden construction and build safety are not established. Third-party reference photos retain all original rights and are excluded from software and dataset licenses.', '']
    for row in rows:
        result = json.loads(Path(row['gpt_result_path']).read_text())
        assert result['model'] == 'azure/gpt-image-2.5-sunburst'
        assert result['promptVersion'] == 'two-step-v5'
        assert result['quality'] == 'low' and result['candidate'] == 1
        assert result['failure'] is None
        gpt_drawing = Image.open(row['gpt_drawing_path'])
        cad = compile_drawing(gpt_drawing)
        assert cad['document']['panels']
        stem = row['id']
        cad['cad'].save(out/(stem+'-gpt-cad.png'))
        (out/(stem+'-gpt-document.json')).write_text(json.dumps(cad['document'])+'\n')
        m11doc = json.loads(Path(row['m11_document_path']).read_text())
        assert m11doc['panels']
        photo = Image.open(row['reference_path'])
        m11_drawing = Image.open(row['m11_drawing_path'])
        m11_cad = Image.open(row['m11_cad_path'])
        canvas = Image.new('RGB', (1800, 1250), BG)
        draw = ImageDraw.Draw(canvas)
        titles = ['Reference photograph', 'GPT Image 2.5', 'Fabivo m11 / Qwen']
        for j, title in enumerate(titles):
            x = 38 + j*588
            text(draw, (x, 26), title, 29)
            draw.line((x, 116, x+548, 116), fill='#d6d3cb')
        text(draw, (626, 72), '2 edits / frontal candidate 1', 21)
        text(draw, (1214, 72), 'Direct / Turbo10 / seed 0', 21)
        place(canvas, photo, 38, 155, 548, 914)
        text(draw, (626, 142), 'Generated board drawing', 23)
        text(draw, (1214, 142), 'Generated board drawing', 23)
        place(canvas, gpt_drawing, 626, 190, 548, 442)
        place(canvas, m11_drawing, 1214, 190, 548, 442)
        for x in [626, 1214]:
            draw.line((x, 658, x+548, 658), fill='#d6d3cb')
            text(draw, (x, 685), 'Compiled Fabivo CAD', 23)
        place(canvas, cad['cad'], 626, 728, 548, 350)
        place(canvas, m11_cad, 1214, 728, 548, 350)
        draw.line((38, 1106, 1762, 1106), fill='#d6d3cb')
        text(draw, (38, 1129), 'Same photo / different pipelines. Saved examples, not a controlled benchmark.', 23)
        text(draw, (38, 1174), 'CAD defaults: 1200 mm width / 350 mm depth / 18 mm boards. Not photo measurements.', 20)
        foot = 'Third-party reference; all original rights retained.'
        if row['gpt_rerun']:
            foot += ' GPT: saved rerun after the first provider response failed.'
        text(draw, (38, 1210), foot, 18, '#686961')
        composite = stem+'.jpg'
        canvas.save(out/composite, quality=94)
        public = {'id':stem, 'name':row['name'], 'comparison':composite,
                  'gpt_model':result['model'], 'gpt_prompt_version':result['promptVersion'],
                  'gpt_quality':result['quality'], 'gpt_candidate':1,
                  'gpt_run':row['gpt_run'], 'gpt_rerun':row['gpt_rerun'],
                  'gpt_drawing_sha256':sha(row['gpt_drawing_path']),
                  'gpt_document_sha256':sha(out/(stem+'-gpt-document.json')),
                  'm11_checkpoint_sha256':'776a9b8c897337449e65441866123b3a58e6f1ee12515b589e09e705c96e4b40',
                  'm11_policy':'Turbo10 / seed0 / 768 pixels',
                  'm11_drawing_sha256':sha(row['m11_drawing_path']),
                  'm11_document_sha256':sha(row['m11_document_path']),
                  'reference_sha256':sha(row['reference_path']),
                  'defaults_mm':{'width':1200,'depth':350,'thickness':18},
                  'rights':'Third-party reference photo; all original rights retained.',
                  'renderer':'Actual Fabivo production reader and depth-buffer renderer'}
        published.append(public)
        docs += [f'## {row["name"]}', '', f'![Same reference, GPT Image 2.5 drawing and compiled CAD, m11 drawing and compiled CAD.](../assets/gpt-comparison/{composite})', '', 'GPT uses the saved rerun after an invalid provider response.' if row['gpt_rerun'] else 'GPT uses candidate 1 of the saved production run.', '']
    (out/'manifest.json').write_text(json.dumps(published, indent=2)+'\n')
    docs += ['## Rebuild', '', '`python3 scripts/build_gpt_comparison.py --manifest PRIVATE_MANIFEST --bridge AUTHORIZED_FABIVO_BRIDGE`', '', 'The script checks the saved GPT model metadata and compiles its real drawing. It needs Pillow and the authorized Fabivo CPU bridge. It does not call an image API, load gold geometry, or perform GPU inference. Public hashes identify the exact archived artifacts; local input paths are not published.', '']
    (ROOT/'docs/gpt-image-comparison.md').write_text('\n'.join(docs))
    print('Built three paired visual examples from real archived outputs.')


if __name__ == '__main__':
    main()
