import json,gdb
OUT=r'D:\Prog\simant_recon\build\workers\whole_runtime_flow_review\gdb-window-rects.jsonl';f=open(OUT,'w',encoding='utf8');inf=gdb.selected_inferior();hits=0
def emit(e,**x):f.write(json.dumps({'event':e,**x},sort_keys=True)+'\n');f.flush()
def val(e):return int(gdb.parse_and_eval(e))
class Finish(gdb.FinishBreakpoint):
 def __init__(self,obj,ptr):super().__init__(gdb.newest_frame(),internal=True);self.obj=obj;self.ptr=ptr
 def stop(self):
  try:
   b=bytes(inf.read_memory(self.ptr,8)); w=[int.from_bytes(b[i:i+2],'little',signed=True) for i in range(0,8,2)]
   emit('get-obj-rect-return',obj=self.obj,rect_ptr=self.ptr,rect=w,bytes=b.hex())
  except Exception as e:emit('get-obj-rect-error',obj=self.obj,error=str(e))
  return False
class GetRect(gdb.Breakpoint):
 def __init__(self):super().__init__('win_GetObjRect',internal=True)
 def stop(self):
  global hits
  try:
   obj=val('$rcx')&0xffff;ptr=val('$rdx')
   if obj in (0x100,0x101,0x102,0x1900,0x1902):
    hits+=1;emit('get-obj-rect-entry',hit=hits,obj=obj,ptr=ptr)
    Finish(obj,ptr)
  except Exception as e:emit('get-obj-rect-entry-error',error=str(e))
  return False
class Open(gdb.Breakpoint):
 def __init__(self):super().__init__('win_Open',internal=True)
 def stop(self):
  try:
   obj=val('$rcx')&0xffff
   if obj in (0x100,0x101,0x102,0x1900,0x1901,0x1902):emit('open-window',obj=obj)
  except Exception as e:emit('open-window-error',error=str(e))
  return False
GetRect();Open()
def done(e):emit('summary',rect_hits=hits);f.close()
gdb.events.exited.connect(done);emit('probe-start',exe=gdb.current_progspace().filename)
