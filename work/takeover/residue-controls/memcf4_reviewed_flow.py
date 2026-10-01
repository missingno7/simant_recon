from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_171C_0CF4';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name);seed=(ROOT/'work/resJ/mem/cf4_best.txt').read_text();body=seed[seed.index('{'):seed.rfind('}')+1]
out=ROOT/'build/workers/takeover/memcf4-reviewed-flow';out.mkdir(exist_ok=True);vs=[]
for typ in ['unsigned','unsigned long']:
 for lt in ['plain','type_first','nested']:
  for val in ['plain','pointer_local','long_local']:
   for later in ['plain','cached_segment']:
    bb=body.replace('    unsigned seg;', '    '+typ+' seg;')
    if lt=='type_first':bb=bb.replace('(t = n->type, !n->lock) && (t == 1 || t == 3)', '(t = n->type, (t == 1 || t == 3)) && !n->lock')
    elif lt=='nested':bb=bb.replace('(t = n->type, !n->lock) && (t == 1 || t == 3)', '!n->lock && ((t = n->type) == 1 || t == 3)')
    if val!='plain':
     ty='char far *' if val=='pointer_local' else 'unsigned long'
     bb=bb.replace('    int moved;', '    int moved;\n    '+ty+' data;').replace('        *(Handle)((char far *)s_2F46 + b->handle) = (char far *)((long)b + 0x20000L);', '        data = ('+ty+')((long)b + 0x20000L);\n        *(Handle)((char far *)s_2F46 + b->handle) = (char far *)data;')
    if later=='cached_segment':bb=bb.replace('n = NEXTBLK(n);','n = BLK((unsigned)SEG(n) + (unsigned long)n->paras);')
    n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],typ,lt,val,later))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
