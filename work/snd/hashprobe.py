import sys, re, itertools, random
sys.path.insert(0,'D:/Prog/simant_recon/tools'); sys.path.insert(0,'C:/tools/capstone-5.0.3')
import compiler, omf
from capstone import Cs, CS_ARCH_X86, CS_MODE_16
md=Cs(CS_ARCH_X86,CS_MODE_16)
def slots(names):
    decl=''.join(f'    int {n};\n' for n in names)
    asm=''.join(f'        mov ax, {n}\n' for n in names)
    src=f'int far f(void)\n{{\n{decl}\n    _asm {{\n{asm}    }}\n    return 0;\n}}\n'
    r=compiler.compile_c(src,'msc600ax',['/AL','/Os','/Oe','/Og','/Gs'])
    o=omf.OmfReader().read(r.obj)
    b=o.segments['UNIT_TEXT']
    out=[]
    for i in md.disasm(b,0):
        m=re.search(r'\[bp - (0x[0-9a-f]+|\d+)\]',i.op_str)
        if i.mnemonic=='mov' and m: out.append(int(m.group(1),0))
    return dict(zip(names,out))
random.seed(int(sys.argv[1]) if len(sys.argv)>1 else 0)
tests=[['a','b','c','d','e'],['e','d','c','b','a'],['aa','b','c'],['x','v','port','c1','f'],['f','c1','port','v','x']]
for t in tests: print(t, slots(t))
def order(names):
    s=slots(names); return [n for n,_ in sorted(s.items(), key=lambda kv: kv[1])]
if len(sys.argv)>2:
    for grp in sys.argv[2:]:
        print(grp, order(grp.split(',')))
