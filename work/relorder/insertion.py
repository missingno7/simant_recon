import json,struct,sys; sys.path.insert(0,'tools')
import exe
x=exe.load()
seqs=json.load(open('build/scratch/relorder_seqs.json'))
cons=set()
for _,o in seqs:
    for i in range(len(o)):
        for j in range(i+1,len(o)): cons.add((o[i],o[j]))
syms=json.load(open('layout/symbols.json'))
addr={}
for n,r in syms['runtime'].items(): addr[n]=(r['unit'],r['seg']*16+r['off'])
addr['_main']=('root',0x15F84)
# first reference: scan root relocs in table order and also by address
first_ref_tbl={}; first_ref_addr={}
lin2name={v[1]:k for k,v in addr.items() if v[0]=='root'}
for i,(s,o) in enumerate(x.relocs):
    a=s*16+o
    if x.image[a-3] in (0x9a,0xea):
        off=struct.unpack_from('<H',x.image,a-2)[0]; v=struct.unpack_from('<H',x.image,a)[0]
        n=lin2name.get(v*16+off)
        if n:
            first_ref_tbl.setdefault(n,i); first_ref_addr[n]=min(first_ref_addr.get(n,1<<30),a)
    else:
        v=struct.unpack_from('<H',x.image,a)[0]
        if v==0x55B3: first_ref_tbl.setdefault('DGROUP',i); first_ref_addr['DGROUP']=min(first_ref_addr.get('DGROUP',1<<30),a)
def test(key,label):
    ok=bad=miss=0; bads=[]
    for a,b in cons:
        if a not in key or b not in key: miss+=1; continue
        if key[a]<key[b]: ok+=1
        else: bad+=1; bads.append((a,b))
    print(label,'ok',ok,'bad',bad,'missing',miss, bads[:6])
test({k:v[1] for k,v in addr.items()},'definition address')
test(first_ref_tbl,'first reference (table)')
test(first_ref_addr,'first reference (address)')
for n in sorted(first_ref_addr,key=first_ref_addr.get)[:40]: print(n,hex(first_ref_addr[n]),hex(addr.get(n,('',0))[1]))
