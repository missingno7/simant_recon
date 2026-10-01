from pathlib import Path
import sys,json,itertools,re
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_1C62_0415';ctx=modctx.resolve(func=name);base=(ROOT/'build/workers/takeover/question-loop-order/v2.c').read_text();f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/question-loop-conditions';out.mkdir(exist_ok=True);vs=[]
for coords,cond in itertools.product(['scalar','volatile_v','point','pt','array','separate_records'],['plain','subtract','subtract_ge','volatile_count','volatile_j','j_alias']):
 bb=b
 if coords=='volatile_v':bb=bb.replace('int v;', 'volatile int v;')
 if coords in ['point','pt','array','separate_records']:
  bb=bb.replace('    int h;\n','').replace('    int v;\n','')
  hv={'point':('pt.h','pt.v','struct Point pt;'),'pt':('pt.y','pt.x','struct Pt pt;'),'array':('coords[1]','coords[0]','int coords[2];'),'separate_records':('hx.value','vx.value','struct { int value; } hx, vx;')}[coords]
  bb=re.sub(r'\bh\b',hv[0],bb);bb=re.sub(r'\bv\b',hv[1],bb);bb=bb.replace('    int width;', '    '+hv[2]+'\n    int width;')
 if cond=='subtract':bb=bb.replace('j < count', 'count - j > 0')
 if cond=='subtract_ge':bb=bb.replace('j < count', 'count - j - 1 >= 0')
 if cond=='volatile_count':bb=bb.replace('int count;', 'volatile int count;')
 if cond=='volatile_j':bb=bb.replace('int j;', 'volatile int j;')
 if cond=='j_alias':bb=bb.replace('j < count', '*(int near *)&j < count')
 n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],coords,cond))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,meta,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
