"""FF-only virtual-DOS map lookup: compiled controls, locked instructions, GUI.

Run with --gui to include production mouse replay and a separate read-only
observer link. --evidence optionally checks the retained original/canonical
buffers from the map-cache investigation; it is never written.
"""
from __future__ import annotations
import argparse
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from portable.tests.hidden_desktop import install
install()
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, 'C:/tools/unicorn-2.1.4')
import exe as dos_exe
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16
from unicorn.x86_const import (UC_X86_REG_CS, UC_X86_REG_IP, UC_X86_REG_DS,
                              UC_X86_REG_SS, UC_X86_REG_SP, UC_X86_REG_EFLAGS)

PLATFORM = ROOT / 'portable/whole_program/platform'
TEST = Path(__file__).with_name('map_frozen_cache_test.c')
WIDTHS = (128, 64, 128, 64, 128, 64)
SIZES = (1024, 512, 256, 128, 64, 32)
ENTRIES = (0, 0x137, 0x26a, 0x3a9, 0x4d8, 0x6a3)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked(command, log, **kwargs):
    result = subprocess.run(list(map(str, command)), capture_output=True, text=True,
                            timeout=120, **kwargs)
    log.write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(f'{command[0]} exit {result.returncode}: {log}')
    return result.stdout


class Layout(C.Structure):
    _fields_ = [(n, C.c_uint16) for n in ('raster', 'callback', 'load')]


class OriginalInstructions:
    """Execute immutable S00 bytes; only declared virtual machine data varies.

    Resident table and instructions come directly from the locked EXE. The
    virtual addresses remain fixed; the relocated dispatch segment data is
    varied independently, exactly as an MZ loader would add a paragraph.
    """
    def __init__(self):
        self.image = dos_exe.load()
        self.cpu = Uc(UC_ARCH_X86, UC_MODE_16)
        self.cpu.mem_map(0, 0x100000)
        for index in (0, 27):
            section = self.image.sections[index]
            self.cpu.mem_write(section.load_seg * 16, section.data)
        symbols = json.loads((ROOT / 'layout/symbols.json').read_text())['data']
        width = symbols['gfx_screen_width_pixels']
        self.width_at = width['seg'] * 16 + width['off']

    def pack(self, transform, profile, source, load=0x824, raster=0x31ad):
        cpu = self.cpu
        cpu.mem_write(0x55b30 + 0x209a,
                      struct.pack('<HH', (raster + load) & 65535, 0x166a))
        cpu.mem_write(self.width_at, struct.pack('<H', 320 if profile else 640))
        cpu.mem_write(0x70000, source)
        cpu.mem_write(0x70fff, b'\xcc' * (SIZES[transform] + 2))
        cpu.mem_write(0x55b30 + 0xf000,
                      struct.pack('<8H', 0, 0x8000, 0, 0x7000, 0, 0x7100,
                                  len(source), 0))
        for register, value in ((UC_X86_REG_CS, 0x3126), (UC_X86_REG_IP, ENTRIES[transform]),
                                (UC_X86_REG_DS, 0x55b3), (UC_X86_REG_SS, 0x55b3),
                                (UC_X86_REG_SP, 0xf000), (UC_X86_REG_EFLAGS, 2)):
            cpu.reg_write(register, value)
        cpu.emu_start(0x31260 + ENTRIES[transform], 0x80000, count=20000)
        assert cpu.reg_read(UC_X86_REG_CS) == 0x8000
        assert bytes(cpu.mem_read(0x70000, len(source))) == source
        assert bytes(cpu.mem_read(0x70fff, 1)) == b'\xcc'
        assert bytes(cpu.mem_read(0x71000 + SIZES[transform], 1)) == b'\xcc'
        return bytes(cpu.mem_read(0x71000, SIZES[transform]))


def native_pack(native, t, p, source, load=0x824, raster=0x31ad):
    assert native.sim_s00_map_bind_dos_layout(C.byref(Layout(raster, 0x166a, load))) == 0
    src = (C.c_uint8 * len(source)).from_buffer_copy(source)
    dest = (C.c_uint8 * (SIZES[t] + 2))(*([0xcc] * (SIZES[t] + 2)))
    assert native.map_frozen_convert(t, p, src, len(source), C.byref(dest, 1), SIZES[t]) == 0
    assert bytes(src) == source and dest[0] == dest[-1] == 0xcc
    return bytes(dest)[1:-1]


