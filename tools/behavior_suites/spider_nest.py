"""Controlled differential cases for SpiderScan and EnterNest.

The adapters deliberately do not assign a proof status.  Every case carries the
contract boundary and callback tier so the shared runner can report which
dependencies were executed from the original EXE and which were modeled.

Run through tools/behavior.py once its public API is available:
    python tools/behavior.py SpiderScan --suite spider_nest
    python tools/behavior.py o25_3BA4_1035 --suite spider_nest
"""
from __future__ import annotations

import math
import random
from typing import Any


SUITE_ID = "spider_nest_contracts_v1"

HELPER_STACK_WORDS = {
    "SpiderScan": {
        "SRand1": 1, "SRand4": 0, "fracSIN": 1, "fracCOS": 1,
        "FindAntIndex": 4, "DeadAntHere": 3,
    },
    "o25_3BA4_1035": {
        "SRand1": 1, "SRand4": 0, "ClearMyLife": 5,
        "SetMyLife": 6, "DigMyTile": 3, "TryAntTheme": 0,
        "SetAlarmDropState": 2,
    },
}

CONTRACTS = {
    "SpiderScan": {
        "target": "root:0CDB:0F90",
        "current_residue": "Target is 392 bytes; best source is 389 bytes. Original has an additional dead initialization sequence before the pass loop. Candidate CFG is reported matching; strict historical proof remains open.",
        "compared": ["return", "spider globals", "LifeA", "A ant arrays/count", "MapA", "corpse-ring state", "LFSR state and callback results", "laser callback arguments", "all non-stack writes"],
        "helper_policy": "In original-helper mode, SRand1/SRand4/fracSIN/fracCOS/FindAntIndex/DeadAntHere execute as original overlay/oracle helpers and are entry-watched. Default mode retains source-derived trig/RNG callbacks. DoLaserFire is trace-only.",
        "boundedness": "DoLaserFire output is represented by its ordered call/argument trace; rendering/audio device effects are outside this simulation contract.",
    },
    "o25_3BA4_1035": {
        "target": "S25:3BA4:1035",
        "current_residue": "Target and best source are both 281 bytes; normalized body and CFG match; two register-role operand bytes differ and strict relocation-order proof is grouped.",
        "compared": ["return", "MePlane/MeLocX/MeLocY", "ant type/direction/alarm globals", "LifeB/LifeR", "MapA/MapB/MapR", "hole maps", "LFSR state and callback results", "audio/window/invalidation callback traces", "all non-stack writes"],
        "helper_policy": "ClearMyLife/SetMyLife/DigMyTile/TryAntTheme/SetAlarmDropState execute as original overlay/oracle helpers and are entry-watched. win_SetObjSelectedState and InvalEuMap are explicit host UI boundaries; TickCount is deterministic and myBeginSong is trace-only.",
        "boundedness": "Host audio, window selection, and map invalidation are observed at callback boundaries; their physical device effects are outside this function contract.",
    },
}


def _behavior():
    # Keep importing this module useful while the shared executor is being
    # developed.  The harness owns Case/Callback/Range and symbol placement.
    import behavior
    return behavior


def _signed16(value: int) -> int:
    return value & 0xFFFF


def _word_write(name: str, value: int) -> tuple[int, bytes]:
    b = _behavior()
    return b.symbol_address(name), (_signed16(value)).to_bytes(2, "little")


def _blob_write(name: str, data: bytes, offset: int = 0) -> tuple[int, bytes]:
    b = _behavior()
    return b.symbol_address(name) + offset, data


def _range(name: str, size: int, *, offset: int = 0):
    b = _behavior()
    return b.Range(name, b.symbol_address(name) + offset, size)


