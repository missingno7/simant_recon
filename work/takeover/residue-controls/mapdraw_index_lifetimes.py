from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_0250_129E';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/mapdraw-index-lifetimes';out.mkdir(exist_ok=True);vs=[]
for loc in ['plain','long_ay','ulong_ay','y_copy','x_copy']:
 for use in ['plain','y_check','y_draw','index_check','index_write','pointer_check','x_check']:
  bb=b
  if loc in ['long_ay','ulong_ay']:bb=bb.replace('    int ay;', '    '+('long' if loc=='long_ay' else 'unsigned long')+' ay;').replace('if (ay > 0x3f)', 'if ((int)ay > 0x3f)')
  elif loc=='y_copy':
   bb=bb.replace('    int ay;', '    int ay;\n    int screenY;').replace('    ay =', '    screenY = y;\n    ay =',1)
   bb=bb.replace('g_19C0 * y','g_19C0 * screenY').replace('y * g_19C0','screenY * g_19C0')
  elif loc=='x_copy':bb=bb.replace('    int ay;', '    int ay;\n    int screenX;').replace('    ay =', '    screenX = x;\n    ay =',1).replace('g_19BE * x','g_19BE * screenX')
  if use=='y_check':bb=bb.replace('if (*p !=', 'if ((unsigned)y >= 0 && (*p !=').replace('g_19CE != 0)) {','g_19CE != 0))) {')
  elif use=='y_draw':bb=bb.replace('if (g_9126)', 'if ((unsigned)y >= 0 && g_9126)')
  elif use=='index_check':bb=bb.replace('if (fd_50F6_15C4[0][i] == -2)', 'if ((unsigned)i >= 0 && fd_50F6_15C4[0][i] == -2)')
  elif use=='index_write':bb=bb.replace('        *p = g_9126;', '        if ((unsigned)i >= 0)\n            *p = g_9126;')
  elif use=='pointer_check':bb=bb.replace('if (*p !=', 'if ((unsigned long)p >= 0 && (*p !=').replace('g_19CE != 0)) {','g_19CE != 0))) {')
  elif use=='x_check':bb=bb.replace('if (ay > 0x3f)', 'if ((unsigned)x >= 0 && ay > 0x3f)')
  n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],loc,use))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