def instruction_checks(native, original, out):
    counts = {}
    for load in (0x824, 0x82c, 0x924):
        count = 0
        for t in (0, 1, 4, 5):
            for neighbour in range(25):
                for pos in range(WIDTHS[t]):
                    source = bytearray([neighbour] * WIDTHS[t]); source[pos] = 255
                    expected = original.pack(t, 0, bytes(source), load)
                    actual = native_pack(native, t, 0, bytes(source), load)
                    assert actual == expected, (t, load, neighbour, pos)
                    count += 1
        counts[f'{load:04X}'] = count
        print(f'load {load:04X}: {count} complete instruction buffers equal', flush=True)
    ordinary = 0
    for t in range(6):
        for p in ((0, 1) if t >= 4 else (0,)):
            for color in range(25):
                for source in (bytes([color] * WIDTHS[t]),
                               bytes((i + color) % 25 for i in range(WIDTHS[t]))):
                    assert native_pack(native, t, p, source) == original.pack(t, p, source)
                    ordinary += 1
    return dict(load_profiles=counts, ordinary_buffers_equal=ordinary,
                cache_footprints=producer_checks(native, original))


def producer_checks(native, original):
    """Actual original dirty-mark instructions at controlled positions.

    Bitmap drawing/allocator services are explicit callbacks. No claim of
    ordinary full-game foot reachability follows from these isolated fixtures.
    """
    import behavior as b
    import functions
    from types import SimpleNamespace
    cases = []
    for width, transform in ((128, 0), (64, 1)):
        for entry, y, enabled in (('DrawMapFoot', 40, 0), ('DrawMapSpider', 32, 1),
                                   ('DrawMapSpider', 0, 1), ('DrawMapSpider', 64, 1),
                                   ('DrawMapFoot', 40, 1), ('DrawMapFoot', -4, 1),
                                   ('DrawMapFoot', 61, 1), ('DrawMapFoot', 64, 1)):
            machine = b.Machine(SimpleNamespace(function=functions.get(entry), vectors={}))
            values = [('FootHere', enabled), ('FootX', 10), ('FootY', y), ('BoyHere', 0),
                      ('BoyDir', 0), ('multiplier', width), ('gfx_screen_width_pixels', 640),
                      ('newMapForce', 0)]
            writes = [(b.symbol_address(n), b.words(v)) for n,v in values]
            writes += [(b.symbol_address('fd_50F6_10E2'), b.words(1,1)),
                       (b.symbol_address('map_viewport_rect'), b.words(64,82,576,338)),
                       (0x71000, bytes([11])*8192)]
            result = machine.run(b.Case(f'{entry}-{width}-{y}-{enabled}',
                args=[10,y,0] if entry=='DrawMapSpider' else [], writes=writes,
                callbacks={'mem_Lock':b.Callback(2,handler=lambda m,a:(0,0x7100)),
                           'mem_Unlock':b.Callback(2,handler=lambda m,a:0),
                           'win_DrawBitMap':b.Callback(3,handler=lambda m,a:0)},
                observe=[b.Range('cache',0x71000,8192)],return_kind='void',observe_at_calls=False))
            cache=bytes.fromhex(result['ranges']['cache'])
            start=y-2 if entry=='DrawMapSpider' else y
            rows=list(range(max(0,start),min(64,start+(5 if entry=='DrawMapSpider' else 8)))) if enabled else []
            expected=bytearray([11]*8192)
            for row in rows: expected[row*width]=255
            assert cache==bytes(expected), (entry,width,y)
            for row in range(64):
                source=cache[row*width:(row+1)*width]
                assert native_pack(native,transform,0,source)==original.pack(transform,0,source)
            assert cache==bytes(expected)
            cases.append(dict(producer=entry,width=width,y=y,enabled=enabled,
                              dirty_rows=rows,complete_rows_equal=64))
    return cases


