"""Bounded real-window CPU/lifecycle audit. Percentages are of one CPU core.

Runs without interactive input. Saves evidence, including inaccessible desktop
capabilities, rather than calling simulated display/focus transitions hardware QA.
"""
import argparse, ctypes as C, ctypes.wintypes as W, json, os, shutil, subprocess, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
U=C.WinDLL('user32',use_last_error=True);K=C.WinDLL('kernel32',use_last_error=True)
CB=C.WINFUNCTYPE(W.BOOL,W.HWND,W.LPARAM)
U.EnumWindows.argtypes=[CB,W.LPARAM];U.GetWindowThreadProcessId.argtypes=[W.HWND,C.POINTER(W.DWORD)]
U.GetWindowTextW.argtypes=[W.HWND,W.LPWSTR,C.c_int];U.PostMessageW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM]
U.ShowWindow.argtypes=[W.HWND,C.c_int];U.SetForegroundWindow.argtypes=[W.HWND];U.DestroyWindow.argtypes=[W.HWND]
U.SetWindowPos.argtypes=[W.HWND,W.HWND,C.c_int,C.c_int,C.c_int,C.c_int,W.UINT]
U.CreateWindowExW.argtypes=[W.DWORD,W.LPCWSTR,W.LPCWSTR,W.DWORD,C.c_int,C.c_int,C.c_int,C.c_int,W.HWND,W.HMENU,W.HINSTANCE,W.LPVOID]
U.CreateWindowExW.restype=W.HWND
def windows(pid):
    result=[]
    @CB
    def cb(h,_):
        p=W.DWORD();U.GetWindowThreadProcessId(h,C.byref(p))
        if p.value==pid and U.IsWindowVisible(h):
            title=C.create_unicode_buffer(256);U.GetWindowTextW(h,title,256);result.append((h,title.value))
        return True
    U.EnumWindows(cb,0);return result
