"""Source-only data-provider and MSC/RTLink runtime probe for mono-pattern prefix."""
from __future__ import annotations
import hashlib, json, os, shutil, subprocess, sys
from pathlib import Path

def find_root():
    for p in Path(__file__).resolve().parents:
        if (p/'layout'/'manifest.json').is_file(): return p
    raise RuntimeError('cannot locate repo root')
ROOT=find_root()
OUT=ROOT/'build/workers/dos_mono_pattern_prefix'
sys.path.insert(0,str(ROOT/'tools'))
import compiler, source_only_dos as dos
from omf import OmfReader

PROVIDER=ROOT/'work/source-only-dos/providers/mono-pattern-prefix.c'
PROVIDER_TEXT='unsigned char near g_8EC0[24];\n'
PROVIDER_FLAGS=['/AL','/Os','/Gs']
OWNER_NEG=r'''unsigned char near g_8EC0[24] = { 1 };
'''
CHECK=r'''extern unsigned char near g_8EC0[24];
int far g8ec0_checker(int filled)
{
    unsigned int i;
    unsigned char want;
    for (i=0; i<24; i++) {
        want = filled ? (unsigned char)(i*13+5) : 0;
        if (g_8EC0[i] != want)
            return (int)i+1;
    }
    return 0;
}
'''
MAIN=r'''extern unsigned char near g_8EC0[24];
extern int far g8ec0_checker(int filled);
extern int far puts(char far *text);
int main(void)
{
    unsigned int i;
    if (g8ec0_checker(0) != 0) {
        puts("FAIL");
        return 1;
    }
    for (i=0; i<24; i++)
        g_8EC0[i] = (unsigned char)(i*13+5);
    if (g8ec0_checker(1) != 0) {
        puts("FAIL");
        return 1;
    }
    puts("PASS");
    return 0;
}
'''

def sha(raw): return hashlib.sha256(raw).hexdigest()
def pin(path,expected=None):
    raw=Path(path).read_bytes(); digest=sha(raw)
    if expected and digest!=expected: raise RuntimeError('stale input pin: '+str(path))
    if digest==dos.ORIGINAL_SHA: raise RuntimeError('oracle executable cannot be a build input')
    try: shown=str(Path(path).resolve().relative_to(ROOT)).replace('\\','/')
    except ValueError: shown=str(Path(path).resolve()).replace('\\','/')
    return {'path':shown,'sha256':digest,'size':len(raw)}
def uniq_pins(rows):
    out={}
    for r in rows: out[(r['path'],r['sha256'])]=r
    return [out[k] for k in sorted(out)]
def compile_text(basename,text,flags):
    r=compiler.compile_c(text,'msc600ax',flags,basename=basename)
    if not r.ok: raise RuntimeError(basename+' compile failed:\n'+r.log)
    return r.obj

def live_defs(obj):
    return [d for d in obj.segment_defs if str(d.get('class','')).upper() not in ('DEBSYM','DEBTYP')]
def pub_rows(obj):
    return sorted((p['name'],p['segment'],p['offset']) for p in obj.publics)
def extern_rows(obj,omit='_g_8EC0'):
    return [(n,s) for n,s in zip(obj.externals,obj.external_scopes) if n!=omit]

