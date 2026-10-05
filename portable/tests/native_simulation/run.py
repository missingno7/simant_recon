"""Bounded original DOS / current canonical native DoAntMoveY differential.

Link the current whole-TU build's actual object list and canonical state owners.
Only explicit ordered host/caller observers match the original lane's fixtures.
No extracted target, selected-body native model, or shadow game state is used.
"""
from pathlib import Path
import argparse
import ctypes as ct
import hashlib
import json
import os
import random
import re
import subprocess
import sys
import time
from types import SimpleNamespace

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'src/program.json').is_file())
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
import behavior as b
import canonical
import functions
import fixtures

BOUNDARIES=['DoEditUpdateDraw','GotoMyAnt','myBeginSound','ResetYellowVars',
            'YellowDeath','myBeginSong','EditMessage','TickCount']
EVENT_NAMES={i+1:n for i,n in enumerate(BOUNDARIES)}

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def resolve(name, aliases):
    seen=set()
    while name in aliases and name not in seen:
        seen.add(name); name=aliases[name]
    return name

def native_function_body(text,name):
    """Locate a modern-width definition with the shared lexical tokenizer."""
    tokens=[t for t in b.csrc.tokenize(text) if t.kind not in ('ws','nl','cmt')]
    openings=[]
    for i,t in enumerate(tokens):
        if t.text!=name or i+1>=len(tokens) or tokens[i+1].text!='(':continue
        j=i+2;depth=1
        while j<len(tokens) and depth:
            depth+=int(tokens[j].text=='(')-int(tokens[j].text==')');j+=1
        if j<len(tokens) and tokens[j].text=='{':openings.append(j)
    if len(openings)!=1:raise ValueError('unique current native definition required: '+name)
    j=openings[0];start=tokens[j].s;depth=1;j+=1
    while j<len(tokens) and depth:
        depth+=int(tokens[j].text=='{')-int(tokens[j].text=='}');j+=1
    if depth:raise ValueError('unclosed current native function: '+name)
    return start,tokens[j-1].e

def corpus(count,seed):
    # Goal stays distant, maps bounded, no entrance/exit, carrying, death or UI flow.
    for mode in (0,1,2):
        for heading,(dx,dy) in enumerate(zip((0,1,1,1,0,-1,-1,-1),(-1,-1,0,1,1,1,0,-1))):
            for blocked in (False,True):
                obstacles=[(64+dx,32+dy,0x54)] if blocked else ()
                yield fixtures.case_for(seed+mode*32+heading,mode,64,32,
                    64+dx*6,32+dy*6,obstacles=obstacles,
                    ant_type=0x10,move_count=heading&1,path_delay=-1)
    r=random.Random(seed)
    for i in range(count):
        x,y=r.randrange(8,120),r.randrange(8,56)
        dx,dy=r.choice(((0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1)))
        obstacles=[]; occupied=[]
        for nx in range(x-1,x+2):
            for ny in range(y-1,y+2):
                if (nx,ny)==(x,y):continue
                if r.randrange(3)==0:obstacles.append((nx,ny,r.choice((0x54,0x80,0x90,0xa0,0xff))))
                if r.randrange(5)==0:occupied.append((nx,ny,r.choice((0x18,0x28,0x48))))
        yield fixtures.case_for(seed+i+1000,i%3,x,y,x+dx*6,y+dy*6,
            terrain=i&1,obstacles=obstacles,occupied=occupied,
            ant_type=r.choice((0x08,0x10,0x20,0x30,0x40)),
            move_count=i&1,path_delay=r.choice((-2,-1,0,1,4)))

def tick_cases():
    """Actual queen RNG rejection and health/death paths, excluding egg creation."""
    for plane in (1,2,3):
        for phase,health,ant_type,seed in ((0,63,0x10,0x20),(16,63,0x60,0x20),
                (16,63,0x60,0x8000),(17,1,0x10,0x3f),(16,0,0x10,0x21)):
            case=fixtures.case_for(seed,0,32,32,38,32,plane=plane,ant_type=ant_type)
            replacements={b.symbol_address('MeHealth'):(health&0xffff).to_bytes(2,'little'),
                          b.symbol_address('g_8BA2'):seed.to_bytes(2,'little')}
            case.writes=[(a,replacements.get(a,d)) for a,d in case.writes]
            case.writes.extend([fixtures.word_write('fd_50F6_0A06',0),
                fixtures.word_write('Cycle',phase,1),fixtures.word_write('fd_50F6_1006',99)])
            case.observe.extend([b.Range('Cycle',b.symbol_address('Cycle'),1),
                b.Range('fd_50F6_1006',b.symbol_address('fd_50F6_1006'),2)])
            case.label=f'tick/plane{plane}/phase{phase}/health{health}/seed{seed:04x}'
            case.metadata['target']='DoAntSimY';case.metadata['RNG_seed']=seed
            yield case