def _case(label: str, *, writes, observe, callbacks, return_kind="s16",
          contract="bounded_contract", provenance=None, state=None):
    # The volatile-register pattern is fixed per case to make runs repeatable,
    # while ensuring entry values cannot accidentally provide useful state.
    import hashlib
    h = hashlib.sha256(label.encode("utf-8")).digest()
    registers = {
        "ax": int.from_bytes(h[0:2], "little"),
        "bx": int.from_bytes(h[2:4], "little"),
        "cx": int.from_bytes(h[4:6], "little"),
        "dx": int.from_bytes(h[6:8], "little"),
        "si": 0xA15E,
        "di": 0xD1A0,
        "bp": 0xBEEF,
        "es": 0xCAFE,
    }
    return _behavior().Case(
        label=label,
        args=[],
        writes=list(writes),
        observe=list(observe),
        callbacks=dict(callbacks),
        return_kind=return_kind,
        state=dict(state or {}),
        registers=registers,
        metadata={
            "suite": SUITE_ID,
            "contract_level": contract,
            "callback_provenance": provenance or {},
            "caller_register_policy": "case-hashed AX/BX/CX/DX with SI/DI/BP sentinels",
            "stack_policy": "runner-poisoned frame below far return; cdecl cleanup",
        },
    )


def _noop(machine, args):
    return None


def _lfsr_next(machine):
    """Exact root:0093 LFSR transition, exposed as a traceable callback."""
    old = machine.state["lfsr_seed"] & 0xFFFF
    value = (old << 1) & 0xFFFF
    if old & 0x8000:
        value ^= 0x1BF5
    machine.state["lfsr_seed"] = value
    machine.state.setdefault("lfsr_results", []).append(value)
    b = _behavior()
    machine.write(b.symbol_address("g_8BA2"), value.to_bytes(2, "little"))
    return value


def _lfsr_value(seed: int) -> int:
    value = (seed << 1) & 0xFFFF
    if seed & 0x8000:
        value ^= 0x1BF5
    return value


def _spider_first_cell(direction: int, sx: int, sy: int, seed: int):
    angle_index = (((direction - 2) & 7) << 5) - 32
    radius = (_lfsr_value(seed) % 12) + 1
    angle = 2.0 * math.pi * angle_index / 256.0
    dx = int(math.cos(angle) * radius)
    dy = int(math.sin(angle) * radius)
    return (sx >> 4) + dx, (sy >> 4) + dy


def _neighbors(x: int, y: int, radius: int = 1):
    return tuple((xx, yy) for xx in range(x - radius, x + radius + 1)
                 for yy in range(y - radius, y + radius + 1)
                 if 0 <= xx < 128 and 0 <= yy < 64)


def _seed_for_kill(want_kill: bool) -> int:
    for seed in range(1, 0x10000):
        next_seed = _lfsr_value(seed)
        result = _lfsr_value(next_seed) & 3
        if bool(result) == want_kill:
            return seed
    raise AssertionError("no LFSR seed found")


def _rand1(machine, args):
    n = args[0] & 0xFFFF
    if n == 0:
        raise AssertionError("SRand1 called with zero range")
    return _lfsr_next(machine) % n


def _rand4(machine, args):
    return _lfsr_next(machine) & 3


def _frac_sin_value(machine, angle: int) -> int:
    """Mirror confirmed S08 fracSIN using its original far table from the EXE."""
    angle &= 0xFFFF
    index = angle & 0x7F
    if index > 0x3F:
        index = 0x80 - index
    if index == 0x40:
        value = 0x7FFF
    else:
        ptr = _behavior().symbol_address("fd_50F6_0B22")
        offset, segment = machine.word(ptr), machine.word(ptr + 2)
        value = machine.word(segment * 16 + offset + 2 * (index & 0x3F))
    if (angle & 0xFF) > 0x7F:
        value = (-value) & 0xFFFF
    return value


def _frac_sin(machine, args):
    value = _frac_sin_value(machine, args[0])
    machine.state.setdefault("fracSIN_results", []).append(value)
    return value


def _frac_cos(machine, args):
    value = _frac_sin_value(machine, args[0] + 0x40)
    machine.state.setdefault("fracCOS_results", []).append(value)
    return value


def _spider_callbacks():
    b = _behavior()
    return {
        "SRand1": b.Callback(stack_words=1, handler=_rand1, pop=0),
        "SRand4": b.Callback(stack_words=0, handler=_rand4, pop=0),
        "fracSIN": b.Callback(stack_words=1, handler=_frac_sin, pop=0),
        "fracCOS": b.Callback(stack_words=1, handler=_frac_cos, pop=0),
        # Rendering stays at a recorded host boundary. All game-state helpers,
        # including DeadAntHere and FindAntIndex, execute from the oracle image.
        "DoLaserFire": b.Callback(stack_words=4, handler=_noop, pop=0),
    }


