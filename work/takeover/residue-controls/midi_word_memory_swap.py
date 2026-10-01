from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='f_284A_0138';text=autosearch.unscaffold((ROOT/'src/root/m284A.c').read_text(),name);f=csrc.Source(text).function(name);out=ROOT/'build/workers/takeover/midi-word-memory-swap';out.mkdir(exist_ok=True);vs=[]
word='*(unsigned _based(g_8DFC) *)off'
for local,op,masked in itertools.product([False,True],['|','+','^'],[False,True]):
 value='value' if local else '('+word+')';hi='('+value+' & 255)' if masked else value;lo='('+value+' >> 8)'
 bb='{\n'+('    unsigned value = '+word+';\n' if local else '')+'    return ('+hi+' << 8) '+op+' '+lo+';\n}'
 vs.append(text[:f.body.s]+bb+text[f.body.e:])
for op in ['|','+','^']:
 bb='{\n    unsigned high = ('+word+') & 255;\n    return (high << 8) '+op+' SONG(off + 1);\n}';vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:8]])
