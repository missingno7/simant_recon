from pathlib import Path
import sys,json,re
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_171C_0CF4';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name);seed=(ROOT/'work/resJ/mem/cf4_best.txt').read_text();body=seed[seed.index('{'):seed.rfind('}')+1]
out=ROOT/'build/workers/takeover/memcf4-segment-views';out.mkdir(exist_ok=True);vs=[]
for view in ['union_value','union_bits','union_bits_low','long_low','long_low_assign']:
 for zero in ['literal','param_fold','sizeof_zero','not_param_fold']:
  for nextwidth in ['plain','width']:
   bb=body
   if view.startswith('union'):
    bb=bb.replace('    unsigned seg;','')
    bb=re.sub(r'\bseg\b','seg.value',bb).replace('{\n','{\n    union { unsigned value; unsigned long bits; } seg;\n',1)
    if view=='union_bits':bb=bb.replace('(seg.value = (unsigned)SEG(b))','(unsigned)(seg.bits = SEG(b))').replace('b->paras + seg.value','b->paras + seg.bits')
    elif view=='union_bits_low':bb=bb.replace('(seg.value = (unsigned)SEG(b))','(seg.bits = SEG(b), seg.value)').replace('b->paras + seg.value','b->paras + seg.bits')
   else:
    bb=bb.replace('    unsigned seg;','    unsigned long seg;')
    bb=bb.replace('(seg = (unsigned)SEG(b))','(*(unsigned near *)&seg = (unsigned)SEG(b))' if view=='long_low_assign' else '(seg = SEG(b), *(unsigned near *)&seg)')
    bb=bb.replace('b->paras + seg','b->paras + *(unsigned near *)&seg')
   if zero=='param_fold':bb=bb.replace('moved = 0;', 'moved = (unsigned)emsOnly < 0;')
   elif zero=='sizeof_zero':bb=bb.replace('moved = 0;', 'moved = sizeof moved - sizeof moved;')
   elif zero=='not_param_fold':bb=bb.replace('moved = 0;', 'moved = !((unsigned)emsOnly >= 0);')
   if nextwidth=='width':bb=bb.replace('n = NEXTBLK(n);','n = BLK((unsigned)SEG(n) + (unsigned long)n->paras);')
   n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],view,zero,nextwidth))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
