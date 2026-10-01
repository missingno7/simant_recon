from pathlib import Path
import sys,difflib,struct,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,modctx,modules,exe
name='LessonDone';ctx=modctx.resolve(func=name);row=ctx.function(name)
text=Path(sys.argv[1]).read_text();col={};res=modules.verify_module(text,ctx.module_dict(extent=True),autosearch.Evaluator(ctx,name,1,ROOT/'build/workers/takeover/lesson-comparison-cache').claims,collect=col)
cb=autosearch.candidate_bytes(col['object'],row,ctx.placements);orig=exe.load().read(row['unit'],row['seg']*16+row['off'],row['size'])
print('Length',len(cb),len(orig),'exact',res.get('exact'))
a=list(autosearch.MD.disasm(cb[0x8e:],row['off']+0x8e));b=list(autosearch.MD.disasm(orig[0x8e:],row['off']+0x8e))
def norm(i):return i.mnemonic if autosearch.BRANCH_RE.match(i.mnemonic) else i.mnemonic+' '+i.op_str
sm=difflib.SequenceMatcher(a=[norm(i) for i in a],b=[norm(i) for i in b],autojunk=False)
for tag,i,j,k,l in sm.get_opcodes():
 if tag=='equal':continue
 print('CHUNK',tag)
 for x,y in zip(a[max(0,i-2):min(len(a),j+2)],b[max(0,k-2):min(len(b),l+2)]):print(f'{x.address:04X} {x.mnemonic} {x.op_str:<38} | {y.address:04X} {y.mnemonic} {y.op_str}')
 for x in a[i+max(0,l-k):j]:print('C',f'{x.address:04X}',x.mnemonic,x.op_str)
 for y in b[k+max(0,j-i):l]:print('O',f'{y.address:04X}',y.mnemonic,y.op_str)
ac=struct.unpack('<56H',cb[0x1e:0x8e]);bc=struct.unpack('<56H',orig[0x1e:0x8e]);print('Case addresses',[(i+1,hex(x),hex(y)) for i,(x,y) in enumerate(zip(ac,bc)) if x!=y])
