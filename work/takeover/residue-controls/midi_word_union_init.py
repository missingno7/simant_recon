from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_284A_0138';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name)
out=ROOT/'build/workers/takeover/midi-word-union-init';out.mkdir(exist_ok=True);vs=[]
for typ in ['int','unsigned']:
 for reg in ['', 'register ']:
  for rep in ['fields','array']:
   for high in ['low_copy','source_copy','word_shift']:
    decl=reg+'union { '+typ+' word; '+('struct { unsigned char lo, hi; } bytes;' if rep=='fields' else 'unsigned char bytes[2];')+' } result;'
    lo='result.bytes.lo' if rep=='fields' else 'result.bytes[0]';hi='result.bytes.hi' if rep=='fields' else 'result.bytes[1]'
    mid=hi+' = '+lo+';' if high=='low_copy' else hi+' = SONG(off);' if high=='source_copy' else 'result.word <<= 8;'
    b='{\n    '+decl+'\n    result.word = SONG(off);\n    '+mid+'\n    '+lo+' = SONG(off + 1);\n    return result.word;\n}'
    vs.append(('v'+str(len(vs)),base[:f.body.s]+b+base[f.body.e:]))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
