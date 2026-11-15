"""Bounded owned-window measurement; every suspension and button is released."""
import argparse,ctypes,json,os,shutil,subprocess,sys,time
from ctypes import wintypes as w
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from portable.tests.acceptance.ideal_check import native_script
p=argparse.ArgumentParser();p.add_argument('build',type=Path);p.add_argument('out',type=Path);p.add_argument('--seconds',type=int,default=95);p.add_argument('--interruptions',action='store_true');p.add_argument('--drag-only',action='store_true');p.add_argument('--no-trace',action='store_true');p.add_argument('--input-script',type=Path,help='Native input script; default is the canonical Ant Menu recipe');a=p.parse_args()
a.build=a.build.resolve();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False);shutil.copytree(a.build/'runtime-assets',a.out/'a')
if a.input_script:shutil.copyfile(a.input_script,a.out/'input.txt')
else:native_script(ROOT/'dos/scenarios/ideal-v1/ant-commands.scr',a.out/'input.txt')
script=a.out/'input.txt'
script.write_text(script.read_text().replace(' enter',' Return').replace(' lctrl',' Left Ctrl').replace(' lshift',' Left Shift').replace(' esc',' Escape'))
env=dict(os.environ,SIMANT_PACING_STATS=str(a.out/'pacing.json'))
if not a.no_trace:env['SIMANT_AUDIO_QUEUE_TRACE']=str(a.out/'queue.jsonl')
cmd=[str(a.build/'simant-canonical.exe'),'--assets',str(a.out/'a'),'--seed','0','--smoke-ms',str(a.seconds*1000),'--input-script',str(a.out/'input.txt'),'--diagnostics-dir='+str(a.out/'diagnostics')]
k=ctypes.WinDLL('kernel32',use_last_error=True);u=ctypes.WinDLL('user32',use_last_error=True);nt=ctypes.WinDLL('ntdll')
k.GetProcessTimes.argtypes=[w.HANDLE,*([ctypes.POINTER(ctypes.c_ulonglong)]*4)]
nt.NtSuspendProcess.argtypes=[w.HANDLE];nt.NtResumeProcess.argtypes=[w.HANDLE]
u.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)];u.GetWindowRect.argtypes=[w.HWND,ctypes.POINTER(w.RECT)]
u.ShowWindow.argtypes=[w.HWND,ctypes.c_int];u.SetForegroundWindow.argtypes=[w.HWND];u.IsWindowVisible.argtypes=[w.HWND]
u.EnumWindows.argtypes=[ctypes.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM),w.LPARAM]
u.GetWindowTextW.argtypes=[w.HWND,w.LPWSTR,ctypes.c_int]
u.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM]
def window(pid):
    result=[]
    @ctypes.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
    def visit(h,param):
        owner=w.DWORD();u.GetWindowThreadProcessId(h,ctypes.byref(owner))
        if owner.value==pid and u.IsWindowVisible(h):
            title=ctypes.create_unicode_buffer(256);u.GetWindowTextW(h,title,256);result.append((h,title.value))
        return True
    u.EnumWindows(visit,0)
    return next((h for h,title in result if title=='SimAnt'),next((h for h,title in result if 'SimAnt' in title),result[-1][0] if result else None))
def cpu(proc):
    v=[ctypes.c_ulonglong() for _ in range(4)]
    if not k.GetProcessTimes(int(proc._handle),*[ctypes.byref(x) for x in v]):raise ctypes.WinError(ctypes.get_last_error())
    return (v[2].value+v[3].value)/1e7
actions=[];samples=[];suspended=False;down=False;moving=False;h=None
with (a.out/'log.txt').open('w') as log:
    proc=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=log,stderr=log);start=time.perf_counter()
    schedule=[(55,'minimize'),(58,'restore'),(65,'drag-start'),(66,'drag-end'),(75,'breakpoint-start'),(76,'breakpoint-end')] if a.interruptions else [(20,'drag-start'),(21,'drag-end')] if a.drag_only else []
    try:
        while proc.poll() is None:
            elapsed=time.perf_counter()-start
            if elapsed>a.seconds+20:raise TimeoutError('game failed bounded exit')
            samples.append([elapsed,cpu(proc)])
            if schedule and elapsed>=schedule[0][0]:
                _,action=schedule.pop(0);h=window(proc.pid) or h
                title=ctypes.create_unicode_buffer(256);r=w.RECT()
                if h:u.GetWindowTextW(h,title,256);u.GetWindowRect(h,ctypes.byref(r))
                actions.append(dict(seconds=elapsed,action=action,window=int(h or 0),title=title.value,rect=[r.left,r.top,r.right,r.bottom]))
                if action=='minimize':assert h;u.ShowWindow(h,6)
                elif action=='restore':u.ShowWindow(h,9)
                elif action=='drag-start':
                    assert h;u.PostMessageW(h,0x0112,0xf010,0);moving=True
                elif action=='drag-end':u.PostMessageW(h,0x0100,13,1);u.PostMessageW(h,0x0101,13,1);moving=False
                elif action=='breakpoint-start':assert nt.NtSuspendProcess(int(proc._handle))==0;suspended=True
                elif action=='breakpoint-end':assert nt.NtResumeProcess(int(proc._handle))==0;suspended=False
            if down:
                r=w.RECT();u.GetWindowRect(h,ctypes.byref(r));u.SetCursorPos((r.left+r.right)//2+2,r.top+12)
            if moving:u.PostMessageW(h,0x0100,39,1);u.PostMessageW(h,0x0101,39,1)
            time.sleep(.05)
        end=time.perf_counter()-start;total=cpu(proc)
    finally:
        if down:u.mouse_event(4,0,0,0,0)
        if moving and h:u.PostMessageW(h,0x0100,13,1);u.PostMessageW(h,0x0101,13,1)
        if suspended:nt.NtResumeProcess(int(proc._handle))
        if proc.poll() is None:proc.kill()
        proc.wait()
receipt=dict(command=cmd,code=proc.returncode,seconds=end,cpu_seconds=total,samples=samples,actions=actions)
play=[s for s in samples if s[0]>=12]
receipt['play_one_core_percent']=100*(play[-1][1]-play[0][1])/(play[-1][0]-play[0][0]) if len(play)>1 else None
(a.out/'session.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k!='samples'}))
raise SystemExit(int(proc.returncode!=0))
