"""Research-only binding and reference audit; original never enters a build recipe."""
from __future__ import annotations
import hashlib,json,re,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
import exe,libmatch
from omf import OmfReader
RD=OmfReader(communals=True)
def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p):
    p=Path(p);raw=p.read_bytes()
    try:s=p.relative_to(ROOT).as_posix()
    except ValueError:s=p.as_posix()
    return {'path':s,'size':len(raw),'sha256':sha(raw)}
man=json.loads((ROOT/'layout/manifest.json').read_text())
syms=json.loads((ROOT/'layout/symbols.json').read_text())
reportpath=ROOT/'build/source-only-dos/build-report.json'
build=json.loads(reportpath.read_text())
libpath=Path(man['runtime']['libraries']['llibcr.lib']['path']); lib=RD.split_library(libpath.read_bytes())
assert sha(libpath.read_bytes())==man['runtime']['libraries']['llibcr.lib']['sha256']
pubowner={p['name']:i for i,(n,b) in enumerate(lib) for p in RD.read(b,n).publics}
importers=[]
accepted={r['module_index'] for r in man['runtime']['members'] if r['library']=='llibcr.lib'}
for i,(n,b) in enumerate(lib):
    o=RD.read(b,n)
    if '__fheap' in o.externals:
        importers.append({'index':i,'member':n,'member_sha256':sha(b),'accepted_historical_code':i in accepted,
                          'publics':o.publics,'heap_live_fixups':[f for f in o.linker_fixups if f['target']=='__fheap']})
objects=[];appheap=[];apidefs=[]
api={'__fheap','__fmalloc','__ffree','__frealloc','__fexpand','__fheapchk','__fheapset','__fheapwalk','__fheapmin','__heapadd'}
for row in build['translation_units']:
    if not row.get('object'):continue
    p=Path(row['object']['path']);p=p if p.is_absolute() else ROOT/p
    assert sha(p.read_bytes())==row['object']['sha256'],p
    o=RD.read(p.read_bytes(),row['module']);objects.append({'module':row['module'],**pin(p)})
    relevant=[f for f in o.linker_fixups if f['target_kind']=='external' and f['target'] in api]
    declarations=sorted(set(o.externals)&api)
    if relevant or declarations:appheap.append({'module':row['module'],'declarations':declarations,'live_fixups':relevant})
    for pdef in o.publics:
        if pdef['name'] in api|{'_malloc','_free'}:apidefs.append({'module':row['module'],**pdef})

x=exe.load();sec=x.sections[27];units={u:x.unit_bytes(u) for u in x.units()}
# Diagnostic exclusion only; these wildcard locator findings never accept source.
locator=[]
for im in importers:
    i=im['index'];o=RD.read(lib[i][1],lib[i][0])
    for sd in o.segment_defs:
        s=sd['name'];body=o.segments.get(s,b'')
        if not sd['class'].upper().endswith('CODE') or not body:continue
        mask=bytearray(len(body))
        for f in o.linker_fixups:
            if f['segment']==s:mask[f['offset']:f['offset']+f['width']]=bytes([1])*f['width']
        rx=libmatch.to_regex(body,mask)
        hits=[{'unit':u,'linear':base+m.start()} for u,(base,data) in units.items() for m in rx.finditer(data)]
        # All exported entry bodies, including the shorter __ffree block, are contrasted.
        pubs=sorted((p['offset'],p['name']) for p in o.publics if p['segment']==s)
        parts=[]
        for start,name in pubs:
            end=min([v for v,_ in pubs if v>start]+[len(body)])
            prx=libmatch.to_regex(body[start:end],mask[start:end])
            ph=[{'unit':u,'linear':base+m.start()} for u,(base,data) in units.items() for m in prx.finditer(data)]
            parts.append({'public':name,'range':[start,end],'locator_hits':ph})
        locator.append({'index':i,'member':im['member'],'segment':s,'whole_length':len(body),
                        'whole_locator_hits':hits,'exported_body_locator_results':parts})

# Independent historical symbol gives all six ctype-prefix pointer fixups a real binding.
cm=RD.read(lib[77][1],lib[77][0]); candidate=bytearray(cm.segments['_DATA'])
trap=syms['runtime']['__fptrap'];start=0x55B3*16+0x7A00
for f in cm.linker_fixups:
    assert f['segment']=='_DATA' and f['target']=='__fptrap' and f['loc']=='pointer32'
    struct.pack_into('<HH',candidate,f['offset'],trap['off']+f['displacement'],trap['seg'])
old=sec.data[start-sec.load_linear:start-sec.load_linear+30]
actual_rels=[sg*16+off-start for sg,off in sec.relocs if start<=sg*16+off<start+30]
expected_rels=[f['offset']+2 for f in cm.linker_fixups]
assert old==candidate and actual_rels==expected_rels

# The accepted output and growseg own-segment fixups independently anchor the gap's neighbors.
neighbor=[]
for i in [35,55]:
    row=next(r for r in man['runtime']['members'] if r['library']=='llibcr.lib' and r['module_index']==i)
    o=RD.read(lib[i][1],lib[i][0]);codebase=row['linear'];data_start=row['data_segments'][0]['linear']-0x55B3*16
    fx=[]
    for f in o.linker_fixups:
        if f['segment']=='_TEXT' and f['target_kind']=='segment' and f['target']=='_DATA':
            v=struct.unpack_from('<H',x.image,codebase+f['offset'])[0]
            assert v==data_start+f['displacement']
            fx.append({'code_linear':codebase+f['offset'],'source_displacement':f['displacement'],
                       'bound_word':v,'implied_data_start':v-f['displacement'],
                       'frame':f['frame'],'frame_kind':f['frame_kind']})
    neighbor.append({'index':i,'member':row['member'],'independent_whole_code_owner':row,
                     'all_data_anchor_fixups':fx,'implied_data_start':data_start})

