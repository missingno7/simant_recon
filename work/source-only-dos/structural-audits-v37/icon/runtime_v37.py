"""Natural test-owned Handle views under pinned CRT and both RTLinks.

No original executable/resource payload enters these controls. Null is checked
only as a value; every executed dereference follows assignment of valid test-owned
pointer cells and byte arrays. These fixtures are not proposed game setup code.
"""
from __future__ import annotations
import hashlib,json,os,re,shutil,struct,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]; OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
import compiler
from omf import OmfReader
compiler.WORK=OUT/'cc'
def sha(b): return hashlib.sha256(b).hexdigest()
def pin(p):
    b=p.read_bytes(); return {'path':str(p.resolve()).replace('\\','/'),'size':len(b),'sha256':sha(b)}

MAIN=r'''
typedef char far * far *Handle;
extern Handle far fd_50F6_46D2;
extern int far puts(char far *);
char far fixturePixelsA[128] = { 11, 22, 33 };
char far fixturePixelsB[128] = { 44, 55, 66 };
char far * far fixtureMaster = fixturePixelsA;
char far * far fixtureMaster2 = fixturePixelsB;
char far * far derive(int n)
{
    return *fd_50F6_46D2 + (n << 5);
}
int main(void)
{
    unsigned char far *bytes;
    unsigned far *words;
    int i;
    unsigned long cell;
    bytes=(unsigned char far *)&fd_50F6_46D2;
    if(sizeof(fd_50F6_46D2)!=4 || sizeof(Handle)!=4 || sizeof(char far *)!=4) {
        puts("FAIL_HANDLE_WIDTH"); return 1;
    }
    for(i=0;i<4;i++) if(bytes[i]) { puts("FAIL_INITIAL_ZERO"); return 2; }
    if(fd_50F6_46D2!=0) { puts("FAIL_NULL_REPRESENTATION"); return 3; }
    puts("PASS_INITIAL_ZERO_4BYTE_VIEW");
    fd_50F6_46D2=&fixtureMaster;
    if((Handle)fd_50F6_46D2!=&fixtureMaster) { puts("FAIL_TYPED_STORE"); return 4; }
    if(derive(1)!=fixturePixelsA+32 || derive(2)!=fixturePixelsA+64) {
        puts("FAIL_POINTER_CHAIN_OR_BYTE_STRIDE"); return 5;
    }
    fixtureMaster=fixturePixelsB;
    if(derive(1)!=fixturePixelsB+32) { puts("FAIL_CELL_REPOINT"); return 6; }
    puts("PASS_HANDLE_CELL_REPOINT_BYTE_STRIDE");
    words=(unsigned far *)&fd_50F6_46D2;
    cell=(unsigned long)&fixtureMaster2;
    if(words[0]!=(unsigned)(unsigned long)&fixtureMaster ||
       words[1]!=(unsigned)((unsigned long)&fixtureMaster>>16)) {
        puts("FAIL_RAW_OFFSET_SEGMENT_ORDER"); return 7;
    }
    words[0]=(unsigned)cell; words[1]=(unsigned)(cell>>16);
    if((Handle)fd_50F6_46D2!=&fixtureMaster2 || derive(3)!=fixturePixelsB+96) {
        puts("FAIL_RAW_WORD_ROUNDTRIP"); return 8;
    }
    fixtureMaster2=fixturePixelsA;
    if(derive(3)!=fixturePixelsA+96) { puts("FAIL_SECOND_CELL_REPOINT"); return 9; }
    for(i=0;i<4;i++) bytes[i]=0;
    if(fd_50F6_46D2!=0) { puts("FAIL_RAW_ZERO_RESET"); return 10; }
    puts("PASS_TYPED_RAW_WRITE_ZERO_RESET");
    return 0;
}
'''

def compile_one(label,text):
    d=OUT/'runtime-sources'; d.mkdir(exist_ok=True); p=d/(label+'.c'); p.write_text(text,encoding='ascii')
    r=compiler.compile_c(text,'msc600ax',['/AL','/Os','/Gs'],basename=label)
    (d/(label+'.compiler.log')).write_text(r.log,encoding='utf-8')
    if not r.ok: raise RuntimeError(r.log)
    op=d/(label+'.obj'); op.write_bytes(r.obj); o=OmfReader(communals=True).read(r.obj)
    return r.obj,{'label':label,'source':pin(p),'object':pin(op),'communals':o.communals,
        'segment_defs':o.segment_defs,'segment_lengths':o.segment_lengths,'publics':o.publics,
        'ordered_fixups':o.linker_fixups,'segment_sha256':{n:sha(bytes(b)) for n,b in o.segments.items()}}

