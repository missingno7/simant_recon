"""Unmodified FileSelect prefix and locked object lookup: C:/K: controls.

The prefix stops at its first selection consumer. The real DOS drive-directory
body executes; INT21 AH47 is an explicit successful-directory service model.
UI/allocator/drawing calls are models. A separate original RepointObjects and
win_ObjAddr sequence uses the actual shipped window, with explicit locked/window
lookup services and returning Punt. This is a bounded environmental-domain
counterexample, not a full-game execution witness or admitted failure behavior.
"""
from pathlib import Path
from types import SimpleNamespace
import json
import struct
import sys
sys.dont_write_bytecode = True
ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'src/program.json').is_file())
sys.path.insert(0, str(ROOT / 'tools'))
import behavior as b
import exe
import functions
import resource_domains as r

class ConsumerReached(Exception):
    pass

class FatalExitReached(Exception):
    pass

class PrefixMachine(b.Machine):
    def _on_interrupt(self, cpu, number, userdata):
        if number != 0x21 or self.reg('ax') >> 8 != 0x47:
            return super()._on_interrupt(cpu, number, userdata)
        self.state.setdefault('get_directory_calls', []).append(self.reg('dx') & 255)
        self.write(self.reg('ds') * 16 + self.reg('si'), b'WORK\0')
        self.set_reg('eflags', self.reg('eflags') & ~1)

def case(drive):
    def memset(machine, args):
        machine.write(args[1] * 16 + args[0], bytes([args[2] & 255]) * args[3])
        return args[0], args[1]
    def rectangle(machine, args):
        machine.write(args[2] * 16 + args[1], b.words(0, 0, 300, 200))
    def selected(machine, args):
        machine.state['selected_argument'] = args[0]
        raise ConsumerReached('bounded prefix completed at first selection consumer')
    no = lambda machine, args: None
    image = exe.load()
    pair = SimpleNamespace(function=functions.get('o09_35F5_03C6'),
        vectors={exe.MANAGER_SEG * 16 + v.offset: v for v in image.vectors},
        identity={'oracle_sha256': image.sha256})
    machine = PrefixMachine(pair)
    callbacks = {'chdir': b.Callback(2, lambda m, a: 0),
        'f_171C_13CA': b.Callback(5, lambda m, a: (0, 0xa000)),
        '__fmemset': b.Callback(4, memset),
        'win_LockWin': b.Callback(0, no, ('ax',)),
        'win_SetObjFormatStr': b.Callback(3, no),
        'f_22BF_00AA': b.Callback(2, rectangle, ('ax',), pop=4),
        'win_MakeGroupSelectable': b.Callback(0, no, ('ax', 'dx')),
        'win_MakeGroupVisible': b.Callback(0, no, ('ax', 'dx')),
        'win_Open': b.Callback(1, no),
        'win_DrawObjectNum': b.Callback(0, no, ('ax',)),
        'win_MakeObjSelected': b.Callback(0, selected, ('ax',))}
    input_case = b.Case(label='FileSelect-successful-drive-' + drive,
        args=[0, 0xa200, 20, 0xa200, 40, 0xa200, 1], callbacks=callbacks,
        writes=[(0xa000 * 16, b.words(0, 0xa100)), (0xa100 * 16, bytes(0xc80)),
                (0xa200 * 16, bytes(80)), (0x55b3 * 16 + 0x2966, b.words(0)),
                (0x50f6 * 16 + 0x38b6, b.words(ord(drive))),
                (0x410, bytes([0xc0]))])
    try:
        machine.run(input_case)
    except b.ExecutionError as error:
        if not isinstance(error.__cause__, ConsumerReached):
            raise
    else:
        raise ValueError('prefix did not reach selection consumer')
    argument = machine.state['selected_argument']
    return dict(drive=drive, successful_directory_calls=machine.state['get_directory_calls'],
        selected_argument=argument, window=argument >> 8, object=argument & 255,
        blocks=machine.blocks, stop='first win_MakeObjSelected consumer; no object body executed')

