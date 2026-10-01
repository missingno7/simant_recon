from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='win_UnlockWin';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/unlock-address-values';out.mkdir(exist_ok=True);vs=[]
for valtype in ['unsigned long','long','unsigned char far *','void far *']:
 for access in ['typed','bytes','word_index']:
  for expr in ['original','listptr','pword','fold_obj']:
   bb=b.replace('struct Obj far *obj;',valtype+' obj;').replace('obj = w->objs[i];','obj = ('+valtype+')w->objs[i];')
   if access=='typed':bb=bb.replace('obj->','((struct Obj far *)obj)->')
   else:
    bb=bb.replace('switch (obj->type)', 'switch (((char far *)obj)[0x21])')
    for off in ['34','2a']:
     pe='(char far * far * far *)((char far *)obj + 0x'+off+')' if access=='bytes' else '(char far * far * far *)((int far *)obj + 0x'+format(int(off,16)//2,'x')+')'
     bb=bb.replace('&obj->h'+off,pe)
   if expr=='listptr':bb=bb.replace('w->objs[i]','((struct Obj far * far *)((char far *)w + 0x2c))[i]')
   if expr=='pword':bb=bb.replace('if (*p)', 'if (*(unsigned long far *)p)').replace('*p = 0;', '*(unsigned long far *)p = 0;')
   if expr=='fold_obj':bb=bb.replace('switch (', 'if ((unsigned long)obj >= 0)\n                    switch (',1)
   n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],valtype,access,expr))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
