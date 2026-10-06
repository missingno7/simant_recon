"""Read-only original local window-ID controls; modeled drawing boundaries."""
from pathlib import Path
from types import SimpleNamespace
import hashlib
import importlib.util
import json
import re
import struct
import sys

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'src/program.json').is_file())
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'tools'))
import behavior as b
import exe
import functions

TOKENS = {'ToggleHistButton', 'ProcHistoryEvent', 'shownGraphs', 'histColor', 'histShown',
          'freeColors', 'SetYardMode', 'YardMode', 'fd_50F6_035C', 'g_1984',
          'SetMapModeAnt', 'g_1960', 'DrawEditGraphs', 'ScoreDialog', 'CalcScore',
          'SetMapPlaneLocation', 'LoadGame', 'SaveGame'}
TOKENS |= {'PrepareStrings', 'LoadStringAnt', 'fd_50F6_0EAC', 'fd_50F6_38B6', 's_2966'}
if not __debug__: raise RuntimeError('proof checks require Python without -O')


def coverage(source_overrides=None, symbols_override=None, program_aliases_override=None):
    source_overrides = source_overrides or {}
    symbols = symbols_override or json.loads((ROOT / 'layout/symbols.json').read_text())
    registry = {**symbols['code'], **symbols['data']}
    aliases = (program_aliases_override if program_aliases_override is not None else
               json.loads((ROOT/'src/program.json').read_text())['aliases'])
    def source_name(linker_name):
        # One linker decoration, not lstrip: __name represents source _name.
        return linker_name[1:] if linker_name[:1] in ('_', '@') else linker_name
    relevant = set(TOKENS)
    while True:
        added = {n for n, row in registry.items() if row.get('alias_of') in relevant}
        for row in aliases:
            a, target = source_name(row['alias']), source_name(row['target'])
            if a in relevant or target in relevant:
                added.update((a, target))
        if added <= relevant:
            break
        relevant |= added
    pattern = r'(?<!\w)[_@]?(?:' + '|'.join(re.escape(n) for n in sorted(relevant)) + r')\b'
    rx, asm_rx = re.compile(pattern), re.compile(pattern, re.I)
    pins = []
    sources = {p.relative_to(ROOT).as_posix(): p.read_bytes() for p in (ROOT/'src').rglob('*')
               if p.suffix.lower() in ('.c', '.asm')}
    sources.update({n: v.encode() if isinstance(v, str) else v for n, v in source_overrides.items()})
    for path, raw in sorted(sources.items()):
        if (asm_rx if path.lower().endswith('.asm') else rx).search(raw.decode()):
            pins.append({'path': path, 'sha256': hashlib.sha256(raw).hexdigest()})
    return {'source_pins': pins,
            'code_aliases': {n: {k: registry[n][k] for k in ('unit', 'seg', 'off', 'alias_of')
                                if k in registry[n]} for n in sorted(relevant) if n in symbols['code']},
            'data_aliases': {n: {k: registry[n][k] for k in ('seg', 'off', 'alias_of')
                                if k in registry[n]} for n in sorted(relevant) if n in symbols['data']},
            'program_aliases': sorted(
                ({k: r[k] for k in ('alias', 'target', 'offset', 'kind') if k in r} for r in aliases
                 if source_name(r['target']) in relevant or source_name(r['alias']) in relevant),
                key=lambda r: r['alias'])}