def callback_cases():
    for mode in (0,1,2):
        case=fixtures.case_for(0x8000+mode,mode,64,32,64,32)
        address=b.symbol_address('fd_3D57_07A8')
        case.writes=[(a,b'\x01\x00' if a==address else d) for a,d in case.writes]
        case.label=f'movement/completed-goal/ordered-callbacks/mode{mode}'
        yield case

class Event(ct.Structure):
    _fields_=[('kind',ct.c_int32),('count',ct.c_int32),('args',ct.c_int32*3)]

def build_native(build,out,mutation=None):
    out.mkdir(parents=True,exist_ok=True)
    report_path=build/'report.json'; report=json.loads(report_path.read_text())
    if report['schema']!='canonical-native-complete-attempt-v1' or not report['core_link']['passed']:
        raise ValueError('current canonical native build with successful core link required')
    if report.get('passed') is False or report.get('conversion_failures'):
        raise ValueError('native build is not green')
    # Native services may be built from an installation proposal while the
    # canonical sources still come from ROOT. Resolve each pinned namespace
    # from the report's actual source paths, never from a historical snapshot.
    provider_roots=set()
    for row in report['native_services']:
        source=Path(row['source']);generated=Path(row['generated']).resolve()
        if tuple(generated.parts[-len(source.parts):])!=source.parts:
            raise ValueError('native service source path does not match receipt')
        provider_roots.add(generated.parents[len(source.parts)-1])
    if len(provider_roots)!=1:raise ValueError('single current platform source root required')
    provider_root=provider_roots.pop()
    def input_path(name):
        path=Path(name)
        return path if path.is_absolute() else (provider_root if path.parts[0]=='portable' else ROOT)/path
    for name,expected in report.get('input_pins',{}).items():
        path=input_path(name)
        if sha(path)!=expected:raise ValueError('current native build input changed: '+name)
    objects=report['core_link']['object_inputs']
    if not objects or any(Path(p).suffix!='.o' for p in objects):
        raise ValueError('native report core object list changed')
    response=Path(report['core_link']['response_file'])
    expected_response='\n'.join('"'+Path(p).as_posix()+'"' for p in objects[1:])+'\n'
    if sha(response)!=report['core_link']['response_file_sha256'] or response.read_text(encoding='utf-8')!=expected_response:
        raise ValueError('native core linker response differs from its object inventory')
    native_rows=[r for r in report['canonical_TUs'] if r.get('compile',{}).get('passed')]
    if not any(r['source']=='src/S25/m3BA4.c' for r in native_rows):
        raise ValueError('whole canonical S25 target TU missing from native build')
    pins={str(Path(p).resolve().relative_to(ROOT)):sha(p) for p in objects}
    pins[str(report_path.relative_to(ROOT))]=sha(report_path)
    for row in native_rows:
        pins[row['source']]=sha(ROOT/row['source'])
        p=Path(row['generated']);pins[str(p.resolve().relative_to(ROOT))]=sha(p)
    for row in report['native_services']+report['canonical_ASM_data_translations']:
        p=Path(row['generated']);pins[str(p.resolve().relative_to(ROOT))]=sha(p)
    for name,expected in report.get('input_pins',{}).items():
        path=input_path(name)
        pins[str(path.resolve().relative_to(ROOT))]=expected
    control=None
    if mutation:
        mutation_target,old,new=mutation
        row=next(r for r in native_rows if r['source']=='src/S25/m3BA4.c')
        path=Path(row['generated']);text=path.read_text(encoding='latin1')
        body_start,body_end=native_function_body(text,mutation_target)
        body=text[body_start:body_end]
        if body.count(old)!=1:raise ValueError('unique current-body mutation anchor changed')
        modified=text[:body_start]+body.replace(old,new)+text[body_end:]
        mutant_source=out/'S25-mutant.c';mutant_source.write_text(modified,encoding='latin1')
        compile_command=list(row['compile']['command'])
        original_object=compile_command[compile_command.index('-o')+1]
        mutant_object=out/'S25-mutant.o'
        compile_command[compile_command.index('-c')+1]=str(mutant_source)
        compile_command[compile_command.index('-o')+1]=str(mutant_object)
        compile_result=subprocess.run(compile_command,capture_output=True,text=True)
        (out/'mutation-compile.txt').write_text(compile_result.stdout+compile_result.stderr)
        if compile_result.returncode:raise RuntimeError('whole-current-TU mutation failed to compile')
        objects=[str(mutant_object) if Path(p)==Path(original_object) else p for p in objects]
        control={'target':mutation_target,'change':[old,new],'current_whole_source_sha256':sha(path),
            'mutant_whole_source_sha256':sha(mutant_source),'compile_command':compile_command,
            'mutant_object_sha256':sha(mutant_object)}
    response=out/'fixture-objects.rsp'
    response.write_text('\n'.join('"'+Path(p).as_posix()+'"' for p in objects)+'\n',encoding='utf-8')
    pins[str(response)]=sha(response)
    command=[report['core_link']['command'][0],'-shared','-Wl,--export-all-symbols',
        *['-Wl,--wrap='+n for n in BOUNDARIES],str(HERE/'native_callbacks.c'),
        '-Wl,@fixture-objects.rsp',str(Path(report['sdk']['path'])/'lib/libSDL3.dll.a'),
        '-o',str(out/'native.dll')]
    run=subprocess.run(command,cwd=out,capture_output=True,text=True)
    (out/'link.txt').write_text(run.stdout+run.stderr)
    if run.returncode:raise RuntimeError('native fixture link failed: '+run.stderr[:2000])
    dll_dir=os.add_dll_directory(str(Path(report['sdk']['path'])/'bin'))
    lib=ct.CDLL(str(out/'native.dll'))
    lib.DoAntMoveY.argtypes=[];lib.DoAntMoveY.restype=None
    lib.DoAntSimY.argtypes=[];lib.DoAntSimY.restype=None
    lib.SetSRandSeed.argtypes=[ct.c_int16];lib.SetSRandSeed.restype=None
    lib.GetSRandSeed.argtypes=[];lib.GetSRandSeed.restype=ct.c_uint32
    lib.native_fixture_reset.argtypes=[ct.c_uint32];lib.native_fixture_reset.restype=None
    lib.native_fixture_event_count.restype=ct.c_int32
    lib.native_fixture_events.restype=ct.POINTER(Event)
    return lib,pins,command,dll_dir,control

