#!/usr/bin/env python3
"""Build genuine MSC object libraries and link-only RTLink selection controls."""
import hashlib,json,os,re,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
import compiler,rtlink
from omf import OmfReader
rd=OmfReader(communals=True)
compiler.WORK=OUT/'compiler-scratch'
CONTROL=OUT/'controls-v37a-final'; CONTROL.mkdir(exist_ok=False)
LIBSRC=Path(r'C:\tools\msc-6.00\BIN\LIB.EXE')
LIBSHA='418aec4161ef09084aaf2bed66e4de9e007eb6f2bedd1990b73707f624336ff3'
LIBRUN=CONTROL/'LIB.EXE'; LIBRUN.write_bytes(LIBSRC.read_bytes())
if hashlib.sha256(LIBRUN.read_bytes()).hexdigest()!=LIBSHA: raise SystemExit('librarian hash mismatch')
sources={
 'BASE':'void main(void) { }\n',
 'DONLY':'volatile int probe_data_only = 0x1234;\nint probe_common_only;\n',
 'CDMEM':'volatile int probe_cd_data = 0x5678;\nint probe_cd_fn(void) { return probe_cd_data; }\n',
 'COMMON':'int probe_common_only;\n',
 'REFDATA':'extern volatile int probe_data_only;\nvoid main(void) { if (probe_data_only == 0x1234) return; }\n',
 'REFCOM':'extern volatile int probe_common_only;\nvoid main(void) { probe_common_only = 1; }\n',
 'REFFN':'extern int probe_cd_fn(void);\nvoid main(void) { (void)probe_cd_fn(); }\n',
}
compiled={}
for basename,source in sources.items():
    (CONTROL/(basename+'.C')).write_text(source,encoding='ascii',newline='\r\n')
    result=compiler.compile_c(source,'msc600ax',['/AL','/Oeg','/Gs'],basename=basename,keep=True)
    if not result.ok or result.obj is None: raise SystemExit(f'{basename} compile failed: {result.log[-1200:]}')
    blob=result.obj; dst=CONTROL/(basename+'.OBJ'); dst.write_bytes(blob)
    o=rd.read(blob,basename)
    compiled[basename]={'source_sha256':hashlib.sha256(source.encode()).hexdigest(),
      'object':dst.name,'object_sha256':hashlib.sha256(blob).hexdigest(),
      'publics':[{'name':p['name'],'segment':p['segment'],'offset':p['offset']} for p in o.publics],
      'external_declarations':o.externals,
      'live_fixups':[f['target'] for f in o.linker_fixups if f.get('target_kind')=='external'],
      'communals':getattr(o,'communals',[]),
      'segments':[{'name':k,'length':len(v)} for k,v in o.segments.items()],
      'segment_defs':[{k:s.get(k) for k in ('name','class','length','alignment','combine')} for s in o.segment_defs],
      'comment_records':[{'class':c['class'],'attribute':c['attribute'],'data_hex':c['data_hex']} for c in o.comments]}
# LIB's prompts are answered with the documented response-file form. The previous v37
# shell-input control answered the create prompt but then hit EOF at List file/Output library.
for lib,mod in (('DATAONLY','DONLY'),('CODEDATA','CDMEM'),('COMONLY','COMMON')):
    (CONTROL/(lib+'.RSP')).write_text(
      f'{lib}.LIB\r\nyes\r\n+{mod}.OBJ\r\nNUL\r\n{lib}.LIB\r\n',
      encoding='ascii',newline='')
(CONTROL/'LIB.BAT').write_text(
 '@echo off\r\nLIB.EXE @DATAONLY.RSP > DATAONLY.LOG\r\n'
 'LIB.EXE @CODEDATA.RSP > CODEDATA.LOG\r\n'
 'LIB.EXE @COMONLY.RSP > COMONLY.LOG\r\n'
 'LIB.EXE /NOLOGO DATAONLY.LIB; > DATAONLY.CHK\r\n'
 'LIB.EXE /NOLOGO CODEDATA.LIB; > CODEDATA.CHK\r\n'
 'LIB.EXE /NOLOGO COMONLY.LIB; > COMONLY.CHK\r\n'
 'echo complete > LIBDONE.TXT\r\nexit\r\n',encoding='ascii',newline='')
