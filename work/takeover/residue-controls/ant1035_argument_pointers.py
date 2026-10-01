from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='o25_3BA4_1035';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/ant1035-argument-pointers';out.mkdir(exist_ok=True);vs=[];meta=[]
args=['fd_50F6_048C','fd_50F6_047C','fd_50F6_048A'];pointers=['planePtr','xPtr','yPtr']
for mask,reg,place in itertools.product(range(1,8),['','register '],['entry','before_if']):
 bb=b;decl=[];init=[];views=args[:]
 for i in range(3):
  if mask&(1<<i):
   decl.append('    '+reg+'int far *'+pointers[i]+';');init.append('    '+pointers[i]+' = &'+args[i]+';');views[i]='*'+pointers[i]
 bb=bb.replace('{\n','{\n'+'\n'.join(decl)+'\n\n',1)
 if place=='entry':bb=bb.replace('    f_0BE8_0EB7();','\n'.join(init)+'\n    f_0BE8_0EB7();')
 else:bb=bb.replace('    if (fd_50F6_048C == 2)', '\n'.join(init)+'\n    if (fd_50F6_048C == 2)')
 bb=bb.replace('DigMyTile('+', '.join(args)+');','DigMyTile('+', '.join(views)+');')
 vs.append(text[:f.body.s]+bb+text[f.body.e:]);meta.append([mask,reg,place])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}','meta':meta[i],**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('meta'),r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:10]])
