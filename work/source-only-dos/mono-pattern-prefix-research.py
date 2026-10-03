"""Oracle-dependent static/reference and whole-S15 declaration research.

Keep this research entrypoint separate from the SOURCE_ONLY runtime probe. It
reads the original only for disassembly/address comparison and invokes
promote.py --verify-only once for the full-module source control.
"""
from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path

def find_root():
    for p in Path(__file__).resolve().parents:
        if (p/'layout'/'manifest.json').is_file(): return p
    raise RuntimeError('cannot locate repo root')
ROOT=find_root()
OUT=ROOT/'build/workers/dos_mono_pattern_prefix_research'
OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'tools'))
import compiler, exe, functions
from omf import OmfReader
try:
    from capstone import Cs, CS_ARCH_X86, CS_MODE_16, CS_OP_IMM, CS_OP_MEM, CS_GRP_CALL, CS_GRP_JUMP
    from capstone.x86_const import X86_REG_INVALID
except ImportError:
    sys.path.insert(0,'C:/tools/capstone-5.0.3')
    from capstone import Cs, CS_ARCH_X86, CS_MODE_16, CS_OP_IMM, CS_OP_MEM, CS_GRP_CALL, CS_GRP_JUMP
    from capstone.x86_const import X86_REG_INVALID

MD=Cs(CS_ARCH_X86,CS_MODE_16); MD.detail=True
TARGET=(0x8EC0,0x8ED8)
SOURCE=ROOT/'src/S15/m384C.c'
DECL='extern unsigned char near g_8EC0[];'
TYPED='unsigned char near g_8EC0[24];'
FLAGS=['/AL','/Os','/Og','/Oe','/Zi']

def sha(raw): return hashlib.sha256(raw).hexdigest()
def pin(path):
    raw=Path(path).read_bytes()
    return {'path':str(Path(path).resolve().relative_to(ROOT)).replace('\\','/'),
            'sha256':sha(raw),'size':len(raw)}

def static_reference_scan():
    image=exe.load(); units={u:image.unit_bytes(u) for u in image.units()}
    direct=[]; immed=[]; decoded=0; rows=functions.table()['functions']
    for row in rows:
        unit=row['unit']; base,data=units[unit]
        linear=row['seg']*16+row['off']; start=linear-base
        if start<0 or start+row['size']>len(data): continue
        name=functions.name_of(unit,row['seg'],row['off'])
        for ins in MD.disasm(data[start:start+row['size']],linear):
            decoded+=1
            for op in ins.operands:
                if op.type==CS_OP_MEM and op.mem.base==X86_REG_INVALID and op.mem.index==X86_REG_INVALID:
                    value=op.mem.disp&0xffff
                    if TARGET[0]<=value<TARGET[1]:
                        direct.append({'unit':unit,'function':name,'instruction_offset':f'{ins.address-linear:04X}',
                          'mnemonic':ins.mnemonic,'operands':ins.op_str,'offset16':f'{value:04X}'})
                elif op.type==CS_OP_IMM and not (ins.group(CS_GRP_CALL) or ins.group(CS_GRP_JUMP)):
                    value=op.imm&0xffff
                    if TARGET[0]<=value<TARGET[1]:
                        immed.append({'unit':unit,'function':name,'instruction_offset':f'{ins.address-linear:04X}',
                          'mnemonic':ins.mnemonic,'operands':ins.op_str,'immediate16':f'{value:04X}'})
    symbols=json.loads((ROOT/'layout/symbols.json').read_text(encoding='utf-8'))['data']
    registered=[{'name':n,'seg':r.get('seg'),'off':r.get('off'),'alias_of':r.get('alias_of')}
        for n,r in symbols.items() if r.get('seg')==0x55b3 and TARGET[0]<=r.get('off',-1)<TARGET[1]]
    expected_immediates=[('S15','LoadMonoPats','8EC0')]
    actual_immediates=[(r['unit'],r['function'],r['immediate16']) for r in immed]
    if len(rows)!=1730 or decoded!=123267 or direct or actual_immediates!=expected_immediates:
        raise RuntimeError(f'original reference scan differs from reviewed 8EC0 evidence: functions={len(rows)} decoded={decoded} direct={direct} immediates={actual_immediates}')
    if registered!=[{'name':'g_8EC0','seg':0x55b3,'off':0x8ec0,'alias_of':None}]:
        raise RuntimeError('registered symbol interior/base views changed in the candidate region')
    return {'schema':'mono-pattern-prefix-original-reference-scan-v1','original_sha256':image.sha256,
      'functions_scanned':len(rows),'decoded_instructions':decoded,'target':'DGROUP 55B3:8EC0-8ED7',
      'absolute_memory_operands_into_target':direct,'noncontrol_immediate_candidates':immed,
      'registered_symbol_rows_in_target':registered,'inputs':[pin(ROOT/'layout/functions.json'),
       pin(ROOT/'layout/symbols.json'),pin(ROOT/'src/S15/m384C.c'),pin(ROOT/'src/S01/m328E.asm')]}