def run_case(profile,label,main,owner,shift=None,overlay=False):
    tc=compiler.toolchain(); prof=tc['linkers'][profile]; runner=tc['runners']['dosbox-x']; tree=compiler.pinned_tree(prof)
    d=OUT/'runtime'/profile/label; d.mkdir(parents=True,exist_ok=True)
    (d/'MAIN.OBJ').write_bytes(main); (d/'OWNER.OBJ').write_bytes(owner)
    if shift: (d/'SHIFT.OBJ').write_bytes(shift)
    libs=json.loads((ROOT/'layout/manifest.json').read_text())['runtime']['libraries']; pins=[]
    for n in ('llibcr.lib','libh.lib'):
        p=Path(libs[n]['path'])
        if sha(p.read_bytes())!=libs[n]['sha256']: raise ValueError('library drift')
        shutil.copyfile(p,d/n.upper()); pins.append(pin(p))
    lnk='OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\nLIBRARY LLIBCR, LIBH\r\n'
    if shift: lnk+='FILE SHIFT\r\n'
    lnk+='FILE MAIN\r\n'
    lnk+=('BEGINAREA\r\nSECTION FILE OWNER\r\nENDAREA\r\n' if overlay else 'FILE OWNER\r\n')
    (d/'PROBE.LNK').write_bytes(lnk.encode('ascii'))
    (d/'RTLINK.CFG').write_bytes(b'SYNTAX = FREEFORMAT\r\n')
    (d/'RUN.BAT').write_bytes(('@echo off\r\nD:\\'+prof['executable']+' @PROBE.LNK < NUL > LINK.LOG\r\nPROBE.EXE > RUN.LOG\r\n').encode('ascii'))
    lines=[]
    for sec,settings in runner['conf'].items():
        lines.append('['+sec+']'); lines += [str(k)+'='+str(v) for k,v in settings.items()]
    lines+=['[autoexec]','mount c "'+str(d)+'"','mount d "'+str(tree)+'" -ro','c:','call RUN.BAT','exit']
    conf=d/'dosbox.conf'; conf.write_text('\n'.join(lines)+'\n',encoding='ascii')
    env=os.environ.copy(); env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
    r=subprocess.run([runner['path'],'-conf',str(conf),'-fastlaunch','-exit','-nomenu'],cwd=d,env=env,
        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=45,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    log=(d/'LINK.LOG').read_text(encoding='latin1'); run=(d/'RUN.LOG').read_text(encoding='latin1'); mp=(d/'PROBE.MAP').read_text(encoding='latin1')
    diagnostics=[l for l in log.splitlines() if re.search(r'(?i)warning|error|wrt\d|undefined|unresolved|duplicate',l)]
    pairs=re.findall(r'(?im)^\s*([0-9a-f]{4}):([0-9a-f]{4})\s+(?:Res\s+)?_fd_50F6_46D2\b',mp)
    locations=sorted(set((int(s,16),int(o,16)) for s,o in pairs))
    disk=[]
    if not overlay:
        b=(d/'PROBE.EXE').read_bytes(); header=struct.unpack_from('<H',b,8)[0]*16
        nr=struct.unpack_from('<H',b,6)[0]; rt=struct.unpack_from('<H',b,24)[0]
        rels=[sg*16+of for of,sg in (struct.unpack_from('<HH',b,rt+4*j) for j in range(nr))]
        if len(locations)!=1: raise ValueError('missing or ambiguous slot map public')
        seg,off=locations[0]; at=seg*16+off; span=b[header+at:header+at+4]
        overlap=[x-at for x in rels if at-1<=x<at+4]
        disk={'slot_length':len(span),'unrelocated_all_zero':len(span)==4 and not any(span),
            'overlapping_relocation_word_offsets':overlap,'zero_before_crt':len(span)==4 and not any(span) and not overlap,'slot_sha256':sha(span)}
    result={'profile':profile,'case':label,'owner_overlay':overlay,'shifted_layout':shift is not None,
        'runner_returncode':r.returncode,'run_log':run,'link_diagnostics':diagnostics,
        'map_slot_locations':locations,'mz_slot_before_crt':disk,'inputs':pins+[pin(Path(runner['path']))],
        'artifacts':[pin(d/n) for n in ('PROBE.LNK','RTLINK.CFG','dosbox.conf','RUN.BAT','PROBE.MAP','LINK.LOG','RUN.LOG','PROBE.EXE')]}
    print(profile,label,run.strip().replace('\n','; '),flush=True); return result

def main():
    objects={}; facts=[]
    sources={'MAIN':MAIN,'OWN':'typedef char far * far *Handle;\nHandle far fd_50F6_46D2;\n',
        'ZERO':'typedef char far * far *Handle;\nHandle far fd_50F6_46D2 = 0;\n',
        'INIT':'typedef char far * far *Handle;\nextern char far * far fixtureMaster;\nHandle far fd_50F6_46D2 = &fixtureMaster;\n',
        'SHIFT':'char far fixtureShift[257] = {0x5a};\n',
        'RAWOWN':'char far * far fd_50F6_46D2;\n',
        # The rawfar contrast points into the representation of a 128-byte
        # struct, so its incorrect +32/+64 result stays inside test-owned storage.
        # Its first member is still the typed master cell at the same address.
        'RAWMAIN':MAIN.replace('extern Handle far fd_50F6_46D2;','extern char far * far fd_50F6_46D2;')
            .replace('char far * far fixtureMaster = fixturePixelsA;',
                'struct FixtureCell { char far *cell; char spare[124]; };\n'
                'struct FixtureCell far fixtureCell = {fixturePixelsA};\n'
                '#define fixtureMaster fixtureCell.cell')
            .replace('return *fd_50F6_46D2 +','return fd_50F6_46D2 +')
            .replace('fd_50F6_46D2=&fixtureMaster;','fd_50F6_46D2=(char far *)&fixtureCell;')}
    for label,source in sources.items():
        raw,fact=compile_one(label,source); objects[label]=raw; facts.append(fact)
    cases=[]
    for profile in ('rtlink400','rtlink610'):
        cases.append(run_case(profile,'typed-root',objects['MAIN'],objects['OWN']))
        cases.append(run_case(profile,'typed-overlay',objects['MAIN'],objects['OWN'],overlay=True))
        cases.append(run_case(profile,'typed-shifted',objects['MAIN'],objects['OWN'],objects['SHIFT']))
        cases.append(run_case(profile,'rawfar-negative',objects['RAWMAIN'],objects['RAWOWN']))
        cases.append(run_case(profile,'nonzero-initializer-negative',objects['MAIN'],objects['INIT']))
        cases.append(run_case(profile,'explicit-zero-nondiscriminator',objects['MAIN'],objects['ZERO']))
    for p in ('rtlink400','rtlink610'):
        root=next(r for r in cases if r['profile']==p and r['case']=='typed-root')
        shifted=next(r for r in cases if r['profile']==p and r['case']=='typed-shifted')
        shifted['location_changed_from_root']=shifted['map_slot_locations']!=root['map_slot_locations']
    expected={r['case']:('FAIL_POINTER_CHAIN_OR_BYTE_STRIDE' if r['case']=='rawfar-negative' else 'FAIL_INITIAL_ZERO' if r['case']=='nonzero-initializer-negative' else 'PASS_TYPED_RAW_WRITE_ZERO_RESET') for r in cases}
    for r in cases:
        r['expected_observation']=expected[r['case']]
        r['observation_pass']=r['expected_observation'] in r['run_log'] and not r['link_diagnostics']
    result={'schema':'dos-icon-handle-stock-controls-v37','admitted':False,'compiler_controls':facts,'cases':cases,
        'all_observations_as_expected':all(r['observation_pass'] for r in cases),
        'limits':['Test-owned cell/payload validity proves a typed ABI, not a game producer or resource lifetime.',
            'Initial zero is observed before any dereference. Nonzero initializer is rejected before dereference; rawfar contrast compares pointer values only.',
            'Explicit zero succeeds intentionally: runtime observations cannot distinguish zero initialized FAR_DATA from tentative FAR_BSS.',
            'Shifted layout tests symbolic references within this fixture, not the historical menu adjacency or hidden computed aliases.',
            'No original payload or game execution. Wrong two-byte ownership is compile-only in audit_v37.py.']}
    (OUT/'runtime-facts.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__': main()
