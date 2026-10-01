from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_171C_0ADC';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/memadc-next-cache';out.mkdir(exist_ok=True);vs=[]
for cache in ['n','new_pointer','segment','paragraphs','both']:
 for null in ['pointer','segment','zero_ulong','zero_word']:
  for seguse in ['plain','folded']:
   bb=b
   if cache=='n':bb=bb.replace('    f_194D_0006(b, NEXTBLK(b), NEXTBLK(b)->paras);','    n = NEXTBLK(b);\n    f_194D_0006(b, n, n->paras);')
   elif cache=='new_pointer':bb=bb.replace('    Block save;', '    Block far *next;\n    Block save;').replace('    f_194D_0006(b, NEXTBLK(b), NEXTBLK(b)->paras);','    next = NEXTBLK(b);\n    f_194D_0006(b, next, next->paras);')
   elif cache=='segment':bb=bb.replace('    Block save;', '    unsigned nextseg;\n    Block save;').replace('    f_194D_0006(b, NEXTBLK(b), NEXTBLK(b)->paras);','    nextseg = b->paras + SEG(b);\n    f_194D_0006(b, BLK(nextseg), BLK(nextseg)->paras);')
   elif cache=='paragraphs':bb=bb.replace('    Block save;', '    unsigned nextparas;\n    Block save;').replace('    f_194D_0006(b, NEXTBLK(b), NEXTBLK(b)->paras);','    nextparas = NEXTBLK(b)->paras;\n    f_194D_0006(b, NEXTBLK(b), nextparas);')
   else:bb=bb.replace('    Block save;', '    unsigned nextparas;\n    Block save;').replace('    f_194D_0006(b, NEXTBLK(b), NEXTBLK(b)->paras);','    n = NEXTBLK(b);\n    nextparas = n->paras;\n    f_194D_0006(b, n, nextparas);')
   if null=='segment':bb=bb.replace('if (n)', 'if (SEG(n))')
   elif null=='zero_ulong':bb=bb.replace('if (n)', 'if (n != 0L)')
   elif null=='zero_word':bb=bb.replace('if (n)', 'if (SEG(n) != (unsigned)0)')
   if seguse=='folded':bb=bb.replace('    f_194D_0006(', '    if (seg >= 0) f_194D_0006(')
   vs.append(('v'+str(len(vs)),base[:f.body.s]+bb+base[f.body.e:]))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
