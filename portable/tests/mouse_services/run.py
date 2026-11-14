"""Controls for the corpus mouse-service investigations; no oracle replacement."""
import argparse,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--build',type=Path,default=ROOT/'build/current/portable')
 p.add_argument('--out',type=Path,default=ROOT/'build/current/tests/mouse-services')
 a=p.parse_args();b=a.build.resolve();out=a.out.resolve()
 report=json.loads((b/'report.json').read_text())
 if not report['passed']:raise ValueError('fresh successful native build required')
 if out.exists():raise ValueError('explicit control output must be fresh')
 out.mkdir(parents=True)
 row=next(r for r in report['canonical_TUs'] if r['source']=='src/ui/view_dialog_helpers.c')
 if hashlib.sha256((ROOT/row['source']).read_bytes()).hexdigest()!=report['input_pins'][row['source']]:
  raise ValueError('canonical edge source changed; rebuild')
 # Compile the unchanged generated function with controlled services. Keep the
 # body as an artifact so the control is inspectable without this conversation.
 text=Path(row['generated']).read_text()
 anchor='void ui_pump_events_edge_scroll(int16_t portable_event_incoming_si)\n{'
 if text.count(anchor)!=1:raise ValueError('canonical edge body is not unique')
 start=text.index(anchor);at=text.index('{',start);depth=1;end=at+1
 while depth:
  depth+=(text[end]=='{')-(text[end]=='}');end+=1
 body=text[start:end]
 source=out/'edge-control.c'
 source.write_text((HERE/'edge_phase.c').read_text()+'\n'+body+'\n')
 exe=out/'edge-phase.exe'
 cmd=[row['compile']['command'][0],'-std=c11','-Wall','-Wextra','-Werror',str(source),'-o',str(exe)]
 run=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
 (out/'compile.txt').write_text(run.stdout+run.stderr)
 if run.returncode:raise RuntimeError(run.stderr)
 run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15)
 (out/'report.json').write_text(json.dumps(dict(passed=run.returncode==0,compile=cmd,generated=row['generated'],
   generated_sha256=hashlib.sha256(text.encode()).hexdigest(),body=body,
   body_sha256=hashlib.sha256(body.encode()).hexdigest(),output=run.stdout+run.stderr,
   scope='Actual converted canonical edge branch with controlled interrupt placement and interior-pointer negative control. This demonstrates an admission ambiguity, not a production fix.'),indent=2)+'\n')
 print(run.stdout+run.stderr,end='')
 return run.returncode
if __name__=='__main__':raise SystemExit(main())
