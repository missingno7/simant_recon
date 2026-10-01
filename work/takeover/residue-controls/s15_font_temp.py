from pathlib import Path
import sys,json,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='o15_384C_0239';text=autosearch.unscaffold((ROOT/'src/S15/m384C.c').read_text(),name)
f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/s15-font-temp';out.mkdir(exist_ok=True);vs=[]
for resultty in ['int','register int']:
 for fontty in ['int','unsigned','register int']:
  for place in ['first','last']:
   for form in ['ternary','if']:
    bb=b.replace('int result;',resultty+' result;')
    if place=='first':bb=bb.replace('{\n','{\n    '+fontty+' font;\n',1)
    else:bb=bb.replace(resultty+' result;',resultty+' result;\n    '+fontty+' font;')
    calc='font = g_3DB2 == 0x140 ? 2 : 4;'
    if form=='if':calc='if (g_3DB2 == 0x140) font = 2; else font = 4;'
    bb=bb.replace('f_24AB_02AD(g_3DB2 == 0x140 ? 2 : 4);',calc+'\n    f_24AB_02AD(font);')
    vs.append(('v'+str(len(vs)),text[:f.body.s]+bb+text[f.body.e:]))
ev=autosearch.Evaluator(modctx.resolve(func=name),name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
