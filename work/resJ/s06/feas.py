"""feas.py DRAFT.c : for each /Zi LINNUM flush k, the absolute cumulative shifts c_k (line entries
added before flush k) for which the constraints touching flush k are satisfied, assuming the
other flushes stay where they are.  Analysis only (uses tools/records.py)."""
import sys
sys.path.insert(0, r'D:\Prog\simant_recon\tools')
import modctx, records

src = sys.argv[1]
R = int(sys.argv[2]) if len(sys.argv) > 2 else 30
ctx = modctx.resolve(module='S06:35F5', source=src, profile=None, flags=None, placements=[])
an = records.Analysis(ctx)
nfl = len(an.flushes)
base = [0] * nfl
cons = [c for c in an.constraints if an.checkable(c)]


def viol(shifts):
    br = an.breaks_for(an.flush_frames(lambda j: shifts[j - 1] if j <= len(shifts) else shifts[-1]))
    return [c for c in cons if an.violated(c, br)]


v0 = viol(base)
print('violations now:', len(v0))
for k in range(nfl):
    ok = []
    for c in range(-R, R + 1):
        s = list(base)
        s[k] = c
        v = viol(s)
        # constraints near this flush: count only those not already violated elsewhere
        ok.append((c, len(v)))
    best = min(n for _, n in ok)
    good = [c for c, n in ok if n == best]
    fl = an.flushes[k]
    print(f'flush {k + 1:2d} @ {fl.frame:04X} entry {fl.idx}: min viol {best} at c in {records.compress(good)}')
