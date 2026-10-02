"""Quit dialog ordered command/input contract, with original Ralloc helpers."""
import argparse
import hashlib
import json
import random
import re
import struct
import sys
import time
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from behavior_suites import lists
import behavior as b
from behavior_ledger import CaseLedger

_MEMORY_FIXTURE = ROOT/'tools/behavior_suites/archive/window-memory-fixture-dda4f6dd.py'
_memory_spec = importlib.util.spec_from_file_location('dialog_memory_fixture', _MEMORY_FIXTURE)
memory_fixture = importlib.util.module_from_spec(_memory_spec)
sys.modules[_memory_spec.name] = memory_fixture
_memory_spec.loader.exec_module(memory_fixture)

FUNCTION='o15_384C_0239'
SUITE_SOURCE=Path(__file__).read_bytes()
EFFECTS=['return','ordered GUI/window/font/resource/input commands','rectangle/text/font contents',
         'resource lock/unlock/release and age','input arbitration and consumption',
         'logical window state','all nonstack writes','caller ABI']
SOURCE_DEFINITIONS={
    'win_Open':('src/root/m20E8.c','win_Open'),
    'win_Close':('src/root/m20E8.c','win_Close'),
    'f_1A53_00F0':('src/root/m1A53.c','f_1A53_00F0'),
    'f_171C_1B84':('src/root/m171C.c','f_171C_1B84'),
    'f_171C_1BBA':('src/root/m171C.c','f_171C_1BBA'),
    'f_24AB_02AD':('src/root/m24AB.c','f_24AB_02AD'),
    'win_GetObjRect':('src/root/m2505.c','win_GetObjRect'),
    'win_DrawWindow':('src/root/m21FA.c','win_DrawWindow'),
    'f_2505_03B9':('src/root/m2505.c','f_2505_03B9'),
    'f_2505_04D7':('src/root/m2505.c','f_2505_04D7'),
    'f_2505_0831':('src/root/m2505.c','f_2505_0831'),
    'f_2505_08EA':('src/root/m2505.c','f_2505_08EA'),
    'win_LockInit':('src/root/m23AE.c','win_LockInit'),
    'db_ReleaseHandle':('src/root/m1A53.c','db_ReleaseHandle'),
    'f_171C_15A2':('src/root/m171C.c','f_171C_15A2'),
    'win_SetColorFromObjNum':('src/root/m21FA.c','win_SetColorFromObjNum'),
    'f_21FA_0B4B':('src/root/m21FA.c','f_21FA_0B4B'),
    'f_1CE2_044D':('src/root/m1CE2.c','f_1CE2_044D'),
    'win_GetEvent':('src/root/m218D.c','win_GetEvent'),
    'win_FlushEvents':('src/root/m218D.c','win_FlushEvents'),
    'f_218D_01EB':('src/root/m218D.c','f_218D_01EB'),
    'clip_KillWin':('src/root/m1E57.c','clip_KillWin'),
    'clip_SetWin':('src/root/m1E57.c','clip_SetWin'),
    'clip_Off':('src/root/m1E57.c','clip_Off'),
    'f_1E57_038E':('src/root/m1E57.c','f_1E57_038E'),
    'win_PrintTextInRect':('src/root/m259D.c','win_PrintTextInRect'),
}


def source_definition_pins():
    pins={}
    for name,(relative,path_name) in SOURCE_DEFINITIONS.items():
        source=(ROOT/relative).read_text(encoding='latin1')
        match=re.search(r'\b'+re.escape(path_name)+r'\s*\([^;]*?\)\s*\{',source,re.S)
        if not match: raise RuntimeError(f'cannot locate source definition {path_name}')
        end=match.end();depth=1
        while end<len(source) and depth:
            if source[end]=='{':depth+=1
            elif source[end]=='}':depth-=1
            end+=1
        if depth: raise RuntimeError(f'unclosed source definition {path_name}')
        body=source[match.start():end].encode('latin1')
        pins[name]={'path':relative,'line':source.count('\n',0,match.start())+1,
                    'sha256':b.digest(body),'bytes':len(body)}
    return pins


def linear(args,index=0): return args[index+1]*16+args[index]


def clobber(m):
    for name in ('ax','bx','cx','dx','es'):
        m.set_reg(name,m.state['volatile'])


def command(m,args):
    clobber(m)
    return None


def win_open(m,args):
    m.state['open_windows'].append(args[0])
    clobber(m)


def win_close(m,args):
    win=args[0]
    if win in m.state['open_windows']:
        m.state['open_windows'].remove(win)
    m.state['closed_windows'].append(win)
    clobber(m)