def _spider_observations():
    return [
        _range("fd_50F6_1004", 2),
        _range("fd_50F6_0F12", 2),
        _range("fd_50F6_0F34", 2),
        _range("LifeA", 128 * 64),
        _range("AlistX", 1000),
        _range("AlistY", 1000),
        _range("AlistT", 1000),
        _range("ListIndexA", 2),
        _range("g_8BA2", 2),
        _range("MapA", 128 * 64),
        _range("fd_50F6_0476", 2),
        _range("fd_50F6_037C", 100),
        _range("fd_50F6_0404", 100),
    ]


def _spider_case(label: str, *, direction: int, sx: int, sy: int,
                 life_cells=(), ants=(), count=None, lfsr_seed=0xACE1):
    # The arrays are deliberately zero-initialized before sparse overlays.
    # LifeA is x-major in the DOS image: offset x*64+y.
    writes = [
        _word_write("fd_50F6_1004", direction),
        _word_write("fd_50F6_0F12", sx),
        _word_write("fd_50F6_0F34", sy),
        _blob_write("LifeA", bytes(128 * 64)),
        _blob_write("AlistX", bytes(1000)),
        _blob_write("AlistY", bytes(1000)),
        _blob_write("AlistT", bytes(1000)),
        _word_write("ListIndexA", len(ants) if count is None else count),
        _word_write("g_8BA2", lfsr_seed),
        _word_write("fd_50F6_0476", 0),
        _word_write("TERRAINset", 0),
        _blob_write("MapA", bytes(128 * 64)),
        _blob_write("fd_50F6_037C", bytes(100)),
        _blob_write("fd_50F6_0404", bytes(100)),
    ]
    life_base = _behavior().symbol_address("LifeA")
    ax = _behavior().symbol_address("AlistX")
    ay = _behavior().symbol_address("AlistY")
    at = _behavior().symbol_address("AlistT")
    for x, y, value in life_cells:
        if 0 <= x < 128 and 0 <= y < 64:
            writes.append((life_base + x * 64 + y, bytes((value & 0xFF,))))
    for i, (x, y, value) in enumerate(ants[:1000]):
        writes.extend(((ax + i, bytes((x & 0xFF,))),
                       (ay + i, bytes((y & 0xFF,))),
                       (at + i, bytes((value & 0xFF,)))))
    case = _case(label, writes=writes, observe=_spider_observations(),
                 callbacks=_spider_callbacks(),
                 return_kind="s16", contract="bounded_contract",
                 state={"lfsr_seed": lfsr_seed},
                 provenance={
                     "SRand1/SRand4": "source-derived root:0093 LFSR transition callback pending original-helper watch mode",
                     "fracCOS/fracSIN": "source-derived callback reading the original far sine table pending original-helper watch mode",
                     "FindAntIndex/DeadAntHere": "execute original EXE helpers",
                     "DoLaserFire": "trace-only callback",
                 })
    case.metadata["domain"] = {
        "direction": direction & 0xFFFF, "spider_x16": sx & 0xFFFF,
        "spider_y16": sy & 0xFFFF, "life_cells": len(life_cells),
        "ant_count": len(ants) if count is None else count,
        "lfsr_seed": lfsr_seed & 0xFFFF,
    }
    return case


