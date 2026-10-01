from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx,srcrules as R
name='o10_35F5_0384';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);out=ROOT/'build/workers/takeover/s10-prototype-parameters';out.mkdir(exist_ok=True)
cx=R.Ctx(text,name);moves=[m for m in list(R.r_proto_names(cx))+list(R.r_sym_names(cx)) if m.site.endswith('unnamed')];vs=[text];meta=[[]]
for i,m in enumerate(moves):vs.append(R.apply_move(text,m));meta.append([i])
for i in range(2,len(moves)+1):vs.append(R.apply_edits(text,[e for m in moves[:i] for e in m.edits]));meta.append(list(range(i)))
for ids in itertools.combinations(range(len(moves)),2):vs.append(R.apply_edits(text,[e for i in ids for e in moves[i].edits]));meta.append(list(ids))
ev=autosearch.Evaluator(ctx,name,8,out/'cache');rows=[];print('moves',len(moves),'planned',len(vs),flush=True)
for start in range(0,len(vs),30):
 for i,(t,r) in enumerate(zip(vs[start:start+30],ev.many(vs[start:start+30])),start):
  (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}','meta':meta[i],**r})
 ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));best=min((r for r in rows if r.get('score')),key=lambda r:r['score']);print('done',len(rows),'best',best['name'],best.get('score'),'exact',sum(bool(r.get('all_exact')) for r in rows),flush=True)
 if any(r.get('all_exact') for r in rows):break