def bindings(lib,program,cases):
    aliases={x['alias'].lstrip('_@'):x for x in program['aliases'] if x['kind']!='code'}
    sizes={r.name:r.size for c in cases for r in c.observe if r.name!='g_8BA2'}
    sizes['Cycle']=1
    sizes['fd_50F6_0A06']=2
    sizes['fd_3D57_0C22']=2
    text=(HERE/'fixtures.py').read_text()
    for name in re.findall(r'word_write\("([^"]+)"',text):sizes.setdefault(name,2)
    for name in ('fd_3D57_02A4','fd_3D57_02A8','fd_3D57_02AC','fd_3D57_02B0'):sizes[name]=4
    sizes['fd_50F6_0214']=4
    result={}
    for name,size in sizes.items():
        if name=='g_8BA2':continue
        spec=aliases.get(name); owner=spec.get('target',spec.get('owner')).lstrip('_@') if spec else name
        offset=spec.get('offset',0) if spec else 0
        native=ct.addressof(ct.c_uint8.in_dll(lib,owner))+offset
        result[name]={'dos':b.symbol_address(name),'native':native,'size':size,
                      'owner':owner,'offset':offset,'baseline':ct.string_at(native,size)}
    return result

def native_run(lib,case,storage):
    for spec in storage.values():ct.memmove(spec['native'],spec['baseline'],spec['size'])
    seed_address=b.symbol_address('g_8BA2')
    seed=None
    for address,data in case.writes:
        if address==seed_address:
            seed=int.from_bytes(data,'little');continue
        found=[s for s in storage.values() if s['dos']<=address and address+len(data)<=s['dos']+s['size']]
        if not found:raise AssertionError(f'unbound canonical fixture write {address:x}+{len(data)}')
        spec=min(found,key=lambda s:s['size'])
        ct.memmove(spec['native']+address-spec['dos'],data,len(data))
    if seed is None:raise AssertionError('fixture RNG seed missing')
    lib.SetSRandSeed(ct.c_int16(seed).value)
    lib.native_fixture_reset(case.state['tick'])
    getattr(lib,case.metadata.get('target','DoAntMoveY'))()
    ranges={r.name:(lib.GetSRandSeed()&0xffff).to_bytes(2,'little').hex() if r.name=='g_8BA2'
        else ct.string_at(storage[r.name]['native'],storage[r.name]['size']).hex() for r in case.observe}
    events=[]
    for e in lib.native_fixture_events()[:lib.native_fixture_event_count()]:
        events.append((EVENT_NAMES[e.kind],[int(a)&0xffff for a in e.args[:e.count]]))
    return {'ranges':ranges,'events':events,
        'bound_state':{n:ct.string_at(s['native'],s['size']).hex() for n,s in storage.items()}}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--native-build',type=Path,required=True)
    ap.add_argument('--out',type=Path,default=ROOT/'build/current/tests/simulation')
    ap.add_argument('--random-count',type=int,default=128)
    ap.add_argument('--seed',type=lambda v:int(v,0),default=0xC0DE25)
    args=ap.parse_args();out=args.out.absolute()
    from workspace import prepare_output
    prepare_output(out,ROOT/'build/current/tests/simulation',ROOT)
    build=args.native_build.resolve();start=time.monotonic()
    program=canonical.load();cases=list(corpus(args.random_count,args.seed))+list(callback_cases())+list(tick_cases())
    lib,pins,command,dll_dir,_=build_native(build,out)
    for p in (Path(__file__),HERE/'fixtures.py',HERE/'native_callbacks.c',ROOT/'src/program.json',ROOT/'tools/behavior.py'):
        pins[str(p.relative_to(ROOT))]=sha(p)
    imported_files=sorted({Path(m.__file__).resolve() for m in list(sys.modules.values())
        if getattr(m,'__file__',None) and Path(m.__file__).suffix=='.py'
        and Path(m.__file__).resolve().is_relative_to(ROOT)})
    for p in imported_files:pins[str(p.relative_to(ROOT))]=sha(p)
    forbidden=[str(p.relative_to(ROOT)) for p in imported_files if '/archive/' in p.as_posix()
        or any(x in p.as_posix() for x in ('/tests/yellow/','/source_conversion/','/portable/game/'))]
    if forbidden:raise ValueError('retired execution dependency: '+str(forbidden))
    code_aliases={x['alias'].lstrip('_@'):x.get('target',x.get('owner')).lstrip('_@') for x in program['aliases'] if x['kind']=='code'}
    storage=bindings(lib,program,cases)
    owned_addresses={a for s in storage.values() for a in range(s['dos'],s['dos']+s['size'])}
    owned_addresses.update(range(b.symbol_address('g_8BA2'),b.symbol_address('g_8BA2')+2))
    machines={name:b.Machine(SimpleNamespace(function=functions.get(name),
        vectors={b.exe.MANAGER_SEG*16+v.offset:v for v in b.exe.load().vectors},delegate={}))
        for name in ('DoAntMoveY','DoAntSimY')}
    failures=[];matched=0;ledger=[]
    for case in cases:
        try:
            target=case.metadata.get('target','DoAntMoveY');machine=machines[target]
            oracle=machine.run(case);native=native_run(lib,case,storage);diff={}
            escaped=sorted(set(oracle['written_addresses'])-owned_addresses)
            if escaped:diff['unbound_oracle_effects']=escaped
            for name,spec in storage.items():
                expected=machine.read(spec['dos'],spec['size']).hex()
                actual=native['bound_state'][name]
                if expected!=actual:diff[name]={'oracle':expected,'native':actual}
            for name,actual in native['ranges'].items():
                expected=oracle['ranges'][name]
                if expected!=actual:diff[name]={'oracle':expected,'native':actual}
            expected_events=[(resolve(e['name'],code_aliases),list(e['args'])) for e in oracle['trace']]
            if expected_events!=native['events']:diff['ordered_callbacks']={'oracle':expected_events,'native':native['events']}
            ledger.append({'case':case.label,'target':target,'input':case.metadata['input'],'diff':diff,
                'oracle_events':expected_events,'native_events':native['events'],
                'RNG_before':case.metadata.get('RNG_seed',0xbeef),'RNG_after':int.from_bytes(bytes.fromhex(native['ranges']['g_8BA2']),'little'),
                'oracle_state_sha256':hashlib.sha256(json.dumps(oracle['ranges'],sort_keys=True).encode()).hexdigest()})
            if diff:failures.append(ledger[-1]);break
            matched+=1
        except Exception as exc:
            failures.append({'case':case.label,'execution_error':repr(exc)});break
    controls=[]
    if not failures:
        mutations=[('DoAntMoveY','fd_50F6_0C3E++;','fd_50F6_0C3E += 2;'),
            ('DoAntMoveY','ResetYellowVars(MePlane, MeLocX, MeLocY);',
             'ResetYellowVars(MePlane, MeLocY, MeLocX);'),
            ('DoAntSimY','if (MeHealth <= 0) {','SRand128();\n    if (MeHealth <= 0) {')]
        for index,mutation in enumerate(mutations):
            mutant,control_pins,control_command,control_dll_dir,negative=build_native(build,out/f'negative-{index}',mutation)
            pins.update(control_pins);negative['link_command']=control_command
            mutation_storage=bindings(mutant,program,cases)
            detected=None
            for case in cases:
                if case.metadata.get('target','DoAntMoveY')!=mutation[0]:continue
                machine=machines[case.metadata.get('target','DoAntMoveY')]
                oracle=machine.run(case);result=native_run(mutant,case,mutation_storage)
                different=[name for name,value in result['ranges'].items() if value !=
                    oracle['ranges'][name]]
                expected=[(resolve(e['name'],code_aliases),list(e['args'])) for e in oracle['trace']]
                if expected!=result['events']:different.append('ordered_callbacks')
                if different:
                    detected={'case':case.label,'state_fields':different};break
            negative['detected']=detected;negative['execution_errors']=0;controls.append(negative)
            if detected is None:failures.append({'control_error':'whole-current-TU mutation escaped corpus','mutation':mutation})
    (out/'cases.json').write_text(json.dumps(ledger,indent=2)+'\n')
    changed=[p for p,h in pins.items() if sha(ROOT/p)!=h]
    report={'schema':'canonical-native-simulation-differential-v1','pass':not failures and not changed,
        'targets':['DoAntMoveY','DoAntSimY'],'cases_requested':len(cases),'matched':matched,'failures':failures,
        'elapsed_seconds':round(time.monotonic()-start,3),'seed':args.seed,
        'directed_cases':66,'random_cases':args.random_count,'native_build':str(build.relative_to(ROOT)),
        'whole_TU':'src/S25/m3BA4.c','definition_sha256':{name:canonical.definition_sha((ROOT/'src/S25/m3BA4.c').read_text(encoding='latin1'),name)
            for name in ('DoAntMoveY','DoAntSimY')},
        'native_command':command,'native_library_sha256':sha(out/'native.dll'),
        'oracle_sha256':b.exe.load().sha256,'inputs':pins,'changed_inputs':changed,
        'imported_repository_python_files':[str(p.relative_to(ROOT)) for p in imported_files],
        'forbidden_retired_execution_dependencies':forbidden,
        'host':{'python':sys.version,'unicorn':b.uc.__version__,
                'compiler':command[0],'compiler_sha256':sha(command[0])},
        'canonical_state_bindings':{n:{k:v for k,v in s.items() if k in ('owner','offset','size')} for n,s in storage.items()},
        'negative_controls':controls,
        'coverage':{'RNG_advanced_cases':sum(r['RNG_before']!=r['RNG_after'] for r in ledger),
                    'ordered_callback_cases':sum(bool(r['oracle_events']) for r in ledger),
                    'all_oracle_nonstack_writes_bound':not any(r['diff'].get('unbound_oracle_effects') for r in ledger)},
        'boundaries':BOUNDARIES,'effects':['canonical maps and Life grids','yellow state and health',
            'RNG preservation and actual source RNG advancement','ordered callback names and argument words'],
        'scope':'Finite surface interior DoAntMoveY caller contracts in modes 0/1/2, plus DoAntSimY health/death and queen RNG rejection paths across the three planes. Actual converted whole TUs, canonical ordinary state owners and RNG execute. The listed host/caller observer bodies are excluded identically in DOS/native. Egg creation, nest exit, full tick, backend and whole-game equality remain outside this corpus.'}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'pass':report['pass'],'matched':matched,'requested':len(cases),'first_failure':failures[:1]},indent=2))
    return int(not report['pass'])

if __name__=='__main__':raise SystemExit(main())
