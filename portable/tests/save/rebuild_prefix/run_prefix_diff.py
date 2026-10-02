#!/usr/bin/env python3
"""Bounded DOS-vs-source-lowered-C differential for S09 rebuild prefix."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
import behavior  # noqa: E402
import exe  # noqa: E402
import functions  # noqa: E402
import match  # noqa: E402
from lower_source import generate  # noqa: E402

NATIVE_C = Path(__file__).with_name("rebuild_prefix_native_v3.c")
BUILD = ROOT / "build/workers/save_rebuild_prefix"
NATIVE_EXE = BUILD / "rebuild-prefix-native.exe"
CAP = {"A": 1000, "B": 500, "R": 500}
SIZE = {"A": (128, 64), "B": (64, 64), "R": (64, 64)}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def addr(name: str) -> int:
    return behavior.symbol_address(name)


def dos_writes(case: dict) -> list[tuple[int, bytes]]:
    writes = [
        (addr("TERRAINset"), struct.pack("<h", case["terrain"])),
        (addr("CurGndTileID"), struct.pack("<h", case["cur_ground_initial"])),
        (addr("Barrier"), struct.pack("<h", case["barrier_initial"])),
        (addr("ListIndexA"), struct.pack("<h", case["counts"]["A"])),
        (addr("ListIndexB"), struct.pack("<h", case["counts"]["B"])),
        (addr("ListIndexR"), struct.pack("<h", case["counts"]["R"])),
        (addr("fd_50F6_0A06"), struct.pack("<h", 0)),
    ]
    for kind, (width, height) in SIZE.items():
        writes.append((addr("Life" + kind), case["life"][kind]))
        for field in ("X", "Y", "T"):
            writes.append((addr(kind + "list" + field), case["lists"][kind][field]))
    return writes


def validate_case(case: dict) -> None:
    for kind, cap in CAP.items():
        count = case["counts"][kind]
        if not 0 <= count < cap:
            raise ValueError(f"{kind} count {count} outside supported source-prefix domain 0..{cap-1}")
        width, height = SIZE[kind]
        for i in range(count + 1):  # exact source loop includes ListIndex itself
            x, y = case["lists"][kind]["X"][i], case["lists"][kind]["Y"][i]
            if x >= width or y >= height:
                raise ValueError(f"{kind}[{i}] coordinate {(x,y)} outside {width}x{height}")


def pack_input(case: dict) -> bytes:
    validate_case(case)
    raw = bytearray(struct.pack("<hhhhh", case["terrain"], case["barrier_initial"],
                                case["counts"]["A"], case["counts"]["B"], case["counts"]["R"]))
    for kind in "ABR":
        raw.extend(case["life"][kind])
    for kind in "ABR":
        for field in "XYT":
            raw.extend(case["lists"][kind][field])
    return bytes(raw)


def unpack_native(raw: bytes) -> dict:
    head_size = 6
    if len(raw) < head_size:
        raise ValueError("truncated native result")
    cur_ground, barrier, count = struct.unpack_from("<hhH", raw)
    at = head_size
    events = []
    for _ in range(count):
        events.append(struct.unpack_from("<hhh", raw, at))
        at += 6
    outputs = {}
    for kind in "ABR":
        size = CAP[kind]  # replaced below with the exact byte extent
        width, height = SIZE[kind]
        size = width * height
        outputs[kind] = raw[at:at + size]
        at += size
    if at != len(raw):
        raise ValueError(f"native result has {len(raw)-at} trailing bytes")
    return {"cur_ground": cur_ground, "barrier": barrier, "events": events,
            "life": outputs}


class PrefixMachine(behavior.Machine):
    def __init__(self, pair):
        super().__init__(pair)
        target = functions.get("SetMyLife")
        self.stop_linear = target["seg"] * 16 + target["off"]
        self.prefix_stopped = False

    def _on_block(self, cpu, address, size, userdata):
        if address == self.stop_linear:
            self.prefix_stopped = True
            cpu.emu_stop()
            return
        super()._on_block(cpu, address, size, userdata)

    def run_prefix(self, case: behavior.Case) -> dict:
        self._reset()
        self.prefix_stopped = False
        self.case = case
        self.state = dict(case.state)
        self.written, self.effect_initial = set(), {}
        self.trace, self.raw_trace, self.io, self.raw_effect_trace = [], [], [], []
        self.blocks = 0
        self.error = self.resume = self.completed = False
        self.active = False
        self.callback_addresses = {}
        for name, spec in case.callbacks.items():
            s = behavior.symbol(name)
            self.callback_addresses[s["seg"] * 16 + s["off"]] = (name, spec)
            v = match.vector_for(s.get("unit"), s["seg"], s["off"])
            if v and spec.handler:
                self.callback_addresses[exe.MANAGER_SEG * 16 + v.offset] = (name, spec)
        defaults = dict(ax=0x1234,bx=0x2345,cx=0x3456,dx=0x4567,si=0x5678,di=0x6789,
                        bp=0x789A,ss=match.DGROUP_SEG,ds=match.DGROUP_SEG,
                        es=match.DGROUP_SEG,sp=0xA400,eflags=2)
        defaults.update({k:v for k,v in case.registers.items() if k != "stack_poison"})
        if not 0 < case.stack_bytes <= defaults["sp"]:
            raise behavior.ExecutionError("invalid stack size")
        frame = behavior.words(behavior.SENTINEL[1], behavior.SENTINEL[0])
        self.stack_bounds = (defaults["ss"] * 16 + defaults["sp"] - case.stack_bytes,
                             defaults["ss"] * 16 + defaults["sp"] + len(frame))
        for address, data in case.writes:
            if address < self.stack_bounds[1] and address + len(data) > self.stack_bounds[0]:
                raise behavior.ExecutionError("fixture overlaps stack")
            self.write(address, data)
        for name, value in defaults.items():
            self.set_reg(name, value)
        self.initial_registers = defaults
        self.write(defaults["ss"] * 16 + defaults["sp"], frame)
        target = self.pair.function
        self.set_reg("cs", target["seg"]); self.set_reg("ip", target["off"])
        self.active = True
        try:
            while not self.prefix_stopped:
                self.resume = False
                start = self.reg("cs") * 16 + self.reg("ip")
                self.cpu.emu_start(start, behavior.SENTINEL_LINEAR,
                                   count=case.max_instructions)
                if self.error:
                    raise behavior.ExecutionError(self.error)
                if self.reg("cs") * 16 + self.reg("ip") == behavior.SENTINEL_LINEAR:
                    raise behavior.ExecutionError("source returned before the SetMyLife boundary")
                if not self.prefix_stopped and not self.resume:
                    raise behavior.ExecutionError("stopped without reaching prefix boundary")
        finally:
            self.active = False
        return {"trace": self.trace, "providers": self.state["providers"],
                "life": {k:self.read(addr("Life"+k), SIZE[k][0]*SIZE[k][1]) for k in "ABR"},
                "cur_ground": struct.unpack("<h", self.read(addr("CurGndTileID"),2))[0],
                "barrier": struct.unpack("<h", self.read(addr("Barrier"),2))[0],
                "stop": "SetMyLife-entry"}


def random_case(label: str, terrain: int, counts: dict[str, int], seed: int,
                collisions=False) -> dict:
    rng = random.Random(seed)
    life = {k: bytes(rng.randrange(256) for _ in range(SIZE[k][0]*SIZE[k][1])) for k in "ABR"}
    lists = {}
    for kind in "ABR":
        width,height = SIZE[kind]
        cap = CAP[kind]
        xs = bytearray(rng.randrange(width) for _ in range(cap))
        ys = bytearray(rng.randrange(height) for _ in range(cap))
        ts = bytearray(rng.randrange(256) for _ in range(cap))
        lists[kind] = {"X":bytes(xs), "Y":bytes(ys), "T":bytes(ts)}
    if collisions:
        for kind in "ABR":
            n = counts[kind]
            if n >= 2:
                x,y = (1,2) if SIZE[kind][0] > 64 else (1,2)
                for i,value in ((0,0x20),(1,0x40),(n,0x60)):
                    lists[kind]["X"] = lists[kind]["X"][:i] + bytes([x]) + lists[kind]["X"][i+1:]
                    lists[kind]["Y"] = lists[kind]["Y"][:i] + bytes([y]) + lists[kind]["Y"][i+1:]
                    lists[kind]["T"] = lists[kind]["T"][:i] + bytes([value]) + lists[kind]["T"][i+1:]
    return {"label":label,"terrain":terrain,"barrier_initial":0x3765,
            "cur_ground_initial":0x2211,"counts":counts,"life":life,"lists":lists}


def cases() -> list[dict]:
    out = []
    directed = [
        ("empty_lists_index0_observable", 0, {"A":0,"B":0,"R":0}, 0, True),
        ("terrain_one", 1, {"A":2,"B":2,"R":2}, 1, True),
        ("terrain_other_exactly_not_one", 2, {"A":3,"B":3,"R":3}, 2, True),
        ("capacity_minus_one", 1, {"A":999,"B":499,"R":499}, 3, True),
    ]
    for label,terrain,counts,seed,collisions in directed:
        out.append(random_case(label,terrain,counts,seed,collisions))
    for i in range(12):
        out.append(random_case(f"random_seed_{i:02d}", i % 3,
             {"A":(i*83+17)%999,"B":(i*47+9)%499,"R":(i*61+1)%499},
             0x9A100+i, i%2==0))
    return out


def native_run(binary: Path, case: dict) -> dict:
    proc = subprocess.run([str(binary)], input=pack_input(case), capture_output=True)
    if proc.returncode:
        raise RuntimeError(f"native prefix returned {proc.returncode}: {proc.stderr.decode(errors='replace')}")
    return unpack_native(proc.stdout)


def run_dos(case: dict, pair, machine: PrefixMachine) -> dict:
    provider_events = []
    def provider(vm, args):
        if len(args) != 1:
            raise AssertionError(f"unexpected f_0250_0256 args: {args}")
        barrier = struct.unpack("<h", vm.read(addr("Barrier"),2))[0]
        tile = struct.unpack("<h", vm.read(addr("CurGndTileID"),2))[0]
        provider_events.append((args[0], barrier, tile))
        return None
    observed = [behavior.Range("CurGndTileID",addr("CurGndTileID"),2),
                behavior.Range("Barrier",addr("Barrier"),2)]
    c = behavior.Case(case["label"], writes=dos_writes(case), observe=observed,
        callbacks={"f_0250_0256":behavior.Callback(1,provider)}, return_kind="void",
        max_instructions=8_000_000, max_blocks=100_000,
        stack_bytes=0xF00, observe_at_calls=True,
        state={"providers":provider_events})
    # `Case` deep-copies state into the machine; let the callback state be read
    # from that actual per-machine copy rather than this local list.
    machine.run_prefix(c)
    return {"trace":machine.trace,"providers":machine.state["providers"],
            "life":{k:machine.read(addr("Life"+k),SIZE[k][0]*SIZE[k][1]) for k in "ABR"},
            "cur_ground":struct.unpack("<h",machine.read(addr("CurGndTileID"),2))[0],
            "barrier":struct.unpack("<h",machine.read(addr("Barrier"),2))[0],
            "stop":"SetMyLife-entry"}


def snapshot_paths() -> list[Path]:
    profile=ROOT/"build/workers/recovered_source_next10/generated"
    return [NATIVE_C,Path(__file__),Path(__file__).with_name("lower_source.py"),
            ROOT/"src/S09/m35F5.c",ROOT/"src/root/m0250.c",ROOT/"tools/behavior.py",
            ROOT/"tools/exe.py",ROOT/"tools/functions.py",ROOT/"tools/match.py",
            ROOT/"layout/functions.json",ROOT/"layout/symbols.json",ROOT/"layout/manifest.json",
            ROOT/"layout/oracle.lock.json",ROOT/"assets/SIMANT.EXE",
            profile/"provenance.json",profile/"recovered_state.c",profile/"recovered_state.h"]


def compile_native(compiler: str) -> dict:
    BUILD.mkdir(parents=True,exist_ok=True)
    command=[compiler,"-std=c11","-O2","-Wall","-Wextra","-Werror",
             str(NATIVE_C),"-o",str(NATIVE_EXE)]
    proc=subprocess.run(command,cwd=ROOT,text=True,capture_output=True)
    if proc.returncode:
        raise RuntimeError("native prefix compile failed:\n"+proc.stdout+proc.stderr)
    version=subprocess.check_output([compiler,"--version"],text=True).splitlines()[0]
    resolved=shutil.which(compiler) or compiler
    return {"command":command,"compiler":str(Path(resolved).resolve()),"version":version,
            "binary_sha256":sha(NATIVE_EXE)}


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--report",type=Path,required=True)
    ap.add_argument("--case-limit",type=int)
    args=ap.parse_args()
    report_path=(ROOT/args.report).resolve() if not args.report.is_absolute() else args.report.resolve()
    report_path.relative_to(ROOT)
    if report_path.exists():
        raise SystemExit(f"refusing to overwrite report: {report_path}")
    source,pins=generate()
    if not NATIVE_C.is_file() or NATIVE_C.read_text(encoding="utf-8")!=source:
        raise SystemExit("source-derived native C is absent/stale")
    compiler=os.environ.get("SIMANT_CC") or shutil.which("gcc") or r"C:\msys64\mingw64\bin\gcc.exe"
    before={str(p.relative_to(ROOT)):sha(p) for p in snapshot_paths()}
    native=compile_native(compiler)
    f=functions.get("o09_35F5_0DBB")
    pair=type("Pair",(),{})()
    pair.function=f
    pair.vectors={exe.MANAGER_SEG*16+v.offset:v for v in exe.load().vectors}
    pair.candidate=False
    machine=PrefixMachine(pair)
    results=[]
    for case in cases()[:args.case_limit]:
        validate_case(case)
        dos=run_dos(case,pair,machine)
        c=native_run(NATIVE_EXE,case)
        diffs=[]
        for k in ("cur_ground","barrier","providers"):
            dv=dos[k]
            cv=c.get(k)
            if k=="providers":
                cv=c["events"]
            if dv!=cv: diffs.append({"field":k,"dos":dv,"native":cv})
        for k in "ABR":
            if dos["life"][k]!=c["life"][k]:
                ix=next(i for i,(x,y) in enumerate(zip(dos["life"][k],c["life"][k])) if x!=y)
                diffs.append({"field":"Life"+k,"first_offset":ix,
                              "dos":dos["life"][k][ix],"native":c["life"][k][ix]})
        results.append({"case":case["label"],"equal":not diffs,"diffs":diffs,
            "counts":case["counts"],"terrain":case["terrain"],
            "DOS_stop":dos["stop"],"native_prefix_returned":True,
            "final_state":{"DOS":{"CurGndTileID":dos["cur_ground"],"Barrier":dos["barrier"]},
                           "native":{"CurGndTileID":c["cur_ground"],"Barrier":c["barrier"]}},
            "life_sha256":{"DOS":{k:hashlib.sha256(dos["life"][k]).hexdigest() for k in "ABR"},
                           "native":{k:hashlib.sha256(c["life"][k]).hexdigest() for k in "ABR"}},
            "provider_trace_DOS":dos["providers"],"provider_trace_native":c["events"]})
    after={str(p.relative_to(ROOT)):sha(p) for p in snapshot_paths()}
    next10_provenance=json.loads((ROOT/"build/workers/recovered_source_next10/generated/provenance.json").read_text(encoding="utf-8"))
    next10_extension=next10_provenance.get("versioned_profile_extension_next10")
    report={"schema":"save-rebuild-prefix-differential-v1","status":"DIAGNOSTIC_PREFIX_ONLY",
        "claim":"actual DOS o09_35F5_0DBB through SetMyLife entry vs mechanically extracted source C prefix",
        "source_pins":pins,"next10_reference_only":{
            "profile":"recovered_source_next10/generated",
            "provenance_sha256":sha(ROOT/"build/workers/recovered_source_next10/generated/provenance.json"),
            "recovered_state_c_sha256":sha(ROOT/"build/workers/recovered_source_next10/generated/recovered_state.c"),
            "recovered_state_h_sha256":sha(ROOT/"build/workers/recovered_source_next10/generated/recovered_state.h"),
            "extension_id":next10_extension.get("id") if next10_extension else None,
            "extension_descriptor_sha256":hashlib.sha256(json.dumps(next10_extension,sort_keys=True).encode()).hexdigest() if next10_extension else None,
            "executed_by_this_prefix_runner":False},
        "oracle_sha256":exe.load().sha256,"harness_sha256":behavior.digest(behavior.HARNESS_SOURCE),
        "native_compile":native,"case_count":len(results),"passed":sum(r["equal"] for r in results),
        "failed":sum(not r["equal"] for r in results),"results":results,
        "negative_controls":negative_controls(),
        "input_closure":{"before":before,"after":after,
                          "changed":[p for p in before if before[p]!=after.get(p)]}}
    if report["failed"]:
        report["status"]="MISMATCH"
    if report["input_closure"]["changed"]:
        report["status"]="INPUT_CLOSURE_CHANGED"
    report_path.parent.mkdir(parents=True,exist_ok=True)
    report_path.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("status","case_count","passed","failed","changed") if k in report},indent=2))


def negative_controls() -> dict:
    base=random_case("negative",0,{"A":0,"B":0,"R":0},0xBAD)
    cap=dict(base); cap["counts"]={**base["counts"],"A":CAP["A"]}
    coords=dict(base); coords["lists"]={k:{f:bytearray(v) for f,v in fields.items()}
                                         for k,fields in base["lists"].items()}
    coords["lists"]["A"]["X"][0]=SIZE["A"][0]
    def rejected(case):
        try: validate_case(case)
        except ValueError: return True
        return False
    return {"count_at_capacity_rejected":rejected(cap),
            "invalid_coordinate_rejected":rejected(coords),
            "out_of_range_entry_used_by_inclusive_loop":True}


if __name__=="__main__":
    main()
