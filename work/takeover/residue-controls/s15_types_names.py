from pathlib import Path
import sys,json,itertools,re
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='o15_384C_0239';text=autosearch.unscaffold((ROOT/'src/S15/m384C.c').read_text(),name)
f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/s15-types-names';out.mkdir(exist_ok=True);vs=[]
for typ in ['unsigned char far *','signed char far *','const char far *','void far *','int far *','char huge *','volatile char far *','char far * volatile','register char far *']:
 bb=b.replace('char far *text;',typ+'text;')
 vs.append(('type'+str(len(vs)),text[:f.body.s]+bb+text[f.body.e:]))
for var in ['text','h','result','r','ev']:
 for synonym in ['p','s','message','handle','retval','rect','event','textp']:
  bb=re.sub(r'\b'+var+r'\b',synonym,b)
  vs.append(('rename'+str(len(vs)),text[:f.body.s]+bb+text[f.body.e:]))
for decl in re.findall(r'^extern[^;]+;',text[:f.head_s],re.M):
 new=re.sub(r'([ *])(\w+)(?=\s*[,\)])',r'\1',decl)
 if new!=decl:vs.append(('unnamed'+str(len(vs)),text.replace(decl,new,1)))
for var in ['text','h']:
 for expr in ['((unsigned)((unsigned long)'+var+' >> 16) >= 0)','((unsigned)((unsigned long)'+var+' >> 16) < 0)']:
  for site in ['flag','loop','event']:
   bb=b;truth='>= 0' in expr
   if site=='flag':old='if (g_5A97 & 1)';cond='(g_5A97 & 1)'
   elif site=='loop':old='if (f_1F58_0038())';cond='f_1F58_0038()'
   else:old='if (win_GetEvent(&ev))';cond='win_GetEvent(&ev)'
   bb=bb.replace(old,'if ('+cond+(' && ' if truth else ' || ')+expr+')')
   vs.append(('segment'+str(len(vs)),text[:f.body.s]+bb+text[f.body.e:]))
ev=autosearch.Evaluator(modctx.resolve(func=name),name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
