from __future__ import annotations
import hashlib, json, re, sys
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'build/workers/dos_remaining_scalar_tail_v26'))
import audit as prior
TARGETS = {'fd_50F6_04C0': 0x04C0, 'fd_50F6_0B20': 0x0B20, 'fd_50F6_0F38': 0x0F38}
WRITE = {'write','member_write','indexed_write','read_write'}

def sha(b): return hashlib.sha256(b).hexdigest()
def pin(rel):
    p=ROOT/rel; b=p.read_bytes()
    return {'path':p.resolve().relative_to(ROOT).as_posix(),'sha256':sha(b),'size':len(b)}
def load(rel): return json.loads((ROOT/rel).read_text(encoding='utf-8'))
def norm(p): return p.replace('\\','/')
def hx(v): return f'{v:04X}'

def main():
    sources, authority=prior.source_inventory()
    pins={
      'schema':'simant-dos-readonly-words-source-pins-v32',
      'source_universe':'current SOURCE_ONLY_DOS 127 report-canonical U000-U126 plus 29 strict-effective whole modules selected by current intake/index/receipts',
      'canonical_count':authority['canonical_count'],'strict_effective_count':authority['effective_count'],
      'unique_source_paths':authority['unique_source_paths'],
      'current_intake':authority['current_intake'],'build_report':authority['build_report'],
      'strict_index':authority['strict_index'],'strict_receipts':authority['strict_receipts'],
      'canonical_source_pins':authority['canonical_source_pins'],
      'strict_effective_source_pins':authority['strict_effective_source_pins']}
    pinbytes=(json.dumps(pins,indent=2,ensure_ascii=False)+'\n').encode()
    (OUT/'source-pins-v32.json').write_bytes(pinbytes)
    symbols=load('layout/symbols.json')['data']
    intake=load('work/source-only-dos/current-intake.json')
    report=load('build/source-only-dos/build-report.json')
    decisions=load('evidence/cross_version/decisions.json')
    corr=load('evidence/cross_version/simantw_correspondence.json')

    # Exact source name/access sweep over the full currently selected 156-source graph.
    sites={n:{'declarations':[],'operations':[]} for n in TARGETS}
    control_counter_sites=[]
    numeric=[]; segment_literals=[]; api_counts={}; api_sensitive=[]
    token_re={n:re.compile(r'(?<![A-Za-z0-9_])'+re.escape(n)+r'(?![A-Za-z0-9_])',re.I) for n in TARGETS}
    offsets={hx(v) for v in TARGETS.values()}
    offset_re=re.compile(r'(?i)(?<![A-Za-z0-9_])(?:0x0*(?:4c0|b20|f38)|(?:0?4c0|0?b20|0?f38)h|1216|2848|3896)(?![A-Za-z0-9_])')
    seg_re=re.compile(r'(?i)(?:0x0*50f6|50f6h|50f6\s*:)')
    api_re=re.compile(r'(?i)\b(_?f?mem(?:cpy|move|set)|_?read|read|fread|_fread|bcopy|qmemcpy|loadgame|savegame|loadstate|savestate)\s*\(')
    # All named 50F6 symbols close enough to be possible owner/view bases.
    near_symbols={t:[(s,r) for s,r in symbols.items() if r.get('seg')==0x50F6 and isinstance(r.get('off'),int) and abs(r['off']-off)<=0x60]
                  for t,off in TARGETS.items()}
    near_names={t:{s.lower() for s,r in rows} for t,rows in near_symbols.items()}
    for src in sources:
        rel=src['path']; text=(ROOT/rel).read_text(encoding='latin1'); lines=text.splitlines()
        asm=rel.lower().endswith('.asm'); fmap=prior.function_lines(text,asm)
        for ln,raw in enumerate(lines,1):
            code=prior.mask_source_line(raw,asm)
            control_name='fd_50F6_1092'
            if re.search(r'(?<![A-Za-z0-9_])'+control_name+r'(?![A-Za-z0-9_])',code,re.I):
                control_counter_sites.append({'path':rel,'module':src.get('module'),'source_kind':src['identity_kind'],'line':ln,'function':fmap.get(ln),'access':prior.classify(raw,control_name,asm),'text':raw.strip()})
            found=[]
            for name in TARGETS:
                if token_re[name].search(code):
                    kind=prior.classify(raw,name,asm)
                    item={'path':rel,'module':src.get('module'),'source_kind':src['identity_kind'],'line':ln,'function':fmap.get(ln),'access':kind,'text':raw.strip()}
                    if kind=='declaration': item['view']=prior.extent(code)
                    (sites[name]['declarations'] if kind=='declaration' else sites[name]['operations']).append(item)
                    found.append(name)
            if offset_re.search(code): numeric.append({'path':rel,'line':ln,'text':raw.strip()})
            if asm and seg_re.search(code): segment_literals.append({'path':rel,'line':ln,'text':raw.strip()})
            for m in api_re.finditer(code):
                api=m.group(1).lower(); api_counts[api]=api_counts.get(api,0)+1
                if found or offset_re.search(code):
                    api_sensitive.append({'path':rel,'module':src.get('module'),'line':ln,'api':api,'target_name_hits':found,'text':raw.strip()})

    # Any source declaration that defines a same-segment array whose explicit declared byte view spans a target.
    declared_views=[]
    declname_re=re.compile(r'\b(?:fd_50F6_([0-9A-Fa-f]{4})|([A-Za-z_]\w*))\s*(?:\[\s*(\d+)\s*\])?')
    type_width_re=re.compile(r'\b(unsigned\s+)?(char|short|int|long|Point|Pnt)\b',re.I)
    registry_to_target={s.lower():t for t,rows in near_symbols.items() for s,r in rows}
    for src in sources:
        rel=src['path']; asm=rel.lower().endswith('.asm')
        for ln,raw in enumerate((ROOT/rel).read_text(encoding='latin1').splitlines(),1):
            code=prior.mask_source_line(raw,asm)
            if not re.search(r'\b(?:extern|static|far|near|char|short|int|long|unsigned|signed|struct|Point|Pnt)\b',code,re.I): continue
            # Name tokens first; registry offsets ensure the possible view is grounded.
            for m in declname_re.finditer(code):
                off_text,other_name,count_text=m.groups()
                name=('fd_50F6_'+off_text) if off_text else other_name
                reg=symbols.get(name)
                if not reg or reg.get('seg')!=0x50F6 or not isinstance(reg.get('off'),int): continue
                typ=type_width_re.search(code)
                if not typ: continue
                kind=typ.group(2).lower(); unit=4 if kind in ('long','point','pnt') else 1 if kind=='char' else 2
                count=int(count_text) if count_text else 1
                extent=unit*count
                ends=[t for t,o in TARGETS.items() if name.lower()!=t.lower() and count>1 and reg['off']<o+2 and o<reg['off']+extent]
                if ends:
                    declared_views.append({'path':rel,'module':src.get('module'),'line':ln,'name':name,'registered_offset':hx(reg['off']),'target_hits':ends,'type':typ.group(0),'unit_bytes':unit,'count':count,'declared_bytes':extent,'end_exclusive':hx(reg['off']+extent),'text':raw.strip()})

    # Every accepted source-owned communal extent with an exact registered 50F6 start.
    provider_spans=[]; provider_pins=[]
    for proof in intake.get('storage_provider_proofs',[]):
        srcpin=proof.get('source',{})
        if srcpin.get('path'):
            actual=pin(norm(srcpin['path']))
            if actual['sha256']!=srcpin.get('sha256') or actual['size']!=srcpin.get('size'): raise RuntimeError('provider source hash mismatch '+actual['path'])
            provider_pins.append({'module':proof.get('module'),**actual})
        objpin=proof.get('object',{})
        if objpin.get('path'):
            actual=pin(norm(objpin['path']))
            if actual['sha256']!=objpin.get('sha256') or actual['size']!=objpin.get('size'): raise RuntimeError('provider object hash mismatch '+actual['path'])
        for c in proof.get('communals',[]):
            name=c.get('name','').lstrip('_'); reg=symbols.get(name)
            if not reg or reg.get('seg')!=0x50F6 or not isinstance(reg.get('off'),int) or not isinstance(c.get('length'),int): continue
            lo=reg['off']; hi=lo+c['length']
            provider_spans.append({'module':proof.get('module'),'name':name,'start':lo,'end_exclusive':hi,'length':c['length'],'kind':c.get('kind'),'count':c.get('count'),'element_size':c.get('element_size'),'source':srcpin.get('path'),'object':objpin.get('path'),'source_sha256':srcpin.get('sha256'),'object_sha256':objpin.get('sha256')})
    provider_spans.sort(key=lambda x:(x['start'],x['name']))
    catalog_extents=[]
    catalog_extents.extend({'catalog':'current_storage_provider_proofs','module':p['module'],'name':p['name'],'start':p['start'],'end_exclusive':p['end_exclusive'],'length':p['length']} for p in provider_spans)
    provider_by={t:{'intersecting_word':[p for p in provider_spans if p['start']<off+2 and off<p['end_exclusive']],
                    'left_boundary':[p for p in provider_spans if p['end_exclusive']<=off],
                    'right_boundary':[p for p in provider_spans if p['start']>=off+2]}
                 for t,off in TARGETS.items()}
    for t,off in TARGETS.items():
        provider_by[t]['left_boundary']=sorted(provider_by[t]['left_boundary'],key=lambda p:(off-p['end_exclusive'],p['start']))[:2]
        provider_by[t]['right_boundary']=sorted(provider_by[t]['right_boundary'],key=lambda p:(p['start']-(off+2),p['start']))[:2]
    # Cross-check the other admitted owner/view catalogs carried in the current intake.
    # These are additional independent schemas; do not extend any scalar from adjacency.
    for key in ('source_owned_far_scalars','source_owned_history_arrays','source_owned_water_arrays'):
        for row in intake.get(key,[]):
            addr=row.get('historical_address'); length=row.get('length')
            if isinstance(addr,list) and len(addr)==2 and addr[0]==0x50F6 and isinstance(length,int):
                catalog_extents.append({'catalog':key,'name':row.get('name'),'start':addr[1],'end_exclusive':addr[1]+length,'length':length})
    reviewed_aliases=[]
    for row in intake.get('reviewed_data_aliases',[]):
        addr=row.get('address'); size=row.get('owner_size'); vsize=row.get('view_size'); delta=row.get('offset')
        if isinstance(addr,list) and len(addr)==2 and addr[0]==0x50F6 and all(isinstance(x,int) for x in (size,vsize,delta)):
            owner_start=addr[1]-delta
            reviewed_aliases.append({'alias':row.get('alias'),'owner':row.get('owner'),'owner_start':owner_start,'owner_end_exclusive':owner_start+size,'view_start':addr[1],'view_end_exclusive':addr[1]+vsize,'owner_size':size,'view_size':vsize,'source_anchor':row.get('source_anchor')})
            catalog_extents.append({'catalog':'reviewed_data_aliases:owner','name':row.get('owner'),'start':owner_start,'end_exclusive':owner_start+size,'length':size})
            catalog_extents.append({'catalog':'reviewed_data_aliases:view','name':row.get('alias'),'start':addr[1],'end_exclusive':addr[1]+vsize,'length':vsize})
    binding_receipts=[]; binding_extents=[]; owner_contract_pins=[]; owner_contract_summaries=[]
    for ref in intake.get('storage_owner_bindings_v26',[]):
        if not ref.get('path'): continue
        path=norm(ref['path']); actual=pin(path)
        if actual['sha256']!=ref.get('sha256') or actual['size']!=ref.get('size'):
            raise RuntimeError('storage owner binding receipt hash mismatch: '+actual['path'])
        binding_receipts.append(actual)
        doc=load(path)
        contract_ref=doc.get('runtime_contract',{})
        if contract_ref.get('path'):
            contract_path=norm(contract_ref['path']); contract_pin=pin(contract_path)
            if contract_pin['sha256']!=contract_ref.get('sha256') or contract_pin['size']!=contract_ref.get('size'):
                raise RuntimeError('storage owner runtime contract hash mismatch: '+contract_pin['path'])
            owner_contract_pins.append(contract_pin)
            contract=load(contract_path)
            if '_fd_50F6_1092' in [c.get('name') for c in contract.get('communals',[])]:
                owner_contract_summaries.append({'path':contract_pin['path'],'sha256':contract_pin['sha256'],'root_reviewed':contract.get('root_reviewed'),'admitted':contract.get('admitted'),'all_required_checks_pass':contract.get('all_required_checks_pass'),'required_cases':contract.get('required_cases'),'startup_zero_cases':[{'linker':c.get('linker'),'case':c.get('case'),'actual':c.get('actual'),'clean':c.get('clean'),'runner_exit':c.get('runner_exit')} for c in contract.get('cases',[]) if c.get('case')=='positive_typed_raw_startup_zero']})
        for provider in doc.get('providers',[]):
            for c in provider.get('communals',[]):
                name=c.get('name','').lstrip('_'); reg=symbols.get(name)
                if reg and reg.get('seg')==0x50F6 and isinstance(reg.get('off'),int) and isinstance(c.get('length'),int):
                    row={'catalog':'storage_owner_bindings_v26','module':provider.get('module'),'name':name,'start':reg['off'],'end_exclusive':reg['off']+c['length'],'length':c['length'],'receipt':actual['path']}
                    binding_extents.append(row); catalog_extents.append(row)
    admitted_extent_audit={}
    for t,off in TARGETS.items():
        hit=[e for e in catalog_extents if e['start']<off+2 and off<e['end_exclusive']]
        admitted_extent_audit[t]={'intersecting_word':hit,'catalog_entries_scanned':len(catalog_extents)}
    # Keep only the closest provider extents that bracket each physical target word.
    relevant_edges={}
    for t,off in TARGETS.items():
        relevant_edges[t]=provider_by[t]['intersecting_word']+provider_by[t]['left_boundary']+provider_by[t]['right_boundary']
    usedmods={p['module'] for rows in relevant_edges.values() for p in rows}
    relevant_proofs=[]
    for proof in intake.get('storage_provider_proofs',[]):
        if proof.get('module') not in usedmods: continue
        selected=[]
        for c in proof.get('communals',[]):
            nm=c.get('name','').lstrip('_'); reg=symbols.get(nm)
            if reg and reg.get('seg')==0x50F6 and any(p['name']==nm and p['module']==proof.get('module') for rows in relevant_edges.values() for p in rows): selected.append(c)
        if selected:
            relevant_proofs.append({'module':proof.get('module'),'status':proof.get('status'),'source':proof.get('source'),'object':proof.get('object'),'relevant_communals':selected})

    # Parse the full SaveRec source table and compute explicit physical spans using exact registered starts.
    save_path='src/S09/m35F5.c'; save_text=(ROOT/save_path).read_text(encoding='latin1')
    start=save_text.index('struct SaveRec far fd_4E4B_0000[308]'); brace=save_text.index('{',start); end=save_text.index('\n};',brace); table=save_text[brace+1:end]
    row_re=re.compile(r'\{\s*(\d+)\s*,\s*(\d+)\s*,\s*\(void\s+far\s*\*\)\s*(.*?)\s*\}',re.S)
    save_rows=[]
    for m in row_re.finditer(table):
        elem,count=int(m.group(1)),int(m.group(2)); expr=' '.join(m.group(3).split())
        ln=save_text[:brace+1].count('\n')+table[:m.start()].count('\n')+1
        row={'index':len(save_rows)+1,'line':ln,'element_bytes':elem,'count':count,'span_bytes':elem*count,'target':expr,'start':None,'end_exclusive':None,'segment':None}
        for ident in re.findall(r'[A-Za-z_]\w*',expr):
            reg=symbols.get(ident)
            if reg and isinstance(reg.get('seg'),int):
                row['segment']=reg['seg']; row['start']=reg.get('off')
                if row['start'] is not None: row['end_exclusive']=row['start']+elem*count
                break
        save_rows.append(row)
    sentinel=bool(re.search(r'(?m)^\s*\{\s*0\s*,\s*0\s*,\s*0\s*\}',table))
    if len(save_rows)!=307 or not sentinel: raise RuntimeError('SaveRec table shape unexpected')
    save_near={}; save_overlap={}
    for t,off in TARGETS.items():
        rows=[r for r in save_rows if r['segment']==0x50F6 and r['start'] is not None]
        save_overlap[t]=[r for r in rows if r['start']<off+2 and off<r['end_exclusive']]
        left=[r for r in rows if r['end_exclusive']<=off]
        right=[r for r in rows if r['start']>=off+2]
        save_near[t]=[{**r,'start':hx(r['start']),'end_exclusive':hx(r['end_exclusive'])} for r in
                      sorted(left,key=lambda r:(off-r['end_exclusive'],r['start']))[:1]+sorted(right,key=lambda r:(r['start']-(off+2),r['start']))[:1]]

    # Check whether any nearby array base escapes into a non-SaveRec call or is adjusted as a pointer.
    tracked_array_bases=['fd_50F6_04A6','fd_50F6_04C8','fd_50F6_04E6','fd_50F6_04F6',
                         'fd_50F6_0B12','SowDir','SowSave','fd_50F6_0F46']
    owner_base_escapes=[]; owner_base_arithmetic=[]
    for src in sources:
        rel=src['path']; asm=rel.lower().endswith('.asm')
        for ln,raw in enumerate((ROOT/rel).read_text(encoding='latin1').splitlines(),1):
            code=prior.mask_source_line(raw,asm)
            for name in tracked_array_bases:
                if not re.search(r'(?<![A-Za-z0-9_])'+re.escape(name)+r'(?![A-Za-z0-9_])',code,re.I): continue
                if re.search(r'(?<!&)&(?!&)\s*'+re.escape(name)+r'\b',code) and not (rel==save_path and 900<=ln<=1200):
                    owner_base_escapes.append({'path':rel,'line':ln,'name':name,'text':raw.strip()})
                if re.search(r'\b'+re.escape(name)+r'\s*[+-]\s*(?:\d+|0x[0-9a-f]+|[A-Za-z_]\w*)',code,re.I):
                    owner_base_arithmetic.append({'path':rel,'line':ln,'name':name,'text':raw.strip()})

    # Symbols/views around each address; exact offset aliases and signed/typed source declarations.
    symbol_records={}
    for t,off in TARGETS.items():
        symbol_records[t]={
          'exact_registered_names':[{'name':n,'alias_of':r.get('alias_of'),'grounding':r.get('grounding')} for n,r in symbols.items() if r.get('seg')==0x50F6 and r.get('off')==off],
          'nearby_registered_names':[{'name':n,'offset':hx(r['off']),'alias_of':r.get('alias_of'),'grounding':r.get('grounding')} for n,r in symbols.items() if r.get('seg')==0x50F6 and isinstance(r.get('off'),int) and abs(r['off']-off)<=0x30]}

    # Source-shaped neighboring arrays are audited where their extents touch the target vicinity.
    array_bounds_review={
      'fd_50F6_04C0':[
        {'owner':'fd_50F6_04A6','span':'[04A6,04BE)','shape':'6 far pointers, 4 bytes each','writer':'AddMsgBalloon stores index fd_50F6_1092 only after `if (fd_50F6_1092 >= 6) return`; index 6 would overlap 04C0 but this write is guarded out. Negative index is excluded by the separately admitted zero-filled counter owner plus its only transitions (reset to 0; guarded increment).','reader':'DrawBalloons loops to fd_1092, so its maximum index is 5 under that same proven counter invariant.','sources':[pin('work/source-only-dos/providers/balloon-buffer-tables.c'),pin('src/root/m0250.c')],'source_lines':[1762,1770,1966,1967,1974]},
        {'owner':'fd_50F6_04C8','span':'[04C8,04E0)','shape':'6 Pnt objects, 4 bytes each','writer':'Same AddMsgBalloon counter bound; indices are 0..5. Index 6 begins at 04E0, after this owner and not across 04C0.','sources':[pin('work/source-only-dos/providers/balloon-buffer-tables.c'),pin('src/root/m0250.c')],'source_lines':[1762,1766,1767]},
        {'owner':'fd_50F6_04E6','span':'[04E6,04F2)','shape':'6 signed-int words','writer':'AddMsgBalloon shares the same counter. An index -19 would address [04C0,04C2); zero-start plus reset/guarded increment excludes negative indices.','sources':[pin('work/source-only-dos/providers/balloon-buffer-tables.c'),pin('src/root/m0250.c')],'source_lines':[1762,1769,1771]},
        {'owner':'fd_50F6_04F6','span':'[04F6,0502)','shape':'6 signed-int words','writer':'AddMsgBalloon shares the same counter. An index -27 would address [04C0,04C2); zero-start plus reset/guarded increment excludes negative indices.','sources':[pin('work/source-only-dos/providers/balloon-buffer-tables.c'),pin('src/root/m0250.c')],'source_lines':[1762,1768,1771]},
      ],
      'fd_50F6_0B20':[
        {'owner':'fd_50F6_0B12','span':'[0B12,0B1E)','shape':'6 signed-int words','writer':'TallyModePop writes exactly constant indices 0..5. The next element starts at 0B1E and ends exactly at 0B20; reaching the target requires index 7, which is not used. Other indexed source reads use i<3 or fixed index 5.','sources':[pin('work/source-only-dos/providers/mode-population-vectors.c'),pin('src/root/m0894.c'),pin('src/root/m1383.c')],'source_lines':[251,253,258,188,194]},
      ],
      'fd_50F6_0F38':[
        {'owner':'SowDir','span':'[0F1A,0F20)','shape':'3 signed-int words','writer':'Sow routines index the three slots with i in their three-element iteration; extent ends 18 bytes before target.','sources':[pin('src/root/m0AD9.c')],'source_lines':[80,85,104]},
        {'owner':'SowSave','span':'[0F28,0F2E)','shape':'3 signed-int words','writer':'Sow routines index three slots; extent ends 10 bytes before target. No address-taking or copy base reaches 0F38.','sources':[pin('src/root/m0AD9.c')],'source_lines':[80,86,115,116]},
        {'owner':'fd_50F6_0F46','span':'[0F46,0F78)','shape':'50 signed-byte slots','writer':'DrawSwarm initializes i=0; before any indexed operation it breaks on i>=16 or fd_50F6_07C8<=i, so the accesses are nonnegative and at most index 15. This owner starts 14 bytes after the target and cannot reach backward to 0F38.','sources':[pin('work/source-only-dos/providers/swarm-serialized-buffers.c'),pin('src/S13/m384C.c')],'source_lines':[643,650,651,653,654,657,658]}
      ]
    }

    unresolved={}
    for row in report.get('unresolved_symbols',[]):
        name=row.get('name','').lstrip('_')
        if name in TARGETS: unresolved[name]=row
    if set(unresolved)!=set(TARGETS): raise RuntimeError('unresolved rows changed')

    # Address constants only; no byte content is read and no raw context option is requested.
    contexts=[]
    for fn,file in [('main','build/workers/dos_readonly_words_v32/context-main.txt'),('o06_35F5_020C','build/workers/dos_readonly_words_v32/context-simrain.txt'),('f_004A_008A','build/workers/dos_readonly_words_v32/context-map-bound.txt')]:
        actual=pin(file); contexts.append({'function':fn,'artifact':actual,'target_mentions':[line.strip() for line in (ROOT/file).read_text(encoding='latin1').splitlines() if re.search(r'(?i)(?:0x0*4c0|0x0*b20|0x0*f38)',line)]})

    # Any numeric data-address constants and all data/address name sites are summarized, not interpreted as backing bytes.
    target_rows={}
    for t,off in TARGETS.items():
        ops=sites[t]['operations']; writes=[r for r in ops if r['access'] in WRITE]
        target_rows[t]={
          'address':f'50F6:{hx(off)}','target_interval':f'[{hx(off)},{hx(off+2)})','registered_symbol':symbols.get(t),
          'declarations':sites[t]['declarations'],'source_view_summary':sorted({json.dumps(r.get('view'),sort_keys=True) for r in sites[t]['declarations']}),
          'direct_operations':ops,'direct_reads':len(ops)-len(writes),'direct_writes':writes,
          'direct_address_escapes':[r for r in ops if r['access'] in ('address_escape','SaveRec_address')],
          'explicit_array_views_covering_target': [r for r in declared_views if t in r['target_hits']],
          'interpretation':'The selected graph contains named reads of this signed-int extern; no named source write or explicit target-address escape is present. This alone does not prove read-only lifetime, initialization, or backing ownership.'}

    # Numeric rows may be false positives, so preserve context and mark interpretation deliberately limited.
    numeric_segment_pairs=[r for r in numeric if re.search(r'(?i)(?:50f6|es\s*:\s*|seg)',r['text'])]
    result={
      'schema':'simant-dos-readonly-words-source-audit-v32','status':'READONLY_STORAGE_LINEAGE_AUDIT_COMPLETE_ROOT_REVIEW_PENDING','root_reviewed':False,
      'conclusion':'None of the three requested physical words intersects an accepted current source-owned provider extent, current owner/view catalog extent, or explicit SaveRec span. The full 156-source scan provides signed-int named reads and no named writes/address escapes; bounded neighboring arrays and bulk-load spans do not reach any target. This does not establish BSS-zero or a wider source-owned object. All three imports remain unresolved; no zero-initialized scalar, padding, alias, or owner is inferred.',
      'scope':{'source_universe':pins['source_universe'],'source_count':authority['unique_source_paths'],'canonical_count':authority['canonical_count'],'strict_effective_count':authority['effective_count'],'strict_status_counts':authority['strict_status_counts'],'source_pins_file':{'path':'build/workers/dos_readonly_words_v32/source-pins-v32.json','sha256':sha(pinbytes),'size':len(pinbytes)},'source_files_read_only':True,'production_canonical_admission_and_Git_untouched':True,'original_byte_arrays_or_fallback_used':False,'raw_data_or_byte_matching':False,'runtime_or_game_run':False,'context_py_use':'default symbolic non-raw context output; no --raw option','authority':{'current_intake':authority['current_intake'],'build_report':authority['build_report'],'strict_index':authority['strict_index'],'strict_receipts':authority['strict_receipts'],'current_status':intake.get('status'),'standalone_dos_executable':intake.get('standalone_dos_executable'),'runnable':intake.get('runnable')}},
      'targets':target_rows,
      'provider_extent_audit':{'proof_count':len(intake.get('storage_provider_proofs',[])),'registered_50f6_extent_count':len(provider_spans),'provider_span_census_sha256':sha(json.dumps(provider_spans,sort_keys=True,separators=(',',':')).encode('utf-8')),'intersecting_target_words':{t:provider_by[t]['intersecting_word'] for t in TARGETS},'nearest_provider_boundaries_by_target':{t:{side:[{**p,'start':hx(p['start']),'end_exclusive':hx(p['end_exclusive']),'distance_bytes':(off-p['end_exclusive'] if side=='left_boundary' else p['start']-(off+2))} for p in provider_by[t][side]] for side in ('left_boundary','right_boundary')} for t,off in TARGETS.items()},'admitted_owner_view_catalog_audit':{'combined_extent_count':len(catalog_extents),'catalog_extent_census_sha256':sha(json.dumps(catalog_extents,sort_keys=True,separators=(',',':')).encode('utf-8')),'intersections_by_target':admitted_extent_audit,'reviewed_data_aliases_in_50f6_count':len(reviewed_aliases),'reviewed_data_aliases_in_50f6':reviewed_aliases,'storage_owner_binding_receipt_pins':binding_receipts,'binding_communal_extent_count':len(binding_extents),'binding_runtime_contract_pins':owner_contract_pins},'relevant_provider_proofs':relevant_proofs,'interpretation':'The full current intake provider extent list, source-owned scalar/history/water extent catalogs, reviewed 50F6 alias geometry, and pinned v26 owner-binding receipt providers were checked as physical half-open spans against each two-byte word. No accepted extent intersects. Nearest boundaries are evidence of separate extents, not padding.'},
      'save_record_audit':{'source':pin(save_path),'declaration':'fd_4E4B_0000[308]','payload_rows':len(save_rows),'sentinel_present':sentinel,'loadgame_surface':'LoadGame iterates these rows and reads exactly p->count*p->size bytes into p->data; the parser resolves symbolic targets through exact registered starts. Intersections are checked against the full two-byte target word.','overlapping_rows_by_target':save_overlap,'nearest_bracketing_50f6_rows':save_near,'interpretation':'No explicit SaveRec row intersects any target word. This closes the known SaveRec bulk read/write surface only.'},
      'source_graph_scans':{'target_site_counts':{t:{'declarations':len(sites[t]['declarations']),'operations':len(sites[t]['operations']),'direct_writes':sum(x['access'] in WRITE for x in sites[t]['operations']),'address_escapes':sum(x['access'] in ('address_escape','SaveRec_address') for x in sites[t]['operations'])} for t in TARGETS},'explicit_larger_typed_views_covering_targets':declared_views,'numeric_offset_rows':numeric,'numeric_rows_with_segment_or_ES_context':numeric_segment_pairs,'asm_50F6_segment_literal_rows':segment_literals,'registered_symbols_near_targets':symbol_records,'pointer_or_bulk_api_call_counts':dict(sorted(api_counts.items())),'pointer_or_bulk_api_direct_target_argument_hits':api_sensitive,'nearby_array_owner_base_escape_scan':{'tracked_array_bases':tracked_array_bases,'non_SaveRec_address_escapes':owner_base_escapes,'explicit_base_plus_minus_arithmetic':owner_base_arithmetic},'nearby_array_write_boundary_review':array_bounds_review,'counter_range_evidence_for_balloon_arrays':{'counter':'fd_50F6_1092','address':'50F6:1092','whole_graph_sites':control_counter_sites,'write_sites':[x for x in control_counter_sites if x['access'] in WRITE or x['access']=='read_write'],'admitted_contracts':owner_contract_summaries,'interpretation':'The current admitted UI-state contract records both RTLink400 and RTLink610 typed/raw startup-zero fixtures as clean PASS and the current graph sites show reset-to-zero plus a guarded increment. After a zero start, the >=6 guard preserves [0,6]. This is a control-index invariant only, not evidence for any target value.'},'all_graph_source_extensions':{ext:sum(1 for s in sources if Path(s['path']).suffix.lower()==ext) for ext in sorted({Path(s['path']).suffix.lower() for s in sources})}},
      'nonraw_context_observations':contexts,
      'current_unresolved_import_rows':unresolved,
      'per_target_frontier':{
        'fd_50F6_04C0':['No current accepted provider/view extent intersects [04C0,04C2). The nearest accepted scalar ends at 04C0 and the next begins at 04C2; separate SaveRec rows end/start on those boundaries.','Four AddMsgBalloon arrays are nearby. A positive pointer-array index 6 would cross 04C0; negative Pnt/int indices -2/-19/-27 would reach the same word. Their shared counter is a separately admitted zero-start signed word with only reset-to-zero and guarded-increment writes; the >=6 guard therefore limits writes to indices 0..5. DrawBalloons reads within that count. No non-SaveRec array-base escape/arithmetic or target SaveRec span was found.','Still unresolved: identify a true source-owned backing definition or a reviewed lineage anchor. The counter proof only excludes adjacent-array writes; it does not establish the target value, owner, or zero state.'],
        'fd_50F6_0B20':['No current accepted provider/view extent intersects [0B20,0B22). The six-word mode-population array ends at 0B1E; a separate source-owned scalar and SaveRec span [0B1E,0B20) end exactly at the target.','TallyModePop writes exactly indices 0..5 of the six-word array. No other indirect writer, pointer escape, or SaveRec span covers 0B20. Named consumers only read the signed word.','Still unresolved: identify the actual source-owned backing or a genuine larger object/interior view. A read-only/zero claim still needs explicit source/CRT BSS lineage and indirect-writer closure.'],
        'fd_50F6_0F38':['No current accepted provider/view extent intersects [0F38,0F3A). The word at 0F36 occupies [0F36,0F38); DROPdir starts at 0F3A.','Adjacent arrays end at 0F2E or start at 0F46. The latter is only indexed by nonnegative DrawSwarm i bounded below 16; SaveRec writes exactly [0F46,0F78). No target pointer escape or SaveRec row covers 0F38.','Still unresolved: identify the actual source-owned backing or genuine larger source object. A read-only/zero claim still needs an exact source owner, CRT/BSS startup anchoring, and indirect-writer closure.']},
      'root_review_notes':['Independent bounded read-only scratch audit; root review pending.','No production/canonical/admission/layout/Git files changed.','No original-byte arrays, fallback, guessed initializer, generic byte matching, or game execution.']}
    out=OUT/'source-audit-v32.json'; out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    md=['# Read-only storage-lineage audit v32','','Status: `READONLY_STORAGE_LINEAGE_AUDIT_COMPLETE_ROOT_REVIEW_PENDING`; `root_reviewed: false`.','','This audit checks three unresolved 50F6 words against the current 156-source effective graph, accepted owner/view extents, source-shaped arrays, source address escapes, bulk API calls, and the complete 307-payload-row SaveRec table. Physical overlaps use each full two-byte target interval. No target owner or zero value is inferred from neighboring addresses or absent stores.','','The source graph is pinned in [source-pins-v32.json](source-pins-v32.json); detailed evidence and the per-word frontier are in [source-audit-v32.json](source-audit-v32.json).','', '| Target | Declaration | Direct reads | Direct writes | Address escapes | Provider/SaveRec word overlap |','|---|---|---:|---:|---:|---|']
    for t,off in TARGETS.items():
        row=target_rows[t];
        md.append(f"| `{t}` (`50F6:{hx(off)}`) | signed `int far` | {row['direct_reads']} | {len(row['direct_writes'])} | {len(row['direct_address_escapes'])} | none |")
    md += ['', 'All accepted provider spans, source-owned scalar/history/water lists, reviewed 50F6 alias geometry, and pinned owner-binding receipt providers were checked as half-open intervals. The 307 SaveRec payload rows were resolved to registered starts and lengths, with no target-word overlap. The nearest boundaries are [04BE,04C0)/[04C2,04C4), [0B1E,0B20), and [0F36,0F38)/[0F3A,0F3C).','', 'At 04C0, the four adjacent balloon arrays share `fd_50F6_1092`; its current admitted UI-state contract proves zero startup in RTLink400/610 fixtures, and the source only resets it to zero or increments behind the `>=6` guard. That bounds adjacent-array writes to slots 0..5 and is used only to close array-crossing paths, not to infer 04C0. The other adjacent vector writes fixed indices 0..5, and DrawSwarm indexes its post-target byte array only with nonnegative `i<16`.','', 'The bulk-call inventory has no argument naming any target or its physical offset; nearby owner bases have no non-SaveRec address escapes or explicit +/- pointer arithmetic. The symbolic non-raw contexts confirm the consumers: `main` compares 04C0, `SimRain` compares 0B20, and the map-bound helper reads 0F38. The source graph still does not establish target backing ownership or BSS-zero. All three remain unresolved.','']
    (OUT/'review-v32.md').write_text('\n'.join(md),encoding='utf-8')
    summary={'sources':len(sources),'canonical':authority['canonical_count'],'strict_effective':authority['effective_count'],'target_counts':{t:{'declarations':len(sites[t]['declarations']),'operations':len(sites[t]['operations']),'writes':sum(x['access'] in WRITE for x in sites[t]['operations']),'escapes':sum(x['access'] in ('address_escape','SaveRec_address') for x in sites[t]['operations'])} for t in TARGETS},'provider_overlaps':{t:len(provider_by[t]['intersecting_word']) for t in TARGETS},'admitted_extent_overlaps':{t:len(admitted_extent_audit[t]['intersecting_word']) for t in TARGETS},'save_rows':len(save_rows),'save_overlaps':{t:len(save_overlap[t]) for t in TARGETS},'larger_views':len(declared_views),'numeric_rows':len(numeric),'asm_literals':len(segment_literals),'api_direct_target_rows':len(api_sensitive),'pins_sha256':sha(pinbytes),'output':str(out)}
    print(json.dumps(summary,indent=2))
if __name__=='__main__': main()

