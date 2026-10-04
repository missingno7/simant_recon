"""Bounded five-word MSC 6.00AX / RTLink owner candidate probe.

All generated inputs are fresh, ordinary C source in this worker's run tree.
No original image or reconstructed object is a compiler, linker, or runtime input.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
RUN = OUT / "runs" / RUN_ID
RUN.mkdir(parents=True, exist_ok=False)
sys.path.insert(0, str(ROOT / "tools"))
import compiler
import source_only_dos as dos
from omf import OmfReader

DENIED_READS = dos.install_input_guard()
compiler.WORK = RUN / "compiler-work"

INTAKE_PATH = ROOT / "work/source-only-dos/compile-and-intake-v1.json"
STATIC_INDEX_PATH = ROOT / "work/source-only-dos/static-completeness/index-v1.json"
SYMBOLS_PATH = ROOT / "layout/symbols.json"
TOOLCHAIN_PATH = ROOT / "layout/toolchain.json"
NAMES = ("fd_50F6_04C0", "fd_50F6_0B20", "fd_50F6_0F38", "fd_50F6_0FB6", "fd_50F6_0FFA")
TARGETS = {name: {"segment": "50F6", "offset": int(name[-4:], 16), "bytes": 2} for name in NAMES}
FLAGS = ["/AL", "/Os", "/Gs"]
MASK_RE = re.compile(r"/\*.*?\*/|//[^\n]*|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'", re.S)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pin(path: Path, expected: str | None = None) -> dict:
    raw = path.read_bytes()
    resolved = path.resolve()
    try:
        label = resolved.relative_to(ROOT).as_posix()
    except ValueError:
        label = str(resolved)
    result = {"path": label, "sha256": sha(raw), "size": len(raw)}
    if expected is not None and result["sha256"] != expected:
        raise RuntimeError(f"stale pin: {result['path']}")
    return result


def repo_path(path: str) -> Path:
    return ROOT / path.replace("\\", "/")


def checked_source(ref: dict) -> dict:
    result = pin(repo_path(ref["path"]), ref["sha256"])
    if "size" in ref and result["size"] != ref["size"]:
        raise RuntimeError(f"source size changed: {ref['path']}")
    return result


def load_source_sets() -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    intake = json.loads(INTAKE_PATH.read_text(encoding="utf-8"))
    if intake.get("schema") != "simant-source-only-dos-build-v1" or len(intake.get("translation_units", [])) != 127:
        raise RuntimeError("canonical intake is not the expected 127-unit set")
    canonical = []
    for tu in intake["translation_units"]:
        canonical.append(checked_source(tu["source"]) | {"module": tu["module"]})
    index = json.loads(STATIC_INDEX_PATH.read_text(encoding="utf-8"))
    if index.get("schema") != "simant-dos-strict-static-index-v1" or len(index.get("entries", {})) != 29:
        raise RuntimeError("strict effective-source index is not the expected 29-entry set")
    effective, receipts = [], []
    for function, ref in sorted(index["entries"].items()):
        receipt_path = repo_path(ref["path"])
        receipts.append(pin(receipt_path, ref["sha256"]))
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        selected = receipt.get("registered_source", {})
        role = "registered effective whole module"
        if function == "DrawBalloons":
            selected = receipt.get("audit", {}).get("source", {})
            role = "corrected effective whole module"
        if not selected.get("whole_module") or not selected.get("path") or selected.get("module") is None:
            raise RuntimeError(f"effective whole-module source is incomplete: {function}")
        effective.append(checked_source(selected) | {"module": selected["module"], "function": function, "role": role})
    if len({r["path"] for r in canonical + effective}) != 156:
        raise RuntimeError("canonical/effective source list does not contain 156 distinct source files")
    asm_paths = sorted((ROOT / "src").rglob("*.asm"))
    if len(asm_paths) != 29:
        raise RuntimeError(f"expected 29 tracked assembly sources, found {len(asm_paths)}")
    asm_sources = [pin(path) for path in asm_paths]
    return canonical, effective, receipts, asm_sources


def masked(text: str) -> str:
    return MASK_RE.sub(lambda m: "".join("\n" if ch == "\n" else " " for ch in m.group()), text)


def access_kind(line: str, name: str) -> str:
    q = re.escape(name)
    lhs = r"\b" + q + r"\b"
    if re.search(r"(?:\+\+|--)\s*" + lhs + r"|" + lhs + r"\s*(?:\+\+|--)", line):
        return "write_increment"
    if re.search(lhs + r"\s*(?:[+*/%&|^\-]?=)(?!=)", line):
        return "write_assignment"
    if re.search(r"(?<!&)&(?!&)\s*" + lhs, line):
        return "address_escape"
    if re.search(r"\b(?:extern|static|typedef)\b[^;\n]*\b" + q + r"\b", line):
        return "declaration"
    return "read_or_expression"


def source_scan(canonical: list[dict], effective: list[dict], receipts: list[dict], asm: list[dict]) -> dict:
    hits = {name: [] for name in NAMES}
    for set_name, rows in (("canonical_127", canonical), ("effective_strict_29", effective)):
        for source in rows:
            raw_lines = repo_path(source["path"]).read_text(encoding="latin1").splitlines()
            code_lines = masked("\n".join(raw_lines)).splitlines()
            for line_no, code_line in enumerate(code_lines, 1):
                for name in NAMES:
                    if re.search(r"\b" + re.escape(name) + r"\b", code_line):
                        hits[name].append({"set": set_name, "path": source["path"], "line": line_no,
                                           "access": access_kind(code_line, name),
                                           "text": raw_lines[line_no - 1].strip()})
    source_pins = {"schema": "simant-dos-readonly-word-owners-source-pins-v35",
        "counts": {"canonical_127": len(canonical), "effective_strict_29": len(effective),
                   "unique_game_sources": len({r["path"] for r in canonical + effective}), "tracked_src_asm": len(asm)},
        "canonical": canonical, "effective": effective, "strict_receipts": receipts, "asm_sources": asm}
    pin_path = RUN / "source-pins.json"
    pin_path.write_text(json.dumps(source_pins, indent=2) + "\n", encoding="utf-8")
    scan = {"schema": "simant-dos-readonly-word-owners-source-scan-v35",
        "source_pin_artifact": pin(pin_path), "counts": source_pins["counts"], "targets": TARGETS, "game_source_occurrences": hits,
        "conclusion_scope": "Identifier-shaped accesses in the 156 pinned whole-module C sources; original binary fixups and frame/bulk aliases are covered separately by v34. No current source target owner definition is inferred from absence.",
        "boundary_semantics": {"0FB6": "InvalEuMap right endpoint; also participates in centering and scroll-limit arithmetic.",
            "0FFA": "InvalEuMap bottom endpoint; also participates in vertical centering.",
            "setup_writer": "No setup writer was found in the bounded current-source and original-frame closure. The expected runtime values and original designer intent remain unresolved; no producer is invented."},
        "source_pins": pin_path.relative_to(ROOT).as_posix()}
    scan_path = RUN / "source-scan.json"
    scan_path.write_text(json.dumps(scan, indent=2) + "\n", encoding="utf-8")
    return scan


def comdef_rows(rows: list[dict]) -> list[dict]:
    return sorted(({k: row[k] for k in ("name", "kind", "count", "element_size", "length")} for row in rows),
                  key=lambda row: row["name"])


def raw_comdef_records(obj: bytes) -> list[dict]:
    records = []
    cursor = 0
    for kind, body in OmfReader.records(obj):
        length = int.from_bytes(obj[cursor + 1:cursor + 3], "little")
        record = obj[cursor:cursor + 3 + length]
        if kind == OmfReader.COMDEF:
            records.append({"object_offset": cursor, "record_type": f"{kind:02X}", "record_length_including_checksum": len(record),
                            "record_hex": record.hex().upper(), "body_hex": body.hex().upper()})
        cursor += 3 + length
    return records


def compile_case(tag: str, source: str) -> tuple[bytes, dict, object]:
    result = compiler.compile_c(source, "msc600ax", FLAGS, basename=tag, keep=True)
    if not result.ok or result.obj is None:
        raise RuntimeError(f"MSC 6.00AX failed for {tag}:\n{result.log}")
    artifacts = RUN / "compile-artifacts"
    artifacts.mkdir(exist_ok=True)
    src_path, obj_path, log_path = artifacts / f"{tag}.C", artifacts / f"{tag}.OBJ", artifacts / f"{tag}.LOG"
    src_path.write_text(source, encoding="ascii", newline="\r\n")
    obj_path.write_bytes(result.obj)
    with log_path.open("w", encoding="latin1", newline="") as stream:
        stream.write(result.log)
    parsed = OmfReader(communals=True).read(result.obj, f"{tag}.OBJ")
    receipt = {"tag": tag, "profile": "msc600ax", "flags": FLAGS + compiler.toolchain()["profiles"]["msc600ax"].get("required_flags", []),
        "argv": result.argv, "source": pin(src_path), "object": pin(obj_path), "compiler_log": pin(log_path),
        "communals": comdef_rows(parsed.communals), "segment_lengths": parsed.segment_lengths,
        "segment_names": sorted(parsed.segments), "publics": parsed.publics, "externals": parsed.externals,
        "linker_fixups": parsed.linker_fixups,
        "raw_COMDEF_records": raw_comdef_records(result.obj)}
    return result.obj, receipt, parsed


def owner_source(overrides: dict[str, str] | None = None, initializers: dict[str, str] | None = None) -> str:
    overrides, initializers = overrides or {}, initializers or {}
    rows = ["/* Fresh source-only BSS owner control; no historical payload copied. */"]
    for name in NAMES:
        ctype = overrides.get(name, "int")
        init = " = " + initializers[name] if name in initializers else ""
        rows.append(f"{ctype} far {name}{init};")
    return "\n".join(rows) + "\n"


def consumer_source(mode: str) -> str:
    decls = "\n".join(f"extern int far {name};" for name in NAMES)
    if mode == "positive":
        values = [-1, -1234, 0x1234, -2, 0x2345]
        checks = []
        writes = []
        raw = []
        for i, (name, value) in enumerate(zip(NAMES, values)):
            checks.append(f"    if ({name} != 0) goto fail;")
            writes.append(f"    {name} = ({value});")
            raw.append(f"    p = (unsigned char far *)&{name}; if (p[0] != 0x{value & 255:02x} || p[1] != 0x{(value >> 8) & 255:02x}) goto fail;")
        typed = "\n".join(f"    if ({n} != ({v})) goto fail;" for n, v in zip(NAMES, values))
        return (decls + "\nextern int far puts(char far *text);\nint main(void)\n{\n"
            "    unsigned char far *p;\n" + "\n".join(checks) + "\n" + "\n".join(writes) + "\n" + typed + "\n"
            + "\n".join(raw) + "\n    puts(\"PASS\"); return 0;\nfail: puts(\"FAIL\"); return 1;\n}\n")
    if mode == "boundary":
        # Each accepted raw view is exactly two bytes. A shifted two-byte view
        # would cross the declared word, so the fixture rejects it before access.
        checks = []
        for i, name in enumerate(NAMES):
            value = (0x5030 + i * 0x0101)
            checks.append(f"    p=(unsigned char far *)&{name}; p[0]=0x{value & 255:02x}; p[1]=0x{(value >> 8) & 255:02x}; if ({name} != 0x{value:04x}) goto fail;")
        return (decls + "\nextern int far puts(char far *text);\n"
            "int AcceptRawView(unsigned offset, unsigned length)\n{\n    return offset <= 2U && length <= 2U - offset;\n}\n"
            "int main(void)\n{\n    unsigned char far *p;\n"
            "    if (!AcceptRawView(0U, 2U) || AcceptRawView(1U, 2U)) goto fail;\n"
            + "\n".join(checks) + "\n    puts(\"PASS\"); return 0;\nfail: puts(\"FAIL\"); return 1;\n}\n")
    if mode == "signedness":
        return ("extern unsigned int far fd_50F6_04C0;\nextern int far puts(char far *text);\n"
            "int main(void) { fd_50F6_04C0=0xffffU; if ((long)fd_50F6_04C0 < 0L) { puts(\"PASS\"); return 0; } puts(\"FAIL\"); return 1; }\n")
    raise ValueError(mode)


def map_publics(map_text: str, header: str) -> dict[str, str]:
    lines = map_text.splitlines()
    start = next((i for i, line in enumerate(lines) if header in line), None)
    if start is None:
        return {}
    result = {}
    for line in lines[start + 1:]:
        if any(label in line for label in ("Publics by Name", "Publics by Value", "Line Numbers for", "Module Summary")):
            break
        m = re.match(r"\s*([0-9A-F]{4}:[0-9A-F]{4})\s+\w+\s+(_fd_50F6_[0-9A-F]{4})\s*$", line, re.I)
        if m:
            result[m.group(2).lower()] = m.group(1).upper()
    return result


def map_receipt(map_text: str) -> dict:
    data_rows, resident, overlay = [], [], []
    section = ""
    for line in map_text.splitlines():
        stripped = line.strip()
        if stripped == "Resident":
            section = "resident"
        elif stripped.startswith("Overlay"):
            section = "overlay"
        elif stripped.startswith("Section#"):
            section = "sections"
        if any(re.search(r"\b" + re.escape(tag) + r"\b", line, re.I) for tag in ("FAR_BSS", "FAR_DATA", "_BSS", "_DATA")):
            if re.match(r"^\s*[0-9A-F]{5}H\s", line):
                data_rows.append(stripped)
                if section == "resident": resident.append(stripped)
                if section == "overlay": overlay.append(stripped)
    name, value = map_publics(map_text, "Publics by Name"), map_publics(map_text, "Publics by Value")
    expected = {"_" + n.lower() for n in NAMES}
    chosen_name = {k: name[k] for k in sorted(expected) if k in name}
    chosen_value = {k: value[k] for k in sorted(expected) if k in value}
    return {"resident_data_section_rows": resident, "overlay_data_section_rows": overlay,
        "all_data_section_rows": data_rows, "target_publics_by_name": chosen_name,
        "target_publics_by_value": chosen_value, "both_public_sections_exact": chosen_name == chosen_value and len(chosen_name) == 5}


def link_run(linker_name: str, case: str, consumer_obj: bytes, owner_obj: bytes,
             runtimes: list[dict], linker: dict, runner: dict, tool_dir: Path) -> dict:
    directory = RUN / "link-runs" / linker_name / case
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "TEST.OBJ").write_bytes(consumer_obj)
    (directory / "OWNER.OBJ").write_bytes(owner_obj)
    for lib in runtimes:
        shutil.copyfile(lib["path"], directory / Path(lib["path"]).name.upper())
    staged_runtime_libraries = [pin(directory / Path(lib["path"]).name.upper()) for lib in runtimes]
    (directory / "PROBE.LNK").write_bytes(b"OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\nLIBRARY LLIBCR, LIBH\r\nFILE TEST\r\nBEGINAREA\r\nSECTION FILE OWNER\r\nENDAREA\r\n")
    (directory / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (directory / "RUN.BAT").write_bytes((f"@echo off\r\nD:\\{linker['executable']} @PROBE.LNK < NUL > LINK.LOG\r\nPROBE.EXE > RUN.LOG\r\n").encode("ascii"))
    conf = []
    for section, settings in runner["conf"].items():
        conf.append("[" + section + "]")
        conf += [f"{k}={v}" for k, v in settings.items()]
    conf += ["[autoexec]", f'mount c "{directory.resolve()}"', f'mount d "{tool_dir.resolve()}" -ro', "c:", "call RUN.BAT", "exit"]
    (directory / "dosbox.conf").write_text("\n".join(conf) + "\n", encoding="ascii")
    env = os.environ.copy(); env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    timed_out = False
    try:
        proc = subprocess.run([runner["path"], "-conf", str(directory / "dosbox.conf"), "-fastlaunch", "-exit", "-nomenu"],
            cwd=directory, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        exit_code = proc.returncode
    except subprocess.TimeoutExpired:
        timed_out, exit_code = True, -1
    names = ("PROBE.EXE", "PROBE.MAP", "LINK.LOG", "RUN.LOG")
    outputs = [pin(directory / n) for n in names if (directory / n).is_file()]
    inputs = [pin(directory / n) for n in ("TEST.OBJ", "OWNER.OBJ", "PROBE.LNK", "RTLINK.CFG", "RUN.BAT", "dosbox.conf")]
    map_text = (directory / "PROBE.MAP").read_text(encoding="latin1", errors="replace") if (directory / "PROBE.MAP").exists() else ""
    run_bytes = (directory / "RUN.LOG").read_bytes() if (directory / "RUN.LOG").exists() else b""
    return {"linker": linker_name, "case": case, "actual_run_log": run_bytes.decode("latin1").strip(),
        "run_log_hex": run_bytes.hex(), "emulator_exit": exit_code, "timed_out": timed_out,
        "linker_produced_executable": (directory / "PROBE.EXE").exists(), "map_sections": map_receipt(map_text),
        "raw_map_path": pin(directory / "PROBE.MAP") if (directory / "PROBE.MAP").exists() else None,
        "link_log_path": pin(directory / "LINK.LOG") if (directory / "LINK.LOG").exists() else None,
        "run_log_path": pin(directory / "RUN.LOG") if (directory / "RUN.LOG").exists() else None,
        "staged_runtime_libraries": staged_runtime_libraries,
        "staged_inputs": inputs, "raw_outputs": outputs}


def main() -> None:
    canonical, effective, receipts, asm = load_source_sets()
    source_doc = source_scan(canonical, effective, receipts, asm)
    symbols = json.loads(SYMBOLS_PATH.read_text(encoding="utf-8"))
    current_inputs = [pin(p) for p in (INTAKE_PATH, STATIC_INDEX_PATH, SYMBOLS_PATH, TOOLCHAIN_PATH, ROOT / "layout/manifest.json",
        ROOT / "tools/compiler.py", ROOT / "tools/source_only_dos.py", ROOT / "tools/omf.py")]
    positive_src = owner_source()
    width_src = owner_source({NAMES[0]: "long"})
    unsigned_src = owner_source({NAMES[0]: "unsigned int"})
    initialized_src = owner_source(initializers={NAMES[0]: "1"})
    compiled = {}
    for tag, src in (("OWNV35", positive_src), ("WIDV35", width_src), ("SIGV35", unsigned_src), ("INITV35", initialized_src),
                     ("TYPV35", consumer_source("positive")), ("BNDV35", consumer_source("boundary")),
                     ("UNSV35", consumer_source("signedness"))):
        obj, receipt, parsed = compile_case(tag, src)
        compiled[tag] = {"obj": obj, "receipt": receipt, "parsed": parsed}

    expected = [{"name": "_" + n, "kind": "far", "count": 2, "element_size": 1, "length": 2} for n in NAMES]
    owner_actual = compiled["OWNV35"]["receipt"]["communals"]
    if owner_actual != expected:
        raise RuntimeError(f"natural owner COMDEFs differ from the five expected 2-byte far commons: {owner_actual}")
    width_rows = compiled["WIDV35"]["receipt"]["communals"]
    if next(r for r in width_rows if r["name"] == "_" + NAMES[0])["length"] != 4:
        raise RuntimeError("long width contrast did not emit a 4-byte far COMDEF")
    signed_rows = compiled["SIGV35"]["receipt"]["communals"]
    if signed_rows != owner_actual:
        raise RuntimeError("unsigned contrast changed the same-width COMDEF shape")
    init_rows = compiled["INITV35"]["receipt"]["communals"]
    if any(r["name"] == "_" + NAMES[0] for r in init_rows):
        raise RuntimeError("nonzero-initialized word unexpectedly remained a COMDEF")
    if not compiled["INITV35"]["receipt"]["segment_lengths"]:
        raise RuntimeError("nonzero-initializer control produced no initialized segment")

    tc = compiler.toolchain()
    manifest = json.loads((ROOT / "layout/manifest.json").read_text(encoding="utf-8"))
    runtimes = list(manifest["runtime"]["libraries"].values())
    if not {Path(r["path"]).stem.upper() for r in runtimes}.issuperset({"LLIBCR", "LIBH"}):
        raise RuntimeError("runtime manifest lacks the expected LLIBCR/LIBH libraries")
    runtime_rows, linker_pins, runner_pins = [], {}, {}
    for linker_name in ("rtlink400", "rtlink610"):
        linker = tc["linkers"][linker_name]
        tool_dir = compiler.pinned_tree(linker)
        runner = tc["runners"][linker["runner"]]
        linker_pins[linker_name] = {"executable": pin(Path(linker["directory"]) / linker["executable"]),
            "tool_files": [pin(Path(linker["directory"]) / rel, digest) for rel, digest in linker["files"].items()],
            "mounted_tree_files": [pin(tool_dir / rel) for rel in linker["files"]]}
        runner_pins[linker["runner"]] = pin(Path(runner["path"]), runner["sha256"])
        for case_name, tag, owner_tag, expected_log in (
            ("typed_raw_startup0", "TYPV35", "OWNV35", "PASS"),
            ("typed_raw_boundary_guard", "BNDV35", "OWNV35", "PASS"),
            ("unsigned_signedness_contrast", "UNSV35", "OWNV35", "FAIL"),
            ("initialized_owner_startup_contrast", "TYPV35", "INITV35", "FAIL")):
            row = link_run(linker_name, case_name, compiled[tag]["obj"], compiled[owner_tag]["obj"], runtimes, linker, runner, tool_dir)
            row["expected_run_log"] = expected_log
            row["passed"] = row["actual_run_log"] == expected_log and row["emulator_exit"] == 0 and not row["timed_out"] and row["linker_produced_executable"]
            row["gating_for_owner_candidate"] = True
            runtime_rows.append(row)
    runtime_lib_pins = [pin(Path(row["path"]), row["sha256"]) for row in runtimes]
    cp = tc["profiles"]["msc600ax"]
    cr = tc["runners"][cp["runner"]] if cp.get("runner") else tc["runner"]
    compiler_pins = {"profile_files": [pin(Path(cp["directory"]) / rel, digest) for rel, digest in cp["files"].items()],
        "runner": pin(Path(cr["path"]), cr["sha256"])}
    prior_v34 = json.loads((ROOT / "build/workers/dos_readonly_word_closure_v34/receipt-v34.json").read_text(encoding="utf-8"))
    prior_target_rows = {row["address"].split(":", 1)[1]: row for row in prior_v34["targets"]}
    all_runtime_evidence = [{"linker": row["linker"], "case": row["case"], "expected_run_log": row["expected_run_log"],
        "actual_run_log": row["actual_run_log"], "passed": row["passed"], "map_sections": row["map_sections"],
        "raw_MAP": row["raw_map_path"], "raw_LINK_LOG": row["link_log_path"], "raw_RUN_LOG": row["run_log_path"],
        "staged_objects_and_link_inputs": row["staged_inputs"], "staged_runtime_libraries": row["staged_runtime_libraries"],
        "raw_outputs": row["raw_outputs"]} for row in runtime_rows]
    all_omf_control_evidence = {tag: {"source": compiled[tag]["receipt"]["source"],
        "object": compiled[tag]["receipt"]["object"], "compiler_log": compiled[tag]["receipt"]["compiler_log"],
        "COMDEFs": compiled[tag]["receipt"]["communals"], "segment_lengths": compiled[tag]["receipt"]["segment_lengths"],
        "raw_COMDEF_records": compiled[tag]["receipt"]["raw_COMDEF_records"]}
        for tag in ("OWNV35", "WIDV35", "SIGV35", "INITV35")}
    contract = {"schema": "simant-far-bss-normalized-storage-candidate-v35",
        "status": "ROOT_FALSE_CANDIDATE_FOR_REVIEW", "root_reviewed": False, "root_claimed": False,
        "module": "source-owned:remaining-far-state-words",
        "module_identity_scope": "Normalized source-owned family label only; it does not identify the historical defining translation unit.",
        "storage_region": "FAR_BSS", "original_segment": "50F6", "proposed_source_declaration": "signed int far <symbol>;",
        "candidate_object_extent_bytes": 2, "extent_basis": "Natural target-typed C scalar plus actual MSC 6.00AX FAR COMDEF byte length; no inferred gap/neighbor size.",
        "candidate_initializer": "none (tentative definition)", "original_image_initial_value": 0,
        "original_initial_value_evidence": "v33 locked-image measurement: complete FAR_BSS region is zero; v34 target receipts repeat 0000 per word.",
        "isolated_candidate_startup_value": 0,
        "isolated_startup_controls": ["rtlink400/typed_raw_startup0", "rtlink610/typed_raw_startup0"],
        "mutable": True, "permanent_zero_claim": False, "read_only_claim": False,
        "full_game_alias_clobber_closure": "OPEN under existing source-only and layout gates",
        "full_game_first_use_lifetime_order": "OPEN under existing source-only and layout gates",
        "historical_defining_translation_unit_and_COMDEF_extent": "OPEN",
        "scope_blocker_beyond_historical_TU": "No additional typed-representation or concrete-neighbor/index extent blocker was identified in the pinned source and v34 frontiers. The map-bound runtime value/setup behavior remains unresolved because no setup writer was found; this blocks a map-dimension behavior claim, not the proposed two-byte source representation.",
        "synthetic_boundary_control_limit": "The runtime guard tests its own offset-plus-length policy. It is not evidence of a historical source object extent.",
        "aliases": {name: [] for name in NAMES},
        "alias_closure_basis": "No current reviewed data alias is in segment 50F6; v34 provider/view/save overlaps are empty for each target and its named concrete frontiers are closed.",
        "save_rec_pointer_fixups": [], "save_rec_target_payload_overlaps": [],
        "historical_layout_gate": "Unchanged. Any later placement must satisfy the existing exact source/layout ownership gates; this candidate neither edits nor bypasses them.",
        "targets": [{"symbol": name, "address": f"50F6:{TARGETS[name]['offset']:04X}",
            "candidate_type": "signed int far", "candidate_extent": f"[0x{TARGETS[name]['offset']:04X},0x{TARGETS[name]['offset']+2:04X})",
            "observed_original_direct_reads": prior_target_rows[f"{TARGETS[name]['offset']:04X}"]["direct_original_references"]["reads"],
            "observed_original_direct_stores": prior_target_rows[f"{TARGETS[name]['offset']:04X}"]["direct_original_references"]["writes"],
            "functional_role": prior_target_rows[f"{TARGETS[name]['offset']:04X}"]["functional_role"],
            "concrete_alias_or_index_frontier": prior_target_rows[f"{TARGETS[name]['offset']:04X}"]["concrete_adjacent_write_route"],
            "frontier_result": prior_target_rows[f"{TARGETS[name]['offset']:04X}"]["route_closure"],
            "historical_extent": "OPEN; do not promote the candidate COMDEF byte size to an original historical extent."} for name in NAMES],
        "map_endpoint_state": {"fd_50F6_0FB6": {"role": "InvalEuMap right endpoint, clamped by consumer to 127 and iterated inclusively", "setup_writer": "none found", "intended_or_runtime_value": "unknown"},
            "fd_50F6_0FFA": {"role": "InvalEuMap bottom endpoint, clamped by consumer to 63 and iterated inclusively", "setup_writer": "none found", "intended_or_runtime_value": "unknown"}},
        "evidence": {"source_pins": pin(RUN / "source-pins.json"), "source_scan": pin(RUN / "source-scan.json"),
            "natural_provider_object": compiled["OWNV35"]["receipt"]["object"],
            "all_provider_control_OMF_and_raw_compiler_logs": all_omf_control_evidence,
            "all_RTLink_MAP_sections_and_complete_raw_logs": all_runtime_evidence,
            "v34_review_pins": [pin(ROOT / "build/workers/dos_readonly_word_closure_v34/review-v34.md"),
                pin(ROOT / "build/workers/dos_readonly_word_closure_v34/receipt-v34.json"), pin(ROOT / "build/workers/dos_readonly_word_closure_v34/frame-sweep-v34.json")],
            "v33_initial_value_pins": [pin(ROOT / "build/workers/dos_readonly_bss_semantics_v33/review-v33.md"),
                pin(ROOT / "build/workers/dos_readonly_bss_semantics_v33/receipt-v33.json")]}}
    contract_path = RUN / "storage-contract.json"
    contract_path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    candidate = {"schema": "simant-dos-readonly-word-owner-candidate-v35", "status": "CANDIDATE_NOT_ADMITTED_ROOT_FALSE",
        "root_reviewed": False, "root_claimed": False, "admission_eligible": False,
        "purpose": "Provide a natural mutable zero-initialized source owner shape with compiler/linker/runtime controls; make no historical COMDEF, permanent-zero, designer-intent, or unobserved writer claim.",
        "targets": [{"name": n, **TARGETS[n], "candidate_type": "signed int far", "original_loaded_bytes": "0000",
            "source_owner_status": "candidate supported by natural COMDEF and clean startup test; historical owner identity remains open",
            "role": "InvalEuMap right endpoint" if n.endswith("0FB6") else ("InvalEuMap bottom endpoint" if n.endswith("0FFA") else None),
            "setup_writer": "none found in bounded current-source/original-frame closure; runtime value and intended initialization unresolved" if n.endswith(("0FB6", "0FFA")) else None} for n in NAMES],
        "source_set": source_doc["source_pin_artifact"], "source_counts": source_doc["counts"],
        "current_source_scan": pin(RUN / "source-scan.json"), "source_occurrences": source_doc["game_source_occurrences"],
        "original_closure_reference": {"review": "build/workers/dos_readonly_word_closure_v34/review-v34.md",
            "receipt": "build/workers/dos_readonly_word_closure_v34/receipt-v34.json",
            "scope_note": "v34's named targets and concrete neighboring/indexed write-route analysis remain the original-frame and current-layout evidence; v35 adds prospective source-object/compiler/linker/startup evidence only."},
        "prior_closure_pins": [pin(ROOT / "build/workers/dos_readonly_word_closure_v34/review-v34.md"),
            pin(ROOT / "build/workers/dos_readonly_word_closure_v34/receipt-v34.json"),
            pin(ROOT / "build/workers/dos_readonly_word_closure_v34/frame-sweep-v34.json"),
            pin(ROOT / "build/workers/dos_readonly_bss_semantics_v33/review-v33.md"),
            pin(ROOT / "build/workers/dos_readonly_bss_semantics_v33/receipt-v33.json")],
        "normalized_storage_contract": pin(contract_path),
        "natural_provider": compiled["OWNV35"]["receipt"],
        "compile_controls": {key: compiled[key]["receipt"] for key in ("WIDV35", "SIGV35", "INITV35")},
        "consumer_controls": {key: compiled[key]["receipt"] for key in ("TYPV35", "BNDV35", "UNSV35")},
        "expected_COMDEFs": expected,
        "control_interpretation": {"signedness": "OMF COMDEF shape does not encode C signedness; signed int source type and runtime negative comparison are needed.",
            "width": "Long contrast changes the first far communal from 2 to 4 bytes.",
            "nonzero_initializer": "The first symbol leaves COMDEF and appears in initialized storage.",
            "boundary": "Typed/raw startup0 checks touch exactly bytes 0 and 1. Boundary guard accepts offset 0,length 2 and rejects offset 1,length 2 before dereference; its OMF pointer/fixup is synthetic fixture evidence, not historical SaveRec evidence."},
        "runtime_cases": runtime_rows,
        "tool_pins": {"compiler": compiler_pins, "runtime_libraries": runtime_lib_pins, "linkers": linker_pins, "runners": runner_pins},
        "common_input_pins": current_inputs,
        "denied_oracle_reads": list(DENIED_READS),
        "limits": ["Fresh provider proves MSC 6.00AX's prospective COMDEF shape, not which historical translation unit defined these words.",
            "RTLink 4.00/6.10 tests prove clean isolated startup zeroing and mutable typed/raw access for these fixtures, not full-game runtime initialization order.",
            "v34 identifies FB6/FFA as actual inclusive map bounds but found no setup writer; expected runtime values and designer intent remain unknown.",
            "No original EXE, COMDEF payload, game object, reconstructed image, or metadata payload is an input to compilation, linking, or runtime."]}
    cand_path = RUN / "candidate.json"
    cand_path.write_text(json.dumps(candidate, indent=2) + "\n", encoding="utf-8")
    markdown = ["# Five FAR_BSS signed-word owner candidate v35", "",
        "This bounded candidate defines five separate mutable `int far` source objects. The original image value is zero, and both isolated RTLink startup controls start them at zero; this does not assert permanent zero, a historical defining TU, or original designer intent.", "",
        "| Target | Proposed source type | Candidate OMF size | Current observed role | Setup writer |", "|---|---|---:|---|---|"]
    for n in NAMES:
        role = "InvalEuMap right endpoint" if n.endswith("0FB6") else "InvalEuMap bottom endpoint" if n.endswith("0FFA") else "see v34 named reader evidence"
        setup = "not found; value unresolved" if n.endswith(("0FB6", "0FFA")) else "not asserted by this probe"
        markdown.append(f"| `{n}` | `signed int far` | 2 bytes | {role} | {setup} |")
    markdown += ["", "MSC 6.00AX whole-provider OMF contains exactly five 2-byte FAR COMDEFs. Same-width unsigned source preserves OMF shape; a long contrast changes the target to 4 bytes; a nonzero initializer removes that target from COMDEF and emits initialized data. Both RTLink versions pass zero-start plus mutable typed/raw checks and a boundary guard that rejects offset 1 plus length 2. The raw MAP files (including Resident and Overlay sections), complete link/compiler logs, object sources, OMF control records, and pins are preserved under the run directory.", "",
        "Historical COMDEF owner/extent, full-game zero-before-first-use, dynamic writer/lifetime, FB6/FFA setup/value, and designer intent remain open. This worker is not admitted or root-claimed.", ""]
    md_path = RUN / "candidate.md"; md_path.write_text("\n".join(markdown), encoding="utf-8")
    addendum_lines = ["# v35 append-only clarification", "",
        "The original loaded value is known: the locked original image contains zero at all five FAR_BSS addresses when loaded. This is an observed image-initial value; it does not establish the value at first game read or later. It is not evidence of original designer intent and not a permanent-zero claim. The proposed C objects remain mutable.", "",
        "The synthetic boundary guard only verifies its own test policy: an exact two-byte raw view at offset zero is accepted, and an offset-one/two-byte view is rejected before it dereferences memory. It does not prove any historical object's extent. The prospective two-byte size is supported by the natural signed `int far` declarations and the fresh MSC 6.00AX COMDEF records. The source-wide target-typed accesses and v34's concrete provider/index/frame/SaveRec alias frontiers provide separate no-overlap evidence; they do not convert a candidate extent into historical COMDEF identity.", "",
        "The normalized storage contract is root-false. Each target is modeled as a mutable, uninitialized source-state `int far` whose isolated RTLink startup value is zero. The unchanged layout gates still apply to any future placement or admission. The original defining TU and historical extent remain open.", "",
        "For `fd_50F6_0FB6` and `fd_50F6_0FFA`, `RandWorld`, S22 `SetAlarmDropState`, and the two `SetMapPlane*` callers pass the words as right/bottom endpoints to active `InvalEuMap`. It clamps to 127/63 and iterates inclusively; zero bounds can reduce the request to cell `(0,0)` when the viewport predicate permits. No setup writer was found. The image-initial values are zero, but the value at first use, later runtime values, and intended map size remain unknown. This is a concrete behavior/setup gap, not a basis to relabel the observed uses as arbitrary offsets.", "",
        "Full-game alias clobber closure, first-use order, and lifetime remain open under the existing gates. Current pinned game C sources and the reviewed original-frame sweep found no concrete target writer; this does not assert that the words remain zero for the full game lifetime.", ""]
    addendum_path = RUN / "addendum-v35.md"; addendum_path.write_text("\n".join(addendum_lines), encoding="utf-8")
    run_index = {"schema": "simant-dos-readonly-word-owners-run-index-v35", "run_id": RUN_ID,
        "candidate": pin(cand_path), "markdown": pin(md_path), "source_pins": pin(RUN / "source-pins.json"),
        "source_scan": pin(RUN / "source-scan.json"), "storage_contract": pin(contract_path),
        "addendum": pin(addendum_path), "run_directory": RUN.relative_to(ROOT).as_posix(),
        "root_reviewed": False, "root_claimed": False,
        "runtime_all_cases_pass": all(r["passed"] for r in runtime_rows),
        "compile_controls": {key: {"COMDEFs": compiled[key]["receipt"]["communals"],
            "segment_lengths": compiled[key]["receipt"]["segment_lengths"], "raw_COMDEF_records": compiled[key]["receipt"]["raw_COMDEF_records"]}
            for key in ("OWNV35", "WIDV35", "SIGV35", "INITV35")}}
    index_path = OUT / f"run-index-{RUN_ID}.json"
    index_path.write_text(json.dumps(run_index, indent=2) + "\n", encoding="utf-8")
    if not run_index["runtime_all_cases_pass"]:
        raise RuntimeError("one or more RTLink runtime controls failed; review complete preserved raw logs")
    print(json.dumps(run_index, indent=2))


if __name__ == "__main__":
    main()
