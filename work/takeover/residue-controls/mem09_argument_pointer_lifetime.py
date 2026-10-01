from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='f_171C_09CC';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/mem09-argument-pointer-lifetime';out.mkdir(exist_ok=True);vs=[];meta=[]
for view,form,first in itertools.product(['(unsigned long)b','(unsigned)OFF(b)','(unsigned)SEG(b)'],['false','true','return','return_comma'],[False,True]):
 bb=b.replace('f_171C_068C(f_171C_0160(b, 0), paras, type);','f_171C_068C(b = f_171C_0160(b, 0), paras, type);')
 if first:bb=bb.replace('b->paras > paras','(unsigned)paras >= 0 && b->paras > paras')
 if form=='false':bb=bb.replace('    return 1;\n}', '    if ('+view+' < 0) return 0;\n    return 1;\n}')
 elif form=='true':bb=bb.replace('    return 1;\n}', '    if ('+view+' >= 0) {}\n    return 1;\n}')
 elif form=='return':bb=bb.replace('    return 1;\n}', '    return '+view+' >= 0;\n}')
 else:bb=bb.replace('    return 1;\n}', '    return ('+view+', 1);\n}')
 vs.append(text[:f.body.s]+bb+text[f.body.e:]);meta.append([view,form,first])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}','meta':meta[i],**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('meta'),r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:10]])
