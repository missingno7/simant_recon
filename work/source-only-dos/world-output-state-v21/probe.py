#!/usr/bin/env python3
"""Scratch-only MSC 6.00AX/RTLink/DOSBox-X controls for world-output storage."""
from __future__ import annotations
import hashlib, json, os, re, shutil, subprocess, sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'layout/manifest.json').is_file())
OUT = ROOT / 'build/workers/dos_world_output_words_v21'
RUNTIME = OUT / 'runtime'
FIXTURES = RUNTIME / 'fixtures'
PROVIDER = OUT / 'providers/WORLDOUT.C'
REPORT = RUNTIME / 'probe-v21.json'
PROFILE = 'msc600ax'
FLAGS = ['/AL', '/Os', '/Oe', '/Og', '/Zi']

# Exact typed views from the pinned 156-source graph. 0472 deliberately has a
# union of its two complete, four-byte source views; its audited source actions
# are limited to literal-zero stores, with no source readers or escapes.
TARGETS = [
    ('fd_50F6_0200', 'int', 2, True),
    ('fd_50F6_020E', 'int', 2, True),
    ('fd_50F6_0224', 'int', 2, True),
    ('fd_50F6_0242', 'int', 2, True),
    ('fd_50F6_035E', 'int', 2, True),
    ('fd_50F6_036C', 'int', 2, True),
    ('fd_50F6_0472', 'unsigned long', 4, False),
    ('fd_50F6_09FA', 'int', 2, True),
    ('fd_50F6_0A00', 'int', 2, True),
    ('fd_50F6_1040', 'int', 2, True),
    ('fd_50F6_1068', 'long', 4, True),
    ('fd_50F6_1082', 'long', 4, True),
    ('fd_50F6_108E', 'long', 4, True),
    ('fd_50F6_10A2', 'long', 4, True),
    ('fd_50F6_10B2', 'int', 2, True),
    ('fd_50F6_10C0', 'int', 2, True),
]
SAVE_TARGETS = [row for row in TARGETS if row[3]]
SYMBOLS = ['_' + row[0] for row in TARGETS]
EXACT_ALIASES = [f'ProbeE{i}' for i in range(len(TARGETS))]
SAVE_ALIASES = {row[0]: f'ProbeS{i}' for i, row in enumerate(SAVE_TARGETS)}
PROVIDER_TEXT = '''\
int far fd_50F6_0200;
int far fd_50F6_020E;
int far fd_50F6_0224;
int far fd_50F6_0242;
int far fd_50F6_035E;
int far fd_50F6_036C;
/* The source graph declares both long views; all four observed stores write zero. */
typedef union { long signed_view; unsigned long unsigned_view; } FAR_LONG_VIEWS;
FAR_LONG_VIEWS far fd_50F6_0472;
int far fd_50F6_09FA;
int far fd_50F6_0A00;
int far fd_50F6_1040;
long far fd_50F6_1068;
long far fd_50F6_1082;
long far fd_50F6_108E;
long far fd_50F6_10A2;
int far fd_50F6_10B2;
int far fd_50F6_10C0;
'''

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'tools'))
import compiler  # noqa: E402
import source_only_dos as dos  # noqa: E402
from omf import OmfReader  # noqa: E402


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin(path: Path, expected: str | None = None) -> dict:
    path = path.resolve()
    raw = path.read_bytes()
    actual = sha(raw)
    if expected is not None and actual != expected:
        raise RuntimeError(f'input pin drift: {path}')
    try:
        rel = path.relative_to(ROOT).as_posix()
    except ValueError:
        rel = str(path).replace('\\', '/')
    return {'path': rel, 'sha256': actual, 'size': len(raw)}


def write_source(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding='ascii', newline='')


def compile_fixture(stem: str, source: str) -> dict:
    if len(stem) > 8:
        raise ValueError('MSC object basename must fit 8.3')
    cpath, opath = FIXTURES / f'{stem}.C', FIXTURES / f'{stem}.OBJ'
    logpath = FIXTURES / f'{stem}.COMPILE.LOG'
    write_source(cpath, source)
    result = compiler.compile_c(source, PROFILE, FLAGS, basename=stem)
    logpath.write_text(result.log, encoding='latin1', newline='')
    if not result.ok or result.obj is None:
        raise RuntimeError(f'MSC compile failed for {stem}:\n{result.log}')
    opath.write_bytes(result.obj)
    return {'source_path': cpath, 'object_path': opath, 'log_path': logpath,
            'source': source, 'object': result.obj, 'log': result.log}


def normalized_obj(obj) -> dict:
    return {
        'segments': {name: {'length': obj.segment_lengths.get(name, 0),
                            'bytes': len(data), 'sha256': sha(data)}
                     for name, data in sorted(obj.segments.items())},
        'segment_defs': obj.segment_defs, 'groups': obj.groups,
        'publics': obj.publics, 'local_publics': obj.local_publics,
        'fixups': obj.fixups, 'linker_fixups': obj.linker_fixups,
    }


def communal_map(obj) -> dict[str, dict]:
    rows = {}
    for row in obj.communals:
        if row['name'] in rows:
            raise RuntimeError(f'duplicate far communal {row["name"]}')
        rows[row['name']] = row
    return rows


