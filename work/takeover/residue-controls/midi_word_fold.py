from pathlib import Path
import sys,json,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_284A_0138';text=autosearch.unscaffold((ROOT/'src/root/m284A.c').read_text(),name)
f=csrc.Source(text).function(name)
out=ROOT/'build/workers/takeover/midi-word-fold';out.mkdir(exist_ok=True);vs=[]
for expr in ['SONG(off) << 8 | SONG(off + 1)','(SONG(off) << 8) + SONG(off + 1)','SONG(off) * 256 + SONG(off + 1)','SONG(off + 1) + SONG(off) * 256']:
 for check in ['SONG(off) >= 0','SONG(off) <= 255','(unsigned)SONG(off) >= 0','SONG(off + 1) >= 0','(unsigned)off >= 0']:
  for form in ['if','ternary']:
   bb='{\n    '+('if ('+check+') return '+expr+';\n    return 0;' if form=='if' else 'return ('+check+') ? ('+expr+') : 0;')+'\n}'
   vs.append(('v'+str(len(vs)),text[:f.body.s]+bb+text[f.body.e:]))
ev=autosearch.Evaluator(modctx.resolve(func=name),name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
