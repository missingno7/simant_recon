"""Read-only current-object census. No compiler, linker or original-image reads."""
import hashlib
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PRIOR = ROOT / 'work/source-only-dos/structural-audits-v29/numeric-frames-v30/dos_numeric_frame_inventory_v30.py'
spec = importlib.util.spec_from_file_location('prior_frame_helpers', PRIOR)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
helper.ROOT = ROOT

def pin(path, expected=None):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if expected is not None:
        assert digest == expected, str(path)
    return dict(path=path.relative_to(ROOT).as_posix(), sha256=digest, size=len(raw))

report_path = ROOT / 'build/source-only-dos/build-report.json'
report = json.loads(report_path.read_bytes())
tus = report['translation_units']
assert len(tus) == 188
assert len(report['unresolved_symbols']) == 15
assert not any(report['original_exe_bytes_used'].values())
objects, object_pins = helper.module_objects(tus)
inputs = [pin(report_path), pin(PRIOR), pin(__file__), pin('tools/omf.py')]
strict = report['semantic_substitutions']
assert len(strict) == 29
for row in strict:
    inputs.append(pin(row['source']['path'], row['source']['sha256']))
source_checks, packet_checks, generated_sites = [], [], []
patterns = {
    'numeric_ss_memory': r'(?i)\bss\s*:\s*\[[^\]]*\b[0-9a-f]{1,4}h\s*\]',
    'literal_mono_base': r'(?i)\badd\s+bx\s*,\s*8ed8h\b',
    'symbolic_mono_base': r'(?i)\badd\s+bx\s*,\s*offset\s+dgroup:_g_8ed8\b',
    'direct_segment_memory': r'(?i)\b(cs|ds|es|ss)\s*:\s*\[\s*[0-9a-f]{1,4}h\s*\]',
    'register_add_immediate': r'(?i)\badd\s+(bx|si|di|bp)\s*,\s*[0-9a-f]{1,4}h\b',
}
for tu in tus:
    for key in ('source', 'generated_source'):
        inputs.append(pin(tu[key]['path'], tu[key]['sha256']))
    for row in (tu.get('source_binding') or {}).get('relocations', []):
        actual = helper.match_relocation(objects[tu['module']], row)
        source_checks.append(dict(module=tu['module'], declared=row, actual=actual))
    if tu['lang'] == 'asm':
        for line, code in helper.source_lines(ROOT / tu['generated_source']['path']):
            for kind, pattern in patterns.items():
                if re.search(pattern, code):
                    generated_sites.append(dict(module=tu['module'], kind=kind,
                        line=line, instruction=code.strip()))

packets = helper.PACKETS + ['mono-base-bindings-v1.json']
for name in packets:
    path = ROOT / 'work/source-only-dos' / name
    inputs.append(pin(path))
    packet = json.loads(path.read_bytes())
    for binding in packet.get('bindings', []):
        module = binding.get('module')
        if module not in objects:
            continue
        obj = objects[module]
        for row in binding.get('relocations', []):
            packet_checks.append(dict(packet=name, module=module,
                kind='relocation', actual=helper.match_relocation(obj, row)))
        for kind in ('reframes', 'local_reframes'):
            for row in binding.get(kind, []):
                fields = ('segment', 'offset', 'target', 'frame_kind', 'frame')
                if kind == 'local_reframes':
                    fields += ('target_kind', 'displacement', 'encoded_addend')
                wanted = {key: row[key] for key in fields}
                found = [f for f in obj.linker_fixups if all(f.get(k) == v for k, v in wanted.items())]
                assert len(found) == 1, (module, wanted, found)
                assert found[0]['loc'] == 'offset16'
                packet_checks.append(dict(packet=name, module=module, kind=kind, actual=found[0]))

counts = {kind: sum(row['kind'] == kind for row in generated_sites) for kind in patterns}
assert counts == dict(numeric_ss_memory=0, literal_mono_base=0,
    symbolic_mono_base=4, direct_segment_memory=51, register_add_immediate=60), counts
mono = objects['S01:328E']
mono_fixups = [f for f in mono.linker_fixups if f['target'] == '_g_8ED8']
assert len(mono_fixups) == 4
assert sorted(f['offset'] for f in mono_fixups) == [14, 161, 304, 473]
for fixup in mono_fixups:
    assert all(fixup.get(key) == value for key, value in dict(loc='offset16',
        width=2, frame_kind='group', frame='DGROUP', encoded_addend='0000').items()), fixup

receipt = dict(schema='simant-current-frame-observation-v33', status='PASS',
    root_reviewed=True, source_or_layout_admitted=False, original_game_bytes_used=0,
    translation_units=188, strict_substitutions=29, unresolved_imports=15, input_pins=inputs,
    object_pins=object_pins, source_binding_checks=source_checks,
    packet_site_checks=packet_checks, generated_operand_counts=counts,
    generated_operand_sites=generated_sites, monochrome_fixups=mono_fixups,
    scope='Current generated ASM operand shapes and declared binding tuples only. '
          'No complete computed-alias, resource-bound, arbitrary numeric expression, '
          'storage-extent or runtime-entry proof. Direct hardware classifications remain '
          'the separately pinned v30 audit; no new hardware interpretation.',
    remaining_gate='UNRESOLVED; owner/extent and unchecked paths stay open')
(OUT / 'current-frames.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps(dict(status='PASS', tus=len(tus), pins=len(inputs) + len(object_pins),
    source_binding_checks=len(source_checks), packet_site_checks=len(packet_checks),
    generated_operand_counts=counts), indent=2))
