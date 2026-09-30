import sys,json; sys.path.insert(0,'tools')
import exe
from omf import OmfReader
from collections import defaultdict
x=exe.load()
rd=OmfReader(communals=True)
libs={'llibcr.lib':'C:/tools/msc-6.00/LIB/llibcr.lib','libh.lib':'C:/tools/msc-6.00/LIB/libh.lib'}
mods={}
for k,p in libs.items():
    for n,b in rd.split_library(open(p,'rb').read()): mods[(k,n)]=b
loc=json.load(open('evidence/toolchain/runtime-location.json'))['members']
relidx={s*16+o:i for i,(s,o) in enumerate(x.relocs)}
seqs=[]
for m in loc:
    obj=rd.read(mods[(m['library'],m['member'])],m['member'])
    segs=[s['name'] for s in obj.segment_defs if s['class']=='CODE']
    fx=[f for f in obj.linker_fixups if f['segment'] in segs and f['loc'] in('pointer32','base16')]
    items=[]
    for f in fx:
        a=m['linear']+f['offset']+(2 if f['loc']=='pointer32' else 0)
        if a in relidx: items.append((relidx[a],f['target'],a))
    items.sort()
    order=[]
    for _,t,_ in items:
        if not order or order[-1]!=t: order.append(t)
    seqs.append((m['member'],order,items))
json.dump([(a,b) for a,b,c in seqs],open('build/scratch/relorder_seqs.json','w'))
split=sum(1 for _,o,_ in seqs if len(o)!=len(set(o)))
print('members',len(seqs),'with split groups',split)
edges=defaultdict(set)
for _,o,_ in seqs:
    for i in range(len(o)):
        for j in range(i+1,len(o)):
            if o[i]!=o[j]: edges[o[i]].add(o[j])
conf=[(a,b) for a in edges for b in edges[a] if a in edges.get(b,())]
print('pairwise conflicts',len(conf)//2, conf[:10])
for n,o,_ in seqs:
    if len(o)>=3: print(n,o)

print('--- EXTDEF order test')
good=bad=0
for m in loc:
    obj=rd.read(mods[(m['library'],m['member'])],m['member'])
    order=[o for n,o,_ in seqs if n==m['member']][0]
    ext=[e for e in obj.externals]
    pos={e:i for i,e in enumerate(ext)}
    ks=[pos.get(t,-1) for t in order]
    if ks==sorted(ks): good+=1
    else:
        bad+=1
        if bad<8: print(m['member'],order,'extdef:',ext[:12], [s['name'] for s in obj.segment_defs][:6], obj.groups[:1])
print('extdef-order consistent',good,'inconsistent',bad)
