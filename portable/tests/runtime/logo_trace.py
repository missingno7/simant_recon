"""Read-only GDB observations of startup waits; no inferior calls or writes."""
import gdb
import json
import os
import time

output = open(os.environ['SIMANT_TRACE_OUT'], 'w', encoding='utf-8')
started = time.monotonic()
calls = {}


def emit(event, **fields):
    output.write(json.dumps({'event': event,
                            'trace_elapsed_ms': int((time.monotonic() - started) * 1000),
                            **fields}, sort_keys=True) + '\n')
    output.flush()


def state():
    return {'mouse_status': int(gdb.parse_and_eval('g_9120')),
            'replay_next': int(gdb.parse_and_eval('app.replay_next')),
            'source_window': int(gdb.parse_and_eval('((short *)&g_5702)[0]')) & 0xffff,
            'space_down': int(gdb.parse_and_eval('app.host->dos_scan_down[57]')),
            'insert_down': int(gdb.parse_and_eval('app.host->dos_scan_down[82]')),
            'delete_down': int(gdb.parse_and_eval('app.host->dos_scan_down[83]'))}


class Returned(gdb.FinishBreakpoint):
    def __init__(self, function, call):
        super().__init__(gdb.newest_frame(), internal=True)
        self.function, self.call = function, call

    def stop(self):
        try:
            emit(self.function + '-return', call=self.call, **state())
        except Exception as error:
            emit('trace-error', function=self.function, error=str(error))
        return False


class Entry(gdb.Breakpoint):
    def __init__(self, function):
        super().__init__(function, internal=True)
        self.function = function

    def stop(self):
        calls[self.function] = calls.get(self.function, 0) + 1
        try:
            fields = state()
            if self.function == 'DialogWaitInit':
                fields['secs'] = int(gdb.parse_and_eval('secs'))
            emit(self.function + '-entry', call=calls[self.function], **fields)
            Returned(self.function, calls[self.function])
        except Exception as error:
            emit('trace-error', function=self.function, error=str(error))
        return False


def exited(event):
    emit('inferior-exit', exit_code=getattr(event, 'exit_code', None), calls=calls)


gdb.events.exited.connect(exited)
for function in ('ShowIntro', 'CustomerIDDialog', 'DialogWaitInit'):
    Entry(function)
