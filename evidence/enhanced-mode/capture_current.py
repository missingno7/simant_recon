import sys
sys.dont_write_bytecode=True
import ctypes as C, ctypes.wintypes as W, subprocess, time, shutil, json, hashlib, os
from pathlib import Path
from PIL import Image
ROOT=Path('D:/Prog/simant_recon');OUT=ROOT/'build/workers/enhanced-design';BUILD=ROOT/'build/current/portable'
U=C.WinDLL('user32');CB=C.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
U.EnumWindows.argtypes=[CB,W.LPARAM];U.GetWindowThreadProcessId.argtypes=[W.HWND,C.POINTER(W.DWORD)];U.GetWindowTextW.argtypes=[W.HWND,W.LPWSTR,C.c_int]
def windows(pid):
    a=[]
    @CB
    def cb(h,_):
        p=W.DWORD();U.GetWindowThreadProcessId(h,C.byref(p))
        if p.value==pid and U.IsWindowVisible(h):
            t=C.create_unicode_buffer(256);U.GetWindowTextW(h,t,256);r=W.RECT();U.GetWindowRect(h,C.byref(r));a.append(dict(hwnd=h,title=t.value,rect=[r.left,r.top,r.right,r.bottom]))
        return True
    U.EnumWindows(cb,0);return a
def run(name,lines,smoke,headless=False,mode='--windows'):
    d=OUT/'r2'/name;d.mkdir(parents=True,exist_ok=False);shutil.copytree(BUILD/'runtime-assets',d/'a');(d/'sessions').mkdir()
    script=d/'input.txt';script.write_text(lines)
    cmd=[str(OUT/'p/simant-canonical.exe'),*([mode] if mode else []),'--seed','0','--assets',str(d/'a'),'--diagnostics-dir='+str(d/'sessions'),'--smoke-ms',str(smoke),'--frame',str(d/'frame.bmp'),'--input-script',str(script)]
    if headless:cmd+=['--headless']
    row={'command':cmd,'started':time.time(),'headless':headless};samples=[]
    with (d/'stderr.txt').open('w') as log:
        p=subprocess.Popen(cmd,stdout=log,stderr=log,cwd=d,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
        try:
            while p.poll() is None and time.time()-row['started']<70:
                current=windows(p.pid)
                if not samples or [x['title'] for x in current]!=[x['title'] for x in samples[-1]['windows']]:samples.append({'elapsed':time.time()-row['started'],'windows':current})
                time.sleep(.2)
            if p.poll() is None:row['forced_cleanup']=True;p.kill()
            row['exit']=p.wait(timeout=5)
        finally:
            if p.poll() is None:p.kill();p.wait()
            row['remaining_windows']=windows(p.pid)
    row['samples']=samples;row['elapsed']=time.time()-row['started']
    for b in d.glob('frame*.bmp'):
        im=Image.open(b);im.save(b.with_suffix('.png'))
    (d/'run.json').write_text(json.dumps(row,indent=2))
    print(name,row['exit'],round(row['elapsed'],2),[x.name for x in d.glob('*.png')],flush=True)
    return row
if __name__=='__main__':
    p=OUT/'p';p.mkdir(exist_ok=True)
    for f in ['simant-canonical.exe','SDL3.dll','simant-build-id.txt','report.json']:shutil.copy2(BUILD/f,p/f)
    shutil.copytree(BUILD/'runtime-bios-fonts',p/'runtime-bios-fonts',dirs_exist_ok=True)
    identities={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in p.iterdir() if f.is_file()}
    (OUT/'build-identities.json').write_text(json.dumps(identities,indent=2))
    fixture=(ROOT/'portable/tests/runtime/windows-quick.txt').read_text()
    cases={
      'title':('',4000),
      'registration':((ROOT/'portable/tests/runtime/windows-startup.txt').read_text(),6500),
      'select':('\n'.join(fixture.splitlines()[:7])+'\n',9800),
      'quick':(fixture,17500),
      'panels':(fixture+'16000 menu FD15\n17000 menu FD16\n18000 menu FD13\n19000 menu FD14\n',20500),
      'status':(fixture+'16000 menu FD17\n',18000),
      'saveas':(fixture+'16000 menu FD06\n',18000),
      'yard':(fixture+'16000 menu FD21\n',18500),
      'menu':((ROOT/'portable/tests/runtime/windows-menu.txt').read_text(),17500),
      'prox':((ROOT/'portable/tests/runtime/windows-prox.txt').read_text().split('18000')[0],17800),
    }
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        results=list(pool.map(lambda a:run(a[0],*a[1]),cases.items()))
    (OUT/'capture-report.json').write_text(json.dumps(dict(zip(cases,results)),indent=2))
