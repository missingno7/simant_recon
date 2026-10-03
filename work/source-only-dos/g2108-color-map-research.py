"""Original-only static research receipt for g_2108 color-map ownership.

This script is intentionally separate from the SOURCE_ONLY compiler/runtime
probe. It reads the original image only to identify the bounded data value,
references, and layouts, and emits hashes/facts only (never raw bytes).
"""
from __future__ import annotations
import hashlib, json, re, subprocess, sys
from pathlib import Path

def find_root():
    for p in Path(__file__).resolve().parents:
        if (p/'layout'/'manifest.json').is_file(): return p
    raise RuntimeError('cannot locate repo root')
ROOT=find_root()
OUT=ROOT/'build/workers/dos_color_translation_owners'
sys.path.insert(0,str(ROOT/'tools'))
import exe

DGROUP=0x55B3
def sha(data): return hashlib.sha256(data).hexdigest()
def pin(path):
    p=Path(path).resolve(); raw=p.read_bytes()
    try: name=p.relative_to(ROOT).as_posix()
    except ValueError: name=str(p).replace('\\','/')
    return {'path':name,'sha256':sha(raw),'size':len(raw)}

def dataref(module,offset):
    run=subprocess.run([sys.executable,str(ROOT/'tools/dataref.py'),module],cwd=ROOT,
      text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
    if run.returncode: raise RuntimeError('dataref failed: '+run.stdout[-2000:])
    rows=[x.strip() for x in run.stdout.splitlines()
      if re.match(r'^\s*'+re.escape(offset)+r'\s+DATA\b',x)]
    if not rows: raise RuntimeError(f'no dataref for {module}:{offset}')
    # dataref prints sampled bytes; retain only the structural symbol/use
    # fields so this research receipt never serializes original byte values.
    return [{'offset':parts[0],'record':parts[1],'view':parts[2],
      'consumer':parts[-1]} for parts in (row.split() for row in rows)]

def accepted_s03_map():
    text=(ROOT/'src/S03/m3126.asm').read_text(encoding='latin1')
    lines=text.splitlines(); start=None
    for i,line in enumerate(lines):
        if re.match(r'^\s*_g_2216\s+db\b',line,re.I): start=i; break
    if start is None: raise RuntimeError('accepted S03 _g_2216 source declaration missing')
    values=[]
    for i in range(start,len(lines)):
        line=lines[i]
        if i>start and re.match(r'^\s*[A-Za-z_.$?][\w.$?]*\s+(?:db|dw|dd|label|segment|ends)\b',line,re.I): break
        m=re.match(r'^\s*(?:_g_2216\s+)?db\s+(.+?)\s*(?:;.*)?$',line,re.I)
        if m:
            for token in m.group(1).split(','):
                token=token.strip()
                if token.lower().endswith('h'): values.append(int(token[:-1],16))
                else: values.append(int(token,10))
    if len(values)!=16 or any(v<0 or v>255 for v in values):
        raise RuntimeError('accepted S03 _g_2216 extent changed')
    return bytes(values)

def main():
    image=exe.load(); sec=image.sections[27]
    dg_base=DGROUP*16-sec.load_linear; dgroup=sec.data[dg_base:]
    original=dgroup[0x2108:0x2118]
    neighbor=dgroup[0x2100:0x2108]
    accepted=accepted_s03_map()
    direct_refs=[]
    for src in (ROOT/'src').rglob('*'):
        if src.suffix.lower() not in ('.asm','.c'): continue
        for line_no,line in enumerate(src.read_text(encoding='latin1').splitlines(),1):
            code=line.split(';',1)[0]
            names=[name for name in ('g_2108','g_2216','g_41C0') if name in code]
            if names: direct_refs.append({'path':src.relative_to(ROOT).as_posix(),'line':line_no,
              'names':names,'text':line.strip()})
    symbols=json.loads((ROOT/'layout/symbols.json').read_text(encoding='utf-8'))['data']
    views=[{'name':n,'off':r['off'],'alias_of':r.get('alias_of')}
      for n,r in symbols.items() if r.get('seg')==DGROUP and 0x2100<=r.get('off',-1)<0x2118]
    manifest=json.loads((ROOT/'layout/manifest.json').read_text(encoding='utf-8'))['modules']
    def span(key):
        p=manifest[key]['placements']['_DATA']
        return {'module':key,'source':manifest[key]['source'],'start':p['off'],'end':p['off']+p['size']}
    s00=span('S00:3126'); s01=span('S01:3126')
    r={
      'schema':'dos-g2108-original-research-v1','original_sha256':image.sha256,
      'g_2108':{'dgroup_offset':0x2108,'read_width':len(original),
        'value_sha256':sha(original),'accepted_source_value_sha256':sha(accepted),
        'matches_accepted_S03_g_2216_values':original==accepted},
      'neighbor_g_2100':{'dgroup_offset':0x2100,'read_width':len(neighbor),
        'value_sha256':sha(neighbor),'matches_0x80_shift_right_index':list(neighbor)==[0x80>>i for i in range(8)]},
      'registered_views_2100_2117':views,
      'known_datarefs':{'S00:31AD g_2108':dataref('S00:31AD','2108'),
        'S01:3126 g_2100':dataref('S01:3126','2100'),
        'S03:3126 g_2216':dataref('S03:3126','2216'),
        'root:1B4E g_41C0':dataref('root:1B4E','41C0')},
      'canonical_direct_identifier_refs':direct_refs,
      'accepted_neighbor_placements':{'previous':s00,'next':s01,
        'gap_2100_to_2118_is_24_bytes':s00['end']==0x2100 and s01['start']==0x2118},
      'inputs':[pin(ROOT/'layout/symbols.json'),pin(ROOT/'layout/manifest.json'),
        pin(ROOT/'src/S00/m31AD.asm'),pin(ROOT/'src/S00/m3126.asm'),pin(ROOT/'src/S01/m3126.asm'),
        pin(ROOT/'src/S03/m3126.asm'),pin(ROOT/'src/root/m1B4E.asm'),
        pin(ROOT/'tools/exe.py'),pin(ROOT/'tools/dataref.py'),pin(Path(__file__))],
      'raw_original_bytes_emitted':False}
    out=OUT/'g2108-original-research-report.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    if not r['g_2108']['matches_accepted_S03_g_2216_values']:
        raise RuntimeError('original bounded map differs from accepted S03 source values')
    if sum('g_2108' in x['names'] for x in direct_refs)!=2 or sum('g_2216' in x['names'] for x in direct_refs)!=2:
        raise RuntimeError('canonical direct identifier-reference inventory changed')
    print('g_2108_width',len(original),'original_slice_sha256',sha(original))
    print('g_2100_matches_bitmask',r['neighbor_g_2100']['matches_0x80_shift_right_index'])
    print('candidate_24_byte_gap',r['accepted_neighbor_placements']['gap_2100_to_2118_is_24_bytes'])
    print('matches_accepted_S03_map',r['g_2108']['matches_accepted_S03_g_2216_values'])
    print('raw_original_bytes_emitted',False,'report',out)

if __name__=='__main__': main()