def _spider_directed():
    cases = []
    # Coordinates on each edge, with an interior fraction and off-map values.
    coordinates = (-17, -1, 0, 1, 15, 16, 2031, 2047, 2048, 2063)
    for d_index, d in enumerate((-1, 0, 1, 4, 7, 8, 0x7FFF, 0xFFFF)):
        for sx in (coordinates[0], coordinates[2], coordinates[4], coordinates[6],
                   coordinates[7], coordinates[8], coordinates[9]):
            sy = (sx * 13 + d * 37) % 2080 - 16
            cases.append(_spider_case(
                f"edge-dir{d & 0xffff:04x}-variant{d_index}-x{sx & 0xffff:04x}",
                direction=d, sx=sx, sy=sy,
            ))

    # Explicit accepted-target and rejected-target paths.  The fixed candidate
    # cell is a valid map position; the RNG/trig callbacks remain in charge of
    # Cells are placed around the first path sample predicted from the exact
    # LFSR and the helper angle convention. Neighbor coverage absorbs the
    # original fixed-point trig rounding at a tile boundary.
    for direction in range(8):
        for life in (1, 0x81, 0xFF):
            seed = _seed_for_kill(False)
            hx, hy = _spider_first_cell(direction, 1024, 512, seed)
            pool = _neighbors(hx, hy)
            cases.append(_spider_case(
                f"one-live-cell-dir{direction}-life{life:02x}", direction=direction,
                sx=1024, sy=512,
                life_cells=tuple((x, y, life) for x, y in pool),
                ants=tuple((x, y, life) for x, y in pool), lfsr_seed=seed,
            ))
            cases.append(_spider_case(
                f"ant-type-mismatch-dir{direction}-life{life:02x}", direction=direction,
                sx=1024, sy=512,
                life_cells=tuple((x, y, life) for x, y in pool),
                ants=tuple((x, y, life ^ 1) for x, y in pool), lfsr_seed=seed,
            ))
            seed_kill = _seed_for_kill(True)
            kx, ky = _spider_first_cell(direction, 1024, 512, seed_kill)
            kill_pool = _neighbors(kx, ky)
            cases.append(_spider_case(
                f"matching-target-kill-dir{direction}-life{life:02x}",
                direction=direction, sx=1024, sy=512,
                life_cells=tuple((x, y, life) for x, y in kill_pool),
                ants=tuple((x, y, life) for x, y in kill_pool),
                lfsr_seed=seed_kill,
            ))

    # Invalid count/slot and multiple duplicate entries exercise reverse scan
    # selection and guard against accidentally accepting an inactive ant.
    cases.append(_spider_case("duplicate-active-ant-prefers-last", direction=2,
                               sx=1024, sy=512,
                               life_cells=((64, 32, 0x29),),
                               ants=((64, 32, 0x29), (64, 32, 0x29))))
    cases.append(_spider_case("inactive-ant-count-zero", direction=2,
                               sx=1024, sy=512,
                               life_cells=((64, 32, 0x29),),
                               ants=((64, 32, 0x29),), count=0))
    # Dense 9x9 neighborhoods centered on the first sample drive target
    # resolution, competing matches, and both corpse outcomes.
    for direction in range(8):
        for want_kill in (False, True):
            seed = _seed_for_kill(want_kill)
            cx, cy = _spider_first_cell(direction, 1024, 512, seed)
            dense = _neighbors(cx, cy, radius=4)
            life_cells = tuple((x, y, 0x20 | ((x + y) & 0x1F)) for x, y in dense)
            ants = tuple((x, y, life) for x, y, life in life_cells)
            cases.append(_spider_case(
                f"dense-target-dir{direction}-kill{int(want_kill)}",
                direction=direction, sx=1024, sy=512,
                life_cells=life_cells, ants=ants, lfsr_seed=seed,
            ))
    return cases


def _spider_random(seed: int, count: int):
    rng = random.Random(seed)
    for n in range(count):
        direction = rng.choice([*range(8), -1, 8, 0x7FFF, 0xFFFF])
        sx = rng.choice([rng.randrange(0, 2048), -1, 0, 15, 16, 2032, 2047, 2048])
        sy = rng.choice([rng.randrange(0, 1024), -1, 0, 15, 16, 1008, 1023, 1024])
        lfsr_seed = rng.randrange(1, 0x10000)
        cells = []
        ants = []
        # Sparse random LifeA cells; duplicate ant tuples naturally test reverse
        # selection.  Coordinates are unbiased over the valid board.
        for _ in range(rng.randrange(0, 12)):
            x, y = rng.randrange(128), rng.randrange(64)
            life = rng.choice([0, 1, 8, 0x18, 0x29, 0x61, 0x80, 0x81, 0xFF])
            cells.append((x, y, life))
            if life and rng.random() < 0.55:
                ants.append((x, y, life if rng.random() < 0.8 else (life ^ 8)))
        # Deliberately exercise live target resolution on half the cases.
        if rng.random() < 0.5:
            life = rng.choice([1, 8, 0x18, 0x29, 0x61, 0x80, 0x81, 0xFF])
            hx, hy = _spider_first_cell(direction, sx, sy, lfsr_seed)
            pool = _neighbors(hx, hy)
            cells.extend((x, y, life) for x, y in pool)
            ants.extend((x, y, life) for x, y in pool)
        yield _spider_case(f"seed{seed:08x}-case{n:06d}", direction=direction,
                           sx=sx, sy=sy,
                           life_cells=cells, ants=ants, lfsr_seed=lfsr_seed)


