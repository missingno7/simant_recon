from __future__ import annotations
import ast, hashlib, json, re
from pathlib import Path

ROOT = Path.cwd()
OUT = ROOT / 'build/workers/dos_sound_record_owners_v20/source-audit.json'

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()

def jload(path: str):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))

def integer_expr(expr: str):
    # Evaluate only integer-literal expressions under a tiny allowlist.
    expr = re.sub(r'/\*.*?\*/|//.*', '', expr).strip()
    expr = re.sub(r'(?<=\w)[uUlL]+\b', '', expr)
    if not re.fullmatch(r'[\s0-9a-fA-FxX()+\-*/%<>&|^~]+', expr):
        return None
    try:
        node = ast.parse(expr, mode='eval').body
        allowed = (ast.Constant, ast.UnaryOp, ast.BinOp, ast.Add, ast.Sub, ast.Mult, ast.FloorDiv,
                   ast.Div, ast.Mod, ast.LShift, ast.RShift, ast.BitOr, ast.BitAnd, ast.BitXor,
                   ast.Invert, ast.UAdd, ast.USub, ast.Load)
        if any(not isinstance(n, allowed) for n in ast.walk(node)):
            return None
        return int(eval(compile(ast.Expression(node), '<expr>', 'eval'), {'__builtins__': {}}, {}))
    except Exception:
        return None

def split_args(text: str):
    args, start, depth, quote, esc = [], 0, 0, None, False
    for i, ch in enumerate(text):
        if quote:
            if esc: esc = False
            elif ch == '\\': esc = True
            elif ch == quote: quote = None
            continue
        if ch in "'\"": quote = ch
        elif ch == '(': depth += 1
        elif ch == ')':
            if depth == 0:
                args.append(text[start:i].strip())
                return args, i
            depth -= 1
        elif ch == ',' and depth == 0:
            args.append(text[start:i].strip()); start = i+1
    return [], None

manifest_path = 'layout/manifest.json'
manifest = jload(manifest_path)
mods = manifest['modules']
canonical = []
for module, m in mods.items():
    canonical.append({'role':'canonical_tu','module':module,'path':m['source'],'sha256':m['source_sha256']})

idx_path = 'work/source-only-dos/static-completeness/index-v1.json'
idx = jload(idx_path)
strict = []
strict_index_sources = []
strict_entry_issues = []
for name, entry in idx['entries'].items():
    entry_path = entry['path']
    if sha(ROOT / entry_path) != entry['sha256'] or (ROOT / entry_path).stat().st_size != entry['size']:
        strict_entry_issues.append({'path':entry_path,'issue':'strict entry hash/size mismatch'})
    d = jload(entry_path)
    audit_src = d.get('audit', {}).get('source') or {}
    reg_src = d.get('registered_source') or {}
    effective = audit_src if name == 'DrawBalloons' or not reg_src.get('whole_module') else reg_src
    strict.append({'role':'strict_effective','function':name,'entry':entry_path,
                   'path':effective.get('path'),'sha256':effective.get('sha256')})
    strict_index_sources.append({'path':entry_path,'sha256':entry['sha256'],'size':entry['size']})

report_path = 'build/source-only-dos/build-report.json'
report = jload(report_path)
report_sources = []
for tu in report.get('translation_units',[]):
    src=tu.get('source') or {}
    if src.get('path'):
        report_sources.append({'role':'build_report_source','module':tu.get('module'),
                               'path':src['path'].replace('\\','/'),'sha256':src.get('sha256')})

# Work over the canonical + strict graph, and include exact source files represented by the current 159-TU report.
roles = canonical + strict + report_sources
by_path = {}
for item in roles:
    p=item.get('path')
    if not p: continue
    p=p.replace('\\','/')
    by_path.setdefault(p, {'path':p,'roles':[],'expected_sha256':set()})
    by_path[p]['roles'].append({k:v for k,v in item.items() if k not in ('path','sha256')})
    if item.get('sha256'): by_path[p]['expected_sha256'].add(item['sha256'])

