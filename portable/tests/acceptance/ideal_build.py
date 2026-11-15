"""Build the ideal-v1 observer from pinned DOSBox-X sources and readable patches.

Every installed TU which includes pic.h is recompiled. No installed source or
object is written, and the normal core executes every guest instruction.
"""
from pathlib import Path
import concurrent.futures
import hashlib
import json
import os
import re
import subprocess
import time

HERE=Path(__file__).resolve().parent
SOURCE=Path('C:/tools/dosbox-x-2026.08.31-simant-acceptance-observation-src')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def apply_patch(source,patch):
    """Apply all unified hunks with exact context; no fuzz or ignored lines."""
    original=source.splitlines(True);lines=patch.splitlines(True);result=[];position=0;i=2
    while i<len(lines):
        match=re.match(r'@@ -(\d+)(?:,\d+)? \+\d+(?:,\d+)? @@',lines[i])
        if not match:raise ValueError('Invalid patch header: '+lines[i])
        start=int(match[1])-1;i+=1;old=[];new=[]
        while i<len(lines) and not lines[i].startswith('@@ '):
            line=lines[i];i+=1
            if line[0] in ' -':old.append(line[1:])
            if line[0] in ' +':new.append(line[1:])
        if start<position or original[start:start+len(old)]!=old:raise ValueError('Patch context differs')
        result+=original[position:start]+new;position=start+len(old)
    return ''.join(result+original[position:])

def build(out):
    out=out.resolve();out.mkdir(parents=True,exist_ok=False);(out/'include').mkdir();(out/'ideal').mkdir()
    patches=HERE/'ideal';pins=json.loads((patches/'source-pins.json').read_text())
    own_inputs={str(p.resolve()):sha(p) for p in [Path(__file__),HERE/'compact_observer.inc',HERE/'event_context_rule.h',HERE/'animation_identity.h',HERE/'build_observer.py',*patches.glob('*')] if p.is_file()}
    inputs={}
    for path,expected in pins.items():
        source=SOURCE/path
        if sha(source)!=expected:raise ValueError('Pinned emulator source differs: '+path)
        inputs[str(source)]=expected
        destination=out/('include/pic.h' if path=='include/pic.h' else Path(path).name)
        destination.write_text(apply_patch(source.read_text(encoding='utf-8'),(patches/(source.name+'.patch')).read_text(encoding='utf-8')),encoding='utf-8')
    for name in ('ideal_clock.inc','native_clock_v1.h'):(out/'ideal'/name).write_bytes((patches/name).read_bytes())
    (out/'compact_observer.inc').write_bytes((HERE/'compact_observer.inc').read_bytes())
    (out/'event_context_rule.h').write_bytes((HERE/'event_context_rule.h').read_bytes())
    (out/'animation_identity.h').write_bytes((HERE/'animation_identity.h').read_bytes())
    obj=SOURCE/'obj/dosbox-x/x64/Release SDL2';logs=obj/'dosbox-x.tlog'
    clines=(logs/'CL.command.1.tlog').read_text(encoding='utf-16').splitlines()
    # Compiler include dependency logs identify every consumer of the changed
    # inline PIC time reader. Rebuild those, plus every directly patched TU.
    dependencies=(logs/'CL.read.1.tlog').read_text(encoding='utf-16').splitlines()
    consumers=set();current=None
    for line in dependencies:
        if line.startswith('^'):current=Path(line[1:]).stem.lower()
        elif line.upper().endswith('\\INCLUDE\\PIC.H') and current:consumers.add(current)
    consumers.update(Path(p).stem for p in pins if p.endswith('.cpp'))
    jobs={}
    for i,line in enumerate(clines[:-1]):
        if not line.startswith('^'):continue
        source=Path(line[1:]);stem=source.stem.lower()
        if stem not in consumers:continue
        args=clines[i+1]
        args=re.sub(r'/Fo"[^"]*"',lambda m:'/Fo"'+str(out/(stem+'.obj'))+'"',args,flags=re.I)
        args=re.sub(r'/Fd"[^"]*"',lambda m:'/Fd"'+str(out/(stem+'.pdb'))+'"',args,flags=re.I)
        # The final argument is the source; retain original flags and include
        # directories, preferring our frozen-time pic.h and patched siblings.
        args=args[:args.upper().rfind(' C:\\TOOLS\\')]
        patched=out/(stem+'.cpp');selected=patched if patched.exists() else source
        args='/I"'+str(out/'include')+'" /DSIMANT_IDEAL_BUILD '+args+' "'+str(selected)+'"'
        args+=' /I"'+str(source.parent)+'" /I"'+str(SOURCE/'src/cpu')+'" /I"'+str(SOURCE/'src/ints')+'"'
        (out/(stem+'.rsp')).write_text(args);jobs[stem]=selected
        inputs[str(source)]=sha(source)
    if consumers-set(jobs):raise ValueError('No compiler recipe: '+str(consumers-set(jobs)))
    link=(logs/'link.command.1.tlog').read_text(encoding='utf-16').splitlines()
    start=max(i for i,l in enumerate(link) if l.startswith('^'));link='\n'.join(link[start+1:])
    for option,name in [('OUT','dosbox-x.exe'),('PDB','dosbox-x.pdb'),('IMPLIB','dosbox-x.lib'),('LTCGOUT','dosbox-x.iobj')]:
        link=re.sub('/'+option+r':"[^"]*"',lambda m:'/'+option+':"'+str(out/name)+'"',link,flags=re.I)
    link=re.sub(r'/NATVIS:\S+','',link,flags=re.I)
    for stem in jobs:link=re.sub(r'"[^"\n]*\\'+re.escape(stem)+r'\.OBJ"',lambda m:'"'+str(out/(stem+'.obj'))+'"',link,flags=re.I)
    (out/'link.rsp').write_text(link)
    vc=Path('C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Auxiliary/Build/vcvars64.bat')
    (out/'environment.cmd').write_text('@echo off\ncall "'+str(vc)+'" >nul\nset\n')
    env=dict(os.environ)
    for line in subprocess.check_output(['cmd','/c',str(out/'environment.cmd')],text=True).splitlines():
        if '=' in line:k,v=line.split('=',1);env[k]=v
    compiler=Path(env['VCToolsInstallDir'])/'bin/Hostx64/x64/cl.exe'
    def compile(stem):
        with (out/(stem+'.log')).open('w') as log:
            run=subprocess.run([str(compiler),'@'+stem+'.rsp'],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=300)
        if run.returncode:raise RuntimeError((out/(stem+'.log')).read_text()[-4000:])
    started=time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(compile,jobs))
    with (out/'link.log').open('w') as log:
        run=subprocess.run([str(compiler.with_name('link.exe')),'@link.rsp'],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=600)
    if run.returncode:raise RuntimeError((out/'link.log').read_text()[-4000:])
    if any(sha(Path(p))!=expected for p,expected in own_inputs.items()):
        raise ValueError('Observer source changed during build; rebuild before recording')
    inputs.update(own_inputs)
    inputs.update({str(p):sha(p) for p in obj.glob('*.obj')})
    receipt=dict(schema='simant-ideal-observer-build-v1',contract='ideal-v1',clock_revision='native-clock-v1-display-v4',executable=str(out/'dosbox-x.exe'),sha256=sha(out/'dosbox-x.exe'),inputs=inputs,
        compiled_units=sorted(jobs),seconds=time.perf_counter()-started,
        scope='ideal-v1 program-read clock, real guest instructions/PIC/IRQs, tick-script input, observation-only state/frame/audio outputs')
    (out/'observer-build.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('inputs','compiled_units')},indent=2),flush=True)
