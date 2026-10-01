from pathlib import Path
import sys,json,itertools,re
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='DrawBalloons';text=(ROOT/'build/workers/takeover/balloons-repeated-size.c').read_text();f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/balloons-origin-point';out.mkdir(exist_ok=True);vs=[]
for point,early,picchar in itertools.product(['Pnt','struct { int x, y; }','struct { int y, x; }'],[False,True],[False,True]):
 bb=b.replace('    int by;\n    int bx;\n','');decl='    '+point+' origin;\n';bb=bb.replace('    Pnt pos;', decl+'    Pnt pos;' if early else '    Pnt pos;\n'+decl.rstrip('\n'))
 bb=re.sub(r'\bby\b','origin.y',bb);bb=re.sub(r'\bbx\b','origin.x',bb)
 if picchar:
  bb=bb.replace('    int far *pic;', '    char far *pic;').replace('pic = (int far *)f_171C_1B84(h);', 'pic = f_171C_1B84(h);').replace('pic[4]', '((int far *)(pic + 8))[0]').replace('pic[5]', '((int far *)(pic + 8))[1]')
 vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:8]])
