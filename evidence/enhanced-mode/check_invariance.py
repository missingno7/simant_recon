import sys
sys.dont_write_bytecode=True
from pathlib import Path
import importlib.util,json,shutil,subprocess,hashlib
ROOT=Path('D:/Prog/simant_recon');OUT=ROOT/'build/workers/enhanced-design';BUILD=ROOT/'build/current/portable'
sys.path.insert(0,str(ROOT/'portable/tests/runtime'))
import run_modern as m
out=OUT/'invariance';out.mkdir(exist_ok=False)
states={}
for name,mode in [('modern','--windows'),('hosted_control','--windows=200')]:
    diag=out/(name+'-diag');diag.mkdir()
    text=m.gdb_run(BUILD,OUT/'p/simant-canonical.exe',out,name,'windows-quick.txt',m.STATE,(mode,'--diagnostics-dir='+str(diag)))
    states[name]=m.values(text)
result={'method':'same copied as-built executable; run_modern.gdb_run, STATE and windows-quick.txt; no rebuilt source or clock changes','state_fields':m.STATE,'values':states,'bounded_equal':len(states['modern'])==len(m.STATE) and states['modern']==states['hosted_control'],'executable_sha256':hashlib.sha256((OUT/'p/simant-canonical.exe').read_bytes()).hexdigest()}
(out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
