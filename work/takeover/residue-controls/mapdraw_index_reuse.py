from pathlib import Path
import sys,json,itertools,re
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_0250_129E';ctx=modctx.resolve(func=name)
base=(ROOT/'build/workers/takeover/mapdraw-coordinate-copies/v9.c').read_text()
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/mapdraw-index-reuse';out.mkdir(exist_ok=True);vs=[]
for reuse,form in itertools.product(['index','sum','independent'],['plain','bounds_comma','copy_chain','sum_chain','sum_fold','screen_fold','index_chain']):
 bb=b
 if reuse=='index':bb=bb.replace('    int ay;\n','');bb=re.sub(r'\bay\b','i',bb)
 if reuse=='sum':bb=bb.replace('    int i;\n','');bb=re.sub(r'\bi\b','ay',bb)
 av='i' if reuse=='index' else 'ay';iv='ay' if reuse=='sum' else 'i'
 if form=='bounds_comma':bb=bb.replace(av+' = fd_50F6_0508.y + screenY;\n    if (x < 0','if (('+av+' = fd_50F6_0508.y + screenY), x < 0')
 if form=='copy_chain':bb=bb.replace('screenY = y;\n    '+av+' = fd_50F6_0508.y + screenY;', av+' = fd_50F6_0508.y + (screenY = y);')
 if form=='sum_chain':bb=bb.replace(av+' = fd_50F6_0508.y + screenY;', av+' = screenY;\n    '+av+' += fd_50F6_0508.y;')
 if form=='sum_fold':bb=bb.replace('if (x < 0','if ((unsigned)'+av+' < 0 || x < 0',1)
 if form=='screen_fold':bb=bb.replace('if (x < 0','if ((unsigned)screenY < 0 || x < 0',1)
 if form=='index_chain':bb=bb.replace(iv+' = screenY * 40 + x;', iv+' = screenY * 40;\n    '+iv+' += x;')
 n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],reuse,form))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,meta,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
