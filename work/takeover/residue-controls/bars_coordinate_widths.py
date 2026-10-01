from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='DrawColonyBars';text=(ROOT/'build/workers/takeover/bars-left-stages/v0.c').read_text();f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/bars-coordinate-widths';out.mkdir(exist_ok=True)
old='                    r.bottom = y * 10 + fd_50F6_10D2.top + 0x47;';line='                    l = (x + 6) * 28 + fd_50F6_10D2.left - y * 10;'
prods=['(int)((long)y * 10)','(int)((unsigned long)y * 10)','(unsigned)y * 10','(int)(y * 10L)','(int)(y * 10UL)','(int)((unsigned)y * 10)','(int)((long)y * 10 + fd_50F6_10D2.top + 0x47)']
forms=[line,'                    l = (x + 6) * 28 + fd_50F6_10D2.left;\n                    l -= y * 10;', '                    tmp2 = (x + 6) * 28 + fd_50F6_10D2.left;\n                    l = tmp2 - y * 10;']
vs=[]
for prod,form,rightfirst in itertools.product(prods,forms,[False,True]):
 bottom='                    r.bottom = '+prod+';' if prod.endswith('0x47)') else old.replace('y * 10',prod)
 bb=b.replace(line,form,1).replace(old,bottom,1)
 if not rightfirst:bb=bb.replace('                    r.right = l + 9;\n                    r.top = r.bottom - h;', '                    r.top = r.bottom - h;\n                    r.right = l + 9;',1)
 vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:6]])
