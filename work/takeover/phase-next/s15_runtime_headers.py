from pathlib import Path
import sys,json,itertools
sys.path.insert(0,'tools')
import modctx,variants
name='o15_384C_0239';ctx=modctx.resolve(func=name);base=Path('work/takeover/phase-next/s15-base.c').read_text();vs=[]
for headers,placement in itertools.product([['stdio.h'],['stdlib.h'],['stdio.h','stdlib.h']],['top','runtime']):
 t=base
 for h in headers:
  t=t.replace('extern int far puts(char far *s);\n','') if h=='stdio.h' else t.replace('extern void far exit(int code);\n','')
 inc=''.join('#include <'+h+'>\n' for h in headers)
 if placement=='top':t=inc+t
 else:t=t.replace('extern void far f_171C_0676(int flag);',inc+'\nextern void far f_171C_0676(int flag);')
 vs.append(('-'.join(headers)+'-'+placement,t,''))
out=Path('build/workers/phase_next/s15-runtime-headers');out.mkdir(parents=True,exist_ok=True)
rows=variants.run(ctx,[('base',base,'')]+vs,extra_funcs=[name],claims_only=True,jobs=6,out_dir=out)
(out/'results.json').write_text(json.dumps({'function':name,'profile':ctx.profile,'flags':ctx.flags,'variants':rows},indent=1))
for x in rows:
 r=x['result'];print(x['name'],r.get('claims',{}).get(name),[c['name'] for c in ctx.claims if not r.get('claims',{}).get(c['name'],{}).get('exact')],r.get('log','')[-500:],flush=True)
