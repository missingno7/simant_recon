"""Ownership exclusion test: a TU that defines far variables in its own segment references them
through CONST words whose fixup target is that *segment* (exp1), so all such words fall in one
RTLink target group = one contiguous run of the S27 relocation list.  A module whose words to
frame F appear in >=2 separate runs therefore references F only through external symbols."""
import json, collections
R=json.load(open('build/workers/data/s27_relocs.json'))
man=json.load(open('layout/manifest.json'))['modules']
d=json.load(open('build/workers/data/refs.json'))
# owner of each CONST word by link-order region: word site -> module (placement or dominant user)
cw=json.load(open('build/workers/data/constwords.json'))
runid=0; prev=None; runs=[]
for r in R:
    if prev is None or r['val']!=prev: runid+=1
    prev=r['val']; runs.append(runid)
res=collections.defaultdict(lambda: collections.defaultdict(set))
for r,rid in zip(R,runs):
    site=r['site']
    if not site.startswith('DG:'): continue
    off=site[3:]
    users=cw.get(off,{}).get('users',[])
    mod=(r['owner'] or '').split('/')[0] or (users[0] if len(users)==1 else None)
    if mod is None: continue
    res[r['val']][mod].add(rid)
for f in ('3D57','3E1D','4DA7','4E37','4F6F','5071','50EF','50F6','4E4B','4EE5'):
    mods=res.get(f,{})
    single=sorted(m for m,s in mods.items() if len(s)==1)
    multi=sorted(m for m,s in mods.items() if len(s)>1)
    print(f, 'excluded(>=2 runs):',len(multi), ' possible(1 run):', single)