public_anchors=[]
bound_data_names={'__fmode':0x79EE,'__iomode':0x79EE,'__cfltcvt_tab':0x7A00,
                  '__asizeC':0x7A1C,'__asizeD':0x7A1D}
for row in man['runtime']['members']:
    if row['library']!='llibcr.lib':continue
    o=RD.read(lib[row['module_index']][1],row['member'])
    for f in o.linker_fixups:
        if f['segment']!=row['segment'] or f['target_kind']!='external' or f['target'] not in bound_data_names or f['loc']!='offset16':continue
        at=row['linear']+f['offset'];bound=struct.unpack_from('<H',x.image,at)[0]
        add=int.from_bytes(bytes.fromhex(f.get('encoded_addend','0000')),'little')
        implied=(bound-f['displacement']-add)&0xffff
        assert implied==bound_data_names[f['target']],(row['member'],f,hex(bound),hex(implied))
        public_anchors.append({'code_member':row['member'],'code_member_index':row['module_index'],'code_linear':at,
                               'target':f['target'],'fixup':f,'bound_word':bound,'implied_public_offset':implied})

# Actual original startup's __myalloc call must resolve to the game's allocator,
# rather than the allocator used by the minimal CRT execution fixture.
stdrow=next(r for r in man['runtime']['members'] if r['module_index']==11 and r['library']=='llibcr.lib')
stdo=RD.read(lib[11][1],stdrow['member']);malloc_calls=[]
for f in stdo.linker_fixups:
    if f['target_kind']=='external' and f['target']=='_malloc':
        off,sg=struct.unpack_from('<HH',x.image,stdrow['linear']+f['offset'])
        malloc_calls.append({'fixup':f,'original_call_target':{'seg':sg,'off':off,'linear':sg*16+off}})
assert malloc_calls and all(c['original_call_target']['seg']==0x171C for c in malloc_calls)

priorpaths=[
 'work/source-only-dos/structural-audits-v27/dos_fheap_source_owner_v35/review-v35.md',
 'work/source-only-dos/structural-audits-v28/fheap/review-v36.md',
 'work/source-only-dos/structural-audits-v28/fheap/fheap-runtime-probe-v36.json',
 'work/source-only-dos/structural-audits-v29/fheap-selection-v37a/review-v37a.md',
 'work/source-only-dos/structural-audits-v29/fheap-selection-v37a/selection-cause-controls-v37a.json',
 'work/source-only-dos/structural-audits-v32/heap-v38/review-v38.md',
 'build/workers/dos_fdata_file_order_v39/review-v39.md',
 'build/workers/dos_fdata_file_order_v39/file-order-v39.json',
 'work/source-only-dos/structural-audits-v35/ctype-worker-receipt.md',
 'work/source-only-dos/structural-audits-v35/ctype-prefix-vm.json',
 'work/source-only-dos/structural-audits-v35/fheap-counterreview-v35.md',
 'work/source-only-dos/structural-audits-v35/original-debt-operands.json',
]
docs=[Path('C:/tools/RTLink-Plus-4.00-DiscMaster/installed/dest/READ.ME'),
      Path('C:/tools/RTLink-Plus-4.00-DiscMaster/installed/dest/RTLINK.HLP'),
      Path('C:/tools/rtlink-plus-6.10/installed/READ.ME'),Path('C:/tools/rtlink-plus-6.10/installed/RTLINK.HLP')]
report={'status':'RESEARCH_ONLY_NO_OWNER_ADMISSION','input_pins':[pin(ROOT/'layout/manifest.json'),pin(ROOT/'layout/symbols.json'),pin(reportpath),pin(libpath),pin(ROOT/'assets/SIMANT.EXE'),pin(ROOT/'tools/source_only_dos.py')],
        'previous_evidence_pins':[pin(ROOT/p) for p in priorpaths],'local_linker_documentation_pins':[pin(p) for p in docs],
        'accepted_source_object_pins':objects,'app_heap_declarations_and_live_fixups':appheap,'app_api_public_owners':apidefs,
        'pinned_heap_importer_members':importers,'heap_importer_locator_diagnostics':locator,
        'accepted_historical_runtime_heap_importer_count':sum(v['accepted_historical_code'] for v in importers),
        'neighbor_code_anchors':neighbor,'independent_neighbor_public_anchors':public_anchors,
        'original_stdalloc_game_malloc_binding':malloc_calls,
        'cmiscdat_bound_proof':{'whole_30_bytes_equal':True,
            'all_six_pointer32_fixups_bound_to_independent_runtime_public':trap,'relocation_word_offsets':actual_rels,
            'ordered_relocation_words_equal':True},
        'limits':['OMF census covers the current accepted 188-source-object graph and 90 attributed original runtime code owners.',
          'Locator absence excludes these intact pinned code spellings only; it does not accept a claim about rewritten/unregistered code, partial bodies, indirect targets or computed writes.',
          'Current app source allocator definitions differ from stock fmalloc; a real minimal CRT fixture therefore cannot stand in for application startup state.',
          'Explicit FILE ordering proves realizability and binding, not automatic archival extraction or the historical link script.']}
(OUT/'reference-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('source objects',len(objects),'app heap import rows',[(r['module'],r['declarations']) for r in appheap])
print('accepted original heap importer members',report['accepted_historical_runtime_heap_importer_count'])
print('diagnostic intact heap code hits',[(r['member'],r['whole_locator_hits'],[(p['public'],len(p['locator_hits'])) for p in r['exported_body_locator_results']]) for r in locator])
print('anchors',[(r['member'],hex(r['implied_data_start']),len(r['all_data_anchor_fixups'])) for r in neighbor])
