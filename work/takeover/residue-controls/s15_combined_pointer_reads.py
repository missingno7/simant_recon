from pathlib import Path
import sys,json,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='o15_384C_0239';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name);f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/s15-combined-pointer-reads';out.mkdir(exist_ok=True);vs=[]
for mask,huse in itertools.product(range(64),['none','font','loop']):
 bb=b;wide='(unsigned long)text >= 0';seg='(unsigned)((unsigned long)text >> 16) >= 0';checks={'font':[],'flag':[],'loop':[]}
 for bit,site,expr in [(1,'font',wide),(2,'flag',wide),(4,'loop',wide),(8,'font',seg),(16,'flag',seg),(32,'loop',seg)]:
  if not mask&bit:continue
  checks[site].append(expr)
 if huse!='none':checks[huse].append('(unsigned long)h >= 0')
 if checks['font']:bb=bb.replace('g_3DB2 == 0x140 ?', '('+' && '.join(checks['font'])+' && g_3DB2 == 0x140) ?')
 if checks['flag']:bb=bb.replace('if (g_5A97 & 1)', 'if ('+' && '.join(checks['flag'])+' && (g_5A97 & 1))')
 if checks['loop']:bb=bb.replace('if (f_1F58_0038())', 'if ('+' && '.join(checks['loop'])+' && f_1F58_0038())')
 n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],mask,huse))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,meta,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