def cpu(p):
    t=[W.FILETIME() for _ in range(4)]
    assert K.GetProcessTimes(W.HANDLE(int(p._handle)),*[C.byref(x) for x in t])
    return sum((x.dwHighDateTime<<32|x.dwLowDateTime)*1e-7 for x in t[2:])
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--build',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--headless',action='store_true');ap.add_argument('--case',choices=['normal','paused','modal','fast','ultra','hosted'])
    ap.add_argument('--debug-captures',action='store_true')
    a=ap.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);build=a.build.resolve();rows=[]
    for case in [a.case] if a.case else ['normal','paused','modal','fast','ultra','hosted']:
        d=out/case;d.mkdir();assets=d/'a';shutil.copytree(build/'runtime-assets',assets)
        fixture='windows-quick.txt' if case=='hosted' else 'full-game-vga.txt'
        lines=(ROOT/'portable/tests/runtime'/fixture).read_text().splitlines()
        if case in ('paused','fast','ultra'):
            key={'paused':'0','fast':'3','ultra':'4'}[case]
            lines += ['16000 down Left Shift',f'16010 down {key}',f'16050 up {key}','16060 up Left Shift']
        if case=='modal':lines+=['16000 down Left Ctrl','16010 down S','16050 up S','16060 up Left Ctrl']
        # Checkpoints are machine time, not wall time; Ultra is sampled using
        # external GetProcessTimes even when these checkpoints race ahead.
        lines += [f'{t} checkpoint' for t in (15000,18000,21000,24000,27000,30000)]
        finish=34000 if case=='normal' else 23000
        # Responses use SDL's input boundary, scheduled independently of
        # simulation speed and Windows foreground-activation permissions.
        if case in ('modal','ultra'):lines+=['22000 down Escape','22050 up Escape']
        if a.debug_captures:lines+=['21500 down F12','21550 up F12','23500 down F12','23550 up F12']
        lines += [f'{finish} quit',f'{finish+1000} down Return',f'{finish+1050} up Return',
                  f'{finish+2000} down Return',f'{finish+2050} up Return',f'{finish+7000} exit']
        lines=[l for l in lines if l and not l.startswith('#')];lines.sort(key=lambda l:int(l.split()[0]))
        script=d/'input.txt';script.write_text('# clock: host-ms\n'+'\n'.join(lines)+'\n')
        command=[str(build/'simant-canonical.exe'),'--assets',str(assets),'--seed','1','--input-script',str(script),f'--diagnostics-dir={d/"sessions"}']
        if case=='hosted':command+=['--windows']
        if a.debug_captures:command+=['--debug']
        if a.headless:command+=['--headless']
        env=dict(os.environ,SIMANT_PACING_STATS=str(d/'stats.json'))
        row=dict(case=case,command=command,samples=[]);rows.append(row);start=time.perf_counter();focus=None
        with (d/'stderr.txt').open('w') as log:
            p=subprocess.Popen(command,stdout=log,stderr=log,env=env,cwd=ROOT)
            try:
                def until(t):
                    while p.poll() is None and time.perf_counter()-start<t:time.sleep(.02)
                def sample(label,seconds=3):
                    t=time.perf_counter();c=cpu(p);until(t-start+seconds);elapsed=time.perf_counter()-t
                    row['samples'].append(dict(phase=label,wall_s=elapsed,cpu_s=cpu(p)-c,one_core_percent=100*(cpu(p)-c)/elapsed))
                until(3)
                row['windows']=windows(p.pid)
                if case=='normal':sample('title',2)
                if case=='ultra':
                    until(16.1);sample('ultra-active',.2)
                until(18);sample(case)
                # Owned popups can also be titled SimAnt. Keep the root HWND
                # observed before the game opens any hosted windows/dialogs.
                h=next((h for h,t in row['windows'] if t=='SimAnt'),None)
                if case=='normal' and h:
                    focus=U.CreateWindowExW(0,'STATIC','Desktop audit focus target',0x10cf0000,20,20,300,200,None,None,None,None)
                    row['focus_target_created']=bool(focus)
                    row['focus_change_return']=bool(U.SetForegroundWindow(focus)) if focus else False
                    sample('unfocused');U.ShowWindow(h,6);sample('minimized');U.ShowWindow(h,9);sample('restored')
                    U.SetWindowPos(h,None,30,30,400,330,0x14);sample('small-window',1)
                    U.ShowWindow(h,3);sample('maximized',1);U.ShowWindow(h,9)
                # Dismiss the Save filename modal before testing Quit. Paused
                # and speed modes need no extra state mutation to close.
                def key(vk,scan):
                    U.PostMessageW(h,0x100,vk,1|(scan<<16));time.sleep(.08)
                    U.PostMessageW(h,0x101,vk,1|(scan<<16)|(3<<30))
                if h:
                    if case=='modal':key(0x1b,1);time.sleep(.3)
                    t=time.perf_counter()
                    if case=='fast':
                        row['quit_origin']='Alt+F4 window message'
                        U.PostMessageW(h,0x104,0x12,1|(0x38<<16));time.sleep(.08)
                        U.PostMessageW(h,0x104,0x73,1|(0x3e<<16)|(1<<29))
                        time.sleep(.08)
                        U.PostMessageW(h,0x105,0x73,1|(0x3e<<16)|(1<<29)|(3<<30))
                        U.PostMessageW(h,0x105,0x12,1|(0x38<<16)|(3<<30))
                    elif case=='paused':
                        row['quit_origin']='game Ctrl+Q'
                        U.PostMessageW(h,0x100,0x11,1|(0x1d<<16));key(ord('Q'),0x10)
                        U.PostMessageW(h,0x101,0x11,1|(0x1d<<16)|(3<<30))
                    else:
                        row['quit_origin']='WM_CLOSE'
                        U.PostMessageW(h,0x10,0,0)
                    time.sleep(.6)
                    row['alive_for_game_quit_prompt']=p.poll() is None
                    # The original quit prompt defaults to DON'T SAVE.
                    for _ in range(1):
                        if p.poll() is not None:break
                        key(0x0d,0x1c);time.sleep(.5)
                    logs=list((d/'sessions').glob('*/session.log'))
                    row['close_request_before_script_fallback']=bool(logs and 'close_request=' in logs[0].read_text(errors='replace'))
                    try:p.wait(timeout=10)
                    except subprocess.TimeoutExpired:row['quit_timeout']=True
                    row['shutdown_s_including_prompt_response']=time.perf_counter()-t
                else:
                    p.wait(timeout=20)
                row['exit']=p.poll()
            finally:
                if focus:U.DestroyWindow(focus)
                if p.poll() is None:p.kill();row['forced_cleanup']=True
                p.wait();row['remaining_windows']=windows(p.pid)
        if (d/'stats.json').exists():row['stats']=json.loads((d/'stats.json').read_text())
        logs=list((d/'sessions').glob('*/session.log'))
        if logs:
            text=logs[0].read_text(errors='replace')
            row['first_frame_ms_from_main']=next((l.split('=',1)[1] for l in text.splitlines() if l.startswith('first_frame_ms_from_main=')),None)
            row['script_forced_exit']='stop_reason=input replay exit' in text
        (out/'result.json').write_text(json.dumps(rows,indent=2)+'\n')
        print(case+': '+json.dumps(row['samples']),flush=True)
    assert all(not r.get('forced_cleanup') and not r.get('script_forced_exit') and not r['remaining_windows'] for r in rows),rows
    return 0
if __name__=='__main__':raise SystemExit(main())