source_hashes=[]
source_issues=[]
line_hits=[]
call_sites=[]
all_text={}
rx_ids = re.compile(r'\b(fd_50F6_0000|fd_50F6_4A4E|fd_55B3_0A82|fd_50F6_4B8E|f_295C_0367|f_284A_0521|myBeginSoundReverse|myBeginSound|f_00DF_00E8|f_00DF_0112|soundChan)\b')
call_names = ('myBeginSound','myBeginSoundReverse','f_00DF_00E8','f_00DF_0112','f_295C_0367','f_284A_0521')
for p, meta in sorted(by_path.items()):
    fp=ROOT / p
    if not fp.is_file():
        source_issues.append({'path':p,'issue':'missing source'}); continue
    raw=fp.read_bytes()
    actual=hashlib.sha256(raw).hexdigest()
    expected=sorted(meta['expected_sha256'])
    if len(expected)>1: source_issues.append({'path':p,'issue':'conflicting expected sha256','expected':expected})
    elif expected and expected[0] != actual: source_issues.append({'path':p,'issue':'sha256 mismatch','expected':expected[0],'actual':actual})
    try: text=raw.decode('utf-8-sig')
    except UnicodeDecodeError: text=raw.decode('latin1')
    all_text[p]=text
    source_hashes.append({'path':p,'sha256':actual,'size':len(raw),'roles':meta['roles']})
    for ln,line in enumerate(text.splitlines(),1):
        if rx_ids.search(line):
            line_hits.append({'path':p,'line':ln,'text':line.strip()[:500]})
    # Match direct source-level invocations and retain first-argument expressions.
    for name in call_names:
        token=re.compile(r'\b'+re.escape(name)+r'\s*\(')
        for match in token.finditer(text):
            # Find balanced closing paren, respecting quoted strings and nested calls.
            start=match.end(); depth=1; quote=None; esc=False; end=None
            for i in range(start,len(text)):
                ch=text[i]
                if quote:
                    if esc: esc=False
                    elif ch=='\\': esc=True
                    elif ch==quote: quote=None
                    continue
                if ch in "'\"": quote=ch
                elif ch=='(': depth+=1
                elif ch==')':
                    depth-=1
                    if depth==0: end=i; break
            if end is None: continue
            # Determine line and reject declarations: function token prelude on this statement.
            line_no=text.count('\n',0,match.start())+1
            line_start=text.rfind('\n',0,match.start())+1
            prefix=text[line_start:match.start()].strip()
            stmt_prefix=prefix[-100:]
            # A preceding type/extern or function-pointer declarator marks prototype/definition, not a call site.
            if re.search(r'\b(extern|void|int|unsigned|char|long|struct|typedef)\b[^;{}]*$', stmt_prefix):
                continue
            argtext=text[start:end]
            args,_=split_args(argtext+')')
            # split_args expects its own closing char after the arg slice.
            args=[a for a in args if a!='']
            if not args: continue
            first=args[0]
            line=text.splitlines()[line_no-1].strip() if line_no <= len(text.splitlines()) else ''
            call_sites.append({'path':p,'line':line_no,'name':name,'first_arg':first,
                               'first_arg_literal_value':integer_expr(first),'line_text':line[:400]})

# Registry symbols/aliases for all claimed data-labels and the sound entry name.
symbol_path='layout/symbols.json'
symbols=jload(symbol_path)
registry={}
for group in ('code','data'):
    for name,ent in symbols.get(group,{}).items():
        if name in ('fd_50F6_0000','fd_50F6_4A4E','fd_55B3_0A82','soundChan','myBeginSound','myBeginSoundReverse','f_00DF_00E8','f_00DF_0112','f_295C_0367','f_284A_0521'):
            registry[group+':'+name]=ent
        if isinstance(ent, dict) and ent.get('alias_of') in ('fd_50F6_0000','fd_50F6_4A4E','myBeginSound','myBeginSoundReverse','f_00DF_00E8'):
            registry[group+':'+name]=ent
candidate_registry_addresses=[]
for name,ent in symbols.get('data',{}).items():
    if isinstance(ent,dict) and ent.get('seg') == 0x50F6:
        off=ent.get('off')
        if isinstance(off,int) and (0 <= off <= 0x150 or 0x4A4E <= off <= 0x4B14):
            candidate_registry_addresses.append({'name':name,'segment':ent['seg'],'offset':off,'grounding':ent.get('grounding')})
