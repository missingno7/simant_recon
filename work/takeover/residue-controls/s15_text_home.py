from pathlib import Path
import sys,json,itertools,re
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='o15_384C_0239';text=autosearch.unscaffold((ROOT/'src/S15/m384C.c').read_text(),name)
f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/s15-text-home';out.mkdir(exist_ok=True);vs=[]
decls=['struct Event ev;','struct Rect r;','Handle h;','char far *text;','int result;']
old='\n'.join('    '+d for d in decls)
for ds in itertools.permutations(decls):
 bb=b.replace(old,'\n'.join('    '+d for d in ds))
 vs.append(('decl'+str(len(vs)),text[:f.body.s]+bb+text[f.body.e:]))
for decl in re.findall(r'^extern[^;]+;',text,re.M):
 if text.index(decl)<f.head_s:continue
 # Real declarations used by subsequent module functions, moved before this body.
 tt=text.replace(decl,'',1);pos=csrc.Source(tt).function(name).head_s
 tt=tt[:pos]+decl+'\n'+tt[pos:]
 vs.append(('proto'+str(len(vs)),tt))
for var in ['text','h','which']:
 for site in ['flag','loop','event','return']:
  expr='((unsigned long)'+var+' >= 0)';bb=b
  if site=='flag':bb=bb.replace('if (g_5A97 & 1)','if ((g_5A97 & 1) && '+expr+')')
  elif site=='loop':bb=bb.replace('if (f_1F58_0038())','if (f_1F58_0038() && '+expr+')')
  elif site=='event':bb=bb.replace('if (win_GetEvent(&ev))','if (win_GetEvent(&ev) && '+expr+')')
  else:bb=bb.replace('return result;','return '+expr+' ? result : result;')
  vs.append(('fold'+str(len(vs)),text[:f.body.s]+bb+text[f.body.e:]))
ev=autosearch.Evaluator(modctx.resolve(func=name),name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r})
 if r.get('score')==[0,0,0,0] or n.startswith('proto'):print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('Finished',len(rows),'variants',flush=True)
