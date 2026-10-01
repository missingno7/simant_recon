from pathlib import Path
import sys,json,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='o25_3BA4_1035';text=autosearch.unscaffold((ROOT/'src/S25/m3BA4.c').read_text(),name)
f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/anthelper-folded-uses';out.mkdir(exist_ok=True);vs=[]
for var in ['fd_50F6_048C','fd_50F6_047C','fd_50F6_048A','fd_50F6_04C2','fd_50F6_0496']:
 for truth in [False,True]:
  check='((unsigned)'+var+(' >= 0)' if truth else ' < 0)')
  for order in [False,True]:
   op=' && ' if truth else ' || '
   cmp=check+op+'(fd_50F6_048C == 2)' if order else '(fd_50F6_048C == 2)'+op+check
   bb=b.replace('if (fd_50F6_048C == 2)','if ('+cmp+')')
   vs.append(('fold'+str(len(vs)),text[:f.body.s]+bb+text[f.body.e:]))
for expr in ['(unsigned)fd_50F6_047C','(int)(unsigned)fd_50F6_047C','*(unsigned far *)&fd_50F6_047C','*(volatile int far *)&fd_50F6_047C','(fd_50F6_047C | 0)','(fd_50F6_047C & 0xffff)','(fd_50F6_047C + 0L)']:
 bb=b.replace('DigMyTile(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A);','DigMyTile(fd_50F6_048C, '+expr+', fd_50F6_048A);')
 vs.append(('arg'+str(len(vs)),text[:f.body.s]+bb+text[f.body.e:]))
ev=autosearch.Evaluator(modctx.resolve(func=name),name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