def source_declarations(type_overrides=None, initialize=None) -> str:
    type_overrides = type_overrides or {}
    lines = []
    for name, type_name, _size, _saved in TARGETS:
        actual_type = type_overrides.get(name, type_name)
        if name == 'fd_50F6_0472':
            if actual_type == 'views-union':
                lines += ['typedef union { long signed_view; unsigned long unsigned_view; } FAR_LONG_VIEWS;',
                          'FAR_LONG_VIEWS far fd_50F6_0472;']
            else:
                lines.append(f'{actual_type} far {name};')
        elif name == initialize:
            lines.append(f'{actual_type} far {name} = 1;')
        else:
            lines.append(f'{actual_type} far {name};')
    return '\n'.join(lines) + '\n'


def summarize_provider(raw: bytes) -> dict:
    obj = OmfReader(communals=True).read(raw)
    rows = communal_map(obj)
    expected = {symbol: size for (_name, _type, size, _saved), symbol in zip(TARGETS, SYMBOLS)}
    measured = {name: row['length'] for name, row in rows.items()}
    live_segments = {'_DATA', 'CONST', '_BSS', 'FAR_DATA', 'FAR_BSS'}
    live_payloads = {name: len(data) for name, data in obj.segments.items()
                     if name in live_segments and len(data)}
    live_fixups = [x for x in obj.fixups if x['segment'] in live_segments]
    live_code = {name: n for name, n in obj.segment_lengths.items()
                 if name.endswith('_TEXT') and n}
    if measured != expected or len(rows) != len(TARGETS):
        raise RuntimeError(f'WORLDOUT communal lengths differ: {measured!r}')
    if any(row['kind'] != 'far' for row in rows.values()):
        raise RuntimeError('WORLDOUT contains a non-far communal')
    if live_payloads or live_fixups or live_code or obj.publics:
        raise RuntimeError('WORLDOUT is not a data-only zero-storage provider')
    for name, type_name, size, _saved in TARGETS:
        row = rows['_' + name]
        if row['count'] * row['element_size'] != size:
            raise RuntimeError(f'communal byte count mismatch: {name}')
        if type_name == 'int' and (row['count'], row['element_size']) != (2, 1):
            raise RuntimeError(f'int far scalar OMF shape mismatch: {row}')
        if type_name == 'long' and (row['count'], row['element_size']) != (4, 1):
            raise RuntimeError(f'long far scalar OMF shape mismatch: {row}')
    return {'omf': normalized_obj(obj), 'communals': obj.communals,
            'communal_lengths': measured, 'publics': obj.publics,
            'nonzero_live_segment_payloads': live_payloads,
            'live_storage_fixups': live_fixups, 'nonempty_code_segments': live_code,
            'source_function_definitions': 0}


def typed_raw_source() -> str:
    lines = []
    for i, (name, typ, _size, _saved) in enumerate(TARGETS):
        lines += [f'extern {typ} far {name};', f'extern {typ} far {EXACT_ALIASES[i]};']
    for name, typ, _size, _saved in SAVE_TARGETS:
        lines.append(f'extern {typ} far {SAVE_ALIASES[name]};')
    lines += ['extern int far puts(char far *text);',
              'struct SaveRec { int size; int count; void far *data; };']
    save_rows = [f'    {{{size}, 1, (void far *)&{SAVE_ALIASES[name]}}}'
                 for name, _type, size, _saved in SAVE_TARGETS]
    lines += [f'struct SaveRec far ProbeSaveTable[{len(SAVE_TARGETS)}] = {{',
              ',\n'.join(save_rows), '};', 'int main(void)', '{',
              '    unsigned char far *bytes;', '    int i;']
    for i, (name, _type, _size, _saved) in enumerate(TARGETS):
        lines.append(f'    if (&{name} != &{EXACT_ALIASES[i]}) {{ puts("FAIL_EXACT_BASE"); return 1; }}')
        lines.append(f'    if ({name} != 0) {{ puts("FAIL_ZERO_CRT"); return 2; }}')
    for i, (name, _type, size, _saved) in enumerate(SAVE_TARGETS):
        lines += [f'    if (ProbeSaveTable[{i}].size != {size} || ProbeSaveTable[{i}].count != 1) {{ puts("FAIL_SAVEREC_EXTENT"); return 3; }}',
                  f'    if (ProbeSaveTable[{i}].data != (void far *)&{name}) {{ puts("FAIL_SAVEREC_BASE"); return 4; }}',
                  f'    bytes = (unsigned char far *)ProbeSaveTable[{i}].data;',
                  f'    for (i = 0; i < {size}; i++) if (bytes[i] != 0) {{ puts("FAIL_SAVEREC_ZERO"); return 5; }}']
    # 0472 has no SaveRec row: inspect its bytes without adding a fake row.
    lines += ['    bytes = (unsigned char far *)&fd_50F6_0472;',
              '    for (i = 0; i < 4; i++) if (bytes[i] != 0) { puts("FAIL_0472_ZERO"); return 6; }']
    for i, (name, typ, size, _saved) in enumerate(TARGETS):
        if size == 2:
            typed_value, raw_value = 0x1201 + i * 0x101, 0x3101 + i * 0x101
            typed_literal, raw_literal = f'0x{typed_value:04x}', f'0x{raw_value:04x}'
        else:
            typed_value, raw_value = 0x11223344 + i * 0x010101, 0x22334455 + i * 0x010101
            suffix = 'UL' if typ == 'unsigned long' else 'L'
            typed_literal, raw_literal = f'0x{typed_value:08x}{suffix}', f'0x{raw_value:08x}{suffix}'
        typed_bytes = [(typed_value >> (8*j)) & 255 for j in range(size)]
        raw_bytes = [(raw_value >> (8*j)) & 255 for j in range(size)]
        lines += [f'    {name} = {typed_literal};',
                  f'    if ({name} != {typed_literal}) {{ puts("FAIL_TYPED_READ"); return 7; }}',
                  f'    bytes = (unsigned char far *)&{name};']
        test = ' || '.join(f'bytes[{j}] != 0x{b:02x}' for j,b in enumerate(typed_bytes))
        lines.append(f'    if ({test}) {{ puts("FAIL_TYPED_BYTES"); return 8; }}')
        lines.extend(f'    bytes[{j}] = 0x{b:02x};' for j,b in enumerate(raw_bytes))
        lines.append(f'    if ({name} != {raw_literal}) {{ puts("FAIL_RAW_TYPED_READ"); return 9; }}')
    lines += ['    puts("PASS_TYPED_RAW_SAVEREC_ZERO_CRT");', '    return 0;', '}']
    return '\n'.join(lines) + '\n'


