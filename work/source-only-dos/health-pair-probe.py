"""Self-contained S08 COMDEF comparison and HealthB/HealthR runtime probe.

Compile the canonical manifest source as U016, compile a candidate made only
by changing the two Health declarations, then compare the complete OMF live
contribution. A separate minimal typed owner with a test-only overlay accessor
uses the measured COMDEF shape in RTLink fixtures; the generated U016 object is
never linked into those fixtures. No game functions are stubbed or called.
"""
from pathlib import Path
from collections import Counter
import hashlib
import json
import os
import shutil
import subprocess
import sys

def find_root():
    for candidate in Path(__file__).resolve().parents:
        if (candidate / 'layout' / 'manifest.json').is_file():
            return candidate
    raise RuntimeError('cannot locate repository root (layout/manifest.json)')


ROOT = find_root()
OUT = ROOT / 'build/workers/dos_health_pair_runtime'
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / 'tools'))
import compiler
import dos_source_bindings as bindings
import source_only_dos as dos
from omf import OmfReader

OWNER = r'''int far HealthB;
int far HealthR;
int far health_pair_owner_word_sum(void)
{
    return HealthB + HealthR;
}
'''

BAD_OWNER = r'''int far HealthB = 1;
int far HealthR = 2;
int far health_pair_owner_word_sum(void)
{
    return HealthB + HealthR;
}
'''

WORD = r'''extern int far HealthB;
extern int far HealthR;
extern int far fd_50F6_10BE;
extern int far fd_50F6_01FE;
extern int far health_pair_owner_word_sum(void);
extern int far puts(char far *text);
int main(void)
{
    if (&HealthB != &fd_50F6_10BE || &HealthR != &fd_50F6_01FE ||
        HealthB != 0 || HealthR != 0 || health_pair_owner_word_sum() != 0) {
        puts("FAIL");
        return 1;
    }
    HealthB = 0x1234;
    fd_50F6_01FE = 0x5678;
    if (fd_50F6_10BE != 0x1234 || HealthR != 0x5678 ||
        health_pair_owner_word_sum() != 0x68AC) {
        puts("FAIL");
        return 1;
    }
    puts("PASS");
    return 0;
}
'''

BYTE = r'''extern unsigned char far HealthB[];
extern unsigned char far HealthR[];
extern int far fd_50F6_10BE;
extern int far fd_50F6_01FE;
extern int far health_pair_owner_word_sum(void);
extern int far puts(char far *text);
struct SaveRec { int size; int count; void far *data; };
struct SaveRec far SaveRecTable[2] = {
    {2, 1, (void far *)&HealthB},
    {2, 1, (void far *)&HealthR}
};
int main(void)
{
    unsigned char far *black;
    unsigned char far *red;
    black = (unsigned char far *)SaveRecTable[0].data;
    red = (unsigned char far *)SaveRecTable[1].data;
    if (SaveRecTable[0].size != 2 || SaveRecTable[0].count != 1 ||
        SaveRecTable[1].size != 2 || SaveRecTable[1].count != 1 ||
        black != HealthB || red != HealthR ||
        &fd_50F6_10BE != (int far *)HealthB ||
        &fd_50F6_01FE != (int far *)HealthR ||
        black[0] != 0 || black[1] != 0 || red[0] != 0 || red[1] != 0 ||
        health_pair_owner_word_sum() != 0) {
        puts("FAIL");
        return 1;
    }
    black[0] = 0x34;
    black[1] = 0x12;
    red[0] = 0x78;
    red[1] = 0x56;
    if (*((int far *)HealthB) != 0x1234 || *((int far *)HealthR) != 0x5678 ||
        fd_50F6_10BE != 0x1234 || fd_50F6_01FE != 0x5678 ||
        health_pair_owner_word_sum() != 0x68AC) {
        puts("FAIL");
        return 1;
    }
    fd_50F6_10BE = 0x2468;
    if (black[0] != 0x68 || black[1] != 0x24 ||
        health_pair_owner_word_sum() != 0x7AE0) {
        puts("FAIL");
        return 1;
    }
    puts("PASS");
    return 0;
}
'''


def compile_fixture(name, source, profile, flags):
    path = OUT / (name + '.c')
    path.write_text(source, encoding='ascii')
    result = compiler.compile_c(source, profile, flags, basename=name)
    if not result.ok:
        raise RuntimeError(name + ' compile failed:\n' + result.log)
    return path, result.obj