def resource(m,args):
    clobber(m)
    data_off,data_seg=struct.unpack('<HH',m.read(linear((lists.HANDLE[0],lists.HANDLE[1])),4))
    header_at=(data_seg-2)*16
    paras=struct.unpack('<H',m.read(header_at+6,2))[0]
    dg=b.match.DGROUP_SEG*16
    hard=struct.unpack('<H',m.read(dg+0x2f36,2))[0]
    firm=struct.unpack('<H',m.read(dg+0x2f3a,2))[0]
    # Model f_1A53_00F0's source-level type-0 -> type-1 transition.
    m.write(dg+0x2f36,b.words(hard-paras))
    m.write(dg+0x2f3a,b.words(firm+paras))
    m.write(header_at+8,b'\x01')
    m.state['resource_requests'].append({'object':args[0],'kind':args[1],
                                         'type':args[2],'handle':list(lists.HANDLE)})
    m.state['resource_state']='acquired-firm'
    return lists.HANDLE


def rect_result(m,args):
    # AX object number, followed by far destination rectangle on stack.
    rect=m.state['rects'].get(args[0],m.state['rects']['default'])
    m.write(linear(args,1),b.words(*rect))
    clobber(m)


def rect_input(m,args):
    return {'rect':list(struct.unpack('<4h',m.read(linear(args),8))), 'width':args[2]}


def text_input(m,args):
    # Fastcall AX first, rect last C argument is first on the stack.
    at=linear(args,3); text=bytearray()
    for i in range(4096):
        v=m.read(at+i,1)[0]
        if not v: break
        text.append(v)
    else: raise AssertionError('unterminated dialog resource')
    font=b.symbol('fd_55B3_65A4')
    font_pointer=list(struct.unpack('<HH',m.read(font['seg']*16+font['off'],4)))
    return {'first':args[0],'rect':list(struct.unpack('<4h',m.read(linear(args,1),8))),
            'font_pointer':font_pointer,'text':bytes(text).hex()}


def key_ready(m,args):
    ready=bool(m.state['keys'])
    clobber(m)
    return int(ready)


def key_read(m,args):
    key=m.state['keys'].pop(0)
    clobber(m)
    return key


def event(m,args):
    item=m.state['events'].pop(0) if m.state['events'] else None
    if item is not None:
        # The caller reads Event.code at offset 12 only on a successful result.
        m.write(linear(args),b.words(1,0,0,0,0,0,item,0))
    clobber(m)
    return int(item is not None)


def _real_2100_window():
    """Decode the locked uncompressed HCEGANT window 0x21, kind 0 record."""
    idx=Path(ROOT/'assets/HCEGANT.NDX').read_bytes()
    dat=Path(ROOT/'assets/HCEGANT.DAT').read_bytes()
    count=struct.unpack_from('<H',idx,0)[0]
    entry_at=len(idx)-count*8
    found=[]
    for i in range(count):
        offset,object_id,kind,flags=struct.unpack_from('<IHBB',idx,entry_at+i*8)
        if object_id==0x21 and kind==0:
            found.append((offset,flags))
    if len(found)!=1 or found[0][1]!=8:
        raise RuntimeError('expected one uncompressed HCEGANT 0x21,kind0 record')
    offset,_=found[0]
    header=struct.unpack_from('<HHHHH',dat,offset+14)
    size=header[3]
    payload=dat[offset+24:offset+24+size]
    if len(payload)!=size or struct.unpack_from('<H',payload,0x0c)[0]!=6:
        raise RuntimeError('unexpected HCEGANT window record shape')
    ptrs=[struct.unpack_from('<H',payload,0x2c+i*4)[0] for i in range(6)]
    modes=[list(struct.unpack_from('<4H',payload,p+24)) for p in ptrs]
    if modes!=[[0,0,1,2]]+[[1,2,1,2] for _ in range(5)]:
        raise RuntimeError(f'unexpected 0x2100 geometry modes: {modes!r}')
    return payload,{'index_count':count,'entry_offset':offset,'flags':8,
        'record_header':list(header),'payload_size':size,'object_count':6,
        'object_offsets':ptrs,'modes':modes,
        'ndx_sha256':b.digest(idx),'dat_sha256':b.digest(dat)}


def _capture_window_draw(m,args):
    win=args[0]
    handles=b.symbol('win_handles'); at=handles['seg']*16+handles['off']+(win>>8)*4
    handle_off,handle_seg=struct.unpack('<HH',m.read(at,4))
    data_off,data_seg=struct.unpack('<HH',m.read(handle_seg*16+handle_off,4))
    w_at=data_seg*16+data_off
    count=struct.unpack('<H',m.read(w_at+0x0c,2))[0]
    rows=[]
    for i in range(count):
        obj_off,obj_seg=struct.unpack('<HH',m.read(w_at+0x2c+i*4,4))
        rows.append(list(struct.unpack('<4h',m.read(obj_seg*16+obj_off,8))))
    m.state.setdefault('drawn_windows',[]).append({'win':win,
        'rect':list(struct.unpack('<4h',m.read(w_at,8))),
        'flags':struct.unpack('<H',m.read(w_at+0x1c,2))[0],'objects':rows})


def _flush_stale(m,args):
    m.state['stale_events'].clear()
    m.state['flush_count']+=1


def _rect_invalidated(m,args):
    m.state.setdefault('invalidated_rects',[]).append(
        list(struct.unpack('<4h',m.read(linear(args),8))))


