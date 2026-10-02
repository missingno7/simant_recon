"""Quit dialog ordered command/input contract, with original Ralloc helpers."""
import argparse
import hashlib
import json
import random
import struct
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from behavior_suites import lists
import behavior as b
from behavior_ledger import CaseLedger

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
    m.write((data_seg-2)*16+8,b'\x01')
    m.state['resource_requests'].append({'object':args[0],'kind':args[1],
                                         'type':args[2],'handle':list(lists.HANDLE)})
    m.state['resource_state']='acquired-firm'
    return lists.HANDLE


def release_resource(m,args):
    # The boundary models f_1A53_00F0/db_ReleaseHandle against a single valid
    # fixture handle.  Source db_ReleaseHandle delegates to f_171C_15A2(h,3),
    # which stores the released soft type and clears attr when flags are 3.
    handle_at=linear(args)
    data_off,data_seg=struct.unpack('<HH',m.read(handle_at,4))
    header_at=(data_seg-2)*16
    m.write(header_at+8,b'\x03')
    m.write(header_at+0x12,b'\x00')
    m.state['resource_state']='released-soft'
    clobber(m)


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


def case(label,which,width,mono,keys,events,rect,volatile,text=b'Dialog text',rects=None):
    fixture=lists.make_case(label,[text],0,1,0)
    dg=b.match.DGROUP_SEG*16
    empty=b.symbol('f_1B4E_000C'); zero=b.symbol('f_171C_001E')
    fixture.args=[which&65535]; fixture.registers={};fixture.callee_pop=0;fixture.return_kind='s16'
    fixture.state={'keys':list(keys),'events':list(events),
        'rects':dict(rects or {'default':rect,0x2100:rect,0x2101:rect}),
        'volatile':volatile,'open_windows':[],'closed_windows':[],'resource_requests':[]}
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
    fixture.callbacks={
        'win_Open':b.Callback(1,win_open),
        'f_1A53_00F0':b.Callback(3,resource),
        'f_171C_1B84':b.Callback(2),
        'f_171C_1BBA':b.Callback(2),
        'db_ReleaseHandle':b.Callback(2,release_resource),
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
                      'rect':rect,'rects':rects,'volatile':volatile,'resource':text.hex()}
    return fixture


def cases(count,seed):
    endings=[([k],[]) for k in (13,27,67,68,83,99,100,115)]
    endings += [([], [e]) for e in (0x2103,0x2104,0x2105)]
    for which in (-1,0,1,2,0x7FFF):
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


def run(count,seed,out):
    pair=b.PreparedPair(FUNCTION,out=out); counts={'directed':0,'randomized':0};failures=[]
    ledger=CaseLedger(out/'cases.jsonl.gz',pair,EFFECTS)
    started=time.monotonic()
    positive=None
    for group,c in cases(count,seed):
        try: r=pair.compare(c)
        except Exception as exc:
            failures.append({'case':c.metadata,'error':str(exc)});break
        counts[group]+=1
        row=ledger.record(c,r,lane=group)
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
            if state['open_windows'] or state['closed_windows']!=[0x2100] or \
                    state['resource_state']!='released-soft':
                failures.append({'case':c.metadata,'lane':lane,'expected_side_effects':{
                    'open_windows':[],'closed_windows':[0x2100],
                    'resource_state':'released-soft'},'actual_side_effects':{
                    'open_windows':state['open_windows'],'closed_windows':state['closed_windows'],
                    'resource_state':state.get('resource_state')}})
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
    source=pair.source.read_text(encoding='latin1')
    anchor="case 's':\n                result = 1;"
    if source.count(anchor)!=1: raise RuntimeError('negative source anchor not unique')
    mutant=out/'negative-return.c'
    mutant.write_text(source.replace(anchor,"case 's':\n                result = 2;",1),encoding='latin1')
    negpair=b.PreparedPair(FUNCTION,source=mutant,out=out/'negative-return')
    neg=negpair.compare(case('negative/save-becomes-cancel',1,640,0,[115],[],[0,0,100,100],0x9876))
    release_anchor='    db_ReleaseHandle(h);'
    if source.count(release_anchor)!=1: raise RuntimeError('negative release source anchor not unique')
    release_mutant=out/'negative-release.c'
    release_mutant.write_text(source.replace(release_anchor,'    /* negative control: release omitted */',1),encoding='latin1')
    release_pair=b.PreparedPair(FUNCTION,source=release_mutant,out=out/'negative-release')
    release_neg=release_pair.compare(case('negative/omit-resource-release',1,640,0,[115],[],[0,0,100,100],0x9876))
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
        'negative_controls':[
            negative_evidence('save-result-mutated-to-cancel',mutant,negpair,neg,'negative-return'),
            negative_evidence('omit-resource-release',release_mutant,release_pair,release_neg,'negative-release')],
        'failures':failures,'seed':seed,'status':'UNRESOLVED: host command boundary pending review',
        'compared':EFFECTS,
        'domain':'caller values which=0 (LoadGame) and which=1 (MenuQuit); all dialog keys/events, keyboard/event arbitration, ignored input, both video widths, display flags, distinct signed dialog/text rectangles, arbitrary nonzero resource text, hostile volatile register returns',
        'boundaries':'window/input/resource providers are modeled; original Ralloc lock/unlock executes; db_ReleaseHandle is modeled at the valid-handle boundary from its source contract (set block type 3, clear attr), excluding allocator-wide private accounting; actual font selector executes and active font pointer is projected into text output; distinct object rectangles and input queues are captured',
        'elapsed_seconds':round(time.monotonic()-started,3)}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    if failures or neg.equal or release_neg.equal: raise AssertionError(failures or 'negative control was not detected')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--count',type=int,default=10000)
    p.add_argument('--seed',type=lambda s:int(s,0),default=0x0239)
    p.add_argument('--out',type=Path,default=ROOT/'build/workers/behavior_dialog/ledger-20261002')
    a=p.parse_args();print(json.dumps(run(a.count,a.seed,a.out),indent=2))
