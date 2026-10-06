"""Default sound selection and lifecycle; hardware helpers are explicit models."""
from pathlib import Path
from types import SimpleNamespace
import sys,json,hashlib,struct,importlib.util
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'src/program.json').is_file())
sys.path.insert(0,str(ROOT/'tools'))
import behavior as b,exe,functions
if not __debug__:raise RuntimeError('proof checks require Python without -O')

PROTECTED={'fd_50F6_01F0':14,'fd_55B3_610A':2,'g_1926':2,
 'fd_55B3_74FE':4,'fd_55B3_74DA':36,'g_68B6':36,'g_68DA':36}

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,ROOT/path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

class Boundary(Exception): pass

def machine(name):
 x=exe.load(); return b.Machine(SimpleNamespace(function=functions.get(name),vectors={exe.MANAGER_SEG*16+v.offset:v for v in x.vectors}))

def original_controls():
 sel=b.symbol_address('fd_50F6_01F0'); rows=[]
 for detected,expected,setup in [(0,1,'f_277E_017D'),(1,6,'f_277E_04E8')]:
  m=machine('f_277E_0000')
  def detect(cpu,args,value=detected): return value
  cb={'f_293A_0121':b.Callback(0,detect),setup:b.Callback(0,lambda cpu,args:1),
      'f_29F0_001A':b.Callback(0,lambda cpu,args:None),'f_29F0_0022':b.Callback(0,lambda cpu,args:None),
      'f_28BC_0488':b.Callback(2,lambda cpu,args:None),'f_28BC_03CC':b.Callback(0,lambda cpu,args:None),
      'f_19A9_000B':b.Callback(2,lambda cpu,args:None)}
  r=m.run(b.Case('mode6-detector-'+str(detected),args=[6,0],writes=[(sel,b.words(0,0,0,0,0,0,0))],callbacks=cb,max_instructions=30000))
  assert r['return']==expected and m.word(sel)==expected
  called=[x['name'] for x in r['raw_trace']]
  assert setup in called and ('f_277E_017D' if expected==1 else 'f_277E_04E8') in called
  rows.append({'entry_mode':6,'detector_result':detected,'local_and_stored_mode':expected,'setup_entry':setup,'callbacks':called})
 cleanup=[]
 for guard in [-1,6]:
  m=machine('o15_384C_0152'); seen=[]
  def stop_exit(cpu,args): raise Boundary()
  cb={'f_171C_0676':b.Callback(1,lambda cpu,args:None),
      'f_277E_0154':b.Callback(0,lambda cpu,args:seen.append(m.word(sel))),
      'f_1C62_00A1':b.Callback(0,lambda cpu,args:None),'f_1C62_0090':b.Callback(0,lambda cpu,args:None),
      'puts':b.Callback(1,lambda cpu,args:0),'exit':b.Callback(1,stop_exit)}
  initial_selector=m.word(sel)
  assert initial_selector==0
  try:
   r=m.run(b.Case('startup-cleanup-guard-'+str(guard),args=[0,0x7000,0],writes=[
    (b.symbol_address('fd_55B3_610A'),b.words(guard)),(0x70000,b'cleanup\0')],
    callbacks=cb,return_kind='void',max_instructions=30000))
  except b.ExecutionError as exc:
   if not isinstance(exc.__cause__,Boundary):raise
  else:raise AssertionError('cleanup did not reach explicit exit boundary')
  assert seen==[0] and 'f_277E_0154' in [x['name'] for x in m.raw_trace]
  cleanup.append({'g_610A':guard,'CRT_selector_before_cleanup':initial_selector,'selector_at_cleanup':seen[0],'guard_took_cleanup':True})
 for mode in [0,1,6]:
  m=machine('f_277E_0154')
  cb={'f_295C_0391':b.Callback(0,lambda cpu,args:None),'f_0000_0429':b.Callback(0,lambda cpu,args:None),
      'f_28BC_04E0':b.Callback(1,lambda cpu,args:None),'f_29F0_002A':b.Callback(2,lambda cpu,args:None),
      'f_2815_0118':b.Callback(0,lambda cpu,args:None)}
  r=m.run(b.Case('dispatch-cleanup-'+str(mode),writes=[(sel,b.words(mode,0,0,0,0,0,0)),
    (b.symbol_address('fd_55B3_6BA0'),b.words(0x220))],callbacks=cb,return_kind='void',io_reads={0x61:0},max_instructions=30000))
  assert 'f_28BC_04E0' in [x['name'] for x in r['raw_trace']]
  cleanup.append({'selector':mode,'cleanup_returned':True,'calls':[x['name'] for x in r['raw_trace']]})
 # Stop on the original indirect-call instruction for /s9; record its adjacent table target without executing it.
 m=machine('f_277E_0000'); reached={}
 def guard(cpu,address,size,user):
  call=b.symbol_address('f_277E_0000')+0x16
  if address==call:
   es=cpu.reg_read(b.REGS['es']); bx=cpu.reg_read(b.REGS['bx']); at=es*16+0x74da+bx
   raw=bytes(cpu.mem_read(at,4)); reached.update(index=cpu.reg_read(b.REGS['si']),table_address=at,target_offset=int.from_bytes(raw[:2],'little'),target_segment=int.from_bytes(raw[2:],'little'))
   raise Boundary()
 m.cpu.hook_add(b.uc.UC_HOOK_CODE,guard)
 try:m.run(b.Case('out-of-domain-s9-prefix',args=[9,0],max_instructions=1000))
 except b.ExecutionError as exc:
  if not isinstance(exc.__cause__,Boundary):raise
 else:raise AssertionError('/s9 did not stop at the indirect call')
 assert reached.get('index')==9
 return {'default_setup_original_prefixes':rows,'startup_cleanup_original_prefixes':cleanup,
  's9_negative_control':reached,'scope':'Original instructions through setup selection and cleanup selector dispatch; hardware detector/setup internals are explicit callback boundaries; s9 stops before executing the out-of-range pointer.'}

