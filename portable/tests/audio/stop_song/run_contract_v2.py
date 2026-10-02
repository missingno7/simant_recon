"""Bounded DOS/native differential for StopSong orchestration only."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
import behavior  # noqa: E402

EVIDENCE = ROOT / "portable/tests/audio/stop_song/evidence/stop-song-contract-v2.json"
BUILD = ROOT / "build/workers/audio_stop_song_v2"
NATIVE = ROOT / "portable/tests/audio/stop_song/stop_song_contract.c"
SOURCE = ROOT / "src/root/m284A.c"
DOS_ORACLE_SHA = "aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11"

INPUTS = [
    SOURCE, ROOT / "src/root/m0000.c", ROOT / "src/root/m295C.c",
    ROOT / "src/root/m171C.c", ROOT / "src/root/m277E.c",
    ROOT / "src/data/d55B3_00B8.c",
    ROOT / "portable/game/recovered/engine.c",
    ROOT / "portable/audio/intent.c", ROOT / "portable/audio/intent.h",
    ROOT / "portable/platform/sdl3/audio_host.c", ROOT / "portable/platform/sdl3/audio_host.h",
    ROOT / "portable/tests/menus/procmenu_native_probe.c",
    ROOT / "portable/tests/menus/engine_procmenu.c",
    ROOT / "portable/tests/audio/stop_song/run_contract_v2.py", NATIVE,
    ROOT / "portable/tests/audio/stop_song/run_contract.py",
    ROOT / "portable/tests/audio/stop_song/evidence/stop-song-contract-v1.json",
    ROOT / "portable/tests/audio/stop_song/evidence/stop-song-contract-v1-erratum.json",
    ROOT / "layout/functions.json", ROOT / "layout/symbols.json",
    ROOT / "layout/manifest.json", ROOT / "layout/toolchain.json",
    ROOT / "layout/oracle.lock.json", ROOT / "assets/SIMANT.EXE",
    ROOT / "tools/behavior.py", ROOT / "tools/exe.py", ROOT / "tools/functions.py",
    ROOT / "tools/match.py", ROOT / "tools/modctx.py", ROOT / "tools/modules.py",
    ROOT / "tools/compiler.py", ROOT / "tools/omf.py", ROOT / "tools/symbols.py",
    ROOT / "tools/autosearch.py",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def key(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve()).replace("\\", "/")


def hash_files(paths: list[Path]) -> dict[str, str]:
    return {key(p): digest(p) for p in sorted(set(paths), key=lambda x: str(x).casefold())}


def unicorn_runtime_files() -> list[Path]:
    # Pin the Python evaluator modules and native engine DLL actually loaded
    # from the repository's isolated Unicorn installation.
    root = ROOT / "build/behavior/deps/unicorn"
    return [p for p in root.rglob("*") if p.is_file() and
            (p.suffix.lower() == ".py" or p.name.lower() == "unicorn.dll")]


def msc_files() -> list[Path]:
    config = json.loads((ROOT / "layout/toolchain.json").read_text(encoding="utf-8"))
    profile = config["profiles"]["msc600ax"]
    return [(Path(profile["directory"]) / rel).resolve() for rel in sorted(profile["files"])]


def gcc_files(cc: Path) -> list[Path]:
    result = [cc.resolve()]
    for tool in ("cc1", "collect2", "ld", "as"):
        name = subprocess.check_output([str(cc), f"-print-prog-name={tool}"], text=True).strip()
        p = Path(name)
        if not p.is_absolute():
            p = cc.parent / p
        p = p.resolve()
        if not p.is_file():
            raise RuntimeError(f"GCC helper missing: {tool}: {p}")
        result.append(p)
    return result


def signed_word(data: bytes) -> int:
    value = int.from_bytes(data, "little")
    return value - 0x10000 if value & 0x8000 else value


def parse_native(output: str) -> tuple[list[dict], dict]:
    events: list[dict] = []
    final = None
    for line in output.splitlines():
        fields = line.split("|")
        row = {part.split("=", 1)[0]: part.split("=", 1)[1]
               for part in fields[1:] if "=" in part}
        if fields[0] == "release":
            events.append({"kind": "release", "active_at_entry": int(row["active"]),
                           "song_number": int(row["song"]),
                           "song_token": "current-song", "song_data_live_at_entry": int(row["data_before"])})
        elif fields[0] == "reset":
            events.append({"kind": "reset", "active_at_entry": int(row["active"]),
                           "song_data_live_at_entry": int(row["data"])})
        elif fields[0] == "final":
            final = {"active": int(row["active"]), "song_number": int(row["song"]),
                     "song_data_live": int(row["data"]), "calls": int(row["calls"])}
        else:
            raise RuntimeError(f"unrecognized native line: {line}")
    if final is None:
        raise RuntimeError(f"native model omitted final state: {output}")
    return events, final


def compile_native(cc: Path, source: Path, out: Path) -> None:
    result = subprocess.run([str(cc), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
                             str(source), "-o", str(out)], cwd=ROOT,
                            capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"native StopSong fixture compilation failed:\n{result.stdout}{result.stderr}")


def main() -> None:
    if EVIDENCE.exists():
        raise SystemExit(f"refusing to overwrite immutable evidence: {EVIDENCE}")
    if digest(ROOT / "assets/SIMANT.EXE") != DOS_ORACLE_SHA:
        raise RuntimeError("frozen DOS oracle SHA-256 mismatch")
    BUILD.mkdir(parents=True, exist_ok=True)
    cc_name = shutil.which("gcc")
    if cc_name is None:
        raise RuntimeError("GCC is required for the native contract fixture")
    cc = Path(cc_name).resolve()
    gcc_bins = gcc_files(cc)
    msc_bins = msc_files()
    python_bin = Path(sys.executable).resolve()
    evaluator_files = unicorn_runtime_files()
    source_before = hash_files([*INPUTS, *evaluator_files])
    evaluator_before = hash_files(evaluator_files)
    gcc_before = hash_files(gcc_bins)
    msc_before = hash_files(msc_bins)
    python_before = {"executable": str(python_bin), "sha256": digest(python_bin),
                     "version": sys.version, "implementation": sys.implementation.name}
    gcc_version_before = subprocess.check_output([str(cc), "--version"], text=True).splitlines()[0]
    gcc_target_before = subprocess.check_output([str(cc), "-dumpmachine"], text=True).strip()

    pair = behavior.PreparedPair("StopSong", source=SOURCE,
                                 out="build/workers/audio_stop_song_v2/prepared")
    target_exact = pair.strict["claims"].get("StopSong", {}).get("exact") is True
    if not target_exact:
        raise RuntimeError("StopSong canonical historical candidate failed its existing exact module gate")

    active_addr = behavior.symbol_address("g_756E")
    number_addr = behavior.symbol_address("g_7578")
    current_song_global = behavior.symbol_address("fd_55B3_00B4")
    song_seg, song_off = 0xA100, 0x0100
    song_linear = song_seg * 16 + song_off
    song_data_off, song_data_seg = 0x0200, 0xA200
    song_bytes = bytearray(60)
    song_bytes[56:60] = song_data_off.to_bytes(2, "little") + song_data_seg.to_bytes(2, "little")
    ranges = [
        behavior.Range("active", active_addr, 2),
        behavior.Range("song_number", number_addr, 2),
        behavior.Range("current_song_pointer", current_song_global, 4),
        behavior.Range("song_data_handle", song_linear + 56, 4),
    ]
    # IDs are source-backed values passed to myBeginSong in resident/UI call
    # sites. The cleanup number itself is ignored by f_0000_039B; these cases
    # verify the signed-word ABI without inventing 0x8000+ song IDs.
    scenarios = [(0, 0x2AFE, "inactive"), (1, 0x2711, "playing"),
                 (2, 0x4E27, "finished")]
    rows = []
    native_exe = BUILD / "stop_song_contract.exe"
    compile_native(cc, NATIVE, native_exe)

    for active, number, label in scenarios:
        callbacks_by_side: dict[str, list[dict]] = {"dos": [], "candidate": []}

        def on_release(machine, args):
            side = "candidate" if machine.candidate else "dos"
            if len(args) != 3:
                raise RuntimeError(f"unexpected release ABI argument words: {args}")
            off, seg, received_number = args
            if (off, seg) != (song_off, song_seg):
                raise RuntimeError(f"StopSong passed wrong Song far pointer: {(off, seg)}")
            if signed_word(received_number.to_bytes(2, "little")) != number:
                raise RuntimeError(f"StopSong passed wrong signed song id: {received_number:#x}")
            active_now = signed_word(machine.read(active_addr, 2))
            data_now = int.from_bytes(machine.read(song_linear + 56, 4), "little")
            callbacks_by_side[side].append({"kind": "release", "active_at_entry": active_now,
                "song_number": number, "song_token": "current-song",
                "song_data_live_at_entry": int(data_now != 0),
                "raw_song_far_pointer": {"segment": seg, "offset": off},
                "raw_number_word": received_number})
            # Controlled replacement of the f_0000_039B resource-owner edge:
            # closing the owned stream clears the Song data handle before reset.
            machine.write(song_linear + 56, b"\0\0\0\0")

        def on_reset(machine, args):
            if args:
                raise RuntimeError(f"unexpected reset helper arguments: {args}")
            side = "candidate" if machine.candidate else "dos"
            active_now = signed_word(machine.read(active_addr, 2))
            data_now = int.from_bytes(machine.read(song_linear + 56, 4), "little")
            callbacks_by_side[side].append({"kind": "reset", "active_at_entry": active_now,
                "song_data_live_at_entry": int(data_now != 0)})

        cb = {"f_0000_039B": behavior.Callback(3, handler=on_release),
              "f_295C_0391": behavior.Callback(0, handler=on_reset)}
        writes = [
            (active_addr, (active & 0xFFFF).to_bytes(2, "little")),
            (number_addr, (number & 0xFFFF).to_bytes(2, "little")),
            (current_song_global, song_off.to_bytes(2, "little") + song_seg.to_bytes(2, "little")),
            (song_linear, bytes(song_bytes)),
        ]
        first = behavior.Case(f"StopSong/{label}/first", writes=writes,
            callbacks=cb, observe=ranges, return_kind="void")
        repeat = behavior.Case(f"StopSong/{label}/repeat", callbacks=cb,
            observe=ranges, return_kind="void")

        raw_by_side = {}
        for side, machine in (("dos", pair.original_machine),
                              ("candidate", pair.candidate_machine)):
            raw_by_side[side] = [machine.run(first), machine.run(repeat, preserve=True)]

        native = subprocess.run([str(native_exe), str(active), str(number)], cwd=ROOT,
                                capture_output=True, text=True, check=True)
        native_events, native_final = parse_native(native.stdout)
        dos_events = [{k: v for k, v in row.items() if k != "raw_song_far_pointer" and k != "raw_number_word"}
                      for row in callbacks_by_side["dos"]]
        candidate_events = [{k: v for k, v in row.items() if k != "raw_song_far_pointer" and k != "raw_number_word"}
                            for row in callbacks_by_side["candidate"]]
        dos_final = {
            "active": signed_word(bytes.fromhex(raw_by_side["dos"][-1]["ranges"]["active"])),
            "song_number": signed_word(bytes.fromhex(raw_by_side["dos"][-1]["ranges"]["song_number"])),
            "song_data_live": int(any(bytes.fromhex(raw_by_side["dos"][-1]["ranges"]["song_data_handle"]))),
            "calls": 2,
        }
        if dos_events != native_events or dos_final != native_final:
            raise AssertionError({"scenario": label, "dos_events": dos_events,
                                  "native_events": native_events, "dos_final": dos_final,
                                  "native_final": native_final})
        if candidate_events != dos_events:
            raise AssertionError({"scenario": label, "candidate_events": candidate_events,
                                  "dos_events": dos_events})
        rows.append({"scenario": label, "initial_active": active, "song_number": number,
            "calls": 2, "status": "MATCH", "dos_callbacks": dos_events,
            "candidate_callbacks": candidate_events, "native_callbacks": native_events,
            "dos_final": dos_final, "native_final": native_final,
            "dos_raw_first": raw_by_side["dos"][0],
            "dos_raw_repeat": raw_by_side["dos"][1],
            "candidate_raw_first": raw_by_side["candidate"][0],
            "candidate_raw_repeat": raw_by_side["candidate"][1]})

    source_after = hash_files([*INPUTS, *evaluator_files])
    evaluator_after = hash_files(evaluator_files)
    gcc_after = hash_files(gcc_bins)
    msc_after = hash_files(msc_bins)
    python_after = {"executable": str(python_bin), "sha256": digest(python_bin),
                    "version": sys.version, "implementation": sys.implementation.name}
    gcc_version_after = subprocess.check_output([str(cc), "--version"], text=True).splitlines()[0]
    gcc_target_after = subprocess.check_output([str(cc), "-dumpmachine"], text=True).strip()
    if source_before != source_after or gcc_before != gcc_after or msc_before != msc_after or \
       python_before != python_after or gcc_version_before != gcc_version_after or \
       gcc_target_before != gcc_target_after or evaluator_before != evaluator_after:
        raise RuntimeError("one or more StopSong proof inputs changed during the run")

    report = {
        "schema": "simant-stop-song-contract-v1",
        "status": "PASS_DIAGNOSTIC_NOT_PRODUCTION",
        "function": "root:284A:010A StopSong",
        "oracle_sha256": DOS_ORACLE_SHA,
        "contract": {
            "guard": "any nonzero g_756E, including source states 1=playing and 2=finished, enters stop path",
            "transition_order": ["g_756E := 0", "release current Song/resource ownership",
                                 "reset active MIDI/song synth channels"],
            "inactive": "g_756E == 0 causes no release or reset callback",
            "number": "g_7578 is passed as a signed 16-bit number to release; source helper f_0000_039B does not read it",
            "ownership_boundary": "f_0000_039B owns clearing Song.data and returning loaded sample references; this suite abstracts that edge by clearing the test handle at callback entry",
            "reset_boundary": "f_295C_0391 owns scanning active MIDI-channel descriptors and calling f_295C_02E8; this suite tests StopSong order, not device-register sequencing",
        },
        "domains": {"music_states": [0, 1, 2], "source_backed_song_numbers": [10001, 11006, 20007],
                    "note": "No signed high-bit song IDs are in the inspected myBeginSong call-site domain; 0x8000/0xFFFF are not treated as valid songs."},
        "scenario_count": len(rows), "invocations": sum(r["calls"] for r in rows),
        "exact_historical_candidate": target_exact,
        "pair_identity": pair.identity,
        "rows": rows,
        "inputs_before_sha256": source_before, "inputs_after_sha256": source_after,
        "gcc_binaries_before_sha256": gcc_before, "gcc_binaries_after_sha256": gcc_after,
        "gcc_version_before": gcc_version_before, "gcc_version_after": gcc_version_after,
        "gcc_target_before": gcc_target_before, "gcc_target_after": gcc_target_after,
        "msc_toolchain_before_sha256": msc_before, "msc_toolchain_after_sha256": msc_after,
        "python_identity_before": python_before, "python_identity_after": python_after,
        "native_source_sha256": digest(NATIVE), "native_executable_sha256": digest(native_exe),
        "unicorn_version": behavior.uc.__version__,
        "unicorn_runtime_sha256_before": evaluator_before,
        "unicorn_runtime_sha256_after": evaluator_after,
        "limitations": [
            "DOS resource and physical ISA/MIDI device internals are normalized as two reviewed helper boundaries.",
            "This suite does not establish the internal f_0000_039B allocator/freelist contract or f_295C_0391 MIDI register sequence.",
            "It is a focused StopSong orchestration contract, not a BEHAVIOR_EXACT registration or a full lifecycle proof.",
        ],
    }
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="")
    print(f"StopSong contract PASS: {len(rows)} scenarios, {report['invocations']} invocations; diagnostic only")
    print(f"evidence={key(EVIDENCE)}")


if __name__ == "__main__":
    main()