sound_alias_registry={}
for name,ent in symbols.get('code',{}).items():
    if isinstance(ent,dict) and ent.get('alias_of') in ('myBeginSound','myBeginSoundReverse'):
        sound_alias_registry[name]=ent

# Local source proof counters for the 56-entry note table and fixed song map.
data_paths=['src/data/d55B3_0064.c','src/data/d55B3_00B8.c']
data_records=[]
for p in data_paths:
    fp=ROOT/p
    data_records.append({'path':p,'sha256':sha(fp),'size':fp.stat().st_size})

# Report subset details for two symbols without inferring extent from unverified gaps.
report_hits={}
for section in ('unresolved_symbols','unresolved_data','resolved_data','symbolic_aliases','reviewed_data_aliases','reviewed_communal_aliases'):
    value=report.get(section)
    if isinstance(value,list):
        report_hits[section]=[x for x in value if any(n in json.dumps(x) for n in ('fd_50F6_0000','fd_50F6_4A4E','fd_55B3_0A82','f_00DF_00E8','f_00DF_0112','myBeginSound','myBeginSoundReverse','f_295C_0367'))]

nonliteral=[c for c in call_sites if c['first_arg_literal_value'] is None]
literals=[c['first_arg_literal_value'] for c in call_sites if c['first_arg_literal_value'] is not None]
# Distinguish the requested canonical + strict-effective graph from report-only
# material; callers in either role remain visible in the broad audit above.
effective_paths={p for p,m in by_path.items() if any(r.get('role') in ('canonical_tu','strict_effective') for r in m['roles'])}
effective_calls=[c for c in call_sites if c['path'] in effective_paths]
entry_names=('myBeginSound','myBeginSoundReverse','f_00DF_00E8','f_00DF_0112')
effective_entry_calls=[c for c in effective_calls if c['name'] in entry_names]
effective_effect_calls=[c for c in effective_calls if c['name']=='f_295C_0367']
effective_program_calls=[c for c in effective_calls if c['name']=='f_284A_0521']
entry_literals=[c['first_arg_literal_value'] for c in effective_entry_calls if c['first_arg_literal_value'] is not None]
# Address-taking and numeric-address scans are deliberately scoped and exact;
# a field-row address such as &fd_50F6_4A4E[i] is a local consumer view, not a
# base-array escape.
base_address_taking={}
for name in ('fd_50F6_0000','fd_50F6_4A4E'):
    base_address_taking[name]=[]
for p in sorted(effective_paths):
    text=all_text[p]
    for name in ('myBeginSound','myBeginSoundReverse','f_00DF_00E8','f_00DF_0112'):
        for m in re.finditer(r'&\s*'+re.escape(name)+r'\b',text):
            base_address_taking.setdefault(name,[]).append({'path':p,'line':text.count('\n',0,m.start())+1,'text':text.splitlines()[text.count('\n',0,m.start())].strip()})
    for name in ('fd_50F6_0000','fd_50F6_4A4E'):
        for m in re.finditer(r'&\s*'+re.escape(name)+r'\s*(?!\[)\b',text):
            base_address_taking[name].append({'path':p,'line':text.count('\n',0,m.start())+1,'text':text.splitlines()[text.count('\n',0,m.start())].strip()})
numeric_record_address_refs=[]
for p in sorted(effective_paths):
    for ln,line in enumerate(all_text[p].splitlines(),1):
        if re.search(r'(?i)(?:0x0*50f6\s*:\s*0x0*(?:0000|4a4e|4a4f|4a50|4a51|4a52|4a53)|0x0*(?:50f60000|50f64a4e|df00e8|df0112)\b)',line):
            numeric_record_address_refs.append({'path':p,'line':ln,'text':line.strip()})
# Close exact-address registered data labels and registered alias names. Range
# membership is reported for audit only and is never used to derive an extent.
registered_data_inside=[]
for name,ent in symbols.get('data',{}).items():
    if isinstance(ent,dict) and ent.get('seg')==0x50F6 and isinstance(ent.get('off'),int):
        off=ent['off']
        if 0 <= off < 336 or 0x4A4E <= off < 0x4A4E+198:
            registered_data_inside.append({'name':name,'segment':ent['seg'],'offset':off,'alias_of':ent.get('alias_of')})
