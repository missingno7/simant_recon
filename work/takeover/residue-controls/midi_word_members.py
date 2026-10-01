from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_284A_0138';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name)
out=ROOT/'build/workers/takeover/midi-word-members';out.mkdir(exist_ok=True);vs=[]
for word in ['int','unsigned']:
 for rep in ['byte_array','fields','char_lvalue']:
  for reg in ['', 'register ']:
   for order in ['high_low','low_high']:
    if rep=='byte_array':decl=reg+'union { '+word+' value; unsigned char byte[2]; } result;';lo='result.byte[0]';hi='result.byte[1]';ret='result.value'
    elif rep=='fields':decl=reg+'union { '+word+' value; struct { unsigned char lo, hi; } byte; } result;';lo='result.byte.lo';hi='result.byte.hi';ret='result.value'
    else:decl=reg+word+' result;';lo='*(unsigned char *)&result';hi='*((unsigned char *)&result + 1)';ret='result'
    assignments=[hi+' = SONG(off);',lo+' = SONG(off + 1);']
    if order=='low_high':assignments.reverse()
    b='{\n    '+decl+'\n    '+'\n    '.join(assignments)+'\n    return '+ret+';\n}'
    vs.append(('v'+str(len(vs)),base[:f.body.s]+b+base[f.body.e:]))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
