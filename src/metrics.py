"""Shared evaluation for canonical front-elevation labels.

Document conversion is not included; pass canonical label strings.
score(pred, gold)     dict with
  f1      board F1, greedy one-to-one, both labels normalized to their OWN box
          (x/W, y/H in 0..1000) with tolerance tol -> layout/topology, independent of
          the overall proportion;
  f1_abs  the same in the shared canonical frame (tol) -> also punishes proportion;
  aspect  |log(aspect_pred / aspect_gold)|;
  count   n_pred - n_gold.
"""
import json, math

def parse(text):
    box, out = None, []
    for line in (text or '').strip().splitlines():
        p = line.split()
        try:
            if len(p) == 3 and p[0] == 'box': box = (float(p[1]), float(p[2]))
            elif len(p) == 5 and p[0] in ('h', 'v'): out.append((p[0], *[float(v) for v in p[1:]]))
        except ValueError: pass
    if out and not box:
        box = (max(b[3] for b in out), max(b[4] for b in out))
    return box, out

def merge(boards, box):
    """Segmentation-invariant: fuse boards of one orientation that lie on the same
    line (thickness band within 1.5% of the long side) and touch or are separated
    only by a crossing board (gap <= 2.5 thicknesses)."""
    L = max(box) or 1000; bs = [list(b) for b in boards]; changed = True
    while changed:
        changed = False
        for i in range(len(bs)):
            for j in range(i + 1, len(bs)):
                a, b = bs[i], bs[j]
                if a[0] != b[0]: continue
                if a[0] == 'h': ta, tb, la, lb = (a[2], a[4]), (b[2], b[4]), (a[1], a[3]), (b[1], b[3])
                else: ta, tb, la, lb = (a[1], a[3]), (b[1], b[3]), (a[2], a[4]), (b[2], b[4])
                if abs(ta[0] - tb[0]) > 0.015 * L or abs(ta[1] - tb[1]) > 0.015 * L: continue
                th = max(ta[1] - ta[0], tb[1] - tb[0], 0.005 * L)
                if max(la[0], lb[0]) - min(la[1], lb[1]) > 2.5 * th: continue
                lo, hi = min(la[0], lb[0]), max(la[1], lb[1]); t0, t1 = min(ta[0], tb[0]), max(ta[1], tb[1])
                bs[i] = ['h', lo, t0, hi, t1] if a[0] == 'h' else ['v', t0, lo, t1, hi]
                del bs[j]; changed = True; break
            if changed: break
    return [tuple(b) for b in bs]

def _norm(box, boards):
    W, H = box
    return [(k, 1000 * a / W, 1000 * b / H, 1000 * c / W, 1000 * d / H) for k, a, b, c, d in boards]

def _match(pred, gold, tol):
    # optimal-ish: greedy by smallest max-coordinate error
    pairs = []
    for i, p in enumerate(pred):
        for j, g in enumerate(gold):
            if p[0] != g[0]: continue
            e = max(abs(a - b) for a, b in zip(p[1:], g[1:]))
            if e <= tol: pairs.append((e, i, j))
    pairs.sort(); ui, uj, hit = set(), set(), 0
    for e, i, j in pairs:
        if i in ui or j in uj: continue
        ui.add(i); uj.add(j); hit += 1
    pr = hit / len(pred) if pred else 0.0; rc = hit / len(gold) if gold else 0.0
    return (2 * pr * rc / (pr + rc)) if pr + rc else 0.0

def score(pred_text, gold_text, tol=40):
    pb, pred = parse(pred_text); gb, gold = parse(gold_text)
    if pred: pred = merge(pred, pb)
    if gold: gold = merge(gold, gb)
    if not pred or not pb or pb[0] <= 0 or pb[1] <= 0:
        return {'f1': 0.0, 'f1_abs': 0.0, 'aspect': None, 'count': -len(gold), 'valid': False}
    return {
        'f1': _match(_norm(pb, pred), _norm(gb, gold), tol),
        'f1_abs': _match(pred, gold, tol),
        'aspect': abs(math.log((pb[0] / pb[1]) / (gb[0] / gb[1]))),
        'count': len(pred) - len(gold),
        'valid': True,
    }