def compile_full_module(manifest_row):
    source_path = ROOT / manifest_row['source']
    raw_source = source_path.read_bytes()
    source_hash = hashlib.sha256(raw_source).hexdigest()
    if source_hash != manifest_row['source_sha256']:
        raise RuntimeError('manifest source pin mismatch for ' + manifest_row['source'])
    source = raw_source.decode('ascii')
    edits = [('extern int far HealthB;', 'int far HealthB;'),
             ('extern int far HealthR;', 'int far HealthR;')]
    candidate = source
    edit_counts = {}
    for before, after in edits:
        count = candidate.count(before)
        if count != 1:
            raise RuntimeError(f'expected one exact declaration {before!r}, found {count}')
        candidate = candidate.replace(before, after, 1)
        edit_counts[before] = count
    normalized_back = candidate
    for before, after in edits:
        normalized_back = normalized_back.replace(after, before, 1)
    if normalized_back != source:
        raise RuntimeError('candidate source differs outside the two approved declaration edits')

    control_source_path = OUT / 'U016-source-control.c'
    candidate_source_path = OUT / 'U016-health-owner-candidate.c'
    control_source_path.write_bytes(raw_source)
    candidate_source_path.write_bytes(candidate.encode('ascii'))
    profile, flags = manifest_row['profile'], manifest_row['flags']
    control = compiler.compile_c(source, profile, flags, basename='U016')
    if not control.ok:
        raise RuntimeError('U016 canonical control compile failed:\n' + control.log)
    candidate_result = compiler.compile_c(candidate, profile, flags, basename='U016')
    if not candidate_result.ok:
        raise RuntimeError('U016 two-COMDEF candidate compile failed:\n' + candidate_result.log)
    control_object_path = OUT / 'U016-control.OBJ'
    candidate_object_path = OUT / 'U016-health-owner-candidate.OBJ'
    control_object_path.write_bytes(control.obj)
    candidate_object_path.write_bytes(candidate_result.obj)
    return {
        'source_path': source_path,
        'source_raw': raw_source,
        'source_hash': source_hash,
        'control_source_path': control_source_path,
        'candidate_source_path': candidate_source_path,
        'control_object_path': control_object_path,
        'candidate_object_path': candidate_object_path,
        'control_object': control.obj,
        'candidate_object': candidate_result.obj,
        'candidate_source': candidate,
        'profile': profile,
        'flags': flags,
        'edit_counts': edit_counts,
    }


def compare_full_module(control_obj, candidate_obj):
    exact_checks = {
        'all_segment_bytes_equal': control_obj.segments == candidate_obj.segments,
        'segment_name_set_equal': set(control_obj.segments) == set(candidate_obj.segments),
        'segment_extents_equal': control_obj.segment_lengths == candidate_obj.segment_lengths,
        'segment_definitions_equal': control_obj.segment_defs == candidate_obj.segment_defs,
        'groups_equal': control_obj.groups == candidate_obj.groups,
        'publics_equal': control_obj.publics == candidate_obj.publics,
        'local_publics_equal': control_obj.local_publics == candidate_obj.local_publics,
        'legacy_fixups_equal': control_obj.fixups == candidate_obj.fixups,
        'normalized_fixup_sequence_equal': (
            [bindings.fixup_key(f) for f in control_obj.linker_fixups] ==
            [bindings.fixup_key(f) for f in candidate_obj.linker_fixups]),
        'normalized_fixup_multiset_equal': (
            Counter(bindings.fixup_key(f) for f in control_obj.linker_fixups) ==
            Counter(bindings.fixup_key(f) for f in candidate_obj.linker_fixups)),
        'full_ordered_linker_fixups_equal': control_obj.linker_fixups == candidate_obj.linker_fixups,
        'external_names_equal': control_obj.externals == candidate_obj.externals,
    }
    scope_changes = []
    scopes_aligned = len(control_obj.external_scopes) == len(candidate_obj.external_scopes) == len(control_obj.externals)
    if scopes_aligned:
        for name, before, after in zip(control_obj.externals,
                                       control_obj.external_scopes,
                                       candidate_obj.external_scopes):
            if before != after:
                scope_changes.append({'name': name, 'before': before, 'after': after})
    expected_scope_changes = [
        {'name': '_HealthB', 'before': 'external', 'after': 'communal'},
        {'name': '_HealthR', 'before': 'external', 'after': 'communal'},
    ]
    scope_changes_ok = (scopes_aligned and
                        {tuple(r.values()) for r in scope_changes} ==
                        {tuple(r.values()) for r in expected_scope_changes} and
                        len(scope_changes) == 2)
    expected_communal_keys = {
        ('_HealthB', 'far', 2, 1, 2),
        ('_HealthR', 'far', 2, 1, 2),
    }
    actual_communal_keys = [bindings.communal_key(c) for c in candidate_obj.communals]
    communal_check = (set(actual_communal_keys) == expected_communal_keys and
                      len(actual_communal_keys) == 2 and not control_obj.communals)
    segment_byte_checks = []
    for name in sorted(set(control_obj.segments) | set(candidate_obj.segments)):
        before = control_obj.segments.get(name)
        after = candidate_obj.segments.get(name)
        segment_byte_checks.append({
            'segment': name,
            'equal': before == after,
            'control_length': None if before is None else len(before),
            'candidate_length': None if after is None else len(after),
            'control_sha256': None if before is None else hashlib.sha256(before).hexdigest(),
            'candidate_sha256': None if after is None else hashlib.sha256(after).hexdigest(),
        })
    return {
        'checks': exact_checks,
        'all_live_contribution_checks_pass': all(exact_checks.values()),
        'segment_byte_checks': segment_byte_checks,
        'control_segment_extents': control_obj.segment_lengths,
        'candidate_segment_extents': candidate_obj.segment_lengths,
        'segment_definition_count': len(control_obj.segment_defs),
        'group_count': len(control_obj.groups),
        'public_count': len(control_obj.publics),
        'normalized_fixup_count': len(control_obj.linker_fixups),
        'ordered_normalized_fixup_sha256': hashlib.sha256(json.dumps(
            [bindings.fixup_key(f) for f in control_obj.linker_fixups],
            separators=(',', ':')).encode('utf-8')).hexdigest(),
        'external_scope_changes': scope_changes,
        'only_expected_extern_to_communal_scope_changes': scope_changes_ok,
        'control_communal_rows': control_obj.communals,
        'candidate_communal_rows': candidate_obj.communals,
        'exactly_two_expected_far_communal_records': communal_check,
        'expected_communal_keys': [list(k) for k in sorted(expected_communal_keys)],
        'passed': all(exact_checks.values()) and scope_changes_ok and communal_check,
    }


