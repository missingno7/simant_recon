"""Replay the current canonical S03 source-owned code-address proof.

Run after installing at evidence/canonical/s03-owned-addresses/replay.py:
  python evidence/canonical/s03-owned-addresses/replay.py --out build/s03-address-proof

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

CANONICAL_MODULES = {
    'A': ROOT / 'src/S03/m3126.asm',
    'C': ROOT / 'src/S03/m3258.asm',
}
LITERAL_REVERSIONS = {
    'A': [('di', 'linebuf', 'ds:[0]', 2), ('si', 'linebuf', 'ds:[0]', 2)],
    'C': [('dx', 'xlat_tabs', 'ds:[0Ch]', 2),
          ('bx', 'xlat_tabs+512', 'ds:[20Ch]', 2),
          ('bx', 'xlat_tabs+256', 'ds:[10Ch]', 2),
          ('bx', 'xlat_tabs+768', 'ds:[30Ch]', 2)],
}

def select_output(argument):
    build = (ROOT / 'build').resolve()
    try:
        build.relative_to(ROOT.resolve())
    except ValueError:
        raise ValueError('Repository build directory resolves outside the repository')
    if argument is None:
        parent = (build / 'proofs').resolve()
        try:
            parent.relative_to(build)
        except ValueError:
            raise ValueError('Default proof directory resolves outside repository build/')
        parent.mkdir(parents=True, exist_ok=True)
        return Path(tempfile.mkdtemp(prefix='s03-owned-addresses-', dir=parent))
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

def derive_negative(letter, canonical):
    negative = canonical
    recipe = []
    for register, symbolic, literal, expected_count in LITERAL_REVERSIONS[letter]:
        expression = r'(?m)^(\s*lea\s+' + register + r',\s*)' + re.escape(symbolic) + r'([ \t]*(?:;[^\n]*)?)$'
        negative, count = re.subn(expression,
                                 lambda m: m.group(1) + literal + m.group(2), negative)
        if count != expected_count:
            raise ValueError(f'{CANONICAL_MODULES[letter]}: expected {expected_count} symbolic LEA '
                             f'{register}, {symbolic} instructions, found {count}')
        recipe.append({'register': register, 'canonical_operand': symbolic,
                       'negative_operand': literal, 'count': count})
    return ('; TEST-OWNED NEGATIVE: whole canonical module with only the reviewed LEA operands reverted.\n'
            + negative), recipe

def stage_current_modules():
    inputs = []
    for letter, origin in CANONICAL_MODULES.items():
        raw = origin.read_bytes()
        canonical = raw.decode('ascii').replace('\r\n', '\n').replace('\r', '\n')
        negative, recipe = derive_negative(letter, canonical)
        newpath = write_source('NEW' + letter, canonical)
        oldpath = write_source('OLD' + letter, negative)
        inputs.append({'module': 'S03:3126' if letter == 'A' else 'S03:3258',
                       'canonical_source': pin(origin, raw), 'positive_source': pin(newpath),
                       'negative_source': pin(oldpath), 'negative_recipe': recipe})
    return inputs

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

def checker(sites):
    publics = sorted({s['function'] for s in sites} | {'_o03_3126_0140', '_o03_3258_040C'})
    lines = ['; Fixture checks actual linked instruction operands in the whole S03 objects.',
             '; It executes no game procedure and does not synthesize any game bytes.',
             'extrn ' + ','.join(p + ':far' for p in publics),
             "CHECK_STACK segment para stack 'STACK'", 'dw 128 dup (?)', 'CHECK_STACK ends',
             "CHECK_TEXT segment para public 'CODE'", 'assume cs:CHECK_TEXT',
             'public CheckStart', 'CheckStart:', 'xor di,di']
    for i, s in enumerate(sites):
        lines += [f'mov ax,seg {s["function"]}', 'mov es,ax',
                  f'mov bx,offset {s["function"]}',
                  f'mov ax,word ptr es:[bx+{s["function_delta"]}]',
                  f'mov dx,offset {s["origin_public"]}',
                  f'sub dx,{s["origin_public_offset"]}',
                  f'add dx,{s["table_offset"]}', 'cmp ax,dx', f'je short CheckNext{i}',
                  'inc di', f'CheckNext{i}:']
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

def prefix(a, c):
    lines = ['; Test-owned contributions change whole-object placement; no game code.']
    for seg, size in [('S03A_TEXT', a), ('S03C_TEXT', c)]:
        lines += [f"{seg} segment word public 'CODE'"]
        if size:
            lines.append(f'dw {size // 2} dup (0)')
        lines.append(f'{seg} ends')
    lines += ['end']
    return '\n'.join(lines) + '\n'

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
    for name in [variant + 'A', variant + 'C', 'CHECK', 'BOUND', case]:
        shutil.copyfile(OUT / 'objects' / (name + '.OBJ'), directory / (name + '.OBJ'))
    lines = ['OUTPUT PROBE', 'MAP = PROBE S,N,A,L', 'NODEFLIB',
             'FILE ' + ', '.join([case, variant + 'A', variant + 'C', 'BOUND', 'CHECK'])]
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
    assert raw[:2] == b'MZ'
    image = raw[struct.unpack_from('<H', raw, 8)[0] * 16:]
    map_text = (directory / 'PROBE.MAP').read_text(encoding='latin1')
    maps = parse_map(map_text)
    segment_starts = {name: int(start, 16) for start, name in
                      re.findall(r'^\s*([0-9A-F]+)H\s+[0-9A-F]+H\s+[0-9A-F]+H\s+(\S+)\s+CODE', map_text, re.M)}
    operands = []
    origins = {}
    for s in sites:
        anchor = maps[s['origin_public']]
        origin = anchor['offset'] - s['origin_public_offset']
        origins[s['module']] = origin
        addr = maps[s['function']]
        linear = addr['segment'] * 16 + addr['offset'] + s['function_delta']
        actual = struct.unpack_from('<H', image, linear)[0]
        expected = origin + s['table_offset']
        operands.append({**s, 'linked_operand': actual, 'expected_own_label_offset': expected,
                         'matches': actual == expected})
    for module, code_seg, prefix_size in [('S03:3126', 'S03A_TEXT', specs[0]),
                                          ('S03:3258', 'S03C_TEXT', specs[1])]:
        origin_public = next(s['origin_public'] for s in sites if s['module'] == module)
        frame = maps[origin_public]['segment'] * 16
        assert origins[module] == segment_starts[code_seg] + prefix_size - frame, (case, origins)
    matches = all(s['matches'] for s in operands)
    mismatching_count = sum(not s['matches'] for s in operands)
    assert mismatching_count == (0 if variant == 'NEW' else
                                 {'ZERO': 8, 'HIST': 0, 'MOVE': 12}[case]), (case, variant, operands)
    result = (directory / 'RUN.LOG').read_text().strip()
    assert result == ('PASS' if matches else 'FAIL'), (case, result, matches)
    if variant == 'NEW':
        assert matches
    else:
        assert matches == (case == 'HIST')
    print(f'{linker} {case} {variant}: origins={origins} runtime={result}', flush=True)
    return {'linker': linker, 'case': case, 'variant': variant, 'contribution_origins': origins,
            'test_prefix_bytes': {'S03A_TEXT': specs[0], 'S03C_TEXT': specs[1]},
            'linked_segment_starts': segment_starts,
            'runtime_result': result, 'expected_runtime_result': 'PASS' if matches else 'FAIL',
            'mismatching_operands': mismatching_count,
            'actual_linked_operands': operands, 'passed': True,
            'files': [pin(directory / n) for n in ['PROBE.LNK', 'RUN.BAT', 'dosbox.conf',
                      'PROBE.EXE', 'PROBE.MAP', 'LINK.LOG', 'RUN.LOG']]}

def main(argv=None):
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path,
                        help='Absent or empty output directory beneath build/ (default: fresh build/proofs directory)')
    args = parser.parse_args(argv)
    if not __debug__:
        raise RuntimeError('Proof replay requires ordinary Python assertion checks; do not use -O')
    OUT = select_output(args.out)
    compiler.WORK = OUT / 'cc'
    inputs = stage_current_modules()
    provenance_path = OUT / 'source_inputs.json'
    provenance_path.write_text(json.dumps(inputs, indent=2) + '\n')
    object_names = ('OLDA', 'NEWA', 'OLDC', 'NEWC')
    objects = {name: assemble(name, OUT / 'sources' / (name + '.asm')) for name in object_names}
    reviews = {}
    sites = []
    for module, letter, count, firstpub, puboffset in [
            ('S03:3126', 'A', 4, '_o03_3126_0140', 320),
            ('S03:3258', 'C', 8, '_o03_3258_040C', 1024)]:
        review, added = compare_module(module, objects['OLD' + letter], objects['NEW' + letter], count)
        reviews[module] = review
        obj = objects['NEW' + letter]
        for f in added:
            preceding = max((p for p in obj.publics if p['segment'] == f['segment'] and
                             p['offset'] <= f['offset']), key=lambda p: p['offset'])
            table_offset = int.from_bytes(obj.segments[f['segment']][f['offset']:f['offset']+2], 'little') + f['displacement']
            sites.append({'module': module, 'object_operand_offset': f['offset'],
                          'function': preceding['name'], 'function_delta': f['offset'] - preceding['offset'],
                          'origin_public': firstpub, 'origin_public_offset': puboffset,
                          'table_offset': table_offset})
    assemble('CHECK', write_source('CHECK', checker(sites)))
    assemble('BOUND', write_source('BOUND', provider([objects['NEWA'], objects['NEWC']])))
    # A 4824-byte S03A contribution leaves S03C_TEXT's paragraph frame at
    # offset 8. Four fixture bytes reproduce the historical label offset 12.
    cases = {'ZERO': (0, 0), 'HIST': (0, 4), 'MOVE': (32, 32)}
    for case, (a, c) in cases.items():
        assemble(case, write_source(case, prefix(a, c)))
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
    report = {'schema': 'simant-s03-owned-address-current-proof-v1',
              'scope': 'Only complete source-owned S03:3126 and S03:3258 objects. Real-linker fixtures inspect their actual linked LEA displacement fields at runtime; no original game function executes. Test providers satisfy unexecuted boundaries only. This is not a full DOS game link, standalone execution, new assembly admission, or storage proof.',
              'original_image_read': False, 'canonical_sources_written': False,
              'output_directory': str(OUT),
              'reproduce': 'python evidence/canonical/s03-owned-addresses/replay.py --out build/s03-address-proof-fresh',
              'canonical_source_inputs_and_negative_recipes': inputs, 'whole_object_review': reviews,
              'linker_status': {name: tc['linkers'][name]['status'] for name in tool_dirs},
              'cases': results, 'all_required_checks_pass': True,
              'input_and_output_pins': [pin(Path(__file__)), pin(ROOT / 'tools/compiler.py'),
                                        pin(ROOT / 'tools/omf.py'), pin(ROOT / 'layout/toolchain.json'),
                                        pin(provenance_path)] + toolpins +
                                      [pin(p) for p in sorted((OUT / 'sources').glob('*.asm'))] +
                                      [pin(p) for p in sorted((OUT / 'objects').glob('*.OBJ'))]}
    receipt = OUT / 'receipt.json'
    receipt.write_text(json.dumps(report, indent=2) + '\n')
    summary = {'schema': 'simant-s03-owned-address-current-proof-summary-v1',
               'scope': report['scope'], 'reproduce': report['reproduce'],
               'full_receipt': pin(receipt), 'reproducer': pin(Path(__file__)),
               'canonical_source_inputs_and_negative_recipes': inputs, 'whole_object_review': {
                   module: {k: row[k] for k in ('code_and_data_lengths', 'public_count',
                            'old_fixup_count', 'new_fixup_count',
                            'retained_fixups_identical_in_order',
                            'all_other_code_and_data_bytes_identical', 'passed')}
                   for module, row in reviews.items()},
               'cases': [{k: row[k] for k in ('linker', 'case', 'variant',
                          'contribution_origins', 'test_prefix_bytes',
                          'runtime_result', 'mismatching_operands', 'passed')}
                         for row in results],
               'negative_controls_derived_from_current_canonical_sources': True, 'all_required_checks_pass': True}
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print('Receipt: ' + str(OUT / 'summary.json'), flush=True)

if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, AssertionError, subprocess.SubprocessError) as error:
        print(f'Proof replay failed: {error}', file=sys.stderr)
        raise SystemExit(1)
