from pathlib import Path
import sys,json,re,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_171C_0CF4';ctx=modctx.resolve(func=name);base=(ROOT/'build/workers/takeover/memcf4-reviewed-flow/v1.c').read_text()
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/memcf4-loop-state';out.mkdir(exist_ok=True);vs=[]
for order in itertools.permutations(['moved','seg','t']):
 for wide in ['none','moved','seg']:
  for init in ['plain','type_zero','segment_zero']:
   bb=b
   for var in ['moved','seg','t']:
    bb=bb.replace('    '+('unsigned' if var=='seg' else 'int')+' '+var+';\n','')
    bb=re.sub(r'\b'+var+r'\b','state.'+var,bb)
   fields=' '.join(('unsigned long' if var==wide else 'unsigned' if var=='seg' else 'int')+' '+var+';' for var in order)
   bb=bb.replace('{\n','{\n    struct { '+fields+' } state;\n',1)
   if init=='type_zero':bb=bb.replace('state.moved = 0;', 'state.moved = state.t = 0;')
   elif init=='segment_zero':bb=bb.replace('state.moved = 0;', 'state.moved = state.seg = 0;')
   if wide=='seg':bb=bb.replace('(state.seg = (unsigned)SEG(b)) < end','(unsigned)(state.seg = (unsigned)SEG(b)) < end').replace('b->paras + state.seg','b->paras + (unsigned)state.seg')
   n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],order,wide,init))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
