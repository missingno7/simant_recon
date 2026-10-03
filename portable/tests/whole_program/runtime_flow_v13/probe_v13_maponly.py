import hashlib,json,gdb
OUT=r'D:\Prog\simant_recon\build\workers\whole_runtime_flow_review\gdb-raster-maponly.jsonl';f=open(OUT,'w',encoding='utf8');inf=gdb.selected_inferior();counts={'map_cb':0,'all_cb':0,'row':0}
def emit(e,**x): f.write(json.dumps({'event':e,**x},sort_keys=True)+'\n');f.flush()
def val(x): return int(gdb.parse_and_eval(x))
def raw(p,n): return bytes(inf.read_memory(p,n))
def snap(p,n):
 b=raw(p,n);return {'ptr':p,'n':n,'sha256':hashlib.sha256(b).hexdigest(),'nonzero':sum(bool(x) for x in b),'distinct':len(set(b)),'head':b[:48].hex()}
class CB(gdb.Breakpoint):
 def __init__(self): super().__init__('source_g914C_callback',internal=True)
 def stop(self):
  counts['all_cb']+=1
  fr=gdb.newest_frame(); chain=[]; q=fr
  while q and len(chain)<8:
   chain.append(q.name()); q=q.older()
  if any('o12_384C_0B76' in (n or '') for n in chain):
   counts['map_cb']+=1
   if counts['map_cb']<=20:
    try:
     x,y,w,h=(val(z) for z in ('x','y','width','height'));p=val('(uintptr_t)bitmap');clip=val('(uintptr_t)g_5AAC'); length=4*((w+7)//8)*h
     emit('map-callback',index=counts['map_cb'],chain=chain,x=x,y=y,width=w,height=h,clip=clip,clip_head=raw(clip,16).hex() if clip else None,data=snap(p,length),scale=(val('fd_50F6_3856'),val('fd_50F6_3858')),rowbytes=val('fd_50F6_3854'),panel=val('fd_50F6_38C0'))
    except Exception as e: emit('map-callback-error',index=counts['map_cb'],chain=chain,error=str(e))
  return False
class Row(gdb.Breakpoint):
 def __init__(self): super().__init__('o12_384C_03D0',internal=True)
 def stop(self):
  counts['row']+=1
  if counts['row']<=3:
   try: emit('row',num=counts['row'],n=val('n'),source=snap(val('(uintptr_t)src'),64),dest=snap(val('(uintptr_t)dst'),512),g_5A97=val('g_5A97'),mode=val('fd_3D57_07C8'))
   except Exception as e: emit('row-error',error=str(e))
  return False
CB();Row()
def done(e): emit('summary',**counts);f.close()
gdb.events.exited.connect(done);emit('start',exe=gdb.current_progspace().filename)
