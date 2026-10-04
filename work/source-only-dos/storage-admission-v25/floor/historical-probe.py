#!/usr/bin/env python3
"""Two-word source-owned FAR_BSS admission probe, isolated under this worker."""
from __future__ import annotations
import collections, hashlib, json, os, re, shutil, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'build/workers/dos_floor_task_words_v24'
RUNTIME=OUT/'runtime-v4'
FIXTURES=RUNTIME/'fixtures'
REPORT=RUNTIME/'runtime-receipt-v24.json'
PROVIDER=OUT/'providers'/'FLOORTSK.C'
MANIFEST=ROOT/'layout/manifest.json'
SYMBOLS=ROOT/'layout/symbols.json'
BUILD_REPORT=ROOT/'build/source-only-dos/build-report.json'
INTAKE=ROOT/'work/source-only-dos/compile-and-intake-v1.json'
STATIC_INDEX=ROOT/'work/source-only-dos/static-completeness/index-v1.json'
SOURCE_AUDIT=OUT/'source-audit-v24.json'
TARGETS=['DROPdir','Tindex']
ALIASES=['fd_50F6_0F3A','fd_50F6_0F18']
OWNERS=['_DROPdir','_Tindex']
ALIAS_PUBLICS=['_fd_50F6_0F3A','_fd_50F6_0F18']
PROFILE='msc600ax'; FLAGS=['/AL','/Os','/Oe','/Og','/Zi']
COMPILE_LOG_TEXT={}
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'tools'))
import compiler
import source_only_dos as dos
from omf import OmfReader

def sha(b): return hashlib.sha256(b).hexdigest()
def pin(path:Path, expected=None):
 path=path.resolve(); raw=path.read_bytes(); actual=sha(raw)
 if expected is not None and actual!=expected: raise RuntimeError('input pin drift: '+str(path))
 try: rel=path.relative_to(ROOT).as_posix()
 except ValueError: rel=str(path).replace('\\','/')
 return {'path':rel,'sha256':actual,'size':len(raw)}
def repo_path(rel): return ROOT/rel.replace('\\','/')
def source_graph():
 manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
 intake=json.loads(INTAKE.read_text(encoding='utf-8'))
 canonical=[]; manifest_rows=manifest['modules']
 if len(manifest_rows)!=127 or len(intake.get('translation_units',[]))!=127: raise RuntimeError('canonical graph changed')
 intake_by_module={r['module']:r for r in intake['translation_units']}
 for module,row in manifest_rows.items():
  rel=row['source'].replace('\\','/'); p=repo_path(rel); actual=pin(p,row['source_sha256'])
  ir=intake_by_module.get(module)
  if not ir or ir.get('source',{}).get('path','').replace('\\','/')!=rel or ir['source'].get('sha256')!=actual['sha256']:
   raise RuntimeError('manifest/intake source disagreement: '+module)
  canonical.append(actual|{'module':module,'set':'canonical_127'})
 idx=json.loads(STATIC_INDEX.read_text(encoding='utf-8'))
 if idx.get('schema')!='simant-dos-strict-static-index-v1' or len(idx.get('entries',{}))!=29: raise RuntimeError('strict index changed')
 effective=[]; strict_receipts=[]
 for function,ref in sorted(idx['entries'].items()):
  rp=repo_path(ref['path']); receipt_pin=pin(rp,ref['sha256'])
  if receipt_pin['size']!=ref['size']: raise RuntimeError('strict receipt size changed: '+function)
  strict=json.loads(rp.read_text(encoding='utf-8'))
  selected=strict.get('registered_source') or strict.get('audit',{}).get('source')
  if function=='DrawBalloons': selected=strict.get('audit',{}).get('source')
  if not selected or not selected.get('whole_module') or not selected.get('path'): raise RuntimeError('strict source not whole: '+function)
  sp=repo_path(selected['path']); source_pin=pin(sp,selected['sha256'])
  effective.append(source_pin|{'function':function,'module':selected.get('module'),'set':'effective_strict_29'})
  strict_receipts.append(receipt_pin|{'function':function,'source_path':source_pin['path'],'source_sha256':source_pin['sha256']})
 if len(effective)!=29: raise RuntimeError('effective strict source count changed')
 allrows=canonical+effective; unique={r['path'] for r in allrows}
 if len(unique)!=156: raise RuntimeError('source graph must contain 156 unique paths')
 audit=json.loads(SOURCE_AUDIT.read_text(encoding='utf-8'))
 audited={r['path']:r['sha256'] for r in audit['source_graph']}
 current={r['path']:r['sha256'] for r in allrows}
 if audited!=current: raise RuntimeError('v24 source audit graph disagrees with current graph')
 return allrows,strict_receipts

