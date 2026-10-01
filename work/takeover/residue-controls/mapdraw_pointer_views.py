from pathlib import Path
import sys,json,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_0250_129E';ctx=modctx.resolve(func=name)
base=(ROOT/'build/workers/takeover/mapdraw-coordinate-copies/v9.c').read_text();f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/mapdraw-pointer-views';out.mkdir(exist_ok=True);vs=[]
for typ,init in itertools.product(['int far *','unsigned far *','char far *','void far *','unsigned long','register int far *'],['plain','pointer_zero','sum_zero','index_zero']):
 bb=b.replace('int far *p;',typ+'p;' if typ.endswith('*') else typ+' p;')
 if typ not in ['int far *','register int far *']:
  bb=bb.replace('p = &fd_50F6_15C4[0][i];','p = ('+typ+')&fd_50F6_15C4[0][i];').replace('if (*p','if (*(int far *)p').replace('        *p =','        *(int far *)p =')
 if init=='pointer_zero':bb=bb.replace(('p;' if typ.endswith('*') else ' p;'),('p = 0;' if typ.endswith('*') else ' p = 0;'),1)
 if init=='sum_zero':bb=bb.replace('int ay;','int ay = 0;')
 if init=='index_zero':bb=bb.replace('int i;','int i = 0;')
 n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],typ,init))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,meta,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
