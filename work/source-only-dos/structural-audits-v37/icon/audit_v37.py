"""Bounded Handle-slot ownership review; all writes stay in this directory."""
from __future__ import annotations
import contextlib, hashlib, importlib.util, io, json, re, sys
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'tools'))
import compiler, context, exe, functions, modules, search
from omf import OmfReader
compiler.WORK = OUT/'cc'
# search.run keeps diagnostic history; redirect its output root, not any registry.
search.ROOT = OUT/'search-output'

def sha(b): return hashlib.sha256(b).hexdigest()
def pin(p, expected=None):
    p = p.resolve(); b=p.read_bytes(); h=sha(b)
    if expected and h != expected: raise ValueError('pin drift: '+str(p))
    return {'path':str(p).replace('\\','/'),'size':len(b),'sha256':h}
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p, r): p.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
def model(o):
    segs={r['name'] for r in o.segment_defs if r.get('class','').upper() not in {'DEBSYM','DEBTYP'}}
    return {'segment_lengths':{n:v for n,v in o.segment_lengths.items() if n in segs},
        'segment_sha256':{n:sha(bytes(b)) for n,b in o.segments.items() if n in segs},
        'segment_defs':[r for r in o.segment_defs if r['name'] in segs],
        'publics':[r for r in o.publics if r['segment'] in segs],
        'externals':o.externals,'external_scopes':o.external_scopes,'communals':o.communals,
        'ordered_fixups':[f for f in o.linker_fixups if f['segment'] in segs]}
def compile_owned(name,text,flags=None):
    p=OUT/(name+'.c'); p.write_text(text,encoding='ascii')
    r=compiler.compile_c(text,'msc600ax',flags or ['/AL','/Os','/Gs'],basename='UNIT')
    (OUT/(name+'.compiler.log')).write_text(r.log,encoding='utf-8')
    if not r.ok: raise RuntimeError(r.log)
    q=OUT/(name+'.obj'); q.write_bytes(r.obj)
    return r.obj, OmfReader(communals=True).read(r.obj), {'source':pin(p),'object':pin(q)}

def static_review():
    prior_path=ROOT/'build/workers/dos_icon_handle_owner_v33/receipt-v33.json'
    prior=read(prior_path); reopened=[]
    for name in ('source_census','strict_receipts_and_index','reviewed_evidence'):
        for r in prior['pins'][name]: reopened.append(pin(ROOT/r['path'],r['sha256']))
    for name in ('audit_script','review_artifact'):
        r=prior['pins'][name]; reopened.append(pin(ROOT/r['path'],r['sha256']))
    spec=importlib.util.spec_from_file_location('prior_icon_v33',ROOT/'build/workers/dos_icon_handle_owner_v33/audit_v33.py')
    old=importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
    targets=[dict(functions.get(n),extent=functions.get(n)['size']) for n in old.TARGET_FUNCS]
    original=old.original_scan(0x55632,4,targets)
    image=exe.load(); common=image.read('S27',0x50f60,0x4bd0); slot=image.read('S27',0x55632,4)
    rels=[]
    for unit in image.units():
        for seg,off in image.unit_relocs(unit):
            at=seg*16+off
            if 0x55631<=at<0x55636: rels.append({'unit':unit,'segment':seg,'offset':off})
    report_path=ROOT/'build/source-only-dos-v36/build-report.json'; report=read(report_path)
    source_refs=[]; object_refs=[]; census=[]
    wanted={'_fd_50F6_46D2','_f_208F_027F','_f_208F_02F0'}
    for row in report['translation_units']:
        sp=ROOT/row['generated_source']['path']; op=ROOT/row['object']['path']
        s=pin(sp,row['generated_source']['sha256']); o=pin(op,row['object']['sha256'])
        census.append({'module':row['module'],'source':s,'object':o})
        for i,line in enumerate(sp.read_text(encoding='latin1').splitlines(),1):
            if any(re.search(r'\b'+re.escape(n[1:])+r'\b',line) for n in wanted):
                source_refs.append({'module':row['module'],'line':i,'text':line.strip()})
        obj=OmfReader(communals=True).read(op.read_bytes())
        ext=[n for n in obj.externals if n in wanted]
        fx=[f for f in obj.linker_fixups if any(f.get(k)==n for k in ('target','frame') for n in wanted)]
        # Raw structured fixups often use names in target_datum/frame_datum.
        fx=[f for f in obj.linker_fixups if any(n in json.dumps(f) for n in wanted)]
        defs=[p for p in obj.publics+obj.communals if p.get('name') in wanted]
        if ext or fx or defs: object_refs.append({'module':row['module'],'externals':ext,'definitions':defs,'live_fixups':fx})
    corr=read(ROOT/'evidence/cross_version/simantw_correspondence.json')
    pairs=[p for p in corr['pairs'] if p['dos'] in old.TARGET_FUNCS]
    sy=read(ROOT/'layout/symbols.json')
    return {'prior_receipt':pin(prior_path),'reopened_prior_pins':reopened,
        'original_scan':original,'original_initial_state':{
            'exe':pin(ROOT/'assets/SIMANT.EXE'),'common_frame':0x50f6,'common_length':len(common),
            'common_all_zero':not any(common),'common_sha256':sha(common),'slot_length':len(slot),
            'slot_all_zero':not any(slot),'slot_sha256':sha(slot),'overlapping_relocations':rels,
            'bytes_serialized':0,'conclusion':'Loaded section-27 FAR_BSS slot is 4 zero bytes with no loader relocation; this proves startup, not permanent zero.'},
        'current_report':pin(report_path),'current_generated_object_census':census,
        'current_identifier_references':source_refs,'current_object_references':object_refs,
        'naming':{'policy':pin(ROOT/'docs/cross-version.md'),'xver_pairs_for_consumers':pairs,
            'slot_registry':sy['data']['fd_50F6_46D2'],
            'v33_win16_stub':prior['win16_readonly_crosscheck'],
            'correction':'win_DrawWinIcons is the separate DOS 21FA helper, not a paired 208F consumer. No Win16 anchor proves this slot identity or producer; address names stay.'},
        'producer_review':{'reviewed_sources':[pin(ROOT/p) for p in ('src/root/m205F.c','src/root/m1B28.c','src/root/m1A53.c','src/root/m171C.c')],
            'finding':'No direct slot assignment in the 190 generated TUs. Display setup loads cursor Handles and fonts, not this slot. DOS Handle typedef and cell operations corroborate pointer-to-far-pointer ABI only. Computed and assembly aliases remain open.'},
        'menu_cross_owner':prior['source_menu_clobber_review'],
        'root_inbound_corroboration':pin(ROOT/'work/source-only-dos/structural-audits-v33/root/root-inbound.json')}

