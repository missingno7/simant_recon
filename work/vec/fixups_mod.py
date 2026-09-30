"""List code fixups (pointer targets) of a canonical module object: every non-call fixup to a code symbol."""
import sys, json; sys.path.insert(0,'tools')
import compiler
from omf import OmfReader
key=sys.argv[1]
m=json.load(open('layout/manifest.json'))['modules'][key]
src=open(m['source']).read()
r=compiler.compile_c(src,m['profile'],m['flags']) if m.get('lang','c')=='c' else compiler.assemble(src,m['profile'],m['flags'])
o=OmfReader(communals=True).read(r.obj)
locs={}
for f in o.linker_fixups:
    locs.setdefault(f['loc'],0); locs[f['loc']]+=1
print(key, locs)
for f in o.linker_fixups:
    if f['loc'] in ('loader-offset16',) or (f['loc'] in ('offset16','base16') and f['target_kind'] in ('external','segment') and ('TEXT' in f['target'] or f['target'].startswith('_f_') or f['target'].startswith('_o'))):
        print('  ',f['segment'],hex(f['offset']), f['loc'], f['target_kind'], f['target'], f['frame_kind'], f.get('frame'), f['encoded_addend'])
