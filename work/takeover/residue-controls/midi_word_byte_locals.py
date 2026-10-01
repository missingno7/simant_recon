from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='f_284A_0138';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);f=csrc.Source(text).function(name);out=ROOT/'build/workers/takeover/midi-word-byte-locals';out.mkdir(exist_ok=True);vs=[]
for high,low,view,op in itertools.product(['int','unsigned'],['unsigned char','signed char','int'],['high','(unsigned char)high','(high & 255)'],['+','|']):
 bb='{\n    '+high+' high;\n    '+low+' low;\n    high = SONG(off);\n    low = SONG(off + 1);\n    return ('+view+' << 8) '+op+' '+('(unsigned char)low' if low=='signed char' else 'low')+';\n}'
 vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:8]])
