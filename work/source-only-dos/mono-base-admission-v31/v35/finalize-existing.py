from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BUILDER = OUT / "relocation-probe.py"
sys.path.insert(0, str(ROOT / "tools"))

spec = importlib.util.spec_from_file_location("offset16_probe_v35", BUILDER)
probe = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(probe)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(path: Path) -> dict:
    path = path.resolve()
    try:
        label = path.relative_to(ROOT).as_posix()
    except ValueError:
        label = str(path)
    return {"path": label, "sha256": sha(path), "size_bytes": path.stat().st_size}


def need(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("v35 existing-artifact finalizer failed closed: " + message)


def omf(label: str):
    path = OUT / "objects" / f"{label}.OBJ"
    need(path.is_file(), f"missing prebuilt OMF {path}")
    return probe.OmfReader().read(path.read_bytes(), label)


def no_link_diagnostics(path: Path) -> bool:
    return re.search(r"\b(?:warning|undefined|fatal|unresolved|error)\b",
                     path.read_text(encoding="latin1", errors="replace"), re.I) is None


def diagnostic_worker(version: str, failure: dict) -> dict:
    worker = ROOT / "build" / "workers" / f"dos_mono_8ed8_owner_{version}"
    expected = {"DGROUP": 0x35, "LITERAL": 0xA5, "DATA": 0xC7, "TARGET": 0xD3}
    cases = []
    runtime_root = worker / "runtime"
    for linker_dir in sorted(p for p in runtime_root.iterdir() if p.is_dir()):
        for case_dir in sorted(p for p in linker_dir.iterdir() if p.is_dir()):
            obs_path = case_dir / "OBS.BIN"
            if not obs_path.exists():
                continue
            obs = obs_path.read_bytes()
            map_path = case_dir / "LOCAL.MAP"
            map_text = map_path.read_text(encoding="latin1", errors="replace") if map_path.exists() else ""
            map_excerpt = [line.strip() for line in map_text.splitlines()
                           if any(name in line for name in
                                  ("_DATA", "FrameMarker", "LiteralMarker", "_g_8ED8", "_g_8EC0"))]
            case_kind = case_dir.name.upper()
            expected_byte = expected[case_kind]
            cases.append({
                "linker": linker_dir.name,
                "variant": case_kind,
                "expected_byte": f"{expected_byte:02X}",
                "observed_hex": obs.hex(" "),
                "run_log": (case_dir / "RUN.LOG").read_text(encoding="latin1").strip()
                           if (case_dir / "RUN.LOG").exists() else "MISSING",
                "link_diagnostics_clean": no_link_diagnostics(case_dir / "LINK.LOG")
                    if (case_dir / "LINK.LOG").exists() else False,
                "map_sha256": sha(map_path) if map_path.exists() else None,
                "map_excerpt": map_excerpt,
                "runtime_result": "PASS" if obs == bytes([expected_byte]) else "FAIL",
                "raw_artifacts": [pin(p) for p in sorted(case_dir.iterdir()) if p.is_file()],
            })
    raw = []
    for subdir in ("sources", "objects", "runtime"):
        base = worker / subdir
        if base.exists():
            raw.extend(pin(p) for p in sorted(base.rglob("*")) if p.is_file())
    script = worker / "relocation-probe.py"
    if script.exists():
        raw.append(pin(script))
    return {
        "version": version,
        "status": "FAILED_DIAGNOSTIC_ONLY",
        "declared_failure": failure,
        "cases_with_raw_observations": cases,
        "cases_not_observed": [
            {"linker": link, "variant": kind, "expected_byte": f"{expected[kind]:02X}",
             "status": "NOT_RUN_OR_NO_OBSERVED_OUTPUT"}
            for link in ("rtlink400", "rtlink610") for kind in ("DGROUP", "LITERAL", "DATA", "TARGET")
            if not any(row["linker"] == link and row["variant"] == kind for row in cases)
        ],
        "raw_artifact_pins": raw,
    }


def main() -> None:
    src = OUT / "sources"
    obj = OUT / "objects"
    base = omf("BASE_S01_328E")
    pos = omf("POS_DGROUP_328E")
    frame_neg = omf("NEG_DATA_328E")
    target_neg = omf("NEG_TARGET_328E")
    unqualified = omf("NEG_UNQUAL_328E")
    whole = probe.compare_whole_module(base, pos, "_g_8ED8", "group", "DGROUP")
    wrong_frame = probe.compare_control(base, frame_neg, "_g_8ED8", "segment", "_DATA")
    wrong_target = probe.compare_control(base, target_neg, "_g_8EC0", "group", "DGROUP")
    unqualified_control = probe.compare_control(base, unqualified, "_g_8ED8", "segment", "_DATA")

    owner = omf("RUNTIME_OWNER")
    data_defs = [row for row in owner.segment_defs if row["name"] == "_DATA"]
    need(len(data_defs) == 1 and data_defs[0]["alignment"] == "paragraph",
         f"fixture owner _DATA SEGDEF is not paragraph aligned: {data_defs}")

    runtime_cases = []
    fixture_controls = {}
    expected = {"DGROUP": 0x35, "LITERAL": 0xA5, "DATA": 0xC7, "TARGET": 0xD3}
    selected_fixups = {
        "DGROUP": ("external", "_g_8ED8", "group", "DGROUP"),
        "DATA": ("external", "_g_8ED8", "segment", "_DATA"),
        "TARGET": ("external", "_g_8EC0", "group", "DGROUP"),
    }
    for kind in ("DGROUP", "LITERAL", "DATA", "TARGET"):
        checker = omf("CHECK_" + kind)
        saved_source = (src / f"CHECK_{kind}.ASM").read_text(encoding="latin1").replace("\r\n", "\n")
        expected_source = probe.fixture_checker(kind).replace("\r\n", "\n")
        need(saved_source == expected_source, f"saved {kind} checker source differs from its fixture declaration")
        lst = (src / f"CHECK_{kind}.LST").read_text(encoding="latin1")
        add_rows = [line for line in lst.splitlines() if "add bx," in line.lower()]
        need(len(add_rows) == 1, f"{kind} listing has no unique ADD BX site")
        add_offset = int(add_rows[0].split()[0], 16)
        expr_fixups = [row for row in checker.linker_fixups
                       if row["segment"] == "CHECK_TEXT" and row["offset"] == add_offset + 2]
        guard_fixups = [row for row in checker.linker_fixups
                        if row["segment"] == "CHECK_TEXT" and row["loc"] == "base16"
                        and row["target_kind"] == "group" and row["target"] == "DGROUP"
                        and row["frame_kind"] == "group" and row["frame"] == "DGROUP"]
        need(len(guard_fixups) == 1,
             f"{kind} checker lacks exactly one BASE16 DGROUP selector guard fixup: {guard_fixups}")
        if kind == "LITERAL":
            need(not expr_fixups, f"literal checker unexpectedly has expression relocations: {expr_fixups}")
            relocation = None
        else:
            target = selected_fixups[kind]
            matches = [row for row in expr_fixups if row["target_kind"] == target[0]
                       and row["target"] == target[1] and row["frame_kind"] == target[2]
                       and row["frame"] == target[3] and row["loc"] == "offset16"
                       and row["width"] == 2]
            need(len(matches) == 1, f"{kind} expression relocation differs from {target}: {expr_fixups}")
            relocation = matches[0]
        fixture_controls[kind] = {
            "expression": probe.fixture_checker(kind).split("add bx, ", 1)[1].split("\n", 1)[0],
            "add_instruction_offset": add_offset,
            "immediate_field_offset": add_offset + 2,
            "expression_fixups": expr_fixups,
            "expected_expression_fixup": relocation,
            "ss_dgroup_guard": {
                "guard": "SEG DGROUP == SS and SEG DGROUP == DS before SS:[BX]",
                "omf_base16_fixup": guard_fixups[0],
                "wrong_selector_result": "EE",
                "valid_selector_guarded": True,
            },
        }

    for linker in ("rtlink400", "rtlink610"):
        for kind in ("DGROUP", "LITERAL", "DATA", "TARGET"):
            directory = OUT / "runtime" / linker / kind
            map_path = directory / "LOCAL.MAP"
            obs_path = directory / "OBS.BIN"
            link_path = directory / "LINK.LOG"
            run_path = directory / "RUN.LOG"
            need(all(p.is_file() for p in (map_path, obs_path, link_path, run_path)),
                 f"{linker}/{kind} existing run is missing a required retained artifact")
            mapping = probe.parse_map(map_path)
            need(mapping["passed"], f"{linker}/{kind} Name/Value map tables or alignment mismatch: {mapping}")
            observed = obs_path.read_bytes()
            need(observed == bytes([expected[kind]]),
                 f"{linker}/{kind} retained observation {observed.hex(' ')} != {expected[kind]:02X}")
            need(run_path.read_text(encoding="latin1").strip() == "EXECUTED",
                 f"{linker}/{kind} retained run log does not say EXECUTED")
            need(no_link_diagnostics(link_path), f"{linker}/{kind} has warning/error diagnostics")
            if (directory / "LOCAL.EXE").exists():
                need((directory / "DOSBOX.LOG").is_file() and (directory / "dosbox.conf").is_file(),
                     f"{linker}/{kind} is missing raw runner evidence")
            runtime_cases.append({
                "linker": linker,
                "linker_status": "experimental",
                "variant": kind,
                "expected_byte": f"{expected[kind]:02X}",
                "observed_hex": observed.hex(" "),
                "map": mapping,
                "link_diagnostics_clean": True,
                "ss_dgroup_guard": fixture_controls[kind]["ss_dgroup_guard"],
                "artifacts": [pin(path) for path in sorted(directory.iterdir()) if path.is_file()],
                "passed": True,
            })
    need(len(runtime_cases) == 8, f"expected eight retained cases, found {len(runtime_cases)}")

    diagnostic_receipt = {
        "schema": "simant-dos-mono-8ed8-probe-prior-diagnostics-v1",
        "v33": diagnostic_worker("v33", {
            "linker": "rtlink400", "variant": "DATA", "expected_byte": "C7",
            "observed_hex": "00", "reason": "DATA-frame OFFSET16 selected the _DATA-relative target; _DATA group start was 0x8EDA, leaving +0xA skew from the intended literal-frame byte at 0x8FD8.",
        }),
        "v34": diagnostic_worker("v34", {
            "linker": "rtlink400", "variant": "DGROUP", "expected_byte": "35",
            "observed_hex": "00", "reason": "paragraph-aligned _DATA moved the owner target, but the positive marker was placed at _DATA+0xFF rather than _DATA+0x100; this is a failed fixture prediction.",
        }),
        "v35_initial_receipt_assembly": {
            "status": "RECEIPT_ASSEMBLY_FAILURE_AFTER_EIGHT_PASSING_RUNTIME_CASES",
            "expected_path": "build/workers/dos_mono_8ed8_owner_v35/sources/CHECK_DGROUP.LOG",
            "actual_compiler_log_path": "build/workers/dos_mono_8ed8_owner_v35/sources/CHECK_DGROUP.compiler.log",
            "cause": "The original builder's pin loop used the suffix LOG as a filename; save_assembly writes compiler logs with the .compiler.log suffix. It stopped after all eight runtime checks had printed PASS. This was not a runtime failure.",
            "builder_pin": pin(BUILDER),
        },
    }
    diagnostics_path = OUT / "diagnostic-history.json"
    diagnostics_path.write_text(json.dumps(diagnostic_receipt, indent=2) + "\n", encoding="utf-8")

    source_pins = [probe.repo_pin(rel) for rel in (
        "README.md", "docs/codegen-rules.md", "docs/tu-evidence.md", "AGENTS.md",
        "src/S01/m328E.asm", "tools/compiler.py", "tools/omf.py",
        "layout/toolchain.json", "layout/manifest.json")]
    artifact_paths = []
    for label in ("BASE_S01_328E", "POS_DGROUP_328E", "NEG_DATA_328E", "NEG_TARGET_328E",
                  "NEG_UNQUAL_328E", "RUNTIME_OWNER", "RUNTIME_CRT"):
        for suffix in ("ASM", "LST", "compiler.log"):
            p = src / f"{label}.{suffix}"
            if p.is_file():
                artifact_paths.append(p)
        for suffix in ("OBJ",):
            p = obj / f"{label}.{suffix}"
            if p.is_file():
                artifact_paths.append(p)
    for kind in ("DGROUP", "LITERAL", "DATA", "TARGET"):
        for suffix in ("ASM", "LST", "compiler.log"):
            artifact_paths.append(src / f"CHECK_{kind}.{suffix}")
        artifact_paths.append(obj / f"CHECK_{kind}.OBJ")
    tool_pins = []
    for linker_name in ("rtlink400", "rtlink610"):
        linker = probe.TC["linkers"][linker_name]
        for rel, expected_sha in linker["files"].items():
            tool_path = Path(linker["directory"]) / rel
            need(sha(tool_path) == expected_sha, f"pinned linker binary changed: {tool_path}")
            tool_pins.append(pin(tool_path))
    receipt = {
        "schema": "simant-dos-mono-8ed8-offset16-omf-probe-v35-finalized",
        "review_status": "root_review_pending",
        "status": "BOUNDED_TOOLCHAIN_PROBE_ONLY_NO_OWNER_OR_EXTENT_ADMISSION",
        "finalization": {
            "method": "Read-only assembly from retained v35 OMF objects and eight existing runtime directories; no compile, link or emulator invocation.",
            "builder_original_status": "Runtime checks passed; first receipt writer stopped only when pinning nonexistent CHECK_DGROUP.LOG.",
            "diagnostic_history": pin(diagnostics_path),
        },
        "scope": "Whole S01:m328E assembly relocation replacement at the four ADD BX,8ED8h immediate sites, plus test-owned shifted-DGROUP frame fixture; no game storage is defined or claimed.",
        "canonical_module": {
            "path": "src/S01/m328E.asm",
            "sha256": sha(ROOT / "src/S01/m328E.asm"),
            "four_instruction_offsets": [14, 161, 304, 473],
            "baseline_existing_fixups": [452, 621],
        },
        "recommended_source_transformation": {
            "declaration": "inside _DATA segment: EXTRN _g_8ED8:BYTE",
            "instruction": "replace each ADD BX,8ED8h with ADD BX,OFFSET DGROUP:_g_8ED8",
            "declaration_added_once": True,
            "only_four_instruction_operands_changed": True,
            "why_explicit_group": "MASM 5.10 emits external OFFSET16 target _g_8ED8 with frame group DGROUP; unqualified OFFSET _g_8ED8 defaults to segment _DATA in this module's DS assumption.",
        },
        "whole_module_omf": whole,
        "negative_controls": {
            "wrong_frame_DATA": wrong_frame,
            "wrong_target_DGROUP": wrong_target,
            "unqualified_external_default_frame": unqualified_control,
        },
        "runtime_fixture": {
            "fixture_scope": "Test-owned bytes only. PREFIX has a DATA-frame marker at DGROUP offset 0100h and a literal marker at 8FD8h. The _DATA SEGDEF is paragraph aligned; _g_8ED8 is at _DATA+0, _g_8EC0 at +4, 35h at +100h and D3h at +104h. BX starts at 0100h. No byte is claimed as game storage.",
            "checker_expression": "Compare SEG DGROUP to SS and DS; MOV BX,0100h; ADD BX,<case>; MOV AL,BYTE PTR SS:[BX] (0EEh guard result if either selector mismatches)",
            "fixture_omf_controls": fixture_controls,
            "owner_data_segment_definition": data_defs[0],
            "paragraph_alignment_map_check": "For each of eight cases, both Publics by Name and Publics by Value agree for FrameMarker, LiteralMarker, _g_8ED8 and _g_8EC0; _DATA begins at a DGROUP offset divisible by 16.",
            "cases": runtime_cases,
            "case_count": len(runtime_cases),
            "passed": all(row["passed"] for row in runtime_cases),
        },
        "limits": [
            "This establishes only MASM/OMF target and frame encoding, full-module object-delta isolation, and a bounded test-owned SS=DGROUP runtime consequence under experimental RTLink/Plus 4.00 and 6.10.",
            "It does not define or infer the game bytes/extent at 8ED8h, a source owner, index bounds, historical final-image placement, or full game behavior.",
            "No RTLink/emulator invocation occurred during this finalization step; runtime evidence is the retained v35 artifacts pinned below.",
        ],
        "source_and_repository_pins": source_pins,
        "compiler_and_fixture_artifact_pins": [pin(path) for path in sorted(artifact_paths)],
        "linker_binary_pins": tool_pins,
    }
    out = OUT / "receipt.json"
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "receipt": out.relative_to(ROOT).as_posix(),
        "receipt_sha256": sha(out),
        "diagnostics": diagnostics_path.relative_to(ROOT).as_posix(),
        "diagnostics_sha256": sha(diagnostics_path),
        "whole_module_omf_passed": whole["complete_module_omf_comparison_passed"],
        "runtime_cases": len(runtime_cases),
        "runtime_all_passed": all(row["passed"] for row in runtime_cases),
        "no_compile_link_emulator_invoked": True,
    }, indent=2))


if __name__ == "__main__":
    main()
