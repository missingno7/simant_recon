"""Bounded original CRT entry -> main trace with explicit modeled DOS services.

No original disk artifact is modified. Standard load relocations are applied only
to the independent Unicorn address space, as the DOS loader would apply them.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'layout/functions.json').is_file())
sys.path.insert(0,str(ROOT/'tools'))
sys.path.insert(0,str(ROOT/'build/deps/unicorn'))
import exe
import modctx
import unicorn as uc
from unicorn import x86_const as xr

x=exe.load()
MAN=json.loads((ROOT/'layout/manifest.json').read_text())
SYMBOLS=json.loads((ROOT/'layout/symbols.json').read_text())
ORACLE=json.loads((ROOT/'layout/oracle.lock.json').read_text())
assert x.sha256==ORACLE['executable']['sha256']
assert uc.__version__=='2.1.4',uc.__version__
from omf import OmfReader
READER=OmfReader(communals=True)

def pin(path):
    path=Path(path).resolve()
    raw=path.read_bytes()
    return {'path':str(path),'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

INPUTS={}
INPUTS['original_executable']=pin(x.path)
for rel in ['src/program.json','layout/manifest.json','layout/symbols.json',
            'layout/functions.json','layout/oracle.lock.json','layout/toolchain.json',
            'evidence/toolchain/runtime-location.json','tools/exe.py','tools/omf.py',
            'tools/runtime.py']:
    INPUTS[rel]=pin(ROOT/rel)
for key in ['root:171C','root:15F8']:
    row=MAN['modules'][key]
    source=pin(ROOT/row['source'])
    assert source['sha256']==row['source_sha256'],(key,source['sha256'])
    INPUTS[row['source']]=source
HEADER=Path('C:/tools/msc-6.00/STARTUP/heap.inc')
INPUTS['heap.inc']=pin(HEADER)
assert INPUTS['heap.inc']['sha256']=='61f9321fa552ecae0b8fcf5b4f695a2464dddd88342fee4b60d34e819f4b59ba'
LIBRARY_OBJECTS={}
for lib,spec in MAN['runtime']['libraries'].items():
    info=pin(spec['path'])
    assert info['sha256']==spec['sha256'],lib
    INPUTS[lib]=info
    LIBRARY_OBJECTS[lib]=[(name,blob,READER.read(blob,name))
                         for name,blob in READER.split_library(Path(spec['path']).read_bytes())]
RUNTIME_PINS=[]
for row in MAN['runtime']['members']:
    name,blob,obj=LIBRARY_OBJECTS[row['library']][row['module_index']]
    assert name==row['member']
    assert hashlib.sha256(blob).hexdigest()==row['member_sha256'],name
    RUNTIME_PINS.append({k:row[k] for k in ['library','member','module_index','member_sha256','linear','size']})

def original_code(name,section):
    row=SYMBOLS[section][name]
    assert row['unit']=='root'
    return row['seg'],row['off'],row['seg']*16+row['off']

ENTRY_SEG,ENTRY_OFF,ENTRY_LINEAR=original_code('__astart','runtime')
MAIN_SEG,MAIN_OFF,MAIN_LINEAR=original_code('main','code')
ALLOC_SEG,ALLOC_OFF,ALLOC_LINEAR=original_code('malloc','code')
assert (ENTRY_SEG,ENTRY_OFF)==(0x29F4,0x1c)
assert (MAIN_SEG,MAIN_OFF)==(0x15F8,4)
assert (ALLOC_SEG,ALLOC_OFF)==(0x171C,0x2208)
CRTROW=next(r for r in MAN['runtime']['members'] if r['member']=='dos\\crt0.asm')
CRTOBJ=LIBRARY_OBJECTS[CRTROW['library']][CRTROW['module_index']][2]
ASTART=next(p for p in CRTOBJ.publics if p['name']=='__astart')
assert ENTRY_LINEAR==CRTROW['linear']+ASTART['offset']
MAIN_FIX=next(f for f in CRTOBJ.linker_fixups if f['target_kind']=='external' and f['target']=='_main')
assert MAIN_FIX['loc']=='pointer32' and MAIN_FIX['segment']==CRTROW['segment']
assert struct.unpack('<HH',x.read('root',CRTROW['linear']+MAIN_FIX['offset'],4))==(MAIN_OFF,MAIN_SEG)
ALLOCROW=next(r for r in MAN['runtime']['members'] if r['member']=='dos\\stdalloc.asm')
ALLOCOBJ=LIBRARY_OBJECTS[ALLOCROW['library']][ALLOCROW['module_index']][2]
ALLOC_FIX=next(f for f in ALLOCOBJ.linker_fixups if f['target_kind']=='external' and f['target']=='_malloc')
assert ALLOC_FIX['loc']=='pointer32' and ALLOC_FIX['segment']==ALLOCROW['segment']
assert struct.unpack('<HH',x.read('root',ALLOCROW['linear']+ALLOC_FIX['offset'],4))==(ALLOC_OFF,ALLOC_SEG)

def accepted_data_public(member,public):
    row=next(r for r in MAN['runtime']['members'] if r['member']==member)
    obj=LIBRARY_OBJECTS[row['library']][row['module_index']][2]
    pb=next(p for p in obj.publics if p['name']==public)
    ds=next(s for s in row['data_segments'] if s['segment']==pb['segment'])
    return ds['linear']+pb['offset']

AMBLKSIZ_LINEAR=accepted_data_public('growseg.asm','__amblksiz')
NHEAP_LINEAR=accepted_data_public('dos\\crt0.asm','__nheap_desc')
assert AMBLKSIZ_LINEAR==0x55B3*16+0x79FE
assert NHEAP_LINEAR==0x55B3*16+0x7706
HELPERS={original_code(n,'runtime')[2]:n for n in
         ['__initseg','__linkseg','__searchseg','__growseg','__newseg']}
FDATA=next((ix,n,b,o) for ix,(n,b,o) in enumerate(LIBRARY_OBJECTS['llibcr.lib']) if n=='fdata.asm')
assert FDATA[0]==51 and hashlib.sha256(FDATA[2]).hexdigest()=='7eb6a9bfcb257d6470b0bc9c9f7c6215052a7a78749e463a4a6ebaa2294e70ec'
assert x.read('S27',0x55B3*16+0x79F0,14)==bytes(FDATA[3].segments['_DATA'])
REG={n:getattr(xr,'UC_X86_REG_'+n.upper()) for n in
     ('ax','bx','cx','dx','si','di','bp','sp','ip','cs','ds','es','ss','eflags')}

def run(loadseg, env_text):
    machine=uc.Uc(uc.UC_ARCH_X86,uc.UC_MODE_16)
    machine.mem_map(0,0x110000)
    base=loadseg*16
    machine.mem_write(base,x.image)
    s27=x.sections[27]
    machine.mem_write(base+s27.load_linear,s27.data)
    for unit in ['root','S27']:
        for sg,off in x.unit_relocs(unit):
            a=base+sg*16+off
            v=int.from_bytes(machine.mem_read(a,2),'little')
            machine.mem_write(a,struct.pack('<H',(v+loadseg)&0xffff))
    psp=loadseg-16
    env=psp-0x200
    machine.mem_write(psp*16+2,struct.pack('<H',0xA000))
    machine.mem_write(psp*16+0x2c,struct.pack('<H',env))
    machine.mem_write(psp*16+0x80,b'\x00\r')
    machine.mem_write(env*16,env_text+b'\x00\x00\x01\x00C:\\SIMANT.EXE\x00')
    for r,v in {'cs':loadseg+ENTRY_SEG,'ip':ENTRY_OFF,'ss':loadseg+x.mz.ss,
                'sp':x.mz.sp,'ds':psp,'es':psp,'eflags':0x202}.items():
        machine.reg_write(REG[r],v)
    target=base+MAIN_LINEAR
    watch={
        'candidate_fheap':(base+0x55B3*16+0x79F0,14),
        'amblksiz_positive':(base+AMBLKSIZ_LINEAR,2),
        'nheap_desc_positive':(base+NHEAP_LINEAR,20)}
    initial={k:bytes(machine.mem_read(a,n)).hex() for k,(a,n) in watch.items()}
    writes={k:[] for k in watch}
    dos=[]
    trace={'count':0,'reached_main':False,'reached_game_allocator':0,
           'reached_msc_fheap_helpers':[],'stop_reason':None}
    free_start=loadseg+0x55B3+0x1000+0x10
    free_paras=0xA000-free_start
    assert free_paras>0 and free_start*16>max(a+n for a,n in watch.values())
    vectors={}
    heap_helpers={base+r:label for r,label in HELPERS.items()}
    def get(r): return machine.reg_read(REG[r])
    def put(r,v): machine.reg_write(REG[r],v)
    def carry(flag): put('eflags',(get('eflags')|1) if flag else (get('eflags')&~1))
    def on_write(_m,_access,address,size,value,_data):
        for k,(a,n) in watch.items():
            if a<address+size and address<a+n:
                writes[k].append({'instruction_cs':get('cs'),'instruction_ip':get('ip'),
                                 'address':address,'size':size,'value':value})
    def on_code(_m,address,size,_data):
        trace['count']+=1
        if address==target:
            trace['reached_main']=True
            trace['stop_reason']='main entry'
            machine.emu_stop()
        elif address==base+ALLOC_LINEAR:
            trace['reached_game_allocator']+=1
        if address in heap_helpers:
            trace['reached_msc_fheap_helpers'].append(heap_helpers[address])
        if trace['count']>=200000:
            trace['stop_reason']='instruction bound'
            machine.emu_stop()
    def on_intr(_m,number,_data):
        nonlocal free_start,free_paras
        ax=get('ax'); ah=ax>>8; al=ax&0xff
        entry={'int':number,'ax':ax,'bx':get('bx'),'cx':get('cx'),'dx':get('dx'),
               'cs':get('cs'),'ip':get('ip')}
        if number!=0x21:
            trace['stop_reason']=f'unmodeled interrupt {number:02x}'
            dos.append(entry); machine.emu_stop(); return
        if ah==0x30: # version
            put('ax',0x0005); put('bx',0); put('cx',0); carry(False)
        elif ah==0x4A: # already shrunk PSP block; explicit free arena begins beyond it
            carry(False)
        elif ah==0x35: # vectors initially null
            sg,off=vectors.get(al,(0,0)); put('es',sg); put('bx',off); carry(False)
        elif ah==0x25:
            vectors[al]=(get('ds'),get('dx')); carry(False)
        elif ah==0x44 and al==0: # standard handles are redirected files
            put('dx',0); carry(False)
        elif ah==0x3D: # deterministic no-EMS device profile
            a=get('ds')*16+get('dx')
            path=bytes(machine.mem_read(a,128)).split(b'\x00',1)[0]
            entry['filename']=path.decode('ascii',errors='replace')
            if path.upper()==b'EMMXXXX0':
                put('ax',2); carry(True)
            else:
                trace['stop_reason']='unmodeled file open '+entry['filename']
                machine.emu_stop()
        elif ah==0x48:
            request=get('bx')
            if request>free_paras:
                put('ax',8); put('bx',free_paras); carry(True)
            else:
                put('ax',free_start); free_start+=request+1
                free_paras-=request+1; carry(False)
        elif ah==0x2A:
            put('cx',1991); put('dx',(12<<8)|6); put('ax',5); carry(False)
        elif ah==0x2C:
            put('cx',0); put('dx',0); carry(False)
        elif ah==0x4C:
            trace['stop_reason']=f'DOS exit {al}'; machine.emu_stop()
        else:
            trace['stop_reason']=f'unmodeled DOS service {ax:04x}'
            machine.emu_stop()
        entry['out_ax']=get('ax'); entry['carry']=bool(get('eflags')&1)
        dos.append(entry)
    machine.hook_add(uc.UC_HOOK_MEM_WRITE,on_write)
    machine.hook_add(uc.UC_HOOK_CODE,on_code)
    machine.hook_add(uc.UC_HOOK_INTR,on_intr)
    error=None
    try:
        machine.emu_start(base+ENTRY_LINEAR,0x110000,count=210000)
    except uc.UcError as e:
        error=str(e)
    final={k:bytes(machine.mem_read(a,n)).hex() for k,(a,n) in watch.items()}
    return {'load_segment':loadseg,'environment':env_text.decode('ascii'),
        'trace':trace,'error':error,'dos_boundaries':dos,
        'initial':initial,'final':final,'watched_writes':writes,
        'stop_registers':{r:get(r) for r in REG},
        'candidate_unchanged':initial['candidate_fheap']==final['candidate_fheap']}

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out',type=Path,required=True,help='Fresh output directory under this workspace build/')
args=parser.parse_args()
OUT=modctx.under_build(args.out if args.out.is_absolute() else ROOT/args.out)
OUT.mkdir(parents=True,exist_ok=False)
runs=[run(seg,env) for seg,env in [(0x1000,b'PATH=C:\\'),(0x1800,b'PATH=C:\\;TEMP=C:\\TMP')]]
receipt={'scope':'bounded original CRT-entry to main; modeled DOS services, not full DOS execution or all-input write exclusion',
    'oracle_sha256':x.sha256,'unicorn_version':uc.__version__,
    'inputs':INPUTS,'runtime_code_members':RUNTIME_PINS,
    'script':pin(Path(__file__)),
    'entry_metadata':{'crt_entry':{'seg':ENTRY_SEG,'off':ENTRY_OFF,'linear':ENTRY_LINEAR},
        'main':{'seg':MAIN_SEG,'off':MAIN_OFF,'linear':MAIN_LINEAR},
        'game_malloc':{'seg':ALLOC_SEG,'off':ALLOC_OFF,'linear':ALLOC_LINEAR}},
    'standard_load_relocations_applied_only_in_emulator':True,'runs':runs}
(OUT/'startup-trace.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps([{'load_segment':r['load_segment'],'trace':r['trace'],'error':r['error'],
    'writes':{k:len(v) for k,v in r['watched_writes'].items()},
    'candidate_unchanged':r['candidate_unchanged'],'stop_registers':r['stop_registers']}
    for r in runs],indent=2))
if not all(r['trace']['reached_main'] and r['candidate_unchanged'] and not r['error'] and
           r['trace']['reached_game_allocator']==2 and not r['trace']['reached_msc_fheap_helpers'] and
           len(r['watched_writes']['amblksiz_positive'])==4 and
           len(r['watched_writes']['nheap_desc_positive'])==5 and
           not r['watched_writes']['candidate_fheap'] and
           r['trace']['stop_reason']=='main entry'
           for r in runs):
    raise SystemExit('trace incomplete or watched-write control failed')
