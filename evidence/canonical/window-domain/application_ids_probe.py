"""Original application ID expressions with explicit UI/drawing services."""
from pathlib import Path
from types import SimpleNamespace
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'src/program.json').is_file())
sys.path.insert(0,str(ROOT/'tools'))
import behavior as b,exe,functions

def machine(name):
 image=exe.load()
 return b.Machine(SimpleNamespace(function=functions.get(name),
  vectors={exe.MANAGER_SEG*16+v.offset:v for v in image.vectors},identity={'oracle_sha256':image.sha256}))

def expansion_case(history, cleared_proxy=False):
 m=machine('DoExpMenu'); no=lambda m,a:0
 def prox(m,a):m.state.setdefault('proxy_ids',[]).append(a[0])
 def event(m,a):
  n=m.state.get('events',0)+1;m.state['events']=n
  code=0xff00 if cleared_proxy and n==3 else 0xfb09
  m.write(a[1]*16+a[0],b.words(0,0,0,0,0,0,code,0));return 1
 def rect(m,a):m.write(a[2]*16+a[1],b.words(10,10,100,20))
 def size(m,a):m.write(a[2]*16+a[1],b.words(20,20))
 callbacks={'win_Open':b.Callback(3,no),
  '_win_SetProxItem':b.Callback(0,prox,('ax',)),'ButtonHeldInit':b.Callback(0,no),
  'win_IsWinOpen':b.Callback(0,lambda m,a:1,('ax',)),
  'win_IsWinInFront':b.Callback(0,lambda m,a:1,('ax',)),
  'f_1F58_0038':b.Callback(0,no),'win_GetEvent':b.Callback(2,event,pop=4),
  'WinPrintf':b.Callback(2,no),'win_GetProxEvent':b.Callback(0,lambda m,a:0xffff if cleared_proxy and m.state['events']==2 else 0x903),
  'win_GetObjRect':b.Callback(2,rect,('ax',),pop=4),
  'win_GetObjSize':b.Callback(2,size,('ax',),pop=4),'ButtonHeld':b.Callback(0,lambda m,a:1 if cleared_proxy and m.state.get('events')==1 else 0),
  'ButtonHeldEnd':b.Callback(0,no),'win_Close':b.Callback(0,no,('ax',))}
 out=m.run(b.Case(label='original-expansion-history-byte-'+str(history),args=[40,40],
  callbacks=callbacks,writes=[(b.symbol_address('CurExpTool'),b.words(1)),
  (b.symbol_address('ExpSubStates')+1,bytes([history])),
  (b.symbol_address('g_5702'),b.words(0x900,0x8000)),
  (b.symbol_address('g_3DB2'),b.words(320))],return_kind='s16'))
 return {'history_byte':history,'proxy_ids':m.state['proxy_ids'],'result':out['return'],'blocks':m.blocks}

def scent_state_case(result):
 m=machine('EditScentMenu');no=lambda m,a:0
 callbacks={'win_DoProxMenu':b.Callback(2,lambda m,a:result),
  'clip_SetWin':b.Callback(1,no),'win_SetObjSelectedState':b.Callback(0,no,('ax','dx')),
  'f_0250_0E81':b.Callback(0,no)}
 m.run(b.Case(label='original-scent-state-return-'+str(result),callbacks=callbacks,
  writes=[(b.symbol_address('fd_3D57_07BE'),b.words(0))],return_kind='void'))
 state=int.from_bytes(m.read(b.symbol_address('fd_3D57_07BE'),2),'little',signed=True)
 return {'menu_result':result,'scent_state':state,'blocks':m.blocks}

def proxy_case(item,event_ids):
 m=machine('win_DoProxMenu');no=lambda m,a:0
 def prox(m,a):m.state['proxy_id']=a[0]
 def next_event(m,a):
  n=m.state.get('event_reads',0);m.state['event_reads']=n+1;return event_ids[n]
 callbacks={'win_Open':b.Callback(3,no),'_win_SetProxItem':b.Callback(0,prox,('ax',)),
  'ButtonHeldInit':b.Callback(0,no),'ButtonHeld':b.Callback(0,no),
  'win_IsWinOpen':b.Callback(0,lambda m,a:1,('ax',)),
  'win_GetProxEvent':b.Callback(0,next_event),'win_Close':b.Callback(0,no,('ax',))}
 out=m.run(b.Case(label='original-scent-proxy-item-'+str(item),args=[0x600,item,0,0],
  callbacks=callbacks,return_kind='s16'))
 return {'item':item,'proxy_id':m.state.get('proxy_id'),'result':out['return'],
  'event_reads':m.state['event_reads'],'blocks':m.blocks}

def controls():
 expansion=[expansion_case(n) for n in range(256)]
 ids=[x['proxy_ids'][1] for x in expansion if len(x['proxy_ids'])==2]
 assert all(x['proxy_ids'][0]==0x903 and x['result']==1 for x in expansion)
 assert expansion[0]['proxy_ids']==[0x903,0xc02]
 assert expansion[128]['proxy_ids']==[0x903,0xb82]
 assert expansion[255]['proxy_ids']==[0x903]
 assert min(ids)==0xb82 and max(ids)==0xc81
 cleared=expansion_case(0,True)
 assert cleared['result']==253
 scent=[proxy_case(0,[0x602]),proxy_case(253,[0x6ff]),proxy_case(0,[0x700,0x602])]
 assert [x['proxy_id'] for x in scent]==[0x602,0x6ff,0x602]
 assert [x['result'] for x in scent]==[0,253,0]
 states=[scent_state_case(n) for n in (-1,0,253)]
 assert [x['scent_state'] for x in states]==[0,-1,252]
 return {'expansion':{'all_history_bytes':256,'minimum_proxy_id':min(ids),'maximum_proxy_id':max(ids),
  'output_sha256':hashlib.sha256(json.dumps(expansion,separators=(',',':')).encode()).hexdigest(),
  'positive':expansion[0],'signed_byte_contrast':expansion[128],'minus_one_skip':expansion[255]},
  'cleared_proxy_contrast':cleared,'scent':scent,'scent_state_transitions':states,
  'scope':'Unchanged DoExpMenu, EditScentMenu and win_DoProxMenu instruction bodies; UI/event/drawing/lock consumers are explicit boundary models, no full-game ID provenance admission.'}

if __name__=='__main__':print(json.dumps(controls(),indent=2))