def compile_source(stem,source):
 if len(stem)>8: raise ValueError('MSC object basename exceeds 8.3')
 cp=FIXTURES/(stem+'.C'); op=FIXTURES/(stem+'.OBJ'); lp=FIXTURES/(stem+'.COMPILE.LOG')
 for p in (cp,op,lp):
  if p.exists(): raise RuntimeError('refuse overwrite: '+str(p))
 cp.parent.mkdir(parents=True,exist_ok=True); cp.write_text(source,encoding='ascii',newline='')
 r=compiler.compile_c(source,PROFILE,FLAGS,basename=stem)
 if not r.ok or not r.obj: raise RuntimeError('MSC compile failed '+stem+':\n'+r.log)
 op.write_bytes(r.obj); lp.write_bytes(r.log.encode('latin1','replace')); COMPILE_LOG_TEXT[stem]=r.log
 return cp,op,r.obj,r.log

def communal_rows(obj):
 return sorted([{'name':r['name'],'kind':r['kind'],'count':r.get('count'),'element_size':r.get('element_size'),'length':r['length']}
                for r in obj.communals],key=lambda r:r['name'])
def omf_summary(data):
 o=OmfReader(communals=True).read(data)
 return o,{'communals':communal_rows(o),'publics':o.publics,'external_count':len(o.externals),'externals':o.externals,
  'segment_names':sorted(o.segments),'segment_lengths':o.segment_lengths,'segment_data_bytes':{n:len(b) for n,b in o.segments.items()},
  'fixups':o.fixups,'groups':o.groups}
def masked_live_storage(summary):
 storage={'_DATA','CONST','_BSS','FAR_DATA','FAR_BSS'}
 data={n:sz for n,sz in summary['segment_data_bytes'].items() if n in storage and sz}
 fixups=[r for r in summary['fixups'] if r['segment'] in storage]
 code={n:sz for n,sz in summary['segment_lengths'].items() if n.endswith('_TEXT') and sz}
 return data,fixups,code

