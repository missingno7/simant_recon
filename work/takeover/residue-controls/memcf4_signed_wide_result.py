from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='f_171C_0CF4';base=autosearch.unscaffold((ROOT/'src/root/m171C.c').read_text(),name);f=csrc.Source(base).function(name);s=(ROOT/'build/workers/takeover/memcf4-result-lifetime/v6.c').read_text();sf=csrc.Source(s).function(name);b=s[sf.body.s:sf.body.e];out=ROOT/'build/workers/takeover/memcf4-signed-wide-result';out.mkdir(exist_ok=True);vs=[]
for ty,read,initial in itertools.product(['long','unsigned long'],['int near','unsigned near','int far','unsigned far'],[False,True]):
 bb=b.replace('    unsigned long moved;', '    '+ty+' moved;').replace('*(int near *)&moved', '*('+read+' *)&moved')
 if initial:bb=bb.replace('moved = 0;', 'moved = (unsigned)emsOnly < 0;')
 vs.append(base[:f.body.s]+bb+base[f.body.e:])
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:8]])
