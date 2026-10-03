import hashlib,json,collections,gdb
OUT=r'D:\Prog\simant_recon\build\workers\whole_runtime_flow_review\gdb-present-pixels.jsonl';f=open(OUT,'w',encoding='utf8');inf=gdb.selected_inferior();count=0
def emit(e,**x):f.write(json.dumps({'event':e,**x},sort_keys=True)+'\n');f.flush()
def val(x):return int(gdb.parse_and_eval(x))
def sample(p,stride,box):
 x0,y0,x1,y1=box;c=collections.Counter(); digest=hashlib.sha256();
 for y in range(y0,y1):
  b=bytes(inf.read_memory(p+y*stride+x0,x1-x0));c.update(b);digest.update(b)
 return {'box':box,'sha256':digest.hexdigest(),'colors':dict(c),'n':sum(c.values())}
class BP(gdb.Breakpoint):
 def __init__(self):super().__init__('host_present',internal=True)
 def stop(self):
  global count
  count+=1
  if count<=10 or count%100==0:
   try:
    p=val('$rdx');stride=val('$r8');
    emit('present',frame=count,pixels=p,stride=stride,
      map_window=sample(p,stride,(418,96,578,342)),
      transformed_rows=sample(p,stride,(192,82,448,338)))
   except Exception as e:emit('present-error',frame=count,error=str(e))
  return False
BP()
def done(e): emit('summary',present_calls=count);f.close()
gdb.events.exited.connect(done);emit('probe-start',exe=gdb.current_progspace().filename,method='read-only host_present pixel-index samples')
