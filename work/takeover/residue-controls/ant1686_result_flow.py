from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='o25_3BA4_1686';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/ant1686-result-flow';out.mkdir(exist_ok=True);vs=[]
for result in ['plain','register','original_return']:
 for first in ['first','before_threshold','after_d']:
  for order in ['rightleft','leftright']:
   for init in ['before','after']:
    bb=b.replace('    best = -1;\n    threshold','    result = -1;\n    threshold',1)
    decl='    '+('register ' if result=='register' else '')+'int result;\n'
    if first=='first':bb=bb.replace('{\n','{\n'+decl,1)
    elif first=='before_threshold':bb=bb.replace('    int threshold;\n',decl+'    int threshold;\n')
    else:bb=bb.replace('    int d;\n','    int d;\n'+decl)
    if order=='leftright':bb=bb.replace('right = left = *dir;', 'left = right = *dir;')
    if init=='after':bb=bb.replace('        best = -1;\n        '+('right = left' if order=='rightleft' else 'left = right')+' = *dir;', '        '+('right = left' if order=='rightleft' else 'left = right')+' = *dir;\n        best = -1;')
    if result=='original_return':bb=bb.replace('    return best;\nfound:', '    if (threshold > 0) result = best;\n    return result;\nfound:')
    else:
     bb=bb.replace('        if (best < 0)\n            return best;', '        if (best < 0) { result = best; goto done; }')
     bb=bb.replace('    }\n    return best;\nfound:', '        result = best;\n    }\ndone:\n    return result;\nfound:')
     bb=bb.replace('    return right;','    result = right;\n    goto done;')
    vs.append(('v'+str(len(vs)),base[:f.body.s]+bb+base[f.body.e:]))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
