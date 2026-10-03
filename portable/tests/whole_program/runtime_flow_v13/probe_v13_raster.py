import hashlib, json, gdb
OUT = r'D:\Prog\simant_recon\build\workers\whole_runtime_flow_review\gdb-raster-events.jsonl'
f = open(OUT, 'w', encoding='utf-8')
inf = gdb.selected_inferior()
counts = {'row':0,'bitmap':0,'paint':0,'sim':0,'clip':0}
def emit(k, **v): f.write(json.dumps({'event':k,**v},sort_keys=True)+'\n'); f.flush()
def val(x): return int(gdb.parse_and_eval(x))
def read(addr,n): return bytes(inf.read_memory(addr,n))
def info(addr,n):
 d=read(addr,n); return {'address':addr,'length':n,'sha256':hashlib.sha256(d).hexdigest(),'nonzero':sum(bool(x) for x in d),'distinct':len(set(d)),'head':d[:32].hex()}
class RowFinish(gdb.FinishBreakpoint):
 def __init__(self, args, num): super().__init__(gdb.newest_frame(),internal=True); self.args=args; self.num=num
 def stop(self):
  try: emit('row-return',call=self.num,src=self.args['src'],dst=info(self.args['dst'],0x200),n=self.args['n'],stride=self.args['stride'])
  except Exception as e: emit('row-return-error',call=self.num,error=str(e))
  return False
class Row(gdb.Breakpoint):
 def __init__(self): super().__init__('o12_384C_03D0',internal=True)
 def stop(self):
  counts['row']+=1
  try:
   a={'src':val('(uintptr_t)src'),'dst':val('(uintptr_t)dst'),'n':val('n'),'stride':val('fd_50F6_3854')}
   if counts['row']<=8: emit('row-entry',call=counts['row'],src=info(a['src'],64),dst=info(a['dst'],0x200),n=a['n'],stride=a['stride'],g_5A97=val('g_5A97'),mode=val('fd_3D57_07C8'))
   RowFinish(a,counts['row'])
  except Exception as e: emit('row-entry-error',call=counts['row'],error=str(e))
  return False
class Bitmap(gdb.Breakpoint):
 def __init__(self): super().__init__('source_g914C_callback',internal=True)
 def stop(self):
  counts['bitmap']+=1
  if counts['bitmap']<=12:
   try:
    x,y,w,h=val('x'),val('y'),val('width'),val('height'); p=val('(uintptr_t)bitmap'); n=4*((w+7)//8)*h
    clip=val('(uintptr_t)g_5AAC')
    emit('bitmap-entry',call=counts['bitmap'],x=x,y=y,width=w,height=h,clip=clip,clip_active=bool(clip),data=info(p,n),clip_head=(read(clip,16).hex() if clip else None))
   except Exception as e: emit('bitmap-entry-error',call=counts['bitmap'],error=str(e))
  return False
class Raster(gdb.Breakpoint):
 def __init__(self): super().__init__('o12_384C_0B76',internal=True)
 def stop(self):
  counts['paint']+=1
  if counts['paint']<=10:
   try: emit('raster-entry',call=counts['paint'],mode=val('fd_3D57_07C8'),mapplane=val('native_state_MapPlane.signed_value'),g5a97=val('g_5A97'),rowbytes=val('fd_50F6_3854'),scalex=val('fd_50F6_3856'),scaley=val('fd_50F6_3858'),panel=val('fd_50F6_38C0'))
   except Exception as e: emit('raster-error',error=str(e))
  return False
Row(); Bitmap(); Raster()
def exit_cb(e):
 emit('summary',**counts); f.close()
gdb.events.exited.connect(exit_cb)
emit('probe-start',exe=gdb.current_progspace().filename,method='read-only breakpoints; callback and row buffer snapshots')
