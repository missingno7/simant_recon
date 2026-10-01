from pathlib import Path
import sys,json,re,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='DisplayCard';text=autosearch.unscaffold((ROOT/'src/S23/m39C7.c').read_text(),name)
f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/card-iterator-reuse';out.mkdir(exist_ok=True);vs=[]
pos=b.index('                while ((nul = _fmemchr')
for reuse in ['h2','p','q2']:
 for basefirst in [False,True]:
  for counter in ['original','split']:
   bb=b[:pos]+re.sub(r'\bq\b',reuse,b[pos:])
   if reuse=='q2':bb=bb.replace('    char far *q;','    char far *q;\n    char far *q2;')
   if basefirst:bb=bb.replace('off + base','base + off')
   if counter=='split':
    bb=bb.replace('    int k;','    int k;\n    int frame;')
    bb=bb.replace('for (k = 0; k < tr.nFrames; k++)','for (frame = 0; frame < tr.nFrames; frame++)')
   vs.append(('v'+str(len(vs)),text[:f.body.s]+bb+text[f.body.e:]))
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
