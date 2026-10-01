from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='f_284A_0138';text=autosearch.unscaffold((ROOT/'src/root/m284A.c').read_text(),name);f=csrc.Source(text).function(name);out=ROOT/'build/workers/takeover/midi-word-low-first-result';out.mkdir(exist_ok=True);vs=[]
for typ,op,low,init,fold in itertools.product(['unsigned','int','unsigned char'],['|','+','^'],['SONG(off + 1)','(unsigned)SONG(off + 1)'],[False,True],[False,True]):
 decl=typ+' high'+(' = SONG(off);' if init else ';');assign='' if init else '    high = SONG(off);\n';guard='if ((unsigned)high >= 0) ' if fold else ''
 bb='{\n    '+decl+'\n'+assign+'    '+guard+'return '+low+' '+op+' (high << 8);\n'+('    return 0;\n' if fold else '')+'}'
 vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:8]])
