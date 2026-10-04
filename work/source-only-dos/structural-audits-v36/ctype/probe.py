"""Bounded whole-OMF CRT sequencing experiment. Original is comparison only.

Build inputs are MAIN.C and whole unmodified hash-pinned library members.
No application link, canonical acceptance or debt admission is performed.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
import compiler, rtlink
from omf import OmfReader

compiler.WORK = OUT / 'tool-scratch'
RD = OmfReader(communals=True)
SEQ = [35, 46, 51, 55, 77, 78]
EXTRA = [3, 257]
INDEX_NAMES = {35:'OUTPUT',46:'TXTMODE',51:'FDATA',55:'GROWSEG',77:'CMISC',78:'CTYPE',3:'FPTRAP',257:'SYSERR'}
EXPECTED_NAMES = {35:'output.asm',46:'txtmode.asm',51:'fdata.asm',55:'growseg.asm',77:'cmiscdat.asm',78:'ctype.asm',3:'crt0fp.asm',257:'syserr.c'}
SOURCE = '''#include <stdio.h>
#include <ctype.h>
#include <malloc.h>

struct HeapList {
    void far *startseg;
    void far *roverseg;
    void far *lastseg;
    unsigned segflags;
};
extern struct HeapList near _fheap;
extern int sys_nerr;

int lower_test(signed char c)
{
    return islower(c) ? 1 : 0;
}

int main(void)
{
    int i, before, after;
    unsigned saved;
    unsigned char raw[127], lower[127];
    for (i = -128; i <= -2; ++i) {
        raw[i + 128] = (_ctype + 1)[i];
        lower[i + 128] = islower(i) ? 1 : 0;
    }
    saved = _fheap.segflags;
    before = lower_test((signed char)0xdd);
    _fheap.segflags = 0;
    after = lower_test((signed char)0xdd);
    _fheap.segflags = saved;
    printf("CTYPE %04X HEAP %04X NERR %d FLAGS %u MUT %d %d\\n",
           (unsigned)_ctype, (unsigned)&_fheap, sys_nerr, saved, before, after);
    printf("RAW ");
    for (i = 0; i < 127; ++i) printf("%02X", (unsigned)raw[i]);
    printf("\\nLOWER ");
    for (i = 0; i < 127; ++i) printf("%d", (int)lower[i]);
    printf("\\n");
    return 0;
}
'''

def sha(b): return hashlib.sha256(b).hexdigest()
def pin(p):
    p = Path(p); raw=p.read_bytes()
    try: label=p.relative_to(ROOT).as_posix()
    except ValueError: label=p.as_posix()
    return {'path':label,'size':len(raw),'sha256':sha(raw)}
def load_lib():
    man=json.loads((ROOT/'layout/manifest.json').read_text())
    p=Path(man['runtime']['libraries']['llibcr.lib']['path'])
    if sha(p.read_bytes()) != man['runtime']['libraries']['llibcr.lib']['sha256']:
        raise RuntimeError('runtime pin mismatch')
    return man,p,RD.split_library(p.read_bytes())

def audit():
    man,lp,lib=load_lib()
    receipts={}
    placements={}
    for item in man['runtime']['members']+man['runtime']['data_members']:
        if item['module_index'] in SEQ:
            placements[item['module_index']]=item
    for i in SEQ+EXTRA:
        n,b=lib[i]
        assert n==EXPECTED_NAMES[i],(i,n)
        obj=RD.read(b,n)
        receipts[str(i)]={'index':i,'member':n,'member_sha256':sha(b),'whole_omf_size':len(b),
                         'segments':obj.segment_defs,'groups':obj.groups,'publics':obj.publics,
                         'externals':obj.externals,'external_scopes':obj.external_scopes,
                         'fixups':obj.linker_fixups,
                         'payload_sha256':{s:sha(v) for s,v in obj.segments.items()},
                         'manifest_admission':placements.get(i)}
        (OUT/(INDEX_NAMES[i]+'.OBJ')).write_bytes(b)
    # Ownership shape census before viewing comparison bytes.
    width14=[]
    for i,(n,b) in enumerate(lib):
        o=RD.read(b,n)
        if o.segment_lengths.get('_DATA')==14:
            width14.append({'index':i,'member':n,'publics':o.publics,'payload':o.segments['_DATA'].hex(),
                            'member_sha256':sha(b),'fixups':o.linker_fixups})
    report={'scope':'RESEARCH_COMPARISON_ONLY; unadmitted whole members; build never reads original',
            'inputs':[pin(ROOT/'README.md'),pin(ROOT/'docs/codegen-rules.md'),pin(ROOT/'docs/tu-evidence.md'),
                      pin(ROOT/'AGENTS.md'),pin(ROOT/'layout/manifest.json'),pin(ROOT/'layout/symbols.json'),
                      pin(ROOT/'layout/toolchain.json'),pin(lp),pin(Path('C:/tools/msc-6.00/STARTUP/heap.inc'))],
            'members':receipts,'14_byte_data_members':width14}
    # Research comparison is deliberately subsequent to member capture and does not write build sources.
    import exe
    x=exe.load(); section=x.sections[27]
    base=0x55B3*16
    def original(lo,size):
        at=base+lo-section.load_linear
        return section.data[at:at+size]
    hist={35:0x798C,46:0x79EE,51:0x79F0,55:0x79FE,77:0x7A00,78:0x7A1E}
    rows=[]
    for i in SEQ:
        o=RD.read(lib[i][1],lib[i][0]); b=o.segments['_DATA']; old=original(hist[i],len(b))
        f=[v for v in o.linker_fixups if v['segment']=='_DATA']
        rows.append({'index':i,'member':lib[i][0],'original_dgroup_offset':hist[i],
                     'full_length':len(b),'raw_equal_before_binding':old==b,
                     'raw_difference_offsets':[j for j,(a,c) in enumerate(zip(old,b)) if a!=c],
                     'original_payload_sha256':sha(old),'member_payload_sha256':sha(b),
                     'data_fixups':f})
    rels=[{'segment':s,'offset':o,'dgroup_offset':s*16+o-base}
          for s,o in section.relocs if 0x799F<=s*16+o-base<0x7A1E]
    report['comparison']={'oracle':pin(ROOT/'assets/SIMANT.EXE'),'oracle_lock':pin(ROOT/'layout/oracle.lock.json'),
                          'full_contribution_comparisons':rows,
                          'alignment_fill':{'at':0x79ED,'length':1,'value':original(0x79ED,1).hex(),
                                            'classification':'LINK_GENERATED_WORD_ALIGNMENT; no source owner'},
                          'prefix_relocation_words':rels,'prefix_sha256':sha(original(0x799F,127)),
                          'prefix_unrelocated_hex':original(0x799F,127).hex(),
                          'fheap_gap_hex':original(0x79F0,14).hex()}
    # Full partition from symbolic relative _ctype, no absolute source addresses.
    report['prefix_partition']=[
        {'owner':'output.asm','ctype_relative_start':-127,'size':78,'owner_relative_start':19},
        {'owner':'linker word-alignment fill','ctype_relative_start':-49,'size':1},
        {'owner':'txtmode.asm','ctype_relative_start':-48,'size':2},
        {'owner':'candidate fdata.asm','ctype_relative_start':-46,'size':14},
        {'owner':'growseg.asm','ctype_relative_start':-32,'size':2},
        {'owner':'cmiscdat.asm','ctype_relative_start':-30,'size':30},
    ]
    (OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print('AUDIT', [(r['member'],r['raw_equal_before_binding'],r['raw_difference_offsets']) for r in rows])

def compile_main():
    (OUT/'MAIN.C').write_text(SOURCE,encoding='ascii',newline='\r\n')
    r=compiler.compile_c(SOURCE,'msc600ax',['/AL','/Os','/Gs'],basename='MAIN',keep=True)
    if not r.ok: raise RuntimeError(r.log)
    (OUT/'MAIN.OBJ').write_bytes(r.obj)
    o=RD.read(r.obj,'MAIN')
    (OUT/'main-model.json').write_text(json.dumps({'source':pin(OUT/'MAIN.C'),'object':pin(OUT/'MAIN.OBJ'),
            'compiler_log':r.log,'segments':o.segment_defs,'publics':o.publics,'externals':o.externals,
            'fixups':o.linker_fixups,'profile':'msc600ax','flags':['/AL','/Os','/Gs']},indent=2)+'\n')
    print('COMPILED MAIN',len(r.obj))

def map_rows(text):
    rows=[]
    for l in text.splitlines():
        m=re.match(r'^\s*([0-9A-Fa-f]{4}):([0-9A-Fa-f]{4})\s+([0-9A-Fa-f]{4})\s+C=(\S+)\s+S=(\S+)\s+G=(\S+)\s+M=(\S+)',l)
        if m:
            rows.append({'frame':int(m[1],16),'offset':int(m[2],16),'size':int(m[3],16),
                         'class':m[4],'segment':m[5],'group':m[6],'module':m[7],'raw':l.strip()})
    return rows

def map_public(text, name):
    # Non-overlay resident maps omit the Res marker under both linkers.
    m=re.search(r'^\s*([0-9A-Fa-f]{4}):([0-9A-Fa-f]{4})\s+(?:Res\s+)?'+re.escape(name)+r'\s',text,re.M)
    return [int(m[1],16),int(m[2],16)] if m else None

def derived_data_rows(mt, raw, hdr):
    # 4.00 has no detailed contribution table. Use actual linked publics and
    # OUTPUT's three DGROUP-framed _DATA fixups, rather than expected sequence.
    pub=map_public(mt,'__ctype'); gp=pub[0]
    def linear(v):return v[0]*16+v[1]
    oo=RD.read((OUT/'OUTPUT.OBJ').read_bytes(),'output.asm')
    op=map_public(mt,'__output'); os=linear(op)-16
    fixes=[f for f in oo.linker_fixups if f['segment']=='_TEXT' and f['target_kind']=='segment' and f['target']=='_DATA']
    bindings=[struct.unpack_from('<H',raw,hdr+os+f['offset'])[0]-f['displacement'] for f in fixes]
    if not bindings or len(set(bindings))!=1:raise RuntimeError('OUTPUT whole data fixups disagree')
    sy=RD.read((OUT/'SYSERR.OBJ').read_bytes(),'syserr.c')
    syoff=next(p['offset'] for p in sy.publics if p['name']=='_sys_errlist')
    anchors={35:bindings[0],46:map_public(mt,'__fmode')[1],51:map_public(mt,'__fheap')[1],
             55:map_public(mt,'__amblksiz')[1],77:map_public(mt,'__cfltcvt_tab')[1],78:pub[1],
             257:map_public(mt,'_sys_errlist')[1]-syoff}
    rows=[]
    for i,offset in anchors.items():
        o=RD.read((OUT/(INDEX_NAMES[i]+'.OBJ')).read_bytes(),EXPECTED_NAMES[i])
        rows.append({'frame':gp,'offset':offset,'size':o.segment_lengths['_DATA'],
                     'class':'DATA','segment':'_DATA','group':'DGROUP','module':EXPECTED_NAMES[i],
                     'derived_from':'linked public at known whole-OMF PUBDEF offset' if i!=35 else
                                    'all three OUTPUT _DATA group-framed actual linked code fixups',
                     'output_binding_control_values':bindings if i==35 else None})
    return rows

PLANS={
  'sequence':['MAIN',*[INDEX_NAMES[i] for i in SEQ],'FPTRAP','SYSERR'],
  'shift_dgroup':['MAIN','SYSERR',*[INDEX_NAMES[i] for i in SEQ],'FPTRAP'],
  'wrong_data_order':['MAIN','OUTPUT','TXTMODE','CMISC','FDATA','GROWSEG','CTYPE','FPTRAP','SYSERR'],
  'shift_code_binding':['MAIN','FPTRAP',*[INDEX_NAMES[i] for i in SEQ],'SYSERR'],
}

def run_case(plan,profile, collect_only=False):
    case=OUT/'links'/plan/profile
    case.mkdir(parents=True,exist_ok=True)
    for name in PLANS[plan]:
        b=(OUT/(name+'.OBJ')).read_bytes()
        (case/(name+'.OBJ')).write_bytes(b)
    lines=['OUTPUT PROBE','MAP = PROBE S,N,A,L,V,X','NODEFLIB','FILE '+', '.join(PLANS[plan]),
           'LIBRARY LLIBCR, LIBH','VERBOSE']
    (case/'T.LNK').write_text('\n'.join(lines)+'\n',encoding='ascii',newline='\r\n')
    rc=0 if collect_only else rtlink.run_link(case,profile=profile,timeout=240)
    log=(case/'LINK.LOG').read_text(encoding='latin1'); mt=(case/'PROBE.MAP').read_text(encoding='latin1')
    diagnostics=[l for l in log.splitlines() if re.search(r'\bwarning\b|\berror\b|wrt\d{4}|undefined',l,re.I)]
    if rc or diagnostics or not (case/'PROBE.EXE').is_file():
        raise RuntimeError((plan,profile,rc,diagnostics,log[-2000:]))
    raw=(case/'PROBE.EXE').read_bytes(); hdr=struct.unpack_from('<H',raw,8)[0]*16
    rows=map_rows(mt)
    if not rows:rows=derived_data_rows(mt,raw,hdr)
    focuses=[r for r in rows if r['module'].lower() in {EXPECTED_NAMES[i].lower() for i in SEQ+EXTRA}]
    data={r['module'].lower():r for r in focuses if r['segment']=='_DATA' and r['size']}
    c=data['ctype.asm']; origin=c['frame']*16+c['offset']
    prefix=raw[hdr+origin-127:hdr+origin]
    nrel=struct.unpack_from('<H',raw,6)[0]; rt=struct.unpack_from('<H',raw,24)[0]
    rels=[struct.unpack_from('<HH',raw,rt+4*i) for i in range(nrel)]
    prefix_rels=[{'offset':off,'segment':seg,'ctype_relative':seg*16+off-origin} for off,seg in rels if origin-127<=seg*16+off<origin]
    pubs={}
    for n in ['__ctype','__fheap','__fptrap','_sys_nerr','__amblksiz']:
        pubs[n]=map_public(mt,n)
    verification=[]
    for n,r in data.items():
        i=next(i for i,v in EXPECTED_NAMES.items() if v.lower()==n)
        if i not in SEQ: continue
        o=RD.read((OUT/(INDEX_NAMES[i]+'.OBJ')).read_bytes(),n)
        placed=r['frame']*16+r['offset']; block=raw[hdr+placed:hdr+placed+r['size']]
        candidate=bytearray(o.segments['_DATA']); expected_rels=[]
        for f in [f for f in o.linker_fixups if f['segment']=='_DATA']:
            assert f['target_kind']=='external' and f['loc']=='pointer32',f
            target=map_public(mt,f['target']); assert target is not None,f
            struct.pack_into('<HH',candidate,f['offset'],target[1]+f['displacement'],target[0])
            expected_rels.append(placed+f['offset']+2)
        actual_rels=sorted(seg*16+off for off,seg in rels if placed<=seg*16+off<placed+r['size'])
        verification.append({'member':n,'full_segment_length':r['size'],'bound_whole_data_equal':block==candidate,
                             'relocation_set_equal':actual_rels==expected_rels,
                             'data_fixups_bound':len(expected_rels),'payload_sha256':sha(block)})
        if block!=candidate or actual_rels!=expected_rels:raise RuntimeError(verification[-1])
    runtime=execute(case)
    snap={'plan':plan,'profile':profile,'link_rc':rc,'diagnostics':diagnostics,'files':PLANS[plan],
          'input_objects':[pin(case/(n+'.OBJ')) for n in PLANS[plan]],
          'artifacts':[pin(case/n) for n in ['T.LNK','RTLINK.CFG','RUN.BAT','dosbox.conf','LINK.LOG','PROBE.MAP','PROBE.EXE','LLIBCR.LIB','LIBH.LIB']],
          'whole_focus_layout':focuses,'public_coordinates':pubs,'whole_data_verification':verification,
          'ctype_linear':origin,'data_offsets_relative_to_ctype':{n:r['frame']*16+r['offset']-origin for n,r in data.items()},
          'prefix_unrelocated_hex':prefix.hex(),'prefix_sha256':sha(prefix),'prefix_relocation_words':prefix_rels,
          'selected_archive_members':re.findall(r'LLIBCR\.LIB\(([^)]+)\)',log,re.I),
          'runtime':runtime,'application_link_claim':False,'original_executable_build_input':False}
    (case/'receipt.json').write_text(json.dumps(snap,indent=2)+'\n')
    print(plan,profile,'CTYPE',hex(origin),'relative',snap['data_offsets_relative_to_ctype'],'runtime',runtime['header'])

def execute(case):
    runner=compiler.toolchain()['runners']['dosbox-x']
    (case/'RRUN.BAT').write_bytes(b'@echo off\r\nPROBE.EXE > OUTPUT.TXT\r\necho done > DONE.TXT\r\nexit\r\n')
    cf=[]
    for s,vs in runner['conf'].items():
        cf+=['['+s+']']+[k+'='+v for k,v in vs.items()]
    cf+=['[autoexec]',f'mount c "{case.resolve()}"','c:','call RRUN.BAT','exit']
    p=case/'runtime.conf'; p.write_text('\n'.join(cf)+'\n')
    env=os.environ.copy();env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
    process=subprocess.run([runner['path'],'-conf',str(p),'-fastlaunch','-exit','-nomenu'],cwd=case,env=env,
            stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=90,
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    (case/'host-run.log').write_bytes(process.stdout)
    if not (case/'DONE.TXT').is_file(): raise RuntimeError('fixture did not finish')
    out=(case/'OUTPUT.TXT').read_text(encoding='latin1')
    head=re.search(r'CTYPE ([0-9A-F]{4}) HEAP ([0-9A-F]{4}) NERR (\d+) FLAGS (\d+) MUT (\d) (\d)',out)
    rh=re.search(r'RAW ([0-9A-F]{254})',out);lo=re.search(r'LOWER ([01]{127})',out)
    if not (head and rh and lo): raise RuntimeError(out)
    return {'exit_code':process.returncode,'header':head[0],'raw_hex':rh[1],'lower_bits':lo[1],
            'mut_before':int(head[5]),'mut_after':int(head[6]),
            'artifacts':[pin(case/n) for n in ['RRUN.BAT','runtime.conf','OUTPUT.TXT','DONE.TXT','host-run.log']],
            'executed_only_complete_isolated_fixture':True}

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('phase',choices=['audit','compile','run','collect']);
    a.add_argument('--plan',choices=PLANS);a.add_argument('--profile',choices=['rtlink400','rtlink610'])
    args=a.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    if args.phase=='audit':audit()
    elif args.phase=='compile':compile_main()
    else:run_case(args.plan,args.profile,args.phase=='collect')
