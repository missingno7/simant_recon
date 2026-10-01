from pathlib import Path
import sys,json,itertools,re
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='DisplayCard';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/card-address-storage';out.mkdir(exist_ok=True);vs=[];meta=[]
for typ,reuse,order in itertools.product(['pointer','long','unsigned long'],[False,True],[False,True]):
 bb=b
 if typ!='pointer':
  bb=bb.replace('    char far *base;', '    '+typ+' base;').replace('base = f_171C_1B84(h1);', 'base = ('+typ+')f_171C_1B84(h1);').replace('off + base','off + (char far *)base')
 if reuse:
  bb=bb.replace('    long size;', '    union { long length; char far *cursor; } state;')
  at=bb.index('    off = 4;');bb=bb[:at]+re.sub(r'\bsize\b','state.length',bb[at:])
  title='for (q = p; *q; q++)\n            if (*q == \'_\')\n                *q = \' \';';assert title in bb
  bb=bb.replace(title,re.sub(r'\bq\b','state.cursor',title))
 if order:bb=bb.replace('off + '+('(char far *)base' if typ!='pointer' else 'base'), ('(char far *)base' if typ!='pointer' else 'base')+' + off')
 vs.append(text[:f.body.s]+bb+text[f.body.e:]);meta.append([typ,reuse,order])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}','meta':meta[i],**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('meta'),r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:10]])
