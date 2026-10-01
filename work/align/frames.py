"""Every code-frame transition in the function table: first row of each frame, the previous row's
end, the gap bytes and parity.  Oracle read-only."""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import functions as fnmod, exe as exemod
x = exemod.load()
rows = fnmod.table()['functions']
out = []
for unit in sorted({r['unit'] for r in rows}):
    rs = sorted(rows, key=lambda r: r['seg'] * 16 + r['off'])
    rs = [r for r in rs if r['unit'] == unit]
    prev = None
    for r in rs:
        lin = r['seg'] * 16 + r['off']
        if prev is not None and r['seg'] != prev['seg']:
            pend = prev['seg'] * 16 + prev['off'] + prev['size']
            gap = x.read(unit, pend, lin - pend) if 0 <= lin - pend < 64 else None
            out.append({'unit': unit, 'frame': f"{r['seg']:04X}", 'first': f'{lin:05X}', 'off': r['off'],
                        'prev_frame': f"{prev['seg']:04X}", 'prev_end': f'{pend:05X}',
                        'gap': None if gap is None else gap.hex(), 'odd_start': lin % 2 == 1,
                        'prev_odd_end': pend % 2 == 1})
        prev = r
Path(__file__).with_name('frames.json').write_text(json.dumps(out, indent=1))
print(len(out), 'frame transitions')
for o in out:
    if o['odd_start'] or (o['gap'] and o['gap'].strip('0')) or o['gap'] is None:
        print(o)
from collections import Counter
print(Counter((o['prev_odd_end'], o['gap']) for o in out if o['gap'] is not None and len(o['gap']) <= 2))
