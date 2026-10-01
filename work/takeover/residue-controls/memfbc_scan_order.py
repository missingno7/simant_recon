from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_171C_0FBC';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/memfbc-scan-order';out.mkdir(exist_ok=True);vs=[]
for order in ['plain','type_first','type_nested']:
 for chain in ['plain','best_b','b_best','split_b_first']:
  for available in ['plain','before_if','inside_if']:
   bb=b
   cond='!n->lock && (n->type == 1 || n->type == 3 || n->type == 0x80)'
   if order=='type_first':bb=bb.replace(cond, '(n->type == 1 || n->type == 3 || n->type == 0x80) && !n->lock')
   elif order=='type_nested':bb=bb.replace('if ('+cond+')\n                        goto again;', 'if (n->type == 1 || n->type == 3 || n->type == 0x80)\n                        if (!n->lock) goto again;')
   if chain!='plain':
    rhs='best = b = g_91AC;' if chain=='best_b' else 'b = best = g_91AC;' if chain=='b_best' else 'b = g_91AC;\n        best = b;'
    bb=bb.replace('best = g_91AC;\n        for (b = g_91AC;',rhs+'\n        for (;')
   if available!='plain':
    bb=bb.replace('    int first;', '    unsigned available;\n    int first;')
    stmt='        available = best->paras;\n'
    if available=='before_if':bb=bb.replace('        if (best && best->paras >= paras) {', '        if (best) available = best->paras;\n        if (best && available >= paras) {')
    else:bb=bb.replace('            if (best->paras > paras + 4)',stmt+'            if (best->paras > paras + 4)')
    bb=bb.replace('if (best->paras > paras + 4)', 'if (available > paras + 4)').replace('f_171C_068C(best, best->paras - paras, 0);','f_171C_068C(best, available - paras, 0);')
   vs.append(('v'+str(len(vs)),base[:f.body.s]+bb+base[f.body.e:]))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