def captured_checks(native, original, evidence):
    result = []
    for lane, raster in (('original-drag', 0x31ad), ('experimental-drag', 0x31ad),
                         ('canonical-drag', 0x3075)):
        count = dirty = 0
        for path in sorted((evidence / lane).glob('exec-pack-in.*.bin')):
            target = path.with_name(path.name.replace('pack-in.', 'pack-out.'))
            if not target.exists(): continue
            source = path.read_bytes(); expected = target.read_bytes()
            assert native_pack(native, 0, 0, source, raster=raster) == expected
            assert original.pack(0, 0, source, raster=raster) == expected
            count += 1; dirty += 255 in source
        assert count and dirty, lane
        result.append(dict(lane=lane, raster=f'{raster:04X}', complete_buffers_equal=count,
                           dirty_buffers_equal=dirty))
    source = bytes([255, 11]) + bytes([11] * 126)
    original_pattern = native_pack(native, 0, 0, source)
    canonical_pattern = native_pack(native, 0, 0, source, raster=0x3075)
    assert original_pattern != canonical_pattern
    return dict(lanes=result, canonical_layout_debt=True,
                original_pattern_sha256=hashlib.sha256(original_pattern).hexdigest(),
                canonical_pattern_sha256=hashlib.sha256(canonical_pattern).hexdigest(),
                scope='Canonical profile is a contextual control; no three-way FRAME_EQUAL claim.')


def production_enhanced_inputs(process, started):
    """Click/move the uninstrumented production process on its private desktop.

    HWNDs are restricted to this child PID. No global input, desktop capture or
    changes to game memory are used. The separate observer proves source events.
    """
    from ctypes import wintypes as W
    user=C.WinDLL('user32',use_last_error=True)
    user.FindWindowExW.argtypes=[W.HWND,W.HWND,W.LPCWSTR,W.LPCWSTR]
    user.FindWindowExW.restype=W.HWND
    user.GetDlgItem.argtypes=[W.HWND,C.c_int];user.GetDlgItem.restype=W.HWND
    user.IsWindowEnabled.argtypes=[W.HWND];user.IsWindowEnabled.restype=W.BOOL
    user.GetWindowThreadProcessId.argtypes=[W.HWND,C.POINTER(W.DWORD)]
    user.GetWindowRect.argtypes=[W.HWND,C.POINTER(W.RECT)]
    user.MoveWindow.argtypes=[W.HWND,C.c_int,C.c_int,C.c_int,C.c_int,W.BOOL]
    user.SendMessageTimeoutW.argtypes=[W.HWND,W.UINT,W.WPARAM,W.LPARAM,W.UINT,W.UINT,C.POINTER(C.c_size_t)]
    user.SendMessageTimeoutW.restype=W.LPARAM
    def named(title):
        window=None
        while True:
            window=user.FindWindowExW(None,window,None,title)
            if not window:return None
            pid=W.DWORD();user.GetWindowThreadProcessId(window,C.byref(pid))
            if pid.value==process.pid:return window
    def until(seconds):
        while time.monotonic()-started<seconds:
            assert process.poll() is None, ('early production exit',process.returncode)
            time.sleep(.025)
    until(24)
    map_window=named('Map');footer=named('Map / Ant Control Panel')
    assert map_window and footer, 'production enhanced Map/footer missing'
    freeze=user.GetDlgItem(footer,0x10e);pause=user.GetDlgItem(footer,15)
    assert freeze and pause and user.IsWindowEnabled(freeze)
    def click(window):
        result=C.c_size_t()
        assert user.SendMessageTimeoutW(window,0x00f5,0,0,2,2000,C.byref(result)), 'BM_CLICK timeout'
    until(25);click(freeze)
    until(27);rect=W.RECT();assert user.GetWindowRect(map_window,C.byref(rect))
    assert user.MoveWindow(map_window,rect.left+24,rect.top+16,
                           rect.right-rect.left,rect.bottom-rect.top,True)
    moved=W.RECT();assert user.GetWindowRect(map_window,C.byref(moved))
    assert (moved.left,moved.top)==(rect.left+24,rect.top+16)
    until(30);click(freeze)
    until(32);click(pause)
    until(34);click(pause)
    return dict(freeze_id='010E',freeze_seconds=25,move_seconds=27,
                unfreeze_seconds=30,pause_roundtrip_seconds=[32,34],
                window_before=[rect.left,rect.top,rect.right,rect.bottom],
                window_after=[moved.left,moved.top,moved.right,moved.bottom])