def consumer_controls():
    m=read(ROOT/'layout/manifest.json')['modules']['root:208F']; src=(ROOT/m['source']).read_text(encoding='latin1')
    for n in ('f_208F_027F','f_208F_02F0'):
        buf=io.StringIO()
        with contextlib.redirect_stdout(buf): context.show(n,False,False)
        (OUT/('context-'+n+'.txt')).write_text(buf.getvalue(),encoding='utf-8')
    decl='extern char far * far * far fd_50F6_46D2;'
    cases={'m208F_baseline':src,
        'm208F_rawfar':src.replace(decl,'extern char far * far fd_50F6_46D2;').replace('*fd_50F6_46D2 +','fd_50F6_46D2 +'),
        'm208F_near_cell':src.replace(decl,'extern char far * near * far fd_50F6_46D2;'),
        'm208F_word_payload':src.replace(decl,'extern int far * far * far fd_50F6_46D2;'),
        'm208F_array_one':src.replace(decl,'extern char far * far * far fd_50F6_46D2[1];').replace('*fd_50F6_46D2 +','*fd_50F6_46D2[0] +')}
    result=[]; base=None
    for name,text in cases.items():
        p=OUT/(name+'.c'); p.write_text(text,encoding='ascii')
        buf=io.StringIO()
        with contextlib.redirect_stdout(buf):
            rows=[search.run(n,[p],None,None,None,{},True)[0] for n in ('f_208F_027F','f_208F_02F0')]
        (OUT/(name+'.search.log')).write_text(buf.getvalue(),encoding='utf-8')
        collected={}; check=modules.verify_module(text,m,m['claims'],collected)
        obj=collected['object']; op=OUT/(name+'.obj'); op.write_bytes(obj)
        projection=model(OmfReader(communals=True).read(obj))
        if base is None: base=projection
        result.append({'label':name,'source':pin(p),'object':pin(op),'search':rows,'whole_module_check':check,
            'full_nondebug_model':projection,'full_nondebug_equal_baseline':projection==base})
        print(name, 'search', [r['status'] for r in rows], 'whole',check['exact'],flush=True)
    return result

def provider_controls():
    sources={
        'icon-functional-provider':'char far * far * far fd_50F6_46D2;\n',
        'provider_typedef':'typedef char far * far *Handle;\nHandle far fd_50F6_46D2;\n',
        'provider_rawfar':'char far * far fd_50F6_46D2;\n',
        'provider_unsigned_long':'unsigned long far fd_50F6_46D2;\n',
        'provider_near_handle':'char far * near * far fd_50F6_46D2;\n',
        'provider_two_handles':'char far * far * far fd_50F6_46D2[2];\n',
        'provider_explicit_zero':'char far * far * far fd_50F6_46D2 = 0;\n',
        'provider_nonzero':'extern char far * far fixtureMaster;\nchar far * far * far fd_50F6_46D2 = &fixtureMaster;\n'}
    out=[]
    for name,text in sources.items():
        _,o,r=compile_owned(name,text); r['label']=name; r['full_nondebug_model']=model(o); out.append(r)
    return out

def main():
    OUT.mkdir(exist_ok=True)
    result={'schema':'dos-icon-minimum-view-review-v37','admitted':False,'parent_review_required':True,
        'inputs':[pin(ROOT/p) for p in ('README.md','docs/codegen-rules.md','docs/tu-evidence.md','layout/manifest.json','layout/toolchain.json')],
        'static':static_review(),'whole_consumer_controls':consumer_controls(),'provider_controls':provider_controls(),
        'limitations':['Only a minimum four-byte mutable pointer-to-far-pointer view is proposed; maximal historical object extent and defining TU are unknown.',
            'Startup zero does not establish a null-dereference contract, producer identity, allocation ownership, valid cell/payload lifetime, permanent zero or helper deadness.',
            'menu-table-cross-owner-layout remains unresolved; widths[11,12] and xpos[21,22] hit both pointer words. Other computed aliases are not excluded.',
            'No production source, manifest, Git, promotions or original image writes. No promote invocation.']}
    write(OUT/'audit-facts.json',result)
    print('wrote audit-facts.json')
if __name__=='__main__': main()
