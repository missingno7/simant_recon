#!/usr/bin/env python3
"""Compare one native MoveSpider tick with the original 16-bit DOS entry."""
from __future__ import annotations

import argparse
import ctypes as ct
import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools"
LIBRARY = ROOT / "build/portable/spider-sim-test.dll"
REPORT = ROOT / "build/portable/spider-sim-dos-diff.json"
GCC = Path("C:/msys64/mingw64/bin/gcc.exe")
sys.path.insert(0, str(TOOLS))
import behavior  # noqa: E402
import exe  # noqa: E402
import functions  # noqa: E402

SPIDER_FIELDS = (
    ("fd_50F6_1004", 2), ("fd_50F6_0F12", 2), ("fd_50F6_0F34", 2),
    ("SpidBurpCnt", 2), ("EatCnt", 2), ("SCorpseBase", 2),
    ("Scycle", 2), ("Scycle2", 2), ("SpidRevenge", 2),
    ("fd_3D57_0C12", 2), ("fd_50F6_0F0C", 2), ("SMode", 2),
    ("fd_50F6_06AC", 2), ("Starg", 2), ("StargLife", 2),
    ("SuserX", 2), ("SuserY", 2),
)
TICK_FIELDS = (("fd_50F6_0A06", 2), ("fd_50F6_0A8E", 2), ("DeathCnt", 2))
WORLD_FIELDS = (("fd_50F6_0EAC", 2), ("MePlane", 2), ("MeLocX", 2),
                ("MeLocY", 2), ("fd_50F6_04C2", 2), ("fd_50F6_0496", 2),
                ("TERRAINset", 2))
OBSERVE_NAMES = [n for n, _ in SPIDER_FIELDS + TICK_FIELDS + WORLD_FIELDS] + [
    "RAntsEaten", "BAntsEaten", "g_8BA2", "LifeA", "MapA", "AlistX",
    "AlistY", "AlistT", "ListIndexA", "fd_50F6_0476", "fd_50F6_037C",
    "fd_50F6_0404",
]

EVENT_NAMES = {
    "myBeginSound": 2,
    "PictStrnDialog": 3,
    "YellowDeath": 4,
    "MoveMyLife": 5,
    "f_0BE8_0812": 6,
    "f_015B_06A2": 7,
    "DoLaserFire": 1,
    "o25_39C7_0CBD": 8,
}


def symbol(name: str) -> int:
    return behavior.symbol_address(name)


def word(value: int) -> bytes:
    return (value & 0xffff).to_bytes(2, "little")


def load_sine_resource():
    index = (ROOT / "assets/SHARED.NDX").read_bytes()
    data = (ROOT / "assets/SHARED.DAT").read_bytes()
    count = struct.unpack_from("<H", index)[0]
    start = len(index) - count * 8
    found = []
    for i in range(count):
        offset, object_id, kind, flags = struct.unpack_from("<IHBB", index, start + i * 8)
        if object_id == 0x3e8 and kind == 9:
            header = struct.unpack_from("<HHHHH", data, offset + 14)
            payload = data[offset + 24:offset + 24 + header[3]]
            found.append((offset, flags, payload))
    if len(found) != 1 or found[0][1] != 0 or len(found[0][2]) != 128:
        raise RuntimeError("could not decode original Spider sine resource")
    payload = found[0][2]
    # InitStuff calls f_0244_0022, which swaps every word in place.
    table = [int.from_bytes(payload[i:i + 2], "big", signed=True)
             for i in range(0, len(payload), 2)]
    return table


def machine_for_original():
    vectors = {exe.MANAGER_SEG * 16 + v.offset: v for v in exe.load().vectors}
    return behavior.Machine(SimpleNamespace(function=functions.get("MoveSpider"),
                                            vectors=vectors))


def callbacks(route_result: int):
    def noop(machine, args):
        return 0

    def route(machine, args):
        return route_result

    out = {name: behavior.Callback(stack_words=words, handler=noop)
           for name, words in (("myBeginSound", 3), ("PictStrnDialog", 3),
                               ("YellowDeath", 1), ("MoveMyLife", 5),
                               ("f_0BE8_0812", 2), ("f_015B_06A2", 0),
                               ("DoLaserFire", 4))}
    out["o25_39C7_0CBD"] = behavior.Callback(stack_words=5, handler=route)
    return out


