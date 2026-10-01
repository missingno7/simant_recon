from pathlib import Path
import sys,json,hashlib
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'))
import modctx,variants
out=ROOT/'build/workers/fleet_index';basepath=out/'findindex-base.c';base=basepath.read_text(encoding='latin1');ctx=modctx.resolve(func='FindIndex',source=basepath)
inputs=[('base',base)]
for family in ['initial','novel','followup']:
    directory=out/family
    for p in sorted(directory.glob('*.c')):
        if p.name.startswith('000_base'):continue
        inputs.append((family+'/'+p.stem,p.read_text(encoding='latin1')))
auditdir=out/'audit_sources';auditdir.mkdir(parents=True,exist_ok=True)
rows=variants.run(ctx,[(n,t,'') for n,t in inputs],extra_funcs=['FindIndex'],claims_only=True,jobs=2,out_dir=auditdir)
peer_names=[c['name'] for c in ctx.claims]
summary=[]
for (name,text),row in zip(inputs,rows):
    r=row['result'];claims=r.get('claims',{})
    summary.append({'name':name,'source_sha256':hashlib.sha256(text.encode('latin1')).hexdigest(),'compile_ok':r.get('compile_ok'),'FindIndex':claims.get('FindIndex',{}),'existing_claims':{n:claims.get(n,{}) for n in peer_names},'data':r.get('data',{}),'module_exact':r.get('exact'),'warnings':r.get('warnings',[])})
(out/'whole-module-audit.json').write_text(json.dumps({'module':ctx.key,'profile':ctx.profile,'flags':ctx.flags,'placements':ctx.placements,'variants':len(inputs)-1,'positive_peer_claims':peer_names,'rows':summary},indent=2,default=str))
print('variants',len(inputs)-1,'all peer claims exact',all(all(s.get('exact') for s in x['existing_claims'].values()) for x in summary),'all data exact',all(all(s.get('exact') for s in x['data'].values()) for x in summary),'FindIndex exact',sum(bool(x['FindIndex'].get('exact')) for x in summary))
for x in summary:
    print(x['name'],'compile',x['compile_ok'],'FindIndex',x['FindIndex'].get('reasons'),'peers',all(s.get('exact') for s in x['existing_claims'].values()),'data',all(s.get('exact') for s in x['data'].values()),x['source_sha256'])
