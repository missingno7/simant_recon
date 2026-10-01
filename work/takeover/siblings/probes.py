"""Sibling-inspired controls. Whole modules; no gate or profile changes."""
from pathlib import Path
import sys, json, hashlib, itertools
from unittest.mock import patch
ROOT = Path.cwd()
sys.path.insert(0, str(ROOT/'tools'))
import compiler, modules, modctx, variants, autosearch, csrc
OUT = ROOT/'build/workers/siblings'

def filenames():
    rows=[]
    original_compile=compiler.compile_c
    for name, source in [('o15_384C_0239','work/takeover/blockers/s15-context-base.c'),
                         ('f_171C_0CF4','work/takeover/blockers/memory-views-v0.c'),
                         ('CalcScore',None),('o25_3BA4_1035',None)]:
        ctx=modctx.resolve(func=name)
        text=autosearch.unscaffold(ctx.text,name)
        if source:
            saved=Path(source).read_text(encoding='latin1')
            old=csrc.Source(saved).function(name)
            current=csrc.Source(text).function(name)
            text=text[:current.body.s]+saved[old.body.s:old.body.e]+text[current.body.e:]
        claims=variants.check_set(ctx,[name],claims_only=True,text=text)
        draft=OUT/(name+'-filename.c'); draft.write_text(text,encoding='latin1')
        for base in ['U','UN','UNI','UNIT','UNITS','UNITSS','UNITSSS','UNITSSSS']:
            def run(source,profile,flags=None,**kw):
                kw['basename']=base
                return original_compile(source,profile,flags,**kw)
            col={}
            with patch.object(compiler,'compile_c',side_effect=run):
                result=modules.verify_module(text,ctx.module_dict(),claims,collect=col)
            row={'function':name,'basename':base,'compile_ok':result.get('compile_ok'),
                 'source_sha256':hashlib.sha256(text.encode('latin1')).hexdigest()}
            if result.get('compile_ok'):
                bound,_=modctx.bind_function(ctx,modctx.read_obj(col['object']),ctx.function(name))
                row.update(code_sha256=hashlib.sha256(bound.candidate).hexdigest(),
                           exact=result['claims'][name]['exact'],
                           reasons=result['claims'][name].get('reasons'),
                           peer_losses=[c['name'] for c in ctx.claims if not result['claims'][c['name']]['exact']],
                           data_losses=[s for s,r in result.get('data',{}).items() if not r['exact']])
            else: row['log']=result.get('log','')[-500:]
            rows.append(row)
            (OUT/'filenames.json').write_text(json.dumps(rows,indent=1))
        print(name,'filename code identities',len({r.get('code_sha256') for r in rows if r['function']==name}),flush=True)

def scopes():
    name='CalcScore'; ctx=modctx.resolve(func=name)
    text=autosearch.unscaffold(ctx.text,name); f=csrc.Source(text).function(name)
    body=text[f.body.s:f.body.e]
    start=body.index('    j = (fd_50F6_04F4')
    stop=body.index('    if (fd_50F6_0FC2')
    phase=body[start:stop]
    candidates=[]
    for rename in [False,True]:
        for order in itertools.permutations(['j','sum','sum2']):
            for grouped in [False,True]:
                names=list(order)
                if rename: names=['historyIndex' if x=='j' else 'historySum' if x=='sum' else x for x in names]
                decl=('    int '+', '.join(names)+';\n' if grouped else ''.join('    int '+n+';\n' for n in names))
                part=phase
                if rename:
                    import re
                    part=re.sub(r'\bj\b','historyIndex',part)
                    part=re.sub(r'\bsum\b','historySum',part)
                bb=body[:start]+'    {\n'+decl+part+'    }\n\n'+body[stop:]
                bb=bb.replace('    int sum, sum2;', '    int sum;')
                if not rename:
                    # All early uses are local to the block; later j/sum retain their own homes.
                    pass
                candidates.append(text[:f.body.s]+bb+text[f.body.e:])
    ev=autosearch.Evaluator(ctx,name,6,OUT/'scope-cache')
    base=ev.one(text); ev.set_base(base)
    rows=[]; folder=OUT/'scopes'; folder.mkdir(exist_ok=True)
    for i,(candidate,result) in enumerate(zip(candidates,ev.many(candidates))):
        p=folder/f'v{i}.c'; p.write_text(candidate,encoding='latin1')
        rows.append({'draft':str(p),'source_sha256':hashlib.sha256(candidate.encode('latin1')).hexdigest(),
                     'peer_losses':ev.regressions(result),**result})
    ev.save(); (OUT/'scopes.json').write_text(json.dumps({'base':base,'variants':rows},indent=1))
    print('CalcScore scopes',len(rows),'exact',sum(r.get('all_exact',False) for r in rows),
          'best',min(r.get('score',[9]) for r in rows),flush=True)

if __name__=='__main__':
    filenames()
    scopes()
