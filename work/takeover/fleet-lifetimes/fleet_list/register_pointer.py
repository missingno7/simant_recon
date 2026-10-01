from pathlib import Path
import sys,json,itertools,hashlib
sys.path.insert(0,'tools')
import modctx,variants
name='f_23E6_0000'
base=Path('work/takeover/menu-loader/list-base.c').read_text(encoding='utf-8')
ctx=modctx.resolve(func=name,source='work/takeover/menu-loader/list-base.c')
print('context',ctx.key,ctx.profile,ctx.flags,ctx.placements)
print('base_sha256',hashlib.sha256(base.replace('\r\n','\n').encode()).hexdigest())
# Direct local register-variable hypotheses based on the observed SI offset register and
# the original segment reload. Each declaration is a legal C89 spelling and preserves value flow.
vs=[]
for local in ['s','n','off']:
    old=('    char far *s;' if local=='s' else f'    int {local};')
    typ=('char far *' if local=='s' else 'int')
    vs.append((f'register-{local}',base.replace(old,f'    register {typ} {local};',1),''))
for locals_ in [('s','n'),('s','off'),('n','off'),('s','n','off')]:
    t=base
    for local in locals_:
        old=('    char far *s;' if local=='s' else f'    int {local};')
        typ=('char far *' if local=='s' else 'int')
        t=t.replace(old,f'    register {typ} {local};',1)
    vs.append(('register-'+'-'.join(locals_),t,''))
# Distinguish an offset register from a full far-pointer register and test the far pointer's
# top-level qualifier while retaining normal pointed-to char semantics.
vs.append(('register-s-unsigned-offset',base.replace('    char far *s;','    register char far *s;',1).replace('    int off;','    register unsigned int off;',1),''))
vs.append(('register-s-signed-char',base.replace('char far *s;','signed char far *s;',1),''))
vs.append(('register-s-unsigned-char',base.replace('char far *s;','unsigned char far *s;',1),''))
vs.append(('const-string-pointer',base.replace('char far *s;','const char far *s;',1),''))
vs.append(('volatile-pointer-object',base.replace('char far *s;','char far * volatile s;',1),''))
# Additional natural pointer-lifetime: keep base as a named alias used for start-offset selection,
# then traverse current pointer. This tests whether a live base pointer changes segment flow.
t=base.replace('    char far *s;','    char far *s;\n    char far *base;',1)
t=t.replace('    s = f_171C_1B84(list->text) + off;','    base = f_171C_1B84(list->text);\n    s = base + off;',1)
vs.append(('base-pointer-alias',t,''))
vs.append(('base-pointer-alias-through-pointer',t.replace('s += _fstrlen(s) + 1;','s = base + (s - base) + _fstrlen(s) + 1;',1),''))
vs.insert(0,('base',base,''))
out=Path('build/workers/fleet_list/register-pointer')
out.mkdir(parents=True,exist_ok=True)
rows=variants.run(ctx,vs,extra_funcs=[name],claims_only=True,jobs=2,out_dir=out)
(out/'results.json').write_text(json.dumps({'function':name,'profile':ctx.profile,'flags':ctx.flags,'placements':ctx.placements,'base_sha256':hashlib.sha256(base.replace('\r\n','\n').encode()).hexdigest(),'variants':rows},indent=1))
for x in rows:
    r=x['result']; c=r.get('claims',{}).get(name,{})
    failed=[q['name'] for q in ctx.claims if not r.get('claims',{}).get(q['name'],{}).get('exact')]
    print(x['name'],'exact=',c.get('exact'),'reasons=',c.get('reasons'), 'peer_losses=',failed)
