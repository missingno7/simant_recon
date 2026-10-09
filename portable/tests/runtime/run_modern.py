"""Modern Game Window (--windows): the world-space map view over canonical state.

Checks only the new presentation contracts:

* composition: at the default camera the modern map area equals the hosted
  canonical edit view (same tiles, sprites, colours) in a paused world;
* camera synchronisation: a plane change re-centres the camera on the edit
  view; the game's own scrolling moves the camera; a user pan re-centres the
  canonical edit view (MapPnt) on the camera through the game's scroll;
* overview: with a larger, zoomed-out window the map window's indicator is
  the modern visible area, not the canonical edit rectangle;
* input: a click reaches the game at the world tile it was made on, at the
  default camera and for a tile the canonical edit view does not show;
* invariance: without camera input, the deterministic game state is the same
  with the modern Game Window as with the classic one (no RNG or state
  change from extra render frames).
"""
from pathlib import Path
import argparse
import json
import math
import re
import shutil
import subprocess
import sys

import run as runtime
from run_windows import pixels, run_case

PROJECT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).resolve().parent
GDB = 'C:/msys64/mingw64/bin/gdb.exe'
SMOKE = 19500
CASES = (('default', 'modern-default.txt'), ('zoom', 'modern-zoom.txt'))
PROBES = ('plane', 'pan', 'keys', 'click', 'click-far', 'zoom')
STATE = ["'root_0093.c'::seed", 'fd_50F6_0508', 'fd_50F6_383A', 'MapPlane',
         '*(short *)&fd_50F6_0F12', '*(short *)&fd_50F6_0F34']
CAMERA = ['fd_50F6_0508', '*(short(*)[4])&fd_50F6_110C', 'MapPlane',
          "'modern_game_view.c'::g.target", "'modern_game_view.c'::g.shown"]


def values(text):
    return re.findall(r'^\$\d+ = (.*)$', text, re.M)


def numbers(value):
    return [float(x) for x in re.findall(r'-?\d+(?:\.\d+)?(?:e-?\d+)?', value)]


def gdb_run(build, executable, out, name, script, prints, extra=(), breaks=''):
    target = out / name
    target.mkdir()
    shutil.copytree(build / 'runtime-assets', target / 'a')
    commands = target / 'gdb.txt'
    commands.write_text('set pagination off\n' + breaks + 'break __wrap_exit\nrun\n' +
                        ''.join('print ' + p + '\n' for p in prints))
    command = [GDB, '--batch', '-q', '-x', str(commands), '--args', str(executable), '--headless',
               *extra, '--deterministic', '--smoke-ms', str(SMOKE), '--seed', '0', '--assets', str(target / 'a'),
               '--frame', str(target / 'frame.bmp'),
               '--input-script', str(FIXTURES / script)]
    run = subprocess.run(command, capture_output=True, timeout=900)
    text = run.stdout.decode(errors='replace')
    (target / 'gdb-out.txt').write_text(text + run.stderr.decode(errors='replace'))
    return text


def camera(text):
    """MapPnt, editTileRect, plane, target and shown cameras at exit."""
    v = values(text)[-len(CAMERA):]
    if len(v) != len(CAMERA):
        return None
    origin, rect, plane = numbers(v[0]), numbers(v[1]), int(numbers(v[2])[0])
    target, shown = numbers(v[3]), numbers(v[4])
    return {'origin': origin, 'rect': rect, 'plane': plane,
            'target': target, 'shown': shown}


def canonical_center(c):
    return (c['origin'][0] * 16 + (c['rect'][2] - c['rect'][0]) / 2,
            c['origin'][1] * 16 + (c['rect'][3] - c['rect'][1]) / 2)


CLICK_BREAK = ('break processEdit\ncommands\nsilent\nprint ePtr->h\nprint ePtr->v\n'
               'print fd_50F6_0508\nprint *(short(*)[4])&fd_50F6_110C\n'
               "print 'modern_game_view.c'::g.shown\n"
               "print 'native_windows.c'::n.windows[0].view.left\n"
               "print 'native_windows.c'::n.windows[0].view.top_y\n"
               "print 'native_windows.c'::n.windows[0].strip\n"
               "print 'native_windows.c'::n.scale\ncontinue\nend\n")