def consumer_sources():
 positive='''extern int far DROPdir;\nextern int far Tindex;\nextern int far fd_50F6_0F3A;\nextern int far fd_50F6_0F18;\nextern int far puts(char far *text);\nint main(void)\n{\n    unsigned char far *bytes;\n    if (&DROPdir != &fd_50F6_0F3A || &Tindex != &fd_50F6_0F18) { puts("FAIL_EXACT_ALIAS_BASE"); return 1; }\n    if (DROPdir != 0 || Tindex != 0) { puts("FAIL_COMMON_ZERO_STARTUP"); return 2; }\n    DROPdir = -3;\n    bytes = (unsigned char far *)&DROPdir;\n    if (DROPdir >= 0 || bytes[0] != 0xfd || bytes[1] != 0xff || fd_50F6_0F3A != -3) { puts("FAIL_DROP_SIGNED_STORE"); return 3; }\n    bytes = (unsigned char far *)&fd_50F6_0F3A;\n    bytes[0] = 0xd8; bytes[1] = 0xff;\n    if (DROPdir != -40) { puts("FAIL_DROP_RAW_SIGNED_READ"); return 4; }\n    Tindex = -300;\n    bytes = (unsigned char far *)&Tindex;\n    if (Tindex >= 0 || bytes[0] != 0xd4 || bytes[1] != 0xfe || fd_50F6_0F18 != -300) { puts("FAIL_TINDEX_SIGNED_STORE"); return 5; }\n    bytes = (unsigned char far *)&fd_50F6_0F18;\n    bytes[0] = 0xc0; bytes[1] = 0xff;\n    if (Tindex != -64) { puts("FAIL_TINDEX_RAW_SIGNED_READ"); return 6; }\n    puts("PASS_TYPED_RAW_ZERO_SIGNED");\n    return 0;\n}\n'''
 unsigned='''extern unsigned int far DROPdir;\nextern unsigned int far Tindex;\nextern unsigned int far fd_50F6_0F3A;\nextern unsigned int far fd_50F6_0F18;\nextern int far puts(char far *text);\nint main(void)\n{\n    if (&DROPdir != &fd_50F6_0F3A || &Tindex != &fd_50F6_0F18) { puts("FAIL_UNSIGNED_ALIAS_BASE"); return 1; }\n    DROPdir = -1; Tindex = -1;\n    if (DROPdir <= 32767U || Tindex <= 32767U) { puts("FAIL_UNSIGNED_CONSUMER_NOT_DISTINGUISHED"); return 2; }\n    puts("WRONG_UNSIGNED_CONSUMER_DETECTED");\n    return 0;\n}\n'''
 width='''extern long far DROPdir;\nextern long far Tindex;\nextern int far fd_50F6_0F3A;\nextern int far fd_50F6_0F18;\nextern unsigned int far ProbeUpperDrop;\nextern unsigned int far ProbeUpperIndex;\nextern int far puts(char far *text);\nint main(void)\n{\n    if ((int far *)&DROPdir != &fd_50F6_0F3A || (int far *)&Tindex != &fd_50F6_0F18) { puts("FAIL_LONG_ALIAS_BASE"); return 1; }\n    DROPdir = 0x12345678L; Tindex = 0x23455678L;\n    if (fd_50F6_0F3A != 0x5678 || fd_50F6_0F18 != 0x5678 || ProbeUpperDrop != 0x1234 || ProbeUpperIndex != 0x2345) { puts("FAIL_LONG_WIDTH_WORDS"); return 2; }\n    puts("WRONG_WIDTH_LONG_OWNER_DETECTED");\n    return 0;\n}\n'''
 initialized='''extern int far DROPdir;\nextern int far Tindex;\nextern int far fd_50F6_0F3A;\nextern int far fd_50F6_0F18;\nextern int far puts(char far *text);\nint main(void)\n{\n    if (&DROPdir != &fd_50F6_0F3A || &Tindex != &fd_50F6_0F18) { puts("FAIL_INITIALIZED_ALIAS_BASE"); return 1; }\n    if (DROPdir != 0x1234 || Tindex != -7) { puts("FAIL_INITIALIZED_VALUE"); return 2; }\n    puts("INITIALIZED_NONZERO_OWNER_DETECTED");\n    return 0;\n}\n'''
 shifted='''struct WordPair { int base; int following; };\nextern struct WordPair far DROPdir;\nextern struct WordPair far Tindex;\nextern int far fd_50F6_0F3A;\nextern int far fd_50F6_0F18;\nextern int far puts(char far *text);\nint main(void)\n{\n    volatile int far *drop_following;\n    volatile int far *tindex_following;\n    if (&DROPdir.base == &fd_50F6_0F3A || &Tindex.base == &fd_50F6_0F18) { puts(\"FAIL_SHIFTED_ALIAS_COLLAPSED_TO_BASE\"); return 1; }\n    drop_following = &DROPdir.following;\n    tindex_following = &Tindex.following;\n    if (drop_following != &fd_50F6_0F3A || tindex_following != &fd_50F6_0F18) { puts(\"FAIL_SHIFTED_ALIAS_NOT_SEPARATE_BACKING\"); return 2; }\n    if (DROPdir.base || DROPdir.following || Tindex.base || Tindex.following) { puts(\"FAIL_SHIFTED_COMMON_ZERO_STARTUP\"); return 3; }\n    DROPdir.base = 0x1234; DROPdir.following = -2;\n    fd_50F6_0F3A = -40;\n    Tindex.base = 0x2345; Tindex.following = -3;\n    fd_50F6_0F18 = -64;\n    if (DROPdir.base != 0x1234) { puts(\"FAIL_SHIFT_DROP_BASE\"); return 4; }\n    if (*drop_following != -40) { puts(\"FAIL_SHIFT_DROP_FOLLOWING\"); return 5; }\n    if (Tindex.base != 0x2345) { puts(\"FAIL_SHIFT_TINDEX_BASE\"); return 6; }\n    if (*tindex_following != -64) { puts(\"FAIL_SHIFT_TINDEX_FOLLOWING\"); return 7; }\n    puts(\"SHIFTED_ALIAS_SEPARATE_BACKING_DETECTED\");\n    return 0;\n}\n'''
 return {'typed_raw_positive':'TYPRUN', 'wrong_unsigned_consumer':'UNSRUN', 'wrong_width_consumer':'WIDRUN', 'initialized_consumer':'INIRUN', 'shifted_alias_consumer':'SHFRUN'}, {
  'typed_raw_positive':positive,'wrong_unsigned_consumer':unsigned,'wrong_width_consumer':width,
  'initialized_consumer':initialized,'shifted_alias_consumer':shifted}

def parse_public_sections(text):
 heads=list(re.finditer(r'(?im)^\s*Address\s+Publics by (Name|Value)\s*$',text))
 result={'Name':{},'Value':{}}
 for i,m in enumerate(heads):
  section=m.group(1); end=heads[i+1].start() if i+1<len(heads) else len(text)
  for line in text[m.end():end].splitlines():
   row=re.match(r'\s*([0-9A-Fa-f]+:[0-9A-Fa-f]+)\s+(?:Res|Abs)\s+(\S+)',line)
   if row: result[section][row.group(2).lower()]=row.group(1).upper()
 return result
