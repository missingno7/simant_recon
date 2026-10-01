from pathlib import Path
import sys,json,itertools,re
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='f_0250_129E';ctx=modctx.resolve(func=name);text=(ROOT/'build/workers/takeover/mapdraw-coordinate-copies/v9.c').read_text();f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/mapdraw-wide-index';out.mkdir(exist_ok=True);vs=[];meta=[]
for typ,reuse,promotion in itertools.product(['long','unsigned long'],['distinct','merge','parameter'],['word','wide_product','wide_sum']):
 bb=b.replace('    int i;', '    '+typ+' i;')
 if reuse=='merge':bb=bb.replace('    int ay;\n','');bb=re.sub(r'\bay\b','i',bb);bb=bb.replace('if (i > 0x3f)','if ((int)i > 0x3f)')
 elif reuse=='parameter':bb=bb.replace('    int ay;\n','');bb=re.sub(r'\bay\b','y',bb)
 if promotion=='wide_product':bb=bb.replace('i = screenY * 40 + x;', 'i = (long)screenY * 40 + x;')
 elif promotion=='wide_sum':bb=bb.replace('i = screenY * 40 + x;', 'i = (long)(screenY * 40) + x;')
 vs.append(text[:f.body.s]+bb+text[f.body.e:]);meta.append([typ,reuse,promotion])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}','meta':meta[i],**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('meta'),r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:8]])
