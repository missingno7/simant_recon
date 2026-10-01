from pathlib import Path
import sys,struct,hashlib
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root/'tools'))
import exe,functions,modctx,modules,variants,autosearch
name='LessonDone';ctx=modctx.resolve(func=name);row=functions.get(name);claims=variants.check_set(ctx,[name],claims_only=True)
x=exe.load();lin=row['seg']*16+row['off'];base,unit=x.unit_bytes(row['unit']);orig=unit[lin-base:lin-base+row['size']]
print('target len',len(orig),'sha256',hashlib.sha256(orig).hexdigest())
for nm in ['base','case7_9_nested_short_circuit','case7_9_time_result_lifetime']:
 p=Path(__file__).with_name('round4-sources')/(nm+'.c');text=p.read_text(encoding='latin1');col={};res=modules.verify_module(text,ctx.module_dict(extent=True),claims,collect=col);cb=autosearch.candidate_bytes(col['object'],row,ctx.placements) if col.get('object') else b''
 print(nm,'len',len(cb),'sha256',hashlib.sha256(cb).hexdigest(),'claims',res.get('claims',{}).get(name,{}).get('reasons'))
 for tag,a,b in [('entry',0,0x1e),('table',0x1e,0x8e),('posttable',0x8e,min(len(orig),len(cb)))]:
  d=sum(1 for i in range(a,min(b,len(orig),len(cb))) if orig[i]!=cb[i]); print(' ',tag,'bytes_differ',d,'region_len',max(0,min(b,len(orig),len(cb))-a))
 if len(cb)>=0x8e:
  tw=struct.unpack_from('<56H',cb,0x1e);ow=struct.unpack_from('<56H',orig,0x1e);print(' table word mismatches',sum(a!=b for a,b in zip(tw,ow)))
