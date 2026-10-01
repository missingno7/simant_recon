from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_1C62_0415';ctx=modctx.resolve(func=name);base=(ROOT/'build/workers/takeover/question-loop-lifetimes/v21.c').read_text()
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/question-loop-order';out.mkdir(exist_ok=True);vs=[]
for htype in ['int','long']:
 for vtype in ['int','long','unsigned long']:
  for first in ['header','body','body_no_v','header_i_first']:
   for compare in ['plain','reverse']:
    bb=b.replace('    int h;', '    '+htype+' h;').replace('    int v;', '    '+vtype+' v;')
    if first.startswith('body'):
     bb=bb.replace('for (; j < count; j++)', 'for (; j < count;)').replace('        c += 2;', '        j++;\n        c += 2;')
     if first=='body_no_v':bb=bb.replace('c = v = h = j = 0;', 'c = h = j = 0;')
    elif first=='header_i_first':bb=bb.replace('for (; j < count; j++)', 'for (; j < count; j++, c += 2)').replace('        c += 2;\n','')
    if compare=='reverse':bb=bb.replace('j < count','count > j')
    n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],htype,vtype,first,compare))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
