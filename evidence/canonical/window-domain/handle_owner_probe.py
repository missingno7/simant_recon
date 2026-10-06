"""Proposed handle-owner census and original initial/read-boundary controls."""
from pathlib import Path
from types import SimpleNamespace
import hashlib, json, re, struct, sys
sys.dont_write_bytecode=True
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'src/program.json').is_file())
sys.path.insert(0,str(ROOT/'tools'))
import behavior as b
import csrc, exe, functions
if not __debug__: raise RuntimeError('proof checks require Python without -O')
sha=lambda data:hashlib.sha256(data).hexdigest()
OWNER='src/state/window-handles.c'
SOURCES=['src/root/m20E8.c','src/root/m23AE.c','src/root/m22BF.c','src/root/m2505.c','src/S09/m35F5.c']
class Reject(RuntimeError): pass
class BoundaryReached(Exception): pass
def norm(t):return ' '.join(x.text for x in csrc.tokenize(t) if x.kind not in {'ws','nl','cmt'})
def ident(n):return n.lstrip('_@')

def aliases(program,registry):
    edges={n:(r['alias_of'],0) for category in ('code','data','runtime') for n,r in registry.get(category,{}).items() if 'alias_of' in r}
    for row in program['aliases']:
        n,target=ident(row['alias']),ident(row.get('target',row.get('owner','')))
        if n==target and row.get('offset',0)==0:continue
        if n in edges and (ident(edges[n][0]),edges[n][1])!=(target,row.get('offset',0)):raise Reject('program/registry alias conflict')
        edges[n]=(target,row.get('offset',0))
    result={'win_handles':0}
    for n in edges:
        target=n; offset=0; seen=set()
        while target in edges:
            if target in seen:raise Reject('alias cycle')
            seen.add(target);target,delta=edges[target];target=ident(target);offset+=delta
        if target=='win_handles':result[ident(n)]=offset
    at=b.symbol_address('win_handles')
    for name,r in registry['data'].items():
        if r['seg']*16+r['off']==at and ident(name) not in result:raise Reject('unresolved same-address storage identity: '+name)
    return result

def census(texts,program,registry):
    known=aliases(program,registry); rows=[]
    for rel,text in sorted(texts.items()):
        if rel==OWNER:
            if norm(text)!=norm('char far * far * near win_handles[34];'):raise Reject('owner has extra consumer/function/initializer or wrong declaration')
            continue
        if rel.endswith('.asm'):
            for lineno,line in enumerate(text.splitlines(),1):
                code=re.sub(r'"[^\"]*"','',line.split(';',1)[0])
                if any(ident(n).casefold() in {k.casefold() for k in known} for n in re.findall(r'[A-Za-z_][A-Za-z0-9_]*',code)):raise Reject('unreviewed ASM table reference: '+rel)
            continue
        for t in csrc.tokenize(text):
            if t.kind=='pp' and any(re.search(r'\b'+re.escape(n)+r'\b',t.text) for n in known):raise Reject('table preprocessor escape')
            if t.kind=='id' and t.text in known:
                line=text[text.rfind('\n',0,t.s)+1:text.find('\n',t.e) if '\n' in text[t.e:] else len(text)]
                rows.append([rel,t.text,known[t.text],norm(line)])
    return dict(aliases=known,occurrences=rows,source_sha256={p:sha(texts[p].encode()) for p in SOURCES})

def inventory():
    program=json.loads((ROOT/'src/program.json').read_text()); texts={}
    for m in program['modules']:
        rel=m['source'].replace('\\','/');data=(ROOT/rel).read_bytes()
        if rel in texts or sha(data)!=m['source_sha256']:raise Reject('inventory hash/duplicate mismatch')
        texts[rel]=data.decode('utf8')
    found={p.relative_to(ROOT).as_posix() for p in (ROOT/'src').rglob('*') if p.suffix.lower() in {'.c','.asm'}}
    if found!={p for p in texts if p.endswith(('.c','.asm'))}:raise Reject('incomplete inventory')
    return texts,program,json.loads((ROOT/'layout/symbols.json').read_text())

def machine(name):
    image=exe.load()
    if sha((ROOT/'assets/SIMANT.EXE').read_bytes())!=exe.EXPECTED_SHA256:raise Reject('oracle changed')
    return b.Machine(SimpleNamespace(function=functions.get(name),vectors={exe.MANAGER_SEG*16+v.offset:v for v in image.vectors},identity={'oracle_sha256':image.sha256}))

def boundary_run(m,case,entry=None):
    try:m.run(case,original_entry=entry)
    except b.ExecutionError as e:
        if not isinstance(e.__cause__,BoundaryReached):raise
    else:raise Reject('original prefix missed its bounded stop')

def startup_zero_control(cx=None):
    m=machine('win_IsWinOpen');start=0x8b9e;stop=0x94f0;dg=0x55b30
    m.cpu.hook_add(b.uc.UC_HOOK_CODE,lambda cpu,at,size,user:(_ for _ in ()).throw(BoundaryReached('before C initialization')) if at==0x29f40+0xab else None)
    prefix=dict(seg=0x29f4,off=0x9c if cx is None else 0xa7)
    regs={} if cx is None else {'es':0x55b3,'di':start,'cx':cx}
    boundary_run(m,b.Case('original-CRT-BSS-zero',registers=regs,writes=[(dg+start,bytes([0x5a])*(stop-start))],return_kind='void'),prefix)
    cleared=m.read(dg+start,stop-start)==bytes(stop-start)
    table=m.read(b.symbol_address('win_handles'),34*4)
    if cleared!=(cx is None) or (table==bytes(136))!=(cx is None):raise Reject('CRT zero/zero-count contrast differs')
    return dict(entry=prefix,original_clear_start=start,original_clear_end=stop,incoming_cx=cx,proposed_table_zero=table==bytes(136),entire_BSS_interval_zero=cleared,scope='Original CRT instructions execute after stack setup and before C init/main; no DOS service or allocator model in this prefix')

