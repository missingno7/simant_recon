"""Independent read-only reopening; report only metadata and symbolic instructions."""
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PACKET = ROOT / 'build/workers/dos_tail_clear_v36'
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'build/behavior/deps'))
sys.path.insert(0, 'C:/tools/capstone-5.0.3')
import exe
import runtime
import compiler
from omf import OmfReader
from capstone import Cs, CS_ARCH_X86, CS_MODE_16

def pin(path):
    raw = path.read_bytes()
    return dict(path=str(path), size=len(raw), sha256=hashlib.sha256(raw).hexdigest())

candidate = json.loads((PACKET / 'functional-tail-candidate.json').read_bytes())
pin_rows = candidate['artifact_pins'] + candidate['source_fixture_artifact_pins']
pin_results = []
for expected in pin_rows:
    observed = pin(Path(expected['path']))
    pin_results.append(dict(path=expected['path'], exact=observed == expected))
assert all(r['exact'] for r in pin_results)
compiler.verify_profile('msc600ax')
tc = compiler.toolchain()
selected_tool_checks = []
for profile in ('rtlink400', 'rtlink610'):
    definition = tc['linkers'][profile]
    for relative, expected in definition['files'].items():
        observed = pin(Path(definition['directory']) / relative)
        selected_tool_checks.append(dict(role=profile, path=observed['path'],
                                        exact=observed['sha256'] == expected))
for name, definition in json.loads((ROOT/'layout/manifest.json').read_bytes())['runtime']['libraries'].items():
    observed=pin(Path(definition['path']))
    selected_tool_checks.append(dict(role=name,path=observed['path'],exact=observed['sha256']==definition['sha256']))
runner=tc['runners']['dosbox-x']
selected_tool_checks.append(dict(role='dosbox-x',path=runner['path'],
    exact=pin(Path(runner['path']))['sha256']==runner['sha256']))
assert all(r['exact'] for r in selected_tool_checks)
retained_checks = []
for receipt in ('work/source-only-dos/structural-audits-v32/tail-bss-v32/tail-bss-boundary-v32.json',
                'work/source-only-dos/structural-audits-v35/original-debt-operands.json'):
    old = json.loads((ROOT / receipt).read_bytes())
    for expected in old.get('source_and_tools', {}).get('input_pins', old.get('input_pins', [])):
        path = Path(expected['path'])
        if not path.is_absolute():
            path = ROOT / path
        observed = pin(path)
        retained_checks.append(dict(receipt=receipt, path=expected['path'],
            exact=all(observed[k] == expected[k] for k in ('size', 'sha256'))))

results, derived, conflicts, anchors = runtime.verify_all()
assert len(results) == 90 and all(r['exact'] for r in results) and not conflicts
data_results = runtime.verify_data(results, derived)
startup_data = [r for r in data_results if r['member'].lower() in
               {'dos\\crt0.asm','dos\\crt0dat.asm','dos\\crt0msg.asm','dos\\nmsghdr.asm','crt0fp.asm'}]
assert all(r['exact'] for r in startup_data)
assert set(derived['ext::_edata:DGROUP']) == {0x8b9e}
assert set(derived['ext::_end:DGROUP']) == {0x94f0}
x = exe.load()
sec = x.sections[27]
tail_start = 0x55b30 + 0x8b9d
overlap = [dict(seg=seg, off=off) for seg, off in sec.relocs
           if seg * 16 + off < tail_start + 3 and seg * 16 + off + 2 > tail_start]
assert not overlap
assert len(x.image) < tail_start
assert (x.mz.cs, x.mz.ip) == (0x2cff, 0x6f8)
assert (x.mz.ss, x.mz.sp) == (0x5f02, 0x1000)
assert sec.flags == 0x100 and sec.word6 == 0xffff
assert sec.load_linear + len(sec.data) == tail_start + 3

