"""Probe DOS-visible compiler path lengths using unchanged, hash-pinned AX tools.

Research only: copied profiles are not registered and cannot authorize promotion.
"""
from pathlib import Path
import sys, json, hashlib, shutil
from unittest.mock import patch
sys.path.insert(0,'tools')
import compiler, modules, variants, modctx, csrc, autosearch
OUT=Path('build/workers/siblings')
rows=[]
original=compiler._compile_dosbox
profile=compiler.verify_profile('msc600ax')
for name,saved in [('o15_384C_0239','work/takeover/blockers/s15-context-base.c'),
                   ('f_171C_0CF4','work/takeover/blockers/memory-views-v0.c')]:
    ctx=modctx.resolve(func=name)
    text=autosearch.unscaffold(ctx.text,name)
    prior=Path(saved).read_text(encoding='latin1')
    old=csrc.Source(prior).function(name); current=csrc.Source(text).function(name)
    text=text[:current.body.s]+prior[old.body.s:old.body.e]+text[current.body.e:]
    claims=variants.check_set(ctx,[name],claims_only=True,text=text)
    (OUT/(name+'-environment.c')).write_text(text,encoding='latin1')
    for binpath in ['BIN','B','COMPILER','NESTED/COMPILER']:
        dest=OUT/'environment-tools'/binpath.replace('/','_')
        files={}
        for rel,digest in profile['files'].items():
            changed=binpath+'/'+rel.split('/',1)[1] if rel.startswith('BIN/') else rel
            p=dest/changed; p.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(Path(profile['directory'])/rel,p)
            assert compiler._sha(p)==digest
            files[changed]=digest
        experimental=dict(profile,directory=str(dest.resolve()),bin=binpath.replace('/','\\'),files=files)
        def run(prof,runner,*args,**kwargs):
            return original(experimental,runner,*args,**kwargs)
        collected={}
        with patch.object(compiler,'_compile_dosbox',side_effect=run):
            result=modules.verify_module(text,ctx.module_dict(),claims,collect=collected)
        row={'function':name,'dos_bin_path':'D:\\'+binpath.replace('/','\\'),
             'compile_ok':result.get('compile_ok'),'source_sha256':hashlib.sha256(text.encode('latin1')).hexdigest(),
             'tool_files':files,'authority':'DIAGNOSTIC_ONLY; unregistered experimental environment'}
        if result.get('compile_ok'):
            bound,_=modctx.bind_function(ctx,modctx.read_obj(collected['object']),ctx.function(name))
            row.update(code_sha256=hashlib.sha256(bound.candidate).hexdigest(),
                       exact=result['claims'][name]['exact'],reasons=result['claims'][name].get('reasons'),
                       peer_losses=[c['name'] for c in ctx.claims if not result['claims'][c['name']]['exact']],
                       data_losses=[s for s,r in result.get('data',{}).items() if not r['exact']])
        else:row['log']=result.get('log','')[-1000:]
        rows.append(row); (OUT/'environment.json').write_text(json.dumps(rows,indent=1))
        print(name,binpath,row.get('exact'),row.get('reasons',row.get('log')),flush=True)
