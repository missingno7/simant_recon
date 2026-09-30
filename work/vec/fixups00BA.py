import sys; sys.path.insert(0,'tools')
import compiler
from omf import OmfReader
src=open(sys.argv[1]).read()
r=compiler.compile_c(src,'msc600ax',['/AL','/Os','/Oe','/Og','/Zi'])
o=OmfReader(communals=True).read(r.obj)
print([ (p['name'],p['offset']) for p in o.publics])
for f in o.linker_fixups:
    if f['segment'].endswith('_TEXT') and f['offset']<0xB0:
        print(hex(f['offset']), f['loc'], f['target_kind'], f['target'], f['frame_kind'], f.get('frame'), f['encoded_addend'], f.get('displacement'))
