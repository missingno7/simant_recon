import json
seqs=json.load(open('build/scratch/relorder_seqs.json'))
cons=set()
for _,o in seqs:
    for i in range(len(o)):
        for j in range(i+1,len(o)):
            cons.add((o[i],o[j]))
cons=list(cons)
names=sorted({a for c in cons for a in c})
print(len(cons),'constraints',len(names),'names')
def hashes():
    def s(n,f=lambda c:c): return sum(f(ord(c)) for c in n)
    yield 'sum', lambda n: s(n)
    yield 'sum_upper', lambda n: s(n.upper())
    yield 'len', lambda n: len(n)
    def rot(n,sh,up=False):
        h=0
        for c in (n.upper() if up else n):
            h=((h<<sh)|(h>>(16-sh)))&0xffff; h^=ord(c)
        return h
    for sh in range(1,8):
        yield f'rotxor{sh}', lambda n,sh=sh: rot(n,sh)
        yield f'rotxor{sh}u', lambda n,sh=sh: rot(n,sh,True)
    def mul(n,k,up=False):
        h=0
        for c in (n.upper() if up else n): h=(h*k+ord(c))&0xffffffff
        return h
    for k in (2,3,5,7,31,33,37,131):
        yield f'mul{k}', lambda n,k=k: mul(n,k)
        yield f'mul{k}u', lambda n,k=k: mul(n,k,True)
    def pjw(n):
        h=0
        for c in n:
            h=(h<<4)+ord(c); g=h&0xf000
            if g: h^=g>>8; h&=~g
            h&=0xffff
        return h
    yield 'pjw16',pjw
best=[]
for name,h in hashes():
    for N in list(range(2,2048)):
        ok=0; ties=0
        for a,b in cons:
            ha,hb=h(a)%N,h(b)%N
            if ha<hb: ok+=1
            elif ha==hb: ties+=1
        best.append((ok+ties*0.5, ok, ties, name, N))
        # also descending
        ok2=sum(1 for a,b in cons if h(a)%N>h(b)%N)
        best.append((ok2+ties*0.5, ok2, ties, name+'_desc', N))
best.sort(reverse=True)
for b in best[:15]: print(b)
