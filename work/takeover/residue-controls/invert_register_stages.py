from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='InvertPatch';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/invert-register-stages';out.mkdir(exist_ok=True);vs=[]
first='    org.h = x * 28 - y * 10 + fd_50F6_10D2.left;\n    org.v = y * 10 + fd_50F6_10D2.top;\n    h = x * 28 - y * 10;\n    v = y * 10;'
forms=[first,'    h = x * 28;\n    v = y * 10;\n    org.h = h - v + fd_50F6_10D2.left;\n    org.v = v + fd_50F6_10D2.top;\n    h -= v;', '    h = x * 28 - y * 10;\n    v = y * 10;\n    org.h = h + fd_50F6_10D2.left;\n    org.v = v + fd_50F6_10D2.top;', '    org.v = y * 10 + fd_50F6_10D2.top;\n    org.h = x * 28 - y * 10 + fd_50F6_10D2.left;\n    h = x * 28 - y * 10;\n    v = y * 10;']
assert first in b
for decl in ['int i, h, v;', 'int i; register int h, v;', 'int i; register int v, h;', 'register int i; int h, v;', 'int i, v; register int h;', 'int i, h; register int v;']:
 for k,form in enumerate(forms):
  for half in ['plain','split']:
   bb=b.replace('int i, h, v;',decl).replace(first,form)
   if half=='split':bb=bb.replace('h = (h >> 1) + fd_50F6_10D2.left + 4;','h >>= 1;\n        h += fd_50F6_10D2.left + 4;').replace('v = (v >> 1) + fd_50F6_10D2.top + 10;','v >>= 1;\n        v += fd_50F6_10D2.top + 10;')
   n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],decl,k,half))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