def zero_initializer_source() -> str:
    lines = []
    for i, (name, typ, _size, _saved) in enumerate(TARGETS):
        lines += [f'extern {typ} far {name};', f'extern {typ} far {EXACT_ALIASES[i]};']
    lines += ['extern int far puts(char far *text);', 'int main(void)', '{']
    for i, (name, _typ, _size, _saved) in enumerate(TARGETS):
        lines.append(f'    if (&{name} != &{EXACT_ALIASES[i]}) {{ puts("FAIL_ALIAS"); return 1; }}')
    lines += ['    if (fd_50F6_0200 != 0) { puts("INITIALIZED_NONZERO_OWNER_DETECTED"); return 0; }',
              '    puts("FAIL_INITIALIZER_NOT_DETECTED");', '    return 1;', '}']
    return '\n'.join(lines) + '\n'


def wrong_signedness_source() -> str:
    return '''\
extern unsigned long far fd_50F6_1068;
extern unsigned long far ProbeSign;
extern int far puts(char far *text);
int main(void)
{
    if (&fd_50F6_1068 != &ProbeSign) { puts("FAIL_SIGN_ALIAS"); return 1; }
    fd_50F6_1068 = 0xffffffffUL;
    if (fd_50F6_1068 > 0x7fffffffUL) {
        puts("WRONG_UNSIGNED_VIEW_DETECTED");
        return 0;
    }
    puts("FAIL_UNSIGNED_VIEW_NOT_DISTINGUISHED");
    return 1;
}
'''


def shifted_saverec_source() -> str:
    lines = []
    for i, (name, typ, _size, _saved) in enumerate(TARGETS):
        lines += [f'extern {typ} far {name};', f'extern {typ} far {EXACT_ALIASES[i]};']
    for name, typ, _size, _saved in SAVE_TARGETS:
        lines.append(f'extern {typ} far {SAVE_ALIASES[name]};')
    rows = [f'    {{{size}, 1, (void far *)&{SAVE_ALIASES[name]}}}'
            for name, _type, size, _saved in SAVE_TARGETS]
    lines += ['struct SaveRec { int size; int count; void far *data; };',
              f'struct SaveRec far ProbeSaveTable[{len(SAVE_TARGETS)}] = {{',
              ',\n'.join(rows), '};', 'extern int far puts(char far *text);',
              'int main(void)', '{']
    for i, (name, _typ, _size, _saved) in enumerate(TARGETS):
        lines.append(f'    if (&{name} != &{EXACT_ALIASES[i]}) {{ puts("FAIL_EXACT_ALIAS"); return 1; }}')
    for i, (name, _typ, _size, _saved) in enumerate(SAVE_TARGETS):
        lines.append(f'    if (ProbeSaveTable[{i}].data != (void far *)&{name}) {{ puts("SHIFTED_SAVEREC_BASE_DETECTED"); return 0; }}')
    lines += ['    puts("FAIL_SHIFTED_SAVEREC_BASE_NOT_DETECTED");', '    return 1;', '}']
    return '\n'.join(lines) + '\n'


def parse_public_sections(map_text: str) -> dict[str, dict[str, str]]:
    headings = list(re.finditer(r'(?im)^\s*Address\s+Publics by (Name|Value)\s*$', map_text))
    result = {'Name': {}, 'Value': {}}
    for i, match in enumerate(headings):
        section = match.group(1)
        end = headings[i+1].start() if i+1 < len(headings) else len(map_text)
        for line in map_text[match.end():end].splitlines():
            row = re.match(r'\s*([0-9A-Fa-f]+:[0-9A-Fa-f]+)\s+(?:Res|Abs)\s+(\S+)', line)
            if row:
                result[section][row.group(2).lower()] = row.group(1).upper()
    return result