def make_case(label, spider, tick, world, eaten, options, seed,
              ant_count=0, life_cells=(), ants=(), corpse_base=0,
              terrain_cells=(), route_result=-2):
    life = bytearray(128 * 64)
    map_a = bytearray(128 * 64)
    ax = bytearray(1000)
    ay = bytearray(1000)
    at = bytearray(1000)
    corpse_x = bytearray(100)
    corpse_y = bytearray(100)
    writes = []
    for (name, _), value in zip(SPIDER_FIELDS, spider):
        writes.append((symbol(name), word(value)))
    for (name, _), value in zip(TICK_FIELDS, tick):
        writes.append((symbol(name), word(value)))
    for (name, _), value in zip(WORLD_FIELDS, world):
        writes.append((symbol(name), word(value)))
    writes.extend([
        (symbol("ListIndexA"), word(ant_count)),
        (symbol("RAntsEaten"), (eaten[0] & 0xffffffff).to_bytes(4, "little")),
        (symbol("BAntsEaten"), (eaten[1] & 0xffffffff).to_bytes(4, "little")),
        (symbol("g_8BA2"), word(seed)),
        (symbol("fd_50F6_0476"), word(corpse_base)),
        (symbol("TERRAINset"), word(world[6])),
        (symbol("LifeA"), bytes(life)), (symbol("MapA"), bytes(map_a)),
        (symbol("AlistX"), bytes(ax)), (symbol("AlistY"), bytes(ay)),
        (symbol("AlistT"), bytes(at)),
        (symbol("fd_50F6_037C"), bytes(corpse_x)),
        (symbol("fd_50F6_0404"), bytes(corpse_y)),
        (symbol("fd_3D57_07A8"), b"".join(word(v) for v in options)),
    ])
    life_base, map_base = symbol("LifeA"), symbol("MapA")
    for x, y, value in life_cells:
        life_base_index = x * 64 + y
        life[x * 64 + y] = value & 0xff
        writes.append((life_base + life_base_index, bytes((value & 0xff,))))
    for i, (x, y, value) in enumerate(ants):
        ax[i], ay[i], at[i] = x & 0xff, y & 0xff, value & 0xff
        writes.extend(((symbol("AlistX") + i, bytes((ax[i],))),
                       (symbol("AlistY") + i, bytes((ay[i],))),
                       (symbol("AlistT") + i, bytes((at[i],)))))
    for x, y, value in terrain_cells:
        map_a[x * 64 + y] = value & 0xff
        writes.append((map_base + x * 64 + y, bytes((value & 0xff,))))

    # Install the same actual transformed resource the native initializer uses.
    table = load_sine_resource()
    linear = 0xD0100
    writes.extend([
        (symbol("fd_50F6_0B22"), word(0x0100) + word(0xD000)),
        (linear, b"".join((v & 0xffff).to_bytes(2, "little") for v in table)),
    ])
    ranges = [behavior.Range(n, symbol(n), size) for n, size in [
        ("LifeA", 8192), ("MapA", 8192), ("AlistX", 1000),
        ("AlistY", 1000), ("AlistT", 1000), ("fd_50F6_037C", 100),
        ("fd_50F6_0404", 100), ("RAntsEaten", 4), ("BAntsEaten", 4),
        ("g_8BA2", 2), ("fd_50F6_0476", 2),
    ] + [(n, 2) for n, _ in SPIDER_FIELDS + TICK_FIELDS + WORLD_FIELDS]]
    return behavior.Case(label=label, writes=writes, observe=ranges,
        callbacks=callbacks(route_result), return_kind="void",
        state={"route_result": route_result}, metadata={"tick": label})


def s16(data):
    value = int.from_bytes(data, "little")
    return value - 0x10000 if value >= 0x8000 else value


