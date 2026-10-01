from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='win_UnlockWin';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/unlock-segment-offsets';out.mkdir(exist_ok=True);vs=[]
for objtype in ['pointer','ulong']:
 for how in ['wordcast','wordlvalue','fieldoff','fold_pointer','fold_type','fold_after']:
  for decl in ['plain','obj_first','p_last']:
   bb=b
   if objtype=='ulong':bb=bb.replace('struct Obj far *obj;', 'unsigned long obj;').replace('obj = w->objs[i];','obj = (unsigned long)w->objs[i];').replace('obj->','((struct Obj far *)obj)->')
   if how in ['wordcast','wordlvalue','fieldoff']:
    for off in ['34','2a']:
     low='(unsigned)(unsigned long)obj' if how=='wordcast' else '*(unsigned near *)&obj' if how=='wordlvalue' else '(unsigned)(unsigned long)&((struct Obj far *)obj)->h'+off
     if how!='fieldoff':low='('+low+' + 0x'+off+')'
     expr='(char far * far * far *)(((unsigned long)obj & 0xffff0000UL) | (unsigned)'+low+')'
     bb=bb.replace('&obj->h'+off,expr).replace('&((struct Obj far *)obj)->h'+off,expr)
   elif how=='fold_pointer':bb=bb.replace('switch (', 'if ((unsigned long)obj >= 0)\n                    switch (',1)
   elif how=='fold_type':bb=bb.replace('switch (', 'if ((unsigned)((struct Obj far *)obj)->type >= 0)\n                    switch (',1)
   elif how=='fold_after':bb=bb.replace('if (*p)', 'if ((unsigned long)obj >= 0 && *p)')
   if decl=='obj_first':
    ty='unsigned long obj;' if objtype=='ulong' else 'struct Obj far *obj;';bb=bb.replace('    '+ty+'\n','').replace('{\n','{\n    '+ty+'\n',1)
   elif decl=='p_last':bb=bb.replace('    char far * far * far *p;\n','').replace('    struct Win far *w;','    struct Win far *w;\n    char far * far * far *p;')
   n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],objtype,how,decl))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