tc=compiler.toolchain(); runner=tc['runners']['dosbox-x']
conf=[]
for sec,vals in runner['conf'].items(): conf.append(f'[{sec}]'); conf.extend(f'{k}={v}' for k,v in vals.items())
conf += ['[autoexec]',f'mount c "{CONTROL.resolve()}"','c:','call LIB.BAT','exit']
(CONTROL/'dosbox-lib.conf').write_text('\n'.join(conf)+'\n',encoding='ascii')
env=os.environ.copy(); env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
p=subprocess.run([runner['path'],'-conf',str(CONTROL/'dosbox-lib.conf'),'-fastlaunch','-exit','-nomenu'],cwd=CONTROL,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
if not (CONTROL/'LIBDONE.TXT').exists(): raise SystemExit('librarian batch did not finish: '+p.stdout.decode('latin1',errors='replace')[-1000:])
lib_build={}
expected_members={'DATAONLY.LIB':'DONLY.C','CODEDATA.LIB':'CDMEM.C','COMONLY.LIB':'COMMON.C'}
expected_publics={'DATAONLY.LIB':{'_probe_data_only'},'CODEDATA.LIB':{'_probe_cd_data','_probe_cd_fn'},'COMONLY.LIB':set()}
embedded_objects={}
for fn in expected_members:
 path=CONTROL/fn
 if not path.exists(): raise SystemExit(f'librarian did not create {fn}: {(CONTROL/(fn.replace(".LIB",".LOG"))).read_text(encoding="latin1",errors="replace")}')
 log=(CONTROL/fn.replace('.LIB','.LOG')).read_text(encoding='latin1',errors='replace')
 check=(CONTROL/fn.replace('.LIB','.CHK')).read_text(encoding='latin1',errors='replace')
 if re.search(r'(?i)(fatal error|\berror\b)',log) or re.search(r'(?i)(fatal error|\berror\b)',check):
  raise SystemExit(f'librarian failure for {fn}: {log!r} check={check!r}')
 members=rd.split_library(path.read_bytes())
 names=[n for n,_ in members]
 if names != [expected_members[fn]]:
  raise SystemExit(f'{fn} actual members differ: {names!r}')
 member_name,member_blob=members[0]
 member=rd.read(member_blob,member_name)
 publics={p['name'] for p in member.publics}
 if not expected_publics[fn].issubset(publics):
  raise SystemExit(f'{fn} embedded public mismatch: {publics!r}')
 embedded_objects[fn]={'member':member_name,'member_sha256':hashlib.sha256(member_blob).hexdigest(),
   'member_bytes':len(member_blob),'publics':[{'name':p['name'],'segment':p['segment'],'offset':p['offset']} for p in member.publics],
   'external_declarations':member.externals,
   'live_external_fixups':[f['target'] for f in member.linker_fixups if f.get('target_kind')=='external'],
   'communals':getattr(member,'communals',[]),
   'comment_records':[{'class':c['class'],'attribute':c['attribute'],'data_hex':c['data_hex']} for c in member.comments],
   'segment_lengths':{k:len(v) for k,v in member.segments.items()}}
 lib_build[fn]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,
   'members':names,'member_sha256':hashlib.sha256(member_blob).hexdigest(),'log':log,
   'consistency_check_log':check}