def click_tiles(text, client):
    """(tile the game used, tile under the click by the modern camera) for the first processEdit."""
    v = values(text)
    if len(v) < 9:
        return None
    h, vv = numbers(v[0])[0], numbers(v[1])[0]
    origin, rect, shown = numbers(v[2]), numbers(v[3]), numbers(v[4])
    left, top, strip, scale = (numbers(v[i])[0] for i in range(5, 9))
    game = (int((h - rect[0]) // 16 + origin[0]), int((vv - rect[1]) // 16 + origin[1]))
    cx, cy, zoom, width, height = shown
    area_x, area_y = (rect[0] - left) * scale, (rect[1] - top - strip) * scale
    wx = cx + (client[0] * scale - area_x - width / 2) / zoom
    wy = cy + (client[1] * scale - area_y - height / 2) / zoom
    return game, (math.floor(wx / 16), math.floor(wy / 16))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    report_path = args.report.resolve()
    report = json.loads(report_path.read_text())
    if not report.get('passed') or not report.get('input_stability', {}).get('at_end'):
        raise ValueError('successful stable current native build required')
    if runtime.mismatched_inputs(PROJECT, report['input_pins']):
        raise ValueError('build inputs changed; rebuild')
    build = report_path.parent
    executable = Path(report['executable']['path']).resolve()
    if executable.parent != build or runtime.sha(executable) != report['executable']['sha256']:
        raise ValueError('executable differs from build report')
    out = (args.out or PROJECT / 'build/current/modern').absolute()
    sys.path.insert(0, str(PROJECT / 'tools'))
    from workspace import prepare_output
    prepare_output(out, PROJECT / 'build/current/modern', PROJECT)
    checks = {}
    runs = {name: run_case(build, executable, out, name, script, '--windows', SMOKE)
            for name, script in CASES}
    for name, r in runs.items():
        checks[name + '_normal_exit_and_replay'] = r['exit'] == 0 and r['smoke'] and r['replayed']

    # Composition: modern map area == hosted canonical edit view (paused world).
    frame = Path(str(runs['default']['frame']) + '.0000.bmp')
    hosted = Path(str(frame) + '.hosted.bmp')
    if frame.is_file() and hosted.is_file():
        (fw, fh, modern), (hw, hh, canonical) = pixels(frame), pixels(hosted)
        # Map area: editTileRect (50.., below the title strip); the canonical
        # grow icon (bottom-right 16x16 corner) is drawn over it in DOS only.
        cells = [(x, y) for x in range(50, hw - 2) for y in range(0, hh - 2)
                 if not (x >= hw - 20 and y >= hh - 20)]
        same = sum(modern(x, y) == canonical(x, y) for x, y in cells)
        checks['default_camera_matches_canonical_edit_view'] = (fw, fh) == (hw, hh) and same == len(cells)
    else:
        checks['default_camera_matches_canonical_edit_view'] = False

    probes = {name: gdb_run(build, executable, out, 'gdb-' + name, 'modern-' + name + '.txt', CAMERA,
                            ('--windows',), CLICK_BREAK if name.startswith('click') else '')
              for name in PROBES}
    plane = camera(probes['plane'])
    checks['plane_change_recentres_camera'] = bool(plane) and plane['plane'] == 1 and all(
        abs(a - b) < 0.01 for a, b in zip(plane['target'][:2], canonical_center(plane)))
    pan = camera(probes['pan'])
    checks['pan_recentres_canonical_view'] = bool(pan) and pan['origin'] != [25.0, 0.0] and all(
        abs(a - b) <= 8 for a, b in zip(pan['target'][:2], canonical_center(pan)))
    keys = camera(probes['keys'])
    checks['game_scroll_moves_camera'] = bool(keys) and keys['origin'][0] > 25 and all(
        abs(a - b) < 0.01 for a, b in zip(keys['target'][:2], canonical_center(keys)))
    near = click_tiles(probes['click'], (200, 150))
    checks['click_reaches_its_world_tile'] = bool(near) and near[0] == near[1]
    far = click_tiles(probes['click-far'], (580, 300))
    checks['far_click_reaches_its_world_tile'] = bool(far) and far[0] == far[1]

    # Overview: the indicator outline sits where the modern area maps (the
    # frame and the state come from the same deterministic run).
    zoom = camera(probes['zoom'])
    overview = gdb_run(build, executable, out, 'gdb-overview', 'modern-zoom.txt',
                       ["*(short(*)[4])&fd_50F6_10D2", 'fd_50F6_3856', 'fd_50F6_3858', 'fd_50F6_38C0',
                        "'native_windows.c'::n.windows[1].view.left",
                        "'native_windows.c'::n.windows[1].view.top_y",
                        "'native_windows.c'::n.windows[1].strip",
                        "'window_hosting.c'::s.map_cursor_shown",
                        "'modern_game_view.c'::g.shown", 'MapPlane',
                        '*(short(*)[4])&fd_50F6_110C'], ('--windows',))
    map_frame = out / 'gdb-overview' / 'frame.bmp.0100.bmp'
    ov = [numbers(x) for x in values(overview)]
    indicator_ok = False
    if map_frame.is_file() and len(ov) == 11 and ov[7][0] == 1:
        tiles, cw, ch, pad = ov[0], ov[1][0], ov[2][0], ov[3][0]
        mx, my, strip = ov[4][0], ov[5][0], ov[6][0]
        cx, cy, z, vw, vh = ov[8]
        world_w = 64 * 16.0 if ov[9][0] >= 2 else 128 * 16.0
        left = max(0.0, cx - vw / 2 / z)
        right = min(world_w, cx + vw / 2 / z)
        top = max(0.0, cy - vh / 2 / z)
        bottom = min(64 * 16.0, cy + vh / 2 / z)
        x0 = int(round(tiles[0] + pad + left * cw / 16) - mx)
        x1 = int(round(tiles[0] + pad + right * cw / 16) - mx)
        y0 = int(round(tiles[1] + top * ch / 16) - my - strip)
        y1 = int(round(tiles[1] + bottom * ch / 16) - my - strip)
        w, h, at = pixels(map_frame)
        rows = [y for y in range(max(0, y0 + 4), min(h, y1 - 4))]
        # The 2-pixel inverted frame differs from the map just inside it.
        indicator_ok = bool(rows) and sum(at(x0, y) != at(x0 + 3, y) and at(x1 - 1, y) != at(x1 - 4, y)
                                          for y in rows) >= 0.8 * len(rows)
        canonical_width = ov[10][2] - ov[10][0]
        checks['overview_indicator_wider_than_canonical_view'] = (x1 - x0) * 16 / cw > canonical_width
    else:
        checks['overview_indicator_wider_than_canonical_view'] = False
    checks['overview_indicator_is_modern_area'] = indicator_ok

    # Invariance: no camera input -> the same deterministic game state.
    quick = 'windows-quick.txt'
    modern_state = values(gdb_run(build, executable, out, 'inv-modern', quick, STATE,
                                  ('--windows',)))
    classic_state = values(gdb_run(build, executable, out, 'inv-classic', quick, STATE,
                                   ('--windows=200',)))
    checks['modern_view_leaves_game_state_unchanged'] = (len(modern_state) == len(STATE) and
                                                         modern_state == classic_state)

    result = {'passed': all(checks.values()), 'checks': checks,
              'executable_sha256': report['executable']['sha256'],
              'invariance': {'modern': modern_state, 'classic': classic_state},
              'runs': {k: {**v, 'frame': str(v['frame'])} for k, v in runs.items()}}
    (out / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed': result['passed'],
                      'failed_checks': [k for k, v in checks.items() if not v]}))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
