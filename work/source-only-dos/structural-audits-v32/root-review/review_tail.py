"""Read-only parent runtime/fixup reopening before the v32 documentation correction."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import exe
import runtime
import search

WORKER = ROOT / 'build/workers/dos_tail_bss_boundary_v32'
receipt = json.loads((WORKER / 'tail-bss-boundary-v32.json').read_bytes())
pins = receipt['source_and_tools']['input_pins']
for pin in pins:
    path = Path(pin['path'])
    if not path.is_absolute():
        path = ROOT / path
    raw = path.read_bytes()
    assert len(raw) == pin['size'] and hashlib.sha256(raw).hexdigest() == pin['sha256'], path
results, derived, conflicts, anchors = runtime.verify_all()
assert len(results) == 90 and all(r['exact'] for r in results) and not conflicts
crt = next(r for r in results if r['member'].lower() == 'dos\\crt0.asm')
assert (crt['linear'], crt['size'], crt['member_sha256']) == (171868, 255,
    '2e9a254b9bd00ea59884089e78e951f0e40343e11d24976f32d9582f4ded259d')
assert set(derived['ext::_edata:DGROUP']) == {0x8B9E}
assert set(derived['ext::_end:DGROUP']) == {0x94F0}
assert len(derived['ext::_end:DGROUP'][0x94F0]) == 2
x = exe.load()
code = x.read('root', crt['linear'], crt['size'])
# The whole-member verifier above binds every fixup and checks relocations;
# these extra assertions isolate the observed instruction and loop boundaries.
instructions = search.disasm(code[0x80:0x8F], 0x009C)
assert [row[2] for row in instructions] == ['push ss', 'pop es', 'cld',
    'mov di, 0x8b9e', 'mov cx, 0x94f0', 'sub cx, di', 'xor ax, ax',
    'rep stosb byte ptr es:[di], al']
s27 = x.sections[27]
end = s27.load_linear + len(s27.data) - 0x55B30
assert end == 0x8BA0
assert s27.data_file_offset + len(s27.data) == 506256
offsets = list(range(end - 3, end))
written = [n for n in offsets if 0x8B9E <= n < 0x94F0]
assert offsets == [0x8B9D, 0x8B9E, 0x8B9F] and written == [0x8B9E, 0x8B9F]
mapping = receipt['historical_tail_file_to_runtime_mapping']
assert mapping['overwritten_tail_offsets'] == ['8B9E', '8B9F']
assert receipt['root_reviewed'] is False and receipt['admitted'] is False
print(json.dumps(dict(status='PASS', worker_input_pins_reopened=len(pins),
    complete_runtime_members_exact=90, crt0_all_fixups_and_relocations='PASS',
    original_file_mapping='ANALYSIS_ONLY',
    normal_startup_clear='DGROUP:[8B9E,94F0)', written_tail_bytes=['8B9E','8B9F'],
    excluded_tail_byte='8B9D', source_fields_or_physical_owner_admitted=False,
    historical_or_functional_debt_discharged=0, runtime_executed=False), indent=2))
