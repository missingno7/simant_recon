from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='DrawBalloons';text=(ROOT/'build/workers/takeover/balloons-repeated-size.c').read_text();f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/balloons-folded-pointer-reads';out.mkdir(exist_ok=True);vs=[]
for mask in range(16):
 bb=b
 if mask&1:bb=bb.replace('        pic = (int far *)f_171C_1B84(h);','        pic = (int far *)f_171C_1B84(h);\n        if ((unsigned)((unsigned long)pic >> 16) < 0) continue;')
 if mask&2:bb=bb.replace('        by = pos.y', '        if ((unsigned)*(unsigned near *)&pic < 0) continue;\n        by = pos.y',1)
 if mask&4:bb=bb.replace('        bufp = balBufPtr;', '        bufp = balBufPtr;\n        if ((unsigned)((unsigned long)bufp >> 16) < 0) continue;')
 if mask&8:bb=bb.replace('        pos = fd_50F6_04C8[i];', '        if ((unsigned)i < 0) continue;\n        pos = fd_50F6_04C8[i];')
 vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:8]])
