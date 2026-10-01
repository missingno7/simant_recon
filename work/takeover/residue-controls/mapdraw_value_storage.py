from pathlib import Path
import sys,json,itertools,re
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_0250_1018';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name);f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/mapdraw-value-storage';out.mkdir(exist_ok=True);vs=[]
for storage,order in itertools.product(['plain','volatile','near_lvalue','far_lvalue','struct','array','union'],['v_mx_my','mx_my_v','my_mx_v','v_my_mx']):
 bb=b
 decl='int v;'
 if storage=='volatile':decl='volatile int v;'
 if storage in ['near_lvalue','far_lvalue']:
  bb=bb.replace('    int v;\n','');bb=re.sub(r'\bv\b','*(int '+('near' if storage=='near_lvalue' else 'far')+' *)&v',bb);bb=bb.replace('{\n','{\n    int v;\n',1)
 if storage in ['struct','array','union']:
  bb=bb.replace('    int v;\n','')
  expr='v.word' if storage in ['struct','union'] else 'v[0]';bb=re.sub(r'\bv\b',expr,bb)
  decl='struct { int word; } v;' if storage=='struct' else 'union { int word; } v;' if storage=='union' else 'int v[1];'
  bb=bb.replace('{\n','{\n    '+decl+'\n',1)
 if storage=='volatile':bb=bb.replace('    int v;', '    '+decl)
 old='    '+decl+'\n' if storage in ['struct','array','union','volatile'] else '    int v;\n'
 bb=bb.replace(old,'').replace('    int mx;\n','').replace('    int my;\n','')
 ds={'v':decl,'mx':'int mx;','my':'int my;'}
 bb=bb.replace('{\n','{\n'+''.join('    '+ds[v]+'\n' for v in order.split('_')),1)
 n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],storage,order))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,meta,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
