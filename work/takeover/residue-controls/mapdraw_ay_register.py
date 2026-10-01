from pathlib import Path
import sys,json,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_0250_129E';ctx=modctx.resolve(func=name)
base=(ROOT/'build/workers/takeover/mapdraw-coordinate-copies/v9.c').read_text()
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/mapdraw-ay-register';out.mkdir(exist_ok=True);vs=[]
for typ,expr in itertools.product(['int','unsigned','long','unsigned long','register int'],['plain','reverse','split','screen_first','two_locals','assign_condition']):
 bb=b.replace('    int ay;', '    '+typ+' ay;')
 if typ in ['unsigned','long','unsigned long']:bb=bb.replace('if (ay > 0x3f)','if ((int)ay > 0x3f)')
 if expr=='reverse':bb=bb.replace('fd_50F6_0508.y + screenY','screenY + fd_50F6_0508.y')
 if expr=='split':bb=bb.replace('ay = fd_50F6_0508.y + screenY;', 'ay = fd_50F6_0508.y;\n    ay += screenY;')
 if expr=='screen_first':bb=bb.replace('ay = fd_50F6_0508.y + screenY;', 'ay = screenY;\n    ay += fd_50F6_0508.y;')
 if expr=='two_locals':bb=bb.replace('screenY = y;\n    ay = fd_50F6_0508.y + screenY;', 'ay = fd_50F6_0508.y;\n    screenY = y;\n    ay += screenY;')
 if expr=='assign_condition':bb=bb.replace('ay = fd_50F6_0508.y + screenY;', 'ay = fd_50F6_0508.y + screenY;').replace('if (x < 0 || screenY < 0 || x >= 40 || screenY >= 30)','if ((i = x) < 0 || screenY < 0 || i >= 40 || screenY >= 30)')
 n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],typ,expr))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,meta,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
