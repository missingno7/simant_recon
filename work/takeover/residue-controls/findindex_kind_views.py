from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='FindIndex';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/findindex-kind-views';out.mkdir(exist_ok=True);vs=[]
for field,view in itertools.product(['byte','word','signed_word'],['byte','masked_word']):
 prefix=text[:f.head_s];head=text[f.head_s:f.body.s]
 if field!='byte':prefix=prefix.replace('    unsigned char kind;\n    unsigned char spare;', '    '+('unsigned' if field=='word' else 'int')+' kind;')
 value='(*(unsigned char far *)&fd_50F6_3952->kind)' if view=='byte' else '((*(unsigned far *)&fd_50F6_3952->kind) & 255)'
 bb=b.replace('fd_50F6_3952->kind',value)
 vs.append(prefix+head+bb+text[f.body.e:])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in rows])