def object_case(argument):
    raw = next(x['payload'] for x in r.decoder().parse_records('HCEGANT')[1]
               if (x['id'], x['kind']) == (22, 0))
    domain = r.window_domain(raw)
    image = exe.load()
    pair = SimpleNamespace(function=functions.get('RepointObjects'),
        vectors={exe.MANAGER_SEG * 16 + v.offset: v for v in image.vectors},
        identity={'oracle_sha256': image.sha256})
    machine = b.Machine(pair)
    lookup = b.Callback(1, lambda m, a: (0, 0xa300))
    machine.run(b.Case(label='original-window-object-repoint', registers={'ax': 0x1600},
        callbacks={'f_2505_0006': lookup}, writes=[(0xa300 * 16, raw)], return_kind='void'))
    def punt(machine, args):
        at = args[1] * 16 + args[0]
        text = machine.read(at, 100).split(b'\0')[0].decode('ascii')
        machine.state.setdefault('diagnostics', []).append(text)
        return 0
    result = machine.run(b.Case(label='original-locked-object-consumer',
        registers={'ax': argument}, callbacks={'f_2505_0006': lookup,
            'win_IsWinLocked': b.Callback(0, lambda m, a: 1, ('ax',)),
            'Punt': b.Callback(2, punt)}, return_kind='farptr'),
        preserve=True, original_entry=functions.get('win_ObjAddr'))
    valid = {0xa300 << 16 | x['offset'] for x in domain['objects']}
    return dict(argument=argument, count=len(domain['objects']),
        diagnostics=machine.state.get('diagnostics', []),
        pointer_is_shipped_object=result['return'] in valid,
        failure_model='Punt explicitly returns for this separate continuation control')

def controls():
    positive, contrast = case('C'), case('K')
    positive['consumer'] = object_case(positive['selected_argument'])
    contrast['consumer'] = object_case(contrast['selected_argument'])
    if positive['selected_argument'] != 0x160d or not positive['consumer']['pointer_is_shipped_object'] or positive['consumer']['diagnostics']:
        raise ValueError('successful C: positive control changed')
    if contrast['selected_argument'] != 0x1615 or contrast['consumer']['pointer_is_shipped_object'] or contrast['consumer']['diagnostics'] != ['Attempt to get obj address outsize window']:
        raise ValueError('successful K: out-of-range contrast changed')
    return [positive, contrast]

def fatal_case(already_reporting):
    """Actual Punt -> S15 -> Pascal stub, stopping at the CRT exit boundary.

    Formatters, drawing, and cleanup calls are explicit models. The negative
    contrast sets Punt's reentrancy guard: that path returns without shutdown.
    This does not license replacing a first fatal error by a returning callback.
    """
    image = exe.load()
    pair = SimpleNamespace(function=functions.get('Punt'),
        vectors={exe.MANAGER_SEG * 16 + v.offset: v for v in image.vectors},
        identity={'oracle_sha256': image.sha256})
    machine = b.Machine(pair)
    no = lambda machine, args: 0
    def formatter(machine, args):
        machine.write(args[1] * 16 + args[0], b'modeled diagnostic\0')
        return 18
    def exit_boundary(machine, args):
        machine.state['exit_code'] = args[0]
        raise FatalExitReached('original shutdown reached CRT exit')
    draw = b.symbol('f_277D_000B')
    callbacks = {'vsprintf': b.Callback(6, formatter),
        'sprintf': b.Callback(6, formatter), 'printf': b.Callback(2, no),
        'f_277D_000B': b.Callback(3, no),
        'f_1CE2_01C3': b.Callback(4, no),
        '__aFchkstk': b.Callback(0, no),
        'f_171C_0676': b.Callback(1, no), 'f_171C_030C': b.Callback(2, no),
        'f_1C62_00A1': b.Callback(0, no), 'f_1C62_0090': b.Callback(0, no),
        'puts': b.Callback(2, no), 'exit': b.Callback(1, exit_boundary)}
    reached = False
    try:
        machine.run(b.Case(label='original-Punt-first-fatal' if not already_reporting else 'original-Punt-reentrant',
            args=[0, 0xa400], callbacks=callbacks, return_kind='void', writes=[
                (0xa400 * 16, b'window object diagnostic\0'),
                (0x55b3 * 16 + 0x54f8, b.words(already_reporting)),
                (0x55b3 * 16 + 0x2bd4, b.words(1)),
                (0x55b3 * 16 + 0x610a, b.words(0)),
                (b.symbol_address('g_9128'), b.words(draw['off'], draw['seg']))]))
    except b.ExecutionError as error:
        if not isinstance(error.__cause__, FatalExitReached):
            raise
        reached = True
    return dict(initial_reporting_guard=already_reporting, reaches_CRT_exit=reached,
        exit_code=machine.state.get('exit_code'), blocks=machine.blocks,
        executes_original_shutdown=True if reached else False,
        models='formatters, drawing, stack check and shutdown cleanup; CRT exit is a terminal boundary')

def fatal_controls():
    positive, contrast = fatal_case(0), fatal_case(1)
    if not positive['reaches_CRT_exit'] or positive['exit_code'] != 0:
        raise ValueError('first fatal error did not reach original CRT exit call')
    if contrast['reaches_CRT_exit']:
        raise ValueError('reentrant diagnostic unexpectedly entered shutdown')
    return [positive, contrast]

if __name__ == '__main__':
    print(json.dumps(dict(drive_controls=controls(), fatal_controls=fatal_controls()), indent=2))
