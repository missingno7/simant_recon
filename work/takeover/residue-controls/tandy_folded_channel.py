from pathlib import Path
import sys,json,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_29D6_000A';text=autosearch.unscaffold((ROOT/'src/root/m29D6.c').read_text(),name)
f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/tandy-folded-channel';out.mkdir(exist_ok=True);vs=[]
for shift in ['native','address','inline']:
 for wordfold in [False,True]:
  for check in ['(unsigned char)((char)chan + 0x80) >= 0','(unsigned char)chan >= 0','(unsigned)chan >= 0','(unsigned)((char)chan + 0x80) >= 0']:
   bb=b
   if shift!='inline':bb=bb.replace('    _asm {\n        mov cl, 5\n        shl chan, cl\n    }','    '+('chan' if shift=='native' else '*(int *)&chan')+' <<= 5;')
   freq='    f = g_75E8[note % 12] >> note / 12;'
   if wordfold:bb=bb.replace(freq,'    if ((unsigned)chan >= 0)\n    '+freq.lstrip())
   first='    f_29F0_002A(0x205, (f & 0xf) + ((char)chan + 0x80));'
   bb=bb.replace(first,'    if ('+check+')\n    '+first.lstrip())
   vs.append(('v'+str(len(vs)),text[:f.body.s]+bb+text[f.body.e:]))
ev=autosearch.Evaluator(modctx.resolve(func=name),name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
