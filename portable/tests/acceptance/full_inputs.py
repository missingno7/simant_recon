"""Bind each DOS capture to native clock sites and retain input diagnostics."""
import json,re,subprocess,sys,hashlib
from pathlib import Path
if __package__:
    from .state_schema import ROOT,sha
else:
    from state_schema import ROOT,sha

OBJDUMP='C:/msys64/mingw64/bin/objdump.exe'

class InputCoverageError(ValueError):
    def __init__(self, step, message):
        self.step=step
        super().__init__(message)

def parse_trace(path,steps,require_quiet=False):
    records=[];inputs=[];pending=[];boundaries=[];reads=0;saw_delivery=False;site_reads={}
    quiet=None;quiet_delivered=False;quiet_context=None;quiet_time=0
    for line in path.read_text().splitlines():
        p=line.split()
        if not p or p[0]=='#':continue
        if p[:2]==['U','raise']:
            if quiet is not None:raise ValueError('Overlapping boundary holds')
            quiet=tuple(map(int,p[7:12]));quiet_delivered=False
            quiet_context=p[4:7];quiet_time=float(p[2])
            if quiet_time<float(p[3]):raise ValueError('Transition raised before its scheduled time')
            continue
        if p[:2]==['U','return']:
            if quiet is None or not quiet_delivered:raise ValueError('Boundary hold lacks actual IRQ delivery')
            if p[3:6]!=quiet_context or float(p[2])<quiet_time:
                raise ValueError('Boundary hold returned to a different foreground context')
            quiet=None
            continue
        if p[0]=='R':
            kind,pc,value,count=p[1:]
            if kind not in 'TBCV' or int(count)<=0 or not 0<=int(value)<2**32:raise ValueError('Invalid clock record')
            records.append((kind,int(pc,16),int(value),int(count)))
            reads+=int(count)
            key=f'{kind}:{int(pc,16)}';site_reads[key]=site_reads.get(key,0)+int(count)
        elif p[0]=='I':pending.append(dict(milliseconds=float(p[1]),pump=int(p[2]),clock_reads=reads,step=int(p[3]),phase=int(p[4]),description=' '.join(p[5:])))
        elif p[0]=='D':
            saw_delivery=True;kind=p[1];ax,bx,cx,dx=map(int,p[7:11])
            if int(p[6])!=reads:raise ValueError('Delivery read ordinal differs from complete preceding streams')
            candidates=[v for v in pending if v['description'].startswith(('key_', 'keydown ', 'keyup ') if kind=='K' else ('mouse_',))]
            if not candidates:
                if kind=='K' and ax&255!=0xe0:raise ValueError('Unpaired original keyboard scan; repeat/extra input requires an explicit contract')
                continue # Unpaired pointer callback retained in the raw trace; origin not inferred here.
            item=candidates[0];op=item['description'].split();op[0]={'keydown':'key_down','keyup':'key_up'}.get(op[0],op[0]);item['description']=' '.join(op)
            if kind=='K':
                scan=ax&255
                if scan==0xe0:continue
                if bool(scan&128)!=(op[0]=='key_up'):
                    raise InputCoverageError(item['step'],'Missing scan delivery for '+item['description']+
                        ' at submitted step '+str(item['step'])+'; next observed scan has the opposite direction')
                # Bind the keys in the supported scenario prefixes to DOS scan set 1.
                expected={'enter':0x1c,'kp_5':0x4c,'space':0x39,'f2':0x3c,'down':0x50,
                    'a':0x1e,'b':0x30,'c':0x2e,'e':0x12,'h':0x23,'i':0x17,'l':0x26,'m':0x32,'y':0x15,
                    'lshift':0x2a,'lctrl':0x1d,'0':0x0b,'1':0x02,'2':0x03,'3':0x04,'4':0x05,
                    '6':0x07,'8':0x09,'9':0x0a,'home':0x47,'esc':0x01,'tab':0x0f,
                    'f3':0x3d,'f4':0x3e,'f5':0x3f,'f6':0x40}.get(op[1])
                if expected is None or scan&127!=expected:raise InputCoverageError(item['step'],'Missing or unbound scan delivery: '+str((op,scan)))
            else:
                mask=ax&127
                expected=1 if op[0]=='mouse_move' else (2 if op[2]=='down' else 4)<<(2*int(op[1]))
                if not mask&expected:continue
            if require_quiet:
                actual=(int(p[3]),int(p[4]),int(p[5]),int(p[6]),int(p[12]))
                if quiet is None or actual!=quiet:
                    raise ValueError('IRQ was not delivered at its held service boundary: '+str((actual,quiet)))
                quiet_delivered=True
            pending.remove(item)
            item.update(scheduled_milliseconds=item['milliseconds'],milliseconds=float(p[2]),pump=int(p[3]),
                clock_reads=int(p[6]),step=int(p[4]),phase=int(p[5]),delivery_kind=kind,
                registers=dict(ax=ax,bx=bx,cx=cx,dx=dx),position=dict(site_reads),anchor=p[11] if len(p)>11 else None,queries=int(p[12]) if len(p)>12 else 0)
            inputs.append(item)
        elif p[0]=='S':
            if int(p[5])!=reads:raise ValueError('Boundary read ordinal differs from complete preceding streams')
            boundaries.append(dict(milliseconds=float(p[1]),pump=int(p[2]),step=int(p[3]),phase=int(p[4]),inputs=len(inputs) if saw_delivery else len(pending),clock_runs=len(records),clock_reads=int(p[5]),clock_hash=int(p[6]),queries=int(p[7]) if len(p)>7 else 0))
            boundaries[-1]['site_reads']=dict(site_reads)
            if int(p[3])==steps:break
    if require_quiet and quiet is not None:raise ValueError('Unfinished boundary hold')
    if len(boundaries)!=steps:raise ValueError('Missing compact simulation boundaries')
    if saw_delivery and pending:
        first=min(pending,key=lambda v:v['step'])
        raise InputCoverageError(first['step'],'Scripted transition lacks IRQ/callback delivery: '+first['description'])
    if not saw_delivery:inputs=pending # Parsing legacy captures is diagnostic only.
    return records,inputs,boundaries

