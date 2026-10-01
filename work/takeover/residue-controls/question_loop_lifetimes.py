from pathlib import Path
import sys,json,re
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='f_1C62_0415';ctx=modctx.resolve(func=name);base=(ROOT/'build/workers/takeover/question-coordinates/v12.c').read_text()
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/question-loop-lifetimes';out.mkdir(exist_ok=True);vs=[]
for keep in ['scalar','point']:
 seed=b if keep=='scalar' else csrc.Source(autosearch.unscaffold(ctx.source.read_text(),name)).function(name)
 if keep=='point':
  old=autosearch.unscaffold(ctx.source.read_text(),name);seed=old[seed.body.s:seed.body.e]
 for idx in ['plain','width_loop','draw_loop','width_draw','key_loop']:
  for fold in ['plain','i_width','i_draw','c_width','c_draw','i_both','c_both']:
   bb=seed.replace('c = pt.v = pt.h = i = 0;', 'c = pt.h = i = 0;')
   first=bb.index('    for (; i < count; i++)')
   end=bb.index('    if (width < c)',first)
   draw=bb.index('    for (i = 0; i < count; i++)')
   drawend=bb.index('    f_1FD2_02FF();',draw)
   if fold.endswith('width') or fold.endswith('both'):
    var='i' if fold.startswith('i') else 'c'
    bb=bb[:first]+bb[first:end].replace('i < count', '(unsigned)'+var+' >= 0 && i < count')+bb[end:]
   draw=bb.index('    for (i = 0; i < count; i++)');drawend=bb.index('    f_1FD2_02FF();',draw)
   if fold.endswith('draw') or fold.endswith('both'):
    var='i' if fold.startswith('i') else 'c'
    bb=bb[:draw]+bb[draw:drawend].replace('i < count', '(unsigned)'+var+' >= 0 && i < count')+bb[drawend:]
   if idx!='plain':
    bb=bb.replace('    int i;', '    int i;\n    int j;')
    first=bb.index('    for (;');end=bb.index('    if (width < c)',first)
    if idx in ['width_loop','width_draw']:
     bb=bb[:first]+re.sub(r'\bi\b','j',bb[first:end])+bb[end:]
     bb=bb.replace('h = i = 0;', 'h = j = 0;')
    draw=bb.index('    for (i = 0;');drawend=bb.index('    f_1FD2_02FF();',draw)
    if idx in ['draw_loop','width_draw']:bb=bb[:draw]+re.sub(r'\bi\b','j',bb[draw:drawend])+bb[drawend:]
    if idx=='key_loop':
     start=bb.index('    for (;;)');finish=bb.index('done:',start)
     bb=bb[:start]+re.sub(r'\bi\b','j',bb[start:finish])+bb[finish:]
   n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],keep,idx,fold))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