def _enter_nest_callbacks():
    b = _behavior()
    # TickCount and song notification are modeled. Map/life helpers and
    # TryAntTheme execute from the original image. SetAlarmDropState remains a
    # executed from the original S22 overlay; its lower UI effects are modeled.
    return {
        "TickCount": b.Callback(stack_words=0, handler=_tick_count, pop=0),
        "myBeginSong": b.Callback(stack_words=2, handler=_noop, pop=0),
        "SetAlarmDropState": b.Callback(stack_words=2, handler=None, pop=0),
        "win_SetObjSelectedState": b.Callback(stack_words=0, handler=_noop,
                                               register_args=("ax", "dx"), pop=0),
        "InvalEuMap": b.Callback(stack_words=4, handler=_noop, pop=0),
        "SRand1": b.Callback(stack_words=1, handler=_rand1, pop=0),
        "SRand4": b.Callback(stack_words=0, handler=_rand4, pop=0),
    }


def _tick_count(machine, args):
    tick = (machine.state.get("tick", 0) + 37) & 0xFFFFFFFF
    machine.state["tick"] = tick
    machine.state.setdefault("tick_results", []).append(tick)
    return tick & 0xFFFF, tick >> 16


def _nest_observations():
    return [
        _range("fd_50F6_0496", 2),
        _range("fd_50F6_04C2", 2),
        _range("fd_50F6_104E", 2),
        _range("MePlane", 2),
        _range("MeLocX", 2),
        _range("MeLocY", 2),
        _range("LifeB", 64 * 64),
        _range("LifeR", 64 * 64),
        _range("MapB", 64 * 64),
        _range("MapR", 64 * 64),
        _range("MapA", 128 * 64),
        _range("g_8BA2", 2),
        _range("HoleMapB", 64),
        _range("HoleMapR", 64),
    ]


def _nest_case(label: str, *, plane: int, x: int, y: int, ant_type: int,
               direction: int, alarm: int, map_fill=0, life_fill=0):
    # Initial board bytes are explicit, so the map and life effects of the
    # original ClearMyLife/SetMyLife/DigMyTile helpers remain observable.
    writes = [
        _word_write("fd_50F6_0496", direction),
        _word_write("fd_50F6_04C2", ant_type),
        _word_write("fd_50F6_104E", alarm),
        _word_write("MePlane", plane),
        _word_write("MeLocX", x),
        _word_write("MeLocY", y),
        _word_write("g_8BA2", 0xBEEF),
        _blob_write("LifeB", bytes([life_fill & 0xFF]) * (64 * 64)),
        _blob_write("LifeR", bytes([life_fill & 0xFF]) * (64 * 64)),
        _blob_write("MapB", bytes([map_fill & 0xFF]) * (64 * 64)),
        _blob_write("MapR", bytes([map_fill & 0xFF]) * (64 * 64)),
        _blob_write("MapA", bytes([map_fill & 0xFF]) * (128 * 64)),
    ]
    case = _case(label, writes=writes, observe=_nest_observations(),
                 callbacks=_enter_nest_callbacks(), return_kind="void",
                 contract="bounded_contract",
                 state={"lfsr_seed": 0xBEEF, "tick": 0},
                 provenance={
                     "ClearMyLife/SetMyLife/DigMyTile/TryAntTheme/SetAlarmDropState": "execute original EXE helpers",
                     "SRand1/SRand4": "source-derived root:0093 LFSR callback pending original-helper watch mode",
                     "TickCount": "deterministic +37 tick callback",
                     "win_SetObjSelectedState/InvalEuMap": "modeled host UI boundaries",
                     "myBeginSong": "trace-only host callback",
                 })
    case.metadata["domain"] = {
        "initial_plane": plane & 0xFFFF, "initial_x": x & 0xFFFF,
        "initial_y": y & 0xFFFF, "ant_type": ant_type & 0xFFFF,
        "initial_direction": direction & 0xFFFF, "alarm": alarm & 0xFFFF,
        "map_fill": map_fill & 0xFF, "life_fill": life_fill & 0xFF,
    }
    return case