def replay(build, out, report, original):
    """Same production binary for both modes, plus separate instrumented lanes.

    Bare production lanes use ordinary timed mouse inputs. Enhanced observer
    lanes click the live HWND button, move the Map and click it again. Every
    complete intercepted native buffer is compared offline to original code.
    """
    out.mkdir()
    cc = report['application_link']['command'][0]
    obj = out / 'observer.o'; observed = out / 'simant-map-frozen-observer.exe'
    checked([cc, '-std=c11', '-O2', '-g', '-fno-lto', '-DMAP_FROZEN_OBSERVER',
             '-I'+str(ROOT), '-c', TEST, '-o', obj], out/'compile.log')
    command = report['application_link']['command'][:]
    command[command.index('-o')+1] = str(observed)
    wrapped = ['enhanced_execute_next', 'ProcMapEvent', 'gfx_planar_map128_pack2',
               'gfx_planar_map64_pack2', 'gfx_planar_map128_pack4', 'gfx_planar_map64_pack4',
               'gfx_planar_map128_pack8', 'gfx_planar_map64_pack8']
    command[1:1] = [str(obj), *['-Wl,--wrap='+n for n in wrapped]]
    checked(command, out/'link.log', cwd=build)
    for name in ('SDL3.dll', 'simant-build-id.txt'): shutil.copyfile(build/name, out/name)
    shutil.copytree(build/'runtime-bios-fonts', out/'runtime-bios-fonts')
    def run_lane(mode, enhanced, observer):
        lane = out / f'{mode}-{"enhanced" if enhanced else "bare"}-{"observer" if observer else "production"}'
        lane.mkdir(); assets = lane/'assets'; shutil.copytree(build/'runtime-assets', assets)
        if enhanced:
            text = (ROOT/'portable/tests/runtime/windows-quick.txt').read_text()
            text = text.replace('207 58', '133 126' if mode=='full' else '50 190')
            # Production enhanced survival is covered by the live HWND sweep;
            # the observer below drives these same HWND controls explicitly.
        else:
            xy = '294 234' if mode=='full' else '198 302'
            text = ('5000 down Return\n5050 up Return\n7000 down Return\n7050 up Return\n'
                    '9000 down Return\n9050 up Return\n12000 move '+xy+'\n'
                    '12200 mouse-down Left '+xy+'\n12400 mouse-up Left '+xy+'\n'
                    '16000 down Return\n16050 up Return\n20000 down Return\n20050 up Return\n'
                    '22000 down Return\n22050 up Return\n24000 move 340 350\n'
                    '25000 mouse-down Left 340 350\n25150 mouse-up Left 340 350\n'
                    '27000 move 200 72\n27300 mouse-down Left 200 72\n'
                    '27500 move 260 92\n27700 mouse-up Left 260 92\n'
                    '33000 move 400 370\n33300 mouse-down Left 400 370\n33450 mouse-up Left 400 370\n')
        script = lane/'input.txt'; script.write_text(text)
        env = {k:v for k,v in os.environ.items() if not k.startswith(('SIMANT_ENHANCED','SIMANT_FROZEN','SIMANT_WORKSPACE'))}
        env.update(SDL_AUDIODRIVER='dummy', SIMANT_FROZEN_PACKS=str(lane/'packs.bin'),
                   SIMANT_WORKSPACE_LAYOUT=str(lane/'layout.txt'))
        if enhanced: env['SIMANT_FROZEN_ENHANCED']='1'
        else: env['SIMANT_ENHANCED_CONTRACTS']='0'
        cmd = [str(observed if observer else build/'simant-canonical.exe'),
               *(['--windows','--ui-scale','100'] if enhanced else []),
               *([] if enhanced and not observer else ['--deterministic']),
               '--seed','0','--assets',str(assets),'--input-script',str(script),
               '--smoke-ms','39000','--frame',str(lane/'last.bmp'),
               '--diagnostics-dir='+str(lane/'diagnostics')]
        inputs=None
        with (lane/'run.log').open('w') as log:
            if enhanced and not observer:
                started=time.monotonic()
                process=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
                try:
                    inputs=production_enhanced_inputs(process,started)
                    process.wait(timeout=50)
                finally:
                    if process.poll() is None:process.kill();process.wait()
            else:
                process = subprocess.run(cmd, cwd=ROOT, env=env, stdout=log,
                                         stderr=subprocess.STDOUT, timeout=80)
        assert process.returncode == 0, (lane, process.returncode)
        log = (lane/'run.log').read_text()
        if observer:
            assert 'FROZEN_EVENT 1 ' in log and 'FROZEN_EVENT 2 ' in log and 'FROZEN_COMPLETE events=2 ' in log, lane
            assert 'cache_marks=5' in log, lane
            assert 'FROZEN_UNFREEZE dirty_packs_after=0 source_cache_rng_unchanged=1' in log, lane
            if enhanced: assert 'FROZEN_MOVE ' in log, lane
        return dict(mode=mode, enhanced=enhanced, observer=observer,native_inputs=inputs,
                    exit_code=process.returncode, command=cmd, lane=lane.name)
    # Independent processes share no assets or mutable workspace layout.
    jobs = [(mode, False, observer) for mode in ('full','experimental') for observer in (False,True)]
    jobs += [(mode, True, observer) for mode in ('full','experimental') for observer in (False,True)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(lambda job: run_lane(*job), jobs))
    for row in rows:
        if not row['observer']: continue
        raw=(out/row['lane']/'packs.bin').read_bytes(); at=count=dirty=0
        while at<len(raw):
            t,p,n,z=struct.unpack_from('<4H',raw,at);at+=8
            source=raw[at:at+n];at+=n; actual=raw[at:at+z];at+=z
            assert actual==original.pack(t,p,source), (row['lane'],count)
            count+=1; dirty+=255 in source
        assert at==len(raw) and dirty
        row.update(complete_original_instruction_buffers_equal=count, dirty_buffers_equal=dirty)
    (out/'result.json').write_text(json.dumps(dict(rows=rows,observer_link=command,
        production_sha256=sha(build/'simant-canonical.exe'),observer_sha256=sha(observed)),indent=2)+'\n')
    return rows


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--gui', action='store_true')
    args=parser.parse_args()
    build=args.build.resolve(); out=args.out.resolve()
    out.relative_to(ROOT);build.relative_to(ROOT)
    out.mkdir(parents=True,exist_ok=False)
    report=json.loads((build/'report.json').read_text());assert report['passed']
    changed=[p for p,h in report['input_pins'].items() if sha(ROOT/p)!=h]
    assert not changed, changed
    cc=report['application_link']['command'][0]
    sources=[PLATFORM/'graphics_s00_map_tables.c',PLATFORM/'native_video_profile.c',TEST]
    command=[cc,'-std=c11','-Wall','-Wextra','-Werror','-O2','-fno-strict-aliasing',
             '-I'+str(ROOT),'-I'+str(build),*map(str,sources)]
    executable=out/'map-frozen-cache-test.exe'; dll=out/'map-frozen-cache.dll'
    checked([*command,'-o',executable],out/'compile.log')
    controls=checked([executable],out/'controls.log'); print(controls,flush=True)
    checked([*command,'-shared','-Wl,--export-all-symbols','-o',dll],out/'dll.log')
    native=C.CDLL(str(dll))
    native.sim_s00_map_bind_dos_layout.argtypes=[C.POINTER(Layout)]
    native.map_frozen_convert.argtypes=[C.c_int,C.c_int,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t]
    original=OriginalInstructions()
    result=dict(passed=True,controls=controls.strip(),compile_command=command,
                oracle_sha256=original.image.sha256,
                instruction_comparison=instruction_checks(native,original,out),
                source_sha256={str(p.relative_to(ROOT)):sha(p) for p in [*sources,Path(__file__)]})
    if args.evidence: result['captured_buffers']=captured_checks(native,original,args.evidence.resolve())
    if args.gui: result['gui']=replay(build,out/'gui',report,original)
    result['scope']='All complete converter destinations, no masks; GUI native buffer comparisons at original reference load 0824. Full synchronized game scanout equality is not asserted.'
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=True,report=str(out/'report.json'))))
    return 0


if __name__=='__main__': raise SystemExit(main())
