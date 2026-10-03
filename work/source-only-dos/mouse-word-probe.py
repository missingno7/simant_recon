"""Build a source-pinned, generated-only candidate receipt for the mouse words.

The probe compiles only test-owned fixtures and providers/mouse-words.c with the
pinned MSC toolchain, then runs the fixtures under RTLink/Plus 4.00 and 6.10.
It reads the existing startup-zero research receipt but never opens SIMANT.EXE.
All generated receipts, objects, maps, and executables stay under ignored
build/workers/dos_mouse_word_owners/candidate/.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = ROOT / "work" / "source-only-dos"
PROVIDER_PATH = SOURCE_ROOT / "providers" / "mouse-words.c"
PROBE_PATH = Path(__file__).resolve()
WORKER = ROOT / "build" / "workers" / "dos_mouse_word_owners" / "candidate"
FIXTURES = WORKER / "fixtures"
OBJECTS = WORKER / "objects"
TARGETS = ("g_9120", "g_9122", "g_9124")
EXPECTED_NEAR_WORDS = sorted(("_" + name, "near", 2) for name in TARGETS)
SYMBOL_RE = re.compile(r"(?<![A-Za-z0-9_])_?g_9120\b|(?<![A-Za-z0-9_])_?g_9122\b|(?<![A-Za-z0-9_])_?g_9124\b")
sys.path.insert(0, str(ROOT / "tools"))

BYTE_VIEW = """extern unsigned char near g_9120;
unsigned char far mouse_button_low(void) { return g_9120; }
void far mouse_button_low_set(unsigned char value) { g_9120 = value; }
"""

BAD_BYTE_VIEW = """extern unsigned char near g_9120[2];
unsigned char far mouse_button_low(void) { return g_9120[1]; }
void far mouse_button_low_set(unsigned char value) { g_9120[1] = value; }
"""

MAIN = """extern int near g_9120;
extern int near g_9122;
extern int near g_9124;
extern unsigned char far mouse_button_low(void);
extern void far mouse_button_low_set(unsigned char value);
extern int far puts(char far *text);

static int fail(void)
{
    puts("FAIL");
    return 1;
}

