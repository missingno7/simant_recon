from pathlib import Path
import sys, json, hashlib
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import autosearch, csrc, modctx
name = 'win_UnlockWin'
ctx = modctx.resolve(func=name)
base = (ROOT / 'build/workers/ptr_unlock/base.c').read_text(encoding='latin1')
fn = csrc.Source(base).function(name)
body = base[fn.body.s:fn.body.e]
out = ROOT / 'build/workers/ptr_unlock'
variants=[]
old_assign='                    obj = w->objs[i];\n                    switch (obj->type) {'
assert old_assign in body
for label, item in [('switch_assign_index','w->objs[i]'), ('switch_assign_add','*(w->objs + i)')]:
    b=body.replace(old_assign, f'                    switch ((obj = {item})->type) {{')
    variants.append((label,base[:fn.body.s]+b+base[fn.body.e:]))
for label,item in [('switch_direct_index','w->objs[i]'),('switch_direct_add','*(w->objs + i)')]:
    b=body.replace('    struct Obj far *obj;\n','')
    b=b.replace(old_assign, f'                    switch (({item})->type) {{')
    b=b.replace('&obj->h34',f'&({item})->h34').replace('&obj->h2a',f'&({item})->h2a')
    variants.append((label,base[:fn.body.s]+b+base[fn.body.e:]))
for label,item in [('local_obj_repeat_index','w->objs[i]'),('local_obj_repeat_add','*(w->objs + i)')]:
    b=body.replace('&obj->h34', f'&({item})->h34').replace('&obj->h2a', f'&({item})->h2a')
    variants.append((label,base[:fn.body.s]+b+base[fn.body.e:]))
for label,item in [('typed_repeat_index','w->objs[i]'),('typed_repeat_add','*(w->objs + i)')]:
    b=body.replace('                    obj = w->objs[i];\n','')
    b=b.replace('switch (obj->type)', f'switch (({item})->type)')
    b=b.replace('&obj->h34', f'&({item})->h34').replace('&obj->h2a', f'&({item})->h2a')
    b=b.replace('    struct Obj far *obj;\n','')
    variants.append((label,base[:fn.body.s]+b+base[fn.body.e:]))
for label,text in variants:
    (out / f'{label}.c').write_text(text,encoding='latin1')
ev=autosearch.Evaluator(ctx,name,2,out/'cache')
rows=[]
for (label,text),r in zip(variants,ev.many([text for _,text in variants])):
    row={'name':label,'source_sha256':hashlib.sha256(text.encode('latin1')).hexdigest(),**r}
    rows.append(row)
    print(label,r.get('score'),'all_exact=',r.get('all_exact'),'length=',r.get('length'),'reasons=',r.get('reasons'))
ev.save()
(out/'repeated-object-expression-results.json').write_text(json.dumps(rows,indent=1)+'\n')