# Link four exact contrasts under both profiled RTLinks.
cases={
 'natural_main_llibcr_baseline':{'main':'BASE','libs':['LLIBCR','LIBH'],'ref':'none'},
 'both_unreferenced':{'main':'BASE','libs':['LLIBCR','LIBH','DATAONLY','CODEDATA','COMONLY'],'ref':'none'},
 'referenced_data_only':{'main':'REFDATA','libs':['LLIBCR','LIBH','DATAONLY'],'ref':'data'},
 'referenced_comdef_only':{'main':'REFCOM','libs':['LLIBCR','LIBH','COMONLY'],'ref':'common'},
 'referenced_code_plus_data':{'main':'REFFN','libs':['LLIBCR','LIBH','CODEDATA'],'ref':'function'},
}
link_runs=[]
for case_name,spec in cases.items():
    for profile in ('rtlink400','rtlink610'):
        dest=CONTROL/'links'/case_name/profile; dest.mkdir(parents=True,exist_ok=True)
        mainobj=CONTROL/(spec['main']+'.OBJ'); shutil.copyfile(mainobj,dest/'MAIN.OBJ')
        libnames=[]
        for ln in spec['libs']:
            if ln in ('LLIBCR','LIBH'): libnames.append(ln)
            else:
                fname=ln+'.LIB'; shutil.copyfile(CONTROL/fname,dest/fname); libnames.append(fname)
        (dest/'T.LNK').write_text('OUTPUT TEST\r\nMAP = TEST S,N,A,L,V,X\r\nNODEFLIB\r\nLIBRARY '+', '.join(libnames)+'\r\nFILE MAIN\r\nVERBOSE\r\n',encoding='ascii',newline='')
        rc=rtlink.run_link(dest,profile=profile,timeout=240)
        log=(dest/'LINK.LOG').read_text(encoding='latin1',errors='replace') if (dest/'LINK.LOG').exists() else ''
        mp=(dest/'TEST.MAP').read_text(encoding='latin1',errors='replace') if (dest/'TEST.MAP').exists() else ''
        selected=re.findall(r'(?:DATAONLY|CODEDATA|COMONLY)\.LIB\(([^)]+)\)',log,re.I)
        selected_llibcr=re.findall(r'LLIBCR\.LIB\(([^)]+)\)',log,re.I)
        selected_libh=re.findall(r'LIBH\.LIB\(([^)]+)\)',log,re.I)
        outputs=[]
        for sym in ('_probe_data_only','_probe_common_only','_probe_cd_data','_probe_cd_fn'):
            found=re.findall(r'^\s*[0-9A-Fa-f]+:[0-9A-Fa-f]+\s+(?:Res\s+)?'+re.escape(sym)+r'\b[^\r\n]*',mp,re.M|re.I)
            outputs+=found
        warnings=[x.strip() for x in log.splitlines() if 'warning' in x.lower() or 'wrt' in x.lower()]
        undefined=[]
        if 'UNDEFINED SYMBOL' in log:
            tail=log.split('UNDEFINED SYMBOL',1)[1].split('**** WRITING EXECUTABLE ****',1)[0]
            undefined=re.findall(r"^\s*'([^']+)'",tail,re.M)
        fheap_rows=[x.strip() for x in mp.splitlines() if '__fheap' in x.lower()]
        fmalloc_rows=[x.strip() for x in mp.splitlines() if '__fmalloc' in x.lower()]
        link_runs.append({'case':case_name,'profile':profile,'return_code':rc,
          'partial_or_complete_output_written':bool((dest/'TEST.EXE').exists()),'map_written':bool(mp),
          'selected_custom_library_members':selected,'selected_llibcr_members':selected_llibcr,
          'selected_libh_members':selected_libh,'target_public_map_rows':outputs,
          'fheap_map_rows':fheap_rows,'fmalloc_map_rows':fmalloc_rows,'undefined_symbols':undefined,
          'warnings':warnings,'executable_executed':False,
          'link_log':(dest/'LINK.LOG').relative_to(ROOT).as_posix(),'map':(dest/'TEST.MAP').relative_to(ROOT).as_posix() if mp else None,
          'link_log_sha256':hashlib.sha256(log.encode('latin1',errors='replace')).hexdigest(),
          'map_sha256':hashlib.sha256(mp.encode('latin1',errors='replace')).hexdigest() if mp else None,
          'link_script':(dest/'T.LNK').relative_to(ROOT).as_posix()})
        print(case_name,profile,'selected',selected,'map symbols',len(outputs),'rc',rc)
# Parse the pinned natural fdata module comment/COMDEF/public metadata without raw data payload.
ll=Path(r'C:\tools\msc-6.00\LIB\llibcr.lib'); ll_sha=hashlib.sha256(ll.read_bytes()).hexdigest()
libarch={n.lower():(n,b) for n,b in rd.split_library(ll.read_bytes())}
name,blob=libarch['fdata.asm']; fo=rd.read(blob,name)
fdata={'member':name,'publics':[{'name':x['name'],'segment':x['segment'],'offset':x['offset']} for x in fo.publics],
       'externals':fo.externals,'communals':getattr(fo,'communals',[]),
       'segments':[{'name':k,'length':len(v)} for k,v in fo.segments.items()],
       'segment_defs':[{k:s.get(k) for k in ('name','class','length','alignment','combine')} for s in fo.segment_defs],
       'comments':[{'class':c['class'],'attribute':c['attribute'],'data_hex':c['data_hex']} for c in fo.comments],
       'fixup_count':len(fo.linker_fixups)}
runtime_modules={}
for wanted in ('dos\\stdalloc.asm','malloc.asm','fmalloc.asm','fdata.asm'):
    module,blob=libarch[wanted]
    obj=rd.read(blob,module)
    runtime_modules[module]={'publics':[p['name'] for p in obj.publics],
      'external_declarations':obj.externals,
      'live_external_fixups':[f['target'] for f in obj.linker_fixups if f.get('target_kind')=='external'],
      'segment_lengths':{k:len(v) for k,v in obj.segments.items()}}
