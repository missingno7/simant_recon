"""Replay the current canonical source-owned code-address proof.

Run after installing at evidence/canonical/owned-code-addresses/replay.py:
  python evidence/canonical/owned-code-addresses/replay.py --out build/scratch/owned-code-address-proof

This runner reads current canonical sources, derives literal-address negatives
only in whole test-owned copies, and uses pinned MASM/RTLink/DOSBox tools.
All generated files are constrained beneath build/. It never reads the original
game image or changes canonical source, inventory, evidence, or layout metadata.
"""
from __future__ import annotations
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile

def find_root():
    for candidate in Path(__file__).resolve().parents:
        if (candidate / 'layout/toolchain.json').is_file():
            return candidate
    raise RuntimeError('Cannot locate repository root via layout/toolchain.json')

ROOT = find_root()
OUT = None
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
from tools import compiler
from tools.omf import OmfReader

MODULES = {
    'M00': {'key': 'S00:31AD', 'source': 'src/S00/m31AD.asm', 'segment': 'S00B_TEXT',
            'first_public': '_o00_31AD_0004', 'first_offset': 0, 'historical_origin': 4,
            'callbacks': [('o00_31AD_0004', '1Ch', '_o00_31AD_001C'),
                          ('o00_31AD_0122', '13Ah', '_o00_31AD_013A'),
                          ('o00_31AD_037C', '394h', '_o00_31AD_0394'),
                          ('o00_31AD_16A9', '16C1h', 'L16C1'),
                          ('o00_31AD_16E4', '16FCh', '_o00_31AD_16FC')]},
    'M01': {'key': 'S01:3126', 'source': 'src/S01/m3126.asm', 'segment': 'S01A_TEXT',
            'first_public': '_o01_3126_0000', 'first_offset': 0, 'historical_origin': 0,
            'callbacks': [('o01_3126_024C', '264h', 'L0264')]},
    'M02': {'key': 'S02:3126', 'source': 'src/S02/m3126.asm', 'segment': 'S02A_TEXT',
            'first_public': '_o02_3126_0000', 'first_offset': 0, 'historical_origin': 0,
            'callbacks': [('o02_3126_0096', '0AEh', '_o02_3126_00AE'),
                          ('o02_3126_0185', '19Dh', '_o02_3126_019D'),
                          ('o02_3126_027C', '294h', 'L0294')]},
    'M03': {'key': 'S03:3126', 'source': 'src/S03/m3126.asm', 'segment': 'S03A_TEXT',
            'first_public': '_o03_3126_0140', 'first_offset': 320, 'historical_origin': 0,
            'callbacks': [('o03_3126_01F8', '210h', '_o03_3126_0210'),
                          ('o03_3126_03C2', '3DAh', '_o03_3126_03DA'),
                          ('o03_3126_059C', '5B4h', 'L05B4')]},
    'M3C': {'key': 'S03:3258', 'source': 'src/S03/m3258.asm', 'segment': 'S03C_TEXT',
            'first_public': '_o03_3258_040C', 'first_offset': 1024, 'historical_origin': 12,
            'callbacks': []},
}
LEA_REVERSIONS = {
    'M03': [('di', 'linebuf', 'ds:[0]', 2), ('si', 'linebuf', 'ds:[0]', 2)],
    'M3C': [('dx', 'xlat_tabs', 'ds:[0Ch]', 2),
            ('bx', 'xlat_tabs+512', 'ds:[20Ch]', 2),
            ('bx', 'xlat_tabs+256', 'ds:[10Ch]', 2),
            ('bx', 'xlat_tabs+768', 'ds:[30Ch]', 2)],
}
PEER = {'key': 'S00:31AD@2AB4', 'source': 'src/S00/m31AD_2AB4.asm',
        'segment': 'S00B_TEXT', 'first_public': '_o00_31AD_2AB4'}

