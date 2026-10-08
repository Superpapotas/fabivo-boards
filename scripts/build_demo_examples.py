"""CPU-only demo composition. No inference, tracing, or invented CAD.

Input: private manifest.json, ordered list of ten records with id, name,
local_inputpath, originalSHA256, width, height, origin and sourceURL.
Optional generated manifest: ordered records with id, status, drawing_path,
cad_path, document_path. Successful records must also have model='m11',
schedule='Turbo10', seed=0, steps=10 and renderer='Fabivo'. Paths may be
relative to that manifest. Failure records have status='failed' and a short
public error. Never replace a failed record with another seed.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
ORDER = [f'example-{i:02d}' for i in range(1, 7)] + [
    'boxed-centre-photo', 'photo-built-in-display',
    'photo-staggered-console', 'real-open041']
BG = '#faf9f6'
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
RIGHTS = 'Third-party; all original rights retained. No public license granted.'


def text(draw, xy, value, size=22, color='#262824'):
    draw.text(xy, value, fill=color, font=ImageFont.truetype(FONT, size))


def fitted(image, bounds):
    image = image.convert('RGBA')
    image.thumbnail(bounds, Image.Resampling.LANCZOS)
    return image


def place(canvas, image, x, y, w, h):
    image = fitted(image, (w, h))
    canvas.paste(image, (x + (w-image.width)//2, y + (h-image.height)//2), image)


def resolve(record, key, base):
    path = Path(record[key])
    return path if path.is_absolute() else base/path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--generated', type=Path)
    args = parser.parse_args()
    rows = json.loads(args.manifest.read_text())
    assert [r['id'] for r in rows] == ORDER, 'All ten inputs must retain fixed order'
    generated = {}
    if args.generated:
        results = json.loads(args.generated.read_text())
        assert [r['id'] for r in results] == ORDER, 'All ten outcomes are required'
        generated = {r['id']: r for r in results}
    out = ROOT/'assets/demo-examples'
    out.mkdir(parents=True, exist_ok=True)
    sheet = Image.new('RGB', (1600, 2180), BG)
    sd = ImageDraw.Draw(sheet)
    text(sd, (32, 24), 'Ten reference photographs', 32)
    text(sd, (32, 68), 'Fixed input order. Third-party rights retained; sources not verified.', 20)
    public = []
    docs = ['# Demo photographs', '', 'Ten inputs in fixed order: six user-provided files and four reused reference cases. Example 04 repeats the staggered-console reference. The user-provided set is not six independent unseen cases. No gold labels or accuracy scores are supplied for these inputs.', '', 'The photographs remain third-party material. Sources and authors are not verified for all ten. Publication was requested by the owner; this is not a legal warranty or a public license. The photographs are excluded from Apache-2.0 and CC BY 4.0 grants.', '', '![All ten reference photographs in fixed order.](../assets/demo-examples/reference-contact-sheet.jpg)', '']
    for i, row in enumerate(rows):
        case = row['id']
        with Image.open(row['local_inputpath']) as source:
            image = ImageOps.exif_transpose(source).convert('RGB')
            image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
            image = Image.frombytes('RGB', image.size, image.tobytes())
        photo = out/(case+'.jpg')
        image.save(photo, quality=94)
        with Image.open(photo) as check:
            assert check.mode == 'RGB' and not check.getexif()
            check.verify()
        x, y = 32+(i%2)*784, 116+(i//2)*408
        place(sheet, image, x, y, 752, 328)
        text(sd, (x, y+342), f'{i+1:02d} / {row["name"]}', 22)
        sd.line((x, y+389, x+752, y+389), fill='#d6d3cb')
        record = {key: row[key] for key in ('id','name','origin','originalSHA256','sourceURL')}
        record.update(reference=photo.name, width=image.width, height=image.height,
                      referenceSHA256=hashlib.sha256(photo.read_bytes()).hexdigest(),
                      rights=RIGHTS, source_status='Source and author not verified')
        if row.get('same_reference_as'):
            record['same_reference_as'] = row['same_reference_as']
        result = generated.get(case)
        record['status'] = result['status'] if result else 'pending'
        if result:
            assert result['status'] in ('ok', 'failed')
            canvas = Image.new('RGB', (1800, 820), BG)
            draw = ImageDraw.Draw(canvas)
            for j, title in enumerate(('Reference photograph', 'Model drawing', 'Fabivo CAD')):
                px = 38+j*588
                text(draw, (px, 26), f'{j+1:02d} / {title}', 28)
                draw.line((px, 104, px+548, 104), fill='#d6d3cb')
            place(canvas, image, 38, 130, 548, 554)
            if result['status'] == 'ok':
                assert (result['model'], result['schedule'], result['seed'], result['steps'], result['renderer']) == ('m11','Turbo10',0,10,'Fabivo')
                document_path = resolve(result, 'document_path', args.generated.parent)
                document = json.loads(document_path.read_text())
                assert document['panels'], 'CAD must have real compiled panels'
                for j, key in enumerate(('drawing_path', 'cad_path'), start=1):
                    path = resolve(result, key, args.generated.parent)
                    with Image.open(path) as artifact:
                        place(canvas, artifact, 38+j*588, 130, 548, 554)
                    record[key.replace('_path','SHA256')] = hashlib.sha256(path.read_bytes()).hexdigest()
                record['documentSHA256'] = hashlib.sha256(document_path.read_bytes()).hexdigest()
                record.update(model='m11', schedule='Turbo10', seed=0, steps=10, renderer='Fabivo', generation_origin=result.get('origin', 'saved-actual-inference'))
            else:
                message = 'Not generated: hosting unavailable' if result.get('origin') == 'not-generated' else 'Generation or conversion failed'
                text(draw, (626, 340), message, 23)
                text(draw, (1214, 340), 'No compiled CAD', 24)
            draw.line((38, 714, 1762, 714), fill='#d6d3cb')
            text(draw, (38, 738), 'CAD defaults: 1200 mm width / 350 mm depth / 18 mm boards. Not photo measurements.', 21)
            text(draw, (38, 782), 'Third-party photograph; all original rights retained. Source and author not verified.', 18, '#686961')
            comparison = case+'-comparison.jpg'
            canvas.save(out/comparison, quality=94)
            record['comparison'] = comparison
            if result['status'] == 'ok':
                outcome = 'm11 / Turbo10 / seed 0. Actual saved drawing and compiled Fabivo panels; no corrected geometry.'
            elif result.get('origin') == 'not-generated':
                outcome = 'Not generated: Hugging Face denied ZeroGPU hosting (HTTP 402). No GPU call was made and no result was substituted. This is a hosting limit, not a measured model failure.'
            else:
                outcome = 'Conversion failed; no substitute result.'
            docs += [f'## {i+1:02d} / {row["name"]}', '', f'![{row["name"]}: reference, model drawing and CAD outcome.](../assets/demo-examples/{comparison})', '', outcome, '']
        public.append(record)
    sheet.save(out/'reference-contact-sheet.jpg', quality=94)
    (out/'manifest.json').write_text(json.dumps(public, indent=2)+'\n')
    if not generated:
        docs += ['Drawings and CAD outcomes are pending. This page makes no generation or accuracy claim.', '', '| Input | Display label |', '|---|---|']
        docs += [f'| {r["id"]} | {r["name"]} |' for r in rows]
    else:
        docs += ['The reader uses assigned defaults of 1200 mm width, 350 mm depth and 18 mm boards. These are not calibrated measurements. Hidden construction and build safety are not established.', '']
    docs += ['', '## Rebuild', '', 'Run `python3 scripts/build_demo_examples.py --manifest PRIVATE_MANIFEST`. Add `--generated GENERATED_MANIFEST` only after actual drawings and Fabivo renders are ready. The script does not call a model or create CAD geometry. The private manifests must not be published.', '']
    (ROOT/'docs/demo-examples.md').write_text('\n'.join(docs))
    print('Prepared ten fixed-order examples; public manifest contains no local paths.')


if __name__ == '__main__':
    main()
