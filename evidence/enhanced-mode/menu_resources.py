"""Reproduce menu-label provenance and the source wait census (local shipped assets).

Resource images are written only to the requested ignored build directory.
Transcriptions are presentation data, not recovered textual DOS resources.
"""
import argparse,hashlib,json,re,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from portable.tests.enhanced.assets import records

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();out=a.out.resolve()
    if not out.is_relative_to(ROOT/'build'):raise ValueError('Resource-derived images must stay under ignored build/')
    out.mkdir(parents=True,exist_ok=False)
    decoder,resources=records();labels=(ROOT/'portable/whole_program/enhanced/proximity_labels.inc').read_text()
    mappings=[]
    for match in re.finditer(r'\{(\d+),\{([^}]+)\}\}',labels):
        picture=int(match[1]);text=re.findall(r'"([^"]*)"',match[2]);payload=resources[2,picture];raw=payload
        if raw[:2]==b'\xff\xff':raw=decoder.lzss(raw[4:],struct.unpack_from('<H',raw,2)[0])
        typ,depth,_,_,w,h=struct.unpack_from('<6H',raw);depth&=255;stride=(w+7)//8;pixels=[]
        for y in range(h):
            row=raw[12+y*stride*(depth+(typ==3)):]
            for x in range(w):
                index=sum(((row[(plane+(typ==3))*stride+x//8]>>(7-x%8))&1)<<plane for plane in range(depth))
                pixels.append(index*255 if depth==1 else index*17)
        from PIL import Image
        im=Image.frombytes('L',(w,h),bytes(pixels));im.resize((w*4,h*4),Image.Resampling.NEAREST).save(out/(str(picture)+'.png'))
        mappings.append(dict(picture=picture,kind=2,payload_sha256=sha(payload),decoded_sha256=sha(raw),width=w,height=h,
                             labels=text,provenance='Human transcription of the shipped bitmap; no text payload exists in its type-1 hit objects.'))
    census=[]
    for folder in ('ui','window','startup'):
        for path in sorted((ROOT/'src'/folder).glob('*.c')):
            text=path.read_text();functions=list(re.finditer(r'(?m)^(?:static\s+)?(?:void|int|long|unsigned|char|struct)\b[^;{}]*?\b(\w+)\s*\([^;{}]*\)\s*\{',text))
            for i,fn in enumerate(functions):
                end=functions[i+1].start() if i+1<len(functions) else len(text);body=text[fn.end():end]
                waits=[(text.count('\n',0,fn.end()+m.start())+1,m.group(0).strip()) for m in re.finditer(r'(?m)^\s*(?:while\s*\([^\n]*|for\s*\(\s*;\s*;[^\n]*|do\s*$)',body)]
                if waits:census.append(dict(source=path.relative_to(ROOT).as_posix(),function=fn[1],waits=waits))
    report=dict(label_table_sha256=sha(labels.encode()),menus=mappings,source_wait_census=census,
                scope='Static loop census, including noninteractive loops. Reachability and presentation classification are in docs/enhanced-mode/menus.md.')
    (out/'resources.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(menus=len(mappings),functions_with_loops=len(census))))
if __name__=='__main__':main()
