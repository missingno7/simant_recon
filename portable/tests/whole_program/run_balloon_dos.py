"""Fresh DOS/native tests of the genuine m1699 ASM bitmap helpers."""
from pathlib import Path
import argparse
import ctypes as C
import hashlib
import json
import random
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).parent))
from run_asm_utilities_dos import original_machine, case_run, behavior
SEED = 0x16990000
SEG, SRC, DST, HDR = 0x3000, 0x1000, 0x8000, 0x0800

class Bitmap(C.Structure):
    _pack_ = 2
    _fields_ = [('width', C.c_int16), ('height', C.c_int16), ('bits', C.c_void_p)]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', default='build/workers/whole_program/balloon-dos')
    args = ap.parse_args()
    out = (ROOT / args.out).resolve()
    if not out.is_relative_to(ROOT / 'build/workers'):
        raise ValueError('scratch output only')
    out.mkdir(parents=True, exist_ok=False)
    paths = [Path(__file__), ROOT / 'src/root/m1699.asm',
        ROOT / 'layout/oracle.lock.json', ROOT / 'tools/behavior.py',
        ROOT / 'portable/tests/whole_program/run_asm_utilities_dos.py',
        ROOT / 'portable/whole_program/algorithms/balloon.c',
        ROOT / 'portable/whole_program/algorithms/balloon.h',
        ROOT / 'portable/whole_program/types/fonts.h']
    pins = {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}
    compiler = Path('C:/msys64/mingw64/bin/gcc.exe')
    command = [str(compiler), '-std=c11', '-O2', '-Wall', '-Wextra', '-Wconversion',
        '-Werror', '-pedantic', '-I', str(ROOT), '-shared', str(paths[5]),
        '-o', str(out / 'balloon.dll')]
    built = subprocess.run(command, capture_output=True, text=True)
    (out / 'compile.txt').write_text(built.stdout + built.stderr)
    if built.returncode: raise RuntimeError(built.stderr)
    lib = C.CDLL(str(out / 'balloon.dll'))
    signatures = {
        '0000': [C.c_void_p,C.c_int16,C.c_int16,C.c_void_p],
        '0050': [C.c_void_p,C.c_int16,C.c_int16,C.c_void_p,C.c_int16],
        '00A6': [C.c_void_p,C.c_void_p,C.c_int16,C.c_int16],
        '0110': [C.c_void_p,C.c_void_p],
        '01AA': [C.c_void_p,C.c_void_p,C.c_int16]}
    rng = random.Random(SEED)
    rows, mismatches = [], []
    for suffix, signature in signatures.items():
        name = 'f_1699_' + suffix
        function = getattr(lib, name)
        function.argtypes, function.restype = signature, None
        machine = original_machine(name)
        for case in range(64):
            columns = (1,2,3,7,8,16,31,63)[case % 8]
            height = 1 + case % 19
            width = columns * 8 - case % 8
            x, y = case % 3, case % 11
            dst = bytearray(rng.getrandbits(8) for _ in range(8192))
            src = bytearray(rng.getrandbits(8) for _ in range(8192))
            dst[:4] = struct.pack('<HH', width, height)
            if suffix in ('0000','0050','00A6'):
                dst[:4] = struct.pack('<HH', 640, 64)
            if suffix == '0110':
                src[:4] = dst[:4]
            n = case % 65
            native_src = C.create_string_buffer(bytes(src), len(src))
            native_dst = C.create_string_buffer(bytes(dst), len(dst))
            writes = [(SEG*16 + SRC, bytes(src)), (SEG*16 + DST, bytes(dst))]
            if suffix == '0000':
                dos_args = [SRC,SEG,x,y,DST,SEG]
                native_args = [native_src,x,y,native_dst]
            elif suffix == '0050':
                dos_args = [SRC,SEG,x,y,DST,SEG,n]
                native_args = [native_src,x,y,native_dst,n]
            elif suffix == '00A6':
                hdr = struct.pack('<HHHH', width,height,SRC,SEG)
                writes.append((SEG*16 + HDR, hdr))
                bitmap = Bitmap(width,height,C.addressof(native_src))
                dos_args = [HDR,SEG,DST,SEG,x,y]
                native_args = [C.byref(bitmap),native_dst,x,y]
            elif suffix == '0110':
                dos_args = [SRC,SEG,DST,SEG]
                native_args = [native_src,native_dst]
            else:
                # The source's LOOP count 0 requires 64K live spans. This
                # bounded run covers positive lengths; that domain is explicit.
                n = (1,2,3,16,63,255,1024,8192)[case % 8]
                dos_args = [DST,SEG,SRC,SEG,n]
                native_args = [native_dst,native_src,n]
            observed = [behavior.Range('source',SEG*16 + SRC,len(src)),
                        behavior.Range('dest',SEG*16 + DST,len(dst))]
            dos = case_run(machine,f'{suffix}-{case}',dos_args,writes,observed)
            function(*native_args)
            expected = bytes.fromhex(dos['ranges']['source']) + bytes.fromhex(dos['ranges']['dest'])
            actual = native_src.raw + native_dst.raw
            equal = expected == actual
            rows.append({'function':name,'case':case,'equal':equal,
                'oracle_sha256':hashlib.sha256(expected).hexdigest(),
                'native_sha256':hashlib.sha256(actual).hexdigest()})
            if not equal:
                first = next(i for i,(a,b) in enumerate(zip(expected,actual)) if a != b)
                mismatches.append({'function':name,'case':case,'first_byte':first,
                    'original':expected[first],'native':actual[first]})
                break
    stable = all(sha(ROOT / p) == h for p,h in pins.items())
    report = {'schema':'simant-balloon-asm-differential-v1',
        'claim':'FRESH_DOS_NATIVE_BITMAP_CONTRACT_COMPARISON',
        'seed':SEED,'tests':len(rows),'mismatches':mismatches,
        'compared':['all source and destination bytes, including surrounding untouched storage'],
        'domain':'Disjoint live spans; positive width/height; mask column count 1..63; byte-sized loop bounds; no DOS segment wrap. Count-zero REP fill covered; count-zero exchange excluded.',
        'normalization':'Font Bitmap pointer uses native pointer width; DOS private scratch and segment/register identities excluded.',
        'inputs':pins,'inputs_stable':stable,'compiler_sha256':sha(compiler),
        'command':command,'rows':rows,'passed':not mismatches and stable}
    (out / 'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('tests','mismatches','passed')}))
    return 0 if report['passed'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
