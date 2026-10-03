"""Reproducible SOURCE_ONLY_DOS probe for the g_2108 map-owner candidate.

Only accepted source, toolchain inputs, and a sanitized original-research
checksum receipt are read. The original executable and assets are never build
inputs. This script generates fixture sources and a report, but no admission
contract or binding packet.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


def find_root():
    for path in Path(__file__).resolve().parents:
        if (path / 'layout' / 'manifest.json').is_file():
            return path
    raise RuntimeError('cannot locate repository root')


ROOT = find_root()
OUT = ROOT / 'build/workers/dos_color_translation_owners/admission-source-only-v14-final'
S03 = ROOT / 'src/S03/m3126.asm'
S00 = ROOT / 'src/S00/m31AD.asm'
ROOT_VIDEO = ROOT / 'src/root/m1B4E.asm'
SYMBOLS = ROOT / 'layout/symbols.json'
MANIFEST = ROOT / 'layout/manifest.json'
TOOLCHAIN = ROOT / 'layout/toolchain.json'
RESEARCH = ROOT / 'work/source-only-dos/color-translation-initial-state-research-v1.json'
PROBE_PATH = Path(__file__).resolve()
FLAGS = ['/AL', '/Os', '/Gs']

sys.path.insert(0, str(ROOT / 'tools'))
import compiler
import source_only_dos as dos
from omf import OmfReader


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pin(path, expected=None):
    path = Path(path)
    raw = path.read_bytes()
    digest = sha(raw)
    if expected is not None and digest != expected:
        raise RuntimeError('stale input pin: ' + str(path))
    if digest == dos.ORIGINAL_SHA:
        raise RuntimeError('original executable is forbidden as an input')
    try:
        shown = path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        shown = path.resolve().as_posix()
    return {'path': shown, 'sha256': digest, 'size': len(raw)}


def unique(rows):
    return [dict((k, v) for k, v in row.items()) for row in {
        (row['path'], row['sha256']): row for row in rows
    }.values()]


def parse_masm_atom(atom):
    atom = atom.strip()
    if re.fullmatch(r'[0-9A-Fa-f]+[Hh]', atom):
        return int(atom[:-1], 16)
    if re.fullmatch(r'[0-9]+', atom):
        return int(atom, 10)
    raise RuntimeError('unsupported nonliteral in accepted S03 table: ' + atom)


def c_literal(atom):
    atom = atom.strip()
    if re.fullmatch(r'[0-9A-Fa-f]+[Hh]', atom):
        return '0x' + atom[:-1]
    if re.fullmatch(r'[0-9]+', atom):
        return atom
    raise RuntimeError('cannot preserve accepted table literal: ' + atom)


def accepted_table(text):
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines)
                  if re.match(r'^\s*_g_2216\s+db\b', line, re.I)), None)
    if start is None:
        raise RuntimeError('accepted _g_2216 declaration missing')
    decl = []
    tokens = []
    for index in range(start, len(lines)):
        line = lines[index]
        if index != start and re.match(
                r'^\s*[A-Za-z_.$?][\w.$?]*\s+(?:db|dw|dd|label|segment|ends)\b',
                line, re.I):
            break
        match = re.match(r'^\s*(?:_g_2216\s+)?db\s+([^;]+)', line, re.I)
        if match:
            decl.append(line.strip())
            for atom in match.group(1).split(','):
                token = atom.strip()
                tokens.append({'source_line': index + 1, 'masm_literal': token,
                               'c_literal': c_literal(token),
                               'value': parse_masm_atom(token)})
        elif line.strip() and not line.lstrip().startswith(';'):
            raise RuntimeError('unexpected text inside accepted table: ' + line)
    values = [row['value'] for row in tokens]
    if len(values) != 16 or any(value < 0 or value > 0xff for value in values):
        raise RuntimeError('accepted source table is not exactly sixteen bytes')
    if any(value > 0x0f for value in values):
        raise RuntimeError('accepted table contains a value outside the color nibble')
    return '\n'.join(decl), tokens


def source_values_independently(text):
    """Second, deliberately small parser used only for checksum corroboration."""
    rows = []
    active = False
    for line in text.splitlines():
        if re.match(r'^\s*_g_2216\s+db\b', line, re.I):
            active = True
        elif active and re.match(
                r'^\s*[A-Za-z_.$?][\w.$?]*\s+(?:db|dw|dd|label|segment|ends)\b',
                line, re.I):
            break
        if active:
            match = re.match(r'^\s*(?:_g_2216\s+)?db\s+([^;]+)', line, re.I)
            if match:
                for token in match.group(1).split(','):
                    value = token.strip()
                    if value.lower().endswith('h'):
                        rows.append(int(value[:-1], 16))
                    else:
                        rows.append(int(value, 10))
    if len(rows) != 16:
        raise RuntimeError('independent source parser did not find sixteen values')
    return bytes(rows)


def accepted_fixture(declaration):
    return ("_DATA segment word public 'DATA'\n"
            'public _g_2216\n' + declaration + '\n'
            '_DATA ends\nDGROUP group _DATA\nend\n')


def owner_source(tokens, variant='separate'):
    c_values = [row['c_literal'] for row in tokens]
    if variant == 'reverse':
        c_values.reverse()
        extent = 16
    elif variant == 'shifted_backing':
        c_values.append('0xA5')
        extent = 17
    elif variant == 'separate':
        extent = 16
    else:
        raise ValueError(variant)
    return ('/* Values mechanically translated from accepted S03 _g_2216 literals. */\n'
            'unsigned char near g_2108[%d] = { %s };\n' %
            (extent, ', '.join(c_values)))


def main_source(kind):
    header = ('extern unsigned char near g_2216[16];\n'
              'extern int far puts(char far *text);\n')
    if kind == 'alias_view':
        return header + '''int main(void)
{
    unsigned char near *view = g_2216;
    unsigned char before;
    if (view != g_2216) return 2;
    before = g_2216[0];
    view[0] = (unsigned char)(before ^ 0xFF);
    if (g_2216[0] == before) return 3;
    g_2216[0] = before;
    puts("FAIL_ALIAS");
    return 0;
}
'''
    declared_extent = 17 if kind == 'shifted_base' else 16
    view = 'g_2108 + 1' if kind == 'shifted_base' else 'g_2108'
    return (header + 'extern unsigned char near g_2108[%d];\n' % declared_extent +
            '''int main(void)
{
    unsigned char near *view = %s;
    unsigned char before;
    unsigned int i;
    if (view == g_2216) { puts("FAIL_ALIAS"); return 0; }
    for (i = 0; i < 16; i++) {
        if (view[i] != g_2216[i]) { puts("FAIL_VALUES"); return 0; }
    }
    before = g_2216[0];
    g_2108[0] = (unsigned char)(g_2108[0] ^ 0xFF);
    if (g_2216[0] != before || g_2108[0] == before) return 3;
    g_2108[0] = before;
    for (i = 0; i < 16; i++) {
        if (view[i] != g_2216[i]) { puts("FAIL_RESTORE"); return 4; }
    }
    puts("PASS");
    return 0;
}
''' % view)


def compile_c(basename, text):
    result = compiler.compile_c(text, 'msc600ax', FLAGS, basename=basename)
    if not result.ok:
        raise RuntimeError(basename + ' compile failed:\n' + result.log)
    return result.obj


def compile_asm(basename, text):
    result = compiler.assemble(text, 'masm510', ['/Mx'], basename=basename)
    if not result.ok:
        raise RuntimeError(basename + ' assembly failed:\n' + result.log)
    return result.obj


def run_case(out, profile, case, accepted_obj, owner_obj, main_obj,
             expected, runtimes, linker, runner, tool_dir):
    folder = out / profile / case
    folder.mkdir(parents=True, exist_ok=True)
    for name in ('PROBE.EXE', 'PROBE.MAP', 'RUN.LOG', 'LINK.LOG'):
        (folder / name).unlink(missing_ok=True)
    (folder / 'MAIN.OBJ').write_bytes(main_obj)
    (folder / 'ACCEPT.OBJ').write_bytes(accepted_obj)
    if owner_obj is not None:
        (folder / 'OWNER.OBJ').write_bytes(owner_obj)
    for row in runtimes:
        shutil.copyfile(row['path'], folder / Path(row['path']).name.upper())
    source_list = 'FILE MAIN\r\nFILE ACCEPT\r\n'
    if owner_obj is not None:
        source_list += 'FILE OWNER\r\n'
    link_script = ('OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n'
                   'LIBRARY LLIBCR, LIBH\r\n' + source_list)
    (folder / 'PROBE.LNK').write_bytes(link_script.encode('ascii'))
    (folder / 'RTLINK.CFG').write_bytes(b'SYNTAX = FREEFORMAT\r\n')
    (folder / 'RUN.BAT').write_bytes((
        f'@echo off\r\nD:\\{linker["executable"]} @PROBE.LNK < NUL > LINK.LOG\r\n'
        'PROBE.EXE > RUN.LOG\r\n').encode('ascii'))
    conf = []
    for section, settings in runner['conf'].items():
        conf.append('[' + section + ']')
        conf.extend(f'{key}={value}' for key, value in settings.items())
    conf.extend(['[autoexec]', f'mount c "{folder}"', f'mount d "{tool_dir}" -ro',
                 'c:', 'call RUN.BAT', 'exit'])
    conf_path = folder / 'dosbox.conf'
    conf_path.write_text('\n'.join(conf) + '\n', encoding='ascii')
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
    timed_out = False
    try:
        result = subprocess.run([runner['path'], '-conf', str(conf_path),
                                 '-fastlaunch', '-exit', '-nomenu'], cwd=folder,
                                env=env, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, timeout=60,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except subprocess.TimeoutExpired:
        timed_out = True
        result = type('Timeout', (), {'returncode': -1})()
    actual = ((folder / 'RUN.LOG').read_text(encoding='latin1').strip()
              if (folder / 'RUN.LOG').exists() else 'NO RUN.LOG')
    link_log = ((folder / 'LINK.LOG').read_text(encoding='latin1', errors='replace')
                if (folder / 'LINK.LOG').exists() else '')
    return {'linker': profile, 'case': case, 'expected': expected, 'actual': actual,
            'emulator_exit': result.returncode, 'timed_out': timed_out,
            'passed': actual == expected and result.returncode == 0 and not timed_out,
            'link_log_tail': link_log[-1000:]}


def source_anchors_and_layout():
    s00_text = S00.read_text(encoding='latin1')
    s03_text = S03.read_text(encoding='latin1')
    video_text = ROOT_VIDEO.read_text(encoding='latin1')
    symbols = json.loads(SYMBOLS.read_text(encoding='utf-8'))
    symbol = symbols['data']['g_2108']
    refs = []
    numeric = []
    numeric_pattern = re.compile(
        r'(?i)(?<![\w])(?:2108h|0x2108|2108|2100h|0x2100|2118h|0x2118|55b3:2108)(?![\w])')
    identifier_pattern = re.compile(r'(?i)\b_g_2108\b')
    for path in (ROOT / 'src').rglob('*'):
        if path.suffix.lower() not in ('.asm', '.c'):
            continue
        text = path.read_text(encoding='latin1')
        relative = path.relative_to(ROOT).as_posix()
        for number, line in enumerate(text.splitlines(), 1):
            if identifier_pattern.search(line):
                refs.append({'path': relative, 'line': number, 'text': line.strip()})
            if numeric_pattern.search(line):
                numeric.append({'path': relative, 'line': number, 'text': line.strip()})
    expected_refs = [
        {'path': 'src/S00/m31AD.asm', 'line': 18, 'text': 'extrn\t_g_2108:byte'},
        {'path': 'src/S00/m31AD.asm', 'line': 3606, 'text': 'lea si, _g_2108'},
    ]
    if refs != expected_refs:
        raise RuntimeError('canonical source _g_2108 reference set changed: ' + repr(refs))
    target_numeric = [row for row in numeric if re.search(
        r'(?i)(?<![\w])(?:2108h|0x2108|55b3:2108)(?![\w])', row['text'])]
    if target_numeric:
        raise RuntimeError('direct numeric g_2108-layout operand found: ' + repr(target_numeric))
    for row in numeric:
        row['classification'] = ('Win16 window/object handle passed to win_Open/win_GetObjRect/'
                                 'win_Close; not a DOS DGROUP data address'
                                 if row['path'] == 'src/S15/m384C.c'
                                 and '0x2100' in row['text'] else 'unclassified')
    if any(row['classification'] == 'unclassified' for row in numeric):
        raise RuntimeError('unclassified numeric literal near candidate address: ' + repr(numeric))
    for expected, text in (("_g_2108 source reference", s00_text),
                           ("_g_2216 source table", s03_text),
                           ("runtime g_41C0 consumer", video_text)):
        if not text:
            raise RuntimeError(expected + ' is empty')
    if (symbol.get('seg'), symbol.get('off')) != (0x55B3, 0x2108):
        raise RuntimeError('registered g_2108 DGROUP address changed')
    return {
        'registered_symbol': {'name': 'g_2108', 'segment': symbol['seg'],
                              'segment_hex': '0x%04X' % symbol['seg'],
                              'dgroup_offset': symbol['off'],
                              'dgroup_offset_hex': '0x%04X' % symbol['off']},
        'canonical_identifier_references': refs,
        'direct_numeric_operands_scanned': numeric,
        'direct_numeric_g2108_address_operands': target_numeric,
        'source_consumers': [
            {'path': 'src/S00/m31AD.asm', 'anchors': [18, 3605, 3606, 3607, 3608],
             'finding': 'Video-mode 0Dh path copies eight words from g_2108 into mutable g_41C0; no pointer is retained by REP MOVSW.'},
            {'path': 'src/S03/m3126.asm', 'anchors': [52, 53, 180, 182],
             'finding': 'Accepted mode 09h source carries separate g_2216 table and copies eight words into g_41C0.'},
            {'path': 'src/root/m1B4E.asm', 'anchors': [58, 111, 114, 115, 116, 117, 118, 119, 120],
             'finding': 'g_41C0 begins as identity mapping; runtime consumer masks low nibble and uses XLAT through the mutable map.'},
        ],
        'scope_limit': ('No direct numeric address operands were found in canonical C/ASM source. '
                        'Computed or indirect pointer paths, unregistered aliases, other runtime writes, '
                        'and complete lifetime immutability remain unresolved.'),
    }


def main():
    denied = dos.install_input_guard()
    OUT.mkdir(parents=True, exist_ok=True)
    generated = OUT / 'generated'
    generated.mkdir(parents=True, exist_ok=True)

    accepted_text, accepted_pin = dos.pin(S03)
    declaration, tokens = accepted_table(accepted_text.decode('latin1'))
    independently_parsed = source_values_independently(accepted_text.decode('latin1'))
    source_bytes = bytes(row['value'] for row in tokens)
    if independently_parsed != source_bytes:
        raise RuntimeError('independent accepted-source parsers disagree')
    table_sha = sha(source_bytes)

    research_raw, research_pin = dos.pin(RESEARCH)
    research = json.loads(research_raw)
    research_map = research['g_2108']
    if (research.get('schema') != 'dos-g2108-original-research-v1'
            or research_map.get('matches_accepted_S03_g_2216_values') is not True
            or research_map.get('accepted_source_value_sha256') != table_sha
            or research_map.get('value_sha256') != table_sha
            or research_map.get('read_width') != 16):
        raise RuntimeError('sanitized independent checksum receipt does not corroborate accepted source')

    fixture_text = accepted_fixture(declaration)
    fixture_path = generated / 'accepted-s03-g2216-data.asm'
    fixture_path.write_text(fixture_text, encoding='ascii')
    fixture_obj = compile_asm('ACCEPT', fixture_text)

    provider_paths = {}
    provider_objs = {}
    provider_sources = {}
    for variant in ('separate', 'reverse', 'shifted_backing'):
        source = owner_source(tokens, variant)
        path = generated / (variant + '-g2108-provider.c')
        path.write_text(source, encoding='ascii')
        provider_paths[variant] = path
        provider_sources[variant] = pin(path)
        provider_objs[variant] = compile_c(('G2108%02d' % len(variant))[:8], source)

    main_paths = {}
    main_pins = {}
    main_objs = {}
    for kind in ('separate', 'reverse', 'shifted_base', 'alias_view'):
        source = main_source(kind)
        path = generated / (kind + '-main.c')
        path.write_text(source, encoding='ascii')
        main_paths[kind] = path
        main_pins[kind] = pin(path)
        main_objs[kind] = compile_c(('M' + kind.upper())[:8], source)

    reader = OmfReader(communals=True)
    fixture = reader.read(fixture_obj, 'ACCEPT')
    fixture_data = fixture.segments.get('_DATA', b'')
    if (fixture.segment_lengths.get('_DATA') != 16 or fixture_data != source_bytes
            or fixture.publics != [{'name': '_g_2216', 'segment': '_DATA', 'offset': 0}]
            or fixture.fixups or fixture.linker_fixups or fixture.externals):
        raise RuntimeError('accepted source data fixture OMF differs from its exact 16-byte source table')

    good_obj = provider_objs['separate']
    good = reader.read(good_obj, 'G2108OWN')
    good_data = good.segments.get('_DATA', b'')
    if (good.segment_lengths.get('_DATA') != 16 or good_data != source_bytes
            or good.publics != [{'name': '_g_2108', 'segment': '_DATA', 'offset': 0}]
            or good.fixups or good.linker_fixups or good.externals or good.communals
            or any(length for segment, length in good.segment_lengths.items()
                   if segment != '_DATA')):
        raise RuntimeError('candidate owner is not one exact initialized public _DATA extent with no fixups')

    layout = source_anchors_and_layout()
    anchor_paths = [S00, S03, ROOT_VIDEO, SYMBOLS]
    static_pins = [pin(path) for path in anchor_paths]
    manifest_raw, manifest_pin = dos.pin(MANIFEST)
    manifest = json.loads(manifest_raw)
    tc_raw, tc_pin = dos.pin(TOOLCHAIN)
    tc = json.loads(tc_raw)
    tool_inputs = [pin(PROBE_PATH), accepted_pin, *static_pins,
                   manifest_pin, tc_pin,
                   pin(ROOT / 'tools/compiler.py'), pin(ROOT / 'tools/source_only_dos.py'),
                   pin(ROOT / 'tools/omf.py'), pin(RESEARCH)]
    msc = compiler.verify_profile('msc600ax')
    masm = compiler.verify_profile('masm510')
    for profile in (msc, masm):
        for relative, digest in profile['files'].items():
            tool_inputs.append(pin(Path(profile['directory']) / relative, digest))
    runner = tc['runners']['dosbox-x']
    tool_inputs.append(pin(Path(runner['path']), runner['sha256']))
    runtimes = list(manifest['runtime']['libraries'].values())
    for runtime in runtimes:
        tool_inputs.append(pin(Path(runtime['path']), runtime['sha256']))

    cases = []
    for profile in ('rtlink400', 'rtlink610'):
        linker = tc['linkers'][profile]
        for relative, digest in linker['files'].items():
            tool_inputs.append(pin(Path(linker['directory']) / relative, digest))
        tool_dir = compiler.pinned_tree(linker)
        cases.append(run_case(OUT / 'runtime', profile,
                              'separate_mutable_exact_values', fixture_obj,
                              provider_objs['separate'], main_objs['separate'],
                              'PASS', runtimes, linker, runner, tool_dir))
        cases.append(run_case(OUT / 'runtime', profile,
                              'reversed_mapping_negative', fixture_obj,
                              provider_objs['reverse'], main_objs['reverse'],
                              'FAIL_VALUES', runtimes, linker, runner, tool_dir))
        cases.append(run_case(OUT / 'runtime', profile,
                              'one_byte_shifted_map_base_negative', fixture_obj,
                              provider_objs['shifted_backing'], main_objs['shifted_base'],
                              'FAIL_VALUES', runtimes, linker, runner, tool_dir))
        cases.append(run_case(OUT / 'runtime', profile,
                              'alias_view_negative', fixture_obj, None,
                              main_objs['alias_view'], 'FAIL_ALIAS', runtimes,
                              linker, runner, tool_dir))

    required_cases = {
        'separate_mutable_exact_values': 'PASS',
        'reversed_mapping_negative': 'FAIL_VALUES',
        'one_byte_shifted_map_base_negative': 'FAIL_VALUES',
        'alias_view_negative': 'FAIL_ALIAS',
    }
    all_cases_pass = (len(cases) == 8 and all(row['passed'] for row in cases)
                      and not denied)
    omf_check = {
        'object_sha256': sha(good_obj),
        'publics': good.publics,
        'segment_definitions': good.segment_defs,
        'segment_extents': good.segment_lengths,
        'initialized_data_size': len(good_data),
        'initialized_data_sha256': sha(good_data),
        'matches_accepted_source_data_sha256': sha(good_data) == table_sha,
        'fixup_count': len(good.fixups),
        'ordered_linker_fixup_count': len(good.linker_fixups),
        'external_names': good.externals,
        'communal_records': good.communals,
        'exact_one_public_16_byte_initialized_data_extent': True,
    }
    report = {
        'schema': 'simant-source-only-g2108-color-map-admission-probe-v1',
        'status': 'CANDIDATE_FOR_ROOT_REVIEW',
        'probe_source': pin(PROBE_PATH),
        'candidate_provider_source': pin(provider_paths['separate']),
        'provider_recipe': {
            'source': accepted_pin,
            'accepted_declaration': '_g_2216 in src/S03/m3126.asm, lines 52-53',
            'translation': 'Each accepted MASM literal is copied in source order. Hex suffix H is translated to C prefix 0x while retaining the digits; decimal literals remain decimal. No original-executable value is used to generate source.',
            'source_literal_map': tokens,
            'candidate_declaration': 'unsigned char near g_2108[16]',
            'distinct_object': True,
            'lifetime_mutability_claim': 'The object is initialized and writable; no claim that its value remains immutable for the full game lifetime.',
        },
        'independent_research_corroboration': {
            'receipt': research_pin,
            'original_image_sha256_recorded_in_receipt': research['original_sha256'],
            'original_g_2108_width': research_map['read_width'],
            'original_g_2108_value_sha256': research_map['value_sha256'],
            'accepted_source_value_sha256': table_sha,
            'digest_match': research_map['value_sha256'] == table_sha,
            'source_predicate': {
                'exactly_16_literals': len(tokens) == 16,
                'all_values_are_color_nibbles': all(row['value'] <= 0x0f for row in tokens),
                'accepted_source_parsers_agree': independently_parsed == source_bytes,
            },
            'receipt_contains_raw_table_bytes': False,
        },
        'accepted_source_assembler_control': {
            'profile': 'masm510', 'flags': ['/Mx'],
            'object_sha256': sha(fixture_obj),
            'publics': fixture.publics,
            'segment_extents': fixture.segment_lengths,
            'initialized_data_size': len(fixture_data),
            'initialized_data_sha256': sha(fixture_data),
            'fixup_count': len(fixture.fixups),
            'matches_parsed_source': fixture_data == source_bytes,
        },
        'candidate_omf_check': omf_check,
        'canonical_ownership': layout,
        'runtime_profiles': ['rtlink400', 'rtlink610'],
        'cases': cases,
        'required_cases': required_cases,
        'tool_and_input_pins': unique(tool_inputs + list(provider_sources.values()) + list(main_pins.values())),
        'denied_oracle_reads': denied,
        'build_scope': 'Source-only C/MASM fixtures, verified MSC 6.00AX and MASM 5.10, pinned RTLink 4.00/6.10, pinned CRT libraries and DOSBox-X. No original executable or assets are build inputs.',
        'all_required_checks_pass': all_cases_pass and omf_check['exact_one_public_16_byte_initialized_data_extent'],
        'claim_limit': 'Candidate resolves only the bounded initialized owner recipe for DGROUP 0x2108..0x2117 and the S00 _g_2108:byte import. It makes no historical COMDEF/TU identity, alias identity, fixed-order, wider 0x2100..0x2117 owner, full lifetime immutability, computed-pointer, or unregistered-alias claim.',
    }

    report_path = OUT / 'g2108-color-map-admission-report.json'
    report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('all_required_checks_pass', report['all_required_checks_pass'])
    print('probe_report', report_path)
    return 0 if report['all_required_checks_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
