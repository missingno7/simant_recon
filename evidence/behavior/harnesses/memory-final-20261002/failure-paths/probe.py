from __future__ import annotations
import hashlib, json, pathlib, sys
ROOT = next(p for p in pathlib.Path(__file__).resolve().parents if (p / 'layout/manifest.json').exists())
SNAP = ROOT / 'build/workers/behavior_memory/final-pinned-20261002/snapshot'
sys.path.insert(0, str(SNAP / 'tools'))
import behavior
import behavior_suites.memory as memory
from behavior_suites.memory import function_body

SOURCE = SNAP / 'build/workers/behavior_memory/final-run/source/ralloc-module.c'
PUNT_LINEAR = behavior.symbol_address('Punt')

class PuntBoundaryMachine(behavior.Machine):
    """Research-only stop at actual Punt entry; never returns or fakes completion."""
    def __init__(self, pair, candidate=False):
        super().__init__(pair, candidate)
        self.punt_boundary = None
    def _on_block(self, cpu, address, size, userdata):
        if address == PUNT_LINEAR:
            sp = self.reg('sp'); ss = self.reg('ss'); stack = ss * 16 + sp
            ret_off, ret_seg, fmt_off, fmt_seg = __import__('struct').unpack('<4H', self.read(stack, 8))
            fmt_linear = fmt_seg * 16 + fmt_off
            raw = bytearray()
            for i in range(256):
                b = self.read(fmt_linear + i, 1)[0]
                if b == 0: break
                raw.append(b)
            changed = []
            for at in sorted(self.written):
                before = self.effect_initial.get(at, self.read(at,1)[0])
                after = self.read(at,1)[0]
                if before != after:
                    changed.append({'address':at,'before':before,'at_punt':after})
            self.punt_boundary = {
                'kind':'actual_original_Punt_entry_nonreturn_boundary',
                'entry_linear':address,'entry_far':{'seg':self.reg('cs'),'off':self.reg('ip')},
                'registers':{n:self.reg(n) for n in ('ax','bx','cx','dx','si','di','bp','sp','ss','ds','es')},
                'stack_frame':{'return_far':{'off':ret_off,'seg':ret_seg},'format_far':{'off':fmt_off,'seg':fmt_seg}},
                'format_string_far_linear':fmt_linear,
                'format_string_utf8_projection':bytes(raw).decode('latin1'),
                'format_string_raw_hex':bytes(raw).hex(),
                'nonstack_bytes_changed_before_punt':changed,
                'written_addresses_before_punt':sorted(self.written),
                'raw_trace_before_punt':self.raw_trace.copy(),
                'raw_effect_trace_before_punt':self.raw_effect_trace.copy(),
                'basic_blocks_before_punt':self.blocks,
                'observed_ranges':{r.name:self.read(r.address,r.size).hex() for r in self.case.observe},
                'completed':False,'return_value':None,'caller_abi_check_performed':False,
            }
            cpu.emu_stop()
            return
        super()._on_block(cpu,address,size,userdata)

