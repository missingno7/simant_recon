from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='f_171C_0CF4';text=autosearch.unscaffold((ROOT/'src/root/m171C.c').read_text(),name);f=csrc.Source(text).function(name);s=(ROOT/'build/workers/takeover/memcf4-reviewed-flow/v1.c').read_text();sf=csrc.Source(s).function(name);b=s[sf.body.s:sf.body.e];out=ROOT/'build/workers/takeover/memcf4-wide-address-locals';out.mkdir(exist_ok=True);vs=[]
for mask in range(1,16):
 bb=b
 for bit,var in [(1,'seg'),(2,'end'),(4,'paras'),(8,'t')]:
  if mask&bit:bb=bb.replace('    '+('int' if var=='t' else 'unsigned')+' '+var+';', '    unsigned long '+var+';')
 vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}','meta':i+1,**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:8]])
