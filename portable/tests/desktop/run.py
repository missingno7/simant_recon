"""Native desktop boundary: real SDL mapping, physical keyboard, storage errors.

Every child is bounded and reaped. Creates only the requested fresh output.
"""
from pathlib import Path
import argparse, subprocess, shutil, json, os, ctypes, struct
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--build',type=Path,help='also exercise current application Quit/Cancel and unavailable diagnostics')
    ap.add_argument('--sdk',type=Path,default=ROOT/'build/deps/sdl3-sdk/SDL3-3.4.16/x86_64-w64-mingw32')
    args=ap.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False);sdk=args.sdk.resolve()
    base=['C:/msys64/mingw64/bin/gcc.exe','-std=c11','-Wall','-Wextra','-Werror','-I',str(ROOT),'-I',str(sdk/'include')]
    platform=ROOT/'portable/whole_program/platform';results=[]
    for name,sources in [('host',[HERE/'host.c',platform/'sdl3/host.c']),('write',[HERE/'write.c',platform/'drive_directory.c']),('files',[HERE/'files.c',platform/'desktop_files.c'])]:
        command=base+list(map(str,sources))+['-L',str(sdk/'lib'),'-lSDL3','-o',str(out/(name+'.exe'))]
        r=subprocess.run(command,capture_output=True,text=True,timeout=60)
        (out/(name+'-compile.txt')).write_text(r.stdout+r.stderr)
        if r.returncode: raise RuntimeError(r.stderr)
    shutil.copy2(sdk/'bin/SDL3.dll',out/'SDL3.dll')
    def run(name,command,expected=0):
        r=subprocess.run(list(map(str,command)),capture_output=True,text=True,timeout=30)
        results.append(dict(name=name,code=r.returncode,expected=expected,stdout=r.stdout,stderr=r.stderr))
        (out/'result.json').write_text(json.dumps(results,indent=2)+'\n')
        assert r.returncode==expected,results[-1]
    run('mapping-headless',[out/'host.exe']);run('mapping-windowed',[out/'host.exe','--windowed']);run('disk-full',[out/'write.exe'])
    assets=out/'assets';build=(args.build or ROOT/'build/current/portable').resolve()
    shutil.copytree(build/'runtime-assets',assets)
    before={p.name:p.read_bytes() for p in assets.iterdir()}
    # Distribution files can be read-only: default storage lives elsewhere.
    for p in assets.iterdir():os.chmod(p,0o444)
    try:
        run('read-only-distribution',[out/'files.exe',assets,'0',out/'user'])
        volume=Path(results[-1]['stdout'].strip());assert (volume/'SIMANT.CFG').exists()
        cfg=volume/'SIMANT.CFG';cfg.write_text('Display Mode: V\nSound Mode: 0\n')
        save=volume/'A.ANT';save.write_bytes(b'player-owned save')
        run('retain-user-files',[out/'files.exe',assets,'0',out/'user'])
        assert cfg.read_text()=='Display Mode: V\nSound Mode: 0\n' and save.read_bytes()==b'player-owned save'
        assert before=={p.name:p.read_bytes() for p in assets.iterdir()}
    finally:
        for p in assets.iterdir():os.chmod(p,0o666)
    blocked=out/'blocked';blocked.write_text('not a directory')
    run('unwritable-user-root',[out/'files.exe',assets,'0',blocked],70)
    (assets/'SIMANT.CFG').write_text('x'*100)
    run('corrupt-config',[out/'files.exe',assets,'1',out/'user'],70)
    (assets/'SIMANT.CFG').write_bytes(before['SIMANT.CFG'])
    (assets/'SOUND.NDX').write_bytes(b'corrupt')
    run('corrupt-asset',[out/'files.exe',assets,'1',out/'user'],70)
    (assets/'SOUND.NDX').unlink()
    run('missing-asset',[out/'files.exe',assets,'1',out/'user'],70)
    if args.build:
        # No user profile writes or interactive prompts in an automated run.
        game_assets=out/'game-assets';shutil.copytree(build/'runtime-assets',game_assets)
        exe=build/'simant-canonical.exe'
        run('unavailable-diagnostics',[exe,'--headless','--assets',game_assets,'--smoke-ms','1000',f'--diagnostics-dir={blocked}'])
        assert 'could not write its diagnostic log' in results[-1]['stderr']
        recipe=out/'quit.txt'
        recipe.write_text((ROOT/'portable/tests/runtime/full-game-vga.txt').read_text()+
            '\n16000 quit\n17000 down F12\n17050 up F12\n18000 down Escape\n18050 up Escape\n'
            '19000 down F12\n19050 up F12\n20000 quit\n21000 down Return\n21050 up Return\n')
        sessions=out/'sessions'
        run('quit-cancel-discard',[exe,'--headless','--deterministic','--debug','--assets',game_assets,
            '--seed','1','--smoke-ms','23000','--input-script',recipe,f'--diagnostics-dir={sessions}'])
        session=next(sessions.glob('simant-*'));log=(session/'session.log').read_text()
        assert 'stop_reason=source/platform exit' in log and log.count('close_request=')==2
        def pixel(p,x,y):
            b=p.read_bytes();offset=struct.unpack_from('<I',b,10)[0];w,h=struct.unpack_from('<ii',b,18)
            assert (w,abs(h))==(640,480)
            i=offset+((abs(h)-1-y if h>0 else y)*w+x)*4
            return tuple(b[i:i+3])
        prompt=session/'capture-0001/screenshot.bmp';cancelled=session/'capture-0002/screenshot.bmp'
        assert pixel(prompt,450,180)==(195,195,195) and pixel(cancelled,450,180)!=(195,195,195)
    print('PASS desktop boundaries: '+str(len(results))+' checks')
if __name__=='__main__':main()
