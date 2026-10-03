import hashlib,json,collections,gdb
OUT=r'D:\Prog\simant_recon\build\workers\whole_runtime_flow_review\gdb-map-pixels.jsonl'; f=open(OUT,'w',encoding='utf8'); inf=gdb.selected_inferior(); n=0
def emit(e,**x): f.write(json.dumps({'event':e,**x},sort_keys=True)+'\n');f.flush()
def val(e): return int(gdb.parse_and_eval(e))
def digest(b): return hashlib.sha256(b).hexdigest()
class Ret(gdb.FinishBreakpoint):
 def __init__(self,a,idx): super().__init__(gdb.newest_frame(),internal=True);self.a=a;self.idx=idx
 def stop(self):
  try:
   p=val('(uintptr_t)app.graphics.pixel_storage'); stride=val('app.graphics.framebuffer.stride'); fbw=val('app.graphics.framebuffer.width'); fbh=val('app.graphics.framebuffer.height')
   x,y,w,h=(self.a[k] for k in ('x','y','w','h')); rows=[]; colors=collections.Counter()
   for yy in range(y,max(y,min(y+h,fbh))):
    xx0=max(0,x);xx1=min(fbw,x+w)
    b=bytes(inf.read_memory(p+yy*stride+xx0, max(0,xx1-xx0))); rows.append(b);colors.update(b)
   flat=b''.join(rows)
   emit('map-pixel-row',index=self.idx,args=self.a,pixel_store=p,frame=[fbw,fbh,stride],sample={'length':len(flat),'sha256':digest(flat),'nonzero':sum(bool(v) for v in flat),'colors':dict(colors),'head':flat[:64].hex()})
  except Exception as e: emit('map-pixel-error',index=self.idx,error=str(e))
  return False
class BP(gdb.Breakpoint):
 def __init__(self): super().__init__('source_g9150_callback',internal=True)
 def stop(self):
  global n
  fr=gdb.newest_frame();q=fr;chain=[]
  while q and len(chain)<12:chain.append(q.name());q=q.older()
  if not any('o12_384C_0B76' in (z or '') for z in chain): return False
  n+=1
  if n<=12:
   try:
    a={'x':val('$rcx & 0xffff'),'y':val('$rdx & 0xffff'),'bits':val('$r8'),'w':val('$r9 & 0xffff'),'h':val('*(unsigned short*)($rsp+0x28)')}
    p=a['bits'];size=4*((a['w']+7)//8)*a['h'];data=bytes(inf.read_memory(p,size))
    emit('map-blit-entry',index=n,chain=chain,args=a,planar={'n':len(data),'sha256':digest(data),'nonzero':sum(bool(v) for v in data),'head':data[:48].hex()})
    Ret(a,n)
   except Exception as e:emit('map-blit-entry-error',index=n,chain=chain,error=str(e))
  return False
BP()
def done(e): emit('summary',map_blits=n);f.close()
gdb.events.exited.connect(done);emit('probe-start',exe=gdb.current_progspace().filename,method='map row callback register+fifth-stack args; indexed framebuffer sampled after g9150 return')
