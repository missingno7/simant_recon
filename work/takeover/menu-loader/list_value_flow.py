from pathlib import Path
import sys,json,itertools
sys.path.insert(0,'tools')
import csrc,modctx,variants,autosearch
name='f_23E6_0000';ctx=modctx.resolve(func=name);base=Path('work/takeover/menu-loader/list-base.c').read_text(encoding='utf-8');f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e];vs=[]
for order,combined in itertools.product(['pointer-first','count-first'],[False,True]):
 steps='s += _fstrlen(s) + 1, n++' if order=='pointer-first' else 'n++, s += _fstrlen(s) + 1'
 bb=b.replace('while (n < line)', 'for (; n < line'+(' && *s' if combined else '')+'; '+steps+')').replace('        s += _fstrlen(s) + 1;\n','').replace('        n++;\n','')
 if combined:bb=bb.replace('        if (*s == 0)\n            break;\n','')
 vs.append((f'for-{order}-{combined}',base[:f.body.s]+bb+base[f.body.e:],''))
for typ,scope,form in itertools.product(['int','unsigned','long','unsigned long'],[False,True],['separate','embedded']):
 bb=b
 decl=typ+' length;'
 if scope:bb=bb.replace('        s += _fstrlen(s) + 1;', '        {\n        '+decl+'\n        s += _fstrlen(s) + 1;\n        }')
 else:bb=bb.replace('    int off;', '    int off;\n    '+decl)
 if form=='separate':bb=bb.replace('        s += _fstrlen(s) + 1;', '        length = _fstrlen(s);\n        s += length + 1;')
 else:bb=bb.replace('_fstrlen(s) + 1;', '(length = _fstrlen(s)) + 1;')
 vs.append((f'length-{typ}-{scope}-{form}',base[:f.body.s]+bb+base[f.body.e:],''))
for steps in ['(s += _fstrlen(s) + 1), n++;','n++, (s += _fstrlen(s) + 1);','n += ((unsigned long)(s += _fstrlen(s) + 1) >= 0);','n += ((unsigned)(s += _fstrlen(s) + 1) >= 0);']:
 bb=b.replace('        s += _fstrlen(s) + 1;\n        n++;', '        '+steps)
 vs.append((f'comma-{len(vs)}',base[:f.body.s]+bb+base[f.body.e:],'folded assignment-value controls require STEERED if exact' if '>= 0' in steps else ''))
out=Path('build/workers/continue_next/list-value-flow');out.mkdir(parents=True,exist_ok=True)
rows=variants.run(ctx,[('base',base,'')]+vs,extra_funcs=[name],claims_only=True,jobs=6,out_dir=out)
(out/'results.json').write_text(json.dumps({'function':name,'profile':ctx.profile,'flags':ctx.flags,'variants':rows},indent=1))
for x in rows:
 r=x['result'];print(x['name'],r.get('claims',{}).get(name),[c['name'] for c in ctx.claims if not r.get('claims',{}).get(c['name'],{}).get('exact')],flush=True)