def canonical_source_audit():
    syms=json.loads((ROOT/'layout/symbols.json').read_text(encoding='utf-8'))['data']
    interiors=[{'name':n,'seg':r.get('seg'),'off':r.get('off'),'alias_of':r.get('alias_of')}
        for n,r in syms.items() if r.get('seg')==0x55b3 and 0x8ec0<=r.get('off',-1)<0x8ed8]
    source_hits=[]
    for suffix in ('.c','.asm'):
        for p in (ROOT/'src').rglob('*'+suffix):
            text=p.read_text(encoding='latin1')
            for line_no,line in enumerate(text.splitlines(),1):
                if 'g_8EC0' in line or '8EC0h' in line.upper():
                    source_hits.append({'path':p.relative_to(ROOT).as_posix(),'line':line_no,'text':line.strip()})
    s15_path=ROOT/'src/S15/m384C.c'; s15=s15_path.read_text(encoding='ascii')
    start=s15.index('void far LoadMonoPats(void)')
    end=s15.index('void far o15_384C_0125(void)',start)
    loader=s15[start:end]
    required_loader_fragments=(
      'db_LoadObject(0x2710, 0x16)','n = 0x18;','dst = g_8EC0;',
      'for (i = 0; i < n; i++)','*dst++ = ~*src++;','db_PurgeObject(0x2710, 0x16);',
      'db_LoadObject(0x271a, 0x16)','n = (*h)[1] << 3;','dst = g_8ED8;',
      'db_PurgeObject(0x271a, 0x16);')
    s01_path=ROOT/'src/S01/m328E.asm'; s01=s01_path.read_text(encoding='latin1')
    indexed_base=[line.strip() for line in s01.splitlines() if 'ADD BX, 8ED8H' in line.upper()]
    indexed_reads=[line.strip() for line in s01.splitlines() if 'ss:[bx' in line.lower()]
    expected_interiors=[{'name':'g_8EC0','seg':0x55b3,'off':0x8ec0,'alias_of':None}]
    result={'candidate_region':'DGROUP 55B3:8EC0-8ED7','registry_region_rows':interiors,
      'canonical_g8EC0_identifier_or_literal_hits':source_hits,'S15_LoadMonoPats_source_fragments_present':all(x in loader for x in required_loader_fragments),
      'S01_indexed_base_count':len(indexed_base),'S01_indexed_byte_read_lines':len(indexed_reads),
      'S01_indexed_base_lines':indexed_base,
      'only_registered_base_view_in_candidate_region':interiors==expected_interiors,
      'only_canonical_identifier_view_is_S15':len(source_hits)==2 and all(x['path']=='src/S15/m384C.c' for x in source_hits),
      'input_pins':[pin(ROOT/'layout/symbols.json'),pin(s15_path),pin(s01_path)]}
    if not all((result['S15_LoadMonoPats_source_fragments_present'],
        result['S01_indexed_base_count']==4,result['S01_indexed_byte_read_lines']>0,
        result['only_registered_base_view_in_candidate_region'],result['only_canonical_identifier_view_is_S15'])):
        raise RuntimeError('canonical source ownership scan found an unexpected view or changed anchor')
    return result

