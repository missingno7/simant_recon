"""Link whole current/candidate LZSS sources with a shifted test-owned DGROUP.

Reads no original executable or game resource. Writes only this worker tree.
Once canonical is admitted, invoke --source src/root/m1B05.asm; the legacy
negative is derived by removing the decoder-region SS assumption pair.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
OUT = None
sys.path.insert(0, str(ROOT/'tools'))
import compiler
from omf import OmfReader

SITES = [(45,22),(53,22),(60,22),(67,22),(74,22),(106,10),
         (120,10),(141,8),(161,10),(171,10),(194,4),(201,20),
         (243,20),(250,8)]

def pin(path):
    body = path.read_bytes()
    return {'path':path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path),'size':len(body),'sha256':hashlib.sha256(body).hexdigest()}

def owner(prefix):
    return f"""PREFIX segment word public 'DATA'
public _prefix_start,_prefix_end
_prefix_start label byte
db {prefix} dup (0A5h)
_prefix_end label byte
PREFIX ends
_DATA segment word public 'DATA'
_DATA ends
DGROUP group PREFIX,_DATA
end
"""

def checker():
    lines = [
      "TEST_DATA segment word public 'DATA'", "public _test_input,_test_output",
      "_test_input db 1,41h,0EEh,0F1h", "_test_output db 5 dup (0)",
      "TEST_DATA ends", "DGROUP group TEST_DATA", "extrn _f_1B05_0008:far,_f_1B05_0046:far",
      "CHECK_TEXT segment word public 'CODE'", "assume cs:CHECK_TEXT,ds:DGROUP",
      "public _FrameProbe,_open,_read,_close", "_FrameProbe proc far",
      "push bx", "push si", "push di", "push ds", "push es",
      "mov bx,DGROUP", "mov ax,ss", "cmp ax,bx", "je ss_ok", "jmp failed",
      "ss_ok:", "mov ax,ds", "cmp ax,bx", "je ds_ok", "jmp failed",
      "ds_ok:", "mov byte ptr cs:ObservedState,0",
      "mov ax,seg _f_1B05_0046", "mov es,ax", "mov si,offset _f_1B05_0046",
      # The unmodified epilogue's State store offset is a DGROUP-framed owner anchor.
      "mov bx,word ptr es:[si+276]",
    ]
    for i,(off,displacement) in enumerate(SITES):
        lines += ["mov dx,bx",f"sub dx,{22-displacement}",
                  f"cmp word ptr es:[si+{off}],dx",f"je site_{i}_ok", "jmp failed",f"site_{i}_ok:"]
    # Negative cannot enter decoder. Positive initializes authentic ring state,
    # decodes one literal plus one source-propagating backreference into 5 'A's.
    lines += [
      "mov ax,4", "push ax", "push ds", "mov ax,offset DGROUP:_test_input", "push ax",
      "call far ptr _f_1B05_0008", "add sp,6",
      "mov ax,5", "push ax", "push ds", "mov ax,offset DGROUP:_test_output", "push ax",
      "call far ptr _f_1B05_0046", "add sp,6", "cmp ax,5", "jne failed",
      "mov si,offset DGROUP:_test_output", "mov di,offset ObservedOutput",
      "mov cx,5", "check_bytes:", "mov al,byte ptr [si]", "mov byte ptr cs:[di],al",
      "cmp al,41h", "jne failed", "inc si", "inc di", "loop check_bytes",
      "mov byte ptr cs:ObservedStatus,0", "jmp short emit_result",
      "failed:", "mov byte ptr cs:ObservedStatus,1",
      "emit_result:", "push ds", "push cs", "pop ds", "mov dx,offset ObservedStatus",
      "mov cx,7", "mov bx,1", "mov ah,40h", "int 21h", "pop ds",
      "xor ax,ax", "mov al,byte ptr cs:ObservedStatus", "pop es", "pop ds",
      "pop di", "pop si", "pop bx", "retf", "_FrameProbe endp",
      # These are fixture boundary providers; reaching one fails visibly.
      "_open proc far", "mov ax,4C02h", "int 21h", "retf", "_open endp",
      "_read proc far", "mov ax,4C02h", "int 21h", "retf", "_read endp",
      "_close proc far", "mov ax,4C02h", "int 21h", "retf", "_close endp",
      "ObservedStatus db 0FFh", "ObservedState db 0FFh", "ObservedOutput db 5 dup (0)",
      "CHECK_TEXT ends", "end", ""
    ]
    return '\n'.join(lines)

def compile_source(name,body,c=False):
    source = OUT/'fixture_sources'/(name+('.c' if c else '.asm'))
    source.parent.mkdir(exist_ok=True)
    source.write_text(body,encoding='ascii')
    result = (compiler.compile_c(body,'msc600ax',['/AL','/Os','/Gs'],basename=name,keep=True)
              if c else compiler.assemble(body,'masm510',['/Mx'],basename=name,keep=True))
    (OUT/'fixture_sources'/(name+'.compile.log')).write_text(result.log)
    assert result.ok,result.log
    obj = OUT/'fixture_objects'/(name+'.OBJ')
    obj.parent.mkdir(exist_ok=True)
    obj.write_bytes(result.obj)
    return OmfReader(communals=True).read(result.obj)

def mz(raw):
    header = struct.unpack_from('<H',raw,8)[0]*16
    count,table = struct.unpack_from('<H',raw,6)[0],struct.unpack_from('<H',raw,24)[0]
    return raw[header:], [list(struct.unpack_from('<HH',raw,table+4*i)) for i in range(count)]

def maps(body):
    publics = {name:{'segment':int(seg,16),'offset':int(off,16)} for seg,off,name in
      re.findall(r'^\s*([0-9A-F]{4}):([0-9A-F]{4})\s+(\S+)\s*$',body,re.M)}
    group = re.search(r'^\s*([0-9A-F]{4}):([0-9A-F]{1,4})\s+DGROUP\s*$',body,re.M)
    assert group
    return publics, int(group[1],16)*16+int(group[2],16)

def run(linker,prefix,variant,tool_dir):
    tc=compiler.toolchain()
    tool=tc['linkers'][linker]
    runner=tc['runners'][tool['runner']]
    directory=OUT/'fixture_links'/linker/(str(prefix)+'_'+variant)
    directory.mkdir(parents=True,exist_ok=True)
    names=['OWNER'+str(prefix),variant,'CRT','CHECK']
    for name in names:
        shutil.copyfile(OUT/'fixture_objects'/(name+'.OBJ'),directory/(name+'.OBJ'))
    runtime=json.loads((ROOT/'layout/manifest.json').read_text())['runtime']['libraries'].values()
    for spec in runtime:
        path=Path(spec['path'])
        assert pin(path)['sha256']==spec['sha256']
        shutil.copyfile(path,directory/path.name.upper())
    (directory/'PROBE.LNK').write_bytes(('\r\n'.join(['OUTPUT PROBE','MAP = PROBE S,N,A,L',
       'NODEFLIB','LIBRARY LLIBCR, LIBH','FILE '+', '.join(names)])+'\r\n').encode('ascii'))
    (directory/'RTLINK.CFG').write_bytes(b'SYNTAX = FREEFORMAT\r\n')
    batch=f"""@echo off