def lock_read_control(n,nonzero=False,guard=0):
    m=machine('f_23AE_0069');events=[];base=b.symbol_address('win_handles')
    def hook(cpu,at,size,user):
        if at==0x23ae0+0xab:
            events.append(dict(event='table-word-read-at-original-00AB',index=m.reg('si'),offset=m.reg('bx')+2,within_proposed_136_bytes=m.reg('bx')+4<=136))
    m.cpu.hook_add(b.uc.UC_HOOK_CODE,hook)
    def lookup(m,args):events.append(dict(event='resource-lookup',arguments=args));return (0,0)
    def punt(m,args):events.append(dict(event='Punt',guard=guard));raise BoundaryReached('first diagnostic boundary')
    def allocator(m,args):events.append(dict(event='allocator-Handle-consumer',arguments=args));raise BoundaryReached('nonzero table cell used without loading')
    callbacks={'f_1A53_00F0':b.Callback(3,lookup),'f_171C_1AD4':b.Callback(2,allocator)}
    if not guard:callbacks['Punt']=b.Callback(3,punt)
    writes=[(0x55b30+0x644c,b.words(1)),(0x55b30+0x644e,b.words(0)),(base+n*4,b.words(0x1234,0xa200) if nonzero else bytes(4)),(0x55b30+0x8da6+n,bytes(1)),(0x55b30+0x54f8,b.words(guard))]
    boundary_run(m,b.Case('original-lock-index-'+str(n),registers={'ax':n<<8,'dx':0},writes=writes,callbacks=callbacks,return_kind='void'))
    if n<=40 and events[0]['event']!='table-word-read-at-original-00AB':raise Reject('table read ordering changed')
    if n>40 and not guard and events!=[dict(event='Punt',guard=0)]:raise Reject('high-index guard ordering changed')
    if nonzero and [e['event'] for e in events]!=['table-word-read-at-original-00AB','allocator-Handle-consumer']:raise Reject('nonzero adjacent cell did not bypass load')
    return dict(index=n,table_nonzero=nonzero,reporting_guard=guard,events=events,models='Resource lookup explicitly returns null; guard0 Punt is a bounded diagnostic stop, guard1 Punt executes actual returning original; allocator stops at first Handle consumer')

def save_nonoverlap():
    m=machine('win_IsWinOpen');raw=m.read(b.symbol_address('fd_4E4B_0000'),308*8);at=b.symbol_address('win_handles')
    for i in range(307):
        size,count,off,seg=struct.unpack_from('<HHHH',raw,i*8);start=seg*16+off;end=start+size*count
        if start<at+136 and at<end:raise Reject('original save transfer reaches proposed table')
    if raw[-8:]!=bytes(8):raise Reject('save sentinel')
    return dict(original_descriptors=307,table_bytes=136,intersections=0)

def negative_controls(texts,program,registry,expected):
    results=[]
    mutations={'new_reader':'void far rogue(void){ char far * far *h=win_handles[0]; }','new_writer':'void far rogue(void){win_handles[0]=0;}','base_escape':'void far *escape=win_handles;','address_escape':'void far *escape=&win_handles[0];','registry_alias':'void far rogue(void){g_9230[0]=0;}','uppercase_ASM':'extrn _WIN_HANDLES:byte','rogue_state':'char far * far * near win_handles[34]; void far rogue(void){win_handles[0]=0;}'}
    for label,text in mutations.items():
        changed=dict(texts);changed[OWNER if label=='rogue_state' else 'src/probe-negative'+('.asm' if label=='uppercase_ASM' else '.c')]=text
        try:actual=census(changed,program,registry)
        except Reject:results.append(label);continue
        if actual==expected:raise Reject('mutation accepted: '+label)
        results.append(label)
    changed=json.loads(json.dumps(program));changed['aliases'].append(dict(alias='_evil_handles',target='_g_9230',offset=4,kind='data'))
    src=dict(texts);src['src/negative.c']='void far *escape=evil_handles;'
    if census(src,changed,registry)==expected:raise Reject('program interior alias mutation accepted')
    results.append('program_interior_alias')
    return results

def collect():
    texts,program,registry=inventory();snapshot=census(texts,program,registry)
    saved=Path(__file__).with_name('handle-owner-review.json')
    expected=json.loads(saved.read_text())
    if snapshot!=expected:raise Reject('reviewed table census changed')
    result=dict(status='PASS',schema='simant-proposed-window-handle-owner-review-v1',capacity_claim='SUPPORTED_ROOT_PROOF_COMPOSED_IN_HANDLE_REVIEW',oracle_sha256=exe.load().sha256,initialization=[startup_zero_control(),startup_zero_control(0)],original_read_controls=[lock_read_control(33),lock_read_control(34),lock_read_control(34,True),lock_read_control(41),lock_read_control(41,True,guard=1)],save_load=save_nonoverlap(),negative_controls=negative_controls(texts,program,registry,expected),inventory_modules=len(texts))
    result.pop('inventory_modules')
    return result
if __name__=='__main__':print(json.dumps(collect(),indent=2))
