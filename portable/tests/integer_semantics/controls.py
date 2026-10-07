"""MSC 6.00A/AX object execution versus declaration-driven native lowering.

No original image is used. Historical objects are produced by the pinned real
compiler; relocation-free probe functions execute in a 16-bit Unicorn VM.
The negative lane uses the same declarations without expression lowering.
"""
from pathlib import Path
from collections import Counter
import argparse
import ctypes
import hashlib
import json
import struct
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'portable'),str(ROOT/'tools'),str(ROOT/'build/deps/unicorn')]
from canonical_native_abi import integer_frontend, scalar
import compiler
from omf import OmfReader
from workspace import prepare_output
import unicorn
from unicorn import x86_const as X

EXPRESSIONS={
    'unsigned_add_before_div':'(b + 3) / 2',
    'signed_add_before_div':'(a + 7) / 2',
    'unsigned_product_before_div':'(b * 257) / 3',
    'unsigned_contraction_counterexample':'(b * 9) / 3',
    'unsigned_repeated_add_contraction':'(b + b) / 2',
    'unsigned_shift_division':'(b << 1) / 2',
    'unsigned_product_modulo':'(b * 6) % 3',
    'signed_product_before_div':'(a * 9) / 3',
    'unsigned_subtract_compare':'b - 2 > 100',
    'mixed_comparison':'a < b',
    'hexadecimal_type':'a < 0xFFFF',
    'decimal_type_contrast':'a < 40000',
    'large_decimal_unsigned_msc':'a < 4000000000',
    'large_decimal_long_unsigned_msc':'a < 4000000000L',
    'unsigned_division':'a / b',
    'unsigned_modulo':'a % b',
    'signed_division':'a / (int)(c | 1)',
    'signed_modulo':'a % (int)(c | 1)',
    'signed_right_shift':'a >> 3',
    'unsigned_left_shift':'b << 7',
    'signed_left_shift':'a << 2',
    'byte_product':'c * c',
    'bitwise_not':'~b',
    'unary_unsigned_minus':'-b',
    'conditional_type':'c ? a : b',
    'macro_add_before_div':'ADD(b) / 2',
    'long_peer_contrast':'b + 40000',
    'sizeof_expression':'sizeof(a + 1)',
    'sizeof_far_pointer_difference':'sizeof((char far *)0 - (char far *)0)',
    'sizeof_near_pointer_difference':'sizeof((char near *)0 - (char near *)0)',
    'char_sign':'(char)c < 0',
    'nested_modulo':'((b + c) * 17) % 29',
}


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def machine(obj):
    publics={p['name']:p for p in obj.publics}
    segments={p['segment'] for p in obj.publics if p['name'].startswith('_p')}
    if len(segments)!=1:raise AssertionError(segments)
    segment=next(iter(segments))
    if obj.fixups_in(segment):raise AssertionError('Probe code requires relocation; do not ignore it.')
    code=obj.segment_bytes(segment)
    cpu=unicorn.Uc(unicorn.UC_ARCH_X86,unicorn.UC_MODE_16)
    cpu.mem_map(0,0x110000)
    cpu.mem_write(0x20000,code)
    def invoke(name,a,b,c):
        cpu.reg_write(X.UC_X86_REG_CS,0x2000)
        cpu.reg_write(X.UC_X86_REG_IP,publics['_'+name]['offset'])
        for register in (X.UC_X86_REG_SS,X.UC_X86_REG_DS,X.UC_X86_REG_ES):cpu.reg_write(register,0x5000)
        cpu.reg_write(X.UC_X86_REG_SP,0xff00)
        cpu.reg_write(X.UC_X86_REG_BP,0)
        # far return to a mapped sentinel; all parameters are stack words.
        cpu.mem_write(0x5ff00,struct.pack('<5H',0,0x7000,a&65535,b&65535,c))
        cpu.emu_start(0x20000+publics['_'+name]['offset'],0x70000,count=10000)
        if cpu.reg_read(X.UC_X86_REG_CS)!=0x7000:raise AssertionError('Probe did not return')
        value=cpu.reg_read(X.UC_X86_REG_AX)|(cpu.reg_read(X.UC_X86_REG_DX)<<16)
        return ctypes.c_int32(value).value
    return invoke