registered_target_aliases={grp:[{'name':n,'alias_of':e.get('alias_of')} for n,e in items.items() if isinstance(e,dict) and e.get('alias_of') in ('fd_50F6_0000','fd_50F6_4A4E')]
                           for grp,items in symbols.items() if isinstance(items,dict)}
current_next_steps_sha=sha(ROOT/'docs/next-steps.md')
# These are facts transcribed from the checked source/data definitions and the
# paired no-raw context transcripts, with line/column provenance retained.
source_findings={
 'voice_extent':{'count':56,'element_size':6,'source':'src/root/m277E.c','producer':'f_277E_010A: i<0x38 copies signed int kind and 32-bit payload to every row','independent_cleanup':'src/root/m0000.c:f_0000_0429 iterates i<56 and frees each kind==1 pointer','consumer_views':['src/root/m277E.c: struct Voice { int a; long b; }','src/root/m0000.c/src/root/m2815.c/src/root/m290D.c: int + far/default-large-model data pointer','src/root/m295C.c: int + int far *'], 'original_contexts':['context-f277e-010a.txt','context-f0000-0429.txt']},
 'channel_extent_candidate':{'count':33,'element_size':6,'source':'src/root/m277E.c','producer':'f_277E_00AF resets six byte fields for i=0..32','source_setup_max':30,'source_setup_note':'all nine g_68B6 modes use source counts; mode 8 is at most base 4 + 8 MIDI + 8 percussion + 10 drum = 30','consumer_views':['src/root/m277E.c: six plain char byte fields','src/root/m295C.c: six unsigned char byte fields; sentinel scans stop at first type==0'],'original_contexts':['context-f277e-00af.txt','context-f295c-00c9.txt'], 'extent_note':'33 is the candidate capacity touched by reset; no neighboring symbol or gap arithmetic is used as proof.'},
 'voice_source_arrays':{'declared_56_row_tables':['fd_55B3_0C42','fd_55B3_0D92','fd_55B3_0EE2','fd_55B3_1032','fd_55B3_1182','fd_55B3_12D2','fd_55B3_1422','fd_55B3_1572','fd_55B3_16C2'],'passed_to_f_277E_010A':['fd_55B3_0C42','fd_55B3_0D92','fd_55B3_0EE2','fd_55B3_1032','fd_55B3_1182','fd_55B3_12D2','fd_55B3_1422','fd_55B3_1572'],'note':'fd_55B3_16C2 is also a [56] source table but has no tracked f_277E_010A call.'},
 'sound_effect_index':{'entry_call_count':len(effective_entry_calls),'entry_calls_by_name':{n:sum(c['name']==n for c in effective_entry_calls) for n in entry_names},'literal_first_argument_min':min(entry_literals,default=None),'literal_first_argument_max':max(entry_literals,default=None),'nonliteral_entry_calls':[c for c in effective_entry_calls if c['first_arg_literal_value'] is None],'wrapper':'myBeginSoundReverse forwards parameter a; its sole tracked caller is literal 32','tracked_f_295C_0367_calls':[{'path':c['path'],'line':c['line'],'first_arg':c['first_arg'],'literal':c['first_arg_literal_value']} for c in effective_effect_calls],'sfxnote_table':'src/data/d55B3_00B8.c defines fd_55B3_0A82[56]; caller passes its third field as device index; third-field values in all 56 rows are 0..54'},
 'song_bank':{'path':'src/data/d55B3_0064.c','count':14,'values':[0,25,53,3,54,35,46,50,51,48,0,12,43,52],'single_assignment':'fd_55B3_00B4=&g_0068','source_search':'bank fields have no source writes; m284A copies bank values to fd_50F6_4B8E, a different object'},
 'program_map':{'function':'f_284A_0521','only_caller':'f_284A_0537 switch case 12','reachability':'input type = (status & 0x70) >> 4, so source range 0..7 makes case 12 unreachable','writes':'fd_50F6_4B8E[chan], not either candidate array','context':'context-f284a-0537.txt'},
 'source_graph_closure':{'canonical_plus_strict_unique_paths':len(effective_paths),'entry_call_sites':len(effective_entry_calls),'entry_call_sites_by_name':{n:sum(c['name']==n for c in effective_entry_calls) for n in entry_names},'first_argument_literal_min':min(entry_literals,default=None),'first_argument_literal_max':max(entry_literals,default=None),'address_taking':base_address_taking,'numeric_candidate_address_refs':numeric_record_address_refs,'data_labels_inside_candidate_spans':registered_data_inside,'registered_target_aliases':registered_target_aliases,'registered_sound_entry_aliases':sound_alias_registry},
}
# Preserve the original next-steps hash only as a read-time observation: parent
# review confirmed that the document changed after the source audit was read.
historical_next_steps='c2036a6f6e1e367577c11b50287ab5a99be9c987ee60f61c675ac57aa3ca0bd1'
# Define observed public function reference styles.
name_ref_summary={}
for name in call_names:
    items=[x for x in line_hits if re.search(r'\b'+re.escape(name)+r'\b',x['text'])]
    name_ref_summary[name]={'matching_line_count':len(items),'paths':sorted(set(x['path'] for x in items)),
                            'line_refs':items}

