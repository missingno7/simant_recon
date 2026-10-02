import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0, 'tools')
import exe
import functions
import diag

x = exe.load()
report = json.loads(Path('build/link/provenance.json').read_text())
regions = [('root', x.mz.header_size, x.mz.header_size + 0x29F5C)] + [
    (f'S{i:02d}', s.data_file_offset, s.data_file_offset+len(s.data)) for i,s in enumerate(x.sections[:27])]
starts = {u: lo for u, lo, hi in regions}
known = {}
for name in diag.open_functions():
    f = functions.get(name)
    load_base, _ = x.unit_bytes(f['unit'])
    lo = starts[f['unit']] + f['seg']*16 + f['off'] - load_base
    for at in range(lo, lo+f['size']):
        assert at not in known
        known[at] = name
unowned = []
for rng in report['ranges']:
    if rng['class'] in {'C', 'ASM', 'DATA_IN_CODE', 'PAD'}:
        continue
    a, b = rng['file']
    for unit, lo, hi in regions:
        left, right = max(a, lo), min(b, hi)
        start = None
        for at in range(left, right+1):
            outside = at < right and at not in known
            if outside and start is None:
                start = at
            if not outside and start is not None:
                unowned.append({'unit': unit, 'file': [start, at], 'linear': [start-lo, at-lo],
                                'size': at-start, 'class': rng['class'], 'owner': rng['owner']})
                start = None
result = {'schema': 1, 'known_open_functions': len(diag.open_functions()),
          'known_function_bytes': len(known),
          'validated_unresolved_game_code': 15355,
          'outside_known_open_functions_bytes': sum(r['size'] for r in unowned),
          'ranges': unowned, 'authority': 'inventory only; no ownership or padding claim'}
result['provenance_sha256'] = hashlib.sha256(Path('build/link/provenance.json').read_bytes()).hexdigest()
result['oracle_sha256'] = x.sha256
result['manifest_sha256'] = hashlib.sha256(Path('layout/manifest.json').read_bytes()).hexdigest()
destination = Path('build/workers/hardtail_root/non-function-debt.json')
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(json.dumps(result, indent=1))
assert result['outside_known_open_functions_bytes'] + len(known) == result['validated_unresolved_game_code']
print({k: v for k, v in result.items() if k != 'ranges'})
