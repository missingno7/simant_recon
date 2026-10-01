from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='SpiderScan';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/spiderscan-init-lvalue';out.mkdir(exist_ok=True);vs=[]
for typ in ['int','unsigned','short','signed char','unsigned char','char']:
 for access in ['initializer','pass','both','first_random','pass_alias']:
  bb=b.replace('    int r = 0;', '    int r;')
  lv='*('+typ+' *)&r'
  if access in ['initializer','both']:bb=bb.replace('    for (pass = 0;', '    '+lv+' = 0;\n    for (pass = '+(lv if access=='both' else '0')+';')
  else:
   bb=bb.replace('    for (pass = 0;', '    r = 0;\n    for (pass = '+(lv if access in ['pass','pass_alias'] else '0')+';')
   if access=='first_random':bb=bb.replace('r = SRand1(12) + 1;', lv+' = SRand1(12) + 1;')
   elif access=='pass_alias':bb=bb.replace('for (pass = '+lv+';', 'for ('+lv+' = pass = 0;')
  vs.append(('v'+str(len(vs)),base[:f.body.s]+bb+base[f.body.e:]))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
