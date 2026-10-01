from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='f_171C_09CC';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/mem09-pointer-lifetime';out.mkdir(exist_ok=True);vs=[];meta=[]
for view,position,form in itertools.product(['(unsigned long)b','(unsigned)OFF(b)','(unsigned)SEG(b)'],['before','after','first'],['false','true','return','return_comma']):
 bb=b.replace('    f_171C_068C(f_171C_0160(b, 0), paras, type);','    b = f_171C_0160(b, 0);\n    f_171C_068C(b, paras, type);')
 if form=='false':guard='    if ('+view+' < 0) return 0;\n'
 elif form=='true':guard='    if ('+view+' >= 0) {}\n'
 elif form=='return':guard='    return '+view+' >= 0;\n'
 else:guard='    return ('+view+', 1);\n'
 if form.startswith('return'):bb=bb.replace('    return 1;\n}',guard+'}')
 elif position=='before':bb=bb.replace('    f_171C_068C(b, paras, type);',guard+'    f_171C_068C(b, paras, type);')
 elif position=='after':bb=bb.replace('    f_171C_068C(b, paras, type);','    f_171C_068C(b, paras, type);\n'+guard)
 else:bb=bb.replace('    b = HDR(h);','    b = HDR(h);\n'+guard)
 vs.append(text[:f.body.s]+bb+text[f.body.e:]);meta.append([view,position,form])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}','meta':meta[i],**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('meta'),r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:10]])
