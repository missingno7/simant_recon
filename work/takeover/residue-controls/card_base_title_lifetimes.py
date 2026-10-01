from pathlib import Path
import sys,json,itertools,re
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='DisplayCard';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/card-base-title-lifetimes';out.mkdir(exist_ok=True);vs=[];meta=[]
title="for (q = p; *q; q++)\n            if (*q == '_')\n                *q = ' ';"
assert title in b
for basequal,reuse,cursor,order in itertools.product(['plain','volatile'],['plain','separate','union'],['q','h2'],[False,True]):
 bb=b
 if basequal=='volatile':bb=bb.replace('    char far *base;', '    char far * volatile base;')
 if reuse=='separate':
  bb=bb.replace('    char far *q;', '    char far *q;\n    char far *titleCursor;')
  bb=bb.replace(title,re.sub(r'\bq\b','titleCursor',title))
 elif reuse=='union':
  bb=bb.replace('    long size;', '    union { long length; char far *cursor; } state;')
  at=bb.index('    off = 4;');bb=bb[:at]+re.sub(r'\bsize\b','state.length',bb[at:])
  bb=bb.replace(title,re.sub(r'\bq\b','state.cursor',title))
 if cursor=='h2':
  at=bb.index('                while ((nul = _fmemchr');bb=bb[:at]+re.sub(r'\bq\b','h2',bb[at:])
  if reuse!='plain':bb=bb.replace('    char far *q;\n','')
 if order:bb=bb.replace('off + base', 'base + off')
 vs.append(text[:f.body.s]+bb+text[f.body.e:]);meta.append([basequal,reuse,cursor,order])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}','meta':meta[i],**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('meta'),r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:10]])
