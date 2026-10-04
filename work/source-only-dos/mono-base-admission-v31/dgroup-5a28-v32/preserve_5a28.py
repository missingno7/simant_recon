"""Root reopening and preservation of the negative two-byte owner audit."""
from pathlib import Path
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
from omf import OmfReader
OUT = ROOT / 'work/source-only-dos/mono-base-admission-v31/dgroup-5a28-v32'

def pin(path):
    try: label = path.relative_to(ROOT).as_posix()
    except ValueError: label = str(path)
    return dict(path=label, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), size=path.stat().st_size)

def main():
    path = ROOT / 'build/workers/dos_dgroup_5a28_owner_v32/receipt.md'
    assert pin(path)['sha256'] == '909328b4f09d44dfec524eca461b2c34c49848ca567d532ad48dda00fe1ff393'
    receipt = path.read_text(encoding='utf-8')
    pins = []
    for name, digest in re.findall(r'^\| `([^`]+)` \| `([a-f0-9]{64})` \|$', receipt, re.M):
        source = Path(name) if Path(name).is_absolute() else ROOT / name
        actual = pin(source)
        assert actual['sha256'] == digest, name
        pins.append(actual)
    assert len(pins) == 9
    scan_path = ROOT / 'build/workers/behavior_data_audit/reference-scan.json'
    scan = json.loads(scan_path.read_bytes())
    assert scan['game_functions_scanned'] == 1730
    assert scan['function_reference_scan']['direct_data_operands']['dgroup_5a28'] == []
    assert scan['function_reference_scan']['immediate_address_candidates']['dgroup_5a28'] == []
    manifest = json.loads((ROOT / 'layout/manifest.json').read_bytes())
    placement = manifest['modules']['root:1F58']['placements']['_DATA']
    assert (placement['seg'], placement['off'], placement['size']) == (0x55B3, 0x5A2A, 8)
    report = json.loads((ROOT / 'build/source-only-dos/build-report.json').read_bytes())
    row = next(r for r in report['translation_units'] if r['module'] == 'root:1F58')
    obj_path = ROOT / row['object']['path']
    assert pin(obj_path)['sha256'] == row['object']['sha256']
    obj = OmfReader(communals=True).read(obj_path.read_bytes())
    assert obj.segment_lengths['_DATA'] == 8
    # These four labels are private, not PUBDEFs. Do not manufacture publics
    # merely because their canonical source names and offsets are known.
    assert not [p for p in obj.publics if p['segment'] == '_DATA']
    source = (ROOT/'src/root/m1F58.asm').read_text(encoding='ascii')
    assert re.findall(r'^(_g_5A\w+)\s+dw\s+0\b', source, re.M) == [
        '_g_5A2A', '_g_5A2C', '_g_5A2E', '_g_5A30']
    copies = [(path, OUT/'receipt.md'), (scan_path, OUT/'prior-reference-scan.json'),
              (ROOT/'build/workers/behavior_data_audit/REPORT.md', OUT/'prior-reference-report.md'),
              (Path(__file__), OUT/'preserve_5a28.py')]
    OUT.mkdir(exist_ok=True)
    preserved = []
    for source, target in copies:
        if target.exists(): assert target.read_bytes() == source.read_bytes()
        else: target.write_bytes(source.read_bytes())
        preserved.append(dict(original=pin(source), preserved=pin(target)))
    review = dict(root_reviewed=True, verdict='OWNERSHIP_UNRESOLVED', pins_reopened=pins,
                  original_receipts_unchanged=preserved, canonical_placement=placement,
                  actual_generated_object=pin(obj_path), generated_data_length=obj.segment_lengths['_DATA'],
                  generated_data_publics=[p for p in obj.publics if p['segment'] == '_DATA'],
                  source_storage_admission=False, debt_bytes_discharged=0,
                  claim_limit='No direct operand or address immediate in the bounded game scan identifies 5A28. '
                              'Computed pointer flow and runtime code remain outside that scan. The adjacent eight-byte '
                              'keyboard/vector contribution neither owns nor bounds the preceding word. Win16 latches '
                              'supply no independent DOS anchor. No unused/unreachable or alignment-fill conclusion.')
    (OUT/'root-review.json').write_bytes((json.dumps(review, indent=2)+'\n').encode())
    print('5A28 ROOT REVIEW PASS: nine pins; actual adjacent eight-byte object; ownership unresolved; zero debt discharged')

if __name__ == '__main__': main()
