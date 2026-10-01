from pathlib import Path
import sys,json,itertools,re
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='o25_3BA4_1035';text=autosearch.unscaffold((ROOT/'src/S25/m3BA4.c').read_text(),name)
f=csrc.Source(text).function(name)
out=ROOT/'build/workers/takeover/anthelper-declarations';out.mkdir(exist_ok=True);vs=[]
fields=['fd_50F6_048C','fd_50F6_047C','fd_50F6_048A']
positions=[text.index('extern int far '+v+';') for v in fields]
for order in itertools.permutations(fields):
 tt=text
 for p,v in sorted(zip(positions,order),reverse=True):
  stop=tt.index(';',p)+1;tt=tt[:p]+'extern int far '+v+';'+tt[stop:]
 vs.append(('order'+str(len(vs)),tt))
types={'int','char','long','short','unsigned','signed','void','float','double','far','near','const','volatile','Handle'}
for decl in re.findall(r'^extern[^;]+;',text[:f.head_s],re.M):
 new=re.sub(r'([ *])(\w+)(?=\s*[,\)])',lambda m:m.group(0) if m.group(2) in types or m.group(2)[0].isupper() else m.group(1),decl)
 if new!=decl:vs.append(('unnamed'+str(len(vs)),text.replace(decl,new,1)))
for decl in re.findall(r'^extern[^;]+;',text[f.e:],re.M):
 tt=text.replace(decl,'',1);at=csrc.Source(tt).function(name).head_s
 tt=tt[:at]+decl+'\n'+tt[at:];vs.append(('earlier'+str(len(vs)),tt))
ev=autosearch.Evaluator(modctx.resolve(func=name),name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r})
 if r.get('score')!=[1,2,2,0]:print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('Finished',len(rows),flush=True)
