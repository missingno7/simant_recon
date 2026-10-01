from pathlib import Path
import sys,json,itertools,re
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='CalcScore';text=autosearch.unscaffold((ROOT/'src/S14/m384C.c').read_text(),name)
f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/score-local-lvalues';out.mkdir(exist_ok=True);vs=[]
for var in ['j','sum2']:
 for ty in ['int','volatile int','unsigned']:
  for where in ['all','index','add','total']:
   bb=b;ref='(*('+ty+' *)&'+var+')'
   if where=='all':at=bb.index('    for (i = 0;');bb=bb[:at]+re.sub(r'\b'+var+r'\b',ref,bb[at:])
   elif where=='index':bb=bb.replace('[j]', '['+ref+']') if var=='j' else bb.replace('sum2 + sum',ref+' + sum')
   elif where=='add':bb=bb.replace(var+' +=',ref+' +=')
   else:bb=bb.replace('j = sum2 + sum','j = '+(ref+' + sum' if var=='sum2' else 'sum2 + sum')).replace('if (j > 0)','if ('+(ref if var=='j' else 'j')+' > 0)')
   vs.append(('v'+str(len(vs)),text[:f.body.s]+bb+text[f.body.e:]))
ev=autosearch.Evaluator(modctx.resolve(func=name),name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