def select_output(argument):
    build = (ROOT / 'build').resolve()
    try:
        build.relative_to(ROOT.resolve())
    except ValueError:
        raise ValueError('Repository build directory resolves outside the repository')
    if argument is None:
        parent = (build / 'scratch' / 'proofs').resolve()
        try:
            parent.relative_to(build)
        except ValueError:
            raise ValueError('Default proof directory resolves outside repository build/')
        parent.mkdir(parents=True, exist_ok=True)
        return Path(tempfile.mkdtemp(prefix='owned-code-addresses-', dir=parent))
    output = (ROOT / argument).resolve()
    try:
        output.relative_to(build)
    except ValueError:
        raise ValueError('--out must resolve to a subdirectory beneath repository build/')
    if output == build:
        raise ValueError('--out must be a subdirectory, not build/ itself')
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError('--out must be absent or an empty directory; prior receipts are preserved')
    output.mkdir(parents=True, exist_ok=True)
    return output

def derive_negative(token, canonical):
    negative = canonical
    recipe = []
    for register, symbolic, literal, expected_count in LEA_REVERSIONS.get(token, []):
        expression = r'(?m)^([ \t]*lea[ \t]+' + register + r',[ \t]*)' + re.escape(symbolic) + r'([ \t]*(?:;[^\n]*)?)$'
        negative, count = re.subn(expression, lambda m: m.group(1) + literal + m.group(2), negative)
        if count != expected_count:
            raise ValueError(f'{MODULES[token]["source"]}: expected {expected_count} LEAs of '
                             f'{symbolic}, found {count}')
        recipe.append({'type': 'LEA', 'register': register, 'canonical_operand': symbolic,
                       'negative_operand': literal, 'count': count})
    for wrapper, literal, label in MODULES[token]['callbacks']:
        if not re.search(r'(?m)^' + re.escape(label) + r'(?:[ \t]+proc\b|:)', canonical):
            raise ValueError(f'Existing callback code label absent: {label}')
        expression = r'(?m)^([ \t]*mov[ \t]+ax,[ \t]*)OFFSET[ \t]+' + re.escape(label) + r'([ \t]*(?:;[^\n]*)?)$'
        negative, count = re.subn(expression, lambda m: m.group(1) + literal + m.group(2), negative)
        if count != 1:
            raise ValueError(f'{MODULES[token]["source"]}: expected one OFFSET {label}, found {count}')
        recipe.append({'type': 'far_callback', 'wrapper': wrapper, 'target_label': label,
                       'canonical_operand': 'OFFSET ' + label, 'negative_operand': literal, 'count': count})
    return ('; TEST-OWNED NEGATIVE: whole source; only reviewed owned-code operands reverted.\n'
            + negative), recipe

def stage_current_modules():
    inputs = []
    for token, metadata in MODULES.items():
        origin = ROOT / metadata['source']
        raw = origin.read_bytes()
        canonical = raw.decode('ascii').replace('\r\n', '\n').replace('\r', '\n')
        negative, recipe = derive_negative(token, canonical)
        newpath = write_source('NEW' + token, canonical)
        oldpath = write_source('OLD' + token, negative)
        inputs.append({'module': metadata['key'], 'canonical_source': pin(origin, raw),
                       'positive_source': pin(newpath), 'negative_source': pin(oldpath),
                       'negative_recipe': recipe})
    return inputs

def stage_peer():
    origin = ROOT / PEER['source']
    raw = origin.read_bytes()
    staged = write_source('PEER', raw.decode('ascii').replace('\r\n', '\n').replace('\r', '\n'))
    return {'module': PEER['key'], 'canonical_source': pin(origin, raw),
            'unchanged_peer_source': pin(staged)}

