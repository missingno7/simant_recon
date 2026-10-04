"""Root reopening, independent fresh objects, preservation and bounded admission."""
from pathlib import Path
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'work/source-only-dos/mono-base-admission-v31'
WORKER = ROOT / 'build/workers/dos_mono_8ed8_owner_v35'
sys.path.insert(0, str(ROOT / 'tools'))
import compiler
import dos_mono_base as policy
import dos_source_bindings as bindings
from omf import OmfReader

def pin(path):
    path = path.resolve()
    try: name = path.relative_to(ROOT).as_posix()
    except ValueError: name = str(path)
    return dict(path=name, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), size=path.stat().st_size)

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(value, indent=2)+'\n').encode()
    if path.exists(): assert path.read_bytes() == raw, str(path)
    else: path.write_bytes(raw)

def nested_pins(value):
    if isinstance(value, dict):
        if 'path' in value and 'sha256' in value and ('size' in value or 'size_bytes' in value):
            yield value
        for v in value.values(): yield from nested_pins(v)
    elif isinstance(value, list):
        for v in value: yield from nested_pins(v)

def model(obj):
    return dict(segment_defs=obj.segment_defs, segment_lengths=obj.segment_lengths, groups=obj.groups,
                externals=obj.externals, external_scopes=obj.external_scopes, publics=obj.publics,
                communals=obj.communals, fixups=obj.linker_fixups,
                segment_bytes={s: obj.segment_bytes(s).hex() for s in obj.segments})

