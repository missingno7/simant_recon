from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='SpiderScan';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/spiderscan-counter-dependency';out.mkdir(exist_ok=True);vs=[]
for expr in ['r','(unsigned)r < 0','(unsigned)r > 65535U','(unsigned long)r < 0','r & 0','r ^ r','r - r','r * 0','r % 1','r / 32768UL','((unsigned)r >= 0) - 1','((unsigned)r <= 65535U) - 1']:
 for source in ['original','statement','chain']:
  bb=b.replace('for (pass = 0;', 'for (pass = ('+expr+');')
  if source=='statement':bb=bb.replace('int r = 0;', 'int r;').replace('    for (pass', '    r = 0;\n    for (pass',1)
  elif source=='chain':bb=bb.replace('int r = 0;', 'int r;').replace('pass = ('+expr+')', 'pass = (r = 0, '+expr+')',1)
  vs.append(('v'+str(len(vs)),base[:f.body.s]+bb+base[f.body.e:]))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
