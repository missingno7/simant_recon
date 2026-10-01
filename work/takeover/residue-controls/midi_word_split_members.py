from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='f_284A_0138';text=autosearch.unscaffold((ROOT/'src/root/m284A.c').read_text(),name);f=csrc.Source(text).function(name);out=ROOT/'build/workers/takeover/midi-word-split-members';out.mkdir(exist_ok=True);vs=[]
for typ,view,order,fold in itertools.product(['int','unsigned','unsigned char'],['union','word'],[False,True],range(3)):
 if view=='union':decl='union { unsigned word; struct { unsigned char lo, hi; } bytes; } result;';lo='result.bytes.lo';hi='result.bytes.hi';ret='result.word'
 else:decl='unsigned result;';lo='*(unsigned char near *)&result';hi='*((unsigned char near *)&result + 1)';ret='result'
 high='high' if fold!=2 else '*(unsigned char near *)&high'
 assignments=[lo+' = SONG(off + 1);',hi+' = '+high+';']
 if order:assignments.reverse()
 if fold==1:assignments[0]='if ((unsigned)high >= 0) '+assignments[0]
 bb='{\n    '+typ+' high;\n    '+decl+'\n    high = SONG(off);\n    '+'\n    '.join(assignments)+'\n    return '+ret+';\n}'
 vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:8]])
