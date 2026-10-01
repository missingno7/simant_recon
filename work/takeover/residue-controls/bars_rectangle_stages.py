from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='DrawColonyBars';text=(ROOT/'build/workers/takeover/bars-left-stages/v0.c').read_text();f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/bars-rectangle-stages';out.mkdir(exist_ok=True)
old='                    l = (x + 6) * 28 + fd_50F6_10D2.left - y * 10;\n                    r.left = l;\n                    r.bottom = y * 10 + fd_50F6_10D2.top + 0x47;\n                    r.right = l + 9;\n                    r.top = r.bottom - h;'
vs=[]
for kind in range(5):
 heads=['                    l = (x + 6) * 28 + fd_50F6_10D2.left;\n','', '', '                    tmp2 = (x + 6) * 28 + fd_50F6_10D2.left;\n','                    l = (x + 6) * 28 + fd_50F6_10D2.left;\n']
 lefts=['                    r.left = l - y * 10;\n', '                    r.left = (x + 6) * 28 + fd_50F6_10D2.left - y * 10;\n', '                    r.left = (x + 6) * 28 + fd_50F6_10D2.left;\n                    r.left -= y * 10;\n','                    r.left = tmp2 - y * 10;\n','                    l = r.left = l - y * 10;\n']
 fields=[lefts[kind],'                    r.bottom = y * 10 + fd_50F6_10D2.top + 0x47;\n','                    r.right = '+('l' if kind==4 else 'r.left')+' + 9;\n','                    r.top = r.bottom - h;\n']
 for order in itertools.permutations(fields):
  if order.index(fields[1])>order.index(fields[3]) or order.index(fields[0])>order.index(fields[2]):continue
  bb=b.replace(old,heads[kind]+''.join(order).rstrip('\n'),1);assert bb!=b
  vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:8]])
