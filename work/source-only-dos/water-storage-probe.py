from __future__ import annotations

from collections import Counter
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile


def find_root():
    for candidate in Path(__file__).resolve().parents:
        if (candidate / 'layout/manifest.json').is_file():
            return candidate
    raise RuntimeError('cannot locate repository root')


ROOT = find_root()
WORKER_ROOT = ROOT / 'build/workers/dos_farbss_declaration_inventory'
sys.path.insert(0, str(ROOT / 'tools'))
import compiler
import dos_source_bindings as bindings
import source_only_dos as dos
from omf import OmfReader


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def pin(path: Path, expected=None):
    raw, row=dos.pin(path,expected)
    return row

def check(path: str, number: int, expected: str):
    lines=(ROOT/path).read_text(encoding='utf-8',errors='replace').splitlines()
    got=lines[number-1].strip()
    if got != expected:
        raise RuntimeError(f'anchor drift at {path}:{number}: {got!r} != {expected!r}')
    return {'source':path,'line':number,'text':got}

def c_visible(lines):
    result=[]; block=False
    for line in lines:
        out=[]; i=0; quote=None; esc=False
        while i<len(line):
            c=line[i]; n=line[i+1] if i+1<len(line) else ''
            if block:
                out.append(' ')
                if c=='*' and n=='/': block=False; out.append(' '); i+=2; continue
            elif quote:
                out.append(' ')
                if esc: esc=False
                elif c=='\\': esc=True
                elif c==quote: quote=None
            elif c=='/' and n=='*': block=True; out.extend('  '); i+=2; continue
            elif c=='/' and n=='/': out.extend(' '*(len(line)-i)); break
            elif c in ('"',"'"): quote=c; out.append(' ')
            else: out.append(c)
            i+=1
        result.append(''.join(out))
    return result

