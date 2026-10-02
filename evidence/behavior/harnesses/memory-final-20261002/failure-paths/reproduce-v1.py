"""Fresh-bootstrap reproducibility producer for the memory failure-path supplement.

All code imports only after archive inputs and the original DOS asset are hash-checked.
The only generated files are beneath build/workers/behavior_memory/repro-v1/.
"""
from __future__ import annotations
import argparse, hashlib, json, pathlib, shutil, sys, struct, datetime

HERE = pathlib.Path(__file__).resolve()
REPO = next(p for p in HERE.parents if (p / 'layout/manifest.json').is_file())
ARCHIVE = REPO / 'evidence/behavior/harnesses/memory-final-20261002'
ASSET = REPO / 'assets/SIMANT.EXE'
BOOT = REPO / 'build/workers/behavior_memory/repro-v1/bootstrap-v4'
DEFAULT_OUT = REPO / 'build/workers/behavior_memory/repro-v1/runs'
EXPECTED = {
    'archive_index': 'e8b636e2557f058a0f07b5ddede033db3d610dd3bc2258f72291d1b49df0b0ee',
    'runner': '2c0799048057f59eae61a48be4d695278635594484adf0c70bf46c51b4e0c799',
    'suite': 'dda4f6dd78778f2a98b811d1971fc5923300d57b2a2fa35221a213d208eb321d',
    'source': '3d24904696b29c36b118479ecc50dd80b8d173f58a632a339df9391d08ea085b',
    'oracle': 'aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11',
    'manifest': '025a0a9255d910cae4b122ab5a3f3fb40888bb456d7fe42158db7c9e622fcf50',
    'functions': '6089a06e18fbe8f0960392cfe30357f7c19c886f38f10f7f115c72d127a756e7',
    'symbols': '0f5dd5b0a211945a97782cfccdb9bb31b0dfd07fcde5df4d4f9486b487eb0125',
    'oracle_lock': '2c6d9e98c688621ad49a08c78d0e0968f4076b036be56ec0738217b533ccde13',
    'toolchain': 'c0bb71cd8b1f4a1a1f91299bd3b6148aa67b7a1d12c3c3946a229272593eb274',
    'unicorn_tree': '2b2ec2f8c0b83d5d568ebb32789379d503d4cfb51fe05591597b5daffe4ba827',
}

