"""Default-VGA mode invariant and original icon pointer-load exclusion.

Fixtures stop at renderer entry: they do not accept renderer behavior or the
complete helper return ABI. Reviewed source pins carry the lifetime proof.
"""
from pathlib import Path
from types import SimpleNamespace
import sys,json,struct,hashlib,re,importlib.util
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'src/program.json').is_file())
sys.path.insert(0,str(ROOT/'tools'))
import behavior as b,exe,functions,csrc
if not __debug__:raise RuntimeError('proof checks require Python without -O')
TARGETS={'g_5A97','g_6298','ReadConfig','IBMInitStuff','f_205F_0004','main',
         'fd_50F6_46D2','f_208F_027F','f_208F_02F0'}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def norm(text):return ' '.join(t.text for t in csrc.tokenize(text) if t.kind not in {'ws','nl','cmt'})
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def inventory():
    return load('icon_inventory','evidence/canonical/window-domain/handle_owner_probe.py').inventory()

def inventory_pins(texts,program,registry):
    """Require review even for changes with no protected symbolic spelling."""
    def digest(value):return sha(json.dumps(value,sort_keys=True,separators=(',',':')).encode())
    return dict(source_count=len(texts),
        all_source_sha256=digest({p:sha(t.encode()) for p,t in texts.items()}),
        modules_sha256=digest(program['modules']),
        aliases_sha256=digest(program['aliases']),
        registry_sha256=digest(registry))

def census(texts,program,registry):
    def undecorated(name):return name[1:] if name.startswith(('_','@')) else name
    roots={n:n for n in sorted(TARGETS)}
    edges={n:(r['alias_of'],0) for category in ('code','data') for n,r in registry[category].items() if r.get('alias_of')}
    for r in program['aliases']:
        a,t=undecorated(r['alias']),undecorated(r['target'])
        if a!=t or r.get('offset',0):edges[a]=(t,r.get('offset',0))
    for alias in edges:
        target,offset,seen=alias,0,set()
        while target in edges:
            if target in seen:raise ValueError('alias cycle')
            seen.add(target);target,delta=edges[target];offset+=delta
        if target in TARGETS:roots[alias]=target
        # A linker alias may reach a protected byte through a different base.
        for category in ('data','code'):
            r=registry[category].get(target)
            if not r:continue
            at=r['seg']*16+r['off']+offset
            for name in sorted(TARGETS):
                protected=registry[category].get(name)
                length={'g_5A97':1,'g_6298':2,'fd_50F6_46D2':4}.get(name,1)
                if (protected and r.get('unit')==protected.get('unit') and
                    0 <= at-(protected['seg']*16+protected['off']) < length):
                    roots[alias]=name
    for category in ('code','data'):
        addresses={(r.get('unit'),r['seg'],r['off']):n for n,r in registry[category].items() if n in TARGETS}
        for n,r in registry[category].items():
            target=addresses.get((r.get('unit'),r['seg'],r['off']))
            if target:roots[n]=target
    rows=[];pins={}
    for path,text in sorted(texts.items()):
        if path.endswith('.asm'):
            for i,line in enumerate(text.splitlines(),1):
                code=line.split(';',1)[0]
                for token in re.findall(r'[A-Za-z_@][A-Za-z_0-9]*',code):
                    key=undecorated(token).casefold()
                    if key in {n.casefold() for n in roots}:rows.append([path,i,token,code.strip()]);pins[path]=sha(text.encode())
            continue
        for token in csrc.tokenize(text):
            if token.kind=='pp' and any(re.search(r'\b'+re.escape(n)+r'\b',token.text) for n in roots):raise ValueError('preprocessor escape')
            if token.kind=='id' and token.text in roots:
                line=text[text.rfind('\n',0,token.s)+1:text.find('\n',token.e) if '\n' in text[token.e:] else len(text)]
                rows.append([path,roots[token.text],token.text,norm(line)]);pins[path]=sha(text.encode())
    return {'aliases':roots,'occurrences':len(rows),'occurrence_sha256':sha(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()),'source_sha256':pins}

