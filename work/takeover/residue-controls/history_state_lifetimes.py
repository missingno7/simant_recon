from pathlib import Path
import sys,json,itertools,re
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='drawHistGraph';text=autosearch.unscaffold((ROOT/'src/S24/m39C7.c').read_text(),name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/history-state-lifetimes';out.mkdir(exist_ok=True);vs=[]
for size,inline,order,last in itertools.product([20,30],range(4),[False,True],[False,True]):
 bb=b.replace('buf[30]',f'buf[{size}]')
 if inline&1:
  bb=bb.replace('    int start;\n','').replace('    start = fd_50F6_04F4;\n','');bb=re.sub(r'\bstart\b','fd_50F6_04F4',bb)
 if inline&2:
  bb=bb.replace('    int count;\n','').replace('    count = fd_3D57_0828;\n','');bb=re.sub(r'\bcount\b','fd_3D57_0828',bb)
 if order:bb=bb.replace('n < '+('fd_3D57_0828' if inline&2 else 'count'),('fd_3D57_0828' if inline&2 else 'count')+' > n')
 if last:bb=bb.replace('    f_1CE2_01F8(x - 1, ty - 1, f_24AB_0329(s) + x + 1, ty + th + 1, 1);','    width = f_24AB_0329(s);\n    f_1CE2_01F8(x - 1, ty - 1, width + x + 1, ty + th + 1, 1);')
 vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:6]])
