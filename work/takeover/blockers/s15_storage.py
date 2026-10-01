from pathlib import Path
import sys,json,itertools,re
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'))
import modctx,autosearch,csrc
name='o15_384C_0239';ctx=modctx.resolve(func=name);base=ctx.text
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/blockers/s15-storage';out.mkdir(parents=True,exist_ok=True);vs=[]
for member in ['text','h']:
    for rep in ['struct','array']:
        typ='char far *' if member=='text' else 'Handle'
        if rep=='struct':decl='struct { '+typ+' value; } '+member+';';expr=member+'.value'
        else:decl=typ+' '+member+'[1];';expr=member+'[0]'
        bb=re.sub(r'\b'+member+r'\b',expr,b)
        bb,n=re.subn(re.escape(typ)+r'\s*'+re.escape(expr)+';',lambda m:decl,bb);assert n==1
        vs.append((rep+'-'+member,base[:f.body.s]+bb+base[f.body.e:]))
for init,qual,ret in itertools.product(['plain','chain'],['int','unsigned','short','enum Result { Discard, Save, Cancel }'],['result','(int)result']):
    bb=b.replace('int result;',qual+' result;').replace('return result;','return '+ret+';')
    if init=='chain':
        bb=bb.replace('text = f_171C_1B84(h);','text = f_171C_1B84(h);\n    result = 0;')
    vs.append(('v'+str(len(vs)),base[:f.body.s]+bb+base[f.body.e:]))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
    (out/(n+'.c')).write_text(t);rows.append({'name':n,**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print([(r['name'],r.get('score'),r.get('all_exact')) for r in rows])