def signed32(data):
    return int.from_bytes(data, "little", signed=True)


def bytes_for(machine_result, name):
    return bytes.fromhex(machine_result["ranges"][name])


def extract_input(case):
    vals = {"spider": [0] * 17, "tick": [0] * 3, "world": [0] * 7,
            "eaten": [0, 0], "options": [0] * 6, "seed": 0xace1,
            "corpse_x": bytearray(100), "corpse_y": bytearray(100),
            "life": bytearray(8192), "map": bytearray(8192),
            "ax": bytearray(1000), "ay": bytearray(1000), "at": bytearray(1000),
            "count": 0, "corpse_base": 0, "corpse_index": 0,
            "route": case.state.get("route_result", -2)}
    addr_fields = {}
    for i, (name, _) in enumerate(SPIDER_FIELDS): addr_fields[symbol(name)] = ("spider", i)
    for i, (name, _) in enumerate(TICK_FIELDS): addr_fields[symbol(name)] = ("tick", i)
    for i, (name, _) in enumerate(WORLD_FIELDS): addr_fields[symbol(name)] = ("world", i)
    array_ranges = [
        ("life", symbol("LifeA"), 8192), ("map", symbol("MapA"), 8192),
        ("ax", symbol("AlistX"), 1000), ("ay", symbol("AlistY"), 1000),
        ("at", symbol("AlistT"), 1000),
        ("corpse_x", symbol("fd_50F6_037C"), 100),
        ("corpse_y", symbol("fd_50F6_0404"), 100),
    ]
    for address, data in case.writes:
        target = addr_fields.get(address)
        if target and len(data) >= 2:
            bucket, i = target
            vals[bucket][i] = s16(data)
            continue
        if address == symbol("ListIndexA"): vals["count"] = s16(data[:2]); continue
        if address == symbol("g_8BA2"): vals["seed"] = int.from_bytes(data[:2], "little"); continue
        if address == symbol("fd_50F6_0476"): vals["corpse_index"] = s16(data[:2]); continue
        if address == symbol("RAntsEaten"): vals["eaten"][0] = signed32(data[:4]); continue
        if address == symbol("BAntsEaten"): vals["eaten"][1] = signed32(data[:4]); continue
        if address == symbol("fd_3D57_07A8"):
            vals["options"] = [int.from_bytes(data[i:i+2], "little") for i in range(0, 12, 2)]
            continue
        for name, base, size in array_ranges:
            start = address - base
            if start >= 0 and start + len(data) <= size:
                vals[name][start:start + len(data)] = data
                break
    return vals


class Inputs(ct.Structure):
    _fields_ = [("spider", ct.c_int16 * 17), ("tick", ct.c_int16 * 3),
                ("world", ct.c_int16 * 7), ("eaten", ct.c_int32 * 2),
                ("options", ct.c_uint8 * 6), ("seed", ct.c_uint16),
                ("route", ct.c_int16), ("count", ct.c_int16),
                ("life", ct.c_uint8 * 8192), ("map", ct.c_uint8 * 8192),
                ("ax", ct.c_uint8 * 1000), ("ay", ct.c_uint8 * 1000),
                ("at", ct.c_uint8 * 1000), ("cx", ct.c_uint8 * 100),
                ("cy", ct.c_uint8 * 100), ("corpse_base", ct.c_int16), ("corpse_index", ct.c_int16)]


def build_library():
    LIBRARY.parent.mkdir(parents=True, exist_ok=True)
    cmd = [str(GCC), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", "-shared",
           "-I", str(ROOT / "portable/game/simulation"),
           "-I", str(ROOT / "portable/game/state"),
           str(ROOT / "portable/tests/spider_sim/native_bridge.c"),
           str(ROOT / "portable/game/simulation/spider_sim.c"),
           str(ROOT / "portable/game/simulation/spider.c"),
           str(ROOT / "portable/game/simulation/rng.c"),
           str(ROOT / "portable/game/simulation/movement.c"), "-o", str(LIBRARY)]
    subprocess.run(cmd, check=True, cwd=ROOT)
    return cmd, hashlib.sha256(LIBRARY.read_bytes()).hexdigest()


