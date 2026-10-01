from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'))
import modctx,autosearch,csrc
name='f_29D6_000A';ctx=modctx.resolve(func=name);base=ctx.text;f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/blockers/tandy-additions';out.mkdir(parents=True,exist_ok=True);vs=[]
exprs=['((char)chan + (char)0x80)','((unsigned char)chan + (unsigned char)0x80)', '((unsigned char)chan + 0x80)', '(*(char near *)&chan + 0x80)','(*(unsigned char near *)&chan + 0x80)', '(unsigned long)((char)chan + 0x80)', '(long)((char)chan + 0x80)', '((char)chan + 0x80L)', '((char)chan + 0x80UL)', '((char)chan + 0x80) * 1', '((char)chan + 0x80) / 1', '((char)chan + 0x80) & 0xff', '(char)((char)chan - 0x80)', '(unsigned char)((char)chan - 0x80)', '((char)chan + 0x80) << 0']
for e in exprs:
    bb=b.replace('((char)chan + 0x80)', '('+e+')')
    vs.append(('v'+str(len(vs)),base[:f.body.s]+bb+base[f.body.e:],e))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
    (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print([(r['name'],r.get('score'),r.get('all_exact')) for r in rows])