def support():
 vga=load('vga_probe','evidence/canonical/icon-handle-view/vga_probe.py')
 vga.TARGETS={'fd_50F6_01F0','fd_55B3_74FE','fd_55B3_74DA','fd_55B3_610A','g_610A','g_1926','g_68B6','g_68DA','f_277E_0000','f_00DF_0004','f_293A_0006','f_293A_0121','o15_384C_0152','f_277E_0154','main','IBMInitStuff','ReadConfig','f_284A_0013','myBeginSong'}
 return vga

def save_ranges(texts,raw=None):
 db=load('sound_save_table','evidence/canonical/database-domain/replay.py')
 db.save_table_proof(texts)
 if raw is None:raw=db.oracle_machine('OpenDB').read(b.symbol_address('fd_4E4B_0000'),308*8)
 ranges={name:(b.symbol_address(name),size) for name,size in PROTECTED.items()}
 for i in range(307):
  size,count,off,seg=struct.unpack_from('<HHHH',raw,i*8); start=seg*16+off
  for name,(at,width) in ranges.items():
   if start<at+width and at<start+size*count:raise ValueError('save overlaps sound selector/dispatch: '+name)
 return {'records':307,'protected_ranges':{n:{'linear':a,'bytes':w} for n,(a,w) in ranges.items()},'overlap_count':0,'descriptor_sha256':hashlib.sha256(raw).hexdigest()}

def collect():
 vga=support();texts,program,registry=vga.inventory()
 census=vga.census(texts,program,registry)
 db=load('database_replay','evidence/canonical/database-domain/replay.py')
 db.inventory_and_scan(); resources=db.verify_resource_domain()
 omachine=db.oracle_machine('OpenDB')
 table_ids={
  'fd_55B3_74DA':['f_293A_0029','f_293A_0029','f_293A_002D','f_293A_0059','f_293A_0087','f_293A_015E','f_293A_0121','f_293A_017C','f_293A_017F'],
  'g_68B6':['f_277E_0179','f_277E_017D','f_277E_01FA','f_277E_034F','f_277E_040E','f_277E_0606','f_277E_04E8','f_277E_0760','f_277E_07FF'],
  'g_68DA':['f_277E_0938','f_277E_0958','f_277E_0938','f_277E_0938','f_277E_0938','f_277E_0965','f_277E_0939','f_277E_0952','f_277E_0938']}
 table_controls={}
 for name,identities in table_ids.items():
  at=b.symbol_address(name); observed=[]
  for i,identity in enumerate(identities):
   off,seg=struct.unpack('<HH',omachine.read(at+i*4,4))
   sym=b.symbol(identity)
   if (off,seg)!=(sym['off'],sym['seg']):raise AssertionError(f'{name}[{i}] target differs from {identity}')
   observed.append(identity)
  table_controls[name]={'bytes':36,'entries':observed,'original_far_pointer_targets_match':True}
 # Preserve evidence of every textual source occurrence, including data aliases.
 refs=[]
 for path,text in sorted(texts.items()):
  if any(x in text for x in ('fd_50F6_01F0','fd_55B3_74FE','fd_55B3_610A','g_610A')):
   for n,line in enumerate(text.splitlines(),1):
    if any(x in line for x in ('fd_50F6_01F0','fd_55B3_74FE','fd_55B3_610A','g_610A')): refs.append([path,n,line.strip()])
 return {'scope':'Default shipped-resource successful lifetime; config and setup/cleanup selector writes, no /s9 or arbitrary damaged-resource claim.',
  'oracle_sha256':exe.load().sha256,'inventory':vga.inventory_pins(texts,program,registry),
  'selector_census':census,'selector_refs':refs,'resource_domain':resources,
  'save_overlap':save_ranges(texts),
  'dispatch_tables':table_controls,
  'sound_mode_proof':{'cfg_sound_mode':'6','readconfig_digit':'stores numeric digit when isdigit(lang)','startup':'IBMInitStuff resets g_610A=-1 then ReadConfig; empty argv preserves6','main_order':'main calls f_00DF_0004 once after IBMInitStuff and db_SetDataBase(sound)'},
  'selector_transitions':{'entry':0,'setup_request':6,'detector_result_false_fallback':1,'detector_result_true':6,'pre_setup_cleanup_guard_values':[-1,6],'pre_setup_cleanup_selector':0,'setup_write_position':'f_277E_0000 stores selected local mode into fd_50F6_01F0[0] only after setup, framebuffer and helper calls','detector_candidates':list(range(9))},
  'original_controls':original_controls()}

def check():
 actual=collect()
 if actual!=json.loads(Path(__file__).with_name('selector-facts.json').read_text()):
  raise ValueError('sound selector proof differs from reviewed facts')
 return actual

if __name__=='__main__':
 actual=check()
 print('PASS',actual['inventory']['source_count'],'sources',actual['selector_census']['occurrences'],'occurrences')
