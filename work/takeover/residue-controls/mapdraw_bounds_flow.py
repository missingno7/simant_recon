from pathlib import Path
import sys,json,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_0250_129E';ctx=modctx.resolve(func=name)
base=(ROOT/'build/workers/takeover/mapdraw-coordinate-copies/v9.c').read_text();f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/mapdraw-bounds-flow';out.mkdir(exist_ok=True);vs=[]
for flow,comp in itertools.product(['plain','goto','nested','nested_goto','loop_break'],['plain','reverse','invert']):
 bb=b
 if flow=='goto':bb=bb.replace('return;','goto done;');bb=bb[:-1]+'done:;\n}'
 if flow in ['nested','nested_goto']:
  bb=bb.replace('    if (x < 0 || screenY < 0 || x >= 40 || screenY >= 30)\n        return;', '    if (x >= 0 && screenY >= 0 && x < 40 && screenY < 30) {')
  bb=bb[:-1]+'    }\n}'
  if flow=='nested_goto':bb=bb.replace('return;','goto done;');bb=bb[:-1]+'done:;\n}'
 if flow=='loop_break':
  bb=bb.replace('    screenY = y;', '    do {\n    screenY = y;',1).replace('return;', 'break;');bb=bb[:-1]+'    } while (0);\n}'
 if comp=='reverse':bb=bb.replace('if (ay > 0x3f)','if (0x3f < ay)')
 if comp=='invert':bb=bb.replace('if (ay > 0x3f)\n        Punt("Y>MAXAY");','if (ay <= 0x3f) { } else\n        Punt("Y>MAXAY");')
 n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],flow,comp))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,meta,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
