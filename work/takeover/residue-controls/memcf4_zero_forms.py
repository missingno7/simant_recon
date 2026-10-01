from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_171C_0CF4';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name);seed=(ROOT/'build/workers/takeover/memcf4-reviewed-flow/v1.c').read_text();sf=csrc.Source(seed).function(name);body=seed[sf.body.s:sf.body.e]
out=ROOT/'build/workers/takeover/memcf4-zero-forms';out.mkdir(exist_ok=True);vs=[]
forms=['0','0L','0UL','0U','(char)0','(long)0','0 == 1','!1','(0L != 0)','(unsigned)emsOnly * 0','emsOnly - emsOnly','emsOnly & 0','(unsigned long)emsOnly & 0xffff0000UL','(unsigned)sizeof b < 0','(unsigned)SEG(g_91A4) < 0','(unsigned)s_8C70 < 0','(unsigned)end < 0','(unsigned)fd_50F6_3950 < 0']
for typ in ['int','long']:
 for form in forms:
  if form=='(unsigned)end < 0':continue
  bb=body.replace('int moved;',typ+' moved;').replace('moved = 0;', 'moved = '+form+';')
  n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],typ,form))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
