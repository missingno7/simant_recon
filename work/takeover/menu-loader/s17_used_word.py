from pathlib import Path
import sys,itertools,json,re
sys.path.insert(0,'tools')
import csrc,modctx,variants,autosearch
name='o17_384C_0039';ctx=modctx.resolve(func=name);base=Path('work/takeover/menu-loader/s17-base.c').read_text();f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e];vs=[]
for typ,scope,form in itertools.product(['int','unsigned'],[False,True],['returns','goto','entry']):
 bb=b.replace('    int i;', '    int i;\n    '+typ+' result;')
 if form=='returns':bb=bb.replace('return 0;', 'return result = 0;').replace('return 1;', 'return result = 1;')
 elif form=='goto':bb=bb.replace('if (h == 0L)\n        return 0;', 'if (h == 0L) {\n        result = 0;\n        goto done;\n    }').replace('return 1;', 'result = 1;\ndone:\n    return result;')
 else:bb=bb.replace('    h = db_LoadObject', '    result = 0;\n    h = db_LoadObject').replace('return 0;', 'return result;').replace('return 1;', 'result = 1;\n    return result;')
 if scope:
  if form=='goto':continue
  bb=bb.replace('    '+typ+' result;\n','').replace('return result = 0;', '{ '+typ+' result; result = 0; return result; }').replace('return result = 1;', '{ '+typ+' result; result = 1; return result; }')
  if form=='entry':continue
 vs.append((f'result-{typ}-{scope}-{form}',base[:f.body.s]+bb+base[f.body.e:],''))
for scope,reg in itertools.product([False,True],['','register ']):
 bb=b.replace('    int i;', '    int i;\n    '+reg+'int object;').replace('    h = db_LoadObject(id, 6);','    object = id;\n    h = db_LoadObject(object, 6);').replace('db_UnhookObject(id, 6)','db_UnhookObject(object, 6)')
 if scope:bb=bb.replace('    '+reg+'int object;\n','').replace('    object = id;', '    {\n    '+reg+'int object;\n    object = id;').replace('    for (p = fd_55B3_6054;', '    }\n    for (p = fd_55B3_6054;')
 vs.append((f'object-{scope}-{bool(reg)}',base[:f.body.s]+bb+base[f.body.e:],''))
# Use actual induction variables in table fix-up loops; retain original value and stride.
for mask,typ in itertools.product(range(1,4),['int','unsigned']):
 bb=b
 if mask&1:
  bb=bb.replace('    int i;','    int i;\n    '+typ+' outer;')
  bb=bb.replace('for (p = fd_55B3_6054; *p; p++)', 'for (p = fd_55B3_6054, outer = 0; p[outer]; outer++)').replace('*p += (long)fd_55B3_6054;', 'p[outer] += (long)fd_55B3_6054;').replace('*(long far * far *)p', '*(long far * far *)(p + outer)')
 if mask&2:
  bb=bb.replace('    int i;','    int i;\n    '+typ+' inner;')
  bb=bb.replace('for (q = *(long far * far *)(p + outer); *q; q++)' if mask&1 else 'for (q = *(long far * far *)p; *q; q++)', 'for (q = *(long far * far *)'+('(p + outer)' if mask&1 else 'p')+', inner = 0; q[inner]; inner++)').replace('*q += (long)fd_55B3_6054;', 'q[inner] += (long)fd_55B3_6054;')
 vs.append((f'indexed-{mask}-{typ}',base[:f.body.s]+bb+base[f.body.e:],''))
out=Path('build/workers/continue_next/s17-used-word');out.mkdir(parents=True,exist_ok=True)
rows=variants.run(ctx,[('base',base,'')]+vs,extra_funcs=[name],claims_only=True,jobs=6,out_dir=out)
(out/'results.json').write_text(json.dumps({'function':name,'profile':ctx.profile,'flags':ctx.flags,'variants':rows},indent=1))
for x in rows:
 r=x['result'];print(x['name'],r.get('claims',{}).get(name),[c['name'] for c in ctx.claims if not r.get('claims',{}).get(c['name'],{}).get('exact')],flush=True)
