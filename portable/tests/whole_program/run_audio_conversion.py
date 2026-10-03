"""Exercise the bounded audio-module conversions and archive source pins.

The native probe providers below record host intent; they do not implement a
sound card, BIOS service, or ISA device. The DOS cases are separate oracle
controls for the actual original inline-assembly helpers.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / "build/workers/audio_conversion_v8"
REPORT = ROOT / "portable/tests/whole_program/evidence/audio-conversion-v8.json"
GENERATED = WORK / "m29F0_converted.c"
EXE = WORK / "audio_conversion_probe.exe"
DEVICE_EXE = WORK / "audio_device_conversion_probe.exe"
RUNNER = Path(__file__).resolve()
CONVERTER = ROOT / "portable/whole_program/conversions/audio.py"
HEADER = ROOT / "portable/whole_program/platform/audio.h"
SOURCE_C = ROOT / "portable/whole_program/platform/audio.c"
PROBE = ROOT / "portable/tests/whole_program/audio_conversion_probe.c"
DEVICE_PROBE = ROOT / "portable/tests/whole_program/audio_device_conversion_probe.c"
SOURCES = [ROOT / f"src/root/{stem}.c" for stem in ("m29F0", "m284A", "m277E", "m29D6", "m293A")]
DEPENDENCY_SOURCES = [ROOT / p for p in (
    "src/root/m0000.c", "src/root/m171C.c", "src/data/d55B3_00B8.c")]
GCC = Path("C:/msys64/mingw64/bin/gcc.exe")


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def extract_functions(source: str, names: list[str]) -> str:
    bodies = []
    for name in names:
        match = re.search(r"\b" + re.escape(name) + r"\s*\([^;{}]*\)\s*\{", source)
        if match is None:
            raise RuntimeError(f"converted module is missing function body {name}")
        start = source.find("{", match.start())
        depth = 0
        end = None
        for offset in range(start, len(source)):
            if source[offset] == "{":
                depth += 1
            elif source[offset] == "}":
                depth -= 1
                if depth == 0:
                    end = offset + 1
                    break
        if end is None:
            raise RuntimeError(f"unterminated converted function {name}")
        line_start = source.rfind("\n", 0, match.start()) + 1
        bodies.append(source[line_start:end])
    return '#include "portable/whole_program/platform/audio.h"\n\n' + "\n\n".join(bodies) + "\n"


def dos_inline_asm_controls() -> list[dict]:
    sys.path.insert(0, str(ROOT / "tools"))
    import behavior

    source = ROOT / "src/root/m29F0.c"
    targets = [
        ("f_29F0_000A", behavior.Case("cli-a", return_kind="void",
                                       registers={"eflags": 0x202}), []),
        ("f_29F0_0012", behavior.Case("sti-a", return_kind="void",
                                       registers={"eflags": 0x2}), []),
        ("f_29F0_001A", behavior.Case("cli-b", return_kind="void",
                                       registers={"eflags": 0x202}), []),
        ("f_29F0_0022", behavior.Case("sti-b", return_kind="void",
                                       registers={"eflags": 0x2}), []),
        ("f_29F0_002A", behavior.Case("out-dx-al", args=[0x1338, 0x01ab],
                                       return_kind="void"), [("out", 0x1338, 1, 0xab)]),
        ("f_29F0_0038", behavior.Case("in-dx-al", args=[0x0338],
                                       return_kind="u8", io_reads={0x0338: 0xa5}),
         [("in", 0x0338, 1, 0xa5)]),
    ]
    result = []
    for index, (name, case, expected_io) in enumerate(targets):
        pair = behavior.PreparedPair(name, source=source,
                                     out=WORK / "dos-oracle" / f"{index}-{name}")
        comparison = pair.compare(case)
        if not comparison.equal:
            raise RuntimeError(f"original DOS/compiler control differs for {name}: {comparison.diff}")
        if comparison.original["io"] != expected_io or comparison.candidate["io"] != expected_io:
            raise RuntimeError(f"unexpected original port effect for {name}: {comparison.original['io']}")
        result.append({
            "function": name,
            "case": case.label,
            "original_vs_compiler_candidate_equal": comparison.equal,
            "io": comparison.original["io"],
            "return": comparison.original["return"],
            "preserved_registers": comparison.original["preserved_registers"],
            "prepared_pair": pair.identity,
        })
    return result


def dos_device_controls() -> list[dict]:
    sys.path.insert(0, str(ROOT / "tools"))
    import behavior

    expected_fm = [(11146, 159), (5549, 183), (3558, 247), (100, 112), (869, 127)]
    expected_psg = [(141, 221, 159), (174, 238, 183), (238, 14, 247),
                    (100, 0, 112), (107, 3, 127)]
    vectors = [(0, 0, 0), (12, 64, 1), (60, 64, 3), (127, 127, 7), (84, 1, 15)]
    result: list[dict] = []
    cases = []
    port_address = behavior.symbol_address("fd_50F6_4B14")
    for target, source_path in (("f_29D6_00D9", "src/root/m29D6.c"),
                                ("f_29D6_000A", "src/root/m29D6.c")):
        pair = behavior.PreparedPair(target, source=ROOT / source_path,
                                     out=WORK / "dos-oracle" / target)
        for index, (note, volume, channel) in enumerate(vectors):
            writes = [(port_address, (0x0220).to_bytes(2, "little", signed=True))] if target.endswith("00D9") else []
            case = behavior.Case(f"{target}-vector-{index}",
                                 args=[0, note, volume, channel], writes=writes,
                                 return_kind="void")
            comparison = pair.compare(case)
            if not comparison.equal:
                raise RuntimeError(f"DOS/compiler control differs for {case.label}: {comparison.diff}")
            raw_io = comparison.original["io"]
            if target.endswith("00D9"):
                wanted = [("out", 0x0220, 2, expected_fm[index][0]),
                          ("out", 0x0220, 1, expected_fm[index][1])]
            else:
                wanted = [("out", 0x0205, 1, byte) for byte in expected_psg[index]]
            if raw_io != wanted:
                raise RuntimeError(f"unexpected original DOS effects for {case.label}: {raw_io}")
            cases.append({"function": target, "label": case.label,
                          "original_vs_compiler_equal": comparison.equal,
                          "io": raw_io})
        result.append({"function": target, "identity": pair.identity})

    speaker_cases = [
        ("f_277E_0958", behavior.Case("speaker-gate", return_kind="void",
                                      io_reads={0x0061: 0xa5}),
         [("in", 0x0061, 1, 0xa5), ("out", 0x0061, 1, 0xa4)]),
        ("f_277E_0965", behavior.Case("audio-init", return_kind="void"),
         [("out", 0x000a, 1, 0x05), ("out", 0x0220, 1, 0x0f),
          ("out", 0x0221, 1, 0x60)]),
    ]
    for index, (target, case, wanted) in enumerate(speaker_cases):
        pair = behavior.PreparedPair(target, source=ROOT / "src/root/m277E.c",
                                     out=WORK / "dos-oracle" / f"{index}-{target}")
        comparison = pair.compare(case)
        if not comparison.equal or comparison.original["io"] != wanted:
            raise RuntimeError(f"DOS/compiler control differs for {target}: {comparison.diff or comparison.original['io']}")
        cases.append({"function": target, "label": case.label,
                      "original_vs_compiler_equal": comparison.equal,
                      "io": comparison.original["io"], "identity": pair.identity})

    if len(cases) != 12:
        raise RuntimeError(f"expected 12 DOS device controls, got {len(cases)}")
    return [{"case_count": len(cases), "cases": cases,
             "midi_and_bios_limit": "No DOS BIOS/ISA outcome is fabricated; only the port-only helpers are oracle-exercised."}]


def main() -> None:
    if REPORT.exists() or WORK.exists():
        raise FileExistsError("audio conversion outputs are write-once; choose a new evidence version")
    WORK.mkdir(parents=True)
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "portable/tools"))
    from portable.whole_program.conversions.audio import adapt
    import whole_program

    input_hashes = {p.relative_to(ROOT).as_posix(): sha(p) for p in
                    [*SOURCES, *DEPENDENCY_SOURCES, CONVERTER, HEADER, SOURCE_C, PROBE,
                     DEVICE_PROBE, RUNNER,
                     ROOT / "portable/tools/whole_program.py"]}
    converted_sources = {}
    conversion_rows = {}
    for path in SOURCES:
        rel = path.relative_to(ROOT).as_posix()
        adapted, ledger = adapt(rel, path.read_text(encoding="utf-8"))
        native, word_ledger = whole_program.convert_words(adapted)
        converted_sources[path.stem] = native
        conversion_rows[rel] = {
            "conversion": ledger,
            "word_width_lowering": word_ledger,
            "native_source_sha256": sha_bytes(native.encode("utf-8")),
        }

    with GENERATED.open("x", encoding="utf-8", newline="") as stream:
        stream.write(converted_sources["m29F0"])
    compiler_version = subprocess.run([str(GCC), "--version"], capture_output=True,
                                       text=True, check=True).stdout.splitlines()[0]
    compile_command = [str(GCC), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
                       "-I", ".", "-o", str(EXE), str(GENERATED), str(SOURCE_C), str(PROBE)]
    built = subprocess.run(compile_command, cwd=ROOT, capture_output=True, text=True)
    if built.returncode:
        raise RuntimeError(f"audio converted probe compile failed:\n{built.stdout}\n{built.stderr}")
    ran = subprocess.run([str(EXE)], cwd=ROOT, capture_output=True, text=True)
    if ran.returncode:
        raise RuntimeError(f"audio converted probe failed ({ran.returncode}):\n{ran.stdout}\n{ran.stderr}")

    # Every converted TU is syntax-compiled. The more complex device modules
    # are also compiled with per-module suppressions only for dead/originally
    # unused values or original unsigned comparisons; no hardware behavior is
    # supplied by the compiler fixture.
    module_compile_receipts = {}
    module_objects = {}
    compile_options = {
        "m29F0": [],
        "m284A": ["-Wno-unused-parameter"],
        "m277E": ["-Wno-unused-parameter", "-Wno-unused-variable", "-Wno-unused-but-set-variable"],
        "m29D6": ["-Wno-unused-parameter"],
        "m293A": ["-Wno-type-limits"],
    }
    for stem in ("m284A", "m277E", "m29D6", "m293A"):
        module_source = WORK / f"{stem}_converted.c"
        module_object = WORK / f"{stem}_converted.o"
        with module_source.open("x", encoding="utf-8", newline="") as stream:
            stream.write(converted_sources[stem])
        command = [str(GCC), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
                   *compile_options[stem], "-ffunction-sections", "-fdata-sections",
                   "-I", ".", "-c", str(module_source), "-o", str(module_object)]
        compiled = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if compiled.returncode:
            raise RuntimeError(f"converted {stem} syntax compile failed:\n{compiled.stdout}\n{compiled.stderr}")
        module_compile_receipts[stem] = {"command": command, "object_sha256": sha(module_object)}
        module_objects[stem] = module_object

    device_extract = WORK / "audio_boundary_functions.c"
    with device_extract.open("x", encoding="utf-8", newline="") as stream:
        stream.write(extract_functions(converted_sources["m277E"],
                                       ["f_277E_0958", "f_277E_0965"]))
        stream.write(extract_functions(converted_sources["m293A"],
                                       ["f_293A_002D", "f_293A_0059"]).split("\n", 2)[2])
    device_compile = [str(GCC), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
                      "-Wno-unused-parameter", "-I", ".", "-o", str(DEVICE_EXE), str(DEVICE_PROBE),
                      str(device_extract), str(module_objects["m29D6"])]
    device_built = subprocess.run(device_compile, cwd=ROOT, capture_output=True, text=True)
    if device_built.returncode:
        raise RuntimeError(f"audio device probe compile/link failed:\n{device_built.stdout}\n{device_built.stderr}")
    device_ran = subprocess.run([str(DEVICE_EXE)], cwd=ROOT, capture_output=True, text=True)
    if device_ran.returncode:
        raise RuntimeError(f"audio device probe failed ({device_ran.returncode}):\n{device_ran.stdout}\n{device_ran.stderr}")

    # Pin original DOS/compiler controls. The IN value is an explicit model
    # input; it is not an emulation claim about a particular sound card.
    dos_controls = dos_inline_asm_controls()
    dos_device_receipt = dos_device_controls()

    # Assert exact changes and deliberate pending work for the modules not
    # mechanically rewritten in this bounded pass.
    if "_asm" in converted_sources["m29F0"]:
        raise RuntimeError("m29F0 converted body still contains inline assembly")
    if "SONGP(" in converted_sources["m284A"] or "_based" in converted_sources["m284A"]:
        raise RuntimeError("m284A conversion retained a segment-based song access")
    if "void *b;" not in converted_sources["m277E"]:
        raise RuntimeError("m277E native Voice pointer representation missing")
    required_dependency_hashes = {
        "src/root/m0000.c": "d9ccffbb69c4fdcae55eef918bf420cff81ead6849f67298271c2844e04199f9",
        "src/root/m171C.c": "31bd9caa243220db2bd1ba940ac8fae7f5d189b2ec95f1662918e9ca2160b10e",
        "src/data/d55B3_00B8.c": "d04646a28691ff05ad93a50c5e7142405ab64932f875f2d2a4d10d04a4566f3d",
    }
    for rel, expected_sha in required_dependency_hashes.items():
        if input_hashes[rel] != expected_sha:
            raise RuntimeError(f"audio semantic dependency changed: {rel}")
    for stem in ("m277E", "m29D6", "m293A"):
        if "_asm" in converted_sources[stem]:
            raise RuntimeError(f"{stem} converted source retains inline assembly")

    final_hashes = {p.relative_to(ROOT).as_posix(): sha(p) for p in
                    [*SOURCES, *DEPENDENCY_SOURCES, CONVERTER, HEADER, SOURCE_C, PROBE,
                     DEVICE_PROBE, RUNNER,
                     ROOT / "portable/tools/whole_program.py"]}
    if final_hashes != input_hashes:
        raise RuntimeError("source/converter/test input changed during audio conversion test")
    report = {
        "schema": "whole-program-audio-conversion-test-v1",
        "status": "PASS",
        "input_sha256": input_hashes,
        "conversions": conversion_rows,
        "native_probe": {
            "compiler": {"path": str(GCC), "sha256": sha(GCC), "version": compiler_version,
                         "flags": ["-std=c11", "-O2", "-Wall", "-Wextra", "-Werror"]},
            "compile_command": compile_command,
            "executable_sha256": sha(EXE),
            "stdout": ran.stdout.strip(),
            "converted_module_compile_receipts": module_compile_receipts,
            "boundary_functions_source_sha256": sha(device_extract),
            "device_probe_compile_command": device_compile,
            "device_probe_executable_sha256": sha(DEVICE_EXE),
            "device_probe_stdout": device_ran.stdout.strip(),
            "limits": [
                "Host port and interrupt callbacks are recording test providers only; production implementations remain unprovided.",
                "Song bounds-fault provider is a longjmp recorder in this test; no DOS out-of-bounds behavior is claimed.",
                "m284A is syntax-compiled but not linked or run because its timer, MIDI, allocator, and host-service peers are not provided here.",
                "m277E Voice.b follows the exact pinned DATA table pointer member and copy-only source use; BIOS predicates are exercised with controlled service return values, not represented as physical-host oracle results.",
                "m293A device/BIOS predicates remain unresolved until host BIOS and far-memory services exist; test provider results only demonstrate that source branches consume their results.",
                "No hardware I/O, BIOS implementation, device detection result, or delay/ISR behavior is simulated by production code.",
            ],
        },
        "original_dos_controls": {
            "case_count": len(dos_controls),
            "cases": dos_controls,
            "limitations": [
                "The original oracle is the hash-locked DOS executable; compiler candidates use the original C module with inline assembly and all six controls match.",
                "The IN service uses a case-provided byte at port 0338 as an explicit deterministic host boundary input.",
                "These controls validate original instruction/compiler semantics, not a real audio device or the converted host provider implementation.",
            ],
        },
        "original_dos_device_controls": dos_device_receipt,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open("x", encoding="utf-8", newline="") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"status": report["status"], "native_probe": ran.stdout.strip(),
                      "device_probe": device_ran.stdout.strip(),
                      "dos_control_cases": len(dos_controls) + dos_device_receipt[0]["case_count"],
                      "report": REPORT.relative_to(ROOT).as_posix()}, indent=2))


if __name__ == "__main__":
    main()