def _enter_nest_directed():
    cases = []
    xs = (-1, 0, 1, 63, 64, 65, 126, 127)
    ys = (0, 1, 2, 30, 31, 62, 63)
    types = (0x08, 0x10, 0x18, 0x20, 0x28, 0x30, 0x38, 0x40, 0x48, 0x60)
    for plane in (2, 3):
        for x in xs:
            for y in ys:
                for t in (0x08, 0x60):
                    cases.append(_nest_case(
                        f"plane{plane}-x{x}-y{y}-type{t:02x}", plane=plane,
                        x=x, y=y, ant_type=t, direction=(x + y) & 7,
                        alarm=(x ^ y) & 1, map_fill=0, life_fill=0,
                    ))
        for t in types:
            for direction in range(8):
                cases.append(_nest_case(
                    f"plane{plane}-type{t:02x}-dir{direction}", plane=plane,
                    x=64, y=1, ant_type=t, direction=direction,
                    alarm=1, map_fill=0, life_fill=(t | 0x80) & 0xFF,
                ))
    # Exercise the strict > 64 plane threshold independently of board edges.
    for x in (63, 64, 65):
        for alarm in (0, 1, 0xFFFF):
            cases.append(_nest_case(f"threshold-x{x}-alarm{alarm & 0xffff:04x}",
                                    plane=2, x=x, y=10, ant_type=0x30,
                                    direction=4, alarm=alarm))
    # Sweep the complete initial x domain separately on both nest planes.
    # Rotate valid types, directions, alarm states, and destination fills.
    map_fills = (0, 1, 4, 7)
    life_fills = (0, 0x08, 0x20, 0x28, 0x60, 0x81)
    for plane in (2, 3):
        for x in range(128):
            cases.append(_nest_case(
                f"all-x-plane{plane}-x{x}", plane=plane, x=x, y=(x * 17) % 64,
                ant_type=types[x % len(types)], direction=x & 7, alarm=x & 1,
                map_fill=map_fills[x % len(map_fills)],
                life_fill=life_fills[x % len(life_fills)],
            ))
    # Cross valid ant types, planes, and directions with differing occupied
    # destination-state patterns.
    for plane in (2, 3):
        for index, ant_type in enumerate(types):
            for direction in range(8):
                cases.append(_nest_case(
                    f"plane{plane}-type{ant_type:02x}-dir{direction}-destmap",
                    plane=plane, x=(index * 13 + direction * 3) % 128,
                    y=(index * 7 + direction * 5) % 64,
                    ant_type=ant_type, direction=direction,
                    alarm=(index + direction) & 1,
                    map_fill=map_fills[(index + direction) % len(map_fills)],
                    life_fill=life_fills[(index * 2 + direction) % len(life_fills)],
                ))
    return cases


def _enter_nest_random(seed: int, count: int):
    rng = random.Random(seed)
    valid_types = (0x08, 0x10, 0x18, 0x20, 0x28, 0x30, 0x38, 0x40, 0x48, 0x60)
    for n in range(count):
        yield _nest_case(
            f"seed{seed:08x}-case{n:06d}", plane=rng.choice((2, 3)),
            x=rng.choice((rng.randrange(0, 128), 63, 64, 65)),
            y=rng.choice((rng.randrange(0, 64), 0, 1, 2, 62, 63)),
            ant_type=rng.choice(valid_types), direction=rng.randrange(8),
            alarm=rng.choice((0, 1, 0xFFFF)), map_fill=rng.choice((0, 1, 4, 7)),
            life_fill=rng.choice((0, 0x08, 0x28, 0x60, 0x81)),
        )