D:\\{tool['executable']} @PROBE.LNK < NUL > LINK.LOG
if not exist PROBE.EXE goto noexe
PROBE.EXE > OBS.BIN
if errorlevel 1 goto fail
echo PASS > RUN.LOG
goto done
:fail
echo FAIL > RUN.LOG
goto done
:noexe
echo NOEXE > RUN.LOG
:done
"""
    (directory/'RUN.BAT').write_bytes(batch.replace('\n','\r\n').encode('ascii'))
    config=[]
    for section,options in runner['conf'].items():
        config += ['['+section+']']+[str(k)+'='+str(v) for k,v in options.items()]
    config += ['[autoexec]',f'mount c "{directory}"',f'mount d "{tool_dir}" -ro',
               'c:','call RUN.BAT','exit']
    conf=directory/'dosbox.conf'
    conf.write_text('\n'.join(config)+'\n')
    result=subprocess.run([runner['path'],'-conf',str(conf),'-fastlaunch','-exit','-nomenu'],
       cwd=directory,env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},
       stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=60,
       creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    assert result.returncode==0
    log=(directory/'LINK.LOG').read_text(encoding='latin1')
    assert not re.search(r'\bwrt\d{4}\b|\b(?:warnings?|errors?|fatal|undefined|unresolved|aborted)\b|cannot\s+open',log,re.I),log
    image,relocs=mz((directory/'PROBE.EXE').read_bytes())
    public,group=maps((directory/'PROBE.MAP').read_text(encoding='latin1'))
    first=public['_f_1B05_0008']
    proc=public['_f_1B05_0046']
    assert proc['segment']==first['segment'] and proc['offset']-first['offset']==62
    codebase=proc['segment']*16+proc['offset']
    state=struct.unpack_from('<H',image,codebase+276)[0]
    owner_begin=group+state-22
    prefix_start=public['_prefix_start']['segment']*16+public['_prefix_start']['offset']
    prefix_end=public['_prefix_end']['segment']*16+public['_prefix_end']['offset']
    assert prefix_end-prefix_start==prefix
    assert group<=prefix_start<prefix_end<=owner_begin
    site_rows=[]
    for off,displacement in SITES:
        actual=struct.unpack_from('<H',image,codebase+off)[0]
        expected=state-22+displacement
        site_rows.append({'operand_offset':off,'displacement':displacement,'actual':actual,'expected_DGROUP':expected,'passed':actual==expected,'linked_linear':codebase+off})
    status=(directory/'RUN.LOG').read_text().strip()
    observed=(directory/'OBS.BIN').read_bytes()
    if variant=='POS':
        assert all(r['passed'] for r in site_rows)
        assert observed==bytes([0,0,65,65,65,65,65]),observed
        assert status=='PASS',status
    else:
        assert not any(r['passed'] for r in site_rows)
        assert observed==bytes([1,0,0,0,0,0,0]),observed
        assert status=='FAIL',status
    print(linker,prefix,variant,status,observed.hex(' '),flush=True)
    return {'linker':linker,'test_prefix_length':prefix,'variant':variant,'runtime_result':status,
      'observations':observed.hex(' '),'CRT_DS_SS_DGROUP_state_asserted':True,
      'whole_TU_code_anchor':proc,'linked_DGROUP_linear':group,'linked_private_DATA_begin':owner_begin,
      'actual_14_linked_operands':site_rows,'MZ_relocations':relocs,
      'files':[pin(directory/name) for name in ['PROBE.EXE','PROBE.MAP','PROBE.LNK','RUN.BAT','LINK.LOG','RUN.LOG','OBS.BIN','dosbox.conf']]}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path)
    args=ap.parse_args()
    global OUT
    build=(ROOT/'build').resolve()
    if args.out is None:
        parent=build/'scratch'/'proofs'
        parent.mkdir(parents=True,exist_ok=True)
        OUT=Path(tempfile.mkdtemp(prefix='lzss-data-frame-',dir=parent))
    else:
        OUT=(ROOT/args.out).resolve()
        OUT.relative_to(build)
        if OUT==build or (OUT.exists() and any(OUT.iterdir())):
            raise ValueError('--out must be a fresh subdirectory under build/')
        OUT.mkdir(parents=True,exist_ok=True)
    args.source=Path('src/root/m1B05.asm')
    compiler.WORK=OUT/'fixture_compile'
    path=args.source if args.source.is_absolute() else ROOT/args.source
    positive=path.read_text()
    negative,count=re.subn(r'(?m)^\tassume\tss:DGROUP[^\n]*\n','',positive)
    assert count==1
    negative,count=re.subn(r'(?m)^(\tassume\tds:DGROUP), ss:nothing$',r'\1',negative)
    assert count==1
    pos=compile_source('POS',positive)
    neg=compile_source('NEG',negative)
    assert pos.segments==neg.segments
    assert pos.segment_defs==neg.segment_defs and pos.publics==neg.publics
    assert len(pos.linker_fixups)==len(neg.linker_fixups)==61
    changed=[(a,b) for a,b in zip(neg.linker_fixups,pos.linker_fixups) if a!=b]
    assert len(changed)==14
    for old,new in changed:
        for field in ('segment','offset','width','loc','self_relative','target_kind','target','displacement','encoded_addend'):
            assert old[field]==new[field]
        assert old['frame']=='_DATA' and new['frame']=='DGROUP'
    compile_source('CRT','extern int far FrameProbe(void);\nint main(void) { return FrameProbe(); }\n',c=True)
    compile_source('CHECK',checker())
    for prefix in (16,80):
        compile_source('OWNER'+str(prefix),owner(prefix))
    tc=compiler.toolchain()
    cases=[]
    for linker in ('rtlink400','rtlink610'):
        spec=tc['linkers'][linker]
        for relative,expected in spec['files'].items():
            assert pin(Path(spec['directory'])/relative)['sha256']==expected
        runner=tc['runners'][spec['runner']]
        assert pin(Path(runner['path']))['sha256']==runner['sha256']
        tool_dir=compiler.pinned_tree(spec)
        for prefix in (16,80):
            for variant in ('POS','NEG'):
                cases.append(run(linker,prefix,variant,tool_dir))
    pair_checks=[]
    for linker in ('rtlink400','rtlink610'):
        for prefix in (16,80):
            rows={r['variant']:r for r in cases if r['linker']==linker and r['test_prefix_length']==prefix}
            images={v:mz((OUT/'fixture_links'/linker/(str(prefix)+'_'+v)/'PROBE.EXE').read_bytes())[0] for v in ('POS','NEG')}
            assert rows['POS']['MZ_relocations']==rows['NEG']['MZ_relocations']
            allowed={r['linked_linear']+delta for r in rows['POS']['actual_14_linked_operands'] for delta in (0,1)}
            assert len(images['POS'])==len(images['NEG'])
            differences=[i for i,(a,b) in enumerate(zip(images['POS'],images['NEG'])) if a!=b]
            assert all(i in allowed for i in differences),differences
            pair_checks.append({'linker':linker,'prefix':prefix,'all_other_linked_bytes_equal':True,
              'MZ_relocation_set_order_equal':True,'changed_operand_byte_locations':differences})
    receipt={'schema':'lzss-real-linker-ss-frame-v1','source':pin(path),
       'scope':'Whole LZSS TU address operands inspected, safe positive valid-data decode executed; negative fails before decoder. Test-owned shifted DGROUP, pinned CRT/MASM/RTLink, no original game image/resource input.',
       'cases':cases,'whole_linked_pair_controls':pair_checks,'all_required_checks_pass':True,
       'pins':[pin(Path(__file__)),pin(ROOT/'layout/toolchain.json'),pin(ROOT/'tools/compiler.py'),pin(ROOT/'tools/omf.py')]}
    (OUT/'lzss_link_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')

if __name__=='__main__':
    main()
