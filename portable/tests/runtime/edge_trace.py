"""Read-only edge-scroll progress/presentation observations; no inferior calls."""
import gdb
import hashlib
import json
import os

output = open(os.environ['SIMANT_TRACE_OUT'], 'w', encoding='utf-8')
presentations = 0
scrolls = 0
active_scrolls = set()


def emit(event, **fields):
    output.write(json.dumps({'event': event, **fields}, sort_keys=True) + '\n')
    output.flush()


def word(name):
    return int(gdb.parse_and_eval(name))


def stack():
    frames = []
    frame = gdb.newest_frame()
    while frame is not None:
        frames.append(frame.name())
        frame = frame.older()
    return frames


class Present(gdb.Breakpoint):
    def stop(self):
        global presentations
        try:
            presentations += 1
            # The caller is idle; read its already computed monotonic/virtual
            # time, without invoking SDL or a source service in the inferior.
            frame = gdb.newest_frame().older()
            now = int(frame.read_var('now'))
            data = {'elapsed_ns': now - word('app.started_ns'),
                    'replay_next': word('app.replay_next'),
                    'outer_loops': word('fd_50F6_383A'),
                    'mouse': [word('g_9122'), word('g_9124')],
                    'scroll_loop': bool(active_scrolls),
                    'busy': word('g_3DD4') & 255,
                    'cursor_busy': word('g_4333')}
            if data['busy'] or data['cursor_busy']:
                emit('unsafe-presentation', **data)
            if data['scroll_loop']:
                framebuffer = gdb.parse_and_eval('app.graphics.framebuffer')
                pixels = gdb.selected_inferior().read_memory(
                    int(framebuffer['pixels']), int(framebuffer['stride']) * int(framebuffer['height']))
                data['frame_sha256'] = hashlib.sha256(bytes(pixels)).hexdigest()
            emit('present', **data)
        except Exception as error:
            emit('trace-error', error=str(error))
        return False


class ScrollReturned(gdb.FinishBreakpoint):
    def __init__(self, frame, key):
        super().__init__(frame, internal=True)
        self.key = key

    def stop(self):
        active_scrolls.discard(self.key)
        emit('scroll-return', mouse=[word('g_9122'), word('g_9124')],
             outer_loops=word('fd_50F6_383A'), replay_next=word('app.replay_next'))
        return False


class Scroll(gdb.Breakpoint):
    def stop(self):
        global scrolls
        try:
            frame = gdb.newest_frame().older()
            if frame is None or frame.name() != 'f_00F8_01BE':
                return False
            key = int(frame.read_register('rsp'))
            if key in active_scrolls:
                return False
            x, y = word('g_9122'), word('g_9124')
            if x <= 1 or x >= 636 or y < 1 or y >= 476:
                active_scrolls.add(key)
                scrolls += 1
                emit('scroll-entry', mouse=[x, y], replay_next=word('app.replay_next'))
                ScrollReturned(frame, key)
        except Exception as error:
            emit('trace-error', error=str(error))
        return False


def stopped(event):
    if isinstance(event, gdb.SignalEvent):
        emit('signal', signal=event.stop_signal, stack=stack())


def exited(event):
    emit('inferior-exit', exit_code=getattr(event, 'exit_code', None),
         presentations=presentations, scrolls=scrolls)


gdb.events.stop.connect(stopped)
gdb.events.exited.connect(exited)
Present('portable_m1b73_sdl_application_input_present', internal=True)
Scroll('f_0250_0D10', internal=True)
