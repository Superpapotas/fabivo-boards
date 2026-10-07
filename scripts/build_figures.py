"""CPU-only score charts and score tables from archived runs.

Comparison images use build_showcase.py and the actual Fabivo renderer.
This script checks metrics; it does not run inference or copy source photos.
Requires Pillow. Run with --archive and --dataset-stage.
"""
import argparse
import hashlib
import html
import json
import math
from pathlib import Path
from statistics import mean
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets/figures'
BLUE, GREY, INK = '#24618c', '#7a8691', '#172633'


def load(path):
    return json.loads(path.read_text())


def close(a, b):
    assert math.isclose(a, b, abs_tol=1e-12), (a, b)


class Canvas:
    def __init__(self, w, h, title):
        self.w, self.h = w, h
        self.image = Image.new('RGB', (w, h), 'white')
        self.draw = ImageDraw.Draw(self.image)
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><title>{html.escape(title)}</title><rect width="100%" height="100%" fill="white"/>']

    def text(self, x, y, text, size=20, color=INK):
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', size)
        self.draw.text((x, y), text, font=font, fill=color)
        self.svg.append(f'<text x="{x}" y="{y + size}" font-family="DejaVu Sans,sans-serif" font-size="{size}" fill="{color}">{html.escape(str(text))}</text>')

    def line(self, x1, y1, x2, y2, color=GREY, width=1):
        self.draw.line((x1, y1, x2, y2), fill=color, width=width)
        self.svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"/>')

    def rect(self, x, y, w, h, color):
        self.draw.rectangle((x, y, x+w, y+h), fill=color)
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}"/>')

    def polygon(self, points, color):
        self.draw.polygon(points, fill=color, outline='#344c60')
        pts = ' '.join(f'{x:.3f},{y:.3f}' for x, y in points)
        self.svg.append(f'<polygon points="{pts}" fill="{color}" stroke="#344c60" stroke-width="0.7"/>')

    def save(self, name):
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / f'{name}.svg').write_text('\n'.join(self.svg + ['</svg>'])+'\n')
        self.image.save(OUT / f'{name}.png')


def chart(name, title, subtitle, labels, series, note):
    c = Canvas(1080, 600, title)
    c.text(28, 20, title, 27)
    c.text(28, 62, subtitle, 18)
    left, top, bottom, span = 105, 145, 460, 875
    for tick in range(6):
        v = tick / 5
        y = bottom - v * (bottom-top)
        c.line(left, y, left+span, y, '#e5e9ed')
        c.text(48, y-12, f'{v:.1f}', 17)
    c.text(28, 105, 'F1', 18)
    slot = span / len(labels)
    bw = min(92, slot/(len(series)+1))
    for j, (legend, key, color, values) in enumerate(series):
        c.rect(105+j*300, 103, 18, 18, color)
        c.text(132+j*300, 98, legend, 18)
        for i, value in enumerate(values):
            x = left + slot*(i+0.5) + (j-(len(series)-1)/2)*bw - bw/2
            height = value*(bottom-top)
            c.rect(x, bottom-height, bw-9, height, color)
            c.text(x-2, bottom-height-28, f'{value:.4f}', 17)
    for i, label in enumerate(labels):
        c.text(left+slot*(i+0.5)-65, bottom+12, label, 19)
    c.text(28, 525, note, 18)
    c.text(28, 557, 'Gold is reused validation. Failures remain in the denominator.', 17)
    c.save(name)