def word(unit, seg, off):
    return int.from_bytes(x.read(unit, seg * 16 + off, 2), 'little')

header_flags = word('root', 0x2cff, 0xb5f)
fatal_slot = struct.unpack('<HH', x.read('root', 0x2cff0 + 0x9c7, 4))
fatal_target = struct.unpack('<HH', x.read('root', fatal_slot[1] * 16 + fatal_slot[0], 4))
assert header_flags == 1
assert (fatal_slot, fatal_target) == ((0x1286, 0x2fb3), (0x1290, 0x2fb3))
assert x.read('root', 0x2cff0 + 0xb63, 8) == bytes(8)
assert word('S27', 0x55b3, 0x7db2) == 0

cs = Cs(CS_ARCH_X86, CS_MODE_16)
def instructions(unit, seg, start, end):
    return [dict(at=f'{seg:04X}:{i.address:04X}', mnemonic=i.mnemonic, operands=i.op_str)
            for i in cs.disasm(x.read(unit, seg * 16 + start, end-start), start)]

static = dict(
    original_identity=x.sha256, original_research_only=True,
    mz_image_bytes=len(x.image), historical_tail_linear=tail_start,
    mz_entry=dict(cs=x.mz.cs, ip=x.mz.ip),
    section27=dict(flags=sec.flags, mem_paras=sec.mem_paras, file_paras=sec.file_paras,
                   relocation_records=len(sec.relocs), tail_relocation_overlap=overlap),
    manager_header_flags=header_flags, fatal_slot=list(fatal_slot), fatal_target=list(fatal_target),
    crt_boundaries=dict(edata=0x8b9e, end=0x94f0, count=0x952,
                        actual_sp=x.mz.sp, actual_stack_top=x.mz.sp+0x94ee),
    excerpts={
        'manager_entry': instructions('root', 0x2cff, 0x6f8, 0x73c),
        'manager_selected_load': instructions('root', 0x2cff, 0x2ad, 0x429),
        'manager_initial_load_selection': instructions('root', 0x2cff, 0x79d, 0x872),
        'manager_default_callback': instructions('root', 0x2cff, 0x1b0, 0x1b2),
        'manager_fatal': instructions('root', 0x2fb3, 0x1290, 0x12e3),
        'crt_startup': instructions('root', 0x29f4, 0x1c, 0xe7),
    })

rd = OmfReader(communals=True)
members = rd.split_library(Path('C:/tools/msc-6.00/LIB/llibcr.lib').read_bytes())
crt_name, crt_blob = next((n,b) for n,b in members if n.lower() == 'dos\\crt0.asm')
crt = rd.read(crt_blob, crt_name)
assert hashlib.sha256(crt_blob).hexdigest() == candidate['member_sha256']

