from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='SpiderScan';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/spiderscan-volatile-counter';out.mkdir(exist_ok=True);vs=[]
for storage in ['r_volatile','init_volatile','none','r_volatile_unsigned']:
 for init in ['separate','r_chain','pass_chain','assign_then_copy','volatile_copy']:
  bb=b.replace('int r = 0;', {'r_volatile':'volatile int r;','r_volatile_unsigned':'volatile unsigned r;'}.get(storage,'int r;'))
  if init=='separate':initexpr='0';before='r = 0;'
  elif init=='r_chain':initexpr='r = 0';before=''
  elif init=='pass_chain':initexpr='0';before='';bb=bb.replace('for (pass = 0;', 'for (r = pass = 0;')
  elif init=='assign_then_copy':initexpr='r';before='r = 0;'
  else:initexpr='*(volatile int *)&r';before='r = 0;'
  if init!='pass_chain':bb=bb.replace('for (pass = 0;', 'for (pass = '+initexpr+';')
  if before:bb=bb.replace('    for (pass', '    '+before+'\n    for (pass',1)
  if storage=='init_volatile':bb=bb.replace('r = 0', '*(volatile int *)&r = 0')
  vs.append(('v'+str(len(vs)),base[:f.body.s]+bb+base[f.body.e:]))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
