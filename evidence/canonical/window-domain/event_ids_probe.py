"""Original event-ID controls and complete reviewed event-root census."""
from pathlib import Path
import hashlib, importlib.util, json, re, struct, sys
from types import SimpleNamespace
sys.dont_write_bytecode=True
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'src/program.json').is_file())
sys.path.insert(0,str(ROOT/'tools'))
import behavior as b, csrc, exe, functions, resource_domains as r
if not __debug__: raise RuntimeError('proof checks require Python without -O')
spec=importlib.util.spec_from_file_location('palette_contract', ROOT/'evidence/canonical/window-domain/palette_probe.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
TARGETS=set('f_218D_000C f_218D_01EB win_GetProxEvent _win_SetProxItem f_218D_023A f_218D_02D5 win_Events win_GetEvent win_FlushEvents f_218D_0451 f_218D_052F f_218D_0656 f_1B73_030F f_1B73_036E f_1B73_0AC3 f_1B73_0B00 f_1B73_0B5B f_1B73_0BC5 f_1B73_0BFF f_1B73_0C42 f_1B73_0C80 f_1FD2_032F f_1FD2_0390 f_1FD2_03EB f_1FD2_0438 f_1FD2_044F f_1FD2_049C f_1FD2_0883 o10_35F5_0000 o10_35F5_00D7 o17_384C_0184 f_2505_033C f_2505_03B9 f_2505_0453 f_2505_04D7 f_2505_0831 f_2505_08EA RepointObjects win_Recalc win_SetObjBitmap f_20E8_0903 win_SetObjSelectableState win_SetGroupSelectableState win_SetGroupSelectedState win_SetGroupVisibleState win_ProcSliderEvent win_DrawElevator f_23E6_0A53 o26_39C7_0000 o26_39C7_040F o26_39C7_0671'.split())
DATA=set('g_6368 fd_50F6_49FA fd_50F6_4A0A g_6004 g_6016 g_6028 g_603A fd_5071_0060 fd_5071_03C4 fd_5071_0728 input_queue'.split())
TARGETS.update(('win_ObjAddr','win_WinAddr','f_2505_0006'))
def census(overrides=None):
    p.TARGETS=TARGETS;p.DATA=DATA
    texts=p.inventory();texts.update(overrides or {});aliases=p.alias_map()
    asm_names={name.lstrip('_').casefold() for name in aliases}
    def relevant(rel,text):
        if not rel.endswith('.asm'):return any(n in text for n in aliases)
        for line in text.splitlines():
            code=re.sub(r'"[^\"]*"','',line.split(';')[0])
            if any(name.lstrip('_').casefold() in asm_names for name in re.findall(r'[A-Za-z_][A-Za-z0-9_]*',code)):return True
        return False
    asm={rel:hashlib.sha256(text.encode()).hexdigest() for rel,text in texts.items() if rel.endswith('.asm') and relevant(rel,text)}
    ctexts={rel:t for rel,t in texts.items() if rel.endswith('.c')}
    bindings=[line for line in ctexts['src/root/m1FD2.c'].splitlines() if line.startswith(('struct Timer g_6004 =','struct Timer g_603A ='))]
    assert len(bindings)==2 and all('f_1B73_030F' in line for line in bindings)
    for line in bindings:ctexts['src/root/m1FD2.c']=ctexts['src/root/m1FD2.c'].replace(line,line.replace('f_1B73_030F','0'))
    result=p.census(ctexts)
    result['reviewed_descriptor_callback_bindings']=bindings
    result['asm_source_pins']=asm
    result['source_sha256']={rel:hashlib.sha256(t.encode()).hexdigest() for rel,t in texts.items() if relevant(rel,t)}
    return result

def domains():
    p.check_inputs()
    windows,_,_=p.resources()
    refs=[]; counts=[]; codes=[]; links=[]
    for wid,raw,w in windows:
        n=w['object_count'];counts.append(n)
        for o in w['objects']:
            codes.append(wid*256+o['index'])
            for axis,(mode,ref) in enumerate(zip(o['modes'],o['refs'])):
                if 1<=mode<=4:
                    assert 0<=ref>>8<=33
                    target=windows[ref>>8][2]
                    assert ref&255<target['object_count']
                    refs.append([wid,o['index'],axis,mode,ref])
            if o['type'] in (7,8):
                link=struct.unpack_from('<h',raw,o['offset']+40)[0]
                if link>0:links.append([wid,o['index'],link])
    assert max(counts)==31 and links==[[22,8,0x1609]]
    return windows,dict(window_count=len(windows),object_count=len(codes),counts=counts,
        mode_1_to_4_refs=len(refs),ref_window_min=min(x[4]>>8 for x in refs),ref_window_max=max(x[4]>>8 for x in refs),
        ref_sha256=hashlib.sha256(json.dumps(refs,separators=(',',':')).encode()).hexdigest(),slider_links=links,
        registered_object_code_min=min(codes),registered_object_code_max=max(codes),all_ref_objects_valid=True)

def machine(name):
    image=exe.load()
    return b.Machine(SimpleNamespace(function=functions.get(name),vectors={exe.MANAGER_SEG*16+v.offset:v for v in image.vectors},identity={'oracle_sha256':image.sha256}))

def controls(windows):
    slot=b.symbol_address('fd_5071_03C4');tmp=0x80000;stack=b.symbol_address('g_5702')
    registered=0; block_count=0
    for wid,raw,w in windows:
        m=machine('f_1FD2_03EB')
        for i in range(w['object_count']):
            # Distinct rectangles exercise each descriptor via real registration,
            # removal/search, prepend and mouse-code selection instructions.
            writes=[(slot,b.words(0)),(tmp,b.words(i*8,0,i*8+6,6))] if i==0 else []
            if i:m.write(tmp,b.words(i*8,0,i*8+6,6))
            m.run(b.Case('register shipped object code',args=[0,0x8000,wid*256+i],writes=writes,
                callbacks={'f_1B73_00D9':b.Callback(0,lambda m,a:(0,0))},return_kind='void'),preserve=i!=0)
            assert struct.unpack('<H',m.read(slot,2))[0]==i+1
            block_count+=m.blocks
        for i in range(w['object_count']):
            m.write(b.symbol_address('g_9122'),b.words(i*8+1,1))
            m.run(b.Case('select registered code'),preserve=True,original_entry=functions.get('f_1B73_0BFF'))
            assert m.reg('ax')==wid*256+i
            registered+=1;block_count+=m.blocks
        m.write(b.symbol_address('g_9122'),b.words(0x7fff,0x7fff))
        m.run(b.Case('outside rectangles'),preserve=True,original_entry=functions.get('f_1B73_0BFF'))
        assert m.reg('ax')==0
    # Deliberately fabricated descriptor demonstrates lack of ID validation in
    # mouse selection. It is a producer-domain contrast, not nominal reachability.
    m=machine('f_1FD2_03EB')
    m.run(b.Case('fabricated descriptor',args=[0,0x8000,0x2201],writes=[(slot,b.words(0)),(tmp,b.words(0,0,6,6))],
        callbacks={'f_1B73_00D9':b.Callback(0,lambda m,a:(0,0))},return_kind='void'))
    m.write(b.symbol_address('g_9122'),b.words(1,1))
    m.run(b.Case('fabricated selector'),preserve=True,original_entry=functions.get('f_1B73_0BFF'))
    assert m.reg('ax')==0x2201
    # Original dispatch ordinary-vs-special gate. Callback downstream consumers
    # observe forwarded IDs; queue/database/audio services are explicit models.
    rows=[]
    for top,code in [(0x2100,0x2101),(0x2100,0x2201),(0x8000,0x2101),(0x2100,0xFE04),(0x2100,0xFB21),(0x2100,0xF085),(0x2100,0xF086),(0x2100,0xF087),(0x2200,0x2201)]:
        seen=[];m=machine('f_218D_02D5')
        def dequeue(m,a):
            m.write(a[1]*16+a[0],b.words(0,0,0,0,1,1,code,0));return (0,0)
        def record(name):
            return lambda m,a:(seen.append([name,m.reg('ax'),struct.unpack('<H',m.read(b.symbol_address('fd_50F6_49FA')+12,2))[0]]) or (0,0))
        m.run(b.Case('original dispatch',writes=[(stack,b.words(top,0x8000)),(0x55b30+0x8cec,b'\0')],callbacks={
            'f_1B28_0069':b.Callback(0,lambda m,a:(0,0)),'f_0000_046F':b.Callback(0,lambda m,a:(0,0)),
            'f_1B73_032A':b.Callback(0,lambda m,a:(1,0)),'f_1B73_032E':b.Callback(2,dequeue),
            'f_218D_000C':b.Callback(0,record('ordinary')),'f_218D_023A':b.Callback(0,record('hover')),
            'o26_39C7_0000':b.Callback(0,record('zoom')),'f_218D_0656':b.Callback(0,record('focus')),
            'win_FlushEvents':b.Callback(0,lambda m,a:(0,0))},return_kind='void'))
        kind='ordinary' if code==0x2101 and top==0x2100 or code==0x2201 and top==0x2200 else 'hover' if code==0xFB21 else 'zoom' if code==0xF085 else 'focus' if code in (0xF086,0xF087) else None
        assert [x[0] for x in seen]==([kind] if kind else [])
        rows.append(dict(top=top,code=code,called=seen))
    focus_rows=[];hover_rows=[]
    for wid,raw,w in windows:
        top=wid*256;n=w['object_count']
        for start in (top+1,top+n-1,-1):
            for direction in (1,-1):
                seen=[];m=machine('f_218D_0656')
                m.run(b.Case('original focus traversal',registers={'ax':direction},writes=[(stack,b.words(top,0x8000))],callbacks={
                    'f_218D_052F':b.Callback(0,lambda m,a:(start&65535,0)),
                    'f_22BF_0AC5':b.Callback(0,lambda m,a:(n,0)),
                    'f_22BF_0A97':b.Callback(0,lambda m,a:(1,0)),
                    'f_1B73_0C80':b.Callback(1,lambda m,a:(seen.append(a[0]) or (0,0)))},return_kind='void'))
                expected=[] if start==-1 else [top+((start-top-1+direction)%(n-1))+1]
                assert seen==expected and all(x>>8==wid for x in seen)
                focus_rows.append([wid,start,direction,seen])
        for candidate,old in ((top+1,-1),(((wid+1)%34)*256+1,-1),(0,top+2)):
            seen=[];m=machine('f_218D_023A');ev=0x80000;objptr=0x90000
            def addr(m,a):
                m.write(objptr+36,b.words(0x10 if m.reg('ax')==candidate else 0));return (0,0x9000)
            m.run(b.Case('original hover provenance',args=[0,0x8000],writes=[
                (ev,b.words(0,0,0,0,0,0,0xFB00+wid,0)),(stack,b.words(top,0x8000)),(0x55b30+0x6368,b.words(old))],callbacks={
                'win_LockWin':b.Callback(0,lambda m,a:(0,0)),
                'win_UnlockWin':b.Callback(0,lambda m,a:(0,0)),
                'f_1B73_0BFF':b.Callback(0,lambda m,a:(candidate,0)),
                'win_ObjAddr':b.Callback(0,addr),
                '_win_SetProxItem':b.Callback(0,lambda m,a:(seen.append(m.reg('ax')) or (0,0)))},return_kind='void',callee_pop=4))
            expected=[top+1] if candidate==top+1 else [65535] if old!=-1 else []
            assert seen==expected,(wid,candidate,old,seen)
            hover_rows.append([wid,candidate,old,seen])
    capacity=[]
    for name in ('f_1B73_0AC3','f_1B73_0B00'):
        for count in (46,47):
            m=machine(name);initial=b.words(count)+bytes([0xA5])*48*18
            def stop(m,a):raise b.ExecutionError('bounded capacity rejection')
            rejected=False;failure=None
            try:
                m.run(b.Case('original capacity check',args=[0,0x8000,slot%16,slot//16],writes=[
                    (slot,initial),(tmp,b.words(0,0,6,6,0,0,0x2101,0,0))],callbacks={
                    'f_1B73_00D9':b.Callback(0,lambda m,a:(0,0)),
                    'puts':b.Callback(1,lambda m,a:(0,0)),'Punt':b.Callback(0,stop)},return_kind='void'))
            except b.ExecutionError as err:
                if 'bounded capacity rejection' in str(err):failure='stopped at Punt entry'
                elif name=='f_1B73_0AC3' and count==47 and 'at 1B73:0AF5: unmodeled interrupt 01' in str(err):failure='original POPF restores trap flag from saved DS; INT01 at1B73:0AF5'
                else:raise
                rejected=True
            observed=struct.unpack('<H',m.read(slot,2))[0]
            assert rejected==(count==47) and observed==47
            if rejected:assert m.read(slot,len(initial))==initial
            else:assert m.read(slot+2+47*18,18)==bytes([0xA5])*18
            capacity.append(dict(function=name,input_count=count,output_count=observed,rejected_before_count_or_record_write=rejected,failure=failure))
    geometry=[]
    for obj in (0x2101,0x2201,0x3501):
        seen=[];m=machine('f_2505_0453');buf=bytearray(64);struct.pack_into('<h',buf,12,2)
        struct.pack_into('<HH',buf,44+4,0,0x9000)
        m.run(b.Case('original geometry ID gate',registers={'ax':obj,'dx':0},writes=[
            (b.symbol_address('win_numOfWindows'),b.words(34)),(0x80000,buf),(0x90000,b.words(17,18,19,20))],callbacks={
            'win_LockWin':b.Callback(0,lambda m,a:(seen.append(m.reg('ax')) or (0,0))),
            'win_UnlockWin':b.Callback(0,lambda m,a:(0,0)),
            'f_2505_0006':b.Callback(0,lambda m,a:(0,0x8000))},return_kind='int'))
        assert seen==([] if obj==0x2201 else [obj&0xff00])
        geometry.append(dict(object=obj,locks=seen,result=m.reg('ax')))
    return dict(original_selected_codes=registered,registered_selection_blocks=block_count,outside_cases=34,
                fabricated_descriptor_selected_code=0x2201,dispatch=rows,
                focus_cases=len(focus_rows),focus_sha256=hashlib.sha256(json.dumps(focus_rows).encode()).hexdigest(),
                hover_cases=len(hover_rows),hover_sha256=hashlib.sha256(json.dumps(hover_rows).encode()).hexdigest(),capacity=capacity,geometry=geometry)

def census_summary(value):
    return dict(sha256=hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
                direct_calls=sum(map(len,value['calls'].values())),source_sha256=value['source_sha256'],
                asm_source_pins=value['asm_source_pins'],
                callback_bindings=value['reviewed_descriptor_callback_bindings'])

def collect():
    windows,d=domains();m=machine('RepointObjects')
    raw=m.read(b.symbol_address('fd_4E4B_0000'),308*8)
    protected={'proxy':(0x55b30+0x6368,2),'delivered event':(b.symbol_address('fd_50F6_49FA'),16),
        'previous event':(b.symbol_address('fd_50F6_4A0A'),16),'input queue':(b.symbol_address('input_queue'),7*16),
        'event timer templates':(0x55b30+0x6004,18*3+18),
        **{n:(b.symbol_address(n)-2,4+48*18) for n in ('fd_5071_0060','fd_5071_03C4')},
        'fd_5071_0728':(b.symbol_address('fd_5071_0728')-2,4+10*18)}
    for i in range(307):
        size,count,off,seg=struct.unpack_from('<4H',raw,i*8);start=seg*16+off
        assert size and count and all(not(start<at+width and at<start+size*count) for at,width in protected.values())
    assert raw[-8:]==bytes(8)
    return dict(schema='simant-window-event-roots-v1',oracle_sha256=exe.EXPECTED_SHA256,
        domain=d,census=census_summary(census()),controls=controls(windows),save_origins={'descriptors':307,'protected_ranges':{n:list(v) for n,v in protected.items()},'overlaps':0})
if __name__=='__main__':
    print(json.dumps(collect(),indent=2))
