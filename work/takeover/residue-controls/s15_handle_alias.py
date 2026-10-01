from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='o15_384C_0239';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/s15-handle-alias';out.mkdir(exist_ok=True);vs=[]
for loc in ['first','after_handle','after_text']:
 for form in ['lock_alias','release_alias','text_alias','locked_and_release','unlock_result']:
  bb=b
  decl='    '+('char far *message;' if form=='text_alias' else 'Handle stringHandle;')+'\n'
  if loc=='first':bb=bb.replace('{\n','{\n'+decl,1)
  elif loc=='after_handle':bb=bb.replace('    Handle h;\n','    Handle h;\n'+decl)
  else:bb=bb.replace('    char far *text;\n','    char far *text;\n'+decl)
  if form=='lock_alias':bb=bb.replace('text = f_171C_1B84(h);','stringHandle = h;\n    text = f_171C_1B84(stringHandle);')
  elif form=='release_alias':bb=bb.replace('    f_171C_1BBA(h);','    stringHandle = h;\n    f_171C_1BBA(stringHandle);').replace('db_ReleaseHandle(h);','db_ReleaseHandle(stringHandle);')
  elif form=='locked_and_release':bb=bb.replace('text = f_171C_1B84(h);','stringHandle = h;\n    text = f_171C_1B84(stringHandle);').replace('f_171C_1BBA(h);','f_171C_1BBA(stringHandle);').replace('db_ReleaseHandle(h);','db_ReleaseHandle(stringHandle);')
  elif form=='text_alias':bb=bb.replace('text = f_171C_1B84(h);','message = f_171C_1B84(h);\n    text = message;')
  else:bb=bb.replace('f_171C_1BBA(h);','stringHandle = f_171C_1BBA(h);').replace('db_ReleaseHandle(h);','db_ReleaseHandle(stringHandle);') # diagnostic: return-handle semantics need review
  vs.append(('v'+str(len(vs)),base[:f.body.s]+bb+base[f.body.e:]))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
