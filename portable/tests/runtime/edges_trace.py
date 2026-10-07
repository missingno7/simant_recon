"""Read-only witnesses for exterior drawing, RAM sprite offsets and map motion."""
import gdb
import json
import os

stream = open(os.environ['SIMANT_TRACE_OUT'], 'w', encoding='utf-8')
counts = {'tile_exterior': 0, 'sprite_offset': 0, 'window_returns': 0}
origins = set()
map_edges = set()

def emit(event, **fields):
    stream.write(json.dumps({'event': event, **fields}) + '\n')
    stream.flush()

def value(name):
    return int(gdb.parse_and_eval(name))

def stack():
    rows = []
    frame = gdb.newest_frame()
    while frame:
        loc = frame.find_sal()
        rows.append({'function': frame.name(), 'line': loc.line,
                     'file': loc.symtab.fullname() if loc.symtab else None})
        frame = frame.older()
    return rows

class Return(gdb.FinishBreakpoint):
    def stop(self):
        counts['window_returns'] += 1
        emit('window-return', rectangle=[value('fd_50F6_110C.' + f)
             for f in ('left', 'top', 'right', 'bottom')])
        return False

class Observe(gdb.Breakpoint):
    def __init__(self, function, kind):
        super().__init__(function, internal=True)
        self.kind = kind

    def stop(self):
        try:
            if self.kind == 'start':
                emit('start', pid=gdb.selected_inferior().pid)
                self.enabled = False
            elif self.kind == 'window':
                Return(gdb.newest_frame(), internal=True)
            elif self.kind == 'tile':
                x, y = value('x'), value('y')
                if x < 0 or x >= 640 or y < 0 or y >= 480:
                    counts['tile_exterior'] += 1
                    if counts['tile_exterior'] <= 8:
                        emit('tile-exterior', x=x, y=y, offset=value('offset'))
            elif self.kind == 'sprite':
                shift = value('shift')
                offset = value('row_offset')
                if offset > 1 or shift > 15:
                    counts['sprite_offset'] += 1
                    if counts['sprite_offset'] <= 8:
                        emit('sprite-offset', shift=shift, row_offset=offset)
            elif self.kind == 'map':
                origin = (value('fd_50F6_0508.x'), value('fd_50F6_0508.y'))
                width = 128 if value('MapPlane') <= 1 else 64
                limit = (width - value('fd_50F6_10E0'), 64 - value('fd_50F6_10DE'))
                if (origin[0] == 0 or origin[1] == 0 or
                        origin[0] == limit[0] or origin[1] == limit[1]):
                    map_edges.add(origin)
                if origin not in origins:
                    origins.add(origin)
                    emit('map-origin', x=origin[0], y=origin[1], limit=limit)
            else:
                emit('abort', counts=counts, stack=stack())
        except Exception as error:
            emit('trace-error', error=str(error), kind=self.kind)
        return False

def exited(event):
    emit('exit', code=getattr(event, 'exit_code', None), counts=counts,
         origins=sorted(origins), map_edges=sorted(map_edges))

def stopped(event):
    if isinstance(event, gdb.SignalEvent):
        emit('signal', signal=event.stop_signal, stack=stack())

gdb.events.exited.connect(exited)
gdb.events.stop.connect(stopped)
Observe('o26_39C7_040F', 'window')
Observe('o00_31AD_0647', 'tile')
Observe('o00_35A6_0007', 'sprite')
Observe('UpdateEdit', 'map')
Observe('abort', 'abort')
Observe('main', 'start')
