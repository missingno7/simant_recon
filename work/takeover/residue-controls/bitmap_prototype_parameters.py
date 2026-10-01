from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx,srcrules as R
name='win_DrawBitMap';text=(ROOT/'build/workers/takeover/bitmap-original-order.c').read_text();out=ROOT/'build/workers/takeover/bitmap-prototype-parameters';out.mkdir(exist_ok=True)
moves=[m for m in R.r_proto_names(R.Ctx(text,name)) if m.site.endswith('unnamed')]
vs=[text];meta=[[]]
for i,m in enumerate(moves):
 vs.append(R.apply_move(text,m));meta.append([i])
for i in range(2,len(moves)+1):
 vs.append(R.apply_edits(text,[e for m in moves[:i] for e in m.edits]));meta.append(list(range(i)))
for indexes in itertools.combinations(range(len(moves)),2):
 vs.append(R.apply_edits(text,[e for i in indexes for e in moves[i].edits]));meta.append(list(indexes))
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}','meta':meta[i],**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('moves',len(moves),'variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:8]])
