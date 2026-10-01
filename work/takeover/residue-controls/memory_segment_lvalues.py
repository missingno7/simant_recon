from pathlib import Path
import sys,json,itertools,concurrent.futures
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
def run(name):
 ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
 f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
 out=ROOT/'build/workers/takeover'/('segment-lvalues-'+name);out.mkdir(exist_ok=True);vs=[]
 if name=='f_171C_09CC':
  for hdr in ['BLK(FP_SEG(*h) - 2)','BLK(((unsigned far *)h)[1] - 2)','BLK(((unsigned long far *)h)[0] >> 16)']: # third is diagnostic: missing header adjustment, excluded below
   if '>> 16)' in hdr:continue
   for nextseg in ['SEG(b)','FP_SEG(b)','(unsigned)SEG(b)']:
    for cmpseg in ['SEG(next)','FP_SEG(next)']:
     for call in ['nested','assignment']:
      bb=b.replace('HDR(h)',hdr).replace('BLK(SEG(b) + b->paras)', 'BLK('+nextseg+' + (unsigned long)b->paras)').replace('SEG(next)',cmpseg)
      if call=='assignment':bb=bb.replace('f_171C_068C(f_171C_0160(b, 0), paras, type);', 'b = f_171C_0160(b, 0);\n    f_171C_068C(b, paras, type);')
      vs.append(('v'+str(len(vs)),base[:f.body.s]+bb+base[f.body.e:]))
 else:
  for seg in ['FP_SEG(b)','*((unsigned far *)&b + 1)','(unsigned)SEG(b)']:
   for nextseg in ['SEG(b)','FP_SEG(b)','(unsigned)SEG(b)']:
    for null in ['n','FP_SEG(n)','SEG(n)']:
     bb=b.replace('seg = SEG(b);','seg = '+seg+';').replace('NEXTBLK(b)', 'BLK('+nextseg+' + (unsigned long)b->paras)').replace('if (n)', 'if ('+null+')')
     vs.append(('v'+str(len(vs)),base[:f.body.s]+bb+base[f.body.e:]))
 ev=autosearch.Evaluator(ctx,name,3,out/'cache');rows=[]
 for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
  (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(name,n,r.get('score'),r.get('all_exact'),flush=True)
 ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(run,['f_171C_09CC','f_171C_0ADC']))
