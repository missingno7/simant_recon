"""Bounded DOS/native differential for StopSong's two cleanup helpers.

This runner verifies the MSC candidates against the frozen DOS oracle and a
small native C contract model. The actual manager/device leaves are explicit
callbacks and are reported as exclusions; this is diagnostic evidence only.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
import behavior  # noqa: E402

OUT = ROOT / "portable/tests/audio/stop_song_dependencies/evidence/dependencies-v4.json"
BUILD = ROOT / "build/workers/audio_stop_song_dependencies/final"
NATIVE = ROOT / "portable/tests/audio/stop_song_dependencies/helper_contract.c"
DOS_SHA = "aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11"
RELEASE_SOURCE = ROOT / "src/root/m0000.c"
RESET_SOURCE = ROOT / "src/root/m295C.c"
INPUTS = [RELEASE_SOURCE, RESET_SOURCE, ROOT / "src/root/m171C.c",
          ROOT / "src/root/m277E.c", ROOT / "src/root/m284A.c",
          ROOT / "portable/tests/audio/stop_song_dependencies/run_dependencies.py",
          NATIVE, ROOT / "tools/behavior.py", ROOT / "tools/exe.py",
          ROOT / "tools/functions.py", ROOT / "tools/match.py",
          ROOT / "tools/modctx.py", ROOT / "tools/modules.py",
          ROOT / "tools/compiler.py", ROOT / "tools/omf.py",
          ROOT / "tools/symbols.py", ROOT / "tools/autosearch.py",
          ROOT / "portable/tests/audio/stop_song/evidence/stop-song-contract-v2.json",
          ROOT / "portable/research/audio_stop_song_contract.md",
          ROOT / "layout/functions.json", ROOT / "layout/symbols.json",
          ROOT / "layout/manifest.json", ROOT / "layout/toolchain.json",
          ROOT / "layout/oracle.lock.json", ROOT / "assets/SIMANT.EXE"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rel(p: Path) -> str:
    try: return p.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError: return str(p.resolve()).replace("\\", "/")


def hashes(paths):
    return {rel(p): sha(p) for p in sorted(set(paths), key=lambda q: str(q).casefold())}


def runtime_files():
    root = ROOT / "build/behavior/deps/unicorn"
    return [p for p in root.rglob("*") if p.is_file() and
            (p.suffix.lower() == ".py" or p.name.lower() == "unicorn.dll")]


def msc_files():
    tc = json.loads((ROOT / "layout/toolchain.json").read_text())
    cfg = tc["profiles"]["msc600ax"]
    return [(Path(cfg["directory"]) / x).resolve() for x in sorted(cfg["files"])]


def gcc_files(cc):
    out = [cc.resolve()]
    for tool in ("cc1", "collect2", "ld", "as"):
        value = subprocess.check_output([str(cc), f"-print-prog-name={tool}"], text=True).strip()
        p = Path(value)
        if not p.is_absolute(): p = cc.parent / p
        out.append(p.resolve())
    return out


def compile_native(cc, destination):
    proc = subprocess.run([str(cc), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
                           str(NATIVE), "-o", str(destination)], cwd=ROOT,
                          capture_output=True, text=True)
    if proc.returncode:
        raise RuntimeError(proc.stdout + proc.stderr)


def native_events(exe, label):
    p = subprocess.run([str(exe), label], cwd=ROOT, capture_output=True, text=True, check=True)
    result = []
    for line in p.stdout.splitlines():
        head, *items = line.split("|")
        fields = dict(x.split("=", 1) for x in items if "=" in x)
        if head in ("free_song_data", "free_sample_data"):
            result.append({"kind": head, "handle": int(fields["handle"])})
        elif head == "flush_begin":
            result.append({"kind": head, "count": int(fields["count"]),
                           "samples": [int(x) for x in fields["samples"].split(",") if x]})
        elif head == "flush_end":
            result.append({"kind": head, "count": int(fields["count"])})
        elif head == "release_call":
            result.append({"kind": head, "index": int(fields["index"]),
                           "busy": int(fields["busy"])})
        elif head == "queue_state":
            result.append({"kind": head, "count": int(fields["count"]),
                           "song_handle": int(fields["song_handle"])})
        elif head == "sample":
            result.append({"kind": head, "index": int(fields["index"]),
                           "loaded": int(fields["loaded"]), "data": int(fields["data"])})
        elif head == "noteoff":
            result.append({"kind": head, "device": int(fields["device"]),
                           "note": int(fields["note"])})
        elif head == "final":
            result.append({"kind": head, "queue": int(fields["queue"]),
                           "song_handle": int(fields["song_handle"])})
        elif head == "reset_done":
            result.append({"kind": head})
        else:
            raise RuntimeError(f"unexpected native record {line!r}")
    return result, p.stdout


def release_event_projection(rows):
    projection=[]
    for row in rows:
        kind=row["kind"]
        if kind in ("free_song_data","free_sample_data"):
            handle=row["handle"]
            if not isinstance(handle,dict):
                raise RuntimeError(f"expected original far-handle callback row, got {row}")
            off,seg=handle["offset"],handle["segment"]
            if seg != 0xA200: raise AssertionError(f"unexpected handle segment {handle}")
            if kind=="free_song_data": sample="song"
            else:
                sample=off-0x300
                if not 0 <= sample < 14: raise AssertionError(f"unexpected sample handle {handle}")
            projection.append({"kind":kind,"sample":sample})
        elif kind in ("flush_begin","flush_end"):
            item={"kind":kind,"count":row["count"]}
            if kind=="flush_begin":
                item["samples"]=[]
                for off,seg in row["samples"]:
                    if seg != 0xA300 or off < 0x100 or (off-0x100)%0x20:
                        raise AssertionError(f"unexpected queued Sample pointer {(off,seg)}")
                    item["samples"].append((off-0x100)//0x20)
            projection.append(item)
        else: raise RuntimeError(f"unexpected cleanup callback {row}")
    return projection


def native_release_projection(rows):
    out=[]
    for r in rows:
        if r["kind"] not in ("free_song_data","free_sample_data","flush_begin","flush_end"): continue
        item={"kind":r["kind"]}
        if r["kind"]=="free_song_data": item["sample"]="song"
        elif r["kind"]=="free_sample_data": item["sample"]=r["handle"]-1000
        elif r["kind"] in ("flush_begin","flush_end"):
            item["count"]=r["count"]
            if r["kind"]=="flush_begin": item["samples"]=r["samples"]
        out.append(item)
    return out


def decode_release_ranges(raw):
    song=bytes.fromhex(raw["song"])
    samples=bytes.fromhex(raw["samples"])
    freelist=bytes.fromhex(raw["freelist"])
    count=int.from_bytes(bytes.fromhex(raw["count"]),"little",signed=True)
    return {"song_data_handle":song[56:60].hex(),"freelist_count":count,
        "freelist_sample_ptrs":[(int.from_bytes(freelist[i*4:i*4+2],"little"),
                                  int.from_bytes(freelist[i*4+2:i*4+4],"little"))
                                 for i in range(min(max(count,0),39))],
        "samples":[{"index":i,"loaded":int.from_bytes(samples[i*32+12:i*32+14],"little",signed=True),
                     "data_handle":samples[i*32:i*32+4].hex()} for i in range(14)]}


def make_callback_log(side, rows):
    def record(name, transform=lambda a: a):
        def handler(machine, args):
            rows[side].append({"kind": name, "args": transform(args)})
        return handler
    return record


def run_release_pair(pair, mode, symbols):
    table = symbols["fd_50F6_0000"]
    freelist = symbols["fd_50F6_0150"]
    count_addr = symbols["g_181C"]
    busy_addr = symbols["g_7574"]
    song_seg, song_off = 0xA100, 0x0100
    song_linear = song_seg * 16 + song_off
    sample_seg = 0xA300
    sample_offsets = [0x0100 + i * 0x20 for i in range(14)]
    sample_addresses = [sample_seg * 16 + x for x in sample_offsets]
    song = bytearray(60)
    for i in range(14): song[28 + i * 2:30 + i * 2] = i.to_bytes(2, "little")
    song[56:60] = (0x0200).to_bytes(2, "little") + (0xA200).to_bytes(2, "little")
    instr = bytearray(14 * 6)
    kinds = [1, 1, 2, 1, 1, 1, 2, 1, 1, 1, 2, 1, 1, 1]
    sample_ids = [0, 1, 2, -1, 4, 5, 6, 7, 8, 9, 10, -1, 12, 13]
    loaded = [2, 1, 1, 0, 0, 2, 1, 2, 1, 0, 1, 0, 2, 1]
    writes = [(song_linear, bytes(song)), (table, bytes(instr)),
              (count_addr, b"\0\0"), (busy_addr, (1 if mode else 0).to_bytes(2, "little"))]
    # Fill actual six-byte large-model Instr records and packed 32-byte Samples.
    ins = bytearray()
    samps = []
    for i in range(14):
        ptr = sample_ids[i]
        off = 0 if ptr < 0 else sample_offsets[ptr]
        seg = 0 if ptr < 0 else sample_seg
        ins += kinds[i].to_bytes(2, "little") + off.to_bytes(2, "little") + seg.to_bytes(2, "little")
        sample = bytearray(32)
        data_handle = bytes(4) if loaded[i] == 0 else (0x0300 + i).to_bytes(2, "little") + (0xA200).to_bytes(2, "little")
        sample[0:4] = data_handle
        sample[12:14] = loaded[i].to_bytes(2, "little", signed=True)
        samps.append(bytes(sample))
    writes[1] = (table, bytes(ins))
    writes += [(sample_addresses[i], samps[i]) for i in range(14)]
    writes += [(freelist, bytes(14 * 4))]

    events = {"dos": [], "candidate": []}
    free_song = make_callback_log("", events)
    def far_handle(args):
        if len(args) != 2: raise RuntimeError(f"free ABI expected far pointer words, got {args}")
        return {"offset": args[0], "segment": args[1]}
    def marker(name):
        def handler(machine,args):
            n=int.from_bytes(machine.read(count_addr,2),"little",signed=True)
            queued=[]
            for ix in range(max(0,min(n,39))):
                raw=machine.read(freelist+ix*4,4)
                queued.append((int.from_bytes(raw[:2],"little"),int.from_bytes(raw[2:],"little")))
            events["candidate" if machine.candidate else "dos"].append({"kind":name,"count":n,"samples":queued})
        return handler
    callbacks = {
        "f_171C_1C0A": behavior.Callback(2, handler=lambda m, a: events["candidate" if m.candidate else "dos"].append({"kind":"free_song_data","handle":far_handle(a)})),
        "db_ReleaseHandle": behavior.Callback(2, handler=lambda m, a: events["candidate" if m.candidate else "dos"].append({"kind":"free_sample_data","handle":far_handle(a)})),
        "f_29F0_000A": behavior.Callback(0, handler=marker("flush_begin")),
        "f_29F0_0012": behavior.Callback(0, handler=marker("flush_end")),
    }
    case = behavior.Case(f"release/{'deferred' if mode else 'immediate'}", args=[song_off, song_seg, 11006],
        writes=writes, callbacks=callbacks,
        observe=[behavior.Range("song", song_linear, 60), behavior.Range("samples", sample_addresses[0], 14*32),
                 behavior.Range("freelist", freelist, 39*4), behavior.Range("count", count_addr, 2)],
        return_kind="void", max_blocks=500000)
    raw = {}
    for side, machine in (("dos", pair.original_machine), ("candidate", pair.candidate_machine)):
        raw[side] = [machine.run(case)]
        if mode:
            raw[side].append(machine.run(behavior.Case(f"release-repeat/{side}", args=[song_off,song_seg,11006],
                callbacks=callbacks, observe=case.observe, return_kind="void", max_blocks=500000), preserve=True))
            # Explicit flush call is from a separate invocation after repeat has built a deferred queue.
            raw[side].append(machine.run(behavior.Case(f"release-flush/{side}", callbacks=callbacks,
                observe=case.observe, return_kind="void", max_blocks=500000), preserve=True,
                function="f_0000_00DE"))
    return raw, events


def run_reset_pair(pair, boundary=False):
    table = behavior.symbol_address("fd_50F6_4A4E")
    rows = bytearray(7 * 6)
    for i in range(6):
        # Include active and inactive c2 slots; record type nonzero controls scan termination.
        rows[i*6:(i+1)*6] = bytes([i+1, i, 1 if i not in (1,4) else 0,
                                    255 if boundary and i == 2 else i, 60+i, 20+i])
    writes = [(table, bytes(rows))]
    events = {"dos": [], "candidate": []}
    callbacks = {"f_295C_02E8": behavior.Callback(2, handler=lambda m,a:
        events["candidate" if m.candidate else "dos"].append({"device":a[0],"note":a[1]}))}
    case = behavior.Case(f"reset/{'u8-boundary' if boundary else 'six-channel-mask'}",
        writes=writes, callbacks=callbacks,
        observe=[behavior.Range("channels", table, len(rows))], return_kind="void")
    raw = {}
    for side,machine in (("dos",pair.original_machine),("candidate",pair.candidate_machine)):
        raw[side]=machine.run(case)
    return raw,events


def main():
    if OUT.exists(): raise SystemExit(f"refusing to overwrite {OUT}")
    if sha(ROOT / "assets/SIMANT.EXE") != DOS_SHA: raise RuntimeError("oracle hash mismatch")
    BUILD.mkdir(parents=True, exist_ok=True)
    cc = Path(shutil.which("gcc") or "").resolve()
    if not cc.is_file(): raise RuntimeError("GCC not found")
    eval_files = runtime_files(); compiler_files = msc_files(); gcc_bins = gcc_files(cc)
    pyexe=Path(sys.executable).resolve()
    py_identity={"path":str(pyexe),"sha256":sha(pyexe),"version":sys.version,
                 "implementation":sys.implementation.name}
    gcc_version_before=subprocess.check_output([str(cc),"--version"],text=True).splitlines()[0]
    pins_before = hashes([*INPUTS,*eval_files,*compiler_files,*gcc_bins])
    native_exe = BUILD / "helper_contract.exe"
    compile_native(cc,native_exe)
    symbols = {"fd_50F6_0000": 0x50F60, "fd_50F6_0150": 0x50F60 + 0x150,
               "g_181C": 0x55B30 + 0x181C, "g_7574": behavior.symbol_address("g_7574")}
    release = behavior.PreparedPair("f_0000_039B",source=RELEASE_SOURCE,
        out=BUILD / "prepared-release",sequence_targets=("f_0000_00DE","f_0000_0149"))
    reset = behavior.PreparedPair("f_295C_0391",source=RESET_SOURCE,out=BUILD / "prepared-reset")
    if not release.strict["claims"]["f_0000_039B"]["exact"] or not reset.strict["claims"]["f_295C_0391"]["exact"]:
        raise RuntimeError("strict whole-module candidate gate failed")
    release_rows=[]
    for deferred,label in ((0,"release-immediate"),(1,"release-deferred-repeat")):
        raw,events=run_release_pair(release,deferred,symbols)
        native,nout=native_events(native_exe,label)
        # Native model encodes each queue/flush transition; the DOS trace records
        # only external leaf calls, so compare callback ordering against modeled
        # projections built from the actual post-state and recorded flush markers.
        dos=events["dos"]; cand=events["candidate"]
        if cand != dos: raise AssertionError({"case":label,"candidate_callbacks":cand,"dos_callbacks":dos})
        actual_projection=release_event_projection(dos)
        modeled_projection=native_release_projection(native)
        if actual_projection != modeled_projection:
            raise AssertionError({"case":label,"dos_callback_projection":release_event_projection(dos),
                                 "native_model_projection":native_release_projection(native)})
        if raw["candidate"][-1]["ranges"] != raw["dos"][-1]["ranges"]:
            raise AssertionError({"case":label,"candidate_final_ranges":raw["candidate"][-1]["ranges"],
                                 "dos_final_ranges":raw["dos"][-1]["ranges"]})
        if not dos or dos[0]["kind"] != "free_song_data": raise AssertionError({"case":label,"release-order":dos})
        # Post-state checks use observed fixture bytes; freelist order and sample
        # state remain visible even though the heap release call is normalized.
        for stage,(d,c) in enumerate(zip(raw["dos"],raw["candidate"])):
            if d["ranges"] != c["ranges"]:
                raise AssertionError({"case":label,"stage":stage,"candidate":c["ranges"],"dos":d["ranges"]})
        expected_selected=[0,1,4,5,7,8,9,12,13]
        if deferred:
            expected_queues=[expected_selected,expected_selected*2,[]]
            observed_queues=[x["freelist_sample_ptrs"] for x in
                             (decode_release_ranges(y["ranges"]) for y in raw["dos"])]
            expected_ptrs=[[(0x100+i*0x20,0xA300) for i in ids] for ids in expected_queues]
            if observed_queues != expected_ptrs:
                raise AssertionError({"case":label,"observed_queues":observed_queues,"expected_queues":expected_ptrs})
        release_rows.append({"case":label,"callbacks":dos,"candidate_callbacks":cand,
            "oracle_stages":[decode_release_ranges(x["ranges"]) for x in raw["dos"]],
            "candidate_stages":[decode_release_ranges(x["ranges"]) for x in raw["candidate"]],
            "native_trace":native,"native_stdout":nout,"status":"PASS_DIAGNOSTIC"})
    reset_rows=[]
    for boundary in (False,True):
        raw,events=run_reset_pair(reset,boundary)
        native,labeltext=native_events(native_exe,"reset-u8-boundary" if boundary else "reset-six")
        dos=events["dos"];cand=events["candidate"]
        if cand != dos: raise AssertionError({"reset":boundary,"candidate":cand,"dos":dos})
        wanted=[e for e in native if e["kind"]=="noteoff"]
        normalized=[{"device":e["device"],"note":e["note"]} for e in dos]
        if normalized != [{"device":e["device"],"note":e["note"]} for e in wanted]:
            raise AssertionError({"reset":boundary,"dos":normalized,"native":wanted})
        reset_rows.append({"boundary_u8":boundary,"note_offs":normalized,
            "candidate_note_offs":[{"device":e["device"],"note":e["note"]} for e in cand],
            "dos_final_channels":raw["dos"]["ranges"],"native_trace":native,"status":"PASS_DIAGNOSTIC"})
    pins_after=hashes([*INPUTS,*eval_files,*compiler_files,*gcc_bins])
    py_identity_after={"path":str(pyexe),"sha256":sha(pyexe),"version":sys.version,
                       "implementation":sys.implementation.name}
    gcc_version_after=subprocess.check_output([str(cc),"--version"],text=True).splitlines()[0]
    if pins_before != pins_after: raise RuntimeError("proof input changed during run")
    if py_identity != py_identity_after or gcc_version_before != gcc_version_after:
        raise RuntimeError("Python/GCC identity changed during run")
    report={"schema":"simant-stop-song-dependencies-diagnostic-v1","status":"PASS_DIAGNOSTIC_NOT_ACCEPTANCE",
        "oracle_sha256":DOS_SHA,"release_candidate":release.identity,"reset_candidate":reset.identity,
        "release_cases":release_rows,"reset_cases":reset_rows,
        "native_source_sha256":sha(NATIVE),"native_executable_sha256":sha(native_exe),
        "gcc_version_before":gcc_version_before,"gcc_version_after":gcc_version_after,
        "python_identity_before":py_identity,"python_identity_after":py_identity_after,
        "inputs_before_sha256":pins_before,"inputs_after_sha256":pins_after,
        "exclusions":{"f_171C_1C0A":"DOS memory manager free action captured as far handle; allocator internals not modeled",
            "db_ReleaseHandle":"database-owned block release captured as far handle; DB heap/coalescing not modeled",
            "f_29F0_000A":"audio pause/hardware boundary represented only as ordered marker",
            "f_29F0_0012":"audio resume/hardware boundary represented only as ordered marker",
            "f_295C_02E8":"per-voice driver dispatch intercepted; channel mutation and physical MIDI writes are below this boundary",
            "device_domain":"c3=255 is a predicate-width diagnostic only, not asserted as a valid hardware device id"}}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8",newline="")
    print(f"release cases={len(release_rows)} reset cases={len(reset_rows)} diagnostics passed")
    print(f"evidence={rel(OUT)}")

if __name__=="__main__": main()
