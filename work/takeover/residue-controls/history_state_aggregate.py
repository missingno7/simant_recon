from pathlib import Path
import sys,json,itertools,re
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='drawHistGraph';text=(ROOT/'build/workers/takeover/history-state-lifetimes/v13.c').read_text();f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/history-state-aggregate';out.mkdir(exist_ok=True);vs=[]
for form,chain,order,position in itertools.product(range(4),[False,True],[False,True],[False,True]):
 bb=b.replace('    int th;', '    int th;\n    '+(['struct { int count, start; } state;','struct { int start, count; } state;','int state[2];','int state[2];'][form]))
 a,c=[('state.start','state.count'),('state.start','state.count'),('state[1]','state[0]'),('state[0]','state[1]')][form]
 bb=bb.replace('    j = (fd_50F6_04F4 - fd_3D57_0828)', '    '+a+' = fd_50F6_04F4;\n    '+c+' = fd_3D57_0828;\n    j = ('+a+' - '+c+')')
 bb=bb.replace('j = fd_50F6_04F4', 'j = '+a).replace('data[fd_50F6_04F4]', 'data['+a+']').replace('fd_3D57_0828 > n', c+' > n').replace('n < fd_3D57_0828', 'n < '+c)
 if chain:bb=bb.replace('    div = 1;\n    mul = 1;', '    div = mul = 1;')
 if order:bb=bb.replace('n * width / 64 + slot + r.left', 'width * n / 64 + r.left + slot')
 if position:
  decl='    '+(['struct { int count, start; } state;','struct { int start, count; } state;','int state[2];','int state[2];'][form])+'\n'
  bb=bb.replace(decl,'').replace('    struct Rect r;', decl+'    struct Rect r;')
 vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:8]])
