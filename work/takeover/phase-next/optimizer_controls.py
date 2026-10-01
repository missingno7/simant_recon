from pathlib import Path
import sys,json,concurrent.futures,dataclasses,hashlib
sys.path.insert(0,'tools')
import modctx,variants,modules
out=Path('build/workers/phase_next/optimizer-controls');out.mkdir(parents=True,exist_ok=True)
sets=[('o15_384C_0239','work/takeover/phase-next/s15-base.c'),('f_171C_0CF4','work/takeover/phase-next/memory-base.c'),('o25_3BA4_1035','work/takeover/phase-next/s25-base.c')]
items=[]
for name,path in sets:
 ctx=modctx.resolve(func=name);text=Path(path).read_text();claims=variants.check_set(ctx,[name],claims_only=True,text=text)
 for extra in [[],['/Oa'],['/Ol'],['/Oz'],['/Or'],['/Oa','/Ol'],['/Oa','/Ol','/Oz','/Or']]:items.append((ctx,text,claims,name,'msc600ax',ctx.flags+extra))
 if name!='o15_384C_0239':
  for profile in ['msc600','msc600a']:items.append((ctx,text,claims,name,profile,ctx.flags))
def run(item):
 ctx,text,claims,name,profile,flags=item;m=ctx.module_dict();m['profile']=profile;m['flags']=flags;collect={}
 r=modules.verify_module(text,m,claims,collect=collect)
 row={'function':name,'profile':profile,'flags':flags,'source_sha256_lf':hashlib.sha256(text.encode()).hexdigest(),'compile_ok':r.get('compile_ok'),'target':r.get('claims',{}).get(name),'peer_losses':{c['name']:r.get('claims',{}).get(c['name']) for c in ctx.claims if not r.get('claims',{}).get(c['name'],{}).get('exact')},'data':r.get('data'),'module_exact':r.get('exact'),'log':r.get('log','')[-500:]}
 if r.get('compile_ok'):
  local=dataclasses.replace(ctx,profile=profile,flags=flags);bound,_=modctx.bind_function(local,modctx.read_obj(collect['object']),local.function(name));row['code_sha256']=hashlib.sha256(bound.candidate).hexdigest()
 print(name,profile,flags,row['target'],list(row['peer_losses']),flush=True)
 return row
with concurrent.futures.ThreadPoolExecutor(6) as pool:rows=list(pool.map(run,items))
(out/'results.json').write_text(json.dumps(rows,indent=1))
