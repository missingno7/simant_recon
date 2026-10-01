from pathlib import Path
import sys,re,itertools,json
sys.path.insert(0,'tools')
import csrc,modctx,variants
out=Path('build/workers/phase_next')
def run(name,base,vs,folder):
 ctx=modctx.resolve(func=name);d=out/folder;d.mkdir(parents=True,exist_ok=True)
 rows=variants.run(ctx,[('base',base,'')]+vs,extra_funcs=[name],claims_only=True,jobs=6,out_dir=d)
 (d/'results.json').write_text(json.dumps({'function':name,'profile':ctx.profile,'flags':ctx.flags,'variants':rows},indent=1))
 for x in rows:
  r=x['result'];print(folder,x['name'],r.get('claims',{}).get(name),[c['name'] for c in ctx.claims if not r.get('claims',{}).get(c['name'],{}).get('exact')],flush=True)
name='o15_384C_0239';base=Path('work/takeover/phase-next/s15-base.c').read_text();f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e];vs=[]
for sites,form in itertools.product(['first','second','both'],['union','first-member','void-cast']):
 bb=b
 if form=='union':
  bb=bb.replace('    struct Rect r;', '    union { struct Rect border; struct Rect text; } rect;')
  bb=re.sub(r'&r\b','&rect.border',bb,count=2);bb=re.sub(r'&r\b','&rect.text',bb)
 else:
  expr='(struct Rect far *)&r.left' if form=='first-member' else '(struct Rect far *)(void far *)&r'
  start=bb.index('    if (g_5A97 & 1)');end=bb.index('    win_GetObjRect(0x2101');stop=bb.index('    for (;;)')
  first=bb[start:end];second=bb[end:stop]
  if sites in ['first','both']:first=first.replace('&r',expr)
  if sites in ['second','both']:second=second.replace('&r',expr)
  bb=bb[:start]+first+second+bb[stop:]
 t=base[:f.body.s]+bb+base[f.body.e:]
 if any(t==v[1] for v in vs):continue
 vs.append((sites+'-'+form,t,''))
run(name,base,vs,'s15-rect-views')
name='f_171C_0CF4';base=Path('work/takeover/phase-next/memory-base.c').read_text();f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e];vs=[]
start=b.index('        n = BLK');end=b.index('        while');phase=b[start:end]
for alias,mode in itertools.product(['nb','adjacent'],['neighbor','scan','found']):
 bb=b
 if alias=='adjacent':bb=bb.replace('    Block far *nb;', '    Block far *nb;\n    Block far *adjacent;')
 if mode=='neighbor':
  p=re.sub(r'\bn\b',alias,phase)+'        n = '+alias+';\n';bb=bb.replace(phase,p)
 elif mode=='scan':
  p=phase+'        '+alias+' = n;\n';bb=bb.replace(phase,p)
  a=bb.index('        while');z=bb.index('        continue;\nfound:');bb=bb[:a]+re.sub(r'\bn\b',alias,bb[a:z])+bb[z:]
  bb=bb.replace('found:\n','found:\n        n = '+alias+';\n')
 else:
  bb=bb.replace('found:\n','found:\n        '+alias+' = n;\n')
  a=bb.index('found:');z=bb.index('        nb = b;');part=bb[a:z]
  # Only the copied source fields before nb becomes the destination alias.
  at=part.index(';')+1;part=part[:at]+re.sub(r'\bn\b',alias,part[at:]);bb=bb[:a]+part+bb[z:]
 t=base[:f.body.s]+bb+base[f.body.e:];vs.append((alias+'-'+mode,t,''))
run(name,base,vs,'memory-pointer-phases')
