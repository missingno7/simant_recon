from pathlib import Path
import sys,json,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_20E8_0903';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/window-origin-arrays';out.mkdir(exist_ok=True);vs=[]
for types,expr in itertools.product(['pointer','o_array','all_arrays','o_struct'],['plain','addition','dereference','temporary','compound_temp','two_temps']):
 bb=b
 if types=='o_array':
  bb=bb.replace('int far *o;', 'int (far *o)[4];').replace('o = f_2505_02D7(obj);', 'o = (int (far *)[4])f_2505_02D7(obj);')
  bb=bb.replace('origin = o + 4;', 'origin = o[1];').replace('mode = o + 12;', 'mode = o[3];').replace('ref = o + 8;', 'ref = o[2];').replace('o[i]', '(*o)[i]')
 if types=='all_arrays':
  bb=bb.replace('int far *o;', 'int (far *o)[4];').replace('int far *origin;', 'int (far *origin)[4];').replace('int far *mode;', 'int (far *mode)[4];').replace('int far *ref;', 'int (far *ref)[4];')
  bb=bb.replace('o = f_2505_02D7(obj);', 'o = (int (far *)[4])f_2505_02D7(obj);').replace('origin = o + 4;', 'origin = o + 1;').replace('mode = o + 12;', 'mode = o + 3;').replace('ref = o + 8;', 'ref = o + 2;')
  for p in ['o','origin','mode','ref']:
   for ix in ['i','j']:bb=bb.replace(p+'['+ix+']', '(*'+p+')['+ix+']')
 if types=='o_struct':
  bb=bb.replace('int j;', 'struct ObjectCoords { int bounds[4]; int origin[4]; int ref[4]; int mode[4]; };\n    int j;',1).replace('int far *o;', 'struct ObjectCoords far *o;').replace('o = f_2505_02D7(obj);', 'o = (struct ObjectCoords far *)f_2505_02D7(obj);').replace('origin = o + 4;', 'origin = o->origin;').replace('mode = o + 12;', 'mode = o->mode;').replace('ref = o + 8;', 'ref = o->ref;').replace('o[i]', 'o->bounds[i]')
 lhs='(*origin)[i]' if types=='all_arrays' else 'origin[i]';rhs='(*o)[i]' if types in ['o_array','all_arrays'] else 'o->bounds[i]' if types=='o_struct' else 'o[i]'
 old=lhs+' = rect[i] - '+rhs+';'
 if expr=='addition':bb=bb.replace(old,lhs+' = rect[i] + -'+rhs+';')
 if expr=='dereference':bb=bb.replace('rect[i]', '*(rect + i)').replace(rhs, '*('+('o->bounds' if types=='o_struct' else '*o' if types in ['o_array','all_arrays'] else 'o')+' + i)')
 if expr in ['temporary','compound_temp','two_temps']:
  bb=bb.replace('    int j;', '    int delta;\n    int j;',1)
  body='delta = rect[i] - '+rhs+';' if expr=='temporary' else 'delta = rect[i]; delta -= '+rhs+';' if expr=='compound_temp' else 'delta = '+rhs+'; delta = rect[i] - delta;'
  bb=bb.replace(old,'{ '+body+' '+lhs+' = delta; }')
 n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],types,expr))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,meta,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
