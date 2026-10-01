from pathlib import Path
import sys,json,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='InvertPatch';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/invert-coordinate-orders';out.mkdir(exist_ok=True);vs=[]
for expr in ['x * 28 - y * 10 + fd_50F6_10D2.left','fd_50F6_10D2.left + x * 28 - y * 10','x * 28 + (fd_50F6_10D2.left - y * 10)','28 * x - 10 * y + fd_50F6_10D2.left','fd_50F6_10D2.left - y * 10 + x * 28']:
 for assignment in ['plain','chained','chained_reverse','direct_fields']:
  for loops in ['plain','fields','h_and_v']:
   if assignment=='direct_fields' and loops=='h_and_v':continue
   bb=b.replace('org.h = x * 28 - y * 10 + fd_50F6_10D2.left;', 'org.h = '+expr+';')
   if assignment in ['chained','chained_reverse']:
    for axis,field in [('h','h'),('v','v')]:
     bb=bb.replace('        '+axis+' = ', '        '+('org.'+field+' = '+axis if assignment=='chained' else axis+' = org.'+field)+' = ')
     bb=bb.replace('        '+axis+' += ', '        '+('org.'+field+' = '+axis if assignment=='chained' else axis+' = org.'+field)+' = '+axis+' + ')
     bb=bb.replace('        org.'+field+' = '+axis+';\n','')
   elif assignment=='direct_fields':
    for axis in ['h','v']:
     bb=bb.replace('        '+axis+' = ', '        org.'+axis+' = ').replace('        '+axis+' += ', '        org.'+axis+' = '+axis+' + ').replace('        org.'+axis+' = '+axis+';\n','')
    bb=bb.replace(' + v;', ' + org.v;')
   if loops=='fields':bb=bb.replace(' + v;', ' + org.v;')
   elif loops=='h_and_v':bb=bb.replace(' + org.h;', ' + h;')
   n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],expr,assignment,loops))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