def addr_pair(text: str) -> tuple[int,int]:
    seg, off = text.split(':')
    return int(seg,16), int(off,16)


def exact_alias_specs():
    return [('_' + alias, '_' + row[0], 0) for alias,row in zip(EXACT_ALIASES,TARGETS)]


def save_alias_specs(shift_name=None, delta=0):
    return [('_' + SAVE_ALIASES[row[0]], '_' + row[0],
             delta if row[0] == shift_name else 0) for row in SAVE_TARGETS]


def case_link(profile, case, consumer, owner, aliases, expected, required, relations,
              libraries, linker, runner, tool_dir) -> dict:
    folder = RUNTIME / profile / case
    folder.mkdir(parents=True,exist_ok=True)
    folder.resolve().relative_to(RUNTIME.resolve())
    for leaf in ('PROBE.EXE','PROBE.MAP','RUN.LOG','LINK.LOG'):
        (folder/leaf).unlink(missing_ok=True)
    (folder/'CRT.OBJ').write_bytes(consumer)
    (folder/'OWNER.OBJ').write_bytes(owner)
    for row in libraries:
        shutil.copyfile(row['path'],folder/Path(row['path']).name.upper())
    script = ('OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n'
              'LIBRARY LLIBCR, LIBH\r\nFILE CRT\r\nBEGINAREA\r\n'
              'SECTION FILE OWNER\r\nENDAREA\r\n') + ''.join(a+'\r\n' for a in aliases)
    (folder/'PROBE.LNK').write_bytes(script.encode('ascii'))
    (folder/'RTLINK.CFG').write_bytes(b'SYNTAX = FREEFORMAT\r\n')
    (folder/'RUN.BAT').write_bytes((f'@echo off\r\nD:\\{linker["executable"]} @PROBE.LNK < NUL > LINK.LOG\r\n'
                                    'PROBE.EXE > RUN.LOG\r\n').encode('ascii'))
    config=[]
    for section,settings in runner['conf'].items():
        config += ['['+section+']'] + [f'{k}={v}' for k,v in settings.items()]
    config += ['[autoexec]',f'mount c "{folder}"',f'mount d "{tool_dir}" -ro',
               'c:','call RUN.BAT','exit']
    (folder/'dosbox.conf').write_text('\n'.join(config)+'\n',encoding='utf-8')
    env=os.environ.copy(); env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
    timed_out=False
    try:
        done=subprocess.run([runner['path'],'-conf',str(folder/'dosbox.conf'),
                             '-fastlaunch','-exit','-nomenu'],cwd=folder,env=env,
                            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                            timeout=90,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        runner_rc=done.returncode
    except subprocess.TimeoutExpired:
        timed_out=True; runner_rc=-1
    rp,lp,mp=folder/'RUN.LOG',folder/'LINK.LOG',folder/'PROBE.MAP'
    rb=rp.read_bytes() if rp.exists() else b''
    lb=lp.read_bytes() if lp.exists() else b''
    mb=mp.read_bytes() if mp.exists() else b''
    run_text,link_text,map_text=rb.decode('latin1'),lb.decode('latin1'),mb.decode('latin1')
    sections=parse_public_sections(map_text)
    required=sorted(x.lower() for x in required)
    section_evidence={}
    for section in ('Name','Value'):
        section_evidence[section]={
            'heading_present': bool(re.search(r'(?im)^\s*Address\s+Publics by '+section+r'\s*$',map_text)),
            'missing_required_publics':[n for n in required if n not in sections[section]],
            'required_public_addresses':{n:sections[section].get(n) for n in required}}
    publics_both=all(not section_evidence[s]['missing_required_publics'] for s in ('Name','Value'))
    relation_rows=[]; relations_ok=True
    for alias,target,delta in relations:
        na,nt=sections['Name'].get(alias.lower()),sections['Name'].get(target.lower())
        va,vt=sections['Value'].get(alias.lower()),sections['Value'].get(target.lower())
        passed=False
        if na and nt and va and vt:
            ns,no=addr_pair(na); nts,nto=addr_pair(nt)
            vs,vo=addr_pair(va); vts,vto=addr_pair(vt)
            passed=(ns==nts and no==nto+delta and vs==vts and vo==vto+delta)
        relations_ok &= passed
        relation_rows.append({'alias':alias.lower(),'target':target.lower(),
            'expected_displacement_bytes':delta,'name_alias_address':na,'name_target_address':nt,
            'value_alias_address':va,'value_target_address':vt,'passed':passed})
    errors=('unresolved external','undefined symbol','warning wrt','link error','fatal error')
    link_clean=((folder/'PROBE.EXE').exists() and bool(link_text.strip()) and
                'pocket soft' in link_text.lower() and not timed_out and
                not any(x in link_text.lower() for x in errors))
    map_clean=bool(map_text) and publics_both and relations_ok
    marker=run_text.strip()
    passed=(marker==expected and runner_rc==0 and not timed_out and link_clean and map_clean)
    return {'linker':profile,'case':case,'expected_marker':expected,
        'actual_marker_verbatim':run_text,'actual_marker_bytes_hex':rb.hex(),
        'actual_marker_normalized_for_check':marker,'expected_outcome_passed':passed,
        'runner_returncode':runner_rc,'timed_out':timed_out,'exe_created':(folder/'PROBE.EXE').exists(),
        'link_clean':link_clean,'link_log_verbatim':link_text,'link_log_bytes_hex':lb.hex(),
        'map_clean':map_clean,'both_public_sections':section_evidence,
        'all_required_publics_in_both_sections':publics_both,'required_publics':required,
        'alias_target_address_relations':relation_rows,
        'case_artifacts':[pin(p) for p in sorted(folder.iterdir(),key=lambda p:p.name.lower()) if p.is_file()]}


def ensure_pinned_source_graph(audit_path):
    audit=json.loads(audit_path.read_text(encoding='utf-8'))
    if audit['source_scope']['canonical_127_plus_effective_strict_29']!=156 or len(audit['source_pins'])!=156:
        raise RuntimeError('source audit does not contain the full canonical/effective graph')
    observed=[]
    for row in audit['source_pins']:
        item=pin(ROOT/row['path'],row['expected_sha256'])
        if item['size']!=row['size_expected']:
            raise RuntimeError('pinned source size changed: '+row['path'])
        observed.append(item)
    if audit['source_scope']['source_pin_matches']!=156 or audit['source_scope']['source_pin_mismatches']:
        raise RuntimeError('v20 source pin mismatch')
    return audit,observed


def run_runtime(owner_raw, initialized_raw, signed_consumer, positive_consumer,
                shifted_consumer, init_consumer, manifest, toolchain):
    libraries=list(manifest['runtime']['libraries'].values())
    runner=toolchain['runners']['dosbox-x']
    exact=exact_alias_specs(); saves=save_alias_specs()
    target_publics=[x.lower() for x in SYMBOLS]
    exact_names=['_'+x for x in EXACT_ALIASES]
    save_names=['_'+SAVE_ALIASES[row[0]] for row in SAVE_TARGETS]
    specs=[
        ('typed_raw_saverec_zero_crt',positive_consumer,owner_raw,
         [f'DEFINE {a} = {t}' for a,t,_ in exact+saves],
         'PASS_TYPED_RAW_SAVEREC_ZERO_CRT',
         target_publics+exact_names+save_names,exact+saves),
        ('wrong_unsigned_long_consumer',signed_consumer,owner_raw,
         ['DEFINE _ProbeSign = _fd_50F6_1068'],'WRONG_UNSIGNED_VIEW_DETECTED',
         target_publics+['_probesign'],[('_ProbeSign','_fd_50F6_1068',0)]),
        ('initialized_nonzero_owner',init_consumer,initialized_raw,
         [f'DEFINE {a} = {t}' for a,t,_ in exact],
         'INITIALIZED_NONZERO_OWNER_DETECTED',
         target_publics+exact_names,exact),
        ('shifted_saverec_base',shifted_consumer,owner_raw,
         [f'DEFINE {a} = {t}' for a,t,_ in exact]+
         [f'DEFINE _{SAVE_ALIASES[row[0]]} = _{row[0]}'+
          (' + 2' if row[0]=='fd_50F6_0200' else '') for row in SAVE_TARGETS],
         'SHIFTED_SAVEREC_BASE_DETECTED',
         target_publics+exact_names+save_names,
         exact+save_alias_specs('fd_50F6_0200',2)),
    ]
    cases=[]; copied={}
    for profile in ('rtlink400','rtlink610'):
        linker=toolchain['linkers'][profile]
        tool_dir=compiler.pinned_tree(linker)
        copied[profile]=[pin(tool_dir/rel,digest) for rel,digest in linker['files'].items()]
        for case,consumer,owner,aliases,marker,required,relations in specs:
            cases.append(case_link(profile,case,consumer,owner,aliases,marker,required,
                                   relations,libraries,linker,runner,tool_dir))
    if len(cases)!=8 or not all(x['expected_outcome_passed'] for x in cases):
        raise RuntimeError('a runtime marker, link log, map section, or alias address check failed')
    return {'cases':cases,'all_expected_outcomes_pass':True,
        'linkers':['rtlink400','rtlink610'],'runner':runner,
        'linker_tool_copies':copied,
        'startup_contract':'The positive fixture uses pinned MSC 6.00AX CRT startup and checks all 16 candidate objects as zero at main. Its 15 source-grounded SaveRec rows check raw byte extents, counts and exact pointer bases.',
        'map_contract':'Every candidate owner public and each test alias used by a case appears in both Publics by Name and Publics by Value; each alias-to-owner address and expected byte displacement is recorded.'}


def main():
    RUNTIME.mkdir(parents=True,exist_ok=True); FIXTURES.mkdir(parents=True,exist_ok=True)
    compiler.WORK=(RUNTIME/'compiler-work').resolve()
    denied=dos.install_input_guard()
    identity_paths=[ROOT/'layout/manifest.json',ROOT/'layout/toolchain.json',ROOT/'layout/symbols.json',
        ROOT/'tools/compiler.py',ROOT/'tools/omf.py',ROOT/'tools/source_only_dos.py',
        ROOT/'build/workers/dos_far_word_inventory_v20/family-shortlist-v20.json',
        ROOT/'build/workers/dos_far_word_inventory_v20/source-receipts-v20.json',
        ROOT/'build/workers/dos_far_word_inventory_v20/routing-v20.json',
        OUT/'source-audit-v21.json',OUT/'numeric-alias-asm-review-v21.json']
    identity_before={str(p):pin(p) for p in identity_paths}
    source_audit,source_pins=ensure_pinned_source_graph(OUT/'source-audit-v21.json')
    numeric=json.loads((OUT/'numeric-alias-asm-review-v21.json').read_text(encoding='utf-8'))
    if numeric['pinned_source_paths']!=156 or not numeric['all_source_pins_match']:
        raise RuntimeError('numeric/ASM review does not cover the pinned source graph')
    PROVIDER.parent.mkdir(parents=True,exist_ok=True)
    write_source(PROVIDER,PROVIDER_TEXT)
    manifest=json.loads((ROOT/'layout/manifest.json').read_text(encoding='utf-8'))
    toolchain=compiler.toolchain()
    profile=compiler.verify_profile(PROFILE)

    primary=compiler.compile_c(PROVIDER_TEXT,PROFILE,FLAGS,basename='WORLDOUT')
    if not primary.ok or primary.obj is None:
        raise RuntimeError('WORLDOUT compile failed:\n'+primary.log)
    owner_object_path=OUT/'providers/WORLDOUT.OBJ'; owner_object_path.write_bytes(primary.obj)
    owner_log_path=OUT/'providers/WORLDOUT.COMPILE.LOG'
    owner_log_path.write_text(primary.log,encoding='latin1',newline='')
    owner_obj=OmfReader(communals=True).read(primary.obj)
    owner_summary=summarize_provider(primary.obj)
    owner_rows=communal_map(owner_obj)

    # Width and signedness are measured as OMF shape controls, not game runtime failures.
    wide=compile_fixture('WIDEOWN',source_declarations({'fd_50F6_0200':'long'}))
    narrow=compile_fixture('NARROWN',source_declarations({'fd_50F6_1068':'int'}))
    unsigned=compile_fixture('UNSGOWN',source_declarations({'fd_50F6_1068':'unsigned long'}))
    wide_rows=communal_map(OmfReader(communals=True).read(wide['object']))
    narrow_rows=communal_map(OmfReader(communals=True).read(narrow['object']))
    unsigned_rows=communal_map(OmfReader(communals=True).read(unsigned['object']))
    if wide_rows['_fd_50F6_0200']['length']!=4 or narrow_rows['_fd_50F6_1068']['length']!=2:
        raise RuntimeError('wrong-width controls did not measure 4-byte and 2-byte commons')
    shape=lambda rows:{n:(r['kind'],r['count'],r['element_size'],r['length']) for n,r in sorted(rows.items())}
    if shape(unsigned_rows)!=shape(owner_rows):
        raise RuntimeError('signed and unsigned long provider OMF shapes differ')

    initialized=compile_fixture('INITOWN',source_declarations(initialize='fd_50F6_0200'))
    init_obj=OmfReader(communals=True).read(initialized['object'])
    init_commons=communal_map(init_obj); init_publics={p['name'] for p in init_obj.publics}
    if '_fd_50F6_0200' in init_commons or '_fd_50F6_0200' not in init_publics:
        raise RuntimeError('initializer did not replace the target communal with an initialized public')
    init_payloads={name:data.hex() for name,data in init_obj.segments.items()
                   if name.endswith('_DATA') or name in {'FAR_DATA','FAR_BSS'}}
    if not any('0100' in value.lower() for value in init_payloads.values()):
        raise RuntimeError('initializer control lacks its measured nonzero word')

    positive=compile_fixture('WORLDPOS',typed_raw_source())
    signed=compile_fixture('WRNGSIGN',wrong_signedness_source())
    shifted=compile_fixture('SHIFTREC',shifted_saverec_source())
    init_consumer=compile_fixture('INITCONS',zero_initializer_source())
    runtime=run_runtime(primary.obj,initialized['object'],signed['object'],positive['object'],
                        shifted['object'],init_consumer['object'],manifest,toolchain)

    compiler_rows=compiler.verify_profile(PROFILE)
    inputs=[pin(Path(__file__)),pin(PROVIDER),pin(OUT/'source-audit-v21.json'),
            pin(OUT/'numeric-alias-asm-review-v21.json'),
            pin(ROOT/'layout/manifest.json'),pin(ROOT/'layout/toolchain.json'),pin(ROOT/'layout/symbols.json'),
            pin(ROOT/'tools/compiler.py'),pin(ROOT/'tools/omf.py'),pin(ROOT/'tools/source_only_dos.py'),
            pin(ROOT/'build/workers/dos_far_word_inventory_v20/family-shortlist-v20.json'),
            pin(ROOT/'build/workers/dos_far_word_inventory_v20/source-receipts-v20.json'),
            pin(ROOT/'build/workers/dos_far_word_inventory_v20/routing-v20.json')]
    inputs.extend(source_pins)
    for rel,digest in compiler_rows['files'].items():
        inputs.append(pin(Path(compiler_rows['directory'])/rel,digest))
    runner=toolchain['runners']['dosbox-x']
    inputs.append(pin(Path(runner['path']),runner['sha256']))
    for row in manifest['runtime']['libraries'].values():
        inputs.append(pin(Path(row['path']),row['sha256']))
    for name in ('rtlink400','rtlink610'):
        linker=toolchain['linkers'][name]
        for rel,digest in linker['files'].items():
            inputs.append(pin(Path(linker['directory'])/rel,digest))
    artifacts=[pin(PROVIDER),pin(owner_object_path),pin(owner_log_path)]
    artifacts += [pin(p) for p in sorted(FIXTURES.iterdir()) if p.is_file()]
    for row in runtime['cases']:
        artifacts += row['case_artifacts']
    inputs_by_path={x['path']:x for x in inputs}
    input_pins=[inputs_by_path[k] for k in sorted(inputs_by_path)]
    artifact_by_path={x['path']:x for x in artifacts}
    artifacts=[artifact_by_path[k] for k in sorted(artifact_by_path)]
    identity_after={str(p):pin(p) for p in identity_paths}
    if identity_before!=identity_after:
        raise RuntimeError('shared source/tool/config identity changed during execution; refusing silent repin')
    family=json.loads((ROOT/'build/workers/dos_far_word_inventory_v20/family-shortlist-v20.json').read_text(encoding='utf-8'))['families'][1]
    row0472=next(x for x in family['members'] if x['address']=='50F6:0472')
    writes=row0472['all_source_producer_receipts']
    if (len(writes)!=4 or row0472['all_source_consumer_receipts'] or
        row0472['non_save_address_escape_receipts'] or row0472['save_rec_raw_byte_view_receipts'] or
        any(not re.search(r'=\s*0(?:L)?\s*;',x['text']) for x in writes)):
        raise RuntimeError('0472 source zero-only/full-view closure conditions do not hold')

    checks={
        'all_156_pinned_source_paths_match':True,
        'candidate_is_data_only_with_exact_16_far_communal_extents':True,
        'all_runtime_markers_match_under_both_linkers':runtime['all_expected_outcomes_pass'],
        'all_required_publics_and_alias_addresses_match_in_both_map_sections':all(
            c['all_required_publics_in_both_sections'] and c['map_clean'] and
            all(r['passed'] for r in c['alias_target_address_relations']) for c in runtime['cases']),
        'wrong_width_controls_are_omf_only':True,
        'no_original_inputs_or_denied_oracle_reads':not denied,
    }
    report={
        'schema':'simant-dos-world-output-words-runtime-probe-v21',
        'status':'SCRATCH_ONLY_ROOT_REVIEW_PENDING','root_reviewed':False,
        'profile':PROFILE,'flags':FLAGS,
        'candidate_owner':{
            'source':pin(PROVIDER),'object':pin(owner_object_path),'compile_log':pin(owner_log_path),
            'module_id':'source-owned:world-output-state','basename':'WORLDOUT',
            'definition_form':'data-only far scalar tentative definitions; one 4-byte union explicitly preserves the two source views of fd_50F6_0472',
            'members':[{'symbol':name,
                        'type':('long/unsigned long source-view union' if name=='fd_50F6_0472' else typ),
                        'source_typed_views':(['long','unsigned long'] if name=='fd_50F6_0472' else [typ]),
                        'source_derived_bytes':size,'SaveRec_view':saved,
                        'omf_communal':owner_rows['_'+name]} for name,typ,size,saved in TARGETS],
            'omf':owner_summary,'source_function_definitions':0,'live_initialized_storage_bytes':0,
            'live_storage_fixup_count':0,'historical_COMDEF_TU_order_placement_padding_claimed':False},
        'source_audit':{
            'report':pin(OUT/'source-audit-v21.json'),
            'numeric_alias_asm_report':pin(OUT/'numeric-alias-asm-review-v21.json'),
            'v20_source_scope':{'canonical_TUs':127,'effective_strict_sources':29,'unique_pinned_paths':156,'pin_matches':156},
            'complete_typed_producer_consumer_receipts_in_report':True,
            'exact_aliases_interiors_address_escapes_and_raw_SaveRec_views_recorded':True,
            'numeric_and_asm_review':{
                'asm_paths':numeric['asm_source_path_count'],
                'identifier_occurrences_in_asm':numeric['assembly_target_identifier_occurrences'],
                'literal_FAR_BSS_address_references':numeric['explicit_50F6_far_segment_numeric_hits'],
                'registered_interiors':0,'non_SaveRec_address_escapes':0,
                '0472_source_writes':writes,'0472_source_reads':row0472['all_source_consumer_receipts'],
                '0472_SaveRec_rows':row0472['save_rec_raw_byte_view_receipts'],
                '0472_contract':'Four-byte signed/unsigned long union view; every observed source store writes 32 zero bits; no source reader, SaveRec target or pointer escape exposes signedness. No gameplay meaning is assigned.'}},
        'contrasts':{
            'wrong_width':{
                'wide_source':pin(wide['source_path']),'wide_object':pin(wide['object_path']),
                'wide_measured_communal':wide_rows['_fd_50F6_0200'],'expected_bytes':2,
                'narrow_source':pin(narrow['source_path']),'narrow_object':pin(narrow['object_path']),
                'narrow_measured_communal':narrow_rows['_fd_50F6_1068'],'expected_bytes':4,
                'runtime_linked':False,'runtime_failure_claimed':False},
            'signedness':{
                'unsigned_provider_source':pin(unsigned['source_path']),'unsigned_provider_object':pin(unsigned['object_path']),
                'communal_shape_matches_signed_provider':shape(unsigned_rows)==shape(owner_rows),
                'runtime_consumer':'unsigned long view of source-declared signed fd_50F6_1068',
                'runtime_marker':'WRONG_UNSIGNED_VIEW_DETECTED',
                'omf_limit':'OMF records do not encode C signedness; source declarations/operations ground the 15 ordinary types and 0472 retains both observed views.'},
            'initializer':{
                'owner_source':pin(initialized['source_path']),'owner_object':pin(initialized['object_path']),
                'target_communal_absent':'_fd_50F6_0200' not in init_commons,
                'target_initialized_public_present':'_fd_50F6_0200' in init_publics,
                'initialized_data_payloads':init_payloads,'runtime_marker':'INITIALIZED_NONZERO_OWNER_DETECTED'},
            'shifted_SaveRec_base':{
                'consumer_source':pin(shifted['source_path']),'consumer_object':pin(shifted['object_path']),
                'shifted_alias':'_ProbeS0 = _fd_50F6_0200 + 2',
                'runtime_marker':'SHIFTED_SAVEREC_BASE_DETECTED','map_displacement_bytes':2}},
        'runtime':runtime,'source_tool_artifact_inputs':input_pins,'generated_artifacts':artifacts,
        'denied_oracle_reads':denied,
        'original_bytes_build_inputs':{'game_code':0,'game_data':0,'fallback_or_debt':0,'executable_fragments':0},
        'shared_identity_before_after_unchanged':True,'acceptance_checks':checks,
        'semantic_limits':[
            'The typed source graph lists all direct reads and writes; source values and legal numeric ranges beyond those operations remain open.',
            'No common struct, arbitrary SaveRec values, unobserved writers or historical storage lifetime are inferred.',
            'fd_50F6_0472 is source-observably a 4-byte zero-only object: exact source stores write zero, both declarations have 4-byte extent, and the pinned C/ASM graph has no read or address escape. Its purpose/persistence remain unknown.',
            'Runtime fixtures prove test-owned common allocation, MSC CRT zero startup, typed/byte views and linker map relations; they do not execute the game or prove historical communal origin/order.' ]}
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    candidate={
        'schema':'simant-dos-world-output-words-candidate-v21',
        'category':'SOURCE_ONLY_DOS_SOURCE_STORAGE_CANDIDATE',
        'status':'RESEARCH_ONLY_PENDING_ROOT_REVIEW','root_reviewed':False,
        'all_required_checks_pass':all(checks.values()),
        'module_id':'source-owned:world-output-state','basename':'WORLDOUT',
        'provider':pin(PROVIDER),'provider_object':pin(owner_object_path),
        'probe_source':pin(Path(__file__)),'probe_report':pin(REPORT),
        'source_audit':pin(OUT/'source-audit-v21.json'),
        'numeric_alias_asm_audit':pin(OUT/'numeric-alias-asm-review-v21.json'),
        'member_count':len(TARGETS),
        'members':[{'symbol':n,
                    'dos_type':('long/unsigned long source-view union' if n=='fd_50F6_0472' else t),
                    'source_typed_views':(['long','unsigned long'] if n=='fd_50F6_0472' else [t]),
                    'extent_bytes':size,'SaveRec_byte_view':saved}
                   for n,t,size,saved in TARGETS],
        'source_scope':{'canonical_TUs':127,'strict_effective_modules':29,'pinned_paths':156,'pin_mismatches':0},
        'runtime_cases':[{k:c[k] for k in ('linker','case','expected_marker','actual_marker_verbatim',
                         'expected_outcome_passed','link_clean','map_clean','all_required_publics_in_both_sections')}
                         for c in runtime['cases']],
        'original_bytes_build_inputs':report['original_bytes_build_inputs'],
        'denied_oracle_reads':denied,
        'historical_claim_limit':'No original COMDEF producer TU, ordering, absolute placement or padding claim. 0472 purpose, persistence and values beyond observed zero stores remain unknown.'}
    candidate_path=RUNTIME/'candidate-v21.json'
    candidate_path.write_text(json.dumps(candidate,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'report':str(REPORT.relative_to(ROOT)),
        'candidate':str(candidate_path.relative_to(ROOT)),
        'all_runtime_cases_pass':runtime['all_expected_outcomes_pass'],
        'members':len(TARGETS),'measured_lengths':owner_summary['communal_lengths'],
        'cases':[{'linker':c['linker'],'case':c['case'],'marker':c['actual_marker_normalized_for_check'],
                  'passed':c['expected_outcome_passed'],'map_clean':c['map_clean']}
                 for c in runtime['cases']]},indent=2))


if __name__=='__main__':
    main()
