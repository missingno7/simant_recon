"""Read-only GDB trace of bounded pointer-free state and completed frame inputs."""
import gdb
import hashlib
import json
import os

output = open(os.environ['SIMANT_IDLE_TRACE'], 'w')
arrays = {'MapA':8192, 'MapB':4096, 'MapR':4096,
          'LifeA':8192, 'LifeB':4096, 'LifeR':4096,
          **{prefix+axis: count for prefix, count in [('Alist',1001), ('Blist',501), ('Rlist',501)]
             for axis in 'XYMTS'}}
scalars = ['MeLocX', 'MeLocY', 'MePlane', 'MeHealth', "'root_0093.c'::seed",
           'GameSpeed', 'GamePaused', 'midi_service_countdown', 'midi_playback_state']

def value(expression):
    try:
        return int(gdb.parse_and_eval(expression))
    except Exception as error:
        raise ValueError(expression+': '+str(error))

def emit(row):
    output.write(json.dumps(row, sort_keys=True)+'\n')
    output.flush()

class Step(gdb.Breakpoint):
    def stop(self):
        try:
            h = hashlib.sha256()
            for name, size in arrays.items():
                h.update(bytes(gdb.selected_inferior().read_memory(value('&'+name), size)))
            # Canonical cross-TU byte/word views can give GDB an array type.
            # These listed scalars are DOS words; observe their two bytes.
            words = {name:int.from_bytes(bytes(gdb.selected_inferior().read_memory(
                value('&'+name), 2)), 'little') for name in scalars}
            h.update(json.dumps(words, sort_keys=True).encode())
            emit(dict(kind='step', step=value('main_iteration_count'), state_sha256=h.hexdigest(),
                      ns=value('virtual_ns'), ticks=value('app.game_clock.tick_count'),
                      speed=words['GameSpeed'], delay=int.from_bytes(bytes(
                          gdb.selected_inferior().read_memory(value('&GameSpeed')+2+2*words['GameSpeed'], 2)), 'little')))
        except Exception as error:
            emit(dict(kind='error', error=str(error)))
        return False

class Frame(gdb.Breakpoint):
    def stop(self):
        try:
            frame = gdb.newest_frame()
            pixels, stride = int(frame.read_var('pixels')), int(frame.read_var('stride'))
            palette = int(frame.read_var('palette'))
            data = bytes(gdb.selected_inferior().read_memory(pixels, stride*value('app.graphics.framebuffer.height')))
            data += bytes(gdb.selected_inferior().read_memory(palette, 48))
            emit(dict(kind='frame', step=value('main_iteration_count'), ns=value('virtual_ns'),
                      frame_sha256=hashlib.sha256(data).hexdigest()))
        except Exception as error:
            emit(dict(kind='error', error=str(error)))
        return False

Step('DoAntSim', internal=True)
Frame('host_present', internal=True)
