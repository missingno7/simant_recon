from pathlib import Path
import sys,json,itertools,re
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='DisplayCard';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/card-pointer-lifetimes';out.mkdir(exist_ok=True);vs=[]
for reuse,scope,order in itertools.product(['base','p','h2'],['same','block','separate'],[False,True]):
 bb=b
 if reuse!='base':bb=bb.replace('    char far *base;\n','');bb=re.sub(r'\bbase\b',reuse,bb)
 title='for (q = p; *q; q++)\n            if (*q == \'_\')\n                *q = \' \';'
 assert title in bb
 if scope!='same':
  if scope=='block':bb=bb.replace(title,'{\n            char far *q;\n            '+title+'\n        }')
  else:bb=bb.replace('    char far *q;','    char far *q;\n    char far *titleCursor;').replace(title,re.sub(r'\bq\b','titleCursor',title))
 if order:bb=bb.replace('off + '+reuse,reuse+' + off')
 vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:10]])
