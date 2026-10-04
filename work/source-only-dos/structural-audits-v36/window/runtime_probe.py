"""Stock tool controls for the proven 45-entry initialized window views.

The 46-entry fixture is an intentional non-discriminating contrast: it must also
pass, demonstrating that these accesses do not measure a full physical extent.
No original binary or resource input is used in this script.
"""
from __future__ import annotations
import hashlib,json,os,re,shutil,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; OUT=Path(__file__).resolve().parent
sys.dont_write_bytecode=True; sys.path.insert(0,str(ROOT/'tools'))
import compiler
from omf import OmfReader
compiler.WORK=OUT/'cc'
def sha(b): return hashlib.sha256(b).hexdigest()
def pin(p):
 b=p.read_bytes(); return {'path':str(p).replace('\\','/'),'size':len(b),'sha256':sha(b)}
MAIN=r'''
struct Rect { int left,top,right,bottom; };
extern void (far * far win_drawHooks[])(int phase);
extern struct Rect far win_offsets[];
extern void far * far _fmemset(void far *, int, unsigned);
extern void far * far _fmemcpy(void far *, void far *, unsigned);
extern int far puts(char far *);
int calls;
void far callback(int phase) { calls += phase; }
int _fastcall windowIndex(int win) { return win >> 8; }
int _fastcall charWindowIndex(int win) { return (char)(win >> 8); }
void _fastcall setHook(int win, void (far *hook)(int phase))
{
    win_drawHooks[win >> 8] = hook;
}
int main(void)
{
    int i;
    unsigned char far *p;
    struct Rect input[40];
    struct Rect sentinel;
    p=(unsigned char far *)win_drawHooks;
    for(i=0;i<180;i++) if(p[i]) { puts("FAIL_INITIAL_FAR_HOOKS"); return 1; }
    p=(unsigned char far *)win_offsets;
    for(i=0;i<360;i++) if(p[i]) { puts("FAIL_INITIAL_FAR_RECTS"); return 2; }
    if(windowIndex(0x0000)!=0 || windowIndex(0x2800)!=40 ||
       windowIndex(0x2c00)!=44 || windowIndex(0x2d00)!=45 ||
       windowIndex((int)0x8000)!=-128 || windowIndex((int)0xff00)!=-1 ||
       charWindowIndex(0x2c00)!=44 || charWindowIndex(0x2d00)!=45 ||
       charWindowIndex((int)0x8000)!=-128 || charWindowIndex((int)0xff00)!=-1) {
        puts("FAIL_SIGNED_WINDOW_INDEX"); return 7;
    }
    sentinel.left=sentinel.top=sentinel.right=sentinel.bottom=(int)0x8000;
    _fmemset(win_drawHooks,0,180);
    for(i=0;i<45;i++) win_offsets[i]=sentinel;
    for(i=0;i<40;i++) {
        input[i].left=-100-i; input[i].top=200+i;
        input[i].right=-300-i; input[i].bottom=400+i;
    }
    _fmemcpy(win_offsets,input,320);
    for(i=0;i<40;i++)
        if(win_offsets[i].left!=-100-i || win_offsets[i].top!=200+i ||
           win_offsets[i].right!=-300-i || win_offsets[i].bottom!=400+i) {
            puts("FAIL_40_RECT_COPY"); return 3;
        }
    for(i=40;i<45;i++)
        if(win_offsets[i].left!=(int)0x8000 || win_offsets[i].top!=(int)0x8000 ||
           win_offsets[i].right!=(int)0x8000 || win_offsets[i].bottom!=(int)0x8000) {
            puts("FAIL_SENTINEL_TAIL"); return 4;
        }
    win_offsets[windowIndex(0x2c00)].right=-77;
    if(win_offsets[44].right!=-77 || win_offsets[43].right!=(int)0x8000) {
        puts("FAIL_SHIFTED_RECT_WRITE"); return 8;
    }
    setHook(0x0000,callback); setHook(0x2c00,callback);
    (*win_drawHooks[0])(1); (*win_drawHooks[44])(2);
    if(calls!=3) { puts("FAIL_CALLBACK"); return 5; }
    _fmemset(win_drawHooks,0,180);
    p=(unsigned char far *)win_drawHooks;
    for(i=0;i<180;i++) if(p[i]) { puts("FAIL_HOOK_CLEAR"); return 6; }
    puts("PASS_SIGNED_WINDOW_INDEX");
    puts("PASS_45_VIEW_RESET_40_COPY_CALLBACK"); return 0;
}
'''
def compile_one(label,text):
 d=OUT/'runtime-sources'; d.mkdir(exist_ok=True); p=d/(label+'.c'); p.write_text(text,encoding='ascii')
 r=compiler.compile_c(text,'msc600ax',['/AL','/Os','/Gs'],basename=label)
 (d/(label+'.compiler.log')).write_text(r.log,encoding='utf-8')
 if not r.ok: raise RuntimeError(r.log)
 (d/(label+'.obj')).write_bytes(r.obj); o=OmfReader(communals=True).read(r.obj)
 return r.obj,{'source':pin(p),'object_sha256':sha(r.obj),'communals':o.communals,
  'segment_lengths':o.segment_lengths,'publics':o.publics,'fixups':o.linker_fixups,
  'initialized_segments':{n:sha(bytes(b)) for n,b in o.segments.items()}}
