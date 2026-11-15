"""Phase 0 contracts and strict expected failures for phase 1/3 presentation fixes."""
import argparse, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from portable.tests.enhanced.common import ROOT, check_build, probe_link

def run_case(build,exe,out,name,script,smoke,mode=None):
    target=out/name;target.mkdir()
    scratch=ROOT/'build/scratch/enhanced';scratch.mkdir(parents=True,exist_ok=True)
    env={k:v for k,v in os.environ.items() if not k.startswith(('SIMANT_ENHANCED','SIMANT_TEST_'))}
    if mode:env.update(SIMANT_ENHANCED_CONTRACTS='1',SIMANT_ENHANCED_TEST=mode)
    with tempfile.TemporaryDirectory(prefix='a',dir=scratch) as folder:
        assets=Path(folder);shutil.copytree(build/'runtime-assets',assets,dirs_exist_ok=True)
        command=[str(exe),'--headless','--deterministic','--windows','--seed','0','--assets',str(assets),
                 '--input-script',str(script),'--smoke-ms',str(smoke),'--frame',str(target/'frame.bmp'),
                 '--diagnostics-dir',str(target/'diagnostics')]
        process=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,timeout=180)
    log=process.stdout.decode(errors='replace')+process.stderr.decode(errors='replace')
    (target/'run.log').write_text(log)
    rows=re.findall(r'^ENHANCED_PROBE (.*)$',log,re.M)
    if process.returncode or not rows or 'Source-main smoke frame captured;' not in log:
        raise RuntimeError('Incomplete regression '+name+'; see '+str(target/'run.log'))
    return json.loads(rows[-1])

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--build',type=Path,default=ROOT/'build/current/portable')
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();build=a.build.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    check_build(build);exe=probe_link(build,out/'test-build')
    fixtures=ROOT/'portable/tests/runtime'
    first=out/'first-click.txt'
    rows=(fixtures/'windows-caste.txt').read_text().splitlines()
    first.write_text('\n'.join(line for line in rows if line.startswith('#') or int(line.split()[0])<17000)+'\n')
    birth=run_case(build,exe,out,'rebirth',Path(__file__).with_name('rebirth.txt'),40000)
    click=run_case(build,exe,out,'activation',first,16800)
    control=run_case(build,exe,out,'two-click-control',fixtures/'windows-caste.txt',17800)
    executor=run_case(build,exe,out,'executor',fixtures/'windows-quick.txt',19500,'executor')
    # Failure to reach the actual bug is an ERROR, never an expected failure.
    if not birth['occupied'] or not birth['rendered'] or not birth['music_enabled']:
        raise RuntimeError('Music-enabled rebirth null-bank occupied-cell precondition not reached')
    if control['manual_events']!=1 or control['caste_auto']!=0:raise RuntimeError('Two-click positive control failed')
    regressions=[dict(id='music-enabled-rebirth',phase=1,desired='Occupied life cells retain entity imagery with null canonical banks',
        observed=birth,status='XFAIL' if birth['missing'] else 'XPASS'),
        dict(id='first-activation-click',phase=3,desired='One inactive-panel click invokes Manual exactly once',
        observed=click,status='XFAIL' if click['manual_events']!=1 or click['caste_auto']!=0 else 'XPASS')]
    checks={'two_click_control':True,'executor_delivers_once_after_flush':executor['submitted']==1 and executor['delivered']==1 and
        executor['manual_events']==1 and executor['caste_auto']==0 and executor['prepared']==1 and executor['flush_completed']==1,
        'duplicate_is_refused':executor['duplicate_result']==3}
    result=dict(passed=all(checks.values()) and all(x['status']=='XFAIL' for x in regressions),regressions=regressions,
        checks=checks,executor=executor,executable=str(exe))
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    return int(not result['passed'])
if __name__=='__main__':raise SystemExit(main())
