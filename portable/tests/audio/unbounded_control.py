"""Relink the same fresh program with ONLY the former queue policy restored.

Both source diagnostics and all render/game objects stay identical. This is a
measurement control, never a shipped mode or an alternative sound sequencer.
"""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser();p.add_argument('build',type=Path);p.add_argument('out',type=Path);a=p.parse_args();a.build=a.build.resolve();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((a.build/'report.json').read_text());row=next(x for x in r['native_services'] if x['source']=='portable/platform/sdl3/audio.c')
source=ROOT/row['source'];text=source.read_text()
for name,body in [('portable_sdl3_audio_begin','(void)a;(void)frame;return 1;'),('portable_sdl3_audio_service','(void)a;return 1;')]:
    start=text.index('int '+name+'(');at=text.index('{',start);end=at+1;depth=1
    while depth:
        depth+=(text[end]=='{')-(text[end]=='}');end+=1
    text=text[:at+1]+body+text[end-1:]
draft=a.out/'unbounded-audio.c';draft.write_text(text);obj=a.out/'unbounded-audio.o'
cmd=row['compile']['command'][:];cmd[cmd.index('-c')+1]=str(draft);cmd[cmd.index('-o')+1]=str(obj);cmd+=['-I'+str(source.parent)]
subprocess.run(cmd,check=True,capture_output=True)
response=(a.build/'application-objects.rsp').read_text().replace(Path(row['object']).as_posix(),obj.as_posix());rsp=a.out/'objects.rsp';rsp.write_text(response)
link=r['application_link']['command'][:];link=[('-Wl,@'+str(rsp)) if x=='-Wl,@application-objects.rsp' else x for x in link];exe=a.out/'simant-canonical.exe';link[link.index('-o')+1]=str(exe)
run=subprocess.run(link,cwd=a.build,capture_output=True,text=True);(a.out/'link.log').write_text(run.stdout+run.stderr);run.check_returncode()
for name in ('SDL3.dll','simant-build-id.txt'):shutil.copyfile(a.build/name,a.out/name)
shutil.copytree(a.build/'runtime-assets',a.out/'runtime-assets');shutil.copytree(a.build/'runtime-bios-fonts',a.out/'runtime-bios-fonts')
# The game checks the adjacent identity. This receipt describes the relinked
# control accurately instead of borrowing the production executable hash.
identity=a.out/'simant-build-id.txt';lines=identity.read_text().splitlines();lines=[('executable_sha256='+sha(exe)) if x.startswith('executable_sha256=') else x for x in lines];identity.write_text('\n'.join(lines)+'\n')
receipt=dict(base_build=str(a.build),base_report_sha256=sha(a.build/'report.json'),source_sha256=sha(source),draft_sha256=sha(draft),executable_sha256=sha(exe),compile=cmd,link=link,changes='Presentation begin/service are no-ops; original four-period silent priming and first-block start/unbounded append remain. All source events, observer hooks, renderer and game objects are identical.')
(a.out/'control.json').write_text(json.dumps(receipt,indent=2)+'\n');print('unbounded control',exe)