def main():
    assert pin(WORKER/'receipt.json')['sha256'] == 'f32677ae0981b5e2f0bd648c3ee1797a78cc39a037a8d52f96a5fd3714624993'
    receipt = json.loads((WORKER/'receipt.json').read_bytes())
    checked = {}
    for name in ('receipt.json', 'diagnostic-history.json', 'stable-artifact-index.json'):
        for p in nested_pins(json.loads((WORKER/name).read_bytes())):
            actual = pin(ROOT/p['path']) if not Path(p['path']).is_absolute() else pin(Path(p['path']))
            assert actual['sha256'] == p['sha256'] and actual['size'] == p.get('size', p.get('size_bytes')), p
            checked[actual['path']] = actual
    copied = []
    for version in ('v33', 'v34', 'v35'):
        origin = ROOT/f'build/workers/dos_mono_8ed8_owner_{version}'
        for path in sorted(origin.rglob('*')):
            rel = path.relative_to(origin)
            if not path.is_file() or rel.parts[0] in ('compiler-cache', 'cc', '__pycache__', 'objects'):
                continue
            if path.suffix.lower() not in ('.json', '.py', '.asm', '.c', '.lst', '.log', '.map', '.lnk', '.cfg', '.bat', '.conf', '.bin'):
                continue
            if path.suffix.lower() == '.bin': assert path.name == 'OBS.BIN' and path.stat().st_size == 1
            target = OUT/version/rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists(): assert target.read_bytes() == path.read_bytes(), str(target)
            else: target.write_bytes(path.read_bytes())
            copied.append(dict(original=pin(path), preserved=pin(target)))
    binding = dict(module='S01:328E', source='src/S01/m328E.asm', source_sha256=policy.SOURCE_SHA,
                   mono_base_operands=True, edits=policy.EDITS, exports=[], relocations=[policy.RELOCATION])
    root_old = ROOT/'build/workers/dos_mono_base_root_v30'
    objects = {n: OmfReader(communals=True).read((root_old/n/'module.obj').read_bytes())
               for n in ('original', 'positive', 'wrong_frame', 'wrong_target', 'incomplete_sites', 'changed_loop', 'extra_storage')}
    proof = bindings.verify_objects(objects['original'], objects['positive'], binding)
    for case, obj in objects.items():
        for filename in ('module.asm', 'compile.log'):
            source, dest = root_old/case/filename, OUT/'root-whole-tu'/case/filename
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists(): assert dest.read_bytes() == source.read_bytes()
            else: dest.write_bytes(source.read_bytes())
            copied.append(dict(original=pin(source), preserved=pin(dest)))
        result = dict(object=pin(root_old/case/'module.obj'), actual_model=model(obj))
        if case not in ('original', 'positive'):
            try: bindings.verify_objects(objects['original'], obj, binding)
            except ValueError as error: result['root_expected_rejection'] = str(error)
            else: raise AssertionError(case)
        write(OUT/'root-whole-tu'/case/'object-model.json', result)
    # These fixture recipes are independent root literals, not the candidate packet.
    sources = {'owner': ('RUNTIME_OWNER', policy.OWNER_SOURCE),
               'crt': ('RUNTIME_CRT', 'extern void far FrameProbe(void);\nint main(void) { FrameProbe(); return 0; }\n')}
    sources.update({v: ('CHECK_'+v, policy.checker_source(v)) for v in policy.EXPECTED})
    source_pins, fixture_models = {}, {}
    for name, (label, expected) in sources.items():
        extension = 'C' if name == 'crt' else 'ASM'
        source = WORKER/'sources'/f'{label}.{extension}'
        assert source.read_text(encoding='ascii').split() == expected.split()
        source_pins[name] = pin(OUT/'v35/sources'/source.name)
        actual = OmfReader(communals=True).read((WORKER/'objects'/f'{label}.OBJ').read_bytes())
        if name == 'crt':
            run = compiler.compile_c(expected, 'msc600ax', ['/AL', '/Os', '/Zi'], basename=label[:8])
        else:
            run = compiler.assemble(expected, 'masm510', ['/Mx', '/L'], basename=label[:8])
        assert run.ok, run.log
        fresh = OmfReader(communals=True).read(run.obj)
        assert model(fresh) == model(actual), name
        dest = OUT/'root-fixture'/f'{name}-object-model.json'
        write(dest, dict(actual_model=model(actual), independently_recompiled_equal=True,
                         worker_object=pin(WORKER/'objects'/f'{label}.OBJ'),
                         root_object=dict(sha256=hashlib.sha256(run.obj).hexdigest(), size=len(run.obj)),
                         source=source_pins[name]))
        fixture_models[name] = pin(dest)
    cases = []
    for row in receipt['runtime_fixture']['cases']:
        directory = WORKER/'runtime'/row['linker']/row['variant']
        archived = OUT/'v35/runtime'/row['linker']/row['variant']
        observed = (directory/'OBS.BIN').read_bytes()
        assert observed == bytes.fromhex(policy.EXPECTED[row['variant']])
        assert (directory/'RUN.LOG').read_bytes() == b'EXECUTED\r\n'
        log = (directory/'LINK.LOG').read_text(encoding='latin1')
        assert not re.search(r'\bwrt\d{4}\b|\b(?:warnings?|errors?|fatal|undefined|unresolved|aborted)\b|cannot\s+open', log, re.I)
        mapping = policy.parse_map((directory/'LOCAL.MAP').read_text(encoding='latin1'))
        assert (directory/'LOCAL.EXE').read_bytes()[:2] == b'MZ'
        for filename, label in [('CHECK.OBJ', 'CHECK_'+row['variant']), ('OWNER.OBJ', 'RUNTIME_OWNER'), ('CRT.OBJ', 'RUNTIME_CRT')]:
            assert (directory/filename).read_bytes() == (WORKER/'objects'/f'{label}.OBJ').read_bytes()
        cases.append(dict(linker=row['linker'], variant=row['variant'], expected=policy.EXPECTED[row['variant']],
                          actual=observed.hex(), passed=True, dosbox_exit=0, root_map=mapping,
                          executable_observation=pin(directory/'LOCAL.EXE'),
                          raw={key: pin(archived/filename) for key, filename in
                               [('observation', 'OBS.BIN'), ('map', 'LOCAL.MAP'), ('run_log', 'RUN.LOG'), ('link_log', 'LINK.LOG')]}))
    inputs = [pin(OUT/'v35'/n) for n in ('receipt.json', 'diagnostic-history.json', 'stable-artifact-index.json')]
    inputs += list(source_pins.values()) + list(fixture_models.values())
    inputs += [r['preserved'] for r in copied]
    inputs += [pin(p) for p in OUT.glob('root-whole-tu/*/object-model.json')]
    for rel in ('mono-entry-ss-v32/receipt.json', 'mono-entry-ss-v32/correction-addendum-v1.json', 'root-frontier-review.json'):
        inputs.append(pin(ROOT/'work/source-only-dos/structural-audits-v30'/rel))
    inputs.append(pin(ROOT/'src/S01/m328E.asm'))
    tc = compiler.toolchain()
    for profile in ('masm510', 'msc600ax'):
        p = tc['profiles'][profile]
        inputs.extend(pin(Path(p['directory'])/n) for n in p['files'])
    for linker in ('rtlink400', 'rtlink610'):
        t = tc['linkers'][linker]
        inputs.extend(pin(Path(t['directory'])/n) for n in t['files'])
    manifest = json.loads((ROOT/'layout/manifest.json').read_bytes())
    inputs.extend(pin(Path(v['path'])) for v in manifest['runtime']['libraries'].values())
    inputs.append(pin(Path(tc['runners']['dosbox-x']['path'])))
    inputs.append(pin(HERE/'admit.py'))
    # The scratch mechanics pin is replaced by its final identical preserved copy.
    mechanics = OUT/'root-mechanics/admit.py'
    mechanics.parent.mkdir(exist_ok=True)
    mechanics.write_bytes((HERE/'admit.py').read_bytes())
    inputs[-1] = pin(mechanics)
    unique = {p['path']: p for p in inputs}
    contract = dict(schema='simant-mono-symbolic-base-contract-v31', root_reviewed=True,
                    all_required_checks_pass=True, storage_provider=False, owner_extent=None, game_execution=False,
                    required_cases=policy.EXPECTED, fixture_sources=source_pins, fixture_models=fixture_models,
                    whole_tu_proof=proof, negative_object_controls=['wrong_frame', 'wrong_target', 'incomplete_sites', 'changed_loop', 'extra_storage'],
                    inputs=list(unique.values()), cases=cases, probe_source=pin(OUT/'v35/relocation-probe.py'),
                    scope_limit='Four symbolic references only. No game owner, extent, index bound, final game link or execution.')
    write(ROOT/'work/source-only-dos/mono-base-contract-v1.json', contract)
    packet = dict(schema='simant-mono-symbolic-base-bindings-v1', category='REVIEWED_SOURCE_LINK_BINDING',
                  scope=contract['scope_limit'], runtime_contract_key='mono_base_contract',
                  runtime_contract=pin(ROOT/'work/source-only-dos/mono-base-contract-v1.json'),
                  review_sources=contract['inputs'], bindings=[binding])
    write(ROOT/'work/source-only-dos/mono-base-bindings-v1.json', packet)
    test_report = dict(translation_units=[dict(module='S01:328E', source_binding=binding)],
                       mono_base_contract=contract, runtime_components=list(manifest['runtime']['libraries'].values()))
    for linker in ('rtlink400', 'rtlink610'): policy.require_contract(test_report, linker, tc['linkers'][linker])
    write(OUT/'root-review.json', dict(root_reviewed=True, scope=contract['scope_limit'],
                                     raw_worker_identities_reopened=len(checked), archived_files=copied,
                                     independent_whole_tu=proof, independent_fresh_fixture_objects=fixture_models,
                                     runtime_cases=cases, contract=pin(ROOT/'work/source-only-dos/mono-base-contract-v1.json')))
    print('ROOT MONO BASE PASS:', len(checked), 'identities; six independent fixture objects; eight raw runtime/map cases; no owner extent')

if __name__ == '__main__': main()
