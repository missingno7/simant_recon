from pathlib import Path
import sys,json,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,modctx,csrc
name='f_0250_1018';text=autosearch.unscaffold((ROOT/'src/root/m0250.c').read_text(),name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/mapdraw-live-coords';out.mkdir(exist_ok=True);vs=[]
for variables in [('mx',),('my',),('mx','my')]:
 for where in ['zero','scent','mybound','last']:
  check=' && '.join('((unsigned)'+v+' >= 0)' for v in variables)
  bb=b
  if where=='zero':bb=bb.replace('if (v == 0)','if (v == 0 && '+check+')')
  elif where=='scent':bb=bb.replace('if (v > 0x10)','if (v > 0x10 && '+check+')')
  elif where=='mybound':bb=bb.replace('if (my > 0x3f)','if (my > 0x3f && '+check+')')
  else:bb=bb.replace('if (fd_50F6_04C2 < 8)','if (fd_50F6_04C2 < 8 && '+check+')')
  for ty in ['int','volatile int']:
   bc=bb.replace('    int v;', '    '+ty+' v;')
   vs.append(('v'+str(len(vs)),text[:f.body.s]+bc+text[f.body.e:]))
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