int main(void)
{
    if (g_9120 != 0 || g_9122 != 0 || g_9124 != 0)
        return fail();
    g_9120 = 0x1234;
    if (mouse_button_low() != 0x34)
        return fail();
    mouse_button_low_set(0x56);
    if (g_9120 != 0x1256)
        return fail();
    g_9122 = 0x2345;
    g_9124 = -0x1234;
    if (g_9122 != 0x2345 || g_9124 != -0x1234)
        return fail();
    puts("PASS");
    return 0;
}
"""


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def pin_file(path: Path, *, declared_sha: str | None = None) -> dict:
    digest = sha_file(path)
    if declared_sha is not None and digest != declared_sha:
        raise ValueError(f"source pin mismatch: {path}")
    return {"path": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path),
            "sha256": digest, "size": path.stat().st_size}


def source_hits(path: Path) -> list[dict]:
    rows = []
    for number, line in enumerate(path.read_text(encoding="latin1").splitlines(), 1):
        if SYMBOL_RE.search(line):
            rows.append({"line": number, "text": line.rstrip()})
    return rows


def escape_hits(rows: list[dict]) -> list[dict]:
    escaped = []
    for row in rows:
        line = row["text"]
        for name in TARGETS:
            symbol = r"_?" + re.escape(name)
            if (re.search(rf"&\s*{symbol}\b", line)
                    or re.search(rf"\b{symbol}\s*\[", line)
                    or re.search(rf"\b{symbol}\s*[+-]\s*\w", line)
                    or re.search(rf"\b(?:offset|lea|les|lds)\b.*\b{symbol}\b", line, re.I)):
                escaped.append({"line": row["line"], "symbol": name, "text": line})
    return escaped


def omf_word_rows(obj: bytes) -> list[tuple[str, str, int]]:
    from omf import OmfReader
    parsed = OmfReader(communals=True).read(obj)
    return sorted((row["name"], row["kind"], row["length"]) for row in parsed.communals)


def compile_fixture(name: str, source: str, *, flags: list[str] | None = None) -> bytes:
    if len(name) > 8:
        raise ValueError(f"fixture basename must fit DOS 8.3: {name}")
    FIXTURES.mkdir(parents=True, exist_ok=True)
    OBJECTS.mkdir(parents=True, exist_ok=True)
    (FIXTURES / f"{name}.C").write_bytes(source.encode("ascii"))
    import compiler
    result = compiler.compile_c(source, "msc600ax", flags or ["/AL", "/Os"],
                                basename=name, keep=False)
    if not result.ok or result.obj is None:
        raise RuntimeError(f"MSC compile failed for {name}:\n{result.log}")
    (OBJECTS / f"{name}.OBJ").write_bytes(result.obj)
    return result.obj


def read_text(path: Path) -> str:
    return path.read_text(encoding="latin1", errors="replace") if path.exists() else "<missing>"


def link_run(profile: str, case: str, owner_name: str, view_name: str,
             expected_log: str, compiled: dict[str, bytes], tool: dict,
             runner: dict, runtimes: list[dict]) -> dict:
    import compiler
    directory = WORKER / "link-runs" / profile / case
    directory.mkdir(parents=True, exist_ok=True)
    for name in ("PROBE.EXE", "PROBE.MAP", "RUN.LOG", "LINK.LOG"):
        (directory / name).unlink(missing_ok=True)
    for name in (owner_name, view_name, "MMAIN"):
        (directory / f"{name}.OBJ").write_bytes(compiled[name])
    for row in runtimes:
        shutil.copyfile(row["path"], directory / Path(row["path"]).name.upper())
    (directory / "PROBE.LNK").write_bytes(
        ("OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n"
         "LIBRARY LLIBCR, LIBH\r\n"
         f"FILE {owner_name}, {view_name}, MMAIN\r\n").encode("ascii"))
    (directory / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (directory / "RUN.BAT").write_bytes(
        (f"@echo off\r\nD:\\{tool['executable']} @PROBE.LNK < NUL > LINK.LOG\r\n"
         "PROBE.EXE > RUN.LOG\r\n").encode("ascii"))
    conf_lines = []
    for section, settings in runner["conf"].items():
        conf_lines.append("[" + section + "]")
        conf_lines.extend(f"{k}={v}" for k, v in settings.items())
    tool_dir = compiler.pinned_tree(tool)
    conf_lines += ["[autoexec]", f'mount c "{directory}"', f'mount d "{tool_dir}" -ro',
                   "c:", "call RUN.BAT", "exit"]
    conf = directory / "dosbox.conf"
    conf.write_text("\n".join(conf_lines) + "\n", encoding="ascii")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    result = subprocess.run([runner["path"], "-conf", str(conf), "-fastlaunch", "-exit", "-nomenu"],
                            cwd=directory, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            timeout=90, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    actual = read_text(directory / "RUN.LOG").strip()
    exe_path = directory / "PROBE.EXE"
    row = {"linker": profile, "case": case, "owner_object": owner_name,
           "view_object": view_name, "expected_log": expected_log, "actual_log": actual,
           "emulator_exit": result.returncode, "exe_sha256": sha_file(exe_path) if exe_path.exists() else None,
           "link_log": read_text(directory / "LINK.LOG"),
           "passed": exe_path.exists() and result.returncode == 0 and actual == expected_log}
    print(profile, case, actual, "PASS" if row["passed"] else "FAIL", flush=True)
    return row


def main() -> int:
    WORKER.mkdir(parents=True, exist_ok=True)
    import compiler
    compiler.WORK = WORKER / "compile-work"
    (WORKER / "compile-work").mkdir(parents=True, exist_ok=True)
    from omf import OmfReader

    manifest_path = ROOT / "layout" / "manifest.json"
    symbols_path = ROOT / "layout" / "symbols.json"
    behavior_path = ROOT / "evidence" / "behavior" / "manifest.json"
    startup_path = SOURCE_ROOT / "queue-lifetime-contract-v1.json"
    startup_research_path = SOURCE_ROOT / "queue-lifetime-research.py"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    symbols = json.loads(symbols_path.read_text(encoding="utf-8"))["data"]
    behavior = json.loads(behavior_path.read_text(encoding="utf-8"))
    startup = json.loads(startup_path.read_text(encoding="utf-8"))
    manifest_sources = {row["source"]: row["source_sha256"]
                        for row in manifest["modules"].values() if row.get("source")}

    # Re-scan canonical source files, then check that all actual references are
    # to manifest-owned canonical source files with current manifest hashes.
    canonical_hits = []
    src_root = ROOT / "src"
    for path in sorted(p for p in src_root.rglob("*") if p.suffix.lower() in (".c", ".asm")):
        hits = source_hits(path)
        if not hits:
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel not in manifest_sources:
            raise ValueError(f"canonical source with mouse-word reference is not in manifest: {rel}")
        canonical_hits.append({"path": rel, "sha256": sha_file(path),
                               "manifest_sha256": manifest_sources[rel], "refs": hits})
        if canonical_hits[-1]["sha256"] != canonical_hits[-1]["manifest_sha256"]:
            raise ValueError(f"canonical source differs from accepted manifest: {rel}")

    # Scan only the registered BEHAVIOR_EXACT implementation source paths,
    # excluding supplemental excerpts and preserved harness copies.
    exact_sources = {}
    exact_hits = []
    for function, entry in behavior["entries"].items():
        if entry.get("status") != "BEHAVIOR_EXACT":
            continue
        evidence_path = ROOT / entry["evidence_path"]
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        source_row = evidence.get("source", {})
        rel = source_row.get("path")
        if not rel:
            continue
        if rel in exact_sources:
            continue
        path = ROOT / rel
        pin = pin_file(path, declared_sha=source_row.get("sha256"))
        hits = source_hits(path)
        exact_sources[rel] = {"functions": [], "sha256": pin["sha256"], "refs": hits}
        exact_sources[rel]["functions"].append(function)
    for function, entry in behavior["entries"].items():
        if entry.get("status") != "BEHAVIOR_EXACT":
            continue
        evidence = json.loads((ROOT / entry["evidence_path"]).read_text(encoding="utf-8"))
        rel = (evidence.get("source", {}) or {}).get("path")
        if rel in exact_sources and function not in exact_sources[rel]["functions"]:
            exact_sources[rel]["functions"].append(function)
    for rel, row in sorted(exact_sources.items()):
        if row["refs"]:
            exact_hits.append({"path": rel, **row})
    if exact_hits:
        raise ValueError("registered BEHAVIOR_EXACT implementation source uses mouse-word names")

    # Registry establishes three separately named, adjacent word addresses;
    # do not infer provider allocation order or an aggregate from that fact.
    target_rows = {name: symbols[name] for name in TARGETS}
    if any((r["seg"], r["off"]) != (0x55B3, expected)
           for r, expected in zip(target_rows.values(), (0x9120, 0x9122, 0x9124))):
        raise ValueError("registered mouse-word addresses changed")
    registered_names_in_target_bytes = []
    target_start, target_end = 0x9120, 0x9126
    for name, row in symbols.items():
        if row.get("seg") == 0x55B3 and target_start <= row.get("off", -1) < target_end:
            registered_names_in_target_bytes.append({"name": name, "off": row["off"]})
    if {row["name"] for row in registered_names_in_target_bytes} != set(TARGETS):
        raise ValueError("unexpected registered name inside the three-word interval")
    adjacent_symbols = {name: symbols[name] for name in ("g_9126", "g_9128")}
    if (adjacent_symbols["g_9126"].get("off") != target_end
            or adjacent_symbols["g_9128"].get("off") != target_end + 2):
        raise ValueError("registered boundary symbols changed")
    all_canonical_escapes = [{"path": row["path"], **escape}
                             for row in canonical_hits for escape in escape_hits(row["refs"])]
    if all_canonical_escapes:
        raise ValueError(f"canonical pointer/index escape found: {all_canonical_escapes!r}")

    # Import the previously reviewed actual-original crt0 lifetime pin; verify
    # its relevant current source/library anchors and never open the oracle EXE.
    clear = startup["startup_clear"]["clear_interval"]
    clear_start = int(clear["start_inclusive"], 16)
    clear_end = int(clear["end_exclusive"], 16)
    main_call = startup["startup_clear"]["main_call"]
    if not (clear_start <= target_start and target_end <= clear_end):
        raise ValueError("actual original crt0 clear interval does not cover all three words")
    if not main_call.get("occurs_after_clear") or clear["fill"] != 0 or \
            startup["startup_clear"]["clear_instruction"]["text"] != "rep stosb byte ptr es:[di], al":
        raise ValueError("actual original crt0 zero-fill/main-order anchors changed")
    for rel, expected in startup["pins"]["sources"].items():
        if sha_file(ROOT / rel) != expected:
            raise ValueError(f"original-startup source pin changed: {rel}")
    if sha_file(startup_research_path) != startup["pins"]["research_script_sha256"]:
        raise ValueError("actual-original startup research-script pin changed")
    oracle_lock_path = ROOT / "layout" / "oracle.lock.json"
    if sha_file(oracle_lock_path) != startup["pins"]["oracle_lock_sha256"]:
        raise ValueError("original-startup receipt oracle-lock pin changed")
    runtime_rows = list(manifest["runtime"]["libraries"].values())
    llibcr = next((r for r in runtime_rows if Path(r["path"]).name.lower() == "llibcr.lib"), None)
    if not llibcr or llibcr["sha256"] != startup["pins"]["runtime_library"]["sha256"]:
        raise ValueError("actual-original startup runtime library differs from accepted manifest")

    provider_text = PROVIDER_PATH.read_text(encoding="ascii")
    expected_provider_rows = sorted(("_" + name, "near", 2) for name in TARGETS)
    owner_obj = compile_fixture("MOWNER", provider_text, flags=["/AL", "/Os", "/Gs"])
    owner_mod = OmfReader(communals=True).read(owner_obj, "MOWNER.OBJ")
    owner_rows = sorted((r["name"], r["kind"], r["length"]) for r in owner_mod.communals)
    if owner_rows != expected_provider_rows:
        raise ValueError(f"candidate provider OMF communal rows differ: {owner_rows!r}")
    if (owner_mod.publics or owner_mod.local_publics or owner_mod.linker_fixups
            or any(owner_mod.segment_lengths.values()) or any(owner_mod.segments.values())):
        raise ValueError("candidate provider emitted code, initialized data, publics, or fixups")

    main_obj = compile_fixture("MMAIN", MAIN)
    byte_obj = compile_fixture("MBYTE", BYTE_VIEW)
    bad_view_obj = compile_fixture("MBADVW", BAD_BYTE_VIEW)
    init_text = provider_text.replace("int near g_9120;", "int near g_9120 = 1;")
    if init_text == provider_text:
        raise ValueError("initialized-owner contrast edit did not match the provider")
    init_obj = compile_fixture("MINIT", init_text, flags=["/AL", "/Os", "/Gs"])
    short_text = provider_text.replace("int near g_9122;", "unsigned char near g_9122;")
    if short_text == provider_text:
        raise ValueError("wrong-extent contrast edit did not match the provider")
    short_obj = compile_fixture("MSHORT", short_text, flags=["/AL", "/Os", "/Gs"])
    short_rows = omf_word_rows(short_obj)
    if short_rows == expected_provider_rows:
        raise ValueError("wrong-extent contrast unexpectedly matched the candidate provider")
    if ("_g_9122", "near", 1) not in short_rows:
        raise ValueError(f"wrong-extent contrast did not emit a one-byte communal: {short_rows!r}")
    init_mod = OmfReader(communals=True).read(init_obj, "MINIT.OBJ")
    if {r["name"] for r in init_mod.communals} != {"_g_9122", "_g_9124"}:
        raise ValueError("initialized contrast did not remove only g_9120 from near COMDEFs")

    tc = compiler.toolchain()
    profile = tc["profiles"]["msc600ax"]
    runner = tc["runners"]["dosbox-x"]
    if sha_file(Path(runner["path"])) != runner["sha256"]:
        raise ValueError("pinned DOSBox-X runner hash mismatch")
    for runtime in runtime_rows:
        if sha_file(Path(runtime["path"])) != runtime["sha256"]:
            raise ValueError(f"runtime library hash mismatch: {runtime['path']}")
    compile_inputs = [
        {"path": rel, "sha256": digest}
        for rel, digest in profile["files"].items()
    ]
    link_inputs = {}
    runs = []
    compiled = {"MOWNER": owner_obj, "MMAIN": main_obj, "MBYTE": byte_obj,
                "MBADVW": bad_view_obj, "MINIT": init_obj}
    for linker in ("rtlink400", "rtlink610"):
        tool = tc["linkers"][linker]
        for rel, expected in tool["files"].items():
            path = Path(tool["directory"]) / rel
            if sha_file(path) != expected:
                raise ValueError(f"pinned linker component hash mismatch: {path}")
        link_inputs[linker] = tool["files"]
        for case, owner_name, view_name, expected in (
                ("positive_word_and_low_byte_view", "MOWNER", "MBYTE", "PASS"),
                ("wrong_high_byte_view", "MOWNER", "MBADVW", "FAIL"),
                ("initialized_owner_nonzero_contrast", "MINIT", "MBYTE", "FAIL")):
            runs.append(link_run(linker, case, owner_name, view_name, expected,
                                 compiled, tool, runner, runtime_rows))

    source_paths_with_hits = {row["path"] for row in canonical_hits}
    startup_main_source = main_call["claim_source"].replace("\\", "/")
    required_source_paths = sorted(source_paths_with_hits | {startup_main_source})
    source_pins = []
    for rel in required_source_paths:
        if rel not in manifest_sources:
            raise ValueError(f"source pin missing from canonical manifest: {rel}")
        source_pins.append(pin_file(ROOT / rel, declared_sha=manifest_sources[rel]))

    behavior_sources = [{"path": rel, "sha256": row["sha256"],
                         "functions": sorted(row["functions"]),
                         "mouse_word_references": row["refs"]}
                        for rel, row in sorted(exact_sources.items())]
    pins = [pin_file(PROBE_PATH), pin_file(PROVIDER_PATH), pin_file(manifest_path),
            pin_file(symbols_path), pin_file(behavior_path), pin_file(startup_path),
            pin_file(startup_research_path,
                     declared_sha=startup["pins"]["research_script_sha256"]),
            pin_file(ROOT / "layout" / "toolchain.json"), pin_file(oracle_lock_path)]
    for row in source_pins:
        pins.append(row)
    for row in behavior_sources:
        pins.append({"path": row["path"], "sha256": row["sha256"]})
    pins.extend({"path": Path(r["path"]).as_posix(), "sha256": r["sha256"]}
                for r in runtime_rows)
    pins.append({"path": runner["path"], "sha256": runner["sha256"]})
    candidate_contract = {
        "schema": "simant-source-only-dos-mouse-words-candidate-v1",
        "status": "candidate_only_pending_parent_review",
        "research_only": True,
        "candidate_provider": pin_file(PROVIDER_PATH),
        "members": [
            {"name": name, "dos_view": "16-bit word", "candidate_c_definition": "int near tentative definition",
             "registered_address": {"segment": target_rows[name]["seg"], "offset": target_rows[name]["off"]},
             "size_bytes": 2, "ownership_claim": "generated-only candidate; historical TU unknown"}
            for name in TARGETS
        ],
        "allocation_claims": {"aggregate": False, "source_order": False,
                              "historical_communal_order": False,
                              "registered_addresses_are_adjacent": True},
        "source_inventory": {"canonical_reference_files": canonical_hits,
                             "registered_behavior_exact_source_count": len(behavior_sources),
                             "registered_behavior_exact_reference_files": exact_hits,
                             "all_current_references_in_canonical_manifest": True,
                             "pointer_escape_index_or_arithmetic_refs": all_canonical_escapes,
                             "adjacent_non_members": adjacent_symbols},
        "lifecycle": {
            "mouse_initialization": "root:m1B73 _f_1B73_0046 seeds g_9122/g_9124 from screen midpoints at lines 304/307; it does not clear g_9120",
            "functional_event_writer": "root:m1B73 _f_1B73_0445 stores AX/CX/DX as words to all three at lines 748-750",
            "keyboard_updates": "root:m1B73 _f_1B73_051F and _f_1B73_0747 update x/y words; _f_1B73_0747 also edits low-byte button bits",
            "button_refresh": "root:m1B73 _f_1B73_0A40 writes the INT 33h function-3 BX result to g_9120 as a word at line 1481; this is driver refresh, not explicit zeroing",
            "other_consumers": "root:m1FD2, root:m00F8, and S26:m39C7 only read scalar values; none takes an address or indexes these symbols",
            "evidence_source_pins": source_pins
        },
        "original_startup_zero_range": {
            "evidence_path": "work/source-only-dos/queue-lifetime-contract-v1.json",
            "evidence_sha256": sha_file(startup_path),
            "verified_actual_clear": clear,
            "clear_instruction": startup["startup_clear"]["clear_instruction"],
            "main_call": main_call,
            "target_interval": {"segment": "DGROUP", "start_inclusive": "0x9120",
                                "end_exclusive": "0x9126", "length_bytes": 6},
            "target_fully_within_clear": True,
            "crt0_member_pin": startup["pins"]["crt0_member"],
            "runtime_library_pin": startup["pins"]["runtime_library"],
            "research_script_pin": pin_file(startup_research_path,
                                             declared_sha=startup["pins"]["research_script_sha256"]),
            "original_exe_identity_pin_only": startup["pins"]["oracle"],
            "original_exe_opened_by_probe": False,
            "scope": "The cited historical startup clears the registered original DGROUP interval before main; this does not establish that this generated candidate lands at those offsets or identify historical ownership."
        },
        "toolchain_probe": {
            "compiler_profile": "msc600ax",
            "compiler_profile_files": compile_inputs,
            "linkers": link_inputs,
            "runtime_libraries": runtime_rows,
            "omf_candidate_communal_rows": owner_mod.communals,
            "candidate_data_only_shape": {"publics": owner_mod.publics,
                                          "local_publics": owner_mod.local_publics,
                                          "fixups": owner_mod.linker_fixups,
                                          "segment_lengths": owner_mod.segment_lengths},
            "wrong_word_extent_rows": [
                {"name": name, "kind": kind, "length": length}
                for name, kind, length in short_rows],
            "wrong_word_extent_rejected_by_shape_check": True,
            "initialized_owner_communal_rows": init_mod.communals,
            "cases": runs,
            "all_required_controls_match": len(runs) == 6 and all(row["passed"] for row in runs)
        },
        "pins": pins,
        "limits": ["No original COMDEF-producing module or communal order is identified.",
                   "No aggregate layout is claimed.",
                   "Generated linker addresses and broader fixed-layout dependencies are not verified.",
                   "Source lifecycle evidence does not prove initialization before every game use beyond the cited startup clear.",
                   "No production tools, tests, canonical files, or evidence registries are modified."]
    }
    (WORKER / "candidate-contract.json").write_text(
        json.dumps(candidate_contract, indent=2) + "\n", encoding="utf-8")
    receipt = {"schema": "simant-source-only-dos-mouse-word-probe-receipt-v1",
               "candidate_contract_path": "build/workers/dos_mouse_word_owners/candidate/candidate-contract.json",
               "candidate_contract_sha256": sha_file(WORKER / "candidate-contract.json"),
               "probe_sha256": sha_file(PROBE_PATH),
               "provider_sha256": sha_file(PROVIDER_PATH),
               "cases": runs,
               "all_checks_pass": len(runs) == 6 and all(row["passed"] for row in runs),
               "wrong_word_extent_rejected": True,
               "original_exe_read": False}
    (WORKER / "probe-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return 0 if receipt["all_checks_pass"] and candidate_contract["toolchain_probe"]["all_required_controls_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