def _actual_window_state(fixture,text,previous_window=0x0200):
    payload,proof=_real_2100_window()
    text_paras=(len(text)+47)//16
    win_paras=(len(payload)+47)//16
    free_paras=0x100-text_paras-win_paras
    if free_paras<16: raise RuntimeError('dialog/window fixture heap has no valid free tail')
    old=(memory_fixture.HEAP_SEG,memory_fixture.HEAP_PARAS)
    memory_fixture.HEAP_SEG=lists.DATA[1]-2
    memory_fixture.HEAP_PARAS=0x100
    try:
        arena=memory_fixture.heap_case(fixture.label+'/real-2100-window',[
            (text_paras,0,{'size':len(text),'name':b'dialog-text'}),
            (win_paras,1,{'size':len(payload),'name':b'window-2100'}),
            (free_paras,0x80,{'name':b'dialog-window-tail'})],handles=[0,1],
            contract='text handle plus actual uncompressed HCEGANT window 0x21 kind0 and linked free tail')
    finally:
        memory_fixture.HEAP_SEG,memory_fixture.HEAP_PARAS=old
    # The first block's data starts at A100. The second paragraph header starts
    # after the first block, so its payload segment is A100 + text_paras.
    window_data_seg=lists.DATA[1]+text_paras
    window_slot=lists.HANDLE[0]-4
    fixture.writes += arena.writes
    noop=b.symbol('f_20E8_0000')
    noop_pointer=b.words(noop['off'],noop['seg'])
    fixture.writes += [(window_data_seg*16,payload),
        (b.symbol_address('win_handles')+0x21*4,b.words(window_slot,lists.HANDLE[1])),
        (b.symbol_address('win_numOfWindows'),b.words(45)),
        (b.symbol_address('g_6300'),b.words(0)),
        (b.symbol_address('g_5702'),b.words(*([0x8000]*32))),
        (b.symbol_address('g_62E0'),noop_pointer*6)]
    fixture.observe=[r for r in fixture.observe if r.name!='dialog_resource_heap']
    fixture.observe += [r for r in arena.observe if r.name not in ('heap','handle_table')]
    fixture.observe += [b.Range('actual_2100_payload',window_data_seg*16,len(payload)),
        b.Range('dialog_resource_heap',(lists.DATA[1]-2)*16,
                (text_paras+win_paras+free_paras)*16),
        b.Range('actual_window_stack',b.symbol_address('g_5702'),64),
        b.Range('actual_window_handles',b.symbol_address('win_handles'),45*4)]
    fixture.writes.append((b.symbol_address('g_5702'),
                           b.words(previous_window,0x8000,*([0x8000]*30))))
    fixture.state.update({'stale_events':[0x2100,0x2102], 'flush_count':0,
                          'drawn_windows':[],'invalidated_rects':[]})
    fixture.callbacks.update({
        'win_Open':b.Callback(1),
        'win_Close':b.Callback(0,None,('ax',)),
        'win_GetObjRect':b.Callback(2,None,('ax',),pop=4),
        'win_DrawWindow':b.Callback(0,_capture_window_draw,('ax',)),
        # These helpers are the renderer/cursor presentation boundary. The
        # actual Open/Close and z-order code still execute around them.
        'f_2505_0831':b.Callback(0,lambda m,a:None,('ax',)),
        'f_2505_08EA':b.Callback(0,lambda m,a:None,('ax',)),
        'clip_SetWin':b.Callback(1,lambda m,a:None),
        'clip_Off':b.Callback(0,lambda m,a:None),
        'win_FlushEvents':b.Callback(0,_flush_stale),
        'clip_KillWin':b.Callback(1),
        'f_21FA_0B4B':b.Callback(2,_rect_invalidated,pop=4),
        'f_218D_01EB':b.Callback(0,lambda m,a:None),
        'f_1E57_038E':b.Callback(0,lambda m,a:None),
    })
    fixture.metadata['actual_window_resource']=proof
    fixture.metadata['window_data_seg']=window_data_seg
    fixture.metadata['window_handle_slot']=window_slot
    fixture.metadata['window_paras']=win_paras
    fixture.metadata['free_paras']=free_paras
    return fixture


def actual_window_case(label='actual-window/smoke'):
    return case(label,1,640,0,[115],[],[0,0,10,10],0x1234,text=b'Dialog text',
                actual_window=True,previous_window=0x0200)