# ---- structural score: same boards, same order, same connections; millimetres ignored ----
def _lines(boards, kind, axis_thick):
    """Cluster board centre lines of one orientation; stacked boards that touch merge into one line."""
    cs = sorted(((a + c) / 2 if kind == 'v' else (b + d) / 2) for k, a, b, c, d in boards if k == kind)
    cs = [0.0] + cs + [1000.0]
    out = []
    for x in cs:
        if out and x - out[-1][-1] <= 1.2 * axis_thick: out[-1].append(x)
        else: out.append([x])
    return [sum(g) / len(g) for g in out]

def _align(P, G, T):
    """Order-preserving alignment of two sorted line lists maximising total closeness (1 - d/T)."""
    n, m = len(P), len(G)
    best = [[0.0] * (m + 1) for _ in range(n + 1)]; how = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            c, h = best[i - 1][j], 1
            if best[i][j - 1] > c: c, h = best[i][j - 1], 2
            d = abs(P[i - 1] - G[j - 1])
            if d <= T and best[i - 1][j - 1] + 1 - d / T > c: c, h = best[i - 1][j - 1] + 1 - d / T, 3
            best[i][j] = c; how[i][j] = h
    mp = {}; i, j = n, m
    while i and j:
        h = how[i][j]
        if h == 3: mp[i - 1] = j - 1; i -= 1; j -= 1
        elif h == 1: i -= 1
        else: j -= 1
    return mp

def _near(L, x): return min(range(len(L)), key=lambda i: abs(L[i] - x))

def _same(vp, vg, LP, LG, mp, tol):
    """Pred and gold coordinates agree: same structural line after alignment, or simply close."""
    return abs(vp - vg) <= tol or mp.get(_near(LP, vp), -1) == _near(LG, vg)

def struct_score(pred_text, gold_text, T=250):
    pb, pred = parse(pred_text); gb, gold = parse(gold_text)
    if not pred or not pb or pb[0] <= 0 or pb[1] <= 0 or not gold: return {'f1': 0.0, 'valid': False}
    pred = _norm(pb, merge(pred, pb)); gold = _norm(gb, merge(gold, gb))
    th = lambda bs, k: sorted([(c - a) if k == 'v' else (d - b) for kk, a, b, c, d in bs if kk == k] or [20])[len([1 for x in bs if x[0] == k]) // 2 if any(x[0] == k for x in bs) else 0]
    PX, PY = _lines(pred, 'v', th(pred, 'v')), _lines(pred, 'h', th(pred, 'h'))
    GX, GY = _lines(gold, 'v', th(gold, 'v')), _lines(gold, 'h', th(gold, 'h'))
    mx, my = _align(PX, GX, T), _align(PY, GY, T)
    def ok(p, g):
        if p[0] != g[0]: return False
        if p[0] == 'v':
            return (_same((p[1] + p[3]) / 2, (g[1] + g[3]) / 2, PX, GX, mx, 40) and _same(p[2], g[2], PY, GY, my, 60)
                    and _same(p[4], g[4], PY, GY, my, 60))
        return (_same((p[2] + p[4]) / 2, (g[2] + g[4]) / 2, PY, GY, my, 40) and _same(p[1], g[1], PX, GX, mx, 60)
                and _same(p[3], g[3], PX, GX, mx, 60))
    pairs = sorted((max(abs(a - b) for a, b in zip(p[1:], g[1:])), i, j) for i, p in enumerate(pred) for j, g in enumerate(gold) if ok(p, g))
    ui, uj, hit = set(), set(), 0
    for e, i, j in pairs:
        if i in ui or j in uj: continue
        ui.add(i); uj.add(j); hit += 1
    pr, rc = hit / len(pred), hit / len(gold)
    # precision/recall and the unmatched boards (normalised coordinates) are extra keys; callers that read only 'f1' are unaffected
    return {'f1': 2 * pr * rc / (pr + rc) if hit else 0.0, 'valid': True, 'precision': pr, 'recall': rc, 'hit': hit,
            'n_pred': len(pred), 'n_gold': len(gold), 'extra': [pred[i] for i in range(len(pred)) if i not in ui],
            'missed': [gold[j] for j in range(len(gold)) if j not in uj]}
