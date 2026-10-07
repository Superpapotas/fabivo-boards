"""Best-of-N by consensus (no gold involved in the choice): for every case, among the traced candidates of several
generations (seeds and/or mirrored-input TTA), keep the MEDOID: the candidate with the highest mean structural
agreement (metrics.struct_score, symmetrised) with the other candidates. Untraced candidates never win.
usage: consensus.py <mix> <out.json> <gen-dir> <gen-dir> ...   (each dir holds prod.json from fluxeval.py)
Prints, per split: mean single-candidate F1, the consensus pick's F1 and the oracle (best candidate) F1."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import metrics

def agree(a, b):
    return (metrics.struct_score(a, b)["f1"] + metrics.struct_score(b, a)["f1"]) / 2

def pick(cands):
    """Index of the medoid among non-empty candidates (ties -> earliest), or None."""
    ok = [i for i, c in enumerate(cands) if c]
    if not ok: return None
    if len(ok) == 1: return ok[0]
    score = {i: sum(agree(cands[i], cands[j]) for j in ok if j != i) / (len(ok) - 1) for i in ok}
    return max(ok, key=lambda i: (score[i], -i))

if __name__ == "__main__":
    mix, out, dirs = os.path.expanduser(sys.argv[1]), sys.argv[2], sys.argv[3:]
    preds = {}
    for d in dirs:
        for r in json.load(open(os.path.join(d, "prod.json"))): preds.setdefault(r["case"], {})[d] = r.get("pred") or ""
    res, rows = {}, []
    for case, by in sorted(preds.items()):
        sp = next((x for x in ("test", "gold", "holdout", "probe") if os.path.exists(f"{mix}/{x}/{case}.txt")), None)
        if sp is None: continue
        g = open(f"{mix}/{sp}/{case}.txt").read(); ds = [d for d in dirs if d in by]
        cands = [by[d] for d in ds]; f = [metrics.struct_score(c, g)["f1"] if c else 0.0 for c in cands]
        i = pick(cands); chosen = f[i] if i is not None else 0.0
        rows.append({"case": case, "split": sp, "n": len(cands), "pick": ds[i] if i is not None else None, "f1_pick": chosen, "f1_each": f})
        res.setdefault(sp, []).append((sum(f) / len(f), chosen, max(f), len(cands)))
    for sp, v in sorted(res.items()):
        n = len(v); print(f"{sp:5s} n={n:2d} cands/case={sum(x[3] for x in v) / n:.1f}  single(mean) {sum(x[0] for x in v) / n:.3f}  consensus {sum(x[1] for x in v) / n:.3f}  oracle {sum(x[2] for x in v) / n:.3f}")
    json.dump(rows, open(out, "w"), indent=1)
