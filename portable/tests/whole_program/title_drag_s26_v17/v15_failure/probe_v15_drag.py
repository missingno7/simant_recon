import gdb,json,hashlib
OUT=r'D:\Prog\simant_recon\build\workers\whole_runtime_flow_review\v15_title_drag\events.jsonl';f=open(OUT,'w',encoding='utf8');inf=gdb.selected_inferior();rect_count=0;drag_count=0;resize_count=0;open_count=0
def emit(k,**v):f.write(json.dumps({'event':k,**v},sort_keys=True)+'\n');f.flush()
def val(e):return int(gdb.parse_and_eval(e))
def read(p,n):return bytes(inf.read_memory(p,n))
def rect(p):
 b=read(p,8);return {'bytes':b.hex(),'words':[int.from_bytes(b[i:i+2],'little',signed=True) for i in range(0,8,2)]}
class RectFinish(gdb.FinishBreakpoint):
 def __init__(self,obj,p,idx):super().__init__(gdb.newest_frame(),internal=True);self.obj=obj;self.p=p;self.idx=idx
 def stop(self):
  try:emit('get-obj-rect-return',idx=self.idx,obj=self.obj,rect_ptr=self.p,rect=rect(self.p))
  except Exception as e:emit('get-obj-rect-return-error',idx=self.idx,obj=self.obj,error=str(e))
  return False
class GetRect(gdb.Breakpoint):
 def __init__(self):super().__init__('win_GetObjRect',internal=True)
 def stop(self):
  global rect_count
  try:
   obj=val('$rcx')&0xffff;p=val('$rdx')
   if obj in (0x100,0x101,0x102,0x1900,0x1901,0x1902):
    rect_count+=1;emit('get-obj-rect-entry',idx=rect_count,obj=obj,rect_ptr=p);RectFinish(obj,p,rect_count)
  except Exception as e:emit('get-obj-rect-entry-error',error=str(e))
  return False
class Open(gdb.Breakpoint):
 def __init__(self):super().__init__('win_Open',internal=True)
 def stop(self):
  global open_count
  try:
   o=val('$rcx')&0xffff;open_count+=1;emit('win-open',index=open_count,win=o)
  except Exception as e:emit('win-open-error',error=str(e))
  return False
class Drag(gdb.Breakpoint):
 def __init__(self):super().__init__('o26_39C7_040F',internal=True)
 def stop(self):
  global drag_count
  drag_count+=1
  try:
   p=val('$rcx');b=read(p,16);ev=[int.from_bytes(b[i:i+2],'little',signed=True) for i in range(0,16,2)]
   emit('window-drag-entry',index=drag_count,event_ptr=p,event_words=ev,front=val('g_5702[0]'),mouse=[val('g_9122'),val('g_9124')])
  except Exception as e:emit('window-drag-entry-error',index=drag_count,error=str(e))
  return False
class Resize(gdb.Breakpoint):
 def __init__(self):super().__init__('o26_39C7_0671',internal=True)
 def stop(self):
  global resize_count
  resize_count+=1
  emit('window-resize-entry',index=resize_count)
  return False
GetRect();Open();Drag();Resize()
def done(e):emit('summary',rect_queries=rect_count,window_drag_entries=drag_count,window_resize_entries=resize_count,open_calls=open_count);f.close()
gdb.events.exited.connect(done)
emit('probe-start',exe=gdb.current_progspace().filename,input='quick-game-title-drag-v1.txt',method='read-only breakpoints; no state writes or inferior calls')