def main():
    WORKER_ROOT.mkdir(parents=True, exist_ok=True)
    OUT = Path(tempfile.mkdtemp(prefix='water-storage-', dir=WORKER_ROOT))
    compiler.WORK = OUT / 'compiler-work'
    compiler.WORK.mkdir(parents=True, exist_ok=True)
    denied_oracle_reads = dos.install_input_guard()
    manifest_raw, manifest_pin = dos.pin(ROOT / 'layout/manifest.json')
    MANIFEST = json.loads(manifest_raw)
    symbols_raw, symbols_pin = dos.pin(ROOT / 'layout/symbols.json')
    SYMBOLS = json.loads(symbols_raw)['data']
    toolchain_raw, toolchain_pin = dos.pin(ROOT / 'layout/toolchain.json')
    TC = json.loads(toolchain_raw)

    # Direct source facts: current whole owner module and the source-bounded SaveRec table.
    OWNER_PATH = 'src/root/m0BE8.c'
    SAVE_PATH = 'src/S09/m35F5.c'
    root_mod = next(m for m in MANIFEST['modules'].values()
                    if m.get('source') == OWNER_PATH)
    save_mod = next(m for m in MANIFEST['modules'].values()
                    if m.get('source') == SAVE_PATH)
    if (root_mod.get('profile') != 'msc600ax' or root_mod.get('flags') !=
            ['/AL', '/Os', '/Oe', '/Og']):
        raise RuntimeError('manifest root:0BE8 profile or options changed')
    owner_raw, source_pin = dos.pin(ROOT / OWNER_PATH, root_mod['source_sha256'])
    save_raw, save_pin = dos.pin(ROOT / SAVE_PATH, save_mod['source_sha256'])
    owner_text = owner_raw.decode('ascii')
    owner_lines=owner_text.splitlines()
    assert owner_text.count('extern unsigned char far fd_50F6_0256[];')==1
    assert owner_text.count('extern unsigned char far fd_50F6_02C0[];')==1
    candidate_text=owner_text.replace('extern unsigned char far fd_50F6_0256[];',
                                      'unsigned char far fd_50F6_0256[100];',1)
    candidate_text=candidate_text.replace('extern unsigned char far fd_50F6_02C0[];',
                                          'unsigned char far fd_50F6_02C0[100];',1)
    if 'extern unsigned char far fd_50F6_0256[];' in candidate_text or 'extern unsigned char far fd_50F6_02C0[];' in candidate_text:
        raise RuntimeError('candidate replacement incomplete')
    whole_candidate=OUT/'m0BE8-water-owner.c'
    whole_candidate.write_text(candidate_text,encoding='ascii')

    save_lines=save_raw.decode('ascii').splitlines()
    save_re=re.compile(r'^\s*\{\s*(\d+)\s*,\s*(\d+)\s*,\s*\(void\s+far\s*\*\)\s*&([A-Za-z_][A-Za-z0-9_]*)\s*\},\s*$')
    def direct_save_row(name,line):
        text=save_lines[line-1].strip()
        m=save_re.fullmatch(text)
        if not m or (int(m.group(1)),int(m.group(2)),m.group(3))!=(1,100,name):
            raise RuntimeError(f'direct S09 SaveRec mismatch at {SAVE_PATH}:{line}: {text!r}')
        return {'source':SAVE_PATH,'line':line,'text':text,'element_size':1,'element_count':100,'bytes':100}

    source_anchors=[
     check(OWNER_PATH,39,'extern unsigned char far fd_50F6_0256[];'),
     check(OWNER_PATH,40,'extern unsigned char far fd_50F6_02C0[];'),
     check(OWNER_PATH,165,'void far DoWater(void)'),
     check(OWNER_PATH,180,'for (i = 0; i < 100; i++) {'),
     check(OWNER_PATH,181,'x = fd_50F6_0256[i];'),
     check(OWNER_PATH,182,'y = fd_50F6_02C0[i];'),
     check(OWNER_PATH,195,'for (i = 0; i < 100; i++) {'),
     check(OWNER_PATH,196,'x = fd_50F6_0256[i];'),
     check(OWNER_PATH,197,'y = fd_50F6_02C0[i];'),
     check(OWNER_PATH,210,'void far PlaceDrop(int i)'),
     check(OWNER_PATH,215,'x = RRand(128);'),
     check(OWNER_PATH,216,'y = RRand(64);'),
     check(OWNER_PATH,217,'fd_50F6_0256[i] = x;'),
     check(OWNER_PATH,218,'fd_50F6_02C0[i] = y;'),
     check(OWNER_PATH,237,'void far InitWater(void)'),
     check(OWNER_PATH,241,'for (i = 0; i < 100; ++i)'),
     check(OWNER_PATH,242,'PlaceDrop(i);'),
     check('src/S06/m35F5.c',193,'fd_50F6_0352 = 0;           /* RainOn */'),
     check('src/S06/m35F5.c',159,'void far o06_35F5_0000(void)'),
     check('src/S06/m35F5.c',219,'o06_35F5_020C();'),
     check('src/S06/m35F5.c',239,'if (fd_50F6_0352 == 0) {'),
     check('src/S06/m35F5.c',246,'fd_50F6_0352 = 1;'),
     check('src/S06/m35F5.c',248,'f_0BE8_063A();                      /* InitWater */'),
     check('src/S08/m35F5.c',386,'o06_35F5_0000();'),
     check('src/S08/m35F5.c',434,'RandYard();'),
     check('src/root/m0894.c',188,'o06_35F5_0173();'),
     check('src/root/m0894.c',189,'DoWater();'),
     check(SAVE_PATH,114,'for (p = fd_4E4B_0000; p->count != 0; p++)'),
     check(SAVE_PATH,89,'int far LoadGame(void)'),
     check(SAVE_PATH,98,'ok = 0;'),
     check(SAVE_PATH,116,'o09_35F5_0D7A();'),
     check(SAVE_PATH,118,'if ((r = read(fd, p->data, n = p->count * p->size)) != n) {'),
     check(SAVE_PATH,124,'ok = 1;'),
     check(SAVE_PATH,129,'if (ok) {'),
     check(SAVE_PATH,559,'RandYard();'),
     check(SAVE_PATH,966,'{ 1, 100, (void far *)&fd_50F6_0256 },'),
     check(SAVE_PATH,967,'{ 1, 100, (void far *)&fd_50F6_02C0 },'),
     check(SAVE_PATH,1132,'{ 2, 1, (void far *)&fd_50F6_0352 },'),
     check('src/S19/m384C.c',73,'if (LoadGame(0L) == 0 && fd_50F6_0EAC == -1 && NewGame(1) < 0)'),
    ]

    definitions={
     'fd_50F6_0256': {'offset':'0256','owner_line':39,'save_line':966},
     'fd_50F6_02C0': {'offset':'02C0','owner_line':40,'save_line':967},
    }
    for name,spec in definitions.items():
        row=SYMBOLS.get(name)
        if not row or row.get('seg')!=0x50F6 or row.get('off')!=int(spec['offset'],16):
            raise RuntimeError(f'registered symbol mismatch for {name}')
        assert 'extern unsigned char far '+name+'[];' in owner_lines[spec['owner_line']-1]
        spec['registered_base_aliases'] = sorted(
            n for n, e in SYMBOLS.items()
            if isinstance(e, dict) and e.get('seg') == 0x50F6 and e.get('off') == row['off'])
        spec['registered_interiors_in_source_count_window'] = sorted(
            [{'name': n, 'offset': f"{e['off']:04X}"}
             for n, e in SYMBOLS.items()
             if isinstance(e, dict) and e.get('seg') == 0x50F6 and
             row['off'] < e.get('off', -1) < row['off'] + 100],
            key=lambda item: item['offset'])
        if spec['registered_base_aliases'] != [name]:
            raise RuntimeError(f'unexpected exact-base registered aliases for {name}')
        spec['save_record']=direct_save_row(name,spec['save_line'])

    # Exhaustive lexical reference inventory over manifest-backed C modules only.
    module_source_hashes = {m['source']: m.get('source_sha256')
                            for m in MANIFEST['modules'].values()
                            if m.get('source') and m.get('lang') == 'c'}
    module_sources = sorted(module_source_hashes)
    source_scan_pins = {}
    reference_rows={name:[] for name in definitions}
    for source in module_sources:
        path=ROOT/source
        source_raw, source_scan_pins[source] = dos.pin(path, module_source_hashes[source])
        raw=source_raw.decode('utf-8',errors='replace').splitlines()
        code=c_visible(raw)
        for n,(rline,cline) in enumerate(zip(raw,code),1):
            for name in definitions:
                if re.search(r'(?<![A-Za-z0-9_])'+re.escape(name)+r'(?![A-Za-z0-9_])',cline):
                    before=cline[:cline.index(name)].rstrip() if name in cline else ''
                    pos=cline.index(name)
                    after=cline[pos+len(name):].lstrip()
                    if re.match(r'^\s*extern\b',cline): kind='declaration'
                    elif source==SAVE_PATH and n in (966,967): kind='SaveRec_address'
                    elif after.startswith('['): kind='indexed_behavior'
                    elif before.endswith('&'): kind='address_or_bitwise_context'
                    else: kind='bare_or_unknown'
                    reference_rows[name].append({'source':source,'line':n,'text':rline.strip(),'kind':kind})

    pointer_audit={}
    for name,rows in reference_rows.items():
        behavioral=[r for r in rows if r['kind'] not in ('declaration','SaveRec_address')]
        addresses=[r for r in rows if r['kind']=='address_or_bitwise_context']
        bare=[r for r in rows if r['kind']=='bare_or_unknown']
        indexed=[r for r in rows if r['kind']=='indexed_behavior']
        pointer_audit[name]={'behavioral_use_count':len(behavioral),'indexed_behavior_count':len(indexed),
                             'address_contexts_outside_SaveRec':[r for r in addresses if r['source']!=SAVE_PATH],
                             'bare_or_unknown_behavior':[r for r in bare if r['source']!=SAVE_PATH],
                             'all_references':rows}
    if any(x['address_contexts_outside_SaveRec'] or x['bare_or_unknown_behavior'] for x in pointer_audit.values()):
        raise RuntimeError('water arrays have unreviewed address or bare use; inspect output scan before continuing')

    # Compile a fresh canonical control and only the whole-module declaration candidate.
    flags = root_mod['flags']
    profile = compiler.verify_profile(root_mod['profile'])
    compiler_pins = [pin(Path(profile['directory']) / rel, digest)
                     for rel, digest in profile['files'].items()]
    compiler_pins.append(pin(Path(TC['runner']['path']), TC['runner']['sha256']))
    base_run = compiler.compile_c(owner_text, root_mod['profile'], flags,
                                  basename='M0BE8', keep=True)
    if not base_run.ok:
        raise RuntimeError('whole-module control compile failed: ' + base_run.log)
    candidate_run = compiler.compile_c(candidate_text, root_mod['profile'], flags,
                                       basename='M0BE8', keep=True)
    if not candidate_run.ok:
        raise RuntimeError('whole-module candidate compile failed: ' + candidate_run.log)
    (OUT / 'm0BE8-control.OBJ').write_bytes(base_run.obj)
    (OUT / 'm0BE8-water-owner.OBJ').write_bytes(candidate_run.obj)
    base_obj = OmfReader(communals=True).read(base_run.obj, 'M0BE8-control')
    cand_obj = OmfReader(communals=True).read(candidate_run.obj, 'M0BE8-water-owner')

    expected_names = {'_fd_50F6_0256', '_fd_50F6_02C0'}
    expected_communals = [
        {'name': '_fd_50F6_0256', 'kind': 'far', 'count': 100,
         'element_size': 1, 'length': 100},
        {'name': '_fd_50F6_02C0', 'kind': 'far', 'count': 100,
         'element_size': 1, 'length': 100},
    ]

    def debug_records(raw):
        # OMF LINNUM records are the only separate line/debug record family in this profile.
        return [{'kind': kind, 'body_sha256': sha(body), 'body_length': len(body)}
                for kind, body in OmfReader.records(raw) if kind in (0x94, 0x95)]

    control_scopes = list(zip(base_obj.externals, base_obj.external_scopes))
    candidate_scopes = list(zip(cand_obj.externals, cand_obj.external_scopes))
    expected_old_targets = {(name, 'external') for name in expected_names}
    expected_new_targets = {(name, 'communal') for name in expected_names}
    other_control_scopes = [row for row in control_scopes if row[0] not in expected_names]
    other_candidate_scopes = [row for row in candidate_scopes if row[0] not in expected_names]
    target_control_scopes = [row for row in control_scopes if row[0] in expected_names]
    target_candidate_scopes = [row for row in candidate_scopes if row[0] in expected_names]
    scopes_exact = (set(target_control_scopes) == expected_old_targets and
                    set(target_candidate_scopes) == expected_new_targets and
                    len(target_control_scopes) == len(target_candidate_scopes) == 2 and
                    other_control_scopes == other_candidate_scopes)
    candidate_communal_rows = [
        {key: row.get(key) for key in ('name', 'kind', 'count', 'element_size', 'length')}
        for row in cand_obj.communals]
    segment_payloads_equal = base_obj.segments == cand_obj.segments
    exact_object_checks = {
        'all_segment_payload_bytes_equal_including_debug_segments': segment_payloads_equal,
        'segment_lengths_equal': base_obj.segment_lengths == cand_obj.segment_lengths,
        'segment_definitions_equal': base_obj.segment_defs == cand_obj.segment_defs,
        'groups_equal': base_obj.groups == cand_obj.groups,
        'publics_equal': base_obj.publics == cand_obj.publics,
        'local_publics_equal': base_obj.local_publics == cand_obj.local_publics,
        'legacy_fixup_sequence_equal': base_obj.fixups == cand_obj.fixups,
        'full_ordered_linker_fixups_equal': base_obj.linker_fixups == cand_obj.linker_fixups,
        'comments_equal': base_obj.comments == cand_obj.comments,
        'local_externals_equal': base_obj.local_externals == cand_obj.local_externals,
        'external_name_sequence_equal': base_obj.externals == cand_obj.externals,
        'unrelated_external_scope_sequence_equal': other_control_scopes == other_candidate_scopes,
        'only_two_target_external_scopes_become_communal': scopes_exact,
        'debug_line_records_equal': debug_records(base_run.obj) == debug_records(candidate_run.obj),
        'exact_two_far_byte_communal_rows': candidate_communal_rows == expected_communals,
        'control_has_no_communal_rows': base_obj.communals == [],
    }
    def json_comments(obj):
        return [{key: value for key, value in row.items() if key != 'data'}
                for row in obj.comments]
    object_comparison = {
        'module': 'root:0BE8', 'profile': root_mod['profile'], 'flags': flags,
        'control_source_sha256': sha(owner_raw),
        'candidate_source_sha256': sha(candidate_text.encode('ascii')),
        'control_object_sha256': sha(base_run.obj),
        'candidate_object_sha256': sha(candidate_run.obj),
        'object_size_delta': len(candidate_run.obj) - len(base_run.obj),
        'control_segments': {k: {'length': len(v), 'sha256': sha(v)}
                             for k, v in base_obj.segments.items()},
        'candidate_segments': {k: {'length': len(v), 'sha256': sha(v)}
                               for k, v in cand_obj.segments.items()},
        'fixup_count_control': len(base_obj.linker_fixups),
        'fixup_count_candidate': len(cand_obj.linker_fixups),
        'ordered_linker_fixup_sha256': sha(json.dumps(
            [bindings.fixup_key(row) for row in base_obj.linker_fixups],
            separators=(',', ':')).encode('utf-8')),
        'control_debug_line_records': debug_records(base_run.obj),
        'candidate_debug_line_records': debug_records(candidate_run.obj),
        'control_comments': json_comments(base_obj),
        'candidate_comments': json_comments(cand_obj),
        'control_communal_records': base_obj.communals,
        'candidate_communal_records': cand_obj.communals,
        'checks': exact_object_checks,
        'passed': all(exact_object_checks.values()),
    }
    if not object_comparison['passed']:
        raise RuntimeError('whole-module object candidate changed more than the reviewed water commons: ' +
                           json.dumps(exact_object_checks, default=str))

    # Test-owned whole-module-independent C fixtures for actual MSC startup and byte/SaveRec views.
    OWNER_ZERO='''unsigned char far fd_50F6_0256[100];
    unsigned char far fd_50F6_02C0[100];
    int far water_owner_probe(void)
    {
        return fd_50F6_0256[0] + fd_50F6_0256[99] + fd_50F6_02C0[0] + fd_50F6_02C0[99];
    }
    '''
    OWNER_INITIALIZED='''unsigned char far fd_50F6_0256[100] = { 1 };
    unsigned char far fd_50F6_02C0[100] = { 1 };
    int far water_owner_probe(void)
    {
        return fd_50F6_0256[0] + fd_50F6_0256[99] + fd_50F6_02C0[0] + fd_50F6_02C0[99];
    }
    '''
    OWNER_SHORT='''unsigned char far fd_50F6_0256[99];
    unsigned char far fd_50F6_02C0[99];
    int far water_owner_probe(void) { return fd_50F6_0256[0] + fd_50F6_02C0[0]; }
    '''
    OWNER_NEAR='''unsigned char near fd_50F6_0256[100];
    unsigned char near fd_50F6_02C0[100];
    int water_owner_probe(void) { return fd_50F6_0256[0] + fd_50F6_02C0[0]; }
    '''
    CONSUMER='''extern unsigned char far fd_50F6_0256[];
    extern unsigned char far fd_50F6_02C0[];
    extern int far water_owner_probe(void);
    extern int far puts(char far *text);
    struct SaveRec { int size; int count; void far *data; };
    struct SaveRec saveViews[2] = {
        { 1, 100, (void far *)&fd_50F6_0256 },
        { 1, 100, (void far *)&fd_50F6_02C0 }
    };
    int main(void)
    {
        int i;
        unsigned char far *xbytes;
        unsigned char far *ybytes;
        xbytes = (unsigned char far *)saveViews[0].data;
        ybytes = (unsigned char far *)saveViews[1].data;
        if (saveViews[0].size != 1 || saveViews[0].count != 100 || xbytes != fd_50F6_0256 ||
            saveViews[1].size != 1 || saveViews[1].count != 100 || ybytes != fd_50F6_02C0) {
            puts("FAIL_PTR"); return 1;
        }
        for (i = 0; i < 100; i++)
            if (fd_50F6_0256[i] != 0 || fd_50F6_02C0[i] != 0 || xbytes[i] != 0 || ybytes[i] != 0) {
                puts("FAIL_ZERO"); return 1;
            }
        fd_50F6_0256[0] = 0x12; fd_50F6_0256[99] = 0xa5;
        fd_50F6_02C0[0] = 0x34; fd_50F6_02C0[99] = 0x5a;
        if (xbytes[0] != 0x12 || xbytes[99] != 0xa5 ||
            ybytes[0] != 0x34 || ybytes[99] != 0x5a) { puts("FAIL_VIEW"); return 1; }
        if (water_owner_probe() != 325) { puts("FAIL_OWNER"); return 1; }
        puts("PASS");
        return 0;
    }
    '''
    for name,text in [('owner-zero.c',OWNER_ZERO),('owner-initialized.c',OWNER_INITIALIZED),
                      ('owner-short.c',OWNER_SHORT),('owner-near.c',OWNER_NEAR),('consumer.c',CONSUMER)]:
        (OUT/name).write_text(text,encoding='ascii')

    test_flags=['/AL','/Os','/Zi']
    def compile_fixture(name,text):
        result=compiler.compile_c(text,'msc600ax',test_flags,basename=name,keep=True)
        if not result.ok: raise RuntimeError(f'{name} compile failed: {result.log}')
        (OUT/(name+'.OBJ')).write_bytes(result.obj)
        return result.obj

    zero_obj=compile_fixture('WZERO',OWNER_ZERO)
    init_obj=compile_fixture('WINIT',OWNER_INITIALIZED)
    short_obj=compile_fixture('WSHORT',OWNER_SHORT)
    near_obj=compile_fixture('WNEAR',OWNER_NEAR)
    consumer_obj=compile_fixture('WTEST',CONSUMER)
    reader=OmfReader(communals=True)
    zero_mod=reader.read(zero_obj,'WZERO')
    init_mod=reader.read(init_obj,'WINIT')
    short_mod=reader.read(short_obj,'WSHORT')
    near_mod=reader.read(near_obj,'WNEAR')

    def water_communals(obj):
        return sorted((c for c in obj.communals if c['name'].lstrip('_') in definitions),key=lambda c:c['name'])
    expected_far=[{'name':'_fd_50F6_0256','kind':'far','count':100,'element_size':1,'length':100},
                  {'name':'_fd_50F6_02C0','kind':'far','count':100,'element_size':1,'length':100}]
    # Match by normalized name because OMF stores public C symbols with a leading underscore.
    def normalized(rows):
        return sorted((c['name'].lstrip('_'),c['kind'],c.get('count'),c.get('element_size'),c['length']) for c in rows)
    zero_check=normalized(water_communals(zero_mod))==sorted((n,'far',100,1,100) for n in definitions)
    short_check=normalized(water_communals(short_mod))==sorted((n,'far',99,1,99) for n in definitions)
    near_check=normalized(water_communals(near_mod))==sorted((n,'near',None,None,100) for n in definitions)
    init_has_no_comm = not water_communals(init_mod)
    init_public_targets = sorted(p['name'] for p in init_mod.publics
                                 if p['name'] in expected_names)
    init_has_public_pair = init_public_targets == sorted(expected_names)
    if not zero_check or not short_check or not near_check or not init_has_no_comm or not init_has_public_pair:
        raise RuntimeError('fixture OMF COMM controls did not match expected far/near/extent/init shapes: '+json.dumps({
          'zero':water_communals(zero_mod),'initialized':water_communals(init_mod),
          'short':water_communals(short_mod),'near':water_communals(near_mod),
          'checks':[zero_check,short_check,near_check,init_has_no_comm,init_has_public_pair]},default=str))

    # Runtime cases use only test-owned objects, the pinned MSC C runtime, and pinned RTLink.
    manifest_pin=pin(ROOT/'layout/manifest.json')
    runtime_rows=list(MANIFEST['runtime']['libraries'].values())
    runtime_pins=[pin(Path(row['path']),row['sha256']) for row in runtime_rows]
    runner=TC['runners']['dosbox-x']
    runner_pin=pin(Path(runner['path']),runner['sha256'])
    run_cases=[]
    linker_inputs_by_version={}
    for linker_name in ('rtlink400','rtlink610'):
        linker=TC['linkers'][linker_name]
        linker_pins=[pin(Path(linker['directory'])/rel,digest)
                     for rel,digest in linker['files'].items()]
        linker_inputs_by_version[linker_name] = linker_pins
        tool_dir=compiler.pinned_tree(linker)
        cases=[('zero_far_communal',zero_obj),
               ('initialized_nonzero_control',init_obj),
               ('wrong_extent_99_byte_control',short_obj),
               ('wrong_near_communal_control',near_obj)]
        expected_by_case={
          'zero_far_communal':'PASS',
          'initialized_nonzero_control':'FAIL_ZERO',
          'wrong_extent_99_byte_control':('FAIL_VIEW' if linker_name=='rtlink400' else 'FAIL_OWNER'),
          'wrong_near_communal_control':'FAIL_OWNER',
        }
        for case,owner_bytes in cases:
            expected=expected_by_case[case]
            directory=OUT/linker_name/case
            directory.mkdir(parents=True,exist_ok=True)
            for name in ('PROBE.EXE','PROBE.MAP','RUN.LOG','LINK.LOG'):
                (directory/name).unlink(missing_ok=True)
            (directory/'WTEST.OBJ').write_bytes(consumer_obj)
            (directory/'OWNER.OBJ').write_bytes(owner_bytes)
            for row in runtime_rows:
                shutil.copyfile(row['path'],directory/Path(row['path']).name.upper())
            script=('OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n'
                    'LIBRARY LLIBCR, LIBH\r\nFILE WTEST\r\n'
                    'BEGINAREA\r\nSECTION FILE OWNER\r\nENDAREA\r\n')
            (directory/'PROBE.LNK').write_bytes(script.encode('ascii'))
            (directory/'RTLINK.CFG').write_bytes(b'SYNTAX = FREEFORMAT\r\n')
            (directory/'RUN.BAT').write_bytes((
              f'@echo off\r\nD:\\{linker["executable"]} @PROBE.LNK < NUL > LINK.LOG\r\n'
              'PROBE.EXE > RUN.LOG\r\n').encode('ascii'))
            conf=[]
            for section,settings in runner['conf'].items():
                conf += ['['+section+']']+[f'{k}={v}' for k,v in settings.items()]
            conf += ['[autoexec]',f'mount c "{directory}"',f'mount d "{tool_dir}" -ro','c:','call RUN.BAT','exit']
            conf_path=directory/'dosbox.conf'
            conf_path.write_text('\n'.join(conf)+'\n',encoding='ascii')
            env=os.environ.copy(); env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
            timed_out=False
            try:
                proc=subprocess.run([runner['path'],'-conf',str(conf_path),'-fastlaunch','-exit','-nomenu'],
                    cwd=directory,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                    timeout=90,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                exit_code=proc.returncode
            except subprocess.TimeoutExpired:
                timed_out=True; exit_code=-1
            actual=(directory/'RUN.LOG').read_text(encoding='latin1').strip() if (directory/'RUN.LOG').exists() else 'NO RUN.LOG'
            link_log=(directory/'LINK.LOG').read_text(encoding='latin1',errors='replace') if (directory/'LINK.LOG').exists() else ''
            files=[pin(p) for p in sorted(directory.iterdir()) if p.is_file()]
            case_result={'linker':linker_name,'case':case,'expected':expected,'actual':actual,
                         'dosbox_exit':exit_code,'timed_out':timed_out,
                         'passed':actual==expected and exit_code==0 and not timed_out,
                         'link_log_tail':link_log[-1000:],'files':files}
            run_cases.append(case_result)
            print(linker_name,case,actual,'pass='+str(case_result['passed']),flush=True)
            if not case_result['passed']:
                raise RuntimeError(f'runtime fixture failed: {linker_name}/{case}: {actual!r}\n{link_log[-1500:]}')

    # Directly record behavior sites and startup/load ordering; no whole-game image execution.
    anchors_by_name={name:[r for r in rows] for name,rows in reference_rows.items()}
    source_lifecycle={
     'new_world_and_sim_path':[
      {'fact':'RandYard initializes the yard state before the simulation can call DoWater.','anchors':[
        check('src/S08/m35F5.c',373,'void far RandYard(void)'),
        check('src/S08/m35F5.c',386,'o06_35F5_0000();'),
        check('src/S06/m35F5.c',159,'void far o06_35F5_0000(void)'),
        check('src/S06/m35F5.c',193,'fd_50F6_0352 = 0;           /* RainOn */'),
        check('src/S08/m35F5.c',434,'RandYard();'),
        check('src/S15/m384C.c',301,'RandYard();'),
      ]},
      {'fact':'DoAntSim calls DoSimYard before DoWater; DoSimYard invokes SimRain, and the false-to-true SimRain branch calls InitWater before returning.','anchors':[
        check('src/root/m0894.c',188,'o06_35F5_0173();'),
        check('src/root/m0894.c',189,'DoWater();'),
        check('src/S06/m35F5.c',206,'void far o06_35F5_0173(void)'),
        check('src/S06/m35F5.c',219,'o06_35F5_020C();'),
        check('src/S06/m35F5.c',239,'if (fd_50F6_0352 == 0) {'),
        check('src/S06/m35F5.c',246,'fd_50F6_0352 = 1;'),
        check('src/S06/m35F5.c',248,'f_0BE8_063A();                      /* InitWater */'),
      ]},
      {'fact':'InitWater loops 0..99 and calls PlaceDrop, which writes both arrays at the supplied i; DoWater has 0..99 read loops.','anchors':[
        check(OWNER_PATH,241,'for (i = 0; i < 100; ++i)'),
        check(OWNER_PATH,242,'PlaceDrop(i);'),
        check(OWNER_PATH,217,'fd_50F6_0256[i] = x;'),
        check(OWNER_PATH,218,'fd_50F6_02C0[i] = y;'),
        check(OWNER_PATH,180,'for (i = 0; i < 100; i++) {'),
        check(OWNER_PATH,195,'for (i = 0; i < 100; i++) {'),
      ]},
     ],
     'saved_game_path':[
      {'fact':'LoadGame prepares a fresh yard before reading records. Its table loop reads records in source order and aborts a failed read before ok/post-load reconstruction.','anchors':[
        check(SAVE_PATH,89,'int far LoadGame(void)'),
        check(SAVE_PATH,98,'ok = 0;'),
        check(SAVE_PATH,116,'o09_35F5_0D7A();'),
        check(SAVE_PATH,117,'for (p = fd_4E4B_0000; p->count != 0; p++) {'),
        check(SAVE_PATH,118,'if ((r = read(fd, p->data, n = p->count * p->size)) != n) {'),
        check(SAVE_PATH,121,'goto done;'),
        check(SAVE_PATH,120,'fd_50F6_0EAC = -1;'),
        check(SAVE_PATH,124,'ok = 1;'),
        check(SAVE_PATH,129,'if (ok) {'),
        check(SAVE_PATH,559,'RandYard();'),
      ]},
      {'fact':'The two full 100-byte coordinate rows precede the RainOn row in the canonical SaveRec table. On a failed load before those rows finish, RandYard left RainOn off; once RainOn can be restored, both coordinate rows have already succeeded.','anchors':[
        check(SAVE_PATH,966,'{ 1, 100, (void far *)&fd_50F6_0256 },'),
        check(SAVE_PATH,967,'{ 1, 100, (void far *)&fd_50F6_02C0 },'),
        check(SAVE_PATH,1132,'{ 2, 1, (void far *)&fd_50F6_0352 },'),
      ]},
      {'fact':'The caller may start a new game after failed loading; normal NewGame/RandYard reset reestablishes RainOn=0.','anchors':[
        check('src/S19/m384C.c',73,'if (LoadGame(0L) == 0 && fd_50F6_0EAC == -1 && NewGame(1) < 0)'),
        check('src/S15/m384C.c',301,'RandYard();'),
        check('src/S06/m35F5.c',193,'fd_50F6_0352 = 0;           /* RainOn */'),
      ]},
     ]
    }

    # Evidence and review-only candidate output. All generated files remain ignored scratch.
    input_rows = [pin(Path(__file__)), source_pin, save_pin, manifest_pin,
                  symbols_pin, toolchain_pin, *source_scan_pins.values(),
                  *compiler_pins, *runtime_pins, runner_pin,
                  pin(ROOT / 'tools/compiler.py'), pin(ROOT / 'tools/omf.py'),
                  pin(ROOT / 'tools/source_only_dos.py'),
                  pin(ROOT / 'tools/dos_source_bindings.py'),
                  pin(OUT / 'm0BE8-water-owner.c'),
                  pin(OUT / 'm0BE8-control.OBJ'), pin(OUT / 'm0BE8-water-owner.OBJ'),
                  pin(OUT / 'owner-zero.c'), pin(OUT / 'owner-initialized.c'),
                  pin(OUT / 'owner-short.c'), pin(OUT / 'owner-near.c'),
                  pin(OUT / 'consumer.c'), pin(OUT / 'WZERO.OBJ'),
                  pin(OUT / 'WINIT.OBJ'), pin(OUT / 'WSHORT.OBJ'),
                  pin(OUT / 'WNEAR.OBJ'), pin(OUT / 'WTEST.OBJ')]
    for linker_rows in linker_inputs_by_version.values():
        input_rows.extend(linker_rows)
    input_by_path = {row['path'].replace('/', '\\').lower(): row for row in input_rows}
    inputs = [input_by_path[key] for key in sorted(input_by_path)]
    case_receipt = [{key: row[key] for key in
                     ('linker', 'case', 'expected', 'actual', 'dosbox_exit', 'timed_out', 'passed')}
                    for row in run_cases]
    required_case_names = {'zero_far_communal', 'initialized_nonzero_control'}
    required_cases = {'zero_far_communal': 'PASS',
                      'initialized_nonzero_control': 'FAIL_ZERO'}
    required_runtime_cases = [row for row in case_receipt
                              if row['case'] in required_case_names]
    shape_runtime_cases = [row for row in case_receipt
                           if row['case'] not in required_case_names]

    report = {
        'schema': 'simant-dos-water-coordinate-owner-proof-v2',
        'status': 'SCRATCH_ONLY_FUNCTIONAL_OWNER_CANDIDATE_NOT_ADMITTED',
        'run_directory': OUT.relative_to(ROOT).as_posix(),
        'owner_candidate': {
            'module': 'root:0BE8',
            'whole_module_candidate': (OUT / 'm0BE8-water-owner.c').relative_to(ROOT).as_posix(),
            'source_sha256': root_mod['source_sha256'],
            'declaration_edits': [
                {'line': 39, 'before': 'extern unsigned char far fd_50F6_0256[];',
                 'after': 'unsigned char far fd_50F6_0256[100];'},
                {'line': 40, 'before': 'extern unsigned char far fd_50F6_02C0[];',
                 'after': 'unsigned char far fd_50F6_02C0[100];'},
            ],
            'source_extent_bytes': 100,
            'serialized_bytes': 200,
            'historical_communal_producer_or_order_claimed': False,
        },
        'source_evidence': {
            'anchors': source_anchors,
            'lifecycle': source_lifecycle,
            'registered_and_behavioral_reference_audit': pointer_audit,
            'registered': definitions,
            'manifest_c_source_scan_count': len(source_scan_pins),
            'interpretation': ('Both objects are indexed only in DoWater/PlaceDrop; persistent address views '
                               'are the two SaveRec records. The lexical audit found no other base-address '
                               'escape or unclassified behavioral use, and no registered aliases except each '
                               'symbol itself or registered interior within the proposed extents.'),
        },
        'whole_module_object_control': object_comparison,
        'fixture_objects': {
            'flags': test_flags,
            'zero_far_owner': {
                'object_sha256': sha(zero_obj),
                'communal_records': water_communals(zero_mod),
                'exact_far_byte_pair_of_100_each': zero_check,
            },
            'initialized_nonzero_control': {
                'object_sha256': sha(init_obj),
                'communal_records': water_communals(init_mod),
                'registered_publics': init_public_targets,
                'has_no_far_commons': init_has_no_comm,
                'has_initialized_public_pair': init_has_public_pair,
            },
            'wrong_extent_99_byte_control': {
                'object_sha256': sha(short_obj),
                'communal_records': water_communals(short_mod),
                'expected_100_actual_99_shape_detected': short_check,
            },
            'wrong_near_communal_control': {
                'object_sha256': sha(near_obj),
                'communal_records': water_communals(near_mod),
                'expected_far_actual_near_shape_detected': near_check,
            },
            'consumer_object_sha256': sha(consumer_obj),
        },
        'toolchain': {
            'msc_profile': root_mod['profile'],
            'whole_module_flags': flags,
            'fixture_flags': test_flags,
            'runtime_libraries': runtime_pins,
            'dosbox_x_runner': runner_pin,
            'rtlink_files': linker_inputs_by_version,
            'msc_compiler_files': compiler_pins,
        },
        'runtime': {
            'actual_msc_crt_startup': True,
            'linkers': ['rtlink400', 'rtlink610'],
            'required_cases': required_cases,
            'cases': required_runtime_cases,
            'shape_controls': {
                'wrong_extent_99_byte_far': {
                    'omf_shape_rejected': short_check,
                    'runtime_observations': [row for row in shape_runtime_cases
                                             if row['case'] == 'wrong_extent_99_byte_control'],
                },
                'wrong_near_100_byte': {
                    'omf_shape_rejected': near_check,
                    'runtime_observations': [row for row in shape_runtime_cases
                                             if row['case'] == 'wrong_near_communal_control'],
                },
                'initialized_nonzero_public': {
                    'omf_shape_rejected': init_has_public_pair and init_has_no_comm,
                    'runtime_observations': [row for row in required_runtime_cases
                                             if row['case'] == 'initialized_nonzero_control'],
                },
            },
            'all_cases_for_review': run_cases,
            'consumer_contract': ('Check every element for zero, direct far unsigned-byte references and both '
                                  'SaveRec {1,100} byte views, then write/read indices 0 and 99 and call an '
                                  'owner-side far function over those exact bytes.'),
        },
        'inputs': inputs,
        'denied_original_oracle_reads': denied_oracle_reads,
        'limits': [
            'This is a source-level functional owner candidate only; no source admission or historical communal producer/order/padding claim is made.',
            'No original executable, hybrid image, native provider/state, or whole-game runtime was used.',
            'The full object comparison is between two fresh pinned-MSC builds from canonical source text and exact declaration edits.',
        ],
        'all_probe_gates_pass': (object_comparison['passed'] and zero_check and short_check and
                                 near_check and init_has_no_comm and init_has_public_pair and
                                 all(row['passed'] for row in run_cases) and not denied_oracle_reads),
    }
    report_path = OUT / 'water-storage-report.json'
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    report_pin = pin(report_path)

    candidate_receipt = {
        'schema': 'simant-dos-farbss-owner-candidate-v1',
        'status': 'CANDIDATE_FOR_REVIEW_NOT_ADMITTED',
        'candidate': report['owner_candidate'],
        'source_extent_evidence': {
            'constructor': 'src/root/m0BE8.c:241-242 loops i=0..99 and calls PlaceDrop(i)',
            'writes': ['src/root/m0BE8.c:217', 'src/root/m0BE8.c:218'],
            'consumers': ['src/root/m0BE8.c:180-182', 'src/root/m0BE8.c:195-197'],
            'save_records': ['src/S09/m35F5.c:966', 'src/S09/m35F5.c:967'],
            'persistent_views': True,
            'other_address_escapes_or_registered_interiors': False,
            'read_before_write_lifecycle': 'Reset-before-load/new-game plus RainOn gate closes the source-bound startup path; anchors are in the detailed report.',
        },
        'whole_module_object': {
            'all_checks_pass': object_comparison['passed'],
            'checks': object_comparison['checks'],
            'ordered_fixup_count': object_comparison['fixup_count_control'],
            'ordered_fixup_sha256': object_comparison['ordered_linker_fixup_sha256'],
            'communal_records': object_comparison['candidate_communal_records'],
            'object_size_delta': object_comparison['object_size_delta'],
        },
        'water_storage_contract': {
            'required_cases': required_cases,
            'cases': required_runtime_cases,
            'shape_controls': {
                'wrong_extent_99_byte_far': {
                    'omf_shape_rejected': short_check,
                    'runtime_observations': [row for row in shape_runtime_cases
                                             if row['case'] == 'wrong_extent_99_byte_control'],
                },
                'wrong_near_100_byte': {
                    'omf_shape_rejected': near_check,
                    'runtime_observations': [row for row in shape_runtime_cases
                                             if row['case'] == 'wrong_near_communal_control'],
                },
                'initialized_nonzero_public': {
                    'omf_shape_rejected': init_has_public_pair and init_has_no_comm,
                    'runtime_observations': [row for row in required_runtime_cases
                                             if row['case'] == 'initialized_nonzero_control'],
                },
            },
        },
        'full_probe_runtime_observations': case_receipt,
        'toolchain': {
            'compiler_profile': root_mod['profile'],
            'whole_module_flags': flags,
            'test_consumer_flags': test_flags,
            'msc_file_pin_count': len(compiler_pins),
            'crt_files': runtime_pins,
            'runner': runner_pin,
            'linkers': {name: rows for name, rows in linker_inputs_by_version.items()},
        },
        'input_report': {'path': report_path.relative_to(ROOT).as_posix(),
                         'sha256': report_pin['sha256']},
        'source_scan_manifest_modules': len(source_scan_pins),
        'denied_original_oracle_reads': denied_oracle_reads,
        'historical_communal_producer_order_or_padding_claimed': False,
        'all_checks_pass': report['all_probe_gates_pass'],
    }
    receipt_path = OUT / 'water-storage-owner-candidate.json'
    receipt_path.write_text(json.dumps(candidate_receipt, indent=2, ensure_ascii=False) + '\n',
                            encoding='utf-8')

    runtime_rows_by_linker = {
        name: [row for row in run_cases if row['linker'] == name]
        for name in ('rtlink400', 'rtlink610')
    }
    markdown = [
        '# Water-pair source-only ownership candidate', '',
        'Review-only functional owner hypothesis. The script writes no production storage; this receipt makes no historical communal producer/order/padding claim.', '',
        'Candidate whole-module declaration edits:', '',
        '```c',
        'unsigned char far fd_50F6_0256[100];',
        'unsigned char far fd_50F6_02C0[100];',
        '```', '',
        'The constructor and both consumers cover indices 0 through 99. The direct S09 SaveRec rows each serialize 100 bytes. The complete registered-source audit found no other behavioral pointer escapes and no registered interior symbols. New-world and saved-game source ordering resets RainOn before water can be read; the table restores RainOn only after both water rows have been loaded.', '',
        f"Whole-module fresh-build comparison passed: `{object_comparison['passed']}`. All segment bytes (including any debug segments), segment declarations, groups, publics, local publics, comments, legacy fixups and full ordered linker fixups match; the only external-scope change is the two requested symbol rows becoming commons. Ordered fixups: {object_comparison['fixup_count_control']}, SHA-256 `{object_comparison['ordered_linker_fixup_sha256']}`. Exact new commons: `{json.dumps(object_comparison['candidate_communal_records'], separators=(',', ':'))}`.", '',
        'Both linkers ran all four source-built controls under pinned MSC C runtime startup:', '',
        '| Linker | Zero far [100] owner | Nonzero initialized | Wrong far [99] extent | Wrong near [100] type |',
        '| --- | --- | --- | --- | --- |',
    ]
    case_names = ['zero_far_communal', 'initialized_nonzero_control',
                  'wrong_extent_99_byte_control', 'wrong_near_communal_control']
    for linker_name, rows in runtime_rows_by_linker.items():
        by_name = {row['case']: row for row in rows}
        cells = [f"{by_name[name]['actual']} (expected {by_name[name]['expected']})" for name in case_names]
        markdown.append('| ' + linker_name + ' | ' + ' | '.join(cells) + ' |')
    markdown += [
        '',
        'The positive owner verifies all 200 initial bytes, SaveRec byte pointers, and writes/reads both endpoints. Wrong extent and near controls fail the consumer at the expected boundary/owner checks; initialized data fails the zero-startup check. OMF control records independently verify the wrong 99-byte far and 100-byte near shapes.', '',
        f"Run result: **{report['all_probe_gates_pass']}**. Original/oracle reads denied: `{len(denied_oracle_reads)}`. Detailed evidence: `{report_path.relative_to(ROOT).as_posix()}`. Compact candidate receipt: `{receipt_path.relative_to(ROOT).as_posix()}`. All outputs are under this ignored scratch run directory: `{OUT.relative_to(ROOT).as_posix()}`.", '',
        'This is not an admission. Review/admission remains a separate parent-owned step.', '',
    ]
    markdown_path = OUT / 'water-storage-report.md'
    markdown_path.write_text('\n'.join(markdown), encoding='utf-8')
    print(json.dumps({
        'all_checks_pass': report['all_probe_gates_pass'],
        'module_object_checks': object_comparison['checks'],
        'runtime_cases': [(row['linker'], row['case'], row['actual'], row['passed'])
                          for row in run_cases],
        'denied_original_oracle_reads': denied_oracle_reads,
        'report': report_path.relative_to(ROOT).as_posix(),
        'candidate_receipt': receipt_path.relative_to(ROOT).as_posix(),
        'markdown': markdown_path.relative_to(ROOT).as_posix(),
    }, indent=2))
    return 0 if report['all_probe_gates_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