def pin(path, raw=None):
    path = Path(path)
    if raw is None:
        raw = path.read_bytes()
    try:
        name = str(path.relative_to(ROOT)).replace('\\', '/')
    except ValueError:
        name = str(path)
    return {'path': name, 'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)}

def write_source(name, source):
    path = OUT / 'sources' / (name + '.asm')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(source.replace('\r\n', '\n').replace('\n', '\r\n').encode('ascii'))
    return path

def assemble(name, path):
    result = compiler.assemble(path.read_text(), 'masm510', flags=['/Mx'], basename=name, keep=True)
    (OUT / 'objects').mkdir(exist_ok=True)
    (OUT / 'objects' / (name + '.LOG')).write_text(result.log)
    if not result.ok:
        raise RuntimeError(result.log)
    objpath = OUT / 'objects' / (name + '.OBJ')
    objpath.write_bytes(result.obj)
    return OmfReader().read(result.obj, name)

def compare_module(name, old, new, expected_sites):
    structure = {field: getattr(old, field) == getattr(new, field) for field in
                 ('segment_lengths', 'segment_defs', 'publics', 'groups',
                  'externals', 'local_publics', 'local_externals', 'communals')}
    old_keys = {(f['segment'], f['offset']) for f in old.linker_fixups}
    added = [f for f in new.linker_fixups if (f['segment'], f['offset']) not in old_keys]
    retained = [f for f in new.linker_fixups if (f['segment'], f['offset']) in old_keys]
    assert len(added) == expected_sites, (name, added)
    assert retained == old.linker_fixups, name
    assert all(structure.values()), (name, structure)
    assert all(f['width'] == 2 and f['loc'] == 'offset16' and not f['self_relative'] and
               f['target_kind'] == 'segment' and f['target'] == f['segment'] and
               f['frame'] == f['segment'] for f in added), added
    allowed = {(f['segment'], f['offset'] + n) for f in added for n in (0, 1)}
    differences = []
    for seg in old.segments:
        before, after = bytes(old.segments[seg]), bytes(new.segments[seg])
        assert len(before) == len(after)
        for at, (a, b) in enumerate(zip(before, after)):
            if a != b:
                assert (seg, at) in allowed, (name, seg, at)
                differences.append({'segment': seg, 'offset': at, 'before': a, 'after': b})
    report = {'structure': structure, 'code_and_data_lengths': new.segment_lengths,
              'public_count': len(new.publics), 'old_fixup_count': len(old.linker_fixups),
              'new_fixup_count': len(new.linker_fixups), 'added_self_offset_fixups': added,
              'retained_fixups_identical_in_order': True, 'raw_byte_changes': differences,
              'all_other_code_and_data_bytes_identical': True, 'passed': True}
    return report, sorted(added, key=lambda f: f['offset'])

def pub(obj, name):
    return next(p for p in obj.publics if p['name'] == name)

def build_sites(token, obj, added):
    metadata = MODULES[token]
    assert pub(obj, metadata['first_public'])['offset'] == metadata['first_offset']
    by_offset = {f['offset']: f for f in added}
    callbacks = {}
    payload = obj.segment_bytes(metadata['segment'])
    for wrapper, literal, label in metadata['callbacks']:
        wrapper_pub = pub(obj, '_' + wrapper)
        at = wrapper_pub['offset'] + 12
        fixup = by_offset[at]
        seg_at = wrapper_pub['offset'] + 8
        seg_fixup = next(f for f in obj.linker_fixups if f['segment'] == metadata['segment'] and f['offset'] == seg_at)
        assert seg_fixup['loc'] == 'base16' and seg_fixup['width'] == 2
        assert seg_fixup['target_kind'] == 'segment' and seg_fixup['target'] == metadata['segment']
        assert seg_fixup['frame'] == metadata['segment']
        assert payload[at-1] == 0xB8 and payload[at+2] == 0x50
        assert payload[seg_at-1] == 0xB8 and payload[seg_at+2] == 0x50
        target_offset = int.from_bytes(payload[at:at+2], 'little') + fixup['displacement']
        assert target_offset == int(literal[:-1], 16) - metadata['historical_origin']
        assert target_offset - wrapper_pub['offset'] == 24
        target_pub = next((p for p in obj.publics if p['name'] == label), None)
        if target_pub is None:
            target_pub, delta = wrapper_pub, 24
        else:
            assert target_pub['offset'] == target_offset
            delta = 0
        assert target_pub['segment'] == metadata['segment']
        callbacks[at] = {'type': 'far_callback', 'target_label': label,
                         'target_public': target_pub['name'], 'target_public_delta': delta,
                         'segment_function_delta': 8, 'segment_fixup': seg_fixup}
    sites = []
    for fixup in added:
        at = fixup['offset']
        preceding = max((p for p in obj.publics if p['segment'] == metadata['segment'] and p['offset'] <= at),
                        key=lambda p: p['offset'])
        item = {'module': metadata['key'], 'token': token, 'code_segment': metadata['segment'],
                'object_operand_offset': at, 'function': preceding['name'],
                'function_delta': at - preceding['offset'], 'offset_fixup': fixup}
        if at in callbacks:
            item.update(callbacks[at])
            assert item['function_delta'] == 12
        else:
            assert token in LEA_REVERSIONS
            table_offset = int.from_bytes(payload[at:at+2], 'little') + fixup['displacement']
            item.update({'type': 'LEA', 'target_label': 'linebuf' if token == 'M03' else 'xlat_tabs',
                         'target_public': metadata['first_public'],
                         'target_public_delta': table_offset - metadata['first_offset']})
        sites.append(item)
    return sites

def checker(sites):
    publics = sorted({s['function'] for s in sites} | {s['target_public'] for s in sites})
    lines = ['; Fixture reads actual linked operands in complete game source objects.',
             '; No game procedure or test provider is called.']
    lines += [f'extrn {name}:far' for name in publics]
    lines += ["CHECK_STACK segment para stack 'STACK'", 'dw 128 dup (?)', 'CHECK_STACK ends',
             "CHECK_TEXT segment para public 'CODE'", 'assume cs:CHECK_TEXT',
             'public CheckStart', 'CheckStart:', 'xor di,di']
    for i, site in enumerate(sites):
        lines += [f'mov ax,seg {site["function"]}', 'mov es,ax', f'mov bx,offset {site["function"]}']
        if site['type'] == 'far_callback':
            lines += [f'mov ax,word ptr es:[bx+{site["segment_function_delta"]}]',
                      f'mov dx,seg {site["target_public"]}', 'cmp ax,dx',
                      f'je short SegmentNext{i}', 'inc di', f'SegmentNext{i}:']
        lines += [f'mov ax,word ptr es:[bx+{site["function_delta"]}]',
                  f'mov dx,offset {site["target_public"]}',
                  f'add dx,{site["target_public_delta"]}', 'cmp ax,dx',
                  f'je short OffsetNext{i}', 'inc di', f'OffsetNext{i}:']
    lines += ['mov ax,di', 'mov ah,4Ch', 'int 21h', 'CHECK_TEXT ends', 'end CheckStart']
    return '\n'.join(lines) + '\n'

def provider(objects):
    defined = {p['name'] for obj in objects for p in obj.publics}
    needed = set().union(*(set(obj.externals) for obj in objects)) - defined
    far = sorted(n for n in needed if n.startswith('_f_') or n.startswith('_o'))
    data = sorted(needed - set(far))
    lines = ['; Fixture-only boundaries for unexecuted external game references.',
             "_DATA segment word public 'DATA'"]
    for n in data:
        lines += [f'public {n}', f'{n} db 16 dup (0)']
    lines += ['_DATA ends', 'DGROUP group _DATA', "BOUND_TEXT segment word public 'CODE'"]
    for n in far:
        lines += [f'public {n}', f'{n} proc far', 'retf', f'{n} endp']
    lines += ['BOUND_TEXT ends', 'end']
    return '\n'.join(lines) + '\n'

def prefix(origins):
    lines = ['; Test-owned aligned contributions control linked frame offsets.']
    for token, metadata in MODULES.items():
        segment, size = metadata['segment'], origins[token]
        lines.append(f"{segment} segment para public 'CODE'")
        if size:
            lines.append(f'dw {size // 2} dup (0)')
        lines.append(f'{segment} ends')
    lines += ['end']
    return '\n'.join(lines) + '\n'

def mz_image(raw):
    assert raw[:2] == b'MZ'
    header_size = struct.unpack_from('<H', raw, 8)[0] * 16
    count, table = struct.unpack_from('<H', raw, 6)[0], struct.unpack_from('<H', raw, 24)[0]
    entries = [list(struct.unpack_from('<HH', raw, table + i * 4)) for i in range(count)]
    assert table + count * 4 <= header_size
    return raw[header_size:], entries

def parse_map(text):
    return {name: {'segment': int(seg, 16), 'offset': int(off, 16)}
            for seg, off, name in re.findall(r'^\s*([0-9A-F]{4}):([0-9A-F]{4})\s+(\S+)\s*$', text, re.M)}

def run_case(case, linker, variant, specs, sites, tools_dir):
    tool = compiler.toolchain()['linkers'][linker]
    runner = compiler.toolchain()['runners'][tool['runner']]
    directory = OUT / 'links' / linker / f'{case}_{variant}'
    directory.mkdir(parents=True, exist_ok=True)
    for name in ('PROBE.EXE', 'PROBE.MAP', 'LINK.LOG', 'RUN.LOG'):
        (directory / name).unlink(missing_ok=True)
    names = [case, variant + 'M00', 'PEER'] + [variant + token for token in MODULES if token != 'M00'] + ['BOUND', 'CHECK']
    for name in names:
        shutil.copyfile(OUT / 'objects' / (name + '.OBJ'), directory / (name + '.OBJ'))
    lines = ['OUTPUT PROBE', 'MAP = PROBE S,N,A,L', 'NODEFLIB',
             'FILE ' + ', '.join(names)]
    (directory / 'PROBE.LNK').write_bytes(('\r\n'.join(lines) + '\r\n').encode('ascii'))
    (directory / 'RTLINK.CFG').write_bytes(b'SYNTAX = FREEFORMAT\r\n')
    batch = (f'@echo off\r\nD:\\{tool["executable"]} @PROBE.LNK < NUL > LINK.LOG\r\n'
             'if not exist PROBE.EXE goto noexe\r\nPROBE.EXE\r\n'
             'if errorlevel 1 goto fail\r\necho PASS > RUN.LOG\r\ngoto done\r\n'
             ':fail\r\necho FAIL > RUN.LOG\r\ngoto done\r\n'
             ':noexe\r\necho NOEXE > RUN.LOG\r\n:done\r\n')
    (directory / 'RUN.BAT').write_bytes(batch.encode('ascii'))
    config = []
    for section, settings in runner['conf'].items():
        config += ['[' + section + ']'] + [f'{k}={v}' for k, v in settings.items()]
    config += ['[autoexec]', f'mount c "{directory}"', f'mount d "{tools_dir}" -ro',
               'c:', 'set LIB=C:\\;D:\\', 'call RUN.BAT', 'exit']
    conf = directory / 'dosbox.conf'
    conf.write_text('\n'.join(config) + '\n')
    process = subprocess.run([runner['path'], '-conf', str(conf), '-fastlaunch', '-exit', '-nomenu'],
          cwd=directory, env={**os.environ, 'SDL_VIDEODRIVER': 'dummy', 'SDL_AUDIODRIVER': 'dummy'},
          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60,
          creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    log = (directory / 'LINK.LOG').read_text(encoding='latin1')
    assert process.returncode == 0, (case, linker, process.returncode)
    assert not re.search(r'\bwrt\d{4}\b|\b(?:warnings?|errors?|fatal|undefined|unresolved|aborted)\b|cannot\s+open', log, re.I), log
    raw = (directory / 'PROBE.EXE').read_bytes()
    image, mz_entries = mz_image(raw)
    mz_linear_locations = {segment * 16 + offset for offset, segment in mz_entries}
    map_text = (directory / 'PROBE.MAP').read_text(encoding='latin1')
    maps = parse_map(map_text)
    segment_starts = {name: int(start, 16) for start, name in
                      re.findall(r'^\s*([0-9A-F]+)H\s+[0-9A-F]+H\s+[0-9A-F]+H\s+(\S+)\s+CODE', map_text, re.M)}
    origins = {}
    for token, metadata in MODULES.items():
        anchor = maps[metadata['first_public']]
        origin = anchor['offset'] - metadata['first_offset']
        assert origin == specs[token], (case, token, origin)
        assert segment_starts[metadata['segment']] % 16 == 0
        assert anchor['segment'] * 16 == segment_starts[metadata['segment']]
        origins[metadata['key']] = origin
    first = maps[MODULES['M00']['first_public']]
    peer = maps[PEER['first_public']]
    first_size = 10927
    expected_peer_offset = (first['offset'] + first_size + 1) & ~1
    assert peer['segment'] == first['segment']
    assert peer['offset'] == expected_peer_offset, (case, first, peer)
    fill_linear = first['segment'] * 16 + first['offset'] + first_size
    assert image[fill_linear] == 0
    concatenation = {'first_module': MODULES['M00']['key'], 'first_address': first,
                     'first_code_size': first_size, 'peer_module': PEER['key'],
                     'peer_address': peer, 'peer_code_size': PEER['code_size'], 'same_linked_frame': True,
                     'link_fill_bytes': 1, 'link_fill_zero': True,
                     'expected_peer_offset': expected_peer_offset, 'passed': True}
    operands = []
    for site in sites:
        address = maps[site['function']]
        linear = address['segment'] * 16 + address['offset'] + site['function_delta']
        target = maps[site['target_public']]
        actual_offset = struct.unpack_from('<H', image, linear)[0]
        expected_offset = target['offset'] + site['target_public_delta']
        item = {**site, 'linked_operand_linear': linear, 'linked_OFFSET': actual_offset,
                'expected_OFFSET': expected_offset, 'offset_matches': actual_offset == expected_offset}
        if site['type'] == 'far_callback':
            seg_linear = address['segment'] * 16 + address['offset'] + site['segment_function_delta']
            actual_segment = struct.unpack_from('<H', image, seg_linear)[0]
            assert seg_linear in mz_linear_locations, ('callback SEG lacks MZ relocation', site)
            assert actual_segment == target['segment'], ('callback SEG identity failed', site)
            item.update({'linked_segment_operand_linear': seg_linear, 'linked_SEG': actual_segment,
                         'expected_SEG': target['segment'], 'segment_matches': True,
                         'segment_MZ_relocation_present': True})
        item['matches'] = item['offset_matches'] and item.get('segment_matches', True)
        operands.append(item)
    matches = all(s['matches'] for s in operands)
    mismatching_count = sum(not s['matches'] for s in operands)
    mismatching_by_type = {kind: sum(not site['matches'] for site in operands if site['type'] == kind)
                          for kind in ('LEA', 'far_callback')}
    expected_mismatches = 0 if variant == 'NEW' else {'ZERO': 13, 'HIST': 0, 'MOVE': 24}[case]
    assert mismatching_count == expected_mismatches, (case, variant, operands)
    result = (directory / 'RUN.LOG').read_text().strip()
    assert result == ('PASS' if matches else 'FAIL'), (case, result, matches)
    if variant == 'NEW':
        assert matches
    else:
        assert matches == (case == 'HIST')
    print(f'{linker} {case} {variant}: origins={origins} runtime={result}', flush=True)
    return {'linker': linker, 'case': case, 'variant': variant, 'contribution_origins': origins,
            'test_prefix_bytes': {MODULES[token]['segment']: size for token, size in specs.items()},
            'linked_segment_starts': segment_starts,
            'S00_same_name_concatenation': concatenation,
            'runtime_result': result, 'expected_runtime_result': 'PASS' if matches else 'FAIL',
            'mismatching_operands': mismatching_count,
            'mismatching_by_type': mismatching_by_type,
            'actual_linked_operands': operands, 'MZ_relocation_entries': mz_entries, 'passed': True,
            'files': [pin(directory / n) for n in ['PROBE.LNK', 'RUN.BAT', 'dosbox.conf',
                      'PROBE.EXE', 'PROBE.MAP', 'LINK.LOG', 'RUN.LOG']]}

def main(argv=None):
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        help='Absent or empty output directory beneath build/ (default: fresh build/scratch/proofs directory)')
    args = parser.parse_args(argv)
    if not __debug__:
        raise RuntimeError('Proof replay requires ordinary Python assertion checks; do not use -O')
    OUT = select_output(args.out)
    compiler.WORK = OUT / 'cc'
    inputs = stage_current_modules()
    peer_input = stage_peer()
    provenance_path = OUT / 'source_inputs.json'
    provenance_path.write_text(json.dumps(inputs, indent=2) + '\n')
    object_names = [variant + token for variant in ('OLD', 'NEW') for token in MODULES]
    objects = {name: assemble(name, OUT / 'sources' / (name + '.asm')) for name in object_names}
    peer_object = assemble('PEER', OUT / 'sources/PEER.asm')
    assert pub(peer_object, PEER['first_public'])['offset'] == 0
    PEER['code_size'] = peer_object.segment_length(PEER['segment'])
    assert objects['NEWM00'].segment_length(PEER['segment']) == 10927
    reviews, sites = {}, []
    for token, metadata in MODULES.items():
        expected_count = len(metadata['callbacks']) + sum(row[3] for row in LEA_REVERSIONS.get(token, []))
        review, added = compare_module(metadata['key'], objects['OLD' + token], objects['NEW' + token], expected_count)
        reviews[metadata['key']] = review
        sites += build_sites(token, objects['NEW' + token], added)
    assert len(sites) == 24
    assert sum(site['type'] == 'far_callback' for site in sites) == 12
    assert sum(site['type'] == 'LEA' for site in sites) == 12
    assemble('CHECK', write_source('CHECK', checker(sites)))
    assemble('BOUND', write_source('BOUND', provider([objects['NEW' + token] for token in MODULES] + [peer_object])))
    historical = {token: metadata['historical_origin'] for token, metadata in MODULES.items()}
    cases = {'ZERO': {token: 0 for token in MODULES}, 'HIST': historical,
             'MOVE': {token: origin + 32 for token, origin in historical.items()}}
    for case, specs in cases.items():
        assemble(case, write_source(case, prefix(specs)))
    tc = compiler.toolchain()
    toolpins = []
    masm = compiler.verify_profile('masm510')
    toolpins += [pin(Path(masm['directory']) / p) for p in masm['files']]
    toolpins.append(pin(tc['runner']['path']))
    tool_dirs = {}
    for linker in ('rtlink400', 'rtlink610'):
        tool = tc['linkers'][linker]
        for name, sha in tool['files'].items():
            p = pin(Path(tool['directory']) / name)
            assert p['sha256'] == sha
            toolpins.append(p)
        r = tc['runners'][tool['runner']]
        p = pin(r['path'])
        assert p['sha256'] == r['sha256']
        toolpins.append(p)
        tool_dirs[linker] = compiler.pinned_tree(tool)
    jobs = [(case, linker, variant, specs, sites, tool_dirs[linker])
            for linker in ('rtlink400', 'rtlink610') for case, specs in cases.items()
            for variant in ('OLD', 'NEW')]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda args: run_case(*args), jobs))
    pair_comparisons = []
    for linker in ('rtlink400', 'rtlink610'):
        for case in cases:
            old = next(row for row in results if (row['linker'], row['case'], row['variant']) == (linker, case, 'OLD'))
            new = next(row for row in results if (row['linker'], row['case'], row['variant']) == (linker, case, 'NEW'))
            assert old['MZ_relocation_entries'] == new['MZ_relocation_entries']
            old_dir, new_dir = OUT / 'links' / linker / (case + '_OLD'), OUT / 'links' / linker / (case + '_NEW')
            old_image, _ = mz_image((old_dir / 'PROBE.EXE').read_bytes())
            new_image, _ = mz_image((new_dir / 'PROBE.EXE').read_bytes())
            assert len(old_image) == len(new_image)
            allowed = {site['linked_operand_linear'] + delta for site in new['actual_linked_operands'] for delta in (0, 1)}
            changed = [at for at, (a, b) in enumerate(zip(old_image, new_image)) if a != b]
            assert all(at in allowed for at in changed), (linker, case, changed)
            pair_comparisons.append({'linker': linker, 'case': case,
                                     'entire_MZ_relocation_set_and_order_identical': True,
                                     'all_other_linked_code_and_data_bytes_identical': True,
                                     'changed_OFFSET_operand_bytes': changed, 'passed': True})
    report = {'schema': 'simant-owned-code-address-current-proof-v1',
              'scope': 'Twenty-four owned-code offsets in five complete primary assembly TUs, linked with the unchanged same-name second S00 TU: twelve code-data LEAs and twelve far callbacks passed to the synchronous rectangle clipper. Real-linker fixtures inspect actual linked operands at runtime; callback SEG/OFFSET identity is checked against existing PUBDEFs plus reviewed deltas and each SEG retains its MZ relocation. No game procedure or provider stub executes. This is not a full DOS game link, standalone game execution, assembly admission, storage proof, or historical-linker-version claim.',
              'original_image_read': False, 'canonical_sources_written': False,
              'output_directory': str(OUT),
              'reproduce': 'python evidence/canonical/owned-code-addresses/replay.py --out build/scratch/owned-code-address-proof-fresh',
              'canonical_source_inputs_and_negative_recipes': inputs, 'unchanged_concatenated_peer': peer_input,
              'whole_object_review': reviews,
              'linker_status': {name: tc['linkers'][name]['status'] for name in tool_dirs},
              'cases': results, 'fixture_pair_comparisons': pair_comparisons, 'all_required_checks_pass': True,
              'input_and_output_pins': [pin(Path(__file__)), pin(ROOT / 'tools/compiler.py'),
                                        pin(ROOT / 'tools/omf.py'), pin(ROOT / 'layout/toolchain.json'),
                                        pin(ROOT / 'src/root/m1D8E.c'),
                                        pin(provenance_path)] + toolpins +
                                      [pin(p) for p in sorted((OUT / 'sources').glob('*.asm'))] +
                                      [pin(p) for p in sorted((OUT / 'objects').glob('*.OBJ'))]}
    receipt = OUT / 'receipt.json'
    receipt.write_text(json.dumps(report, indent=2) + '\n')
    summary = {'schema': 'simant-owned-code-address-current-proof-summary-v1',
               'scope': report['scope'], 'reproduce': report['reproduce'],
               'full_receipt': pin(receipt), 'reproducer': pin(Path(__file__)),
               'canonical_source_inputs_and_negative_recipes': inputs, 'unchanged_concatenated_peer': peer_input,
               'whole_object_review': {
                   module: {k: row[k] for k in ('code_and_data_lengths', 'public_count',
                            'old_fixup_count', 'new_fixup_count',
                            'retained_fixups_identical_in_order',
                            'all_other_code_and_data_bytes_identical', 'passed')}
                   for module, row in reviews.items()},
               'cases': [{k: row[k] for k in ('linker', 'case', 'variant',
                          'contribution_origins', 'test_prefix_bytes',
                          'runtime_result', 'mismatching_operands', 'mismatching_by_type', 'passed')}
                         for row in results],
               'S00_same_name_concatenation': [{k: row[k] for k in ('linker', 'case', 'variant',
                                              'S00_same_name_concatenation')} for row in results],
               'fixture_pair_comparisons': pair_comparisons,
               'site_counts': {'LEA': 12, 'far_callback': 12},
               'negative_controls_derived_from_current_canonical_sources': True, 'all_required_checks_pass': True}
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print('Receipt: ' + str(OUT / 'summary.json'), flush=True)

if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, AssertionError, subprocess.SubprocessError) as error:
        print(f'Proof replay failed: {error}', file=sys.stderr)
        raise SystemExit(1)
