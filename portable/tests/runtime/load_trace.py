"""GDB-only read observations of the actual current Save/FileSelect/Load path.

No expression here calls a game function or writes source state. Python counters
and hashes are diagnostic state; the game owns every byte that the replay uses.
"""
from pathlib import Path
import gdb
import hashlib
import json
import os
import time

output = open(os.environ['SIMANT_TRACE_OUT'], 'w', encoding='utf-8')
saved_file = Path(os.environ['SIMANT_TRACE_ASSETS']) / 'a.ant'
inferior = gdb.selected_inferior()
started = time.monotonic()
calls = {}
load_reads = 0
read_breakpoint = None


def emit(event, **fields):
    output.write(json.dumps({'event': event,
                            'trace_elapsed_ms': int((time.monotonic() - started) * 1000),
                            **fields}, sort_keys=True) + '\n')
    output.flush()


def cstring(pointer):
    if not pointer:
        return None
    data = bytearray()
    for offset in range(100):
        byte = bytes(inferior.read_memory(pointer + offset, 1))[0]
        if not byte:
            return data.decode(errors='replace')
        data.append(byte)
    raise ValueError('unterminated diagnostic source string')


def file_receipt():
    data = saved_file.read_bytes()
    return {'path': str(saved_file), 'size': len(data),
            'sha256': hashlib.sha256(data).hexdigest()}


class ReadReturned(gdb.FinishBreakpoint):
    def __init__(self, call, count):
        super().__init__(gdb.newest_frame(), internal=True)
        self.call, self.count = call, count

    def stop(self):
        try:
            emit('LoadGame-read-return', call=self.call, requested=self.count,
                 returned=int(self.return_value))
        except Exception as error:
            emit('trace-error', function='dos_read', error=str(error))
        return False


class ReadEntry(gdb.Breakpoint):
    def __init__(self):
        super().__init__('dos_read', internal=True)

    def stop(self):
        global load_reads
        try:
            caller = gdb.newest_frame().older()
            if caller and caller.name() == 'LoadGame':
                load_reads += 1
                count = int(gdb.parse_and_eval('count'))
                emit('LoadGame-read-entry', call=load_reads, requested=count)
                ReadReturned(load_reads, count)
        except Exception as error:
            emit('trace-error', function='dos_read', error=str(error))
        return False


class Returned(gdb.FinishBreakpoint):
    def __init__(self, function, call, fields):
        super().__init__(gdb.newest_frame(), internal=True)
        self.function, self.call, self.fields = function, call, fields

    def stop(self):
        try:
            fields = dict(self.fields)
            result = int(self.return_value)
            if self.function == 'o09_35F5_03C6':
                pointer = fields.pop('name_pointer')
                fields['selected_path'] = cstring(pointer) if result else None
            if self.function in ('o09_35F5_0188', 'LoadGame') and result == 1:
                fields['saved_file'] = file_receipt()
            emit(self.function + '-return', call=self.call, result=result, **fields)
        except Exception as error:
            emit('trace-error', function=self.function, error=str(error))
        return False


class Entry(gdb.Breakpoint):
    def __init__(self, function):
        super().__init__(function, internal=True)
        self.function = function

    def stop(self):
        global read_breakpoint
        calls[self.function] = calls.get(self.function, 0) + 1
        fields = {}
        try:
            if self.function == 'o09_35F5_03C6':
                fields.update(title=cstring(int(gdb.parse_and_eval('title'))),
                              verb=cstring(int(gdb.parse_and_eval('verb'))),
                              save=int(gdb.parse_and_eval('save')),
                              name_pointer=int(gdb.parse_and_eval('name')))
            if self.function == 'o09_35F5_0188':
                fields['use_last'] = int(gdb.parse_and_eval('useLast'))
            if self.function == 'LoadGame' and read_breakpoint is None:
                read_breakpoint = ReadEntry()
            emit(self.function + '-entry', call=calls[self.function],
                 **{key: value for key, value in fields.items() if key != 'name_pointer'})
            Returned(self.function, calls[self.function], fields)
        except Exception as error:
            emit('trace-error', function=self.function, error=str(error))
        return False


def exited(event):
    emit('inferior-exit', exit_code=getattr(event, 'exit_code', None),
         calls=calls, load_reads=load_reads)


for function in ('o09_35F5_0188', 'o09_35F5_03C6', 'LoadGame'):
    Entry(function)
gdb.events.exited.connect(exited)
emit('trace-installed', scope='Read-only breakpoints, source return values and file hashes; '
                            'no game calls or state writes.')
