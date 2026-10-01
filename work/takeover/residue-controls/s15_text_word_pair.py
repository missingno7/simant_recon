from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='o15_384C_0239';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/s15-text-word-pair';out.mkdir(exist_ok=True);vs=[]
for typ,read,init in itertools.product(['long','unsigned long','union'],['cast','lvalue'],[False,True]):
 if typ=='union':
  decl='union { unsigned long bits; char far *ptr; } text;';lhs='text.ptr';value='text.ptr' if read=='cast' else '*(char far * near *)&text'
  bb=b.replace('char far *text;',decl)
 else:
  bb=b.replace('char far *text;',typ+' text;');lhs='text';value='(char far *)text' if read=='cast' else '*(char far * near *)&text'
 bb=bb.replace('text = f_171C_1B84(h);',lhs+' = '+('('+typ+')' if typ!='union' else '')+'f_171C_1B84(h);').replace('win_PrintTextInRect(0, text, &r);','win_PrintTextInRect(0, '+value+', &r);')
 if init:
  declaration='    '+decl if typ=='union' else '    '+typ+' text;'
  bb=bb.replace(declaration+'\n','')
  bb=bb.replace('    '+lhs+' = ', '    {\n    '+declaration.strip()+'\n    '+lhs+' = ',1).replace('    f_24AB_02AD(0);','    f_24AB_02AD(0);\n    }',1)
 vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in rows])
