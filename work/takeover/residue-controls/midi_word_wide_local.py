from pathlib import Path
import sys,json,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_284A_0138';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name)
out=ROOT/'build/workers/takeover/midi-word-wide-local';out.mkdir(exist_ok=True);vs=[]
for typ in ['long','unsigned long']:
 for reg in ['', 'register ']:
  for low in ['direct','int','unsigned char']:
   for op in ['shift_or','multiply_add','shift_xor']:
    decl=reg+typ+' high;'+('' if low=='direct' else '\n    '+low+' low;')
    lo='SONG(off + 1)' if low=='direct' else 'low'
    exp='(high << 8) | '+lo if op=='shift_or' else 'high * 256 + '+lo if op=='multiply_add' else '(high << 8) ^ '+lo
    b='{\n    '+decl+'\n    high = SONG(off);\n    '+('' if low=='direct' else 'low = SONG(off + 1);\n    ')+'return '+exp+';\n}'
    vs.append(('v'+str(len(vs)),base[:f.body.s]+b+base[f.body.e:]))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
