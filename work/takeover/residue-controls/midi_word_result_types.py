from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='f_284A_0138';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);f=csrc.Source(text).function(name);head=text[f.head_s:f.body.s];out=ROOT/'build/workers/takeover/midi-word-result-types';out.mkdir(exist_ok=True);vs=[]
exprs=['SONG(off) << 8 | SONG(off + 1)','SONG(off) * 256 + SONG(off + 1)','((unsigned)SONG(off) << 8) | SONG(off + 1)','(SONG(off + 1)) + ((unsigned)SONG(off) << 8)','((unsigned short)SONG(off) << 8) | SONG(off + 1)','((short)SONG(off) << 8) | SONG(off + 1)']
for typ,expr in itertools.product(['int','unsigned','short','unsigned short'],exprs):
 hh=head.replace('int far f_284A_0138',typ+' far f_284A_0138');bb='{\n    return '+expr+';\n}'
 vs.append(text[:f.head_s]+hh+bb+text[f.body.e:])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in rows])
