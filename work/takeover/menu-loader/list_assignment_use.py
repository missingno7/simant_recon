from pathlib import Path
import sys,json,itertools
sys.path.insert(0,'tools')
import csrc,modctx,variants
name='f_23E6_0000';ctx=modctx.resolve(func=name);base=Path('work/takeover/menu-loader/list-base.c').read_text(encoding='utf-8');f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e];vs=[]
for width,form,assign in itertools.product(['unsigned','unsigned long'],['if','ternary','and','comma'],['s += _fstrlen(s) + 1','s = s + _fstrlen(s) + 1']):
 pred=f'(({width})({assign}) >= 0)'
 if form=='if':update='if ('+pred+') n++;'
 elif form=='ternary':update=pred+' ? n++ : n++;'
 elif form=='and':update=pred+' && n++;'
 else:update='('+width+')('+assign+'), n++;'
 bb=b.replace('        s += _fstrlen(s) + 1;\n        n++;','        '+update)
 vs.append((f'{width}-{form}-{assign.startswith("s +=")}',base[:f.body.s]+bb+base[f.body.e:],'assignment-value control; folded predicates require STEERED if exact'))
# Keep a genuinely used pointer intermediate for the next line.
for scope in [False,True]:
 bb=b
 decl='char far *next;'
 if scope:bb=bb.replace('        s += _fstrlen(s) + 1;', '        {\n        '+decl+'\n        next = s + _fstrlen(s) + 1;\n        s = next;\n        }')
 else:bb=bb.replace('    char far *s;', '    char far *s;\n    '+decl).replace('        s += _fstrlen(s) + 1;', '        next = s + _fstrlen(s) + 1;\n        s = next;')
 vs.append((f'next-{scope}',base[:f.body.s]+bb+base[f.body.e:],''))
out=Path('build/workers/continue_next/list-assignment-use');out.mkdir(parents=True,exist_ok=True)
rows=variants.run(ctx,[('base',base,'')]+vs,extra_funcs=[name],claims_only=True,jobs=6,out_dir=out)
(out/'results.json').write_text(json.dumps({'function':name,'profile':ctx.profile,'flags':ctx.flags,'variants':rows},indent=1))
for x in rows:
 r=x['result'];print(x['name'],r.get('claims',{}).get(name),[c['name'] for c in ctx.claims if not r.get('claims',{}).get(c['name'],{}).get('exact')],flush=True)
