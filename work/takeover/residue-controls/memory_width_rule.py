from pathlib import Path
import sys,json,itertools,concurrent.futures
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
def run(name):
 ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
 f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
 out=ROOT/'build/workers/takeover'/('width-rule-'+name);out.mkdir(exist_ok=True);vs=[]
 for seg,paras in itertools.product(['SEG(b)','(unsigned)SEG(b)','(int)SEG(b)','FP_SEG(b)'],['b->paras','(int)b->paras','(unsigned long)b->paras']):
  for order in [0,1]:
   expr=paras+' + '+seg if order else seg+' + '+paras
   for call in ['original','assignment']:
    bb=b.replace('NEXTBLK(b)','BLK('+expr+')').replace('BLK(SEG(b) + b->paras)','BLK('+expr+')')
    if call=='assignment':
     if name=='f_171C_09CC':bb=bb.replace('f_171C_068C(f_171C_0160(b, 0), paras, type);','b = f_171C_0160(b, 0);\n    f_171C_068C(b, paras, type);')
     else:bb=bb.replace('if (n)', 'if (SEG(n) != 0)')
    vs.append(('v'+str(len(vs)),base[:f.body.s]+bb+base[f.body.e:]))
 ev=autosearch.Evaluator(ctx,name,3,out/'cache');rows=[]
 for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
  (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(name,n,r.get('score'),r.get('all_exact'),flush=True)
 ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(run,['f_171C_09CC','f_171C_0ADC']))
