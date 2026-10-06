"""Original clip caller: synthetic geometry, explicit heap/copy boundaries.

This rejects a capacity argument, not a shipped-game reachability claim.
Original executable instructions are test inputs only.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys
import types

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'src/program.json').is_file())
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'tools'))
import behavior as b
import exe
import functions
import workspace

if not __debug__:
    raise RuntimeError('Run witness checks without Python -O')

ORACLE_PIN = 'aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11'
SOURCE_PINS = {
    'src/root/m1E57.c': '1723a5acc2719d00d79e4a63dd923a1a8c3ec4a5b1a9a8711cbfb85e36570084',
    'src/root/m1D8E.c': 'afe9364f319633dd85c276bed18e848a605934156bfbb4fc276d304cd2ec2556',
}

BASE = 0x70000
HANDLE_BASE = 0x68000

def ptr(address):
    return (address & 15, address >> 4)

def geometry(bars):
    return ([(2 + 2*i, 0, 3 + 2*i, 32) for i in range(bars)] +
            [(0, 2 + 2*i, 32, 3 + 2*i) for i in range(bars)] + [(0, 0, 32, 32)])

def verify_inputs():
    image = exe.load()
    if image.sha256 != ORACLE_PIN or hashlib.sha256(image.path.read_bytes()).hexdigest() != ORACLE_PIN:
        raise ValueError('reviewed oracle pin differs')
    program = json.loads((ROOT / 'src/program.json').read_bytes())
    for path, expected in SOURCE_PINS.items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
            raise ValueError('reviewed source pin differs: ' + path)
        rows = [row for row in program['modules'] if row.get('source') == path]
        if len(rows) != 1 or rows[0]['source_sha256'] != expected:
            raise ValueError('canonical inventory pin differs: ' + path)

def read_list(machine, address):
    result = []
    for index in range(257):
        record = struct.unpack('<4h', machine.read(address + index*8, 8))
        if record[1] == -32768:
            return result
        assert record[0] < record[2] and record[1] < record[3], record
        result.append(record)
    raise AssertionError('clip sentinel absent within bounded fixture')

def execute(bars):
    if bars not in (14, 15):
        raise ValueError('only the two reviewed synthetic arrangements are supported')
    image = exe.load()
    m = b.Machine(types.SimpleNamespace(function=functions.get('f_1E57_038E'),
        vectors={exe.MANAGER_SEG * 16 + v.offset: v for v in image.vectors}))
    allocs = {}
    events = []
    overflow = []
    stopped = False
    rects = geometry(bars)

    def alloc(m, args):
        size = args[0] | args[1] << 16
        tag = m.read(args[4]*16+args[3], 40).split(b'\0', 1)[0].decode('ascii')
        index = len(allocs)
        assert size <= 2048 and index < 34
        address = BASE + 0x1000 * index
        handle = HANDLE_BASE + index*4
        allocs[handle] = dict(address=address, size=size, tag=tag)
        m.write(address, b'\x7a' * (size+16))
        m.write(handle, struct.pack('<HH', *ptr(address)))
        events.append(dict(event='allocate', tag=tag, bytes=size))
        return ptr(handle)

    def lock(m, args):
        address = args[1]*16+args[0]
        return ptr(allocs[address]['address'])

    def getrect(m, args):
        win, off, seg = args
        m.write(seg*16+off, struct.pack('<4h', *rects[win >> 8]))

    def copy(m, args):
        dst = args[1]*16+args[0]
        src = args[3]*16+args[2]
        m.write(dst, m.read(src, args[4]))
        return (args[0], args[1])

    def resize(m, args):
        handle = args[1]*16+args[0]
        events.append(dict(event='resize', bytes=args[2] | args[3] << 16))
        return ptr(handle)

    def write(cpu, access, address, size, value, user):
        for allocation in allocs.values():
            if allocation['tag'] not in ('tmprects', 'clipout'):
                continue
            end = allocation['address']+allocation['size']
            if address < end+16 and address+size > end:
                event = dict(event='scratch-overrun', tag=allocation['tag'],
                    displacement=address-allocation['address'], bytes=size, value=value,
                    pc=f"{m.reg('cs'):04X}:{m.reg('ip'):04X}")
                overflow.append(event)
                events.append(event)

    def code(cpu, address, size, user):
        nonlocal stopped
        if address == b.symbol_address('Punt'):
            stack = m.reg('ss')*16+m.reg('sp')
            off, seg, count = struct.unpack('<3H', m.read(stack+4, 6))
            events.append(dict(event='Punt-entry', message=m.read(seg*16+off,40).split(b'\0',1)[0].decode('ascii'), count=count))
            stopped = True
            cpu.emu_stop()

    m.cpu.hook_add(b.uc.UC_HOOK_MEM_WRITE, write)
    m.cpu.hook_add(b.uc.UC_HOOK_CODE, code)
    noop = lambda m, args: None
    callbacks = {'f_171C_1A9E': b.Callback(5, alloc), 'f_171C_1B84': b.Callback(2, lock),
        'f_171C_1BBA': b.Callback(2, lock), 'f_171C_1C0A': b.Callback(2, noop),
        'f_171C_1B2C': b.Callback(5, resize), 'win_GetObjRect': b.Callback(2,getrect,('ax',),4),
        '__fmemcpy': b.Callback(5,copy)}
    writes = [(b.symbol_address('g_5702'),b.words(*[i<<8 for i in range(len(rects))],0x8000)),
        (b.symbol_address('g_5A9C'),struct.pack('<4h',0,0,32,32)),
        (b.symbol_address('g_5742'),bytes(12)),(b.symbol_address('g_5AAC'),bytes(4)),
        (b.symbol_address('fd_50F6_3B60'),bytes(45*4)),
        (0x55B30+0x584c,b.words(1))]
    try:
        m.run(b.Case('synthetic-bars-'+str(bars),writes=writes,callbacks=callbacks,
            return_kind='void', max_instructions=4000000, max_blocks=800000, observe_at_calls=False))
    except b.ExecutionError:
        if not stopped:
            raise
    assert m.error is None
    tmp = allocs[HANDLE_BASE]
    assert tmp['tag'] == 'tmprects' and tmp['size'] == 2048
    assert allocs[HANDLE_BASE+4]['tag'] == 'clipout' and allocs[HANDLE_BASE+4]['size'] == 2048
    # Successful caller stores the background's visible region separately,
    # then subtracts that full background from the active list (empty result).
    address = tmp['address'] if stopped else list(allocs.values())[-1]['address']
    visible = read_list(m, address)
    for index, first in enumerate(visible):
        for second in visible[index+1:]:
            assert (first[0] >= second[2] or second[0] >= first[2] or
                    first[1] >= second[3] or second[1] >= first[3])
    assert len(visible) == (bars+1)**2
    assert sum((r-l)*(bottom-top) for l,top,r,bottom in visible) == (32-bars)**2
    fatal = [event for event in events if event['event'] == 'Punt-entry']
    if bars == 14:
        assert m.completed and not stopped and not overflow and not fatal
        assert list(allocs.values())[-1]['size'] == 226*8
    else:
        assert stopped and not m.completed
        assert fatal == [dict(event='Punt-entry', message='C097: Clip overflow %d', count=256)]
        assert len(overflow) == 1
        assert overflow[0] == dict(event='scratch-overrun', tag='tmprects', displacement=2050,
            bytes=2, value=0x8000, pc='1D8E:02AD')
        assert events.index(overflow[0]) < events.index(fatal[0])
    tail = m.read(tmp['address']+2048, 8).hex()
    assert tail == ('7a7a7a7a7a7a7a7a' if bars == 14 else '7a7a00807a7a7a7a')
    return dict(bars_per_axis=bars, windows=len(rects), completed=m.completed,
        visible_rectangles=len(visible), pairwise_nonoverlap=True,
        scratch_allocations=[dict(tag=row['tag'], bytes=row['size']) for row in list(allocs.values())[:2]],
        boundary_events=[event for event in events if event['event'] in ('scratch-overrun', 'Punt-entry')],
        tmp_tail=tail)

def controls():
    verify_inputs()
    return [execute(14), execute(15)]

def probe():
    cases = controls()
    paths = [*SOURCE_PINS, 'src/program.json', 'layout/oracle.lock.json',
        'layout/functions.json', 'layout/symbols.json', 'tools/behavior.py',
        'tools/exe.py', 'tools/functions.py', 'tools/match.py', 'tools/workspace.py',
        'evidence/canonical/clip-domain/replay.py', 'evidence/canonical/clip-domain/review.md']
    return dict(schema='simant-clip-precheck-control-v1', admitted=False,
        oracle_sha256=ORACLE_PIN,
        inputs={path: hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in paths},
        unicorn_version=b.uc.__version__, cases=cases,
        executed_original_bodies=['f_1E57_038E', 'f_1E57_0009', 'f_1E57_0006', 'f_1E57_0007',
            'f_1D8E_02BD', 'f_1D8E_003F', 'f_1D8E_0002'],
        modeled_boundaries=['heap allocation/lock/unlock/reallocation/free', 'window rectangle lookup', 'far memcpy'],
        stop='Immediately before entering Punt; no fatal continuation or physical heap corruption claim.',
        limits='Synthetic window geometry and stack order. No shipped-resource reachability, fd_50F6_3C14 capacity, original allocation extent or standalone closure.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT/'build/current/tests/clip-domain')
    args = parser.parse_args()
    out = workspace.prepare_output(args.out, ROOT/'build/current/tests/clip-domain')
    report = probe()
    (out/'receipt.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(cases=report['cases'], receipt=str(out/'receipt.json')), indent=2))