def configure(lib):
    p8 = ct.POINTER(ct.c_uint8)
    p16 = ct.POINTER(ct.c_int16)
    p32 = ct.POINTER(ct.c_int32)
    lib.spider_tick_test.argtypes = [p16, p16, p16, p32, p8, ct.c_uint16,
        ct.c_int16, ct.c_int16] + [p8] * 7 + [p8] * 5 + [p16, p16, p16, p32,
        ct.POINTER(ct.c_uint16), ct.POINTER(ct.c_uint16), p8, p16, p16, p16]
    lib.spider_tick_test.restype = ct.c_int


def as_array(ctype, data):
    return (ctype * len(data)).from_buffer_copy(data)


def native_call(lib, values):
    v = Inputs()
    for field in ("spider", "tick", "world", "eaten", "options"):
        getattr(v, field)[:] = values[field]
    for field in ("seed", "route", "count", "corpse_base", "corpse_index"):
        setattr(v, field, values[field])
    for field, source in (("life", "life"), ("map", "map"), ("ax", "ax"),
                          ("ay", "ay"), ("at", "at"), ("cx", "corpse_x"),
                          ("cy", "corpse_y")):
        getattr(v, field)[:] = values[source]
    out_life, out_map = (ct.c_uint8 * 8192)(), (ct.c_uint8 * 8192)()
    out_at, out_cx, out_cy = (ct.c_uint8 * 1000)(), (ct.c_uint8 * 100)(), (ct.c_uint8 * 100)()
    out_spider, out_tick, out_world = (ct.c_int16 * 17)(), (ct.c_int16 * 3)(), (ct.c_int16 * 7)()
    out_eaten, out_seed, out_count = (ct.c_int32 * 2)(), ct.c_uint16(), ct.c_uint16()
    out_overflow, out_status, out_events = ct.c_uint8(), ct.c_int16(), (ct.c_int16 * 192)()
    out_corpse_index = ct.c_int16(v.corpse_index)
    lib.spider_tick_test(v.spider, v.tick, v.world, v.eaten, v.options, v.seed,
        v.route, v.count, v.life, v.map, v.ax, v.ay, v.at, v.cx, v.cy,
        out_life, out_map, out_at, out_cx, out_cy, out_spider, out_tick,
        out_world, out_eaten, ct.byref(out_seed), ct.byref(out_count),
        ct.byref(out_overflow), ct.byref(out_status), out_events, ct.byref(out_corpse_index))
    return {"life": bytes(out_life), "map": bytes(out_map), "at": bytes(out_at),
        "cx": bytes(out_cx), "cy": bytes(out_cy), "spider": list(out_spider),
        "tick": list(out_tick), "world": list(out_world), "eaten": list(out_eaten),
        "seed": out_seed.value, "count": out_count.value,
        "overflow": out_overflow.value, "status": out_status.value,
        "events": [list(out_events[i*6:i*6+6]) for i in range(out_count.value)],
        "corpse_index": out_corpse_index.value}


