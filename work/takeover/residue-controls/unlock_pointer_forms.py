from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='win_UnlockWin';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/unlock-pointer-forms';out.mkdir(exist_ok=True);vs=[]
for objform in ['typed','char','uchar','register_typed','register_char']:
 for listform in ['embedded','cast','local','local_top']:
  for ptrform in ['field','byte_cast','void_cast']:
   bb=b
   if objform.endswith('typed'):
    if objform.startswith('register'):bb=bb.replace('struct Obj far *obj;', 'register struct Obj far *obj;')
   else:
    ty='unsigned char' if objform=='uchar' else 'char'
    bb=bb.replace('struct Obj far *obj;', ('register ' if objform.startswith('register') else '')+ty+' far *obj;')
    bb=bb.replace('obj = w->objs[i];','obj = ('+ty+' far *)w->objs[i];').replace('switch (obj->type)','switch (obj[0x21])')
   if ptrform!='field' or not objform.endswith('typed'):
    for off in ['34','2a']:
     expr='(char far * far * far *)((char far *)obj + 0x'+off+')'
     if ptrform=='void_cast':expr='(void far *)((char far *)obj + 0x'+off+')'
     bb=bb.replace('&obj->h'+off,expr)
   if listform=='cast':bb=bb.replace('w->objs[i]','((struct Obj far * far *)((char far *)w + 0x2c))[i]')
   elif listform.startswith('local'):
    bb=bb.replace('    struct Win far *w;', '    struct Win far *w;\n    struct Obj far * far *objects;')
    bb=bb.replace('                w = *h;', '                w = *h;\n                objects = w->objs;')
    bb=bb.replace('w->objs[i]','objects[i]')
    if listform=='local_top':bb=bb.replace('w->objs[0]','objects[0]')
   n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],objform,listform,ptrform))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
