from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_1C62_0415';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/question-coordinates';out.mkdir(exist_ok=True);vs=[]
for coords in ['point','scalars','unsigned_scalars','pt_scalars','array']:
 for init in ['plain','no_v','h_first','for_i']:
  for update in ['plain','for_i','for_c']:
   bb=b
   if init=='no_v':bb=bb.replace('c = pt.v = pt.h = i = 0;', 'c = pt.h = i = 0;')
   elif init=='h_first':bb=bb.replace('c = pt.v = pt.h = i = 0;', 'pt.h = c = i = 0;')
   elif init=='for_i':bb=bb.replace('c = pt.v = pt.h = i = 0;\n    for (; i < count; i++)', 'c = pt.h = 0;\n    for (i = 0; i < count; i++)')
   if update=='for_i':
    bb=bb.replace('for (; i < count; i++)', 'for (; i < count;)').replace('for (i = 0; i < count; i++)', 'for (i = 0; i < count;)',1).replace('        c += 2;', '        i++;\n        c += 2;')
   elif update=='for_c':
    bb=bb.replace('for (; i < count; i++)', 'for (; i < count; c += 2)').replace('for (i = 0; i < count; i++)', 'for (i = 0; i < count; c += 2)',1).replace('        c += 2;', '        i++;',1)
   if coords in ['scalars','unsigned_scalars','pt_scalars']:
    ty='unsigned' if coords=='unsigned_scalars' else 'int';hn='h' if coords!='pt_scalars' else 'pointH';vn='v' if coords!='pt_scalars' else 'pointV'
    bb=bb.replace('struct Point pt;',ty+' '+hn+';\n    '+ty+' '+vn+';').replace('pt.h',hn).replace('pt.v',vn)
   elif coords=='array':bb=bb.replace('struct Point pt;', 'int pt[2];').replace('pt.h','pt[0]').replace('pt.v','pt[1]')
   n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],coords,init,update))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
