from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='o25_3BA4_1686';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/ant1686-lifetimes';out.mkdir(exist_ok=True);vs=[]
for dtype in ['int','volatile int','unsigned','long']:
 for site in ['plain','threshold_after','threshold_before','scan_loop','best_test_before','best_test_after','dir_init','first_loop','second_loop','final','negative_init']:
  bb=b.replace('    int d;','    '+dtype+' d;')
  folded='((unsigned)best >= 0)'
  if site=='threshold_after':bb=bb.replace('threshold > 0','threshold > 0 && '+folded,1)
  elif site=='threshold_before':bb=bb.replace('threshold > 0',folded+' && threshold > 0',1)
  elif site=='scan_loop':bb=bb.replace('i < 8','i < 8 && '+folded,1)
  elif site=='best_test_before':bb=bb.replace('best < 0',folded+' && best < 0',1)
  elif site=='best_test_after':bb=bb.replace('best < 0','best < 0 && '+folded,1)
  elif site=='dir_init':bb=bb.replace('right = left = *dir;', 'if ('+folded+') right = left = *dir;')
  elif site=='first_loop':bb=bb.replace('if (*rot == 0)', 'if (*rot == 0 && '+folded+')')
  elif site=='second_loop':bb=bb.replace('if (*rot > 0)', 'if (*rot > 0 && '+folded+')')
  elif site=='final':bb=bb.replace('if (dis <= threshold)', 'if (dis <= threshold && '+folded+')')
  elif site=='negative_init':bb=bb.replace('best = -1;\n    threshold', 'best = ((unsigned)*rot < 0) - 1;\n    threshold',1)
  vs.append(('v'+str(len(vs)),base[:f.body.s]+bb+base[f.body.e:]))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
