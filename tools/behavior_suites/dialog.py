"""Quit dialog ordered command/input contract, with original Ralloc helpers."""
import argparse
import hashlib
import json
import random
import re
import struct
import sys
import time
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'layout/functions.json').is_file())

from behavior_suites import lists
import behavior as b
from behavior_ledger import CaseLedger

from behavior_suites import memory as memory_fixture

FUNCTION='o15_384C_0239'
SUITE_SOURCE=Path(__file__).read_bytes()
EFFECTS=['return','ordered GUI/window/font/resource/input commands','rectangle/text/font contents',
         'resource lock/unlock/release and age','input arbitration and consumption',
         'logical window state','all nonstack writes','caller ABI']




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
    arena=memory_fixture.heap_case(fixture.label+'/real-2100-window',[
        (text_paras,0,{'size':len(text),'name':b'dialog-text'}),
        (win_paras,1,{'size':len(payload),'name':b'window-2100'}),
        (free_paras,0x80,{'name':b'dialog-window-tail'})],handles=[0,1],
        heap_seg=lists.DATA[1]-2,heap_paras=0x100,handle_seg=lists.HANDLE[1],
        contract='text handle plus actual uncompressed HCEGANT window 0x21 kind0 and linked free tail')
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
    arena=memory_fixture.heap_case(label+'/ralloc',
        [(paras,0,{'size':len(text),'name':b'dialog-text'}),
         (16,0x80,{'name':b'dialog-tail'})], handles=[0],
        heap_seg=lists.DATA[1]-2,handle_seg=lists.HANDLE[1],
        contract='valid type-0 resource handle and linked free tail; consistent Ralloc counters')
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
    result=scratch.run(b.Case(label='fixture/win-LockInit',writes=fixture.writes,
                              return_kind='void'),original_entry=b.functions.get('win_LockInit'))
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