def nondebug_segments(obj):
    return {name:raw for name,raw in obj.segments.items()
            if name.upper() not in ('DEBSYM','DEBTYP','$$SYMBOLS','$$TYPES')}

def whole_module_control():
    original=SOURCE.read_text(encoding='latin1')
    if original.count(DECL)!=1: raise RuntimeError('expected one S15 extern declaration')
    candidate=original.replace(DECL,TYPED,1)
    control_obj=compiler.compile_c(original,'msc600ax',FLAGS,basename='M384C')
    candidate_obj=compiler.compile_c(candidate,'msc600ax',FLAGS,basename='M384C')
    if not control_obj.ok or not candidate_obj.ok:
        raise RuntimeError('S15 whole-module compile failed')
    reader=OmfReader(communals=True)
    control=reader.read(control_obj.obj,'M384C-control')
    typed=reader.read(candidate_obj.obj,'M384C-typed24')
    control_load=nondebug_segments(control); typed_load=nondebug_segments(typed)
    omit='_g_8EC0'
    ext_c=[(n,s) for n,s in zip(control.externals,control.external_scopes) if n!=omit]
    ext_t=[(n,s) for n,s in zip(typed.externals,typed.external_scopes) if n!=omit]
    comms=typed.communals
    comparisons={
      'loadable_segment_payloads_identical':control_load==typed_load,
      'loadable_segment_lengths_identical':{k:len(v) for k,v in control_load.items()}=={k:len(v) for k,v in typed_load.items()},
      'groups_identical':control.groups==typed.groups,
      'publics_identical':sorted((p['name'],p['segment'],p['offset']) for p in control.publics)==sorted((p['name'],p['segment'],p['offset']) for p in typed.publics),
      'ordered_linker_fixups_identical':control.linker_fixups==typed.linker_fixups,
      'legacy_fixups_identical':control.fixups==typed.fixups,
      'unrelated_external_scopes_identical':ext_c==ext_t,
      'exact_near24_communal_added':comms==[{'name':'_g_8EC0','kind':'near','type_index':comms[0]['type_index'] if comms else None,'length':24}],
      'control_has_no_g8ec0_communal':not any(c['name']==omit for c in control.communals),
    }
    if not all(comparisons.values()):
        raise RuntimeError('whole-module S15 control differs beyond the measured g_8EC0 COMM')
    typed_path=OUT/'M384C-typed24.c'; typed_path.write_text(candidate,encoding='latin1',newline='')
    command=[sys.executable,str(ROOT/'tools/promote.py'),str(typed_path),'--module','S15:384C','--verify-only']
    result=subprocess.run(command,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=300)
    promote_text=result.stdout
    (OUT/'promote-verify.log').write_text(promote_text,encoding='utf-8')
    if result.returncode:
        raise RuntimeError('promote.py --verify-only failed; see research scratch log')
    return {'source_pin':pin(SOURCE),'candidate_source_sha256':sha(candidate.encode('latin1')),
      'compiler_profile':'msc600ax','flags':FLAGS,'control_object_sha256':sha(control_obj.obj),
      'candidate_object_sha256':sha(candidate_obj.obj),'control_object_bytes':len(control_obj.obj),
      'candidate_object_bytes':len(candidate_obj.obj),'comparisons':comparisons,
      'control_communals':control.communals,'candidate_communals':typed.communals,
      'compiler_nondebug_segment_lengths':{k:len(v) for k,v in typed_load.items()},
      'promote_verify_only':{'returncode':result.returncode,'command':command[1:],
        'output_tail':promote_text[-5000:],'log_pin':pin(OUT/'promote-verify.log')}}

def main():
    refs=static_reference_scan()
    module=whole_module_control()
    report={'schema':'mono-pattern-prefix-static-research-v1','module':'S15:384C',
      'original_reference_scan':refs,'whole_module_control':module,
      'scope':'Research only: the original is used only by disassembly/address comparison. The full S15 candidate is independently compiled, and promote.py is invoked once with --verify-only. Runtime contract is generated by the separate guarded SOURCE_ONLY probe.',
      'all_checks_pass':True}
    out=OUT/'mono-pattern-prefix-research-report.json'
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('all_checks_pass',report['all_checks_pass'])
    print('report',out)
    return 0

if __name__=='__main__': raise SystemExit(main())