def canonical_clock_calls(directory, manifest):
    """Bind canonical calls from its own OMF fixups and CodeView extents."""
    sys.path.insert(0,str(ROOT/'tools'))
    from omf import OmfReader
    execution=json.loads((directory/'execution-report.json').read_text())
    pin=next(p for p in execution['inputs'] if p['path'].endswith('build-report.json'))
    report_path=ROOT/pin['path']
    if sha(report_path)!=pin['sha256']:raise ValueError('Canonical build report changed')
    report=json.loads(report_path.read_text())
    candidate=report['link']['candidate_executable']
    if candidate['sha256']!=manifest['executable_sha256'] or sha(ROOT/candidate['path'])!=candidate['sha256']:
        raise ValueError('Canonical executable identity differs')
    addresses={}
    for line in (ROOT/candidate['path']).with_name('SOURCE.MAP').read_text(encoding='latin1').splitlines():
        match=re.match(r'\s*([0-9A-F]{4}):([0-9A-F]{4})\s+(?:Res|Ovl)\s+[_@](\w+)(?=\s|$)',line)
        if match:addresses.setdefault(match[3],int(match[1],16)*16+int(match[2],16))
    result={};base=manifest['runtime_base']
    from capstone import Cs,CS_ARCH_X86,CS_MODE_16
    decoder=Cs(CS_ARCH_X86,CS_MODE_16)
    for module in report['translation_units']:
        if 'object' not in module:continue
        path=ROOT/module['object']['path']
        if sha(path)!=module['object']['sha256']:raise ValueError('Canonical object changed')
        obj=OmfReader(communals=True).read(path.read_bytes())
        debug=bytes(obj.segments.get('$$SYMBOLS',b''));at=0
        while at<len(debug):
            length=debug[at];body=debug[at+1:at+1+length]
            if not length or len(body)!=length:raise ValueError('Truncated canonical CodeView')
            if body[0]==1 and len(body)>=15:
                name=body[15:15+body[14]].decode('latin1')
                size=int.from_bytes(body[5:7],'little')
                public=next((p for p in obj.publics if p['name'].lstrip('_@')==name),None)
                if public and name in addresses:
                    start=public['offset'];segment=public['segment']
                    raw=bytes(obj.segments[segment])[start:start+size]
                    calls=sorted(f['offset'] for f in obj.linker_fixups if f['segment']==segment
                                 and start<f['offset']<start+size and f['target_kind']=='external'
                                 and f['target']=='_TickCount' and f['loc']=='pointer32')
                    for index,offset in enumerate(calls):
                        if raw[offset-start-1]!=0x9a:raise ValueError('Canonical clock fixup is not a far CALL')
                        pc=base+addresses[name]+offset-start+4
                        result.setdefault(pc,[]).append(dict(name=name,index=index,count=len(calls),
                            unit=module['key'],function_sha256=hashlib.sha256(raw).hexdigest(),
                            evidence='own CodeView procedure length + OMF TickCount pointer32 fixup + MAP public'))
            at+=length+1
        if not debug:
            # Some pinned MSC profiles omit CodeView. Establish call ownership by
            # reachable instructions in the same object, never by the next symbol.
            from capstone import CS_GRP_JUMP,CS_GRP_RET,CS_GRP_IRET
            from capstone.x86 import X86_OP_IMM
            decoder.detail=True
            for public in obj.publics:
                name=public['name'].lstrip('_@');segment=public['segment'];start=public['offset']
                if name not in addresses:continue
                raw=bytes(obj.segments[segment]);pending=[start];seen=set();calls=[]
                other_starts={p['offset'] for p in obj.publics if p['segment']==segment and p['offset']!=start}
                fixes={f['offset']:f for f in obj.linker_fixups if f['segment']==segment and f['target_kind']=='external'
                       and f['target']=='_TickCount' and f['loc']=='pointer32'}
                while pending:
                    at=pending.pop()
                    if at in seen or at in other_starts or not 0<=at<len(raw):continue
                    seen.add(at);ins=next(decoder.disasm(raw[at:at+15],at,count=1),None)
                    if ins is None:
                        calls=[];break # This public is not established executable code.
                    code=bytes(ins.bytes)
                    if len(code)==5 and code[0]==0x9a and at+1 in fixes:calls.append(at+5)
                    if ins.group(CS_GRP_RET) or ins.group(CS_GRP_IRET):continue
                    if ins.group(CS_GRP_JUMP):
                        if ins.operands and ins.operands[0].type==X86_OP_IMM:pending.append(ins.operands[0].imm)
                        if ins.mnemonic in ('jmp','ljmp'):continue
                    pending.append(at+ins.size)
                calls=sorted(calls)
                for index,offset in enumerate(calls):
                    pc=base+addresses[name]+offset-start
                    result.setdefault(pc,[]).append(dict(name=name,index=index,count=len(calls),unit=module['key'],
                        object_sha256=module['object']['sha256'],function_sha256=None,
                        evidence='own OMF public + reachable instruction CFG + TickCount pointer32 fixup + MAP public'))
    return result,addresses


