from pathlib import Path
import contextlib, hashlib, io, json, runpy, sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
import autosearch, compiler, csrc, functions, match, modctx, modules, search, slots, variants

TARGETS = {
    'o15_384C_0239': ROOT / 'src/S15/m384C.c',
    'FindIndex': ROOT / 'work/takeover/residue-controls/findindex-conditional-forms-v16.c',
    'f_171C_0CF4': ROOT / 'work/takeover/phase-next/memory-base.c',
}

def pin(path):
    b = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(b).hexdigest(), 'size': len(b)}

def save(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')

def review_inventory():
    exhausted = json.loads((ROOT / 'work/takeover/hardtail/exhaustion-index.json').read_text())
    selected = [r for r in exhausted['records'] if r['function'] in TARGETS]
    save(OUT / 'prior-index.json', selected)
    refs = set()
    for r in selected:
        for field in ('archived_report_artifacts', 'script_associations'):
            for item in r[field]:
                if isinstance(item, str):
                    refs.add(item)
                else:
                    for key in ('artifact', 'path', 'script', 'generator'):
                        if isinstance(item.get(key), str): refs.add(item[key])
    # The post-index retained storage/lifetime work is reviewed as well.
    for folder in ('residue-controls', 'blockers', 'phase-next'):
        for p in (ROOT / 'work/takeover' / folder).glob('*'):
            if p.suffix in ('.py', '.json') and (p.stem.startswith(('s15', 'memcf4', 'findindex', 'memory', 'index-trees'))):
                refs.add(str(p.relative_to(ROOT)))
    pins, summaries = [], []
    resolved = {str((ROOT / rel).resolve()).casefold(): (ROOT / rel).resolve() for rel in refs}
    for p in sorted(resolved.values(), key=lambda p:str(p).casefold()):
        rel = str(p.relative_to(ROOT))
        if not p.is_file(): continue
        pins.append(pin(p))
        if p.suffix != '.json': continue
        j = json.loads(p.read_text())
        if not isinstance(j, list): continue
        rows = [r for r in j if isinstance(r, dict) and 'compile_ok' in r]
        if not rows: continue
        good = [r for r in rows if r.get('compile_ok')]
        best = min(good, key=lambda r:r.get('score', [999]*4)) if good else {}
        summaries.append({'artifact': rel, 'rows':len(rows), 'compiled':len(good),
                          'exact':sum(bool(r.get('all_exact')) for r in rows),
                          'best':{k:best.get(k) for k in ('name','meta','score','length','reasons')},
                          'peer_regression_rows':sum(any(not ok for n,ok in r.get('claims',{}).items() if n not in TARGETS) for r in good),
                          'data_regression_rows':sum(any(not ok for ok in r.get('data',{}).values()) for r in good)})
    save(OUT / 'reviewed-evidence-pins.json', pins)
    save(OUT / 'reviewed-series-summary.json', summaries)
    print('Reviewed evidence pins',len(pins),'series',len(summaries))

def baseline(name, seed):
    ctx = modctx.resolve(func=name)
    canonical = ctx.text
    text = autosearch.unscaffold(canonical, name)
    if seed != ctx.source:
        f = csrc.Source(text).function(name)
        old = seed.read_text(encoding='latin1')
        sf = csrc.Source(old).function(name)
        text = text[:f.body.s] + old[sf.body.s:sf.body.e] + text[f.body.e:]
    targetdir = OUT / name
    targetdir.mkdir(exist_ok=True)
    draft = targetdir / 'module.c'
    draft.write_text(text, encoding='latin1', newline='\n')
    with (targetdir / 'search.log').open('w') as fh, contextlib.redirect_stdout(fh):
        search.run(name,[draft],None,None,None,{},False)
    collected = {}
    verdict = modules.verify_module(text,ctx.module_dict(),variants.check_set(ctx,[name],claims_only=True,text=text),collect=collected)
    save(targetdir / 'whole-module-verdict.json', verdict)
    (targetdir / 'module.obj').write_bytes(collected['object'])
    r = compiler.compile_c(text,ctx.profile,ctx.flags+['/Fc'],keep=True)
    if not r.ok: raise RuntimeError(r.log)
    listingpaths = list(r.workdir.glob('*.COD')) + list(r.workdir.glob('*.cod'))
    listing = listingpaths[0].read_text(encoding='latin1')
    (targetdir / 'module.cod').write_text(listing,encoding='latin1')
    (targetdir / 'listing-module.obj').write_bytes(r.obj)
    obj = modctx.read_obj(collected['object'])
    bound,_ = modctx.bind_function(ctx,obj,ctx.function(name))
    cand = search.disasm(bound.candidate,ctx.function(name)['off'])
    orig = search.disasm(bound.original,ctx.function(name)['off'])
    diffs = [{'index':i,'candidate':a,'original':b} for i,(a,b) in enumerate(zip(cand,orig)) if a[1]!=b[1]]
    bytesites=[{'relative':i,'candidate':a,'original':b} for i,(a,b) in enumerate(zip(bound.candidate,bound.original)) if a!=b]
    public,_ = match.public_in(obj,name)
    mapped = slots.parse_listing(listing,public)
    mapped['bpnames']={str(k):sorted(v) for k,v in mapped['bpnames'].items()}
    save(targetdir / 'instruction-residue.json',{'target':name,'candidate_extent':bound.candidate_extent_size,
         'target_extent':ctx.function(name)['size'],'candidate_insns':len(cand),'original_insns':len(orig),
         'differing_instructions':diffs,'differing_bytes':bytesites,'candidate_disassembly':cand,'original_disassembly':orig,
         'slots':mapped,'unbound':bound.unbound,'relocs_expected':sorted(bound.relocs_expected),
         'relocs_candidate':sorted(bound.relocs_candidate),'target_reasons':verdict['claims'][name].get('reasons',[]),
         'context':ctx.module_dict()})
    save(targetdir / 'identities.json',{'seed':pin(seed),'canonical':pin(ctx.source),'source':pin(draft),
         'object':pin(targetdir/'module.obj'),'listing_source_object':pin(targetdir/'listing-module.obj'),
         'listing':pin(targetdir/'module.cod'),'listing_object_identical':r.obj==collected['object']})
    with (targetdir / 'promote-verify-only.log').open('w') as fh, contextlib.redirect_stdout(fh),contextlib.redirect_stderr(fh):
        oldargv=sys.argv
        sys.argv=[str(ROOT/'tools/promote.py'),str(draft),'--module',ctx.key,'--claim',name,'--verify-only']
        try: runpy.run_path(str(ROOT/'tools/promote.py'),run_name='__main__')
        except SystemExit as e: print('exit',e.code)
        finally: sys.argv=oldargv
    print(name,'length',bound.candidate_extent_size,'byte residue',len(bytesites),
          'peer losses',[n for n in [c['name'] for c in ctx.claims] if not verdict['claims'][n]['exact']],
          'data losses',[n for n,r in verdict.get('data',{}).items() if not r['exact']],flush=True)
    print('instruction differences',diffs,flush=True)

if __name__=='__main__':
    compiler.WORK = OUT / 'cc'
    compiler.WORK.mkdir(exist_ok=True)
    search.ROOT = OUT / 'search-sandbox'
    review_inventory()
    if '--inventory-only' in sys.argv: raise SystemExit(0)
    save(OUT/'initial-authority-pins.json',[pin(ROOT/p) for p in ('layout/manifest.json','layout/oracle.lock.json','evidence/behavior/manifest.json','src/S15/m384C.c','src/root/m1986.c','src/root/m171C.c')])
    for name,seed in TARGETS.items(): baseline(name,seed)