report={'schema':'simant-rtlink-data-only-member-selection-v37a','status':'LINK_ONLY_CONTROL_RECEIPT',
 'librarian':{'version':'Microsoft Library Manager 3.17','path':str(LIBSRC),'sha256':LIBSHA,'source_sha256':hashlib.sha256(LIBSRC.read_bytes()).hexdigest(),'dosbox_return_code':p.returncode,
    'response_file_method':'LIB @response-file; each response supplies library name, create confirmation, add operation, NUL list file, and output library',
    'responses':{name:{'sha256':hashlib.sha256((CONTROL/(name+'.RSP')).read_bytes()).hexdigest(),'text':(CONTROL/(name+'.RSP')).read_text(encoding='ascii')} for name in ('DATAONLY','CODEDATA','COMONLY')},
    'libraries':{k:{'build_log':v['log'],'consistency_check_log':v['consistency_check_log']} for k,v in lib_build.items()}},
 'runtime_library':{'path':str(ll),'sha256':ll_sha,'natural_crt_chain_omf':runtime_modules,'fdata_omf':fdata},
 'object_controls':compiled,'built_libraries':{k:{'sha256':v['sha256'],'bytes':v['bytes'],'members':v['members'],'member_sha256':v['member_sha256']} for k,v in lib_build.items()},
 'embedded_library_member_omf':embedded_objects,
 'link_runs':link_runs,
 'source_document_review':[
   {'path':r'C:\tools\RTLink-Plus-4.00-DiscMaster\installed\dest\RTLINK.HLP',
    'finding':'Lists LIBRARY syntax; no general EXE archive-extraction or unused-member rule found.'},
   {'path':r'C:\tools\RTLink-Plus-4.00-DiscMaster\installed\dest\EXAMPLE.DOC',
    'finding':'Shows LIBRARY use and compiler-embedded MSC library names; no ordinary-link member-selection algorithm stated.'},
   {'path':r'C:\tools\RTLink-Plus-4.00-DiscMaster\installed\dest\CLIP-A86.HLP',
    'finding':'Lines 59-64 describe unresolved-symbol/UNDEFINE selection when generating an RTL; this is not evidence for normal EXE extraction.'},
   {'path':r'C:\tools\RTLink-Plus-4.00-DiscMaster\installed\dest\MS-C60.HLP',
    'finding':'Lines 66-74 describe regular-library lookup for unresolved symbols while generating an RTL; not a general normal-EXE rule.'},
   {'path':'https://openwatcom.org/ftp/devel/docs/omf.pdf',
    'finding':'OMF TIS pp. 12, 19: class A2 is a pass-separator comment and class A3 is LIBMOD metadata recording a library/module name; these records do not establish an RTLink extraction directive. The post-LIB custom member comments confirm LIB inserted the A3 module-name record.'}],
 'interpretation':{
 'generic_unreferenced_member_autoload':'Not observed for the tested ordinary C-built data-only or code+data members with either RTLink 4.00 or 6.10; v37a repeats this after a clean, successful LIB 3.17 creation and consistency check.',
   'referenced_member_control':'A live reference to initialized data or a function in a code+data member extracts that member under both linkers.',
   'natural_main_baseline':'Both linkers select fdata in the clean natural-main control; pinned OMF fixups show stdalloc->_malloc, malloc->__fmalloc, and fmalloc->__fheap, with fdata defining __fheap.',
   'comdef_only_control':'The live reference to a COMDEF-only library member stays undefined under both linkers; this is a limitation/control result, not an initialized data-only positive.',
   'application_rtlink610_fdata':'The current186 partial 6.10 run selects fdata.asm alone; this control excludes generic unreferenced-member autoload but does not determine the app-specific trigger or any transient linker-internal selection/discard behavior.',
   'historical_79f0':'No inference about historical address, original byte identity, order, or initialization.'},
 'all_generated_exes_unexecuted':True}
# v37's library bytes and member listings are retained as prior evidence, but its interactive
# stdin session ended with U1158 at the output-library prompt. Compare the repaired, clean run
# explicitly so the identical binary results are corroboration rather than silent repinning.
prior_path=ROOT/'build/workers/dos_fdata_selection_cause_v37/selection-cause-controls-v37.json'
prior=json.loads(prior_path.read_text(encoding='utf-8'))
report['prior_v37_reconciliation']={
 'receipt':prior_path.relative_to(ROOT).as_posix(),
 'v37_librarian_logs':{k:prior['librarian'][k] for k in ('dataonly_lib_build_log','codedata_lib_build_log','comdef_only_lib_build_log')},
 'v37a_logs_clean_and_no_fatal_error':all(not re.search(r'(?i)(fatal error|\berror\b)',v['log']) and not re.search(r'(?i)(fatal error|\berror\b)',v['consistency_check_log']) for v in lib_build.values()),
 'same_compiled_object_hashes':{k:prior['object_controls'][k]['object_sha256']==compiled[k]['object_sha256'] for k in ('DONLY','CDMEM','COMMON')},
 'same_library_hashes':{k:prior['built_libraries'][k]['sha256']==lib_build[k]['sha256'] for k in expected_members},
 'same_library_member_names':{k:prior['built_libraries'][k]['members']==lib_build[k]['members'] for k in expected_members},
 'interpretation':'v37 emitted fatal U1158 terminator-missing logs after writing bytes; v37a uses complete LIB response files, clean build logs, clean consistency-check logs, verifies actual embedded modules/publics, and independently reproduces byte-identical libraries from byte-identical C object inputs.'}
(OUT/'selection-cause-controls-v37a.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('written',OUT/'selection-cause-controls-v37a.json')