def make_cases(function: str, *, directed: bool = True,
               random_seed: int = 0x5A17E2,
               random_count: int = 0, original_helpers=()):
    """Return current bounded cases for one function.

    `random_count` is intentionally explicit: the supervisor chooses scale only
    after emulator throughput and per-case memory cost are measured.  The
    function does not label itself BEHAVIOR_EXACT based on generated cases.
    """
    if function == "SpiderScan":
        if directed:
            for case in _spider_directed():
                case.metadata["function"] = function
                yield enable_original_helpers(case, original_helpers)
        for case in _spider_random(random_seed, random_count):
            case.metadata["function"] = function
            yield enable_original_helpers(case, original_helpers)
        return
    if function in ("o25_3BA4_1035", "EnterNest"):
        if directed:
            for case in _enter_nest_directed():
                case.metadata["function"] = "o25_3BA4_1035"
                yield enable_original_helpers(case, original_helpers)
        for case in _enter_nest_random(random_seed, random_count):
            case.metadata["function"] = "o25_3BA4_1035"
            yield enable_original_helpers(case, original_helpers)
        return
    raise KeyError(f"no spider_nest suite for {function}")


def enable_original_helpers(case, names):
    """Watch selected original helper entries and execute them unmodified."""
    specs = HELPER_STACK_WORDS.get(case.metadata.get("function"), {})
    removed = []
    for name in names:
        if name in case.callbacks:
            old = case.callbacks[name]
            case.callbacks[name] = _behavior().Callback(
                stack_words=specs.get(name, old.stack_words), handler=None,
                register_args=old.register_args, pop=old.pop, project=old.project)
            removed.append(name)
        elif name in specs:
            case.callbacks[name] = _behavior().Callback(
                stack_words=specs[name], handler=None)
            removed.append(name)
    case.metadata["original_helpers_enabled"] = sorted(removed)
    if removed:
        case.metadata["contract_level"] = "bounded_contract_original_helpers"
        for name in removed:
            case.metadata.setdefault("callback_provenance", {})[name] = (
                "handler=None entry watch; original oracle helper body executes")
        # Final ranges remain fully compared, while helper traces retain their
        # argument order without copying multi-kilobyte arrays at every call.
        case.observe_at_calls = False
    return case


def run(pair, out, *, function: str, random_seed: int = 0x5A17E2,
        random_count: int = 0, original_helpers=()):
    """Execute directed and requested randomized cases, retaining all failures."""
    all_cases = make_cases(function, directed=True, random_seed=random_seed,
                           random_count=random_count, original_helpers=original_helpers)
    out.mkdir(parents=True, exist_ok=True)
    results = []
    failures = []
    directed_count = 0
    randomized_count = 0
    for case in all_cases:
        group = "randomized" if case.label.startswith(f"seed{random_seed:08x}-") else "directed"
        if group == "directed": directed_count += 1
        else: randomized_count += 1
        try:
            result = pair.compare(case)
        except Exception as exc:
            failures.append({"case": case.label, "execution_error": repr(exc),
                             "initial_state": [[a, bytes(v).hex()] for a,v in case.writes],
                             "metadata": case.metadata})
            break
        row = {"group": group, "case": case.label, "equal": result.equal,
               "difference": getattr(result, "diff", None)}
        results.append(row)
        if not result.equal:
            failures.append({
                "case": case.label,
                "result": result,
                "initial_state": [[a, bytes(v).hex()] for a,v in case.writes],
                "callbacks": list(case.callbacks),
                "metadata": case.metadata,
            })
    # The common runner owns the stable serialization format for its Machine
    # objects.  Keep complete comparison snapshots in-memory for now and write
    # concise case verdicts here without erasing a single mismatch.
    import json
    (out / f"{function}.cases.json").write_text(json.dumps({
        "suite": SUITE_ID,
        "function": function,
        "directed_count": directed_count,
        "randomized_count": randomized_count,
        "original_helpers": sorted(original_helpers),
        "seed": random_seed,
        "mismatches": len(failures),
        "results": results,
        "contract_level": "bounded_contract",
    }, indent=2))
    return failures

