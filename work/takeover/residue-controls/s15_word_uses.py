from pathlib import Path
import sys,json,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='o15_384C_0239';text=autosearch.unscaffold((ROOT/'src/S15/m384C.c').read_text(),name)
f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/s15-word-uses';out.mkdir(exist_ok=True);vs=[]
for var in ['text','h','which']:
 for truth in [True,False]:
  expr='((unsigned)'+var+(' >= 0)' if truth else ' < 0)')
  for site in ['font','flag','loop','event','fontarg']:
   bb=b;op=' && ' if truth else ' || '
   if site=='font':bb=bb.replace('g_3DB2 == 0x140 ?', '(g_3DB2 == 0x140'+op+expr+') ?')
   elif site=='flag':bb=bb.replace('if (g_5A97 & 1)','if ((g_5A97 & 1)'+op+expr+')')
   elif site=='loop':bb=bb.replace('if (f_1F58_0038())','if (f_1F58_0038()'+op+expr+')')
   elif site=='event':bb=bb.replace('if (win_GetEvent(&ev))','if (win_GetEvent(&ev)'+op+expr+')')
   else:bb=bb.replace('f_24AB_02AD(0);','f_24AB_02AD('+('(!'+expr+')' if truth else expr)+');')
   vs.append(('v'+str(len(vs)),text[:f.body.s]+bb+text[f.body.e:]))
ev=autosearch.Evaluator(modctx.resolve(func=name),name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