def run():
    image = exe.load()
    vectors = {exe.MANAGER_SEG * 16 + v.offset: v for v in image.vectors}
    ds = 0x55B3 * 16
    def machine(name):
        return b.Machine(SimpleNamespace(function=functions.get(name), vectors=vectors))
    def no(*args):
        return 0, 0
    def callback(n=0, regs=()):
        return b.Callback(n, no, register_args=regs)
    initial = machine('ToggleHistButton')
    assert initial.read(ds+0x2EF0, 10) == b.words(0x8000, 0x8000, 0x8000, 0x8000, 15)
    assert initial.read(ds+0x8C26, 40) == bytes(40)
    assert initial.read(ds+0x8C4E, 10) == bytes(10)
    history = []
    for g in range(10):
        for position in range(4):
            active = [g] + [n for n in range(10) if n != g][:3]
            active[0], active[position] = active[position], active[0]
            flags = bytes(int(n in active) for n in range(10))
            colors = [active.index(n) if n in active else 0 for n in range(20)]
            copies = []
            def copy(m, a):
                dst, src = a[1] * 16 + a[0], a[3] * 16 + a[2]
                copies.append({'source': src - ds, 'destination': dst - ds, 'size': a[4]})
                m.write(dst, m.read(src, a[4]))
                return a[0], a[1]
            m = machine('ToggleHistButton')
            m.run(b.Case('history removal', args=[0x1503 + g], writes=[
                (ds + 0x2EF0, b.words(*active, 0)),
                (ds + 0x8C26, b.words(*colors)), (ds + 0x8C4E, flags)],
                callbacks={'clip_SetWin': callback(1), 'clip_Off': callback(),
                           'win_DrawHistoryWindow': callback(1), '_fmemmove': b.Callback(5, copy),
                           'win_MakeObjUnselected': callback(regs=('ax',))}, return_kind='void'))
            got = list(struct.unpack('<4H', m.read(ds + 0x2EF0, 8)))
            assert got == [n for n in active if n != g] + [0x8000]
            assert m.read(ds + 0x2EF8, 2) == b.words(1 << position)
            assert m.read(ds + 0x8C4E + g, 1) == b'\0'
            assert copies == [{'source': 0x2EF2 + 2*position,
                               'destination': 0x2EF0 + 2*position, 'size': (4-position)*2}]
            assert copies[0]['source'] + copies[0]['size'] == 0x2EFA
            history.append({'item': 0x1503 + g, 'removal_position': position,
                            'remaining': got, 'read_past_shownGraphs': 2})
    evictions = []
    for g in range(10):
        active = [n for n in range(10) if n != g][:4]
        colors = [active.index(n) if n in active else 0 for n in range(20)]
        m = machine('ToggleHistButton')
        def copy(m, a):
            m.write(a[1]*16+a[0], m.read(a[3]*16+a[2], a[4]))
            return a[0], a[1]
        m.run(b.Case('history eviction', args=[0x1503+g], writes=[
            (ds+0x2EF0, b.words(*active, 0)), (ds+0x8C26, b.words(*colors)),
            (ds+0x8C4E, bytes(int(n in active) for n in range(10)))],
            callbacks={'clip_SetWin': callback(1), 'clip_Off': callback(),
                       'win_DrawHistoryWindow': callback(1), '_fmemmove': b.Callback(5, copy),
                       'win_MakeObjUnselected': callback(regs=('ax',))}, return_kind='void'))
        ids = [r['args'][0] for r in m.raw_trace if r['name'] == 'win_MakeObjUnselected']
        assert ids == [0x1503 + active[3]]
        assert list(struct.unpack('<4H', m.read(ds+0x2EF0, 8))) == [g] + active[:3]
        evictions.append({'item': 0x1503+g, 'unselected': ids[0]})
    events = []
    for code in [0x1502] + list(range(0x1503, 0x150D)) + [0x150F]:
        m = machine('ProcHistoryEvent')
        m.run(b.Case('history event guard', args=[0, 0x7000],
            writes=[(0x70000, b.words(0, 0, 0, 0, 0, 0, code, 0))],
            callbacks={'ToggleHistButton': callback(1)}, return_kind='void'))
        ids = [r['args'][0] for r in m.raw_trace if r['name'] == 'ToggleHistButton']
        assert ids == ([code] if 0x1503 <= code <= 0x150C else [])
        events.append({'code': code, 'toggle_items': ids})
    yard = []
    for mode in range(6):
        m = machine('SetYardMode')
        callbacks = {n: callback() for n in ('win_YardClosed', 'clip_Push', 'clip_Pop', 'DrawYard', 'SetMapTitle')}
        callbacks.update({n: callback(regs=('ax',)) for n in ('win_LockWin', 'win_UnlockWin',
            'win_MakeObjInvisible', 'win_MakeObjVisible', 'win_IsWinOpen', 'win_DrawObjectNum', 'win_MakeObjSelected')})
        callbacks.update({'win_SetObjBitmap': callback(regs=('ax', 'dx')), 'win_Swap': callback(2),
                          'clip_SetWin': callback(1), 'WinPrintf': callback(4), 'SetMapPlane': callback(1)})
        m.run(b.Case('yard mode selector', args=[mode], writes=[(0x50F6*16+0x35C, b.words(0)),
            (ds+0x3DB2, b.words(320))], callbacks=callbacks, return_kind='void'))
        ids = [r['args'][0] for r in m.raw_trace if r['name'] == 'win_MakeObjSelected']
        if mode < 4:
            assert ids == [[0x1908, 0x1908, 0x1909, 0x190A][mode]]
        elif mode == 4:
            assert not ids and m.read(0x50F6*16+0x35C, 2) == b.words(0)
        yard.append({'mode': mode, 'selected': ids, 'supported': mode <= 4,
                     'table_index': mode if mode != 4 else None})
    ants = []
    for mode in (-1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 32767):
        m = machine('SetMapModeAnt')
        m.run(b.Case('map ant mode guard', args=[mode],
            writes=[(0x3D57*16+0x7C8, b.words(0x8000)), (0x50F6*16+0x32E, b.words(1))],
            callbacks={'SetYardMode': callback(1), 'SetMapPlane': callback(1), 'SetMapTitle': callback(),
                'win_MakeObjSelected': callback(regs=('ax',)),
                'win_MakeGroupUnselected': callback(regs=('ax', 'dx'))}, return_kind='void'))
        ids = [r['args'][0] for r in m.raw_trace if r['name'] == 'win_MakeObjSelected']
        assert ids == ([[0x109, 0x10A, 0x10C, 0x10D, 0x10B][mode-4]] if 4 <= mode <= 8 else [])
        ants.append({'mode': mode, 'selected': ids})
    planes = []
    for plane in (-1, 0, 1, 2, 3, 4, 32767):
        m = machine('SetMapPlaneLocation')
        m.run(b.Case('terminal plane selector', args=[plane, 0, 0],
            callbacks={'InvalEuMap': callback(4), 'CenterEdit': callback(2),
                'UpdateEdit': callback(), 'f_0250_0ED2': callback(), 'SetMapModeAnt': callback(1),
                'clip_SetWin': callback(1), 'clip_Off': callback(),
                'win_MakeObjSelected': callback(regs=('ax',)),
                'win_MakeGroupUnselected': callback(regs=('ax', 'dx'))}, return_kind='void'))
        ids = [r['args'][0] for r in m.raw_trace if r['name'] == 'win_MakeObjSelected']
        assert ids == {0:[0x105], 1:[8,0x106], 2:[9,0x107], 3:[10,0x108]}.get(plane, [])
        planes.append({'plane': plane, 'selected': ids})
    edit = []
    for health in (0, 100, 32767):
        m = machine('DrawEditGraphs')
        def rect(m, a):
            m.write(a[2]*16+a[1], bytes(8))
            return 0, 0
        m.run(b.Case('edit static selectors', writes=[
            (0x50F6*16+at, b.words(health)) for at in (0xF78, 0x10BE, 0x1FE)],
            callbacks={'win_SetColorFromObjNum': callback(regs=('ax',)),
                'win_GetObjRect': b.Callback(2, rect, register_args=('ax',), pop=4),
                '__aFldiv': b.Callback(4, no, pop=8), '__aFlmul': b.Callback(4, no, pop=8),
                'f_1CE2_046D': callback(3), 'f_1CE2_0430': callback(2),
                'f_1B4E_000D': callback(1)}, return_kind='void'))
        ids = [r['args'][0] for r in m.raw_trace if r['name'] == 'win_GetObjRect']
        assert ids == [0x11, 0x12, 0x13]
        edit.append({'health': health, 'objects': ids})
    score = []
    for mode in range(4):
        for width in (320, 640):
            m = machine('ScoreDialog')
            def calc(m, a):
                m.write(a[1]*16+a[0], b.words(*[0x7FFF if i % 2 else 0 for i in range(8)]))
                return 0, 0
            callbacks = {'CalcScore': b.Callback(2, calc), 'win_Open': callback(1),
                'win_Close': callback(regs=('ax',)), 'win_LockWin': callback(regs=('ax',)),
                'win_UnlockWin': callback(regs=('ax',)), 'win_IsWinOpen': callback(regs=('ax',)),
                'win_FlushEvents': callback(), 'win_SetObjFormatStr': callback(1),
                'win_PrintfAtObj': callback(1), 'f_24AB_02AD': callback(1), '_fstrcat': callback(4)}
            m.run(b.Case('score fixed loops', writes=[(0x50F6*16+0xEAC, b.words(mode)),
                (ds+0x3DB2, b.words(width))], callbacks=callbacks, return_kind='void'))
            ids = [r['args'][0] for r in m.raw_trace
                   if r['name'] in ('win_SetObjFormatStr', 'win_PrintfAtObj')]
            assert ids == list(range(0x1802, 0x1806)) + [0x180C] + list(range(0x1806, 0x180C))
            score.append({'game_mode': mode, 'width': width, 'objects': ids})
    resident = image.sections[27]
    off = 0x4E4B*16-resident.load_linear
    ranges = {'shownGraphs': (ds+0x2EF0, 8), 'freeColors': (ds+0x2EF8, 2),
              'histColor': (ds+0x8C26, 40), 'histShown': (ds+0x8C4E, 10),
              'g_1960': (ds+0x1960, 10), 'g_1984': (ds+0x1984, 8),
              'DrawEditGraphs.objs': (ds+0x1AA4, 6), 'YardMode': (0x50F6*16+0x35C, 2)}
    ranges.update({'fd_50F6_38B6': (0x50F6*16+0x38B6, 2), 'FileSelect.s_2966': (ds+0x2966, 2)})
    records, cursor = [], 0
    overlaps = {n: [] for n in ranges}
    for index in range(308):
        size, count, lo, seg = struct.unpack_from('<4H', resident.data, off+8*index)
        if not count:
            break
        addr, length = seg*16+lo, size*count
        for name, (start, width) in ranges.items():
            if max(addr, start) < min(addr+length, start+width):
                overlaps[name].append({'record': index, 'stream_offset': cursor,
                                       'size': size, 'count': count, 'relative': start-addr})
        records.append((addr, length))
        cursor += length
    assert index == 307 and cursor == 48386
    assert all(not v for k,v in overlaps.items() if k != 'YardMode')
    assert len(overlaps['YardMode']) == 1
    decoder_path = ROOT / 'evidence/canonical/audio-track-owner/shipped_domain.py'
    spec = importlib.util.spec_from_file_location('local_strings_decoder', decoder_path)
    decoder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(decoder)
    _, resources = decoder.parse_records('SHARED')
    lengths = {}
    for ident in (1001, 1800):
        raw = next(r['payload'] for r in resources if r['kind'] == 4 and r['id'] == ident)
        pos, sizes = 2, []
        for i in range(raw[1]):
            size = raw[pos]
            assert pos + 1 + size <= len(raw)
            sizes.append(size)
            pos += size + 1
        lengths[ident] = sizes
    title_sizes = [lengths[1800][13] + lengths[1001][i] + lengths[1800][14] + 1
                   for i in range(3)]
    assert max(title_sizes) <= 80
    title = {'strings': {'1001': lengths[1001][:4], '1800[13]': lengths[1800][13],
                         '1800[14]': lengths[1800][14]},
             'concatenated_bytes_including_NUL_modes_0_1_2': title_sizes,
             'buffer_capacity': 80, 'resource_pins': [
                {'path': 'assets/'+n, 'sha256': hashlib.sha256((ROOT/'assets'/n).read_bytes()).hexdigest()}
                for n in ('SHARED.NDX', 'SHARED.DAT')],
             'decoder_sha256': hashlib.sha256(decoder_path.read_bytes()).hexdigest()}
    return {'original_image_sha256': image.sha256, 'coverage': coverage(),
            'history_removals': history, 'history_evictions': evictions, 'history_guard': events,
            'yard_modes': yard, 'map_ant_guard': ants, 'plane_terminal_selector': planes,
            'edit_static_objects': edit, 'score_loop_objects': score,
            'score_title_shipped_default': title,
            'SaveRec': {'count': index, 'stream_size': cursor, 'overlap': overlaps},
            'scope': 'Actual original instructions; UI/drawing and memmove boundaries modeled. '
                     'Plane side helpers are modeled, so plane rows isolate its terminal switch. '
                     'Edit CRT arithmetic/zero rectangles and Score CalcScore/text services are modeled. '
                     'No arbitrary-save admission or broad memory-safety/UB waiver.'}


def collect():
    result = run()
    # Keep exhaustive regressions reproducible without publishing per-case traces.
    for name in ('history_removals', 'history_evictions', 'history_guard',
                 'map_ant_guard', 'plane_terminal_selector', 'edit_static_objects',
                 'score_loop_objects'):
        rows = result[name]
        result[name] = dict(count=len(rows), sha256=hashlib.sha256(
            json.dumps(rows, sort_keys=True, separators=(',', ':')).encode()).hexdigest())
    return result

if __name__ == '__main__':
    print(json.dumps(collect(), indent=2))
