from pathlib import Path
import sys,hashlib
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root/'tools'))
import exe,functions,modctx,modules,variants,autosearch
ctx=modctx.resolve(func='LessonDone');row=functions.get('LessonDone');claims=variants.check_set(ctx,['LessonDone'],claims_only=True)
bs=[]
for nm in ['base','reordered_target_block_order','reordered_target_groups']:
 p=Path(__file__).with_name('round3-sources')/(nm+'.c'); col={};res=modules.verify_module(p.read_text(encoding='latin1'),ctx.module_dict(extent=True),claims,collect=col);b=autosearch.candidate_bytes(col['object'],row,ctx.placements);bs.append(b);print(nm,len(b),hashlib.sha256(b).hexdigest())
print('block_order_bytes_equal_base',bs[0]==bs[1])
print('grouped_bytes_equal_base',bs[0]==bs[2])
