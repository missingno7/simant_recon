import gdb
import json

OUT = r'D:\Prog\simant_recon\build\workers\whole_runtime_flow_review\v17_title_drag\events.jsonl'
f = open(OUT, 'w', encoding='utf-8')
inf = gdb.selected_inferior()
counts = {'drag': 0, 'buttonheld': 0, 'stilldown': 0, 'opens': 0}
last_mouse = None


def emit(kind, **fields):
    f.write(json.dumps({'event': kind, **fields}, sort_keys=True) + '\n')
    f.flush()


def val(expr):
    return int(gdb.parse_and_eval(expr))


def read(ptr, size):
    return bytes(inf.read_memory(int(ptr), size))


def i16(data, offset):
    return int.from_bytes(data[offset:offset + 2], 'little', signed=True)


def snapshot(tag):
    try:
        base = val('(uintptr_t)sim_window_ref_registry.entries[0].view.wire')
        count = val('sim_window_ref_registry.entries[0].view.count')
        objects = val('(uintptr_t)sim_window_ref_registry.entries[0].view.object_table')
        if base == 0 or objects == 0:
            emit('snapshot-error', tag=tag, base=base, objects=objects, count=count)
            return
        wire = read(base, 0x30)
        table = read(objects, count * 8)
        object_ptrs = [int.from_bytes(table[i * 8:(i + 1) * 8], 'little')
                       for i in range(min(count, 4))]
        first = read(object_ptrs[0], 0x28) if object_ptrs else b''
        second = read(object_ptrs[1], 0x28) if len(object_ptrs) > 1 else b''
        emit('window-snapshot', tag=tag, base=hex(base), count=count,
             outer_rect=[i16(wire, k) for k in (0, 2, 4, 6)],
             object_ptrs=[hex(x) for x in object_ptrs],
             first_object_rect=[i16(first, k) for k in (0, 2, 4, 6)] if first else None,
             first_object_xywh=[i16(first, k) for k in (8, 10, 12, 14)] if first else None,
             second_type=second[0x21] if second else None,
             first_bytes=first.hex(), second_bytes=second.hex())
    except Exception as exc:
        emit('snapshot-error', tag=tag, error=str(exc))


class Open(gdb.Breakpoint):
    def __init__(self):
        super().__init__('win_Open', internal=True)

    def stop(self):
        counts['opens'] += 1
        try:
            emit('win-open', count=counts['opens'], win=val('$rcx') & 0xffff)
        except Exception as exc:
            emit('win-open-error', error=str(exc))
        return False


class DragFinish(gdb.FinishBreakpoint):
    def __init__(self):
        super().__init__(gdb.newest_frame(), internal=True)

    def stop(self):
        snapshot('after-drag-return')
        emit('drag-return', value=int(self.return_value) if self.return_value else None)
        return False


class Drag(gdb.Breakpoint):
    def __init__(self):
        super().__init__('o26_39C7_040F', internal=True)

    def stop(self):
        counts['drag'] += 1
        try:
            ev = val('$rcx')
            data = read(ev, 16)
            words = [i16(data, i) for i in range(0, 16, 2)]
            emit('drag-entry', count=counts['drag'], event_words=words,
                 front=val('g_5702[0]'), mouse=[val('g_9122'), val('g_9124')],
                 registry_count=val('sim_window_ref_registry.entries[0].view.count'))
            snapshot('before-drag')
            DragFinish()
        except Exception as exc:
            emit('drag-entry-error', error=str(exc))
        return False


class ButtonHeld(gdb.Breakpoint):
    def __init__(self):
        super().__init__('ButtonHeld', internal=True)

    def stop(self):
        global last_mouse
        counts['buttonheld'] += 1
        try:
            mouse = [val('g_9122'), val('g_9124')]
            if mouse != last_mouse:
                emit('mouse-poll-coordinate', count=counts['buttonheld'], mouse=mouse,
                     front=val('g_5702[0]'))
                last_mouse = mouse
        except Exception as exc:
            emit('mouse-poll-error', error=str(exc))
        return False


class StillDown(gdb.Breakpoint):
    def __init__(self):
        super().__init__('StillDown', internal=True)

    def stop(self):
        counts['stilldown'] += 1
        if counts['stilldown'] < 5:
            emit('still-down-poll', count=counts['stilldown'])
        return False


Open()
Drag()
ButtonHeld()
StillDown()
emit('probe-start', executable=gdb.current_progspace().filename,
     replay='quick-game-title-drag-v1.txt', method='read-only symbols/memory snapshots; no inferior calls or state writes')


def done(event):
    snapshot('process-exit')
    emit('summary', **counts)
    f.close()


gdb.events.exited.connect(done)