def addr(v):
 s,o=v.split(':'); return int(s,16),int(o,16)
def relation_rows(case):
 deltas={'typed_raw_positive':0,'wrong_unsigned_consumer':0,'wrong_width_consumer':0,'initialized_consumer':0,'shifted_alias_consumer':2}[case]
 rel=[(a.lower(),o.lower(),deltas) for a,o in zip(ALIAS_PUBLICS,OWNERS)]
 if case=='wrong_width_consumer': rel += [('_probeupperdrop','_dropdir',2),('_probeupperindex','_tindex',2)]
 return rel
def required_publics(case):
 req=OWNERS+ALIAS_PUBLICS
 if case=='wrong_width_consumer': req += ['_ProbeUpperDrop','_ProbeUpperIndex']
 return [x.lower() for x in req]

def link_case(linker_name,case,consumer,owner,link_aliases,expected,libraries,linker,runner,tool_dir):
 folder=RUNTIME/linker_name/case
 if folder.exists(): raise RuntimeError('refuse overwrite case directory '+str(folder))
 folder.mkdir(parents=True)
 for path,data in [(folder/'CRT.OBJ',consumer),(folder/'OWNER.OBJ',owner)]: path.write_bytes(data)
 for lib in libraries: shutil.copyfile(lib['path'],folder/Path(lib['path']).name.upper())
 lines=['OUTPUT PROBE','MAP = PROBE S,N,A,L','NODEFLIB','LIBRARY LLIBCR, LIBH','FILE CRT','BEGINAREA','SECTION FILE OWNER','ENDAREA']+link_aliases
 (folder/'PROBE.LNK').write_bytes(('\r\n'.join(lines)+'\r\n').encode('ascii'))
 (folder/'RTLINK.CFG').write_bytes(b'SYNTAX = FREEFORMAT\r\n')
 (folder/'RUN.BAT').write_bytes((f'@echo off\r\nD:\\{linker["executable"]} @PROBE.LNK < NUL > LINK.LOG\r\nPROBE.EXE > RUN.LOG\r\n').encode('ascii'))
 config=[]
 for section,settings in runner['conf'].items():
  config.append('['+section+']'); config.extend(f'{k}={v}' for k,v in settings.items())
 config.extend(['[autoexec]',f'mount c "{folder}"',f'mount d "{tool_dir}" -ro','c:','call RUN.BAT','exit'])
 (folder/'dosbox.conf').write_text('\n'.join(config)+'\n',encoding='utf-8')
 env=os.environ.copy(); env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
 timed_out=False
 try:
  done=subprocess.run([runner['path'],'-conf',str(folder/'dosbox.conf'),'-fastlaunch','-exit','-nomenu'],cwd=folder,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=90,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
  rc=done.returncode
 except subprocess.TimeoutExpired: timed_out=True; rc=-1
 def read_bytes(n):
  p=folder/n; return p.read_bytes() if p.exists() else b''
 run_bytes=read_bytes('RUN.LOG'); link_bytes=read_bytes('LINK.LOG'); map_bytes=read_bytes('PROBE.MAP')
 run_text=run_bytes.decode('latin1'); link_text=link_bytes.decode('latin1'); map_text=map_bytes.decode('latin1')
 maps=parse_public_sections(map_text); req=required_publics(case); rels=[]
 sections={n:{'heading_present':bool(maps[n]) and bool(re.search(rf'(?im)^\s*Address\s+Publics by {n}\s*$',map_text)),'missing_required_publics':[p for p in req if p not in maps[n]]} for n in ('Name','Value')}
 allpub=all(not sections[n]['missing_required_publics'] for n in sections)
 relation_ok=True
 for alias,target,delta in relation_rows(case):
  aa=maps['Name'].get(alias); ta=maps['Name'].get(target); av=maps['Value'].get(alias); tv=maps['Value'].get(target); okay=False
  if aa and ta and av and tv:
   asg,aoff=addr(aa); tsg,toff=addr(ta); vsg,voff=addr(av); vtg,vtoff=addr(tv)
   okay=(asg==tsg and aoff==toff+delta and vsg==vtg and voff==vtoff+delta)
  relation_ok &= okay
  rels.append({'alias':alias,'target':target,'expected_offset_delta':delta,'alias_address_name_section':aa,'target_address_name_section':ta,'alias_address_value_section':av,'target_address_value_section':tv,'passed':okay})
 link_clean=(folder/'PROBE.EXE').exists() and not timed_out and not re.search(r'(?i)unresolved external|undefined symbol|link error|fatal error',link_text)
 map_clean=bool(map_text) and allpub and relation_ok
 passed=(run_text.strip()==expected and rc==0 and not timed_out and link_clean and map_clean)
 artifacts=[pin(p) for p in sorted(folder.iterdir(),key=lambda p:p.name.lower()) if p.is_file()]
 return {'linker':linker_name,'case':case,'expected_marker':expected,'actual_marker_verbatim':run_text,'actual_marker_bytes_hex':run_bytes.hex(),'expected_outcome_passed':passed,'runner_returncode':rc,'timed_out':timed_out,'exe_created':(folder/'PROBE.EXE').exists(),'link_clean':link_clean,'link_log_verbatim':link_text,'link_log_bytes_hex':link_bytes.hex(),'map_clean':map_clean,'map_public_sections':sections,'all_required_publics_in_both_sections':allpub,'required_publics':req,'alias_map_relations':rels,'artifacts':artifacts}

def main():
 if RUNTIME.exists(): raise RuntimeError('fresh runtime path already exists; refusing to overwrite')
 provider_text='int far DROPdir;\nint far Tindex;\n'
 if PROVIDER.exists() and PROVIDER.read_text(encoding='ascii')!=provider_text: raise RuntimeError('provider source content drift; refusing to overwrite')
 collisions=[p.relative_to(ROOT).as_posix() for p in (ROOT/'build').rglob('*') if p.is_file() and p.name.split('.')[0].casefold()=='floortsk' and OUT not in p.resolve().parents]
 if collisions: raise RuntimeError('basename FLOORTSK collision: '+repr(collisions))
 RUNTIME.mkdir(parents=True); FIXTURES.mkdir()
 compiler.WORK=RUNTIME/'compiler-work'
 denied=dos.install_input_guard()
 sources,strict_receipts=source_graph()
 manifest=json.loads(MANIFEST.read_text(encoding='utf-8')); symbols=json.loads(SYMBOLS.read_text(encoding='utf-8'))
 build_report=json.loads(BUILD_REPORT.read_text(encoding='utf-8'))
 alias_map=dos.identifier_aliases(symbols)
 expected_alias_map={'fd_50F6_0F3A':'DROPdir','fd_50F6_0F18':'Tindex'}
 if any(alias_map.get(a)!=o for a,o in expected_alias_map.items()): raise RuntimeError('identifier_aliases no longer maps aliases to owners')
 current_names={'_DROPdir','_Tindex','_fd_50F6_0F3A','_fd_50F6_0F18'}
 unresolved=[r for r in build_report.get('unresolved_symbols',[]) if r.get('name') in current_names]
 if {r['name'] for r in unresolved}!=current_names: raise RuntimeError('current report no longer contains all four unresolved spellings')
 data_symbols=symbols['data']
 registry_relations={a:data_symbols[a] for a in ALIASES}
 if any(data_symbols[a].get('alias_of')!=o for a,o in zip(ALIASES,TARGETS)): raise RuntimeError('registry alias relation changed')
 sound=build_report.get('sound_control_words_contract',{})
 sound_names={r.get('name','').lstrip('_') for r in sound.get('communals',[])}
 if sound_names.intersection(ALIASES+TARGETS): raise RuntimeError('target overlaps an active sound control owner')
 # Natural whole-module data-only provider. The source is only two signed scalar definitions.
 PROVIDER.parent.mkdir(parents=True,exist_ok=True)
 if not PROVIDER.exists(): PROVIDER.write_text(provider_text,encoding='ascii',newline='')
 providers={
  'natural':compile_source('FLOORTSK',provider_text),
  'wrong_width':compile_source('LONGOWR','long far DROPdir;\nlong far Tindex;\n'),
  'initialized':compile_source('INITOWR','int far DROPdir = 0x1234;\nint far Tindex = -7;\n'),
  'shifted_backing':compile_source('SHFTOWR','struct WordPair { int base; int following; };\nstruct WordPair far DROPdir;\nstruct WordPair far Tindex;\n')}
 consumer_stems,consumer_texts=consumer_sources()
 consumers={case:compile_source(consumer_stems[case],source) for case,source in consumer_texts.items()}
 natural_obj,natural_summary=omf_summary(providers['natural'][2])
 width_obj,width_summary=omf_summary(providers['wrong_width'][2])
 init_obj,init_summary=omf_summary(providers['initialized'][2])
 shift_obj,shift_summary=omf_summary(providers['shifted_backing'][2])
 expected_scalar={('_DROPdir','far',2,1,2),('_Tindex','far',2,1,2)}
 got_scalar={(r['name'],r['kind'],r['count'],r['element_size'],r['length']) for r in natural_summary['communals']}
 if got_scalar!=expected_scalar: raise RuntimeError('natural provider not exactly two scalar int COMDEF 2 x 1: '+repr(natural_summary['communals']))
 nat_data,nat_fix,nat_code=masked_live_storage(natural_summary)
 if nat_data or nat_fix or nat_code or natural_summary['publics']: raise RuntimeError('natural provider has initialized/live storage or code')
 if any(r['kind']!='far' for r in natural_summary['communals']) or len(natural_summary['communals'])!=2: raise RuntimeError('natural provider allocation count wrong')
 expected_long={('_DROPdir','far',4,1,4),('_Tindex','far',4,1,4)}
 if {(r['name'],r['kind'],r['count'],r['element_size'],r['length']) for r in width_summary['communals']}!=expected_long: raise RuntimeError('long contrast not exact 4 x 1')
 if init_summary['communals'] or {r['name'] for r in init_summary['publics']}!={'_DROPdir','_Tindex'}: raise RuntimeError('initialized owner did not replace commons with publics')
 if {(r['name'],r['kind'],r['count'],r['element_size'],r['length']) for r in shift_summary['communals']}!={('_DROPdir','far',4,1,4),('_Tindex','far',4,1,4)}: raise RuntimeError('shift test struct backing OMF extent not 4 x 1')
 expected_init_bytes={'_DROPdir':b'\x34\x12','_Tindex':b'\xf9\xff'}
 init_payloads={}
 for pub in init_obj.publics:
  if pub['name'] in expected_init_bytes:
   seg=pub['segment']; off=pub['offset']; payload=init_obj.segments.get(seg,b'')[off:off+2]
   init_payloads[pub['name']]={'segment':seg,'offset':off,'bytes_hex':payload.hex(),'expected_hex':expected_init_bytes[pub['name']].hex(),'passed':payload==expected_init_bytes[pub['name']]}
 if set(init_payloads)!=set(expected_init_bytes) or not all(r['passed'] for r in init_payloads.values()): raise RuntimeError('initialized OMF payload mismatch: '+repr(init_payloads))
 # The resolver already knows fd spelling -> named owner. Once owner COMDEF is emitted, unresolved_symbols() will define the fd spelling to it by same registry address.
 report_rows={r['name']:r for r in unresolved}
 if report_rows['_fd_50F6_0F3A']['registry'].get('alias_of')!='DROPdir' or report_rows['_fd_50F6_0F18']['registry'].get('alias_of')!='Tindex': raise RuntimeError('build report does not expose registered alias owners')
 case_names={'typed_raw_positive':'PASS_TYPED_RAW_ZERO_SIGNED','wrong_unsigned_consumer':'WRONG_UNSIGNED_CONSUMER_DETECTED','wrong_width_consumer':'WRONG_WIDTH_LONG_OWNER_DETECTED','initialized_consumer':'INITIALIZED_NONZERO_OWNER_DETECTED','shifted_alias_consumer':'SHIFTED_ALIAS_SEPARATE_BACKING_DETECTED'}
 bycase_cons={k:v[2] for k,v in consumers.items()}
 case_data=[
  ('typed_raw_positive',bycase_cons['typed_raw_positive'],providers['natural'][2],['DEFINE _fd_50F6_0F3A = _DROPdir','DEFINE _fd_50F6_0F18 = _Tindex']),
  ('wrong_unsigned_consumer',bycase_cons['wrong_unsigned_consumer'],providers['natural'][2],['DEFINE _fd_50F6_0F3A = _DROPdir','DEFINE _fd_50F6_0F18 = _Tindex']),
  ('wrong_width_consumer',bycase_cons['wrong_width_consumer'],providers['wrong_width'][2],['DEFINE _fd_50F6_0F3A = _DROPdir','DEFINE _fd_50F6_0F18 = _Tindex','DEFINE _ProbeUpperDrop = _DROPdir + 2','DEFINE _ProbeUpperIndex = _Tindex + 2']),
  ('initialized_consumer',bycase_cons['initialized_consumer'],providers['initialized'][2],['DEFINE _fd_50F6_0F3A = _DROPdir','DEFINE _fd_50F6_0F18 = _Tindex']),
  ('shifted_alias_consumer',bycase_cons['shifted_alias_consumer'],providers['shifted_backing'][2],['DEFINE _fd_50F6_0F3A = _DROPdir + 2','DEFINE _fd_50F6_0F18 = _Tindex + 2'])]
 tc=compiler.toolchain(); profile=compiler.verify_profile(PROFILE); runner=tc['runners']['dosbox-x']; msc_runner=tc['runner']
 compiler_tree=compiler.pinned_tree(profile)
 libraries=list(manifest['runtime']['libraries'].values())
 input_pins=[]
 for p in [Path(__file__),PROVIDER,MANIFEST,ROOT/'layout/toolchain.json',SYMBOLS,BUILD_REPORT,INTAKE,STATIC_INDEX,SOURCE_AUDIT,ROOT/'tools/compiler.py',ROOT/'tools/omf.py',ROOT/'tools/source_only_dos.py',ROOT/'tools/dos_source_bindings.py']:
  input_pins.append(pin(p))
 input_pins.extend(sources); input_pins.extend(strict_receipts)
 for rel,digest in profile['files'].items(): input_pins.append(pin(Path(profile['directory'])/rel,digest))
 for rel,digest in (profile.get('include_files') or {}).items():
  p=ROOT/rel[5:] if rel.startswith('repo:') else (compiler.include_root(profile)/rel)
  input_pins.append(pin(p,digest))
 input_pins.append(pin(Path(msc_runner['path']),msc_runner['sha256']))
 input_pins.append(pin(Path(runner['path']),runner['sha256']))
 for lib in libraries: input_pins.append(pin(Path(lib['path']),lib['sha256']))
 cases=[]; linker_copies={}
 for linker_name in ('rtlink400','rtlink610'):
  linker=tc['linkers'][linker_name]
  for rel,digest in linker['files'].items(): input_pins.append(pin(Path(linker['directory'])/rel,digest))
  tool_dir=compiler.pinned_tree(linker); linker_copies[linker_name]=[pin(Path(tool_dir)/rel,digest) for rel,digest in linker['files'].items()]
  case_tag={'typed_raw_positive':'typed_raw_positive','wrong_unsigned_consumer':'wrong_unsigned_consumer','wrong_width_consumer':'wrong_width_long_owner','initialized_consumer':'initialized_nonzero_owner','shifted_alias_consumer':'shifted_alias_separate_backing'}
  for case,consumer,owner,aliases in case_data:
   cases.append(link_case(linker_name,case,consumer,owner,aliases,case_names[case],libraries,linker,runner,tool_dir))
 allpass=len(cases)==10 and all(r['expected_outcome_passed'] for r in cases)
 # Preserve every produced source/object/log/map/link log/EXE with raw bytes and pins.
 artifacts=[]
 for p in [PROVIDER]: artifacts.append(pin(p))
 for folder in (FIXTURES,):
  for p in sorted(folder.iterdir(),key=lambda q:q.name.lower()):
   if p.is_file(): artifacts.append(pin(p))
 for r in cases:
  artifacts.extend(r['artifacts'])
 compiler_tool_copies=[pin(compiler_tree/rel,digest) for rel,digest in profile['files'].items()]
 for rows in linker_copies.values(): artifacts.extend(rows)
 artifacts.extend(compiler_tool_copies)
 # Preserve case outputs only once by relative path.
 uniq={r['path']:r for r in artifacts}; artifacts=list(uniq.values())
 report={'schema':'simant-source-only-dos-floor-task-runtime-proof-v24','status':'SCRATCH_ONLY_ROOT_REVIEW_PENDING','root_reviewed':False,'provider_spec':{'module':'source-owned:floor-task-words','basename':'FLOORTSK','basename_8_3_valid':True,'basename_collision_scan_build_tree':{'passed':True,'matches':[]},'production_provider_spec_registered':False,'source':pin(PROVIDER),'source_text_verbatim':provider_text,'definitions':[{'name':'DROPdir','symbol':'_DROPdir','c_type':'int far','expected_registered_address':'50F6:0F3A','expected_alias':'_fd_50F6_0F3A'},{'name':'Tindex','symbol':'_Tindex','c_type':'int far','expected_registered_address':'50F6:0F18','expected_alias':'_fd_50F6_0F18'}],'source_anchor_summary':['S18:384C floor routines write DROPdir; root:0BE8 FoodFall reads it as a direction index','S06:35F5, S22:3BBD, S25:39C7, root:0894 and root:0F3F read/write Tindex as signed ant-list cursor'],'source_graph_path_count':len(sources),'strict_receipt_count':len(strict_receipts)},'source_graph_receipt':sources,'strict_receipt_pins':strict_receipts,'source_audit_input_pin':pin(SOURCE_AUDIT),'scope':{'original_assets_used_as_build_input':0,'source_game_objects_used':0,'runtime_or_compiler_original_game_inputs':0,'source_graph_unique_paths':len({r['path'] for r in sources}),'canonical_source_count':127,'effective_strict_source_count':29,'no_address_gap_extent_inference':True,'historical_comdef_order_not_used_as_authority':True,'root_reviewed':False},'resolver_alias_audit':{'source_only_identifier_aliases':{a:alias_map[a] for a in ALIASES},'symbols_registry_alias_rows':registry_relations,'current_mutable_report_unresolved_target_rows':unresolved,'current_report_mutable_observation_pin':pin(BUILD_REPORT),'source_only_resolve_symbols_logic':'tools/source_only_dos.py::unresolved_symbols groups registry spellings at the exact (kind, unit, seg, off) start and emits an alias only when exactly one underscore/@ owner public or communal exists at that same registered address. With the two owner COMDEF names present, the existing fd->named-owner rows naturally resolve via RTLink DEFINE; no registry edit is needed.','expected_production_aliases':[{'alias':'_fd_50F6_0F3A','owner':'_DROPdir','delta':0,'registry_owner':'DROPdir'},{'alias':'_fd_50F6_0F18','owner':'_Tindex','delta':0,'registry_owner':'Tindex'}],'no_production_registry_or_tool_edits':True,'active_sound_owner_names':sorted(sound_names),'target_sound_overlap':[]},'provider_omf':{'shape':natural_summary,'communals_are_exactly_two_int_scalar_commons':True,'expected_communal_fields':'each source scalar is count=2, element_size=1, length=2','live_storage_data_bytes':nat_data,'live_storage_fixups':nat_fix,'live_code_segments':nat_code,'source_function_definitions':0,'zero_initialized_segments':True,'all_non_debug_data_empty':not bool(nat_data),'no_code_storage_fixups_or_initialized_publics':not(bool(nat_fix or nat_code or natural_summary['publics']))},'contrasts':{'unsigned_consumer':{'source':consumer_texts['wrong_unsigned_consumer'],'omf_consumer_externals':OmfReader(communals=True).read(consumers['wrong_unsigned_consumer'][2]).externals,'interpretation':'same signed int owner bytes viewed through unsigned int; runtime writes -1 and observes 65535 > 32767U; signedness is source/runtime evidence, not an OMF COMDEF property'},'wrong_width_long_owner':{'source':'long far DROPdir; long far Tindex;','omf':width_summary,'communals_exactly_four_bytes_count4_element1':True},'initialized_owner':{'source':'int far DROPdir = 0x1234; int far Tindex = -7;','omf':init_summary,'owner_initializer_bytes':init_payloads,'common_absent':not bool(init_summary['communals'])},'shifted_alias_separate_backing':{'source':'struct WordPair { int base; int following; }; struct WordPair far DROPdir; struct WordPair far Tindex;','omf':shift_summary,'communal_layout':'test-only 4-byte struct backing per owner; field following is a separately addressable int at +2 and runtime checks that alias follows it without changing base field','aliases_deliberately_at_delta':2}},'runtime':{'linkers':['rtlink400','rtlink610'],'cases':cases,'all_expected_markers_and_map_checks_pass':allpass,'runner':runner,'msc_runner':msc_runner,'pinned_linker_tool_copies':linker_copies,'map_contract':'Each case requires _DROPdir, _Tindex, _fd_50F6_0F3A and _fd_50F6_0F18 in both Address Publics by Name and Value sections. Alias addresses are checked against owner addresses at exact delta 0; width and shifted controls additionally check explicit +2 relations.','markers':'Actual RUN.LOG contents and byte hex are retained verbatim; detection-control markers count as expected PASS outcomes.','all_link_logs_clean':all(c['link_clean'] and c['map_clean'] for c in cases),'raw_logs_maps_and_omf_retained':True},'inputs':input_pins,'artifacts':artifacts,'denied_oracle_reads':denied,'limitations':['The signed-int and unsigned-int COMDEF rows have the same OMF count/element shape; signedness is established by consistent int far source views plus runtime signed stores/unsigned-consumer control.','Runtime proves clean standalone CRT startup zeroing for these natural common owners under both tested RTLinks, not historical communal allocation order or every possible external writer.','This runtime folder is source-only scratch evidence; it does not promote a canonical data owner or prove original full-object extent beyond each 2-byte source declaration.','The deliberate shifted fixture uses a test-only struct to back a distinct field at +2; it makes no claim that any neighboring production address or object exists.']}
 REPORT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
 print(json.dumps({'report':REPORT.relative_to(ROOT).as_posix(),'all_expected_outcomes_pass':allpass,'runtime_cases':len(cases),'natural_communal_shape':natural_summary['communals'],'cases':[{'linker':r['linker'],'case':r['case'],'marker':r['actual_marker_verbatim'],'passed':r['expected_outcome_passed'],'publics_both':r['all_required_publics_in_both_sections'],'relations':r['alias_map_relations']} for r in cases]},indent=2))

if __name__=='__main__': main()
