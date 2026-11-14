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

def parse_trace(path,steps):
    records=[];inputs=[];pending=[];boundaries=[];reads=0;saw_delivery=False;site_reads={}
    for line in path.read_text().splitlines():
        p=line.split()
        if not p or p[0]=='#':continue
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
                expected={'enter':0x1c,'kp_5':0x4c,'space':0x39,'f2':0x3c,'down':0x50,'a':0x1e,'b':0x30,'lshift':0x2a,'4':0x05}.get(op[1])
                if expected is None or scan&127!=expected:raise InputCoverageError(item['step'],'Missing or unbound scan delivery: '+str((op,scan)))
            else:
                mask=ax&127
                expected=1 if op[0]=='mouse_move' else (2 if op[2]=='down' else 4)<<(2*int(op[1]))
                if not mask&expected:continue
            pending.remove(item)
            item.update(scheduled_milliseconds=item['milliseconds'],milliseconds=float(p[2]),pump=int(p[3]),
                clock_reads=int(p[6]),step=int(p[4]),phase=int(p[5]),delivery_kind=kind,
                registers=dict(ax=ax,bx=bx,cx=cx,dx=dx),position=dict(site_reads),anchor=p[11] if len(p)>11 else None)
            inputs.append(item)
        elif p[0]=='S':
            if int(p[5])!=reads:raise ValueError('Boundary read ordinal differs from complete preceding streams')
            boundaries.append(dict(milliseconds=float(p[1]),pump=int(p[2]),step=int(p[3]),phase=int(p[4]),inputs=len(inputs) if saw_delivery else len(pending),clock_runs=len(records),clock_reads=int(p[5]),clock_hash=int(p[6])))
            boundaries[-1]['site_reads']=dict(site_reads)
            if int(p[3])==steps:break
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
    window_pc=base+(canonical_addresses['f_1B28_0069'] if target=='canonical_dos' else symbols['f_1B28_0069']['seg']*16+symbols['f_1B28_0069']['off'])
    pump_points=[('P',p[1]) for p in manifest['compact_observer']['points'] if p[0] in ('P','W')]
    pump_source='both' if len(pump_points)==2 and ('P',window_pc) in pump_points else 'window' if ('P',window_pc) in pump_points else 'queue'
    functions=sorted((base+r['seg']*16+r['off'],n) for n,r in symbols.items() if not r.get('alias_of'))
    addresses={n:a for a,n in functions}
    records,inputs,boundaries=parse_trace(trace,steps)
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
    receipt=dict(schema='simant-original-full-inputs-v1',original_manifest_sha256=sha(directory/'boundary-manifest.json'),
        trace_sha256=sha(trace),native_executable_sha256=sha(exe),scenario_sha256=scenario_sha,input_script_sha256=script_sha,
        clock_tape_sha256=sha(clock_path),steps=steps,pump_source=pump_source,
        clock_reads=sum(r[3] for r in records),clock_runs=len(records),inputs=inputs,boundaries=boundaries,
        bindings=[dict(original_kind=k,original_pc=p,**v) for (k,p),v in bindings.items()],native_disassembly=texts,
        scope='Original per-site/read-ordinal values through the requested entry. Input positions include step, inside/outside phase, completed-site ordinals and service boundary; pump counts/order digest are diagnostics.')
    (out/'full-inputs.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return clock_path,None,receipt
