from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='f_284A_0138';text=autosearch.unscaffold((ROOT/'src/root/m284A.c').read_text(),name);f=csrc.Source(text).function(name);out=ROOT/'build/workers/takeover/midi-word-bitfields';out.mkdir(exist_ok=True);vs=[]
for typ,reg,initial,order in itertools.product(['unsigned','int'],['','register '],[False,True],[False,True]):
 decl=reg+'union { '+typ+' word; struct { unsigned lo:8; unsigned hi:8; } bits; } result;'
 if initial:assignments=['result.word = SONG(off);','result.bits.hi = result.bits.lo;','result.bits.lo = SONG(off + 1);']
 else:
  assignments=['result.bits.hi = SONG(off);','result.bits.lo = SONG(off + 1);']
  if order:assignments.reverse()
 if initial and order:assignments[1:]=reversed(assignments[1:])
 # Initial form requires saving the high byte before overwriting low byte.
 if initial and order:continue
 bb='{\n    '+decl+'\n    '+'\n    '.join(assignments)+'\n    return result.word;\n}'
 vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:8]])