vm_report = json.loads((PACKET / 'stock-crt-controls.json').read_bytes())
spec = importlib.util.spec_from_file_location('tail_probe_reopened', PACKET / 'probe_stock_crt.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
vm_replay = [mod.execute(case, r['poison'], r['dos_version'], r['injected_external_observer'])
             for r in vm_report['runs']
             for case in vm_report['cases']
             if case['name'] == r['name'] and case['linker'] == r['linker']]
assert vm_replay == vm_report['runs']
assert len(vm_replay) == 18
assert [r['observer_output'] for r in vm_replay if r['injected_external_observer']] == [
    ['a5a5'], ['5a5a'], ['a5a5'], ['5a5a']]

fixtures = []
for case in vm_report['cases']:
    directory = Path(case['directory'])
    publics = mod.publics(directory / 'PROBE.MAP')
    raw = (directory / 'PROBE.EXE').read_bytes()
    fields = struct.unpack_from('<13H', raw, 2)
    assert (fields[10], fields[9]) == publics['__astart']
    # Bind every field of the whole genuine CRT from independently generated publics.
    # No fixup is ignored and no source fixture image is modified.
    expected_text = bytearray(crt.segments['_TEXT'])
    crt_seg, crt_off = publics['__astart']
    crt_linear = crt_seg * 16 + crt_off
    dg = publics['_edata'][0]
    segment_offsets = {'_TEXT': crt_off, '_DATA': publics['__atopsp'][1],
                       'DBDATA': publics['___aDBswpflg'][1]}
    expected_relocs = set()
    text_fixups = [f for f in crt.linker_fixups if f['segment'] == '_TEXT']
    for f in text_fixups:
        addend = int.from_bytes(bytes.fromhex(f['encoded_addend']), 'little')
        disp = f.get('displacement') or 0
        if f['target_kind'] == 'external':
            tseg, toff = publics[f['target']]
        elif f['target_kind'] == 'group':
            assert f['target'] == 'DGROUP'
            tseg, toff = dg, 0
        else:
            tseg = crt_seg if f['target'] == '_TEXT' else dg
            toff = segment_offsets[f['target']]
        site = crt_linear + f['offset']
        if f['self_relative']:
            value = (tseg*16 + toff + addend + disp - site - f['width']) & 0xffff
            encoded = struct.pack('<H', value)
        elif f['loc'] == 'base16':
            encoded = struct.pack('<H', (tseg + addend + disp) & 0xffff)
            expected_relocs.add(site)
        elif f['loc'] == 'pointer32':
            encoded = struct.pack('<HH', (toff + (addend & 65535) + disp) & 65535,
                                   (tseg + (addend >> 16)) & 65535)
            expected_relocs.add(site+2)
        else:
            assert f['loc'] == 'offset16'
            encoded = struct.pack('<H', (toff + addend + disp) & 65535)
        expected_text[f['offset']:f['offset']+f['width']] = encoded
    image = raw[fields[3]*16:]
    assert image[crt_linear:crt_linear+len(expected_text)] == expected_text
    actual_relocs = {seg*16+off for off,seg in
                    (struct.unpack_from('<HH', raw, fields[11]+4*i) for i in range(fields[2]))
                    if crt_linear <= seg*16+off < crt_linear+len(expected_text)}
    assert actual_relocs == expected_relocs
    assert (directory / 'FULLRUN.LOG').read_text().strip() == 'PASS'
    fixtures.append(dict(name=case['name'], linker=case['linker'],
        mz_entry=list((fields[10], fields[9])), publics={k:list(publics[k])
        for k in ('__astart', '__cinit', '_main', '_edata', '_end', '_probe')},
        link_log=(directory / 'LINK.LOG').read_text(encoding='latin1'),
        whole_crt_all_fixups_bound=True, whole_crt_relocations_exact=True,
        bound_text_fixups=len(text_fixups), fullrun='PASS'))

out = dict(schema='dos-tail-admission-reopening-v36', root_reviewed=False,
           admitted=False, pin_checks=pin_results, runtime_member_count=len(results),
           retained_receipt_input_checks=retained_checks,
           selected_tool_checks=selected_tool_checks, compiler_profile_verified='msc600ax',
           runtime_all_exact=True, runtime_conflicts=conflicts,
           startup_data_checks=startup_data,
           crt_member=dict(name=crt_name, size=len(crt_blob), sha256=hashlib.sha256(crt_blob).hexdigest(),
               fixups=crt.linker_fixups), static=static, vm_replay_exact=True,
           vm_runs=vm_replay, fixture_checks=fixtures)
(OUT / 'reopened.json').write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8')
print(json.dumps(dict(pins=len(pin_results), runtime_exact=len(results), vm_replayed=len(vm_replay),
    fixture_entries_checked=len(fixtures), crt_member_size=len(crt_blob),
    mz_image_bytes=len(x.image), tail_start=tail_start, section27_relocations=len(sec.relocs),
    manager_header_flags=header_flags, fatal_slot=fatal_slot, fatal_target=fatal_target), indent=2))
