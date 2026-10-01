from pathlib import Path
import sys,json,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_20E8_0903';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/window-origin-addresses';out.mkdir(exist_ok=True);vs=[]
for typ,expr in itertools.product(['char far *','unsigned char far *','void far *','unsigned far *'],['multiply','shift','addition','unsigned_mult','long_mult','unsigned_shift','i_long','alias']):
 bb=b.replace('int far *origin;',typ+'origin;').replace('origin = o + 4;','origin = ('+typ+')(o + 4);')
 for ix in ['i','j']:
  idx={'multiply':ix+' * 2','shift':ix+' << 1','addition':ix+' + '+ix,'unsigned_mult':'(unsigned)'+ix+' * 2','long_mult':ix+' * 2L','unsigned_shift':'(unsigned)'+ix+' << 1','i_long':'(long)'+ix+' * 2','alias':ix+' * 2'}[expr]
  adr='(char far *)origin' if typ=='void far *' else 'origin'
  if typ=='unsigned far *':adr='(char far *)origin'
  replacement='*(int far *)('+adr+' + ('+idx+'))'
  if expr=='alias':replacement='((int far *)origin)['+ix+']'
  bb=bb.replace('origin['+ix+']', replacement)
 n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],typ,expr))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,meta,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
