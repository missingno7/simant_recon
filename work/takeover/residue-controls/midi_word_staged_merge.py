from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='f_284A_0138';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);f=csrc.Source(text).function(name);out=ROOT/'build/workers/takeover/midi-word-staged-merge';out.mkdir(exist_ok=True);vs=[]
for typ,merge,order in itertools.product(['int','unsigned'],['result |= high << 8;','result += high << 8;','result = (result & 255) | (high << 8);','result = (result & 255) + (high << 8);','result ^= high << 8;','result = (result & 255) ^ (high << 8);'],['high_low','low_high']):
 steps=['high = SONG(off);','result = SONG(off + 1);']
 if order=='low_high':steps.reverse()
 bb='{\n    '+typ+' high, result;\n    '+'\n    '.join(steps+[merge,'return result;'])+'\n}'
 vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in rows])
