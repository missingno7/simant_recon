from pathlib import Path
import sys,json,itertools,re
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_0250_129E';ctx=modctx.resolve(func=name)
base=(ROOT/'build/workers/takeover/mapdraw-coordinate-copies/v9.c').read_text()
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/mapdraw-parameter-reuse';out.mkdir(exist_ok=True);vs=[]
for expr,fold in itertools.product(['plain','compound','parameter_sum','screen_sum','inline_bounds','copy_after'],['none','ay_word','ay_long','screen_word']):
 bb=b.replace('    int ay;\n','');bb=re.sub(r'\bay\b','y',bb)
 if expr=='compound':bb=bb.replace('y = fd_50F6_0508.y + screenY;', 'y += fd_50F6_0508.y;')
 if expr=='parameter_sum':bb=bb.replace('y = fd_50F6_0508.y + screenY;', 'y = fd_50F6_0508.y + y;')
 if expr=='screen_sum':bb=bb.replace('y = fd_50F6_0508.y + screenY;', 'y = screenY + fd_50F6_0508.y;')
 if expr=='inline_bounds':bb=bb.replace('y = fd_50F6_0508.y + screenY;\n    if (x < 0', 'if ((y = fd_50F6_0508.y + screenY), x < 0')
 if expr=='copy_after':bb=bb.replace('screenY = y;\n    y = fd_50F6_0508.y + screenY;', 'y = fd_50F6_0508.y + (screenY = y);')
 bound='x < 0 || screenY < 0 || x >= 40 || screenY >= 30'
 if fold=='ay_word':bb=bb.replace(bound,'(unsigned)y < 0 || '+bound)
 if fold=='ay_long':bb=bb.replace(bound,'(unsigned long)(unsigned)y < 0 || '+bound)
 if fold=='screen_word':bb=bb.replace(bound,'(unsigned)screenY < 0 || '+bound)
 n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],expr,fold))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,meta,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
