from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='InvertPatch';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/invert-product-reads';out.mkdir(exist_ok=True);vs=[]
sx='(unsigned)(x * 28) >= 0';sy='(unsigned)(y * 10) >= 0'
for mask,assoc in itertools.product(range(32),[False,True]):
 bb=b
 if assoc:bb=bb.replace('org.h = x * 28 - y * 10 + fd_50F6_10D2.left;', 'org.h = x * 28 + (fd_50F6_10D2.left - y * 10);')
 guard=[]
 if mask&1:guard.append(sx)
 if mask&2:guard.append(sy)
 if guard:bb=bb.replace('    org.h =', '    if ('+' && '.join(guard)+') org.h =',1)
 if mask&4:bb=bb.replace('    org.v =', '    if ('+sy+') org.v =',1)
 if mask&8:bb=bb.replace('if (g_3DB2 == 320)', 'if ('+sx+' && g_3DB2 == 320)')
 if mask&16:bb=bb.replace('i < 4;', 'i < 4 && '+sx+' && '+sy+';')
 vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:10]])
