"""Independent resource-decoder comparison against a test-probe catalog dump.

Resource-derived bytes are read locally and never retained in tracked files.
"""
from pathlib import Path
import argparse,importlib.util,json,struct
ROOT=Path(__file__).resolve().parents[3]

def records():
    spec=importlib.util.spec_from_file_location('shipped',ROOT/'evidence/canonical/audio-track-owner/shipped_domain.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m,{(r['kind'],r['id']):r['payload'] for stem in ('HCEGANT','SHARED') for r in m.parse_records(stem)[1] if stem=='HCEGANT' or r['kind']==2}

def tile(bits):
    return bytes(sum(((bits[y*8+p*2+x//8]>>(7-x%8))&1)<<p for p in range(4)) for y in range(16) for x in range(16))

def compare(dump):
    decoder,resources=records();data=dump.read_bytes();tested=0
    assert len(data)%268==0
    for at in range(0,len(data),268):
        terrain_set,ground,code=struct.unpack_from('<3I',data,at)
        background=resources[9,10-terrain_set][ground*128:(ground+1)*128]
        if code:
            if code>=0x380: bank,n=14,code-0x280
            elif code>=0x200:bank,n=13,code-0x200
            else:bank,n=14,code-0x100
            mode=0 if 0xf0<=n<=0xff else (0,3,1)[n>>7]
            record=resources[9,bank][(n&127)*192:(n&127)*192+192];out=bytearray()
            for y in range(16):
                mask,prefix,*fg=struct.unpack_from('<6H',record,y*12)
                for plane,bg in enumerate(struct.unpack_from('<4H',background,y*8)):
                    v=bg^((fg[plane]^bg)&mask)
                    if mode==0 or mode==3 and plane==1:v^=prefix
                    out+=struct.pack('<H',v)
            background=out
        assert tile(background)==data[at+12:at+268],(terrain_set,ground,code)
        tested+=1
    picture_data=Path(str(dump)+'.pictures').read_bytes();at=0;seen=set();pixels=0
    while at<len(picture_data):
        id,w,h=struct.unpack_from('<3I',picture_data,at);at+=12
        p=resources[2,id]
        if p[:2]==b'\xff\xff':p=decoder.lzss(p[4:],struct.unpack_from('<H',p,2)[0])
        type,depth,_,_,pw,ph=struct.unpack_from('<6H',p);depth &=255
        assert (w,h)==(pw,ph)
        stride=(w+7)//8;out=bytearray()
        for y in range(h):
            row=p[12+y*stride*(depth+(type==3)):]
            for x in range(w):
                v=sum(((row[(plane+(type==3))*stride+x//8]>>(7-x%8))&1)<<plane for plane in range(depth))
                if depth==1:v=15 if v else 0
                out.append(255 if type==3 and not (row[x//8]&(128>>(x%8))) else v)
        assert out==picture_data[at:at+w*h],id
        at+=w*h;seen.add(id);pixels+=w*h
    expected={id for kind,id in resources if kind==2}
    assert seen==expected
    return dict(passed=True,cell_cases=tested,pictures=len(seen),picture_pixels=pixels,
        scope='Both terrain sets, every ground tile, every life/recolour code on three backgrounds, all shipped HCEGANT/SHARED pictures; independent Python decode.')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dump',type=Path);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();result=compare(a.dump);a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