def case(label,which,width,mono,keys,events,rect,volatile,text=b'Dialog text',rects=None,
         actual_window=True,previous_window=0x0200):
    fixture=lists.make_case(label,[text],0,1,0)
    dg=b.match.DGROUP_SEG*16
    paras=(len(text)+47)//16
    old_heap_seg=memory_fixture.HEAP_SEG
    memory_fixture.HEAP_SEG=lists.DATA[1]-2
    try:
        arena=memory_fixture.heap_case(label+'/ralloc',
            [(paras,0,{'size':len(text),'name':b'dialog-text'}),
             (16,0x80,{'name':b'dialog-tail'})], handles=[0],
            contract='valid type-0 resource handle and linked free tail; consistent Ralloc counters')
    finally:
        memory_fixture.HEAP_SEG=old_heap_seg
    empty=b.symbol('f_1B4E_000C'); zero=b.symbol('f_171C_001E')
    fixture.args=[which&65535]; fixture.registers={};fixture.callee_pop=0;fixture.return_kind='s16'
    fixture.state={'keys':list(keys),'events':list(events),
        'rects':dict(rects or {'default':rect,0x2100:rect,0x2101:rect}),
        'volatile':volatile,'open_windows':[],'closed_windows':[],'resource_requests':[],
        'resource_state':'unloaded'}
    fixture.writes += [(dg+0x3DB2,b.words(width)),(dg+0x5A97,bytes([mono])),
                       (dg+0x9128,b.words(empty['off'],empty['seg'])),
                       (dg+0x912C,b.words(zero['off'],zero['seg'])),
                       (dg+0x9130,b.words(zero['off'],zero['seg']))]
    font_table=b.symbol('fd_50F6_4A1A')
    font_at=font_table['seg']*16+font_table['off']
    # Stable opaque far-pointer tokens for fonts 2 and 4.  The dialog only
    # selects/passes these handles; the host print command does not dereference.
    fixture.writes += [(font_at,b.words(0x1234,0x2211)),
                       (font_at+8,b.words(0x5678,0x3344))]
    fixture.writes += arena.writes
    fixture.observe += [r for r in arena.observe if r.name not in ('heap','handle_table')]
    fixture.observe += [b.Range('dialog_resource_heap',(lists.DATA[1]-2)*16,(paras+16)*16),
                        b.Range('dialog_resource_handle',lists.HANDLE[1]*16+lists.HANDLE[0],4),
                        b.Range('dialog_manager_state',dg+0x2f2a,0x28)]
    fixture.callbacks={
        'win_Open':b.Callback(1,win_open),
        'f_1A53_00F0':b.Callback(3,resource),
        'f_171C_1B84':b.Callback(2),
        'f_171C_1BBA':b.Callback(2),
        'db_ReleaseHandle':b.Callback(2),
        'f_24AB_02AD':b.Callback(1),
        'win_GetObjRect':b.Callback(2,rect_result,('ax',),pop=4,
                                      project=lambda m,a:{'object':a[0],
                                        'rect':m.state['rects'].get(a[0],m.state['rects']['default'])}),
        'f_1B4E_000C':b.Callback(3),
        'f_1CE2_044D':b.Callback(3,command,project=rect_input),
        'win_SetColorFromObjNum':b.Callback(0,command,('ax',)),
        'win_PrintTextInRect':b.Callback(4,command,('ax',),pop=8,project=text_input),
        'f_1F58_0038':b.Callback(0,key_ready),
        'f_1F58_0090':b.Callback(0,key_read),
        'win_GetEvent':b.Callback(2,event,pop=4,project=lambda m,a:{'destination':'event'}),
        'win_Close':b.Callback(0,win_close,('ax',))}
    # The list structure is fixture support, not the dialog's output contract.
    fixture.observe=[r for r in fixture.observe if r.name!='list']
    fixture.metadata={'which':which,'width':width,'mono':mono,'keys':keys,'events':events,
                      'rect':rect,'rects':rects,'volatile':volatile,'resource':text.hex(),
                      'resource_paras':paras}
    if actual_window:
        fixture.metadata['previous_window']=previous_window
        return _actual_window_state(fixture,text,previous_window)
    return fixture


