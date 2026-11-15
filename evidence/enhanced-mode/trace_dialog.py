import sys
sys.dont_write_bytecode=True
from capture_current import *
import concurrent.futures
fixture=(ROOT/'portable/tests/runtime/windows-quick.txt').read_text()
cases={
 'full-fixed':fixture.replace('207 58','131 127')+'16000 move@0000 35 29\n16100 mouse-down@0000 Left 35 29\n',
 'yellow-help':fixture+'16000 move@0000 231 150\n16100 mouse-down@0000 Left 231 150\n16700 move@0700 35 91\n17000 mouse-up@0700 Left 35 91\n',
 'health-zero':fixture+'16000 move@0000 15 239\n16100 mouse-down@0000 Left 15 239\n16200 mouse-up@0000 Left 15 239\n23000 down Return\n23100 up Return\n29000 down Return\n29100 up Return\n',
 'tutorial':fixture.replace('207 58','50 55'),
 'death-birth':fixture+''.join(f'{16000+i*300} down {k}\n{16050+i*300} up {k}\n' for i,k in enumerate(['E','R','A','D']))+''.join(f'{t} down Return\n{t+50} up Return\n' for t in (22000,27000,32000,37000,42000)),
 'birth-modal':fixture+''.join(f'{16000+i*300} down {k}\n{16050+i*300} up {k}\n' for i,k in enumerate(['E','R','A','D']))+''.join(f'{t} down Return\n{t+50} up Return\n' for t in (22000,27000,32000,37000)),
}
def trace(name,script):
    d=OUT/'dialog-trace'/name;d.mkdir(parents=True,exist_ok=False);shutil.copytree(BUILD/'runtime-assets',d/'a');(d/'sessions').mkdir()
    (d/'input.txt').write_text(script)
    gdb='C:/msys64/mingw64/bin/gdb.exe'
    python="""import gdb, json
class Log(gdb.Breakpoint):
 def stop(self):
  names=['MapPlane','MapPnt','edit_life_tiles_handle','edit_life_alt_tiles_handle','MeType','MeHealth','MeEgg','main_iteration_count','*(short*)&clip_window_z_order']
  vals={}
  for n in names:
   try: vals[n]=str(gdb.parse_and_eval(n))
   except Exception as e: vals[n]=str(e)
  for n,size in [('LifeA',8192),('LifeB',4096),('LifeR',4096)]:
   try:
    raw=bytes(gdb.selected_inferior().read_memory(int(gdb.parse_and_eval('&'+n)),size));vals[n+'_nonzero']=sum(x!=0 for x in raw)
   except Exception as e: vals[n+'_error']=str(e)
  print('DESIGN_TRACE '+self.location+' '+json.dumps(vals))
  if self.location=='edit_release_life_tiles' and int(gdb.parse_and_eval('main_iteration_count'))>0:
   print(gdb.execute('bt 9',to_string=True))
  return False
for name in ['YellowDialog','YellowBirth','YellowDeath','edit_release_life_tiles','app_window_state_changed','win_EditChanged']:
 Log(name)
class Stop(gdb.Breakpoint):
 def stop(self):
  Log.stop(self)
  return False
Stop('__wrap_exit')
"""
    (d/'observe.py').write_text(python)
    (d/'gdb.txt').write_text('set pagination off\nset confirm off\nsource '+str(d/'observe.py').replace('\\','/')+'\nrun\n')
    smoke=40000 if name=='birth-modal' else (47000 if name=='death-birth' else (33000 if name=='health-zero' else 19000))
    cmd=[gdb,'--batch','-q','-x',str(d/'gdb.txt'),'--args',str(OUT/'p/simant-canonical.exe'),'--headless','--windows','--deterministic','--seed','0','--assets',str(d/'a'),'--diagnostics-dir='+str(d/'sessions'),'--smoke-ms',str(smoke),'--frame',str(d/'frame.bmp'),'--input-script',str(d/'input.txt')]
    try:
        r=subprocess.run(cmd,cwd=d,capture_output=True,timeout=180);(d/'gdb-out.txt').write_bytes(r.stdout+r.stderr);print(name,r.returncode,flush=True)
    except subprocess.TimeoutExpired as e:(d/'gdb-out.txt').write_bytes((e.stdout or b'')+(e.stderr or b''));print(name,'timeout',flush=True)
selected={k:v for k,v in cases.items() if len(sys.argv)<2 or k in sys.argv[1:]}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as p:list(p.map(lambda a:trace(*a),selected.items()))
