from pathlib import Path
import sys,json,itertools,re
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx,srcrules as R
name='FindIndex';ctx=modctx.resolve(func=name);out=ROOT/'build/workers/takeover/findindex-type-tags';out.mkdir(exist_ok=True);vs=[];meta=[]
for base in ['findindex-bound-updates/v0.c','findindex-conditional-forms/v16.c']:
 text=(ROOT/'build/workers/takeover'/base).read_text();cx=R.Ctx(text,name);moves=[m for m in list(R.r_proto_names(cx))+list(R.r_sym_names(cx)) if ' unnamed' in m.site]
 for tags,k in itertools.product(range(8),range(len(moves)+1)):
  t=R.apply_edits(text,[e for m in moves[:k] for e in m.edits]) if k else text
  # Give existing record types real tags; no fields or declarations are invented.
  blocks=list(re.finditer(r'typedef struct \{.*?\}\s*(IndexEntry|IndexHeader|OpenDBRec);',t,re.S))
  for i,m in reversed(list(enumerate(blocks))):
   if tags & (1<<i):t=t[:m.start()]+m.group().replace('typedef struct {','typedef struct '+m.group(1)+'Record {',1)+t[m.end():]
  vs.append(t);meta.append([base,tags,k])
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[];print('planned',len(vs),flush=True)
for start in range(0,len(vs),24):
 for i,(t,r) in enumerate(zip(vs[start:start+24],ev.many(vs[start:start+24])),start):
  (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}','meta':meta[i],**r})
 ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('done',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows),flush=True)
 if any(r.get('all_exact') for r in rows):break
print([(r['name'],r.get('meta'),r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:8]])