def run_case(profile,label,main,owner,overlay):
 tc=compiler.toolchain(); prof=tc['linkers'][profile]; runner=tc['runners']['dosbox-x']; tools=compiler.pinned_tree(prof)
 d=OUT/'runtime'/profile/label; d.mkdir(parents=True,exist_ok=True)
 (d/'MAIN.OBJ').write_bytes(main); (d/'OWNER.OBJ').write_bytes(owner)
 libs=json.loads((ROOT/'layout/manifest.json').read_text())['runtime']['libraries']; pins=[]
 for n in ('llibcr.lib','libh.lib'):
  p=Path(libs[n]['path'])
  if sha(p.read_bytes())!=libs[n]['sha256']: raise ValueError('library pin drift')
  shutil.copyfile(p,d/n.upper()); pins.append(pin(p))
 script='OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\nLIBRARY LLIBCR, LIBH\r\nFILE MAIN\r\n'
 script+=('BEGINAREA\r\nSECTION FILE OWNER\r\nENDAREA\r\n' if overlay else 'FILE OWNER\r\n')
 (d/'PROBE.LNK').write_bytes(script.encode('ascii')); (d/'RTLINK.CFG').write_bytes(b'SYNTAX = FREEFORMAT\r\n')
 (d/'RUN.BAT').write_bytes(('@echo off\r\nD:\\'+prof['executable']+' @PROBE.LNK < NUL > LINK.LOG\r\nPROBE.EXE > RUN.LOG\r\n').encode('ascii'))
 lines=[]
 for sec,settings in runner['conf'].items():
  lines.append('['+sec+']'); lines += [str(k)+'='+str(v) for k,v in settings.items()]
 lines+=['[autoexec]','mount c "'+str(d)+'"','mount d "'+str(tools)+'" -ro','c:','call RUN.BAT','exit']
 conf=d/'dosbox.conf'; conf.write_text('\n'.join(lines)+'\n',encoding='ascii')
 env=os.environ.copy(); env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
 r=subprocess.run([runner['path'],'-conf',str(conf),'-fastlaunch','-exit','-nomenu'],cwd=d,env=env,
   stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=45,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
 run=(d/'RUN.LOG').read_text(encoding='latin1'); log=(d/'LINK.LOG').read_text(encoding='latin1'); mp=(d/'PROBE.MAP').read_text(encoding='latin1')
 diagnostics=[l for l in log.splitlines() if re.search(r'(?i)warning|error|wrt\d|undefined|unresolved|duplicate',l)]
 locations={}
 for n in ('_win_drawHooks','_win_offsets'):
  pairs=re.findall(r'(?im)^\s*([0-9a-f]{4}):([0-9a-f]{4})\s+(?:Res\s+)?'+re.escape(n)+r'\b',mp)
  locations[n]=sorted(set((int(s,16),int(o,16)) for s,o in pairs))
 # A plain root fixture's far common bytes must be explicit MZ payload, before CRT starts.
 disk=[]
 if not overlay:
  b=(d/'PROBE.EXE').read_bytes(); hdr=struct.unpack_from('<H',b,8)[0]*16
  nr,rt=struct.unpack_from('<H',b,6)[0],struct.unpack_from('<H',b,24)[0]
  reloc=[sg*16+of for of,sg in (struct.unpack_from('<HH',b,rt+4*j) for j in range(nr))]
  for n,length in (('_win_drawHooks',180),('_win_offsets',360)):
   if len(locations[n])!=1: raise ValueError('missing/ambiguous public')
   seg,off=locations[n][0]; at=hdr+seg*16+off; span=b[at:at+length]
   rel=[x-(seg*16+off) for x in reloc if seg*16+off-1 <= x < seg*16+off+length]
   disk.append({'name':n,'file_offset':at,'length':length,'present':len(span)==length,'unrelocated_all_zero':len(span)==length and not any(span),
     'relocated_word_offsets':rel,'zero_before_crt':len(span)==length and not any(span) and not rel,'sha256':sha(span)})
 result={'profile':profile,'case':label,'owner_in_overlay':overlay,'runner_returncode':r.returncode,
  'run_log':run,'link_diagnostics':diagnostics,'map_owner_locations':locations,'unrelocated_mz_far_bytes_and_relocations':disk,
  'inputs':pins+[pin(Path(runner['path']))],
  'artifacts':[pin(d/n) for n in ('PROBE.LNK','PROBE.MAP','LINK.LOG','RUN.LOG','PROBE.EXE')]}
 print(profile,label,run.strip(),flush=True); return result
def main():
 objects={}; facts=[]
 raw,fact=compile_one('MAIN',MAIN); objects['main']=raw; facts.append(fact)
 for n in (40,45,46):
  source='struct Rect { int left,top,right,bottom; };\nvoid (far * far win_drawHooks[%d])(int phase);\nstruct Rect far win_offsets[%d];\n'%(n,n)
  raw,fact=compile_one('OW%d'%n,source); objects[n]=raw; facts.append(fact)
 source='struct Rect { int left,top,right,bottom; };\nextern void far callback(int phase);\nvoid (far * far win_drawHooks[45])(int phase) = {callback};\nstruct Rect far win_offsets[45];\n'
 raw,fact=compile_one('OWINIT',source); objects['init']=raw; facts.append(fact)
 cases=[]
 for profile in ('rtlink400','rtlink610'):
  cases.append(run_case(profile,'view45-root',objects['main'],objects[45],False))
  cases.append(run_case(profile,'view45-overlay',objects['main'],objects[45],True))
  cases.append(run_case(profile,'view46-counterexample',objects['main'],objects[46],False))
  cases.append(run_case(profile,'nonzero-initializer',objects['main'],objects['init'],False))
 result={'schema':'window-initialized-view-controls-v36','root_reviewed':False,'admitted':False,
  'whole_source_compiler_controls':facts,'cases':cases,'claim_limits':[
   'Natural MSC far COMDEF allocations, pointer/Rect ABI, loaded zero bytes and known resets/copies/callbacks only.',
   '46-entry case passes intentionally: measured accesses are insufficient to distinguish full owner size.',
   '40-entry owner is compile-only: inadequate to cover proven reset spans; no unsafe overrun executed.',
   'No original owner, historic link version/order/layout, game execution or unrestricted window/palette domain claim.']}
 (OUT/'runtime-facts.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
if __name__=='__main__': main()