def cases(count,seed):
    endings=[([k],[]) for k in (13,27,67,68,83,99,100,115)]
    endings += [([], [e]) for e in (0x2103,0x2104,0x2105)]
    for which in (0,1):
        for width in (320,640):
            for mono in (0,1,2,3):
                for keys,events in endings:
                    label=f'{which}/{width}/{mono}/{keys}/{events}'
                    yield 'directed',case(label,which,width,mono,keys,events,[-10,2,100,200],0xABCD)
    # Both real caller modes: keyboard wins when a key and dialog event are
    # simultaneously available; ignored keys leave the event queue to decide.
    for which in (0,1):
        for key in (13,27,67,68,83,99,100,115):
            for code in (0x2103,0x2104,0x2105):
                yield 'directed',case(f'arbitrate/key-{key}/event-{code:04x}/which-{which}',
                    which,320,1,[key],[code],[0,0,10,10],0xABCD,
                    rects={'default':[0,0,1,1],0x2100:[1,2,30,40],0x2101:[50,60,70,80]})
        for code in (0x2100,0x2102,0x2110,0x2105):
            yield 'directed',case(f'event-queue/ignore-{code:04x}/which-{which}',which,640,0,[],
                [code,0x2104],[0,0,10,10],0xBEEF,
                rects={'default':[0,0,1,1],0x2100:[2,3,32,43],0x2101:[52,63,72,83]})
        for key in (0x03,0x41,0xff):
            yield 'directed',case(f'ignored-key-{key:02x}-then-event/which-{which}',
                which,320,0,[key],[0x2104],[0,0,10,10],0x9876)
    # win_Open reads four adjacent caller-stack words into private window
    # fields. Vary the saved SI/DI words and unused stack poison. The selected
    # resource has no mode-5 object, so these words must not affect behavior.
    for si,di,poison in ((0x1357,0x2468,0x11),(0xffff,0x8000,0xee),
                         (0x0000,0x0000,0x00),(0x7fff,0x8001,0x5a)):
        c=case(f'window-args-poison/{si:04x}/{di:04x}/{poison:02x}',0,640,0,
               [13],[],[0,0,10,10],0x9876)
        c.registers.update({'si':si,'di':di,'stack_poison':poison})
        c.metadata['window_arg_poison']={'si':si,'di':di,'stack_byte':poison}
        yield 'directed',c
    rng=random.Random(seed)
    accepted={13,27,67,68,83,99,100,115}
    ignored=[k for k in range(256) if k not in accepted]
    for i in range(count):
        keys,events=rng.choice(endings)
        prefix=[rng.choice(ignored) for _ in range(rng.randrange(12))]
        # Each ignored key is followed by a nonterminating event result.
        events=([None]*len(prefix))+list(events)
        text=bytes(rng.randrange(1,256) for _ in range(rng.randrange(1,100)))
        yield 'randomized',case(f'random/{seed}/{i}',rng.choice([0,1]),rng.choice([320,640]),
            rng.randrange(4),prefix+keys,events,[rng.randrange(-500,501) for _ in range(4)],
            rng.randrange(65536),text)


def expected_interaction(keys,events):
    key_result={13:0,68:0,100:0,27:2,67:2,99:2,83:1,115:1}
    event_result={0x2103:0,0x2104:1,0x2105:2}
    ki=ei=0
    while ki<len(keys):
        key=keys[ki];ki+=1
        if key in key_result:
            return key_result[key],keys[ki:],events[ei:]
        if ei<len(events):
            item=events[ei];ei+=1
            if item is not None and item in event_result:
                return event_result[item],keys[ki:],events[ei:]
    while ei<len(events):
        item=events[ei];ei+=1
        if item is not None and item in event_result:
            return event_result[item],keys[ki:],events[ei:]
    raise AssertionError('test input must contain a terminating key or event')


def _actual_lock_init_writes(pair,fixture):
    """Run original win_LockInit on scratch DOS state; pin its nonstack writes."""
    scratch=b.Machine(pair)
    initial={a+i for a,data in fixture.writes for i in range(len(data))}
    old=pair.sequence_function
    pair.sequence_function=lambda name:b.functions.get(name)
    try:
        result=scratch.run(b.Case(label='fixture/win-LockInit',writes=fixture.writes,
                                  return_kind='void'),function='win_LockInit')
    finally:
        pair.sequence_function=old
    addresses=sorted(set(result['written_addresses'])-initial)
    stack0,stack1=scratch.stack_bounds
    addresses=[a for a in addresses if not stack0<=a<stack1]
    groups=[]
    for address in addresses:
        if groups and address==groups[-1][-1]+1: groups[-1].append(address)
        else: groups.append([address])
    writes=[(g[0],scratch.read(g[0],len(g))) for g in groups]
    return writes,{'initializer':'win_LockInit','executed_original':True,
        'changed_nonstack_bytes':len(addresses),
        'write_groups':[{'address':hex(g[0]),'length':len(g)} for g in groups]}


