"""Which kinds of names count toward MSC 6.00AX's declaration numbers?

    python tools/research/declaration_kinds.py [KIND ...]

Inserts n names (n = 1..17) of one kind at a fixed point of src/ui/intro_credits.c
(S16:384C, whose code depends on declaration numbers modulo 17; see the layout-inferred
record of that module) and verifies the whole module with promote.py --verify-only. A row of
E (exact) for every n means that kind is not counted; the extern row is the positive
control, exact only where n keeps the residues the module needs (n = 17 is exact again).

Result 2026-11-13: define, enum and members are exact for every n; extern, tags and typedef
show the control's pattern E.EEEE.E........E. Analysis only; writes under build/scratch/.
"""
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/scratch/declaration_kinds'
NL = chr(10)
SRC = ROOT / 'src/ui/intro_credits.c'
ANCHOR = '/* Prototype spelling is inferred'
KINDS = {
    'extern': lambda n: ''.join(f'extern int far probe_x{k};' + NL for k in range(n)),
    'define': lambda n: ''.join(f'#define PROBE_D{k} {k}' + NL for k in range(n)),
    'enum': lambda n: 'enum probe_e { ' + ', '.join(f'PROBE_E{k}' for k in range(n)) + ' };' + NL,
    'members': lambda n: 'struct probe_m { ' + ' '.join(f'int m{k};' for k in range(n)) + ' };' + NL,
    'tags': lambda n: ''.join(f'struct probe_t{k} {{ int a; }};' + NL for k in range(n)),
    'typedef': lambda n: ''.join(f'typedef int probe_ty{k};' + NL for k in range(n)),
}


def run(job):
    kind, n, text, at = job
    path = OUT / f'{kind}_{n:02d}.c'
    path.write_text(text[:at] + KINDS[kind](n) + text[at:], encoding='latin1', newline=NL)
    r = subprocess.run([sys.executable, str(ROOT / 'tools/promote.py'), str(path), '--module', 'S16:384C',
                        '--verify-only'], capture_output=True, text=True, cwd=ROOT)
    return kind, n, 'VERIFY-ONLY OK' in r.stdout + r.stderr


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    text = SRC.read_text(encoding='latin1')
    at = text.index(ANCHOR)
    kinds = sys.argv[1:] or list(KINDS)
    with ThreadPoolExecutor(max_workers=4) as pool:
        res = list(pool.map(run, [(k, n, text, at) for k in kinds for n in range(1, 18)]))
    for kind in kinds:
        print(kind.ljust(8), ''.join('E' if ok else '.' for k, n, ok in res if k == kind), '(n = 1..17)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
