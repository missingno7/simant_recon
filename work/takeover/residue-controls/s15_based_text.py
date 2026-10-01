from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='o15_384C_0239';text=autosearch.unscaffold(modctx.resolve(func=name).text,name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/s15-based-text';out.mkdir(exist_ok=True);vs=[]
for reuse,convert in itertools.product([False,True],['direct','offset']):
 seg='result' if reuse else 'textSeg';bb=b.replace('    char far *text;', '    '+('_segment '+seg+';\n    ' if not reuse else '')+'char _based('+seg+') *text;\n    char far *raw;')
 if reuse:bb=bb.replace('    int result;\n','').replace('    char _based(result) *text;', '    _segment result;\n    char _based(result) *text;')
 bb=bb.replace('    text = f_171C_1B84(h);', '    raw = f_171C_1B84(h);\n    '+seg+' = (_segment)((unsigned long)raw >> 16);\n    text = (char _based('+seg+') *)'+('raw' if convert=='direct' else '(unsigned)raw')+';')
 vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in rows])
