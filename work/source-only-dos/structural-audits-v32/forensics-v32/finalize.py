from pathlib import Path
import hashlib, json, subprocess, sys

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
def pin(p):
    b=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'size':len(b)}

initial=json.loads((OUT/'initial-authority-pins.json').read_text())
authority=[]
for row in initial:
    now=pin(Path(row['path']))
    authority.append({'initial':row,'final':now,'unchanged':row['sha256']==now['sha256']})
(OUT/'authority-unchanged.json').write_text(json.dumps(authority,indent=2)+'\n')
for name in ('o15_384C_0239','FindIndex','f_171C_0CF4'):
    r=subprocess.run([sys.executable,str(ROOT/'tools/context.py'),name],cwd=ROOT,capture_output=True,text=True)
    (OUT/name/'context.log').write_text(r.stdout+r.stderr)
    j=json.loads((OUT/name/'whole-module-verdict.json').read_text())
    target=j['claims'][name]
    neg={'schema':'bounded-historical-residue-negative-v32','target':name,'root_review':'PENDING',
         'new_hypothesis_families':0,'new_family_compiles':0,'fresh_baseline_compiles':4,
         'conclusion':'NO_CREDIBLE_UNEXPLORED_C_HYPOTHESIS_AFTER_RETAINED_EVIDENCE_REVIEW',
         'target_exact':target['exact'],'target_reasons':target.get('reasons',[]),
         'peer_losses':[n for n,r in j['claims'].items() if n!=name and not r['exact']],
         'data_losses':[n for n,r in j.get('data',{}).items() if not r['exact']],
         'promotion':'NOT_RUN','semantics':'Existing 29 strict semantics unchanged; no new receipt or claim.'}
    (OUT/name/'negative-result.json').write_text(json.dumps(neg,indent=2)+'\n')
files=[]
for p in OUT.rglob('*'):
    if not p.is_file() or 'cc' in p.relative_to(OUT).parts or p.name=='stable-artifacts.json': continue
    files.append(pin(p))
(OUT/'stable-artifacts.json').write_text(json.dumps({'schema':'stable-historical-forensics-v32',
    'root_review':'PENDING','authority_unchanged':all(r['unchanged'] for r in authority),
    'fresh_compiles':12,'new_families':0,'expansion':'NONE','artifacts':sorted(files,key=lambda r:r['path'])},indent=2)+'\n')
print('Artifacts stable; root review pending. Authority pins unchanged:',all(r['unchanged'] for r in authority))
print('Report SHA-256',pin(OUT/'REPORT.md')['sha256'])
print('Stable index SHA-256',pin(OUT/'stable-artifacts.json')['sha256'])
