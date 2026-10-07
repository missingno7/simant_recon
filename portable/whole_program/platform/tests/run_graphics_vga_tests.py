"""VGA hardware controls and original-instruction versus native RAM sprite blends."""
from pathlib import Path
from types import SimpleNamespace
import argparse
import ctypes
import hashlib
import json
import random
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--gcc', default='C:/msys64/mingw64/bin/gcc.exe')
    parser.add_argument('--native-report', type=Path, required=True,
                        help='successful native build supplying the generated canonical declarations')
    args=parser.parse_args()
    out=args.out.resolve()
    sys.path.insert(0,str(ROOT/'tools'))
    from workspace import prepare_output
    prepare_output(out,ROOT/'build/current/tests/vga')
    sources=[ROOT/'portable/whole_program/platform'/f for f in ('graphics_vga.c','graphics_s00_raster_source.c','tests/graphics_vga_test.c')]
    command=[args.gcc,'-std=c11','-Wall','-Wextra','-Werror','-O0','-I',str(ROOT),*[str(p) for p in sources]]
    exe=out/'vga-test.exe'
    subprocess.run([*command,'-o',str(exe)],check=True,capture_output=True)
    result=subprocess.run([str(exe)],check=True,capture_output=True,text=True)
    dll=out/'raster.dll'
    subprocess.run([*command,'-shared','-Wl,--export-all-symbols','-o',str(dll)],check=True,capture_output=True)
    native=ctypes.CDLL(str(dll))
    import behavior as b
    import functions
    from graphics_instruction_checks import copy_rect_checks, tile_checks
    rng=random.Random(0x35a6)
    cases=[]
    for masked in (0,1):
        name='o00_35A6_0007' if masked else 'o00_35A6_0177'
        machine=b.Machine(SimpleNamespace(function=functions.get(name),vectors={}))
        call=getattr(native,'sim_s00_raster_masked_blit' if masked else 'sim_s00_raster_opaque_blit')
        call.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_int16,ctypes.c_int16]
        for shift in (0,1,7,8,15,16,46,63):
            for offset in (0,1,2,54,90,100):
                width=48; height=20; dest_width=112; dest_height=112
                image=struct.pack('<HH',width,height)+rng.randbytes(6*height*(5 if masked else 4))
                buffer=struct.pack('<HH',dest_width,dest_height)+rng.randbytes(14*dest_height*4+2)
                source_array=(ctypes.c_uint8*len(image)).from_buffer_copy(image)
                output_array=(ctypes.c_uint8*len(buffer)).from_buffer_copy(buffer)
                status=call(source_array,len(image),output_array,len(buffer),shift,offset)
                original=machine.run(b.Case(f'{name}-{shift}-{offset}',
                    args=[0,0x7000,0,0x7400,shift,offset],
                    writes=[(0x70000,image),(0x74000,buffer)],
                    observe=[b.Range('buffer',0x74000,len(buffer))],return_kind='void'))
                expected=bytes.fromhex(original['ranges']['buffer'])
                actual=bytes(output_array)
                equal=status==0 and actual==expected
                cases.append({'entry':name,'shift':shift,'row_offset':offset,'matched':equal})
                if not equal:
                    (out/'expected.bin').write_bytes(expected); (out/'actual.bin').write_bytes(actual)
                    raise AssertionError(cases[-1])
    # The old domain restriction must reject witnessed ordinary inputs.
    negative=any(c['shift']>15 or c['row_offset']>1 for c in cases)
    # Explicit-size clients retain true storage checks; source ABI has no sizes.
    short=(ctypes.c_uint8*4)(48,0,20,0)
    dest=(ctypes.c_uint8*len(buffer)).from_buffer_copy(buffer)
    CHECK=call(short,4,dest,len(buffer),46,54)!=0
    rect_cases=copy_rect_checks(native,b,functions,rng)
    build_report=json.loads(args.native_report.read_text())
    if not build_report.get('passed'):raise ValueError('successful native build required')
    tile_sources=[ROOT/'portable/whole_program/platform'/f for f in
                  ('graphics_vga.c','graphics_tile_upload.c','graphics_capture_source.c',
                   'ega_map_readback.c','tests/graphics_tile_test.c')]
    tile_dll=out/'tile.dll'
    subprocess.run([args.gcc,'-std=c11','-Wall','-Wextra','-Werror','-O0','-shared',
        '-Wl,--export-all-symbols','-I',str(ROOT),'-I',str(args.native_report.resolve().parent),
        *[str(p) for p in tile_sources],'-o',str(tile_dll)],check=True,capture_output=True)
    tile_cases=tile_checks(ctypes.CDLL(str(tile_dll)),b,functions,rng)
    receipt={'passed':all(c['matched'] for c in cases+rect_cases+tile_cases) and negative and CHECK,
        'hardware':result.stdout.strip(),'raster_cases':cases,
        'copy_rect_cases':rect_cases,'tile_cases':tile_cases,
        'negative_controls':{'former_shape_predicate_excludes_tested_inputs':negative,
            'short_resource_rejected_by_explicit_size_api':CHECK},
        'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in set(sources+tile_sources)},
        'oracle_sha256':b.exe.load().sha256,
        'scope':'Original locked S00 instructions compared with complete destination RAM bytes. VGA aperture/register controls are independent hardware unit checks; whole-game pixel equality is not claimed.'}
    (out/'report.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'passed':receipt['passed'],'original_instruction_cases':len(cases+rect_cases+tile_cases),'hardware':receipt['hardware']}))
    return int(not receipt['passed'])

if __name__=='__main__':
    raise SystemExit(main())
