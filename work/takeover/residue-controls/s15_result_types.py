from pathlib import Path
import sys,json,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='o15_384C_0239';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name);f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/s15-result-types';out.mkdir(exist_ok=True);vs=[]
for typ,ret in itertools.product(['int','unsigned','long','unsigned long','signed char','unsigned char','register unsigned','register long'],['plain','word','low_lvalue']):
 bb=b.replace('int result;',typ+' result;')
 if ret=='word':bb=bb.replace('return result;', 'return (int)result;')
 if ret=='low_lvalue' and typ not in ['signed char','unsigned char']:bb=bb.replace('return result;', 'return *(int near *)&result;')
 if ret=='low_lvalue' and typ in ['signed char','unsigned char']:continue
 n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],typ,ret))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,meta,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
