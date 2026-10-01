from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_171C_0CF4';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name);seed=(ROOT/'build/workers/takeover/memcf4-reviewed-flow/v1.c').read_text();sf=csrc.Source(seed).function(name);body=seed[sf.body.s:sf.body.e]
out=ROOT/'build/workers/takeover/memcf4-result-lifetime';out.mkdir(exist_ok=True);vs=[]
for how in ['plain','low_return','low_write','low_both','first','last','unsigned_return','char_return']:
 for life in ['plain','outer','first_type','before_copy','set_done','set_start']:
  bb=body.replace('int moved;', 'unsigned long moved;')
  if how in ['low_return','low_both']:bb=bb.replace('return moved;', 'return *(int near *)&moved;')
  if how in ['low_write','low_both']:bb=bb.replace('moved = 1;', '*(int near *)&moved = 1;')
  if how in ['first','last']:
   bb=bb.replace('    unsigned long moved;\n','')
   bb=bb.replace('{\n','{\n    unsigned long moved;\n',1) if how=='first' else bb.replace('    Block far *b;', '    Block far *b;\n    unsigned long moved;')
  if how=='unsigned_return':bb=bb.replace('return moved;', 'return (unsigned)moved;')
  if how=='char_return':bb=bb.replace('return moved;', 'return (unsigned char)moved;')
  if life=='outer':bb=bb.replace('(seg = (unsigned)SEG(b)) < end', '(moved >= 0 && (seg = (unsigned)SEG(b)) < end)')
  if life=='first_type':bb=bb.replace('if (b->type != 0x80)', 'if (moved >= 0 && b->type != 0x80)')
  if life=='before_copy':bb=bb.replace('        paras = n->paras;', '        if (moved >= 0)\n            paras = n->paras;')
  if life=='set_done':bb=bb.replace('moved = 1;', 'if (moved >= 0) moved = 1;')
  if life=='set_start':bb=bb.replace('moved = 0;', 'moved = (unsigned)emsOnly < 0;')
  n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],how,life))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
