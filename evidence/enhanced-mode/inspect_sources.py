import sys
sys.dont_write_bytecode = True
from pathlib import Path
import importlib.util, json, struct, re, hashlib
ROOT=Path('D:/Prog/simant_recon')
OUT=ROOT/'build/workers/enhanced-design'
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
d=module('shipped',ROOT/'evidence/canonical/audio-track-owner/shipped_domain.py')
original_parse_ndx=d.parse_ndx
def parse_ndx(raw,label):
    count=struct.unpack_from('<H',raw)[0]
    if len(raw)==20+count*8:return [struct.unpack_from('<IhBB',raw,20+i*8) for i in range(count)]
    return original_parse_ndx(raw,label)
d.parse_ndx=parse_ndx
r=module('domains',ROOT/'tools/resource_domains.py')
result={}
for edition,assets,stems in [('dos',ROOT/'assets',['HCEGANT','SHARED']),('win16',Path('D:/Games/ANTWIN'),['WINGANT','MWINNT','SHARED'])]:
    d.ASSETS=assets;rows=[]
    for stem in stems:
        try: _,records=d.parse_records(stem)
        except Exception as e: rows.append({'stem':stem,'error':str(e)});continue
        for a in records:
            b=a['payload'];entry={k:a[k] for k in ['id','kind','flags']};entry['stem']=stem
            if a['kind']==0:
                entry['header']=list(struct.unpack_from('<22h',b)) if len(b)>=44 else []
                entry['strings']=[s.decode('cp437',errors='replace') for s in re.findall(rb'[\x20-\x7e]{3,}',b)]
                try:
                    entry['objects']=r.window_domain(b)
                    for obj in entry['objects']['objects']:
                        p=obj['offset'];obj['rect_initial']=list(struct.unpack_from('<4h',b,p));obj['layout_xywh']=list(struct.unpack_from('<4h',b,p+8))
                        obj['payload_words']=list(struct.unpack_from('<'+'h'*((obj['size']-40)//2),b,p+40))
                        if obj['type'] in (5,9,12):obj['inline_text']=b[p+42:p+obj['size']].split(b'\0')[0].decode('cp437',errors='replace')
                        elif obj['type'] in (16,17,18):obj['inline_text']=b[p+46:p+obj['size']].split(b'\0')[0].decode('cp437',errors='replace')
                except Exception as e:entry['parse_error']=str(e)
            elif a['kind']==6:
                try:
                    tables=r.menu_domain(b)['lists'];entry['lists']=[[b[p:b.index(0,p)].decode('cp437') for p in t['string_offsets']] for t in tables]
                except Exception as e:entry['parse_error']=str(e)
            elif a['kind'] in (4,5,7,8,9):
                entry['strings']=[s.decode('cp437',errors='replace') for s in re.findall(rb'[\x20-\x7e]{4,}',b)]
                if not entry['strings']: continue
            else:continue
            rows.append(entry)
    result[edition]=rows
m=module('macref',Path('D:/Prog/simantw_recon/tools/mac_ref.py'))
iso=Path('D:/Games/DOS/dos_recosystem/simantmac_forged/assets/SimAnt_CD.iso').read_bytes()
part=next(p for p in m.parse_apm(iso) if p['type']=='Apple_HFS');h=m.hfs_volume_info(iso,part)
app=next(f for f in m.parse_hfs_catalog(h['catalog']) if f.get('creator')=='SANT' and f.get('finder_type')=='APPL')
fork=m.read_hfs_fork(iso,part['start_block']*part['block_size'],h['allocation_start_512'],h['allocation_block_size'],app['resource_extents'],app['resource_size'])
assert m.sha256(iso)==m.EXPECTED_ISO_SHA256 and m.sha256(fork)==m.EXPECTED_RSRC_SHA256
resources,_=m.parse_resource_fork(fork);mac=[]
def pstr(b,p):return b[p+1:p+1+b[p]].decode('mac_roman'),p+1+b[p]
for a in resources:
    typ=a['type'];b=a['data'];e={k:v for k,v in a.items() if k!='data'}
    if typ=='MENU':
        title,p=pstr(b,14);items=[]
        while p<len(b) and b[p]:
            text,p=pstr(b,p);items.append({'text':text,'icon_key_mark_style':list(b[p:p+4])});p+=4
        e.update(title=title,items=items)
    elif typ in ('WIND','DLOG','ALRT','CNTL'):
        e['bounds_tlbr']=list(struct.unpack_from('>4h',b))
        e['hex']=b.hex()
        if typ=='WIND':e['title']=pstr(b,16)[0]
        if typ=='DLOG':e['title']=pstr(b,20)[0]
    elif typ=='DITL':
        p=2;items=[]
        for i in range(m.be16(b,0)+1):
            rect=list(struct.unpack_from('>4h',b,p+4));t=b[p+12];size=b[p+13];data=b[p+14:p+14+size]
            items.append({'type':t,'bounds':rect,'text':data.decode('mac_roman') if (t&0x7f) in (4,5,6,8,16) else data.hex()});p+=14+size+(size%2)
        e['items']=items
    elif typ=='STR#':e['strings']=m.decode_string_list(b)
    elif typ in ('TEXT','CARD'):
        e['text']=b.decode('mac_roman',errors='replace')
    else:continue
    mac.append(e)
result['mac']=mac
result['identities']={'iso_sha256':m.sha256(iso),'mac_resource_sha256':m.sha256(fork)}
(OUT/'resource-inventory.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
for edition in ('dos','win16'):
    print('\n'+edition)
    for e in result[edition]:
        if e.get('kind')==0:print(e['stem'],hex(e['id']),e['strings'])
        if e.get('kind')==6:print('MENU',e['id'],e.get('lists',e))
print('\nMAC')
for e in mac:
    if e['type'] in ('MENU','WIND','DLOG','CNTL','DITL'):print(e['type'],e['id'],e.get('name'),e.get('title',''),e.get('bounds_tlbr',''),e.get('items',''))