def execute_until_boundary(pair, case):
    pair.original_machine = PuntBoundaryMachine(pair,False)
    pair.candidate_machine = PuntBoundaryMachine(pair,True)
    out=[]
    for lane,machine in [('original',pair.original_machine),('candidate',pair.candidate_machine)]:
        try:
            result=machine.run(case)
            out.append({'lane':lane,'outcome':'RETURNED','return':result['return'],'punctuation':machine.punt_boundary})
        except behavior.ExecutionError as e:
            out.append({'lane':lane,'outcome':'PUNT_BOUNDARY' if machine.punt_boundary else 'EXECUTION_ERROR',
                        'error':str(e),'punt':machine.punt_boundary})
    return out

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    report={'schema':'ralloc-memory-failure-path-diagnostic-v2','status':'SUPPLEMENTAL_DIAGNOSTIC_ONLY',
      'fixture_contract':'tools/behavior_suites/memory.py heap_case: valid A100 heap, A000 master table, heap/master disjoint from reserved DOS stack; no fake callbacks or returned Punt values',
      'dependencies':{'source':str(SOURCE.relative_to(ROOT)),'source_sha256':digest(SOURCE),
        'runner':str((SNAP/'tools/behavior.py').relative_to(ROOT)),'runner_sha256':digest(SNAP/'tools/behavior.py'),
        'suite':str((SNAP/'tools/behavior_suites/memory.py').relative_to(ROOT)),'suite_sha256':digest(SNAP/'tools/behavior_suites/memory.py'),
        'oracle_exe_sha256':behavior.exe.load().sha256,'manifest_sha256':digest(SNAP/'layout/manifest.json'),
        'unicorn_version':behavior.uc.__version__,
        'canonical_archive_paths':{'source':'evidence/behavior/harnesses/memory-final-20261002/runs/candidate/ralloc-module.c','runner':'evidence/behavior/harnesses/memory-final-20261002/tools/behavior.py','suite':'evidence/behavior/harnesses/memory-final-20261002/tools/behavior_suites/memory.py'}},'probes':[]}
    # Successful/rejected ordinary return controls, all actual original-vs-C executions.
    resize_ok=memory.heap_case('success/09cc-shrink-split',[(96,1,{'size':1400}),(64,0x80)],args=[memory.MASTER_FIRST,memory.HANDLE_SEG,40,3],handles=[0],contract='valid handle slot; shrink firm block and split free tail')
    resize_fail=memory.heap_case('failure/09cc-grow-too-large',[(20,1,{'size':288}),(8,0x80),(32,0)],args=[memory.MASTER_FIRST,memory.HANDLE_SEG,40,1],handles=[0],contract='valid handle slot; adjacent free extent is too small to grow')
    controls=[('f_171C_09CC',resize_ok),('f_171C_09CC',resize_fail),
              ('f_171C_0FBC',memory.directed()['f_171C_0FBC'][0])]
    for target,case in controls:
        pair=behavior.PreparedPair(target,source=SOURCE)
        comp=pair.compare(case)
        report['probes'].append({'kind':'returned_differential_control','target':target,'case':case.label,
          'oracle_return':comp.original['return'],'candidate_return':comp.candidate['return'],
          'equal':comp.equal,'diff':comp.diff,'pair_identity':pair.identity})
    # Reclaim false is a real original helper call on both sides, not a modeled helper.
    full=memory.heap_case('failure/full-firm-no-reclaim',[(128,1,{'size':2016,'age':1})],args=[0],result='s16',handles=[0],contract='valid full arena; no free block and no reclaimable soft handle')
    pair=behavior.PreparedPair('f_171C_0FBC',source=SOURCE,sequence_targets=['f_171C_0FBC'])
    comp=next(pair.compare_sequence([('f_171C_0BE2',full)]))
    report['probes'].append({'kind':'original_helper_return_both_lanes','target':'f_171C_0BE2','case':full.label,
      'oracle_return':comp.original['return'],'candidate_return':comp.candidate['return'],'equal':comp.equal,
      'execution_mode':'actual same-module original helper on both lanes','pair_identity':pair.identity})
    reclaimable=memory.heap_case('success/reclaim-oldest-soft',[(16,3,{'size':224,'age':1}),(112,1,{'size':1760,'age':2})],args=[0],result='s16',handles=[0,1],contract='valid full arena; reclaim oldest unlocked soft handle')
    pair=behavior.PreparedPair('f_171C_0FBC',source=SOURCE,sequence_targets=['f_171C_0FBC'])
    comp=next(pair.compare_sequence([('f_171C_0BE2',reclaimable)]))
    report['probes'].append({'kind':'original_helper_success_both_lanes','target':'f_171C_0BE2','case':reclaimable.label,
      'oracle_return':comp.original['return'],'candidate_return':comp.candidate['return'],'equal':comp.equal,
      'execution_mode':'actual same-module original helper on both lanes','fixture':reclaimable.metadata,'args':reclaimable.args,'pair_identity':pair.identity})
    # Force the valid full-heap no-space path. Stop exactly at actual Punt entry in each lane.
    exhausted=memory.heap_case('failure/f0fbc-full-no-reclaim',[(128,1,{'size':2016,'age':1})],args=[1,1],result='farptr',handles=[0],contract='valid full arena; no free block and no reclaimable soft handle')
    pair=behavior.PreparedPair('f_171C_0FBC',source=SOURCE,sequence_targets=['f_171C_0FBC'])
    outcomes=execute_until_boundary(pair,exhausted)
    report['probes'].append({'kind':'terminal_punt_boundary_pair','target':'f_171C_0FBC','case':exhausted.label,
      'fixture':exhausted.metadata,'args':exhausted.args,'lanes':outcomes,'pair_identity':pair.identity,
      'boundary_comparison':{'same_punt_entry':outcomes[0].get('punt',{}).get('entry_linear')==outcomes[1].get('punt',{}).get('entry_linear'),'same_message_bytes':outcomes[0].get('punt',{}).get('format_string_raw_hex')==outcomes[1].get('punt',{}).get('format_string_raw_hex'),'same_observed_ranges':outcomes[0].get('punt',{}).get('observed_ranges')==outcomes[1].get('punt',{}).get('observed_ranges'),'same_nonstack_pre_punt_changes':outcomes[0].get('punt',{}).get('nonstack_bytes_changed_before_punt')==outcomes[1].get('punt',{}).get('nonstack_bytes_changed_before_punt')},
      'interpretation':'Punt invocation/nonreturn boundary; no return comparison, completion, or ABI forgery'})
    # Bounded negative: omit only the 0FBC Punt caller in candidate; original must trap, mutant must return.
    text=SOURCE.read_text(encoding='latin1')
    start,end,body=function_body(text,'f_171C_0FBC')
    if body.count('Punt(buffer);') != 1: raise RuntimeError('expected unique 0FBC Punt caller anchor')
    mutant_text=text[:start]+body.replace('Punt(buffer);','return 0L;',1)+text[end:]
    mutant_path=SNAP/'build/workers/behavior_memory/failure-path-probes/negative-omit-punt.c'
    mutant_path.parent.mkdir(parents=True,exist_ok=True)
    mutant_path.write_text(mutant_text,encoding='latin1')
    pair=behavior.PreparedPair('f_171C_0FBC',source=mutant_path,sequence_targets=['f_171C_0FBC'])
    outcomes=execute_until_boundary(pair,exhausted)
    report['probes'].append({'kind':'negative_omit_punt_caller','target':'f_171C_0FBC','case':exhausted.label,
      'mutant_source':str(mutant_path.relative_to(ROOT)),'mutant_source_sha256':digest(mutant_path),
      'lanes':outcomes,'pair_identity':pair.identity,'sensitivity_detected':outcomes[0]['outcome']=='PUNT_BOUNDARY' and outcomes[1]['outcome']=='RETURNED',
      'interpretation':'diagnostic only; omission mutant must not be treated as a recovered implementation'})
    path=pathlib.Path(__file__).resolve().parent/'report-v2.json'
    path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    report['producer_script_sha256']=digest(pathlib.Path(__file__).resolve())
    path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(path)
    for p in report['probes']:
      print(p['kind'],p.get('case'),[(x['lane'],x['outcome'],x.get('return'),x.get('punt',{}).get('format_string_utf8_projection') if x.get('punt') else None) for x in p.get('lanes',[])])

if __name__=='__main__': main()
