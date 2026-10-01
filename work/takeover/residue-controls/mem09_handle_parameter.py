from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='f_171C_09CC';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/mem09-handle-parameter';out.mkdir(exist_ok=True);vs=[];meta=[]
for typ,call,cmp in itertools.product(['Handle','register Handle','volatile Handle','const Handle','char far * far *','void far *'],['nested','argument','separate'],[False,True]):
 bb=b;head=text[:f.body.s];head=head[:f.head_s]+head[f.head_s:].replace('Handle h',typ+' h')
 if typ=='void far *':bb=bb.replace('HDR(h)','HDR((Handle)h)')
 if call=='argument':bb=bb.replace('f_171C_068C(f_171C_0160(b, 0), paras, type);','f_171C_068C(b = f_171C_0160(b, 0), paras, type);')
 elif call=='separate':bb=bb.replace('f_171C_068C(f_171C_0160(b, 0), paras, type);','b = f_171C_0160(b, 0);\n    f_171C_068C(b, paras, type);')
 if cmp:bb=bb.replace('b->paras > paras','paras < b->paras').replace('b->paras < paras + 0x20','paras + 0x20 > b->paras').replace('next->paras + b->paras < paras','paras > next->paras + b->paras')
 vs.append(head+bb+text[f.body.e:]);meta.append([typ,call,cmp])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}','meta':meta[i],**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('meta'),r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:12]])
