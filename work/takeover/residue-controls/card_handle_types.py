from pathlib import Path
import sys,json,itertools,re
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='DisplayCard';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);out=ROOT/'build/workers/takeover/card-handle-types';out.mkdir(exist_ok=True);vs=[];meta=[]
for typ,typedef,raw in itertools.product(['char far * far *','void far * far *'],['none','top','near_prototype'],['char far *','void far *']):
 t=text;ht='CardHandle' if typedef!='none' else typ
 if typedef!='none':
  declaration='typedef '+typ+' CardHandle;\n'
  if typedef=='top':t=declaration+t
  else:t=t.replace('extern char far * far f_1A53_00F0',declaration+'extern char far * far f_1A53_00F0')
 t=t.replace('extern char far * far f_1A53_00F0','extern '+ht+' far f_1A53_00F0')
 t=t.replace('extern char far * far f_171C_1B84(char far *handle);','extern '+raw+' far f_171C_1B84('+ht+' handle);')
 t=t.replace('f_171C_1BBA(char far *handle);','f_171C_1BBA('+ht+' handle);').replace('f_171C_1C1C(char far *handle);','f_171C_1C1C('+ht+' handle);')
 for variable in ['h1','h2','hText','hStyl']:t=t.replace('char far *'+variable+';',ht+' '+variable+';')
 vs.append(t);meta.append([typ,typedef,raw])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}','meta':meta[i],**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('meta'),r.get('score'),r.get('length')) for r in rows])
