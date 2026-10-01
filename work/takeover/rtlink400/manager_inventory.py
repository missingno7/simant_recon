from pathlib import Path
import sys,json,hashlib
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'))
from omf import OmfReader
out=ROOT/'work/takeover/rtlink400';d=Path(sys.argv[1]);r=OmfReader()
rows=[]
for idx,(name,blob) in enumerate(r.split_library((d/'RTLUTILS.LIB').read_bytes())):
    m=r.read(blob);pubs=[p for p in m.publics if p['name'].startswith('$$')]
    segments=[]
    for sd in m.segment_defs:
        sn=sd['name']
        if sn not in m.segments:continue
        body=m.segment_bytes(sn)
        segments.append({'name':sn,'class':sd.get('class'),'length':len(body)})
    rows.append({'member':idx,'name':name,'object_sha256':hashlib.sha256(blob).hexdigest(),'publics':pubs,'segments':segments})
(out/'manager-inventory.json').write_text(json.dumps(rows,indent=1))
print([(q['member'],q['name'],q['segments'],[p['name'] for p in q['publics'] if 'INIT' in p['name']]) for q in rows[:9]])
(out/'payload-manifest.json').write_text(json.dumps({p.name:{'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(d.glob('*')) if p.is_file()},indent=1))
