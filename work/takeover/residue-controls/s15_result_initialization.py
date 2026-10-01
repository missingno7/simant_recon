from pathlib import Path
import sys,json,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='o15_384C_0239';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name);f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/s15-result-initialization';out.mkdir(exist_ok=True);vs=[]
sites=['win_Open(0x2100);','h = f_1A53_00F0','text = f_171C_1B84','f_24AB_02AD(g_3DB2','if (g_5A97 & 1)','win_PrintTextInRect(0, text, &r);']
for at,mask in itertools.product(sites,range(8)):
 if at==sites[-1] and mask&1:continue # The flag test precedes this initializer.
 bb=b.replace('    '+at,'    result = 0;\n    '+at,1)
 fold='(unsigned)result >= 0'
 if mask&1:bb=bb.replace('if (g_5A97 & 1)','if ('+fold+' && (g_5A97 & 1))')
 if mask&2:bb=bb.replace('if (f_1F58_0038())','if ('+fold+' && f_1F58_0038())')
 if mask&4:bb=bb.replace('if (win_GetEvent(&ev))','if ('+fold+' && win_GetEvent(&ev))')
 n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],at,mask))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,meta,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