def saves(texts,raw=None):
    db=load('icon_database','evidence/canonical/database-domain/replay.py')
    db.save_table_proof(texts) # Independently binds every current source descriptor to the original.
    m=db.oracle_machine('OpenDB')
    raw=raw if raw is not None else m.read(b.symbol_address('fd_4E4B_0000'),308*8)
    protected={'g_5A97':1,'g_6298':2,'fd_50F6_46D2':4}
    for i in range(307):
        size,count,off,seg=struct.unpack_from('<HHHH',raw,i*8);start=seg*16+off
        for name,length in protected.items():
            at=b.symbol_address(name)
            if start<at+length and at<start+size*count:raise ValueError('save reaches protected state: '+name)
    assert raw[-8:]==bytes(8)
    return {'records':307,'descriptor_sha256':sha(raw),'protected':protected,'overlaps':0}
class Boundary(Exception): pass

def ptr(name):
    s=b.symbol(name);return b.words(s['off'],s['seg'])

def case(name,mode,n,slot):
    x=exe.load();m=b.Machine(SimpleNamespace(function=functions.get(name),vectors={exe.MANAGER_SEG*16+v.offset:v for v in x.vectors}))
    at=b.symbol_address('fd_50F6_46D2');reads=[]
    def read(cpu,access,address,size,value,data):
        if at<=address<at+4:reads.append([address-at,size])
    m.cpu.hook_add(b.uc.UC_HOOK_MEM_READ,read)
    def rect(cpu,args):
        cpu.write(args[2]*16+args[1],b.words(10,20,30,40));return 0
    def stop(cpu,args): raise Boundary()
    callbacks={'win_GetObjRect':b.Callback(2,rect,register_args=('ax',),pop=4),
        'f_277D_000B':b.Callback(6,stop),
        'f_277D_000C':b.Callback(3,stop)}
    c=b.Case('icon',args=[0x100,n] if name.endswith('027F') else [10,20,n],return_kind='void',callbacks=callbacks,
        writes=[(at,b.words(*slot)),(b.symbol_address('g_5A97'),bytes([mode])),
                (b.symbol_address('g_914C'),ptr('f_277D_000B')),
                (b.symbol_address('g_917C'),ptr('f_277D_000C')),
                (0x70000,b.words(0,0x7100))])
    try: m.run(c)
    except b.ExecutionError as exc:
        if not isinstance(exc.__cause__,Boundary): raise
    else: raise AssertionError('missed renderer boundary')
    rendered=[r for r in m.raw_trace if r['name'] in {'f_277D_000B','f_277D_000C'}]
    assert len(rendered)==1
    return dict(function=name,mode=mode,n=n,slot=list(slot),slot_reads=reads,render=rendered[0])

def collect():
    texts,program,registry=inventory();snapshot=census(texts,program,registry)
    db=load('icon_database_scope','evidence/canonical/database-domain/replay.py')
    db.inventory_and_scan();resource=db.verify_resource_domain()
    assert resource['config']['ReadConfig_g_5A97']==8
    controls=[case(f,mode,n,slot) for f in ['f_208F_027F','f_208F_02F0']
        for mode in [8,2] for n in [0,1,0xffff] for slot in [(0,0),(0,0x7000)]]
    for row in controls:
        assert bool(row['slot_reads'])==(row['mode']==2)
        assert row['render']['name']==('f_277D_000C' if row['mode']==8 else 'f_277D_000B')
    return {'schema':'simant-icon-vga-domain-v1','scope':'Only pointer-load exclusion in the existing default VGA successful-lifetime domain; no external-call, renderer, other-mode or corrupted-control-flow acceptance.',
            'oracle_sha256':exe.load().sha256,'inventory':inventory_pins(texts,program,registry),
            'census':snapshot,'config':resource['config'],
            'save_load':saves(texts),'original_controls':controls}

def check():
    actual=collect()
    expected=json.loads((Path(__file__).parent/'vga-facts.json').read_text())
    if actual!=expected:raise ValueError('default VGA icon proof differs from reviewed facts')
    return actual

if __name__=='__main__':
    result=check()
    print('PASS: default VGA icon exclusion; %d original prefix controls' %
          len(result['original_controls']))