def drawing(c, label, x, y, w, h):
    rows = label.strip().splitlines()
    _, bw, bh = rows[0].split()
    bw, bh = float(bw), float(bh)
    scale = min(w/bw, h/bh)
    ox, oy = x+(w-bw*scale)/2, y+(h-bh*scale)/2
    for row in rows[1:]:
        _, x1, y1, x2, y2 = row.split()
        x1, y1, x2, y2 = map(float, (x1, y1, x2, y2))
        c.rect(ox+x1*scale, oy+y1*scale, (x2-x1)*scale, (y2-y1)*scale, '#172633')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--archive', type=Path, required=True)
    ap.add_argument('--dataset-stage', type=Path, required=True)
    args = ap.parse_args()
    sources = ['qwen21-m11-r64/selection.json', 'qwen21-m11-steps61015-gold/results.json', 'qwen21-m11-standard28-gold/results.json']
    selection, steps, standard = [load(args.archive/s) for s in sources]
    manifest = load(args.archive/'qwen21-m11-steps61015-gold/run-manifest.json')
    assert manifest['seeds'] == [0,1,2,3] and manifest['resolution'] == 768
    assert manifest['checkpoint'].endswith('qwen21-m11-r64/ckpt-3000-ema/lora.safetensors')
    assert len(manifest['completed']) == 19*4*3
    for row in manifest['completed']:
        assert row['steps'] == row['actual_steps']
    for n in [6,10,15]:
        assert len(manifest['samplers'][str(n)]) == n
        group = [r for r in manifest['completed'] if r['steps'] == n]
        close(mean(r['seconds'] for r in group), steps['summary'][str(n)]['seconds_per_image'])
        rows = [r[str(n)] for r in steps['cases']]
        close(mean(r['struct'] for r in rows), steps['summary'][str(n)]['medoid_struct'])
        close(mean(r['board'] for r in rows), steps['summary'][str(n)]['medoid_board'])
        close(mean(mean(r['seed_struct']) for r in rows), steps['summary'][str(n)]['single_seed_struct_mean'])
    assert standard['n'] == 19 and standard['seed'] == 0
    assert [r['case'] for r in steps['cases']] == sorted(r['case'] for r in steps['cases'])
    assert [r['case'] for r in steps['cases']] == [r['case'] for r in standard['cases']]
    for arm, values in standard['arms'].items():
        for metric in ['struct_f1','board_f1']:
            close(mean(r['scores'][arm][metric] for r in standard['cases']), values[metric])
        assert sum(r['scores'][arm]['traced'] for r in standard['cases']) == values['traced']
    common = [r for r in standard['cases'] if all(s['traced'] for s in r['scores'].values())]
    assert len(common) == 17
    aggregate = {
        'sources': {s: hashlib.sha256((args.archive/s).read_bytes()).hexdigest() for s in sources},
        'selection': selection, 'step_study': steps['summary'], 'standard_study': {k:v for k,v in standard.items() if k in ['n','seed','arms','caveat']},
        'conditional_common17': {arm:mean(r['scores'][arm]['struct_f1'] for r in common) for arm in standard['arms']},
        'setup': {k:manifest[k] for k in ['seeds','resolution','base_revision','turbo_revision','prompt','samplers','scheduler','torch','diffusers']},
        'checkpoint': 'm11 rank64 3000-EMA (experimental; not released)',
        'cases': [{'case':r['case'], 'medoid': {n:{'seed': int(Path(r[n]['pick']).name.rsplit('-s',1)[1]) if '-s' in Path(r[n]['pick']).name else 0, 'struct':r[n]['struct'],'board':r[n]['board']} for n in ['6','10','15']}, 'seed0':standard['cases'][i]['scores']} for i,r in enumerate(steps['cases'])]
    }
    (ROOT/'results/m11-verified.json').write_text(json.dumps(aggregate,indent=2)+'\n')
    selected = selection['results'][selection['selected']]
    ref = selection['m10_1430_ema_reference']
    chart('checkpoint-comparison','Checkpoint comparison: four-seed medoid','Historical m10 reference and selected m11 3000-EMA; not a rank ablation', ['Test (53)','Gold (19)','Holdout (12)'], [('m10 1430-EMA','m10',GREY,[ref[s]['medoid_struct'] for s in ['test','gold','holdout']]),('m11 3000-EMA','m11',BLUE,[selected[s]['medoid_struct'] for s in ['test','gold','holdout']])], 'Rank, training length, schedule and warm start changed together.')
    summary = steps['summary']
    chart('m11-step-study','m11 Turbo: four-seed step study','Same 19 gold cases, seeds 0–3, resolution 768; selected 3000-EMA checkpoint',['6 steps','10 steps','15 steps'], [('Medoid structural','struct',BLUE,[summary[n]['medoid_struct'] for n in ['6','10','15']]),('Mean single-seed structural','single',GREY,[summary[n]['single_seed_struct_mean'] for n in ['6','10','15']])], 'Mean seconds per drawing: '+ ' / '.join(f'{summary[n]["seconds_per_image"]:.2f}' for n in ['6','10','15']) + '; medoid requires four drawings.')
    arms = standard['arms']
    chart('m11-standard-turbo','m11: standard and Turbo, seed 0','Same checkpoint, 19 gold cases, resolution 768; no medoid',['Standard 28','Turbo 6','Turbo 10','Turbo 15'], [('Structural F1','struct',BLUE,[a['struct_f1'] for a in arms.values()]),('Board F1','board',GREY,[a['board_f1'] for a in arms.values()])], 'Traced: 17/19 standard; 19/19 each Turbo. Turbo changes weights AND schedule.')
    gallery = ['# All 19 photo-to-CAD cases', '', 'Experimental m11 rank64 3000-EMA, Turbo10, resolution768, seeds0–3. The medoid picks one drawing by agreement among valid candidates, without gold labels. This is a reused gold diagnostic, not a test-selected production policy.', '', '[Open the static HTML case page](cases.html) locally for larger comparisons. Each figure shows the original third-party reference, the ACTUAL selected model drawing and the archived compiled document rendered by Fabivo. No geometry was corrected for presentation. Width1200 mm, depth350 mm and thickness18 mm are illustrative defaults, not photo measurements; the neutral finish is a display override.', '', 'References retain third-party rights and are not CC BY or Apache assets. [Sources and missing credits](comparison-sources.md). [Renderer and asset provenance](figure-provenance.md).', '']
    medoids = load(args.archive/'qwen21-m11-steps61015-gold/cons-10.json')
    assert [r['case'] for r in medoids] == [r['case'] for r in steps['cases']]
    for i, r in enumerate(steps['cases']):
        assert r['10']['pick'] == medoids[i]['pick']
        pick = Path(r['10']['pick'])
        assert pick.parent == args.archive/'qwen21-m11-steps61015-gold'
        load(pick.with_name(pick.name+'-trace')/r['case']/'document-prod.json')
        name = f'{i+1:02d}-{r["case"]}'
        gallery.extend([f'## {i+1:02d} / {r["case"]}', '', f'![Reference photograph, actual selected drawing and actual Fabivo CAD for {r["case"]}.](../assets/comparisons/{name}.png)', ''])
    gallery += ['## All-case scores', '', 'Structural / board F1. Main means include all 19 cases and failures. Full precision and seed-0 standard/Turbo scores are in [the verified JSON](../results/m11-verified.json).', '', '| Case | Turbo6 medoid | Turbo10 medoid | Turbo15 medoid | Standard28 seed0 |', '|---|---:|---:|---:|---:|']
    for i,r in enumerate(steps['cases']):
        pair = lambda a:f'{a[0]:.4f} / {a[1]:.4f}'
        vals = [pair((r[n]['struct'],r[n]['board'])) for n in ['6','10','15']]
        a = standard['cases'][i]['scores']['standard28'];vals.append(pair((a['struct_f1'],a['board_f1'])))
        gallery.append('| '+r['case']+' | '+' | '.join(vals)+' |')
    (ROOT/'docs/m11-gallery.md').write_text('\n'.join(gallery)+'\n')
    thinking_source = 'q35-9b-m10-thinking-gold/results.json'
    thinking = load(args.archive/thinking_source)
    thinking_summary = {}
    for name, arm in thinking['arms'].items():
        assert arm['n'] == 19 and arm['complete']
        for metric in ['struct_f1','board_f1']:
            close(mean(r[metric] for r in arm['per_case']), arm[metric])
        thinking_summary[name] = {k:v for k,v in arm.items() if k != 'per_case'}
    (ROOT/'results/thinking-verified.json').write_text(json.dumps({'source':thinking_source, 'sha256':hashlib.sha256((args.archive/thinking_source).read_bytes()).hexdigest(), 'arms':thinking_summary},indent=2)+'\n')
    labels = ['Off-greedy','Thinking','Off-sampled']
    names = ['off-greedy','think','off-sampled']
    chart('vlm-thinking','Qwen3.5-9B m10: thinking diagnostic','Completed H100 run, 19 reused gold cases; adapter trained without thinking',labels,[('Structural F1','struct',BLUE,[thinking_summary[n]['struct_f1'] for n in names]),('Board F1','board',GREY,[thinking_summary[n]['board_f1'] for n in names])], 'Thinking: 2 invalid outputs; 16/19 forced stops at 6144 thinking tokens.')
    print('Verified archive aggregates, actual steps, all-case order and 19 compiled documents; wrote four metric SVG/PNG pairs and all-case table.')


if __name__ == '__main__':
    main()