def sha(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def sha_path(p: pathlib.Path) -> str: return sha(p.read_bytes())

def verify_archive_inputs():
    dep_root=REPO/'build/behavior/deps'
    dep_files=sorted([p for d in [dep_root/'unicorn',dep_root/'unicorn-2.1.4.dist-info'] if d.exists() for p in d.rglob('*') if p.is_file()])
    dh=hashlib.sha256()
    for p in dep_files: dh.update(p.relative_to(dep_root).as_posix().encode()+b'\0'+sha_path(p).encode()+b'\n')
    if not dep_files or dh.hexdigest()!=EXPECTED['unicorn_tree']: raise RuntimeError('pinned Unicorn 2.1.4 runtime tree hash mismatch/missing')
    index_path=ARCHIVE/'archive-index.json'
    if sha_path(index_path)!=EXPECTED['archive_index']: raise RuntimeError('archive-index hash mismatch')
    index=json.loads(index_path.read_text(encoding='utf-8'))
    assert index['runner_sha256']==EXPECTED['runner'] and index['suite_sha256']==EXPECTED['suite']
    expected_paths={
      'tools/behavior.py':EXPECTED['runner'],
      'tools/behavior_suites/memory.py':EXPECTED['suite'],
      'runs/candidate/ralloc-module.c':EXPECTED['source'],
      'layout/toolchain.json':EXPECTED['toolchain'],
    }
    for rel,digest in expected_paths.items():
        p=ARCHIVE/rel
        if not p.is_file() or sha_path(p)!=digest: raise RuntimeError(f'archived dependency hash mismatch: {rel}')
    retained={r['path']:r['sha256'] for r in index.get('retained_files',[])}
    for rel,digest in expected_paths.items():
        if retained.get(rel)!=digest: raise RuntimeError(f'archive index does not pin {rel}')
    for rel in index['components']:
        pinned=retained.get(rel)
        path=ARCHIVE/rel
        if not pinned or not path.is_file() or sha_path(path)!=pinned:
            raise RuntimeError(f'archived runner component failed pre-import pin: {rel}')
    for key,rel in [('manifest','layout/manifest.json'),('functions','layout/functions.json'),('symbols','layout/symbols.json'),('oracle_lock','layout/oracle.lock.json')]:
        if sha_path(REPO/rel)!=EXPECTED[key]: raise RuntimeError(f'root read-only input hash mismatch: {rel}')
    if sha_path(ASSET)!=EXPECTED['oracle']: raise RuntimeError('original DOS asset hash mismatch')
    return index

def bootstrap(index):
    # Bootstrap is write-once. Existing outputs are checked, never repaired in place.
    if BOOT.exists():
        stamp=BOOT/'bootstrap-pins.json'
        if not stamp.is_file(): raise RuntimeError(f'unrecognized bootstrap already exists: {BOOT}')
        doc=json.loads(stamp.read_text())
        if doc.get('pins') != EXPECTED: raise RuntimeError('existing bootstrap pins differ')
        for rel,digest in doc['archived_files'].items():
            if sha_path(BOOT/rel)!=digest: raise RuntimeError(f'bootstrap file changed: {rel}')
        return doc
    BOOT.mkdir(parents=True)
    shutil.copytree(ARCHIVE/'tools',BOOT/'tools')
    layout=BOOT/'layout'; layout.mkdir()
    for rel in ['manifest.json','functions.json','symbols.json','oracle.lock.json']:
        shutil.copy2(REPO/'layout'/rel,layout/rel)
    shutil.copy2(ARCHIVE/'layout/toolchain.json',layout/'toolchain.json')
    source=BOOT/'work/ralloc-module.c'; source.parent.mkdir(parents=True)
    shutil.copy2(ARCHIVE/'runs/candidate/ralloc-module.c',source)
    (BOOT/'build/cc').mkdir(parents=True)
    archive_files={}
    for rel in ['tools/behavior.py','tools/behavior_suites/memory.py','tools/exe.py','tools/functions.py','tools/match.py','tools/modctx.py','tools/modules.py','tools/autosearch.py','tools/compiler.py','tools/omf.py','tools/symbols.py','tools/lockfile.py','tools/csrc.py','tools/srcrules.py','tools/variants.py','tools/behavior_ledger.py','layout/manifest.json','layout/functions.json','layout/symbols.json','layout/oracle.lock.json','layout/toolchain.json','work/ralloc-module.c']:
        archive_files[rel]=sha_path(BOOT/rel)
    doc={'schema':'memory-repro-bootstrap-v1','pins':EXPECTED,'archived_files':archive_files,
         'original_asset_path':str(ASSET),'original_asset_sha256':EXPECTED['oracle'],'archive_index_sha256':EXPECTED['archive_index'],'unicorn_tree_sha256':EXPECTED['unicorn_tree']}
    (BOOT/'bootstrap-pins.json').write_text(json.dumps(doc,indent=2)+'\n',encoding='utf-8')
    return doc

class PuntBoundaryMachine:
    """Installed dynamically after imports; stops at real Punt entry without return."""
    pass

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',type=pathlib.Path,default=None,help='optional new report path under build/workers/behavior_memory/repro-v1; must not already exist')
    args=ap.parse_args()
    index=verify_archive_inputs()
    pins=bootstrap(index)
    # The original EXE remains at its repository asset path; only the loader's path value is set.
    sys.path.insert(0,str(REPO/'build/behavior/deps'))
    sys.path.insert(0,str(BOOT/'tools'))
    import exe as exe_module
    exe_module.EXE_PATH=ASSET
    exe_module.ASSETS=ASSET.parent
    # `Executable.__init__` captured its default path at import time; redirect only that
    # default to the exact hash-verified original asset, without copying the binary.
    exe_module.Executable.__init__.__defaults__=(ASSET,True)
    import behavior
    import behavior_suites.memory as memory
    from behavior_suites.memory import function_body
    if behavior.exe.load().sha256!=EXPECTED['oracle']: raise RuntimeError('loaded oracle hash differs')
    source=BOOT/'work/ralloc-module.c'
    report={'schema':'ralloc-memory-failure-path-repro-v1','status':'SUPPLEMENTAL_DIAGNOSTIC_ONLY',
      'producer_sha256':sha_path(HERE),'bootstrap':str(BOOT.relative_to(REPO)),
      'bootstrap_pins_sha256':sha_path(BOOT/'bootstrap-pins.json'),'bootstrap_inputs':pins,
      'execution_dependencies':{'source_sha256':sha_path(source),'runner_sha256':sha_path(BOOT/'tools/behavior.py'),
        'suite_sha256':sha_path(BOOT/'tools/behavior_suites/memory.py'),'oracle_sha256':behavior.exe.load().sha256,
        'manifest_sha256':sha_path(BOOT/'layout/manifest.json'),'functions_sha256':sha_path(BOOT/'layout/functions.json'),
        'symbols_sha256':sha_path(BOOT/'layout/symbols.json'),'toolchain_sha256':sha_path(BOOT/'layout/toolchain.json'),
        'unicorn_version':behavior.uc.__version__,'unicorn_tree_sha256':EXPECTED['unicorn_tree'],'unicorn_runtime_path':str(REPO/'build/behavior/deps'),'original_asset_path':str(ASSET),'asset_handling':'uses hash-verified original path directly; no asset copy'},'probes':[]}
    resize_ok=memory.heap_case('success/09cc-shrink-split',[(96,1,{'size':1400}),(64,0x80)],args=[memory.MASTER_FIRST,memory.HANDLE_SEG,40,3],handles=[0],contract='valid handle slot; shrink firm block and split free tail')
    resize_fail=memory.heap_case('failure/09cc-grow-too-large',[(20,1,{'size':288}),(8,0x80),(32,0)],args=[memory.MASTER_FIRST,memory.HANDLE_SEG,40,1],handles=[0],contract='valid handle slot; adjacent free extent too small to grow')
    for target,case in [('f_171C_09CC',resize_ok),('f_171C_09CC',resize_fail),('f_171C_0FBC',memory.directed()['f_171C_0FBC'][0])]:
        pair=behavior.PreparedPair(target,source=source)
        c=pair.compare(case)
        report['probes'].append({'kind':'returned_differential_control','target':target,'case':case.label,'args':case.args,
          'fixture':case.metadata,'oracle_return':c.original['return'],'candidate_return':c.candidate['return'],'equal':c.equal,
          'diff':c.diff,'identity':pair.identity})
    def helper_case(label,rows,handles,expected):
        case=memory.heap_case(label,rows,args=[0],result='s16',handles=handles,contract=label)
        pair=behavior.PreparedPair('f_171C_0FBC',source=source,sequence_targets=['f_171C_0FBC'])
        c=next(pair.compare_sequence([('f_171C_0BE2',case)]))
        report['probes'].append({'kind':'original_helper_return_both_lanes','target':'f_171C_0BE2','case':label,
          'args':case.args,'fixture':case.metadata,'oracle_return':c.original['return'],'candidate_return':c.candidate['return'],
          'equal':c.equal,'expected_return':expected,'execution_mode':'actual same-module original helper on both sides','identity':pair.identity})
    helper_case('failure/full-firm-no-reclaim',[(128,1,{'size':2016,'age':1})],[0],0)
    helper_case('success/reclaim-oldest-soft',[(16,3,{'size':224,'age':1}),(112,1,{'size':1760,'age':2})],[0,1],1)
    # Research subclass preserves Machine failure semantics: emu_stop causes ExecutionError;
    # the caller captures it as a Punt boundary with no return/completion/ABI assertion.
    punt_linear=behavior.symbol_address('Punt')
    class TrapMachine(behavior.Machine):
        def __init__(self,pair,candidate=False):
            super().__init__(pair,candidate); self.punt_boundary=None
        def _on_block(self,cpu,address,size,userdata):
            if address!=punt_linear: return super()._on_block(cpu,address,size,userdata)
            sp=self.reg('sp'); ss=self.reg('ss'); stack=ss*16+sp
            ro,rs,fo,fs=struct.unpack('<4H',self.read(stack,8)); ptr=fs*16+fo; raw=bytearray()
            for i in range(256):
                b=self.read(ptr+i,1)[0]
                if not b: break
                raw.append(b)
            changes=[]
            for at in sorted(self.written):
                before=self.effect_initial.get(at,self.read(at,1)[0]); after=self.read(at,1)[0]
                if before!=after: changes.append({'address':at,'before':before,'at_punt':after})
            self.punt_boundary={'entry_linear':address,'entry_far':{'seg':self.reg('cs'),'off':self.reg('ip')},
              'registers':{n:self.reg(n) for n in ('ax','bx','cx','dx','si','di','bp','sp','ss','ds','es')},
              'stack_frame':{'return_far':{'off':ro,'seg':rs},'format_far':{'off':fo,'seg':fs}},
              'format_string_far_linear':ptr,'format_string_utf8_projection':bytes(raw).decode('latin1'),'format_string_raw_hex':bytes(raw).hex(),
              'nonstack_bytes_changed_before_punt':changes,'written_addresses_before_punt':sorted(self.written),
              'raw_trace_before_punt':self.raw_trace.copy(),'raw_effect_trace_before_punt':self.raw_effect_trace.copy(),
              'basic_blocks_before_punt':self.blocks,'observed_ranges':{r.name:self.read(r.address,r.size).hex() for r in self.case.observe},
              'completed':False,'return_value':None,'caller_abi_check_performed':False}
            cpu.emu_stop()
    exhausted=memory.heap_case('failure/f0fbc-full-no-reclaim',[(128,1,{'size':2016,'age':1})],args=[1,1],result='farptr',handles=[0],contract='valid full arena; no free block or reclaimable soft handle')
    def boundary_pair(pair,case):
        pair.original_machine=TrapMachine(pair,False); pair.candidate_machine=TrapMachine(pair,True); lanes=[]
        for lane,machine in [('original',pair.original_machine),('candidate',pair.candidate_machine)]:
            try:
                result=machine.run(case)
                lanes.append({'lane':lane,'outcome':'RETURNED','return':result['return'],'punt':machine.punt_boundary})
            except behavior.ExecutionError as e:
                lanes.append({'lane':lane,'outcome':'PUNT_BOUNDARY' if machine.punt_boundary else 'EXECUTION_ERROR','error':str(e),'punt':machine.punt_boundary})
        return lanes
    pair=behavior.PreparedPair('f_171C_0FBC',source=source,sequence_targets=['f_171C_0FBC'])
    lanes=boundary_pair(pair,exhausted)
    def same(field): return lanes[0]['punt'].get(field)==lanes[1]['punt'].get(field)
    report['probes'].append({'kind':'terminal_punt_boundary_pair','target':'f_171C_0FBC','case':exhausted.label,
      'args':exhausted.args,'fixture':exhausted.metadata,'lanes':lanes,'identity':pair.identity,
      'boundary_comparison':{'same_punt_entry':same('entry_linear'),'same_message_bytes':same('format_string_raw_hex'),
        'same_observed_ranges':same('observed_ranges'),'same_nonstack_pre_punt_changes':same('nonstack_bytes_changed_before_punt')},
      'interpretation':'Punt invocation/nonreturn boundary; no return comparison or fake completion/ABI result'})
    original=source.read_text(encoding='latin1'); start,end,body=function_body(original,'f_171C_0FBC')
    if body.count('Punt(buffer);')!=1: raise RuntimeError('expected unique 0FBC Punt caller anchor')
    mutant_text=original[:start]+body.replace('Punt(buffer);','return 0L;',1)+original[end:]
    mutant=BOOT/'work/negative-omit-punt.c'; mutant.write_text(mutant_text,encoding='latin1')
    pair=behavior.PreparedPair('f_171C_0FBC',source=mutant,sequence_targets=['f_171C_0FBC'])
    lanes=boundary_pair(pair,exhausted)
    report['probes'].append({'kind':'negative_omit_punt_caller','target':'f_171C_0FBC','case':exhausted.label,
      'mutant_source':'work/negative-omit-punt.c','mutant_source_sha256':sha_path(mutant),'lanes':lanes,'identity':pair.identity,
      'sensitivity_detected':lanes[0]['outcome']=='PUNT_BOUNDARY' and lanes[1]['outcome']=='RETURNED',
      'interpretation':'sensitivity mutant only; never treated as a recovered implementation'})
    out=args.output or (DEFAULT_OUT/f'report-{datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")}.json')
    out=out.resolve()
    out.relative_to((REPO/'build/workers/behavior_memory/repro-v1').resolve())
    if out.exists(): raise RuntimeError(f'refusing to overwrite report: {out}')
    out.parent.mkdir(parents=True,exist_ok=True)
    report['report_path']=str(out.relative_to(REPO))
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(out)
    for p in report['probes']:
        print(p['kind'],p.get('case'),p.get('oracle_return'),p.get('candidate_return'),p.get('equal'),p.get('sensitivity_detected'))

if __name__=='__main__': main()