def full_tape(directory,exe,out,scenario_sha,script_sha,steps):
    from capstone import Cs,CS_ARCH_X86,CS_MODE_16
    manifest=json.loads((directory/'boundary-manifest.json').read_text())
    oracle=json.loads((ROOT/'layout/oracle.lock.json').read_text())['inputs']['SIMANT.EXE']['sha256']
    target=manifest.get('target')
    if (target not in ('original','canonical_dos') or target=='original' and manifest['executable_sha256']!=oracle or
        manifest['scenario_sha256']!=scenario_sha or manifest['input_script_sha256']!=script_sha):
        raise ValueError('Replay requires matching reference executable/scenario/script identities')
    trace=directory/'observer.txt'
    if sha(trace)!=manifest['compact_observer']['trace_sha256']:raise ValueError('Compact trace hash differs')
    if not {'K','M'}.issubset({p[0] for p in manifest['compact_observer']['points']}):
        raise ValueError('Full input replay requires actual original IRQ/callback delivery capture')
    memory_path=directory/'exec-simstep.1.bin'
    if sha(memory_path)!=manifest['snapshots'][memory_path.name]:raise ValueError('Original binding memory hash differs')
    memory=memory_path.read_bytes();base=manifest['runtime_base']
    symbols=json.loads((ROOT/'layout/symbols.json').read_text())['code']
    if target=='canonical_dos':
        dos_calls,canonical_addresses=canonical_clock_calls(directory,manifest)
    functions=sorted((base+r['seg']*16+r['off'],n) for n,r in symbols.items() if not r.get('alias_of'))
    addresses={n:a for a,n in functions}
    records,inputs,boundaries=parse_trace(trace,steps,require_quiet=True)
    decoder=Cs(CS_ARCH_X86,CS_MODE_16)
    # Overlay areas overlap. Bind against each immutable original section,
    # rather than assigning a runtime PC to the nearest unrelated symbol.
    sys.path.insert(0,str(ROOT/'tools'))
    import exe as original_exe
    import functions as original_functions
    image=original_exe.load()
    if target=='original':dos_calls={}
    function_rows=original_functions.by_address()
    for name,symbol in symbols.items():
        if target!='original':break
        if symbol.get('alias_of'):continue
        f=function_rows.get((symbol.get('unit','root'),symbol['seg'],symbol['off']))
        if f is None:continue
        origin,data=image.unit_bytes(f['unit']);at=f['seg']*16+f['off']
        raw_function=data[at-origin:at-origin+f['size']]
        calls=[]
        for ins in decoder.disasm(raw_function,at):
            raw=bytes(ins.bytes)
            if len(raw)==5 and raw[0]==0x9a and int.from_bytes(raw[1:3],'little')+16*int.from_bytes(raw[3:5],'little')==addresses['TickCount']-base:
                calls.append(base+ins.address+ins.size)
        for index,pc in enumerate(calls):dos_calls.setdefault(pc,[]).append(dict(name=name,index=index,count=len(calls),unit=f['unit'],function_sha256=hashlib.sha256(raw_function).hexdigest()))
    texts={};bindings={}
    def native_calls(name,target):
        if name not in texts:texts[name]=subprocess.check_output([OBJDUMP,'-d','--disassemble='+name,str(exe)],text=True)
        return [int(a,16)+len(raw.split()) for a,raw in re.findall(
            r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2} )+)\s*call\s+[^\n]*<'+target+'>',texts[name],re.M)]
    native_calls('portable_test_clock_read','TickCount')
    anchor=int(re.search(r'([0-9a-f]+) <portable_test_clock_read>:',texts['portable_test_clock_read'])[1],16)
    for kind,pc,_,_ in records:
        if (kind,pc) in bindings:continue
        if kind=='C':bindings[kind,pc]=dict(native_delta=0,kind='C',name='IRQ countdown reads');continue
        if kind=='V':
            calls=native_calls('portable_m1b73_event_enqueue_registers','timer_bios_tick_count')
            if len(calls)!=1:raise ValueError('Native event stamp binding differs')
            bindings[kind,pc]=dict(native_delta=calls[0]-anchor,kind='B',name='input_enqueue_event:BIOS timestamp');continue
        candidates=dos_calls.get(pc,[])
        if kind!='T' or len(candidates)!=1:raise ValueError('DOS return PC is ambiguous/unbound: '+str((kind,hex(pc),candidates)))
        candidate=candidates[0];name=candidate['name']
        native=native_calls('dos_game_main' if name=='main' else name,'TickCount')
        if len(native)!=candidate['count']:raise ValueError('Clock call-site count differs: '+str((name,candidate['count'],len(native))))
        bindings[kind,pc]=dict(native_delta=native[candidate['index']]-anchor,kind=kind,call_index=candidate['index'],dos_return_pc=pc,**candidate)
    clock_path=out/'full-clock-inputs.txt'
    for (kind,pc),binding in bindings.items():
        binding['total_reads']=sum(n for k,p,v,n in records if (k,p)==(kind,pc))
    clock_path.write_text('# Exact original primitive reads; kind native-PC-delta value repeat-count\n'+''.join(
        f'{bindings[k,p]["kind"]} {bindings[k,p]["native_delta"]} {k} {p} {v} {n}\n' for k,p,v,n in records)+'X\n')
    order_path=None
    contract=manifest['compact_observer'].get('order_contract')
    if contract:
        source=directory/'observer.txt.order'
        if contract!='service-samples-v5' or sha(source)!=manifest['compact_observer']['order_sha256']:
            raise ValueError('Unbound global service sequence')
        sites={int(v[1]):(v[2],int(v[3],16)) for line in trace.read_text().splitlines()
               if (v:=line.split()) and v[0]=='O'}
        indices={key:i for i,key in enumerate(bindings)}
        if len(bindings)>246:raise ValueError('Clock site IDs overlap reserved service IDs')
        mapping=bytearray(range(256))
        for i,key in sites.items():
            if key in indices:mapping[i]=indices[key]
        order_path=out/'service-order.bin'
        boundary=boundaries[-1]
        limit=boundary['clock_reads']+boundary['pump']+boundary['queries']+2*boundary['step']-boundary['phase']
        order=source.read_bytes()[:limit]
        if len(order)!=limit:raise ValueError('Incomplete global service sequence')
        if any(i<246 and (i not in sites or sites[i] not in indices) for i in set(order)):
            raise ValueError('Global sequence contains an unbound clock site')
        order_path.write_bytes(order.translate(bytes(mapping)))
    receipt=dict(schema='simant-original-full-inputs-v1',original_manifest_sha256=sha(directory/'boundary-manifest.json'),
        trace_sha256=sha(trace),native_executable_sha256=sha(exe),scenario_sha256=scenario_sha,input_script_sha256=script_sha,
        clock_tape_sha256=sha(clock_path),service_order=str(order_path) if order_path else None,steps=steps,
        clock_reads=sum(r[3] for r in records),clock_runs=len(records),inputs=inputs,boundaries=boundaries,
        bindings=[dict(original_kind=k,original_pc=p,**v) for (k,p),v in bindings.items()],native_disassembly=texts,
        scope='Captured per-site/read-ordinal clock values and exact chronological service order. Actual IRQs are admitted at their recorded service positions; state/clock values are never selected from native results.')
    (out/'full-inputs.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return clock_path,None,receipt