def compare_case(machine, lib, case):
    values = extract_input(case)
    native = native_call(lib, values)
    oracle = machine.run(case)
    expected = {
        "spider": [s16(bytes_for(oracle, n)) for n, _ in SPIDER_FIELDS],
        "tick": [s16(bytes_for(oracle, n)) for n, _ in TICK_FIELDS],
        "world": [s16(bytes_for(oracle, n)) for n, _ in WORLD_FIELDS],
        "eaten": [signed32(bytes_for(oracle, "RAntsEaten")), signed32(bytes_for(oracle, "BAntsEaten"))],
        "seed": int.from_bytes(bytes_for(oracle, "g_8BA2"), "little"),
        "life": bytes_for(oracle, "LifeA"), "map": bytes_for(oracle, "MapA"),
        "ax": bytes_for(oracle, "AlistX"), "ay": bytes_for(oracle, "AlistY"),
        "at": bytes_for(oracle, "AlistT"), "cx": bytes_for(oracle, "fd_50F6_037C"),
        "cy": bytes_for(oracle, "fd_50F6_0404"),
        "corpse_index": s16(bytes_for(oracle, "fd_50F6_0476")),
    }
    actual_events = []
    for entry in oracle["trace"]:
        name = entry["name"]
        kind = EVENT_NAMES.get(name)
        if kind is not None:
            args = [((v & 0xffff) - 0x10000 if (v & 0x8000) else (v & 0xffff))
                    for v in entry["args"]]
            actual_events.append([kind] + args[:5] + [0] * (5 - len(args[:5])))
    expected["events"] = actual_events
    actual = {**native, "ax": bytes_for(oracle, "AlistX"), "ay": bytes_for(oracle, "AlistY")}
    # Native only changes the list type field; the coordinate arrays are invariant.
    comparisons = [
        ("status", native["status"], 0),
        ("event_overflow", native["overflow"], 0),
        ("spider", native["spider"], expected["spider"]),
        ("tick", native["tick"], expected["tick"]),
        ("world", native["world"], expected["world"]),
        ("eaten", native["eaten"], expected["eaten"]),
        ("seed", native["seed"], expected["seed"]),
        ("life", native["life"], expected["life"]),
        ("map", native["map"], expected["map"]),
        ("ant_type", native["at"], expected["at"]),
        ("ant_x", actual["ax"], expected["ax"]),
        ("ant_y", actual["ay"], expected["ay"]),
        ("corpse_x", native["cx"], expected["cx"]),
        ("corpse_y", native["cy"], expected["cy"]),
        ("corpse_index", native["corpse_index"], expected["corpse_index"]),
        ("events", native["events"], expected["events"]),
    ]
    mismatch = next(((name, got, want) for name, got, want in comparisons if got != want), None)
    if mismatch:
        name, got, want = mismatch
        return {"case": case.label, "mismatch": name,
                "native": str(got)[:300], "original": str(want)[:300],
                "original_trace": oracle["trace"]}
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--random-count", type=int, default=0)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()
    cmd, lib_hash = build_library()
    lib = ct.CDLL(str(LIBRARY))
    configure(lib)
    machine = machine_for_original()
    spider_defaults = [0, 0x400, 0x200, 10, 0, 0, 0, 3, 0, 0, 1, 0, 0, -2, -1, 64, 64]
    tick_defaults = [0, 0, 0]
    world_defaults = [1, 1, 0x40, 0x20, 0x10, 2, 0]
    options = [0] * 6
    cases = []
    cases.append(make_case("mode0-idle", spider_defaults.copy(), tick_defaults.copy(),
        world_defaults.copy(), [0, 0], options, 0xace1))
    for mode in range(6):
        s = spider_defaults.copy(); s[11] = mode
        s[7] = 2 # skip ScanForAnts unless a directed case requests it
        cases.append(make_case(f"mode-{mode}-seed-a", s, tick_defaults.copy(),
            world_defaults.copy(), [3, 4], options, 0x1234 + mode))
    # Forced branches: user route, tracked target, near-eat, death completion,
    # local ant pressure, and true SpiderScan path.
    s=spider_defaults.copy(); s[7]=2; cases.append(make_case("player-route-forward",s,[1,1,0],world_defaults.copy(),[0,0],options,0x31,route_result=2))
    s=spider_defaults.copy(); s[7]=2; s[11]=2; s[13]=0; s[14]=0x10
    cases.append(make_case("chase-ant",s,[0,0,0],[1,1,64,32,0x10,2,0],[0,0],options,0x35,ant_count=1,ants=[(65,32,0x10)]))
    s=spider_defaults.copy(); s[7]=2; s[11]=2; s[13]=0; s[14]=0x10; s[1]=0x400; s[2]=0x200
    cases.append(make_case("eat-ant",s,[0,0,0],[1,1,64,32,0x10,2,0],[0,0],options,0x39,ant_count=1,ants=[(64,32,0x10)],life_cells=[(64,32,0x10)]))
    s=spider_defaults.copy(); s[7]=2; s[11]=5
    cases.append(make_case("death-complete",s,[0,0,1],world_defaults.copy(),[0,0],options,0x3d))
    s=spider_defaults.copy(); s[7]=3; s[12]=8
    cells=[(63+i,31+j,0x10) for i in range(3) for j in range(3)]
    cases.append(make_case("pressure-spider-scan",s,tick_defaults.copy(),world_defaults.copy(),[0,0],options,0x41,life_cells=cells))
    if args.random_count:
        import random
        rng = random.Random(0xCDB00B3)
        for i in range(args.random_count):
            s=spider_defaults.copy(); s[0]=rng.randrange(8); s[1]=rng.randrange(0x200,0x600); s[2]=rng.randrange(0x100,0x400)
            s[6]=rng.randrange(0x400); s[7]=rng.randrange(4); s[8]=rng.randrange(7); s[9]=rng.randrange(2)
            s[10]=1; s[11]=rng.randrange(6); s[12]=rng.choice([0,1,6,7,8]); s[13]=-2; s[14]=-1
            t=[rng.choice([0,1]),rng.randrange(2),rng.randrange(501)]
            w=world_defaults.copy(); w[1]=rng.choice([1,2]); w[2]=rng.randrange(128); w[3]=rng.randrange(64); w[6]=rng.randrange(2)
            opts=[rng.randrange(2) for _ in range(6)]
            route=rng.choice([-2,-1,*range(8)])
            cells=[]
            ants=[]
            for _ in range(rng.randrange(4)):
                ax=rng.randrange(128); ay=rng.randrange(64); typ=rng.choice([0x10,0x20,0x30,0x80,0xff])
                ants.append((ax,ay,typ)); cells.append((ax,ay,typ))
            cases.append(make_case(f"random-{i:04d}",s,t,w,[rng.randrange(20),rng.randrange(20)],opts,
                rng.randrange(1,65536),ant_count=len(ants),ants=ants,life_cells=cells,route_result=route))
    if args.limit is not None:
        cases = cases[:args.limit]
    mismatches=[]
    for i, case in enumerate(cases):
        mismatch=compare_case(machine,lib,case)
        if mismatch:
            mismatches.append(mismatch)
            break
        if (i+1)%25==0:
            print(f"original-DOS MoveSpider cases={i+1}",flush=True)
    paths=[ROOT/"portable/game/simulation/spider_sim.c",ROOT/"portable/game/simulation/spider_sim.h",
           ROOT/"portable/game/simulation/spider.c",ROOT/"portable/game/simulation/spider.h",
           ROOT/"portable/game/simulation/rng.c",ROOT/"portable/game/simulation/rng.h",
           ROOT/"portable/game/simulation/movement.c",ROOT/"portable/game/simulation/movement.h",
           ROOT/"portable/game/state/world.h",ROOT/"portable/tests/spider_sim/native_bridge.c",
           ROOT/"portable/tests/spider_sim/run_dos_diff.py",ROOT/"tools/behavior.py",
           ROOT/"tools/functions.py",ROOT/"tools/exe.py",ROOT/"src/root/m0CDB.c",
           ROOT/"src/root/m0894.c",ROOT/"assets/SHARED.NDX",ROOT/"assets/SHARED.DAT"]
    report={"schema":"native-dos-spider-tick-differential-v1","target":"MoveSpider / f_0CDB_00B3",
        "oracle_sha256":exe.load().sha256,"source_hashes":{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        "suite":"directed source branch cases plus optional seeded randomized cases","cases":len(cases),
        "passed":len(cases)-len(mismatches),"mismatches":mismatches,"seed":0xCDB00B3,
        "modeled_boundaries":["o25_39C7_0CBD route return","myBeginSound","PictStrnDialog","YellowDeath","MoveMyLife","f_0BE8_0812","f_015B_06A2","DoLaserFire"],
        "native_library_sha256":lib_hash,"compile_command":cmd}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"cases":len(cases),"passed":report["passed"],"mismatches":mismatches[:1],"report":str(args.report)},indent=2))
    if mismatches: raise SystemExit(1)

if __name__ == "__main__":
    main()
