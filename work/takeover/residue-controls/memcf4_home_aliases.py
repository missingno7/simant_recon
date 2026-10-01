from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_171C_0CF4';ctx=modctx.resolve(func=name);base=(ROOT/'build/workers/takeover/memcf4-result-lifetime/v6.c').read_text()
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/memcf4-home-aliases';out.mkdir(exist_ok=True);vs=[]
for mask in range(1,16):
 for typ in ['near','far']:
  bb=b;alias='*(unsigned '+typ+' *)&seg'
  if mask&1:bb=bb.replace('(seg = (unsigned)SEG(b))','('+alias+' = (unsigned)SEG(b))')
  if mask&2:bb=bb.replace('b->paras + seg','b->paras + '+alias)
  if mask&4:bb=bb.replace('if (b->type != 0x80)', 'if ((unsigned)seg >= 0 && b->type != 0x80)')
  if mask&8:bb=bb.replace('        paras = n->paras;', '        if ((unsigned)('+alias+') >= 0)\n            paras = n->paras;')
  n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],mask,typ))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