def defined(label,a,b,c):
    # Explicit C90 defined-input predicates for these small positive controls.
    # Counterexamples outside these predicates stay in the report.
    if label=='signed_add_before_div':return -32768<=a+7<=32767
    if label=='signed_product_before_div':return -32768<=a*9<=32767
    if label=='signed_left_shift':return a>=0 and a*4<=32767
    if label=='byte_product':return c*c<=32767
    if label=='unsigned_contraction_counterexample':return b*9<=65535
    if label=='unsigned_product_modulo':return b*6<=65535
    if label=='large_decimal_unsigned_msc':return False
    return True


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,default=ROOT/'build/current/tests/integers')
    p.add_argument('--cc',default='C:/msys64/mingw64/bin/gcc.exe')
    args=p.parse_args();out=args.out.resolve()
    prepare_output(out,ROOT/'build/current/tests/integers',ROOT)
    compiler.WORK=out/'compiler'
    source='#define ADD(x) ((x) + 3)\n'
    names={}
    for index,(label,expr) in enumerate(EXPRESSIONS.items()):
        name='p'+str(index);names[label]=name
        source+='long far '+name+'(int a, unsigned b, unsigned char c) { return '+expr+'; }\n'
    (out/'canonical.c').write_text(source)
    native='#include <stdint.h>\n'+scalar.convert(source)
    lowered,receipt=integer_frontend.convert(native,(out/'lowered.c').as_posix(),args.cc,[])
    (out/'lowered.c').write_text(lowered)
    (out/'negative.c').write_text(native)
    params=[]
    values=(-32768,-32767,-30000,-1025,-257,-9,-1,0,1,7,127,255,256,1023,16384,30000,32760,32767)
    unsigned=(1,2,3,7,255,256,1023,16384,32767,32768,40000,65533,65534,65535)
    for a in values:
        for b in unsigned:
            for c in (0,1,127,128,255):params.append((a,b,c))
    libraries={}
    for lane in ('lowered','negative'):
        command=[args.cc,'-std=c11','-O2','-fsigned-char','-shared',str(out/(lane+'.c')),'-o',str(out/(lane+'.dll'))]
        run=subprocess.run(command,capture_output=True,text=True)
        (out/(lane+'.compile.log')).write_text(run.stdout+run.stderr)
        if run.returncode:raise AssertionError(run.stderr)
        library=ctypes.CDLL(str(out/(lane+'.dll')))
        for name in names.values():
            fn=getattr(library,name);fn.argtypes=(ctypes.c_int16,ctypes.c_uint16,ctypes.c_uint8);fn.restype=ctypes.c_int32
        libraries[lane]=library
    runs=[];witnesses=[]
    for profile,flags in [('msc600a',['/AL','/Gs','/Od']),('msc600a',['/AL','/Gs','/Oeg']),
                          ('msc600ax',['/AL','/Gs','/Os']),('msc600ax',['/AL','/Gs','/Oeg'])]:
        result=compiler.compile_c(source,profile,flags=flags,keep=True)
        if not result.ok:raise AssertionError(result.log)
        obj=OmfReader().read(result.obj)
        invoke=machine(obj)
        mismatch=Counter();negative=Counter();first=[];excluded=Counter();excluded_witnesses=[]
        for label,name in names.items():
            for a,b,c in params:
                expected=invoke(name,a,b,c)
                actual=getattr(libraries['lowered'],name)(a,b,c)
                raw=getattr(libraries['negative'],name)(a,b,c)
                if not defined(label,a,b,c):
                    excluded[label]+=1
                    if actual!=expected and not any(w['expression']==label for w in excluded_witnesses):
                        excluded_witnesses.append({'expression':label,'input':[a,b,c],'msc':expected,'lowered':actual,'unlowered':raw,
                                                  'classification':'MSC_UNSIGNED_CONTRACTION' if label=='unsigned_contraction_counterexample' else 'UNRESOLVED_COMPILER_DEPENDENT'})
                    continue
                if actual!=expected:
                    mismatch[label]+=1
                    if len(first)<20:first.append({'expression':label,'input':[a,b,c],'msc':expected,'lowered':actual})
                if raw!=expected:
                    negative[label]+=1
                    if not any(w['expression']==label for w in witnesses):
                        witnesses.append({'expression':label,'input':[a,b,c],'msc':expected,'unlowered':raw,'lowered':actual})
        runs.append({'profile':profile,'flags':flags,'object_sha256':hashlib.sha256(result.obj).hexdigest(),
                     'cases':len(params)*len(names),'mismatches':dict(mismatch),'negative_mismatches':dict(negative),
                     'first_mismatches':first,'excluded_contract_cases':dict(excluded),'excluded_witnesses':excluded_witnesses,
                     'compiler_work':str(result.workdir)})
        runs[-1]['unsigned_language_counterexample']={
            'expression':'(b * 9) / 3','b':32768,
            'msc':invoke(names['unsigned_contraction_counterexample'],0,32768,0),
            'C16':((32768*9)&65535)//3,
            'native_without_target_rule':getattr(libraries['lowered'],names['unsigned_contraction_counterexample'])(0,32768,0)}
        runs[-1]['unsuffixed_decimal_counterexample']={
            'expression':'a < 4000000000','a':0,
            'msc':invoke(names['large_decimal_unsigned_msc'],0,1,0),'C90_C16':1,
            'native':getattr(libraries['lowered'],names['large_decimal_unsigned_msc'])(0,1,0),
            'long_suffix_positive':invoke(names['large_decimal_long_unsigned_msc'],0,1,0)}
        print(json.dumps({k:v for k,v in runs[-1].items() if k not in {'first_mismatches','excluded_witnesses'}}))
    passed=all(not r['mismatches'] for r in runs)
    side_source=Path(__file__).with_name('single_evaluation.c')
    side_output,side_receipt=integer_frontend.convert(side_source.read_text(),(out/'single_evaluation.c').as_posix(),args.cc,[])
    (out/'single_evaluation.c').write_text(side_output)
    side_runs=[]
    for opt in ('-O0','-O2'):
        exe=out/('single_evaluation_'+opt[1:]+'.exe')
        run=subprocess.run([args.cc,'-std=c11','-fsigned-char',opt,str(out/'single_evaluation.c'),'-o',str(exe)],capture_output=True,text=True)
        if run.returncode:raise AssertionError(run.stderr)
        run=subprocess.run([str(exe)],timeout=10)
        side_runs.append({'optimization':opt,'passed':run.returncode==0})
        passed=passed and run.returncode==0
    packet={'passed':passed,'runs':runs,'negative_witnesses':witnesses,'conversion':receipt,
            'single_evaluation':side_runs,'single_evaluation_conversion':side_receipt,
            'expressions':EXPRESSIONS,'pins':{str(p):sha(p) for p in [Path(__file__),Path(integer_frontend.__file__),Path(scalar.__file__),out/'canonical.c',out/'lowered.c',out/'negative.c']},
            'scope':'Bounded real MSC 6.00A/AX compiled controls; signed overflow observations do not prove all MSC optimizations or invalid domains.'}
    (out/'report.json').write_text(json.dumps(packet,indent=2)+'\n')
    return not passed

if __name__=='__main__':raise SystemExit(main())