def run_case(profile,case,owner_obj,main_obj,check_obj,expected,runtimes,linker,runner,tool_dir):
    d=OUT/profile/case; d.mkdir(parents=True,exist_ok=True)
    for name in ('PROBE.EXE','PROBE.MAP','RUN.LOG','LINK.LOG'): (d/name).unlink(missing_ok=True)
    (d/'MAIN.OBJ').write_bytes(main_obj); (d/'OWNER.OBJ').write_bytes(owner_obj); (d/'CHECK.OBJ').write_bytes(check_obj)
    for row in runtimes: shutil.copyfile(row['path'],d/Path(row['path']).name.upper())
    script=('OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\nLIBRARY LLIBCR, LIBH\r\n'
      'FILE MAIN\r\nFILE OWNER\r\nBEGINAREA\r\nSECTION FILE CHECK\r\nENDAREA\r\n')
    (d/'PROBE.LNK').write_bytes(script.encode('ascii')); (d/'RTLINK.CFG').write_bytes(b'SYNTAX = FREEFORMAT\r\n')
    (d/'RUN.BAT').write_bytes((f'@echo off\r\nD:\\{linker["executable"]} @PROBE.LNK < NUL > LINK.LOG\r\nPROBE.EXE > RUN.LOG\r\n').encode('ascii'))
    conf=[]
    for section,settings in runner['conf'].items(): conf.append('['+section+']'); conf += [f'{k}={v}' for k,v in settings.items()]
    conf += ['[autoexec]',f'mount c "{d}"',f'mount d "{tool_dir}" -ro','c:','call RUN.BAT','exit']
    conf_path=d/'dosbox.conf'; conf_path.write_text('\n'.join(conf)+'\n')
    env=os.environ.copy(); env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
    timed=False
    try: result=subprocess.run([runner['path'],'-conf',str(conf_path),'-fastlaunch','-exit','-nomenu'],cwd=d,env=env,
      stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=60,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    except subprocess.TimeoutExpired: timed=True; result=type('Timeout',(),{'returncode':-1})()
    actual=(d/'RUN.LOG').read_text(encoding='latin1').strip() if (d/'RUN.LOG').exists() else 'NO RUN.LOG'
    linklog=(d/'LINK.LOG').read_text(encoding='latin1',errors='replace') if (d/'LINK.LOG').exists() else ''
    print(profile,case,actual,flush=True)
    return {'linker':profile,'case':case,'expected':expected,'actual':actual,'emulator_exit':result.returncode,
      'timed_out':timed,'passed':actual==expected and result.returncode==0 and not timed,'link_log_tail':linklog[-1200:],
      'files':[pin(p) for p in sorted(d.iterdir()) if p.is_file()]}

def main():
    denied=dos.install_input_guard()
    OUT.mkdir(parents=True,exist_ok=True)
    if PROVIDER.read_text(encoding='ascii')!=PROVIDER_TEXT: raise RuntimeError('tracked provider must be the exact one-line declaration')
    audit=canonical_source_audit()
    tc=compiler.toolchain(); manifest_raw=dos.pin(ROOT/'layout/manifest.json')[0]; manifest=json.loads(manifest_raw)
    runtimes=list(manifest['runtime']['libraries'].values())
    provider_obj=compile_text('MPOWNER',PROVIDER_TEXT,PROVIDER_FLAGS)
    bad_obj=compile_text('BADOWN',OWNER_NEG,PROVIDER_FLAGS)
    main_obj=compile_text('MAIN',MAIN,['/AL','/Os','/Gs'])
    check_obj=compile_text('CHECK',CHECK,['/AL','/Os','/Gs'])
    reader=OmfReader(communals=True); provider=reader.read(provider_obj,'MPOWNER'); negative=reader.read(bad_obj,'BADOWN')
    good_comm=[{'name':'_g_8EC0','kind':'near','type_index':0,'length':24}]
    if provider.communals!=good_comm or provider.publics or provider.local_publics or provider.fixups or provider.linker_fixups or provider.segments:
        raise RuntimeError('production provider must be exactly one near24 COMM with no code/data/debug/public/fixup bytes')
    if provider.externals!=['_g_8EC0'] or provider.external_scopes!=['communal']:
        raise RuntimeError('provider must have no declarations beyond its one near COMM')
    if negative.communals or not any(p['name']=='_g_8EC0' for p in negative.publics):
        raise RuntimeError('initialized negative owner must be an initialized public rather than a COMM')
    msc=compiler.verify_profile('msc600ax')
    build_pins=[pin(PROVIDER),pin(ROOT/'work/source-only-dos/mono-pattern-prefix-probe.py'),pin(ROOT/'layout/manifest.json'),pin(ROOT/'layout/toolchain.json')]
    for rel,digest in msc['files'].items(): build_pins.append(pin(Path(msc['directory'])/rel,digest))
    build_pins.append(pin(Path(tc['runner']['path']),tc['runner']['sha256']))
    runner=tc['runners']['dosbox-x']; build_pins.append(pin(Path(runner['path']),runner['sha256']))
    for profile in ('rtlink400','rtlink610'):
        linker=tc['linkers'][profile]
        for rel,digest in linker['files'].items(): build_pins.append(pin(Path(linker['directory'])/rel,digest))
        tool_dir=compiler.pinned_tree(linker)
        for row in runtimes: build_pins.append(pin(Path(row['path']),row['sha256']))
    cases=[]
    for profile in ('rtlink400','rtlink610'):
        linker=tc['linkers'][profile]; tool_dir=compiler.pinned_tree(linker)
        cases.append(run_case(profile,'typed24_zero_fill_and_byte_roundtrip',provider_obj,main_obj,check_obj,'PASS',runtimes,linker,runner,tool_dir))
        cases.append(run_case(profile,'initialized_nonzero_owner_negative',bad_obj,main_obj,check_obj,'FAIL',runtimes,linker,runner,tool_dir))
    report={'schema':'simant-source-only-near-data-provider-probe-v1','module':'source-owned:mono-pattern-prefix',
      'provider_source':pin(PROVIDER),'provider_basename':'MPOWNER','provider_flags':PROVIDER_FLAGS,
      'provider_object_sha256':sha(provider_obj),'provider_object_bytes':len(provider_obj),
      'provider_omf':{'communals':provider.communals,'publics':provider.publics,'local_publics':provider.local_publics,
        'externals':list(zip(provider.externals,provider.external_scopes)),'fixup_count':len(provider.linker_fixups),
        'nonempty_segment_payloads':{k:len(v) for k,v in provider.segments.items()},
        'nonzero_segment_lengths':{k:v for k,v in provider.segment_lengths.items() if v}},
      'canonical_source_ownership_audit':audit,'denied_oracle_reads':denied,
      'cases':cases,'build_inputs':uniq_pins(build_pins),
      'build_scope':'Only tracked provider, test main/checker, pinned MSC 6.00AX compiler/runtime and RTLink 4.00/6.10. No original executable or assets are read, compiled, linked, or executed.',
      'all_expected_outcomes_pass':len(cases)==4 and all(x['passed'] for x in cases) and not denied}
    out=OUT/'mono-pattern-prefix-report.json'; out.write_text(json.dumps(report,indent=2)+'\n')
    print('all_expected_outcomes_pass',report['all_expected_outcomes_pass'])
    return 0 if report['all_expected_outcomes_pass'] else 1
if __name__=='__main__': raise SystemExit(main())
