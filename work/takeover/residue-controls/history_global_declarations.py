from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx,srcrules as R
name='drawHistGraph';ctx=modctx.resolve(func=name);out=ROOT/'build/workers/takeover/history-global-declarations';out.mkdir(exist_ok=True);vs=[];meta=[]
for base in ['history-state-lifetimes/v13.c','history-full-word-reads/v12.c']:
 text=(ROOT/'build/workers/takeover'/base).read_text();moves=[m for m in R.r_proto_names(R.Ctx(text,name)) if m.site.endswith('unnamed')]
 for starttype,k in itertools.product(['int','unsigned','unsigned short'],range(len(moves)+1)):
  t=text
  # Only prototype identifiers change; all declarations remain genuine.
  if k:t=R.apply_edits(t,[e for m in moves[:k] for e in m.edits])
  t=t.replace('extern int far fd_50F6_04F4;', 'extern '+starttype+' far fd_50F6_04F4;')
  vs.append(t);meta.append([base,starttype,k])
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for start in range(0,len(vs),24):
 for i,(t,r) in enumerate(zip(vs[start:start+24],ev.many(vs[start:start+24])),start):
  (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}','meta':meta[i],**r})
 ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('done',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows),flush=True)
print([(r['name'],r.get('meta'),r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:8]])
