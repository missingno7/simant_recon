from pathlib import Path
import sys,itertools,json,re
sys.path.insert(0,'tools')
import modctx,variants
name='o15_384C_0239';ctx=modctx.resolve(func=name);base=Path('work/takeover/phase-next/s15-base.c').read_text();vs=[]
for mask,style,ptr in itertools.product(range(1,4),['named','anonymous'],[False,True]):
 t=base
 if ptr:
  t=t.replace('typedef char far * far *Handle;', 'typedef char far *TextPtr;\ntypedef TextPtr far *Handle;')
  t=re.sub(r'(?<!unsigned )\bchar far \*','TextPtr ',t)
  t=t.replace('typedef TextPtr TextPtr;', 'typedef char far *TextPtr;')
 for i,tag in enumerate(['Event','Rect']):
  if not mask&(1<<i):continue
  pat=r'struct '+tag+r' \{[^}]+\};';m=re.search(pat,t);assert m
  definition=m.group()
  definition=('typedef '+definition[:-1]+' '+tag+';' if style=='named' else 'typedef '+definition.replace('struct '+tag,'struct')[:-1]+' '+tag+';')
  a,b=m.span();t=t[:a]+definition+t[b:]
  # Leave the tag in its definition, replace its actual uses after it.
  stop=a+len(definition);t=t[:stop]+t[stop:].replace('struct '+tag,tag)
 vs.append((f'm{mask}-{style}-textptr{ptr}',t,''))
# A TextPtr-only control makes the new alias used in the handle and real prototypes.
t=base.replace('typedef char far * far *Handle;', 'typedef char far *TextPtr;\ntypedef TextPtr far *Handle;');t=re.sub(r'(?<!unsigned )\bchar far \*','TextPtr ',t).replace('typedef TextPtr TextPtr;', 'typedef char far *TextPtr;');vs.append(('textptr-only',t,''))
out=Path('build/workers/phase_next/s15-type-context');out.mkdir(parents=True,exist_ok=True)
rows=variants.run(ctx,[('base',base,'')]+vs,extra_funcs=[name],claims_only=True,jobs=6,out_dir=out)
(out/'results.json').write_text(json.dumps({'function':name,'profile':ctx.profile,'flags':ctx.flags,'variants':rows},indent=1))
for x in rows:
 r=x['result'];print(x['name'],r.get('claims',{}).get(name),[c['name'] for c in ctx.claims if not r.get('claims',{}).get(c['name'],{}).get('exact')],r.get('log','')[-100:],flush=True)
