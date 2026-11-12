"""The far uninitialised data at 50F6:01FE..10C1 as one compiler emission run (rule COMDEF-1).

    python tools/research/communal_runs.py            # summary, buckets of the unnamed objects
    python tools/research/communal_runs.py --table    # every object with its bucket and checksum

MSC 6.00AX emits the COMDEF records of a file's tentative definitions sorted by
(declaration ordinal mod 64, sum of the upper-case name characters mod 256, later first), and
the linkers in hand allocate communal variables in the order they first meet them
(evidence/codegen/COMDEF-1-communal-emission-order.json; linker part measured on RTLink/Plus
4.14 and 6.10 only, not on the release that linked the game).

Along the original addresses of this range the name checksums of the objects with an original
name therefore have to rise inside each of 64 buckets and fall only between buckets.  This
script counts those runs from layout/symbols.json alone.  Exactly 64 runs is the fit; a
shuffled order gives about 134.  It also lists, for each object that still has an
address-based name, the bucket and the checksum interval its original name must fall in.

What this supports: these objects were emitted by one object file (or first referenced by one
in the same order) and each one's declaration ordinal modulo 64.  What it does not give: which
file, the ordinals themselves, or the order between different turns of 64 declarations.
"""
from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEG, LOW, HIGH = 0x50F6, 0x01FE, 0x10C1
PLACEHOLDER = re.compile(r'^(fd|g)_[0-9A-Fa-f]{4}')


def checksum(name: str) -> int:
    return sum(name.upper().encode()) & 255


def objects() -> list[tuple[int, str, bool]]:
    """(offset, primary name, has an original name) in address order."""
    data = json.loads((ROOT / 'layout/symbols.json').read_text())['data']
    rows = {}
    for name, v in data.items():
        if v.get('seg') == SEG and LOW <= v['off'] <= HIGH and not v.get('alias_of'):
            named = not PLACEHOLDER.match(name)
            if v['off'] not in rows or (named and not rows[v['off']][2]):
                rows[v['off']] = (v['off'], name, named)
    return [rows[o] for o in sorted(rows)]


def run_count(names: list[str]) -> int:
    return 1 + sum(1 for a, b in zip(names, names[1:]) if checksum(b) < checksum(a))


def buckets(rows) -> list[dict]:
    """Bucket of every object; an unnamed one gets the range its neighbours allow."""
    out, bucket, last = [], 0, -1
    for off, name, named in rows:
        if named:
            c = checksum(name)
            if c < last:
                bucket += 1
            last = c
            out.append({'off': off, 'name': name, 'bucket': bucket, 'checksum': c})
        else:
            out.append({'off': off, 'name': name, 'bucket': None, 'checksum': None})
    for i, row in enumerate(out):
        if row['bucket'] is not None:
            continue
        before = next((r for r in reversed(out[:i]) if r['bucket'] is not None), None)
        after = next((r for r in out[i + 1:] if r['bucket'] is not None), None)
        lo_b = before['bucket'] if before else 0
        hi_b = after['bucket'] if after else lo_b
        row['bucket_range'] = [lo_b, hi_b]
        if lo_b == hi_b:
            row['checksum_range'] = [before['checksum'] if before else 0, after['checksum'] if after else 255]
        else:       # either at or above the previous name in its bucket, or at or below the next in the next
            row['checksum_range'] = {'in_bucket_%d' % lo_b: [before['checksum'], 255],
                                     'in_bucket_%d' % hi_b: [0, after['checksum']]}
    return out


def main() -> int:
    rows = objects()
    named = [n for _, n, ok in rows if ok]
    runs = run_count(named)
    r = random.Random(1)
    control = []
    for _ in range(200):
        s = named[:]
        r.shuffle(s)
        control.append(run_count(s))
    print(f'{SEG:04X}:{LOW:04X}..{HIGH:04X}: {len(rows)} objects, {len(named)} with an original name')
    print(f'checksum runs along the address order: {runs} (shuffled control: mean '
          f'{sum(control) / len(control):.1f}, minimum {min(control)})')
    table = buckets(rows)
    if '--table' in sys.argv:
        for row in table:
            print(f"  {row['off']:04X} {row['name']:<24} bucket {row.get('bucket', row.get('bucket_range'))} "
                  f"checksum {row.get('checksum') if row['checksum'] is not None else row['checksum_range']}")
    else:
        print('objects without an original name (bucket range, allowed checksum):')
        for row in table:
            if row['bucket'] is None:
                print(f"  {row['off']:04X} {row['name']:<16} {row['bucket_range']} {row['checksum_range']}")
    return 0 if runs == 64 else 1


if __name__ == '__main__':
    raise SystemExit(main())
