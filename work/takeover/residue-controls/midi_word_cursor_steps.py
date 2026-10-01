from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='f_284A_0138';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);f=csrc.Source(text).function(name);out=ROOT/'build/workers/takeover/midi-word-cursor-steps';out.mkdir(exist_ok=True);vs=[]
for typ,mode,op in itertools.product(['int','unsigned','unsigned char'],['post','separate','pointer'],['|','+','^']):
 decl='    '+typ+' high;\n'
 if mode=='post':steps='    high = SONG(off++);\n';low='SONG(off)'
 elif mode=='separate':steps='    high = SONG(off);\n    off++;\n';low='SONG(off)'
 else:decl+='    unsigned char _based(g_8DFC) *cursor;\n';steps='    cursor = SONGP(off);\n    high = *cursor++;\n';low='*cursor'
 bb='{\n'+decl+steps+'    return (high << 8) '+op+' '+low+';\n}'
 vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in rows])
