"""CPU composition of actual archived photos, predictions and Fabivo renders.
No inference. Reference photos remain third-party; no standalone photos emitted.
Requires Pillow and RGBA panes from the app's renderModelObservationIsoPane.
"""
import argparse
import hashlib
import html
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageChops

ROOT = Path(__file__).resolve().parents[1]
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
INK = '#262824'
BG = '#faf9f6'


def text(draw, xy, value, size, color=INK):
    draw.text(xy, value, font=ImageFont.truetype(FONT, size), fill=color)


def fitted(image, size, trim=False):
    image = image.convert('RGBA')
    if trim:
        box = image.getbbox() if image.getextrema()[3][0] == 0 else ImageChops.difference(image.convert('RGB'), Image.new('RGB', image.size, 'white')).convert('L').point(lambda v: 255 if v > 65 else 0).getbbox()
        if box:
            image = image.crop(box)
    scale = min(size[0]/image.width, size[1]/image.height)
    return image.resize((round(image.width*scale), round(image.height*scale)), Image.Resampling.LANCZOS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--archive', type=Path, required=True)
    ap.add_argument('--photos', type=Path, required=True)
    ap.add_argument('--rendered', type=Path, required=True)
    ap.add_argument('--manifest', type=Path, required=True)
    args = ap.parse_args()
    rows = json.loads((args.archive / 'cons-10.json').read_text())
    assert len(rows) == 19 and [r['case'] for r in rows] == sorted(r['case'] for r in rows)
    metrics = json.loads((ROOT/'results/m11-verified.json').read_text())['cases']
    provenance = {r['case']: r for r in map(json.loads, args.manifest.read_text().splitlines()) if r['split'] == 'gold'}
    out = ROOT/'assets/comparisons'
    out.mkdir(parents=True, exist_ok=True)
    records = []
    cards = []
    for i, row in enumerate(rows):
        case, pick = row['case'], Path(row['pick'])
        score = metrics[i]
        assert score['case'] == case
        doc_path = Path(str(pick)+'-trace')/case/'document-prod.json'
        doc = json.loads(doc_path.read_text())
        photo_path, raw_path = args.photos/f'{case}.jpg', pick/f'{case}.png'
        credit = provenance[case]
        assert hashlib.sha256(photo_path.read_bytes()).hexdigest() == credit['used_image_sha256']
        photo = Image.open(photo_path)
        raw = Image.open(raw_path)
        cad = Image.frombytes('RGBA', (1000,1000), (args.rendered/f'{case}.rgba').read_bytes())
        canvas = Image.new('RGB', (1800,820), BG)
        draw = ImageDraw.Draw(canvas)
        labels = [('01', 'Reference photograph', 'Third-party source'), ('02','Model drawing','m11 / Turbo 10 / four-seed medoid'),('03','Fabivo CAD','Actual compiled panels; illustrative material')]
        for j, (number,title,sub) in enumerate(labels):
            x = 38+j*588
            text(draw,(x,26),number,22,'#82776a')
            text(draw,(x+45,22),title,30)
            text(draw,(x,70),sub,19,'#686961')
            draw.line((x,112,x+548,112),fill='#d6d3cb',width=1)
        for j, (image,trim) in enumerate([(photo,False),(raw,True),(cad,True)]):
            im = fitted(image,(516,554),trim)
            x = 38+j*588+(548-im.width)//2
            y = 137+(554-im.height)//2
            canvas.paste(im,(x,y),im)
        text(draw,(592,389),'→',32,'#82776a'); text(draw,(1180,389),'→',32,'#82776a')
        draw.line((38,714,1762,714),fill='#d6d3cb',width=1)
        text(draw,(38,738),'CAD defaults: 1200 mm width · 350 mm depth · 18 mm boards. Not measured from the photograph.',22)
        text(draw,(38,782),f'Reference: {case} · third-party rights retained; source and credit in docs/comparison-sources.md.',17,'#686961')
        name = f'{i+1:02d}-{case}.png'
        canvas.save(out/name,optimize=True)
        records.append({'case':case,'comparison':f'assets/comparisons/{name}','photo_sha256':hashlib.sha256(photo_path.read_bytes()).hexdigest(),'generated_sha256':hashlib.sha256(raw_path.read_bytes()).hexdigest(),'document_sha256':hashlib.sha256(doc_path.read_bytes()).hexdigest(),'medoid_seed':score['medoid']['10']['seed'],'panel_count':len(doc['panels']),'source_page_url':credit.get('source_page_url'),'source_image_url':credit.get('source_image_url'),'source_status':credit['source_status'],'source_credit':'Recorded source: IKEA product catalogue; photographer not verified' if 'ikea.com/' in (credit.get('source_page_url') or '') else 'Original source/author not verified','reference_rights':'Third-party; all original rights retained. No license granted by this repository.','renderer':'Fabivo renderModelObservationIsoPane; material color override only; geometry unchanged'})
        title = case.replace('photo-','').replace('real-','').replace('-',' ').capitalize()
        cards.append(f'<section id="{html.escape(case)}"><h2>{i+1:02d} / {html.escape(title)}</h2><img loading="lazy" src="../assets/comparisons/{name}" alt="{html.escape(title)}: original photograph, actual selected drawing and actual compiled Fabivo CAD"><p>Structural F1 {score["medoid"]["10"]["struct"]:.3f}; board F1 {score["medoid"]["10"]["board"]:.3f}. {len(doc["panels"])} compiled panels. Selected seed {score["medoid"]["10"]["seed"]}. <a href="comparison-sources.md">Reference source and rights</a>.</p></section>')
    (ROOT/'results/comparison-provenance.json').write_text(json.dumps(records,indent=2)+'\n')
    css = 'body{margin:0;background:#faf9f6;color:#262824;font:18px/1.6 system-ui,sans-serif}main{max-width:1240px;margin:60px auto;padding:0 28px}h1{font-size:44px;line-height:1.1;font-weight:650}h2{font-size:25px;font-weight:550;margin-top:65px}a{color:#425e52}img{width:100%;height:auto}p{max-width:950px}nav{display:flex;gap:18px;flex-wrap:wrap}section{border-top:1px solid #d6d3cb;margin-top:48px}'
    intro = '<h1>What the model kept. What it changed.</h1><p>All 19 cases, in fixed alphabetical order. Each drawing is the actual m11 Turbo10 medoid selected by agreement between four seeds, without target labels. The CAD uses the archived reader output: no corrected boards, no hidden back added.</p><p>The photos are third-party references, not CC BY or Apache-licensed assets. Source provenance is incomplete. CAD size, depth, thickness and finish are illustrative defaults, not recovered measurements. This reused gold set is a diagnostic, not an unseen test.</p><nav><a href="../README.md">Project explanation</a><a href="m11-gallery.md">Full score table</a><a href="comparison-sources.md">Sources / rights</a></nav>'
    (ROOT/'docs/cases.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fabivo — all 19 comparison cases</title><style>'+css+'</style><main>'+intro+''.join(cards)+'</main></html>')
    sources = ['# Comparison reference sources and rights', '', 'These composites include original internet reference photographs at the owner’s request. The photographs remain third-party material: all original rights retained. They are excluded from the software Apache-2.0 and annotation CC BY 4.0 grants. A source link identifies origin, not permission. Missing author/source information is not filled with an invented credit. No standalone reference-photo dataset is included.', '', 'The model drawing is the raw selected experimental m11 generation. CAD pixels come from Fabivo’s depth-buffer renderer using its archived compiled document. Only the display material is changed to a neutral finish. The source hashes and selected seeds are in [comparison provenance](../results/comparison-provenance.json).', '', '| Case | Source page | Credit / status |', '|---|---|---|']
    for r in records:
        url = r['source_page_url']
        sources.append(f'| {r["case"]} | {url or "Not recovered"} | {r["source_credit"]}. Third-party rights retained. {r["source_status"]}. |')
    (ROOT/'docs/comparison-sources.md').write_text('\n'.join(sources)+'\n')
    print('Built 19 actual photo → generated drawing → Fabivo CAD comparisons; verified source-photo hashes.')

if __name__ == '__main__':
    main()