def run_case(profile, case, consumer_obj, owner_obj, delta_b, delta_r,
             expected, runtimes, linker, runner, tool_dir):
    directory = OUT / profile / case
    directory.mkdir(parents=True, exist_ok=True)
    for name in ('PROBE.EXE', 'PROBE.MAP', 'RUN.LOG', 'LINK.LOG'):
        (directory / name).unlink(missing_ok=True)
    # The independent MSC consumer is the root/main module. The minimal
    # typed communal pair and its word accessor live in one overlay module.
    (directory / 'CRT.OBJ').write_bytes(consumer_obj)
    (directory / 'OWNER.OBJ').write_bytes(owner_obj)
    for row in runtimes:
        shutil.copyfile(row['path'], directory / Path(row['path']).name.upper())
    script = ('OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n'
              'LIBRARY LLIBCR, LIBH\r\n'
              'FILE CRT\r\n'
              'BEGINAREA\r\nSECTION FILE OWNER\r\nENDAREA\r\n'
              'DEFINE _fd_50F6_10BE = _HealthB'
              + (f' + {delta_b}' if delta_b else '') + '\r\n'
              'DEFINE _fd_50F6_01FE = _HealthR'
              + (f' + {delta_r}' if delta_r else '') + '\r\n')
    (directory / 'PROBE.LNK').write_bytes(script.encode('ascii'))
    (directory / 'RTLINK.CFG').write_bytes(b'SYNTAX = FREEFORMAT\r\n')
    (directory / 'RUN.BAT').write_bytes((
        f'@echo off\r\nD:\\{linker["executable"]} @PROBE.LNK < NUL > LINK.LOG\r\n'
        'PROBE.EXE > RUN.LOG\r\n').encode('ascii'))
    config = []
    for section, settings in runner['conf'].items():
        config.append('[' + section + ']')
        config += [f'{k}={v}' for k, v in settings.items()]
    config += ['[autoexec]', f'mount c "{directory}"',
               f'mount d "{tool_dir}" -ro', 'c:', 'call RUN.BAT', 'exit']
    conf = directory / 'dosbox.conf'
    conf.write_text('\n'.join(config) + '\n')
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
    timed_out = False
    try:
        run = subprocess.run([runner['path'], '-conf', str(conf), '-fastlaunch',
                              '-exit', '-nomenu'], cwd=directory, env=env,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             timeout=60, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except subprocess.TimeoutExpired:
        timed_out = True
        run = type('TimedOut', (), {'returncode': -1})()
    log_path = directory / 'RUN.LOG'
    actual = log_path.read_text(encoding='latin1').strip() if log_path.exists() else 'NO RUN.LOG'
    link_path = directory / 'LINK.LOG'
    link_log = link_path.read_text(encoding='latin1', errors='replace') if link_path.exists() else ''
    row = {'linker': profile, 'case': case, 'alias_health_b_delta': delta_b,
           'alias_health_r_delta': delta_r, 'expected': expected,
           'actual': actual, 'emulator_exit': run.returncode, 'timed_out': timed_out,
           'passed': actual == expected and run.returncode == 0 and not timed_out,
           'link_log_tail': link_log[-1000:],
           'files': [dos.pin(p)[1] for p in sorted(directory.iterdir()) if p.is_file()]}
    print(profile, case, actual, flush=True)
    return row


SHORTLIST = [
    {'name': 'HealthB', 'offset': '10BE', 'bytes': 2, 'SaveRec': 'S09:35F5 line 1061', 'owner': 'S08 RandWorld reset to 100'},
    {'name': 'HealthR', 'offset': '01FE', 'bytes': 2, 'SaveRec': 'S09:35F5 line 1062', 'owner': 'S08 RandWorld reset to 100'},
    {'name': 'MeHealth', 'offset': '0F78', 'bytes': 2, 'SaveRec': 'line 1094', 'owner': 'root:10F7 SetMyHealth clamp'},
    {'name': 'FoodB', 'offset': '1050', 'bytes': 2, 'SaveRec': 'line 1052', 'owner': 'S08 RandWorld reset to 0'},
    {'name': 'FoodR', 'offset': '1060', 'bytes': 2, 'SaveRec': 'line 1053', 'owner': 'S08 RandWorld reset to 0'},
    {'name': 'Cycle', 'offset': '0F08', 'bytes': 2, 'SaveRec': 'line 1036', 'owner': 'S08 reset; root:0894 advances/wraps'},
    {'name': 'BpopT', 'offset': '0330', 'bytes': 2, 'SaveRec': 'line 1020', 'owner': 'root:0BE8 CountAnts recomputes'},
    {'name': 'RpopT', 'offset': '0350', 'bytes': 2, 'SaveRec': 'line 1143', 'owner': 'root:0BE8 CountAnts recomputes'},
    {'name': 'AntsEatenByLions', 'offset': '0A08', 'bytes': 2, 'SaveRec': 'line 995', 'owner': 'root:0AD9 reset/increment'},
    {'name': 'InitialLions', 'offset': '08EA', 'bytes': 2, 'SaveRec': 'line 1066', 'owner': 'root:0AD9 sets/clamps/reads'},
]

SOURCE_PATHS = [
    'src/S07/m35F5.c', 'src/S08/m35F5.c', 'src/S09/m35F5.c',
    'src/S12/m384C.c', 'src/S24/m39C7.c', 'src/S25/m39C7.c', 'src/S25/m3BA4.c',
    'src/root/m015B.c', 'src/root/m0250.c', 'src/root/m0894.c', 'src/root/m0E2E.c',
    'src/root/m0F3F.c', 'src/root/m10F7.c', 'src/root/m1383.c', 'src/root/m0BE8.c',
    'src/root/m0AD9.c',
]


def main():
    denied = dos.install_input_guard()
    tc = compiler.toolchain()
    manifest_raw, manifest_pin = dos.pin(ROOT / 'layout/manifest.json')
    manifest = json.loads(manifest_raw)
    module = manifest['modules'].get('S08:35F5')
    if (not module or module.get('unit') != 'S08' or module.get('seg') != 0x35F5 or
            module.get('source') != 'src/S08/m35F5.c'):
        raise RuntimeError('manifest module S08:35F5 no longer resolves to the expected S08 source')
    full = compile_full_module(module)
    control_omf = OmfReader(communals=True).read(full['control_object'])
    candidate_omf = OmfReader(communals=True).read(full['candidate_object'])
    whole_module = compare_full_module(control_omf, candidate_omf)
    whole_module['object_size_delta_bytes'] = len(full['candidate_object']) - len(full['control_object'])
    whole_module['control_object_sha256'] = hashlib.sha256(full['control_object']).hexdigest()
    whole_module['candidate_object_sha256'] = hashlib.sha256(full['candidate_object']).hexdigest()
    whole_module['baseline_equals_manifest_compiled_source_only_object'] = None
    whole_module['note'] = ('Self-contained source-to-source comparison only; no pre-existing ignored U016 object '
                            'is an input. It proves the candidate preserves this source compile live contribution '
                            'and adds the two expected COMDEF records.')

    flags_owner = module['flags']
    flags_consumer = ['/AL', '/Os', '/Zi']
    owner_path, owner_bytes = compile_fixture('HPOWNER', OWNER, module['profile'], flags_owner)
    bad_path, bad_bytes = compile_fixture('BADOWNER', BAD_OWNER, module['profile'], flags_owner)
    word_path, word_bytes = compile_fixture('HPWORD', WORD, module['profile'], flags_consumer)
    byte_path, byte_bytes = compile_fixture('HPBYTE', BYTE, module['profile'], flags_consumer)
    expected_names = {'_HealthB', '_HealthR'}
    measured_pair = [c for c in candidate_omf.communals if c['name'] in expected_names]
    owner_omf = OmfReader(communals=True).read(owner_bytes)
    owner_pair = [c for c in owner_omf.communals if c['name'] in expected_names]
    owner_records_match = (
        len(owner_omf.communals) == 2 and len(owner_pair) == 2 and
        [bindings.communal_key(c) for c in owner_pair] ==
        [bindings.communal_key(c) for c in measured_pair])
    bad_omf = OmfReader(communals=True).read(bad_bytes)
    bad_public_names = {p['name'] for p in bad_omf.publics}
    bad_owner_is_contrast = not bad_omf.communals and expected_names <= bad_public_names

    worklist_raw, worklist_pin = dos.pin(ROOT / 'work/source-only-dos/farbss-mechanical-worklist-v2.json')
    worklist = json.loads(worklist_raw)
    worklist_by_name = {row[0]: row for row in worklist['length_matches_requiring_review']}
    shortlist_rows = []
    for item in SHORTLIST:
        row = worklist_by_name.get(item['name'])
        if row != [item['name'], item['bytes'], int(item['SaveRec'].split()[-1]), False]:
            raise RuntimeError('selected scalar shortlist no longer matches the pinned mechanical worklist: ' + item['name'])
        shortlist_rows.append({**item, 'worklist_row': row})

    inputs = [dos.pin(Path(__file__))[1], manifest_pin,
              dos.pin(ROOT / 'layout/toolchain.json')[1],
              dos.pin(full['source_path'], module['source_sha256'])[1],
              worklist_pin,
              dos.pin(ROOT / 'layout/symbols.json')[1]]
    for tool_source in ('tools/compiler.py', 'tools/omf.py',
                        'tools/dos_source_bindings.py', 'tools/source_only_dos.py'):
        inputs.append(dos.pin(ROOT / tool_source)[1])
    for relative in SOURCE_PATHS:
        inputs.append(dos.pin(ROOT / relative)[1])
    inputs += [dos.pin(full['control_source_path'])[1], dos.pin(full['candidate_source_path'])[1],
               dos.pin(full['control_object_path'])[1], dos.pin(full['candidate_object_path'])[1]]
    for path in (owner_path, bad_path, word_path, byte_path):
        inputs.append(dos.pin(path)[1])
    msc = compiler.verify_profile(module['profile'])
    for rel, digest in msc['files'].items():
        inputs.append(dos.pin(Path(msc['directory']) / rel, digest)[1])
    inputs.append(dos.pin(Path(tc['runner']['path']), tc['runner']['sha256'])[1])
    runner = tc['runners']['dosbox-x']
    inputs.append(dos.pin(Path(runner['path']), runner['sha256'])[1])
    runtimes = list(manifest['runtime']['libraries'].values())
    cases_report = []
    case_specs = [
        ('typed_owner_word_exact_aliases', word_bytes, owner_bytes, 0, 0, 'PASS'),
        ('typed_owner_SaveRec_BYTE_exact_aliases', byte_bytes, owner_bytes, 0, 0, 'PASS'),
        ('typed_owner_word_wrong_black_alias_plus2', word_bytes, owner_bytes, 2, 0, 'FAIL'),
        ('typed_owner_SaveRec_BYTE_wrong_red_alias_plus2', byte_bytes, owner_bytes, 0, 2, 'FAIL'),
        ('initialized_nonzero_owner_word_contrast', word_bytes, bad_bytes, 0, 0, 'FAIL'),
        ('initialized_nonzero_owner_SaveRec_BYTE_contrast', byte_bytes, bad_bytes, 0, 0, 'FAIL'),
    ]
    for profile in ('rtlink400', 'rtlink610'):
        linker = tc['linkers'][profile]
        for rel, digest in linker['files'].items():
            inputs.append(dos.pin(Path(linker['directory']) / rel, digest)[1])
        tool_dir = compiler.pinned_tree(linker)
        for row in runtimes:
            inputs.append(dos.pin(Path(row['path']), row['sha256'])[1])
        for case, consumer, owner, db, dr, expected in case_specs:
            row = run_case(profile, case, consumer, owner, db, dr, expected,
                           runtimes, linker, runner, tool_dir)
            cases_report.append(row)

    packet = {
        'scope': 'First next-FAR_BSS scalar family reviewed from the mechanical worklist; no size-only or gap-based ownership inference.',
        'candidate_shortlist': shortlist_rows,
        'selected_pair': [
            {'name': 'HealthB', 'address': '50F6:10BE', 'type_views': ['int far'],
             'SaveRec': {'source': 'src/S09/m35F5.c', 'line': 1061, 'size': 2, 'count': 1},
             'alias': 'fd_50F6_10BE'},
            {'name': 'HealthR', 'address': '50F6:01FE', 'type_views': ['int far'],
             'SaveRec': {'source': 'src/S09/m35F5.c', 'line': 1062, 'size': 2, 'count': 1},
             'alias': 'fd_50F6_01FE'},
        ],
        'functional_owner': {
            'manifest_module': 'S08:35F5', 'generated_unit': 'U016', 'source': module['source'],
            'reset': 'RandWorld writes HealthB=100 and HealthR=100 at lines 351-352; RandYard calls RandWorld at 413 and 415.',
            'init_distinction': 'InitSimVars initializes adjacent configuration fields; it is not the health reset.',
            'original_COMDEF_module_identity': 'NOT_CLAIMED',
        },
        'declaration_and_xref_views': {
            'HealthB_int_far_declarations': {'src/S07/m35F5.c': 11, 'src/S08/m35F5.c': 48, 'src/S12/m384C.c': 386, 'src/S24/m39C7.c': 295, 'src/root/m015B.c': 583, 'src/root/m0894.c': 39, 'src/root/m0E2E.c': 23, 'src/root/m10F7.c': 47, 'src/root/m1383.c': 16},
            'HealthR_int_far_declarations': {'src/S07/m35F5.c': 12, 'src/S08/m35F5.c': 49, 'src/S12/m384C.c': 382, 'src/S24/m39C7.c': 296, 'src/root/m015B.c': 395, 'src/root/m0894.c': 40, 'src/root/m0F3F.c': 13, 'src/root/m1383.c': 31},
            'HealthB_numeric_alias_declarations': {'src/S25/m39C7.c': 47, 'src/S25/m3BA4.c': 49, 'src/root/m0250.c': 963},
            'HealthR_numeric_alias_declarations': {'src/root/m0250.c': 964},
            'SaveRec_BYTE_declarations': ['src/S09/m35F5.c:763-764'],
            'SaveRec_lifecycle': 'LoadGame and SaveGame generic loops pass the table-held far address to read/write for 2 bytes at lines 123-127 and 170-176.',
            'address_escapes': ['S09 persistent SaveRec table stores address', 'root:0250 DrawEditGraphs uses stack-local vals[3] pointer array at lines 986, 990, 993; it does not escape'],
            'aggregate_or_interior_views': 'No larger aggregate or interior offset view identified for HealthB/HealthR; registered aliases are exact-base aliases.',
            'history_view': 'S24 HistUpdate copies values into other 64-word arrays; it takes no pointer to these scalars.',
        },
        'lifecycle_xrefs': [
            {'module': 'S07:35F5', 'use': 'CheatKeys writes 100/0 and cheat-revival values (115-125,181).'},
            {'module': 'S08:35F5', 'use': 'RandWorld resets both to 100 (351-352); RandYard routes through RandWorld (413,415).'},
            {'module': 'S12:384C', 'use': 'DrawMapData reads both for health bars (399,404).'},
            {'module': 'S24:39C7', 'use': 'HistUpdate samples both by value (306-307).'},
            {'module': 'S25:39C7 / S25:3BA4', 'use': 'HealthB alias is read, incremented and decremented across simulation/food/dig paths; DoAntMoveY reads/decrements it.'},
            {'module': 'root:015B', 'use': 'XferPatch/MysteryButton reset one or both values to zero (428,630-631).'},
            {'module': 'root:0894', 'use': 'FeedAnts decrements/clamps both and DoAntSimA reads them (269-300).'},
            {'module': 'root:0F3F', 'use': 'red simulation reads, raises/caps and decrements HealthR (136,448,478,636,669-720,797,854).'},
            {'module': 'root:10F7', 'use': 'EatMyFood can raise/cap HealthB; SetMyHealth is MeHealth-specific (1044-1056,1087-1094).'},
            {'module': 'root:1383', 'use': 'GstrB/GstrR read both for strategy thresholds (119-123,214-220).'},
        ],
        'size_basis': 'Two-byte word views plus one SaveRec transfer of size=2,count=1 per scalar and independent zero/nonzero RTLink controls; not declaration-size-only or inter-address gap inference.',
    }

    report = {
        'schema': 'simant-dos-health-pair-self-contained-probe-v1',
        'status': 'RESEARCH_ONLY_NOT_ADMITTED',
        'admission_eligible': False,
        'inputs': inputs,
        'source_module': {'key': 'S08:35F5', 'source': module['source'], 'sha256': full['source_hash'],
                          'profile': full['profile'], 'flags': full['flags'], 'compiler_basename': 'U016',
                          'manifest_source_pin_matches': True},
        'source_edits': {'counts': full['edit_counts'],
                         'exactly_two_extern_to_tentative_definition_edits': True,
                         'control_source_sha256': hashlib.sha256(full['source_raw']).hexdigest(),
                         'candidate_source_sha256': hashlib.sha256(full['candidate_source'].encode('ascii')).hexdigest()},
        'whole_module_compile_comparison': whole_module,
        'runtime_owner': {
            'source': str(owner_path.relative_to(ROOT)).replace('\\', '/'),
            'object_sha256': hashlib.sha256(owner_bytes).hexdigest(),
            'source_shape': 'minimal typed int far HealthB/HealthR tentative definitions plus test-only overlay word-sum accessor',
            'communal_rows': owner_omf.communals,
            'matches_fresh_full_U016_candidate_communal_records': owner_records_match,
            'full_U016_object_linked': False,
            'game_function_definitions_or_calls': 0,
        },
        'negative_owner': {'source': str(bad_path.relative_to(ROOT)).replace('\\', '/'),
                           'object_sha256': hashlib.sha256(bad_bytes).hexdigest(),
                           'communal_names': [c['name'] for c in bad_omf.communals],
                           'health_publics': sorted(expected_names & bad_public_names),
                           'is_initialized_nonzero_contrast': bad_owner_is_contrast},
        'runtime_cases': cases_report,
        'runtime_cases_expected_outcomes_pass': len(cases_report) == 12 and all(r['passed'] for r in cases_report),
        'source_ownership_packet': packet,
        'limits': [
            'Full U016 object is compiled and compared but never linked into the runtime fixtures.',
            'The minimal owner overlay accessor is test-only, not a game function definition.',
            'RandWorld reset semantics are source-anchored but RandWorld is not executed by this probe.',
            'RTLink aliases are supplied explicitly with DEFINE; production source-only alias binding remains a separate integration dependency.',
            'No historical COMDEF-producing object identity is claimed.',
            'Full source-only game/save-load lifetime acceptance remains pending.',
        ],
        'denied_oracle_reads': denied,
        'all_probe_gates_pass': whole_module['passed'] and owner_records_match and bad_owner_is_contrast and
                                len(cases_report) == 12 and all(r['passed'] for r in cases_report) and not denied,
    }
    report_path = OUT / 'report.json'
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    write_packet_markdown(OUT / 'report.md', report)
    return 0 if report['all_probe_gates_pass'] else 1


def write_packet_markdown(path, report):
    module = report['source_module']
    compile_report = report['whole_module_compile_comparison']
    packet = report['source_ownership_packet']
    lines = [
        '# HealthB / HealthR self-contained ownership and runtime probe',
        '',
        'Status: **RESEARCH_ONLY_NOT_ADMITTED**. This scratch probe changes no canonical source, manifest, journal, or tool.',
        '',
        '## Source owner and extent evidence',
        '',
        f"The manifest resolves `S08:35F5` to `{module['source']}` and pins its bytes to `{module['sha256']}`. The probe loads profile `{module['profile']}` and flags `{', '.join(module['flags'])}`, compiling both control and candidate as basename `U016`. The candidate changes only `extern int far HealthB;` and `extern int far HealthR;` to tentative `int far` definitions. It does not consume an ignored prebuilt U016 object.",
        '',
        f"Whole-module comparison: `{compile_report['passed']}`. Every live emitted segment byte and extent, segment definition, group, public, legacy fixup, normalized fixup sequence, and full ordered linker-fixup row is compared. Existing external names stay ordered; only HealthB/HealthR external scopes become communal. Candidate COMDEF check: `{compile_report['exactly_two_expected_far_communal_records']}` for exactly two far length-2 records. Object size delta: {compile_report['object_size_delta_bytes']} bytes.",
        '',
        'This is a compiler contribution comparison, not evidence of the historical COMDEF-producing object identity. `RandWorld` is the source-functional initialization owner: it writes both values to 100 at `src/S08/m35F5.c:351-352`; `RandYard` reaches it at lines 413 and 415. `InitSimVars` initializes adjacent configuration state, not these health scalars.',
        '',
        '## Selected scalar pair',
        '',
        '| Scalar | Registered address | Independent size/lifetime anchors |',
        '| --- | --- | --- |',
        '| `HealthB` | `50F6:10BE` | `int far` word views; `src/S09/m35F5.c:1061` has `{2,1,&HealthB}` |',
        '| `HealthR` | `50F6:01FE` | `int far` word views; `src/S09/m35F5.c:1062` has `{2,1,&HealthR}` |',
        '',
        'S09 declares byte-array address views at lines 763-764. `LoadGame` and `SaveGame` pass the table-held far pointers to generic 2-byte `read`/`write` loops at lines 123-127 and 170-176. That makes the byte declaration an address/serialization view; it does not by itself assign storage type or extent. The two-byte extent is supported by word lvalues, the one-item `size=2,count=1` rows, and successful independent byte/word coherence tests—not by declared-size or gap inference.',
        '',
        '## Source lifecycle and every known view',
        '',
        '- `S07:35F5` `CheatKeys` writes 100/0 and revival values (115-125, 181).',
        '- `S08:35F5` `RandWorld` resets both to 100 (351-352); `RandYard` calls it (413, 415).',
        '- `S09:35F5` retains both addresses in the SaveRec table for generic load/save byte transfers.',
        '- `S12:384C` `DrawMapData` reads them for health bars (399, 404); `S24:39C7` `HistUpdate` copies values by value to 64-entry history arrays (306-307).',
        '- `S25:39C7` and `S25:3BA4` use the registered `fd_50F6_10BE` alias for reads, increments and decrements; `root:0250` declares both numeric aliases and keeps pointers in a local `vals[3]`, stores them at line 990, dereferences at 993, and does not let that local vector escape.',
        '- `root:015B` resets health on transfer/mystery paths (428, 630-631); `root:0894` decrements/clamps both and reads them for ant death probability (269-300).',
        '- `root:0F3F` reads/raises/caps/decrements red health; `root:10F7` `EatMyFood` can raise/cap black health; `root:1383` reads both for strategy thresholds.',
        '',
        'The registry records exact-base aliases `fd_50F6_10BE -> HealthB` and `fd_50F6_01FE -> HealthR`. The source-only intake still needs a reviewed one-owner binding for these numeric names. No larger aggregate or interior view of either scalar was found; the history arrays are copies, not pointer aliases.',
        '',
        '## Runtime controls',
        '',
        'The runtime owner is a minimal typed far-int pair plus a test-only overlay word-sum accessor. Its COMDEF records must equal the newly compiled full-U016 candidate records, but the full U016 object is never linked into runtime cases. The accessor is a test-only overlay function, not a definition or stand-in for a game function. Independent MSC word and SaveRec-shaped BYTE consumers run with pinned MSC startup/runtime under both RTLink 4.00 and 6.10.',
        '',
        '| Linker | Word exact alias | SaveRec BYTE exact alias | Wrong alias controls | Initialized nonzero controls |',
        '| --- | --- | --- | --- | --- |',
    ]
    for linker in ('rtlink400', 'rtlink610'):
        rows = {row['case']: row for row in report['runtime_cases'] if row['linker'] == linker}
        def outcome(name):
            row = rows[name]
            return f"{row['actual']} (expected {row['expected']})"
        lines.append('| ' + linker + ' | ' +
                     outcome('typed_owner_word_exact_aliases') + ' | ' +
                     outcome('typed_owner_SaveRec_BYTE_exact_aliases') + ' | ' +
                     outcome('typed_owner_word_wrong_black_alias_plus2') + ', ' +
                     outcome('typed_owner_SaveRec_BYTE_wrong_red_alias_plus2') + ' | ' +
                     outcome('initialized_nonzero_owner_word_contrast') + ', ' +
                     outcome('initialized_nonzero_owner_SaveRec_BYTE_contrast') + ' |')
    lines += [
        '',
        'Exact alias cases explicitly define `_fd_50F6_10BE = _HealthB` and `_fd_50F6_01FE = _HealthR`; shifted-by-two aliases fail. Both consumers check initial zero fill and cross-view writes. The byte consumer uses independent `{2,1,&HealthB}` / `{2,1,&HealthR}` rows and observes the word sum through the owner overlay accessor.',
        '',
        '## Candidate shortlist and remaining proof dependencies',
        '',
        'The ten worklist candidates with clear scalar/lifecycle evidence were: ' + ', '.join(
            f"`{row['name']}` ({row['offset']})" for row in packet['candidate_shortlist']) + '. The selected pair is the first cohesive two-colony health family; the SaveRec rows are used only with semantic/reset/read-write and consumer evidence.',
        '',
        'Remaining dependencies are the reviewed source-only alias binding and complete source-only game/save-load lifetime evidence. The original COMDEF owner remains unidentified. This probe never runs `RandWorld` and is not source-only DOS acceptance.',
        '',
        'Detailed pins, OMF comparisons, compiler records, and per-case file hashes are in `report.json`.',
    ]
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


if __name__ == '__main__':
    raise SystemExit(main())
