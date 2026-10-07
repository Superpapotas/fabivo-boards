"""Prepare an image-rights-filtered dataset. No network calls."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
import numpy as np

DECISIONS = {
    'blend1': ('included', 'Procedural Blender render. Poly Haven assets are CC0.'),
    'cf1': ('included', 'Counterfactual Blender render. No web-photo composite.'),
    'three1': ('included', 'Procedural Three.js render with the same CC0 asset library.'),
    'orph7t': ('included', 'Procedural Three.js orphan-archetype render.'),
    'codex5': ('labels-only', 'Generated from plans. Generator terms not established for this release.'),
    'codex6': ('labels-only', 'Generated from plans. Generator terms not established for this release.'),
    'codex7s': ('labels-only', 'Generated symmetric plans. Generator terms not established for this release.'),
    'orph7': ('labels-only', 'Gateway/Codex generated images. Generator terms not established.'),
    'photoclean': ('labels-only', 'Earlier generated collection. Full per-image provenance not established.'),
    'sdxl': ('labels-only', 'RealVisXL and ControlNet outputs. All component terms not established.'),
    'real': ('labels-only', 'Third-party web photographs. No image redistribution rights.'),
    'pl': ('labels-only', 'Human-approved pseudo-labels on third-party web photographs.'),
    'photo': ('labels-only', 'Third-party reference photographs. No image redistribution rights.'),
    'boxed': ('labels-only', 'Third-party reference photograph. No image redistribution rights.'),
    'h48': ('labels-only', 'Third-party holdout web photographs. No image redistribution rights.'),
    'syn3d': ('excluded', 'Not present in the static mix10 splits. Online procedural source only.'),
    'flat': ('excluded', 'Not present in the static mix10 splits. Online procedural source only.'),
    'stagger': ('excluded', 'Not present in the static mix10 splits.'),
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mix10', type=Path)
    ap.add_argument('workspace', type=Path)
    ap.add_argument('output', type=Path)
    args = ap.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    # Only known source-index files are read. Credential stores are not read.
    records = []
    for name in ['real/work2/downloaded.json', 'real/work/cand.json', 'real/work/cand2.json']:
        p = args.workspace / name
        if p.exists():
            data = json.loads(p.read_text())
            if isinstance(data, list):
                records.extend(x for x in data if isinstance(x, dict) and x.get('img') and x.get('page'))
    index = {}
    fingerprints = []
    fingerprint_records = []
    for r in records:
        for key in ['dst', 'file']:
            p = Path(r.get(key, ''))
            if p.is_file():
                index[sha(p)] = r
        p = Path(r.get('dst') or r.get('file') or '')
        if p.is_file():
            with Image.open(p) as im:
                fingerprints.append(np.asarray(im.convert('RGB').resize((24,24)), dtype=np.float32).reshape(-1))
                fingerprint_records.append(r)
    fingerprints = np.array(fingerprints)
    eval_labels = {hashlib.sha256(p.read_text().strip().encode()).hexdigest()
                   for split in ['test','gold','holdout'] for p in (args.mix10 / split).glob('*.txt')}
    seen = {}
    rows = []
    counts = collections.defaultdict(collections.Counter)
    excluded = []
    for split in ['train', 'test', 'gold', 'holdout']:
        for photo in sorted((args.mix10 / split).glob('*.jpg')):
            name = photo.stem
            if 'open028' in name.lower() or 'u100' in name.lower():
                excluded.append({'case': name, 'split': split, 'reason': 'Owner exclusion'})
                continue
            label = photo.with_suffix('.txt')
            if not label.is_file():
                raise ValueError('Missing label: ' + name)
            if split == 'train' and hashlib.sha256(label.read_text().strip().encode()).hexdigest() in eval_labels:
                excluded.append({'case': name, 'split': split, 'reason': 'Exact label duplicate of evaluation case'})
                for folder, suffix in [('labels','.txt'), ('drawings','.png'), ('images','.jpg')]:
                    target = out / folder / split / (name + suffix)
                    if target.exists(): target.unlink()
                continue
            digest = sha(photo)
            if digest in seen and seen[digest] != split:
                raise ValueError('Cross-split image duplicate: ' + name)
            seen[digest] = split
            family = name.split('-')[0]
            decision, reason = DECISIONS.get(family, ('labels-only', 'Image provenance not established.'))
            folder = out / 'labels' / split
            folder.mkdir(parents=True, exist_ok=True)
            target = folder / label.name
            target.write_text(label.read_text().strip() + '\n')
            with Image.open(photo) as im:
                width, height = im.size
                if decision == 'included':
                    folder = out / 'images' / split
                    folder.mkdir(parents=True, exist_ok=True)
                    clean = ImageOps.exif_transpose(im).convert('RGB')
                    # A new image holds no source metadata, EXIF or GPS.
                    clean = Image.frombytes('RGB', clean.size, clean.tobytes())
                    clean.save(folder / photo.name, quality=95)
            raw = label.read_text().splitlines()
            _, w, h = raw[0].split()
            w, h = float(w), float(h)
            scale = 768 / max(w, h)
            drawing = Image.new('RGB', (max(1, round(w*scale)), max(1, round(h*scale))), 'white')
            draw = ImageDraw.Draw(drawing)
            for line in raw[1:]:
                if not line.strip(): continue
                orientation, *coords = line.split()
                if orientation not in ['h', 'v'] or len(coords) != 4:
                    raise ValueError('Invalid label: ' + name)
                x1,y1,x2,y2 = [float(v)*scale for v in coords]
                draw.rectangle([x1,y1,x2,y2], fill='black')
            folder = out / 'drawings' / split
            folder.mkdir(parents=True, exist_ok=True)
            drawing.save(folder / (name + '.png'))
            source = index.get(digest)
            source_status = 'exact-file-index-match' if source else None
            if not source and family in ['real', 'pl', 'photo', 'boxed', 'h48'] and len(fingerprints):
                with Image.open(photo) as im:
                    vector = np.asarray(im.convert('RGB').resize((24,24)), dtype=np.float32).reshape(-1)
                errors = np.sqrt(np.mean((fingerprints - vector) ** 2, axis=1))
                order = np.argsort(errors)
                if errors[order[0]] < 3 and (len(order) == 1 or errors[order[1]] > 5):
                    source = fingerprint_records[order[0]]
                    source_status = 'unique-pixel-match-after-resize'
            original = Path(source.get('file', '')) if source else None
            rows.append({'case': name, 'split': split, 'family': family,
                         'image_decision': decision, 'reason': reason,
                         'used_image_sha256': digest, 'width': width, 'height': height,
                         'label': 'labels/' + split + '/' + label.name,
                         'drawing': 'drawings/' + split + '/' + name + '.png',
                         'image': 'images/' + split + '/' + photo.name if decision == 'included' else None,
                         'source_page_url': source['page'] if source else None,
                         'source_image_url': source['img'] if source else None,
                         'source_status': source_status or ('not-recovered' if family in ['real','pl','photo','boxed','h48'] else 'generator-script'),
                         'source_file_sha256': sha(original) if original and original.is_file() else None,
                         'label_sha256': sha(target)})
            counts[split][family] += 1
    (out / 'manifest.jsonl').write_text(''.join(json.dumps(r, sort_keys=True) + '\n' for r in rows))
    released_overlap = {}
    for kind in ['images', 'labels', 'drawings']:
        hashes = collections.defaultdict(set)
        for p in (out / kind).rglob('*'):
            if p.is_file(): hashes[sha(p)].add(p.parent.name)
        released_overlap[kind] = sum('train' in splits and len(splits) > 1 for splits in hashes.values())
    if any(released_overlap.values()):
        raise ValueError('Released train/evaluation content overlap')
    report = {'counts': {k: dict(v) for k,v in counts.items()}, 'excluded': excluded,
              'released_train_eval_sha256_overlap': released_overlap,
              'families': {k: {'decision': v[0], 'reason': v[1]} for k,v in DECISIONS.items()},
              'cross_split_sha256_overlap': 0,
              'missing_source_urls': sum(r['family'] in ['real', 'pl', 'photo', 'boxed', 'h48'] and not r['source_image_url'] for r in rows)}
    (out / 'audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
