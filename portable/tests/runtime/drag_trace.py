"""Read-only tracking/presentation and fault observations; no inferior calls."""
import gdb
import hashlib
import json
import os

output = open(os.environ['SIMANT_TRACE_OUT'], 'w', encoding='utf-8')
active = []
calls = []
presented = 0


def emit(event, **fields):
    output.write(json.dumps({'event': event, **fields}, sort_keys=True) + '\n')
    output.flush()


def word(name):
    return int(gdb.parse_and_eval(name))


def stack():
    """Avoid decoding binary cursor buffers as strings in GDB's bt output."""
    frames = []
    frame = gdb.newest_frame()
    while frame is not None:
        location = frame.find_sal()
        fields = {'function': frame.name(), 'line': location.line}
        if location.symtab:
            fields['file'] = location.symtab.fullname()
        if frame.name() == 'source_g9148_capture':
            fields['rectangle'] = [int(frame.read_var(name)) for name in
                                   ('left', 'top', 'right', 'bottom')]
        frames.append(fields)
        frame = frame.older()
    return frames


class Returned(gdb.FinishBreakpoint):
    def __init__(self, track):
        super().__init__(gdb.newest_frame(), internal=True)
        self.track = track

    def stop(self):
        if self.track in active:
            active.remove(self.track)
        self.track['returned'] = True
        emit('track-return', **self.track)
        return False


class Track(gdb.Breakpoint):
    def __init__(self, function, kind):
        super().__init__(function, internal=True)
        self.kind = kind

    def stop(self):
        try:
            if self.kind == 'triangle' and word('msg->code') != 0x130d:
                return False
            track = {'call': len(calls) + 1, 'kind': self.kind,
                     'presentations': 0, 'active_clip_presentations': 0,
                     'frames': [], 'returned': False}
            calls.append(track)
            active.append(track)
            emit('track-entry', call=track['call'], kind=self.kind)
            Returned(track)
        except Exception as error:
            emit('trace-error', error=str(error))
        return False


class Present(gdb.Breakpoint):
    def stop(self):
        global presented
        presented += 1
        try:
            busy = word('g_3DD4') & 255
            cursor_busy = word('g_4333')
            now = int(gdb.newest_frame().older().read_var('now'))
            previous = word('app.last_present')
            if busy or cursor_busy or now - previous < 16666667:
                emit('unsafe-presentation', busy=busy, cursor_busy=cursor_busy,
                     interval_ns=now - previous)
            if not active or not (word('g_9120') & 1):
                return False
            framebuffer = gdb.parse_and_eval('app.graphics.framebuffer')
            pixels = gdb.selected_inferior().read_memory(
                int(framebuffer['pixels']), int(framebuffer['stride']) * int(framebuffer['height']))
            digest = hashlib.sha256(bytes(pixels)).hexdigest()
            for track in active:
                track['presentations'] += 1
                if int(gdb.parse_and_eval('g_5AAC')):
                    track['active_clip_presentations'] += 1
                if digest not in track['frames']:
                    track['frames'].append(digest)
        except Exception as error:
            emit('trace-error', error=str(error))
        return False


class Mouse(gdb.Breakpoint):
    def stop(self):
        try:
            event = gdb.parse_and_eval('*event')
            x, y = int(event['x']), int(event['y'])
            if x < 0 or y < 0 or x > 636 or y > 476:
                # Entry at callback: the host coordinate mapping/driver limits
                # have completed; inspect source args via a finish observer.
                MouseReturned(x, y)
        except Exception as error:
            emit('trace-error', error=str(error))
        return False


class MouseReturned(gdb.FinishBreakpoint):
    def __init__(self, x, y):
        super().__init__(gdb.newest_frame(), internal=True)
        self.x, self.y = x, y

    def stop(self):
        emit('exterior-mouse-return', host_x=self.x, host_y=self.y,
             source_x=word('g_9122'), source_y=word('g_9124'))
        return False


class Exit(gdb.Breakpoint):
    def stop(self):
        # This runtime target uses the Windows x64 ABI: exit's first argument
        # is in RCX even when the CRT has no parameter debug information.
        status = word('$rcx')
        if status:
            emit('abnormal-exit', status=status, stack=stack())
        return False


def stopped(event):
    if isinstance(event, gdb.SignalEvent):
        emit('signal', signal=event.stop_signal, stack=stack())


def exited(event):
    emit('inferior-exit', exit_code=getattr(event, 'exit_code', None),
         presentations=presented, tracks=calls)


gdb.events.stop.connect(stopped)
gdb.events.exited.connect(exited)
Track('o26_39C7_040F', 'window')
Track('o26_39C7_0671', 'resize')
Track('ProcCasteEvent', 'triangle')
Present('portable_m1b73_sdl_application_input_present', internal=True)
Mouse('portable_m1b73_mouse_consume_event', internal=True)
Exit('exit', internal=True)
