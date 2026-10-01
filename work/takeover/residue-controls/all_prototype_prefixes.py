from pathlib import Path
import sys,json
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx,srcrules as R
name,filename,series=sys.argv[1:4];ctx=modctx.resolve(func=name);text=autosearch.unscaffold(Path(filename).read_text(),name);out=ROOT/'build/workers/takeover'/series;out.mkdir(exist_ok=True)
cx=R.Ctx(text,name);moves=[m for m in list(R.r_proto_names(cx))+list(R.r_sym_names(cx)) if ' unnamed' in m.site];vs=[text];meta=[[]]
for i,m in enumerate(moves):vs.append(R.apply_move(text,m));meta.append([i])
for k in range(2,len(moves)+1):vs.append(R.apply_edits(text,[e for m in moves[:k] for e in m.edits]));meta.append(list(range(k)))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[];print('moves',len(moves),'planned',len(vs),flush=True)
for start in range(0,len(vs),24):
 for i,(t,r) in enumerate(zip(vs[start:start+24],ev.many(vs[start:start+24])),start):
  (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}','meta':meta[i],**r})
 ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('done',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows),flush=True)
 if any(r.get('all_exact') for r in rows):break
print([(r['name'],r.get('meta'),r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:8]])