def run(count,seed,out):
    pair=b.PreparedPair(FUNCTION,out=out); counts={'directed':0,'randomized':0};failures=[]
    ledger=CaseLedger(out/'cases.jsonl.gz',pair,EFFECTS)
    started=time.monotonic()
    setup_evidence=None
    positive=None
    poison_semantics=None
    poison_evidence=[]
    helper_observations={}
    for group,c in cases(count,seed):
        if setup_evidence is None:
            setup_writes,setup_evidence=_actual_lock_init_writes(pair,c)
        c.writes.extend(setup_writes)
        try: r=pair.compare(c)
        except Exception as exc:
            failures.append({'case':c.metadata,'error':str(exc)});break
        counts[group]+=1
        row=ledger.record(c,r,lane=group)
        for call in r.original['trace']:
            name=call['name']
            spec=c.callbacks.get(name)
            mode='MODELED' if spec is not None and spec.handler is not None else 'ORIGINAL_EXE'
            observed=helper_observations.setdefault(name,{
                'name':name,'execution_mode':mode,
                'executed_from_original':mode=='ORIGINAL_EXE',
                'observed_call_count':0,'observed_case_count':0,
                'positive_case_ids':[],'_seen_case_ids':set(),
                'callback_abi':None})
            observed['observed_call_count']+=1
            observed['execution_mode']=mode
            observed['executed_from_original']=mode=='ORIGINAL_EXE'
            if row['case_id'] not in observed['_seen_case_ids']:
                observed['_seen_case_ids'].add(row['case_id'])
                observed['observed_case_count']+=1
                if len(observed['positive_case_ids'])<5:
                    observed['positive_case_ids'].append(row['case_id'])
            if spec is not None:
                observed['callback_abi']={'stack_words':spec.stack_words,
                    'register_args':list(spec.register_args),'callee_pop_bytes':spec.pop,
                    'handler':(getattr(spec.handler,'__name__',type(spec.handler).__name__)
                               if spec.handler is not None else None),
                    'projection':(getattr(spec.project,'__name__',type(spec.project).__name__)
                                  if spec.project is not None else None)}
        if positive is None and r.equal and c.metadata['which'] in (0,1):
            positive={'case_id':row['case_id'],'executed':True,
                'original_executed':True,'candidate_executed':True,'baseline_matches':True,
                'original_observation_sha256':row['original_observation_sha256'],
                'candidate_observation_sha256':row['candidate_observation_sha256'],
                'identity':pair.identity,'suite_sha256':b.digest(SUITE_SOURCE)}
        expected,keys_left,events_left=expected_interaction(c.state['keys'],c.state['events'])
        for lane,result in (('original',r.original),('candidate',r.candidate)):
            state=result['state']
            if result['return']!=expected or state['keys']!=keys_left or state['events']!=events_left:
                failures.append({'case':c.metadata,'lane':lane,'expected':{
                    'return':expected,'keys_left':keys_left,'events_left':events_left},
                    'actual':{'return':result['return'],'keys_left':state['keys'],
                              'events_left':state['events']}})
                break
            window_payload=bytes.fromhex(result['ranges']['actual_2100_payload'])
            zorder=struct.unpack('<32H',bytes.fromhex(result['ranges']['actual_window_stack']))
            if 'window_arg_poison' in c.metadata:
                poison=c.metadata['window_arg_poison']
                expected_private=b.words(poison['si'],poison['di'])+bytes([poison['stack_byte']])*4
                actual_private=window_payload[0x10:0x18]
                semantic={'return':result['return'],
                    'rect':list(struct.unpack_from('<4h',window_payload,0)),
                    'flags':struct.unpack_from('<H',window_payload,0x1c)[0],
                    'objects':state['drawn_windows'][0]['objects'],
                    'zorder':zorder[:4], 'resource_state':state['resource_state'],
                    'flush_count':state['flush_count'], 'invalidated':state['invalidated_rects']}
                if actual_private!=expected_private:
                    failures.append({'case':c.metadata,'lane':lane,
                        'expected_private_window_args':expected_private.hex(),
                        'actual_private_window_args':actual_private.hex()})
                    break
                if poison_semantics is None:
                    poison_semantics=semantic
                elif semantic!=poison_semantics:
                    failures.append({'case':c.metadata,'lane':lane,
                        'expected_poison_invariant':poison_semantics,
                        'actual_poison_semantic':semantic})
                    break
                if lane=='original':
                    poison_evidence.append({'input':poison,'private_bytes':actual_private.hex(),
                        'semantic_sha256':b.digest(json.dumps(semantic,sort_keys=True).encode()),
                        'matched_baseline':semantic==poison_semantics})
            if (state['resource_state']!='acquired-firm' or state['stale_events'] or
                    state['flush_count']!=1 or zorder[:2]!=(c.metadata['previous_window'],0x8000) or
                    struct.unpack_from('<H',window_payload,0x1c)[0]!=0x0840 or
                    list(struct.unpack_from('<4h',window_payload,0))!=[133,70,470,236] or
                    len(state['drawn_windows'])!=1 or state['drawn_windows'][0]['win']!=0x2100 or
                    len(state['invalidated_rects'])!=1):
                failures.append({'case':c.metadata,'lane':lane,'expected_window':{
                    'resource_state':'acquired-firm','stale_events':[],'flush_count':1,
                    'zorder':list((c.metadata['previous_window'],0x8000)),
                    'closed_flag_word':0x0840,'rect':[133,70,470,236],
                    'draws':1,'invalidations':1},'actual_window':{
                    'resource_state':state.get('resource_state'),
                    'stale_events':state.get('stale_events'),'flush_count':state.get('flush_count'),
                    'zorder':list(zorder[:2]),'flag_word':struct.unpack_from('<H',window_payload,0x1c)[0],
                    'rect':list(struct.unpack_from('<4h',window_payload,0)),
                    'draws':state.get('drawn_windows'),'invalidations':state.get('invalidated_rects')}})
                break
            heap=bytes.fromhex(result['ranges']['dialog_resource_heap'])
            manager=bytes.fromhex(result['ranges']['dialog_manager_state'])
            paras=c.metadata['resource_paras']
            expected_manager={
                'hard_paras':0,
                'soft_paras':paras+c.metadata['window_paras'],
                'firm_paras':0,
                'used_paras':paras+c.metadata['window_paras'],
                'free_paras':c.metadata['free_paras'],
                'total_paras':paras+c.metadata['window_paras']+c.metadata['free_paras'],
                'allocated_handles':2,
                'live_handles':2,
            }
            actual_manager={
                'hard_paras':struct.unpack_from('<H',manager,0x0c)[0],
                'soft_paras':struct.unpack_from('<H',manager,0x0e)[0],
                'firm_paras':struct.unpack_from('<H',manager,0x10)[0],
                'used_paras':struct.unpack_from('<H',manager,0x12)[0],
                'free_paras':struct.unpack_from('<H',manager,0x14)[0],
                'total_paras':struct.unpack_from('<H',manager,0x16)[0],
                'allocated_handles':struct.unpack_from('<H',manager,0x18)[0],
                'live_handles':struct.unpack_from('<H',manager,0x1a)[0],
            }
            window_head=c.metadata['window_data_seg']*16-(2*16)
            window_header_off=window_head-(lists.DATA[1]-2)*16
            if (heap[8]!=3 or heap[0x12]!=0 or
                    heap[window_header_off+8]!=3 or heap[window_header_off+0x12]!=0 or
                    actual_manager!=expected_manager):
                failures.append({'case':c.metadata,'lane':lane,'expected_ralloc':{
                    'text_header_type':3,'text_header_attr':0,'window_header_type':3,
                    'window_header_attr':0,'manager':expected_manager},
                    'actual_ralloc':{'text_header_type':heap[8],'text_header_attr':heap[0x12],
                                     'window_header_type':heap[window_header_off+8],
                                     'window_header_attr':heap[window_header_off+0x12],
                                     'manager':actual_manager}})
                break
            expected_object=((0x41-c.metadata['which'])*2)&0xffff
            expected_request={'object':expected_object,'kind':10,'type':1,
                              'handle':list(lists.HANDLE)}
            if state['resource_requests']!=[expected_request]:
                failures.append({'case':c.metadata,'lane':lane,'expected_resource':
                    [expected_request],'actual_resource':state['resource_requests']})
                break
            expected_font=(0x1234,0x2211) if c.metadata['width']==320 else (0x5678,0x3344)
            print_call=next((entry for entry in result['trace']
                             if entry['name']=='win_PrintTextInRect'),None)
            font_calls=[entry['args'] for entry in result['trace']
                        if entry['name']=='f_24AB_02AD']
            expected_font_id=2 if c.metadata['width']==320 else 4
            if (not print_call or tuple(print_call['args']['font_pointer'])!=expected_font or
                    font_calls!=[[expected_font_id],[0]]):
                failures.append({'case':c.metadata,'lane':lane,'expected_font':{
                    'pointer':expected_font,'selector_calls':[[expected_font_id],[0]]},
                    'actual_font':{'print_call':print_call,'selector_calls':font_calls}})
                break
        if failures: break
        if not r.equal: failures.append({'case':c.metadata,'diff':r.diff});break
    for observed in helper_observations.values():
        observed.pop('_seen_case_ids',None)
    source=pair.source.read_text(encoding='latin1')
    anchor="case 's':\n                result = 1;"
    if source.count(anchor)!=1: raise RuntimeError('negative source anchor not unique')
    mutant=out/'negative-return.c'
    mutant.write_text(source.replace(anchor,"case 's':\n                result = 2;",1),encoding='latin1')
    negpair=b.PreparedPair(FUNCTION,source=mutant,out=out/'negative-return')
    negcase=case('negative/save-becomes-cancel',1,640,0,[115],[],[0,0,100,100],0x9876)
    negcase.writes.extend(_actual_lock_init_writes(negpair,negcase)[0])
    neg=negpair.compare(negcase)
    release_anchor='    db_ReleaseHandle(h);'
    if source.count(release_anchor)!=1: raise RuntimeError('negative release source anchor not unique')
    release_mutant=out/'negative-release.c'
    release_mutant.write_text(source.replace(release_anchor,'    /* negative control: release omitted */',1),encoding='latin1')
    release_pair=b.PreparedPair(FUNCTION,source=release_mutant,out=out/'negative-release')
    release_case=case('negative/omit-resource-release',1,640,0,[115],[],[0,0,100,100],0x9876)
    release_case.writes.extend(_actual_lock_init_writes(release_pair,release_case)[0])
    release_neg=release_pair.compare(release_case)
    # Diagnostic negative control: mode 5 explicitly reads win_Open's private
    # words. Mutate only object 0's first mode from constant to mode 5; changed
    # SI must then move the object's left/right coordinates.
    mode5_results=[]
    for si in (1,20):
        diagnostic=case(f'negative/mode5-uses-open-arg/{si}',0,640,0,[13],[],
                        [0,0,10,10],0x9876)
        diagnostic.registers.update({'si':si,'di':2,'stack_poison':0xa5})
        base=diagnostic.metadata['window_data_seg']*16
        resource=diagnostic.metadata['actual_window_resource']
        for index,(address,data) in enumerate(diagnostic.writes):
            if address==base:
                changed=bytearray(data)
                struct.pack_into('<h',changed,resource['object_offsets'][0]+0x18,5)
                diagnostic.writes[index]=(address,bytes(changed))
                break
        else:
            raise RuntimeError('mode-5 diagnostic could not locate window payload')
        diagnostic.writes.extend(_actual_lock_init_writes(pair,diagnostic)[0])
        comparison=pair.compare(diagnostic)
        if not comparison.equal:
            failures.append({'case':diagnostic.metadata,'diff':comparison.diff})
        diagnostic_payload=bytes.fromhex(comparison.original['ranges']['actual_2100_payload'])
        mode5_results.append({'si':si,'rect':list(struct.unpack_from('<4h',diagnostic_payload,
            resource['object_offsets'][0])),'original_candidate_equal':comparison.equal,
            'oracle_observation_sha256':b.digest(json.dumps(comparison.original).encode()),
            'candidate_observation_sha256':b.digest(json.dumps(comparison.candidate).encode())})
    def negative_evidence(control_id,mutant_path,mutant_pair,comparison,object_dir):
        object_path=out/object_dir/'candidate.obj'
        return {'id':control_id,'executed':True,'original_executed':True,
            'mutant_executed':True,'baseline_matches':True,'mutant_differs':not comparison.equal,
            'execution_errors':0,'mismatch_categories':list(comparison.diff),
            'identity':mutant_pair.identity,'suite_sha256':b.digest(SUITE_SOURCE),
            'mutant_source':{'path':mutant_path.resolve().relative_to(ROOT).as_posix(),
                             'sha256':b.digest(mutant_path.read_bytes())},
            'mutant_object':{'path':object_path.resolve().relative_to(ROOT).as_posix(),
                             'sha256':b.digest(object_path.read_bytes())},
            'diff':comparison.diff}
    report={'schema':'behavior-suite-run-v1','function':FUNCTION,'identity':pair.identity,
        'suite_sha256':b.digest(SUITE_SOURCE),'directed':counts['directed'],'randomized':counts['randomized'],
        'case_ledger':ledger.finalize(),
        'mismatches':len([f for f in failures if 'diff' in f]),'errors':len([f for f in failures if 'error' in f]),
        'positive_control':positive,
        'window_arg_poison_controls':{'count':len(poison_evidence),
            'controls':poison_evidence,'semantic_invariant':poison_semantics,
            'negative_mode5_control':mode5_results,
            'mode5_detected_effect':len(mode5_results)==2 and
                mode5_results[0]['rect']!=mode5_results[1]['rect']},
        'source_definition_pins':source_definition_pins(),
        'helper_boundaries':[helper_observations[name] for name in sorted(helper_observations)],
        'fixture_setup':{'lock_init':setup_evidence,
            'captured_nonstack_write_sha256':b.digest(json.dumps(
                [(hex(address),data.hex()) for address,data in setup_writes],
                separators=(',',':')).encode()),
            'captured_nonstack_write_bytes':sum(len(data) for _,data in setup_writes),
            'all_static_setup_values_are_zero_or_lockinit_one':all(
                set(data)<={0,1} for _,data in setup_writes)},
        'dependency_pins':{
            relative:b.digest((ROOT/relative).read_bytes()) for relative in (
                'tools/behavior_suites/lists.py',
                'tools/behavior_ledger.py',
                'tools/behavior_suites/archive/window-memory-fixture-dda4f6dd.py')},
        'negative_controls':[
            negative_evidence('save-result-mutated-to-cancel',mutant,negpair,neg,'negative-return'),
            negative_evidence('omit-resource-release',release_mutant,release_pair,release_neg,'negative-release')],
        'failures':failures,'seed':seed,'status':'UNRESOLVED: host command boundary pending review',
        'compared':EFFECTS,
        'domain':'caller values which=0 (LoadGame) and which=1 (MenuQuit); all dialog keys/events, keyboard/event arbitration, ignored input, both video widths, display flags, distinct signed dialog/text rectangles, arbitrary nonzero resource text, hostile volatile register returns',
        'boundaries':'the actual uncompressed HCEGANT 0x2100 window resource is loaded into a valid DOS Ralloc arena; original win_Open/win_Close, z-order stack mutation/removal, win_Recalc, win_GetObjRect, window LockInit/lock/unlock, db_ReleaseHandle and f_171C_15A2 execute; renderer/cursor primitives and future input/resource/text services are logical command/provider boundaries; stale input is flushed; manager counters, text/window headers, window flags/geometry, prior-current restoration, resource handles and allocation totals are observed; target-only dialog bitmap/text paths are normalized host commands with their source helper definitions pinned for review',
        'elapsed_seconds':round(time.monotonic()-started,3)}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    if failures or neg.equal or release_neg.equal or not report['window_arg_poison_controls']['mode5_detected_effect']:
        raise AssertionError(failures or 'negative control was not detected')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--count',type=int,default=10000)
    p.add_argument('--seed',type=lambda s:int(s,0),default=0x0239)
    p.add_argument('--out',type=Path,default=ROOT/'build/workers/behavior_dialog/ledger-20261002')
    a=p.parse_args();print(json.dumps(run(a.count,a.seed,a.out),indent=2))