out={
 'schema':'sound-record-owner-source-audit-v1',
 'scope':{'canonical_module_roles':len(canonical),'canonical_unique_paths':len(set(x['path'] for x in canonical)),
          'strict_index_entries':len(strict),'strict_unique_paths':len(set(x['path'] for x in strict)),
          'canonical_plus_strict_unique_paths':len(set(x['path'] for x in canonical+strict)),
          'report_translation_units':len(report.get('translation_units',[])),
          'distinct_source_paths_scanned':len(source_hashes),
          'source_role_count':len(roles),
          'index_schema':idx.get('schema'),'report_schema':report.get('schema'),
          'unresolved_symbols_count':len(report.get('unresolved_symbols',[])),
          'unresolved_data_count':len(report.get('unresolved_data',[])),
          'unresolved_functions_count':len(report.get('unresolved_functions',[])),
          'source_only_status':report.get('status'),'standalone_dos_executable':report.get('standalone_dos_executable'),
          'original_exe_bytes_used':report.get('original_exe_bytes_used')},
 'input_hashes':[
   {'path':manifest_path,'sha256':sha(ROOT/manifest_path)},
   {'path':idx_path,'sha256':sha(ROOT/idx_path)},
   {'path':report_path,'sha256':sha(ROOT/report_path)},
   {'path':symbol_path,'sha256':sha(ROOT/symbol_path)},
   {'path':'evidence/behavior/manifest.json','sha256':sha(ROOT/'evidence/behavior/manifest.json')},
 ] + strict_index_sources + [
   {'path':'README.md','sha256':sha(ROOT/'README.md')},
   {'path':'docs/codegen-rules.md','sha256':sha(ROOT/'docs/codegen-rules.md')},
   {'path':'docs/tu-evidence.md','sha256':sha(ROOT/'docs/tu-evidence.md')},
   {'path':'tools/context.py','sha256':sha(ROOT/'tools/context.py')},
   {'path':'tools/farbss.py','sha256':sha(ROOT/'tools/farbss.py')},
   {'path':rel(Path(__file__).resolve()),'sha256':sha(Path(__file__).resolve())},
 ] + [{'path':rel(p),'sha256':sha(p)} for p in sorted((ROOT/'build/workers/dos_sound_record_owners_v20').glob('context-*.txt'))],
 'source_hashes':source_hashes,
 'source_hash_issues':source_issues+strict_entry_issues,
 'target_refs':line_hits,
 'sound_entry_call_sites':call_sites,
 'sound_entry_call_summary':{'site_count':len(call_sites),'minimum_literal_first_arg':min((c['first_arg_literal_value'] for c in call_sites if c['name'] in ('myBeginSound','myBeginSoundReverse','f_00DF_00E8','f_00DF_0112') and c['first_arg_literal_value'] is not None),default=None),
      'maximum_literal_first_arg':max((c['first_arg_literal_value'] for c in call_sites if c['name'] in ('myBeginSound','myBeginSoundReverse','f_00DF_00E8','f_00DF_0112') and c['first_arg_literal_value'] is not None),default=None),
      'nonliteral_call_count':len(nonliteral),'nonliteral_calls':nonliteral,
      'sites_by_name':{n:sum(c['name']==n for c in call_sites) for n in call_names}},
 'sound_entry_name_refs':name_ref_summary,
 'symbol_registry_entries':registry,
 'sound_alias_registry':sound_alias_registry,
 'candidate_registry_addresses':candidate_registry_addresses,
 'data_anchor_inputs':data_records,
 'report_target_hits':report_hits,
 'caveats':['Registry symbol extents and neighboring labels are not used as proof of array extent.','Direct source identifiers, numeric candidate-address references, registered aliases, and base-array escapes are inventoried separately in source_graph_closure.','myBeginSound argument literals prove the complete canonical plus strict-effective source graph and its explicit reverse-wrapper forwarding only; they do not validate arbitrary external callers or resource indices.'],
 'root_reviewed':False,
 'admitted':False
}
out['historical_reading_observations']=[{'path':'docs/next-steps.md','sha256':historical_next_steps,'status':'historical read-time observation; document changed after source audit; not a current proof pin'}]
out['current_context_hashes']=[{'path':'docs/next-steps.md','sha256':current_next_steps_sha,'status':'current at final source-audit generation; context only, not evidence for array ownership'}]
out['source_findings']=source_findings
out['source_graph_role_counts']={'canonical_plus_strict_unique_paths':len(effective_paths),'report_only_source_paths':len(set(by_path)-effective_paths),'effective_call_sites':len(effective_calls)}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf-8')
probe_path=ROOT/'build/workers/dos_sound_record_owners_v20/msc-probe-v2/probe-result.json'
probe=json.loads(probe_path.read_text(encoding='utf-8'))
out['probe_measurement_observation']={
 'path':rel(probe_path),'sha256':sha(probe_path),'schema':probe.get('schema'),
 'root_reviewed':probe.get('root_reviewed'),'admitted':probe.get('admitted'),
 'all_required_checks_pass':probe.get('all_required_checks_pass'),
 'fixture_rows':[{'linker':x.get('linker'),'case':x.get('case'),'passed':x.get('passed'),
                  'executed':x.get('executed'),'expected_log':x.get('expected_log'),
                  'actual_log':x.get('actual_log'),'far_bss_length':(x.get('far_bss_layout') or {}).get('length'),
                  'raw_map_sha256':(x.get('far_bss_layout') or {}).get('raw_map_sha256'),
                  'expected_link_failure_for':x.get('expected_link_failure_for'),
                  'unresolved_target_diagnosed':x.get('unresolved_target_diagnosed')} for x in probe.get('fixtures',[])],
 'tool_pins':probe.get('tool_hashes_after'),'input_pins':probe.get('inputs'),
 'measurement_and_source_audits_are_separate':True
}
review_path=ROOT/'build/workers/dos_sound_record_owners_v20/review.md'
out['cross_wave_context_observations']=[{
 'topic':'pre-sound-init DB cleanup reads',
 'provenance':'parent-reported gate review; kept separate from this source-owner proof',
 'zero_initial_state':['fd_50F6_4A4E[].type sentinel','fd_50F6_0000[0..55].kind'],
 'readers':[
  {'function':'f_295C_0391','source':'src/root/m295C.c','behavior':'scans channel records until the first type==0 sentinel'},
  {'function':'f_0000_0429','source':'src/root/m0000.c','behavior':'visits all 56 Voice.kind words and frees rows whose kind==1'}
 ],
 'not_read_by_these_paths':'fd_50F6_4A4C',
 'distinction':'fd_50F6_4A4C is used as a channel setup index elsewhere; it is not this cleanup gate predicate.'
}]
out['review_only_pin']={'path':rel(review_path),'sha256':sha(review_path),'status':'review prose snapshot; does not identify or alter executed probe outputs'}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({'out':rel(OUT),'scope':out['scope'],'hash_issues':source_issues,
                  'calls':out['sound_entry_call_summary'],'effective_sound_entry_calls':source_findings['source_graph_closure'],
                  'symbol_entries':list(registry)},indent=2))
