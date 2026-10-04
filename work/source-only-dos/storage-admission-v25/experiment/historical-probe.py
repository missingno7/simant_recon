#!/usr/bin/env python3
"""Audit and test a root-false candidate for fd_50F6_09FC.

The source audit independently verifies the canonical+strict source set and
registry views. Runtime fixtures use only the candidate source, MSC 6.00AX,
the pinned CRT/runtime, RTLink 4.00/6.10, and DOSBox-X. No game/original build
inputs or original data bytes are read.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WORKER = ROOT / "build/workers/dos_experiment_anchor_v23"
PROVIDER = WORKER / "providers/experiment-anchor.c"
ROUTING = ROOT / "build/workers/dos_far_word_inventory_v23_plan/candidate-routing-v23.json"
OWNER_FLAGS = ["/AL", "/Os", "/Gs"]
CONSUMER_FLAGS = ["/AL", "/Os", "/Gs"]
TOKEN = "fd_50F6_09FC"
PUBLIC = "_fd_50f6_09fc"
ALIAS = "_ExperimentAnchorProbeAlias"
ALIAS_NORMALIZED = ALIAS.lower()
ALIAS_C = "ExperimentAnchorProbeAlias"
EXPECTED_DECLARATION = "int far fd_50F6_09FC[2];"

sys.path.insert(0, str(ROOT / "tools"))
import compiler  # noqa: E402
import modules  # noqa: E402
from omf import OmfReader  # noqa: E402


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def file_pin(path: Path) -> dict:
    raw = path.read_bytes()
    try:
        label = path.relative_to(ROOT).as_posix()
    except ValueError:
        label = str(path)
    return {"path": label, "sha256": sha(raw), "size": len(raw)}


def source_inventory() -> dict:
    manifest_path = ROOT / "layout/manifest.json"
    symbols_path = ROOT / "layout/symbols.json"
    behavior_path = ROOT / "evidence/behavior/manifest.json"
    strict_path = ROOT / "work/source-only-dos/static-completeness/index-v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    strict = json.loads(strict_path.read_text(encoding="utf-8"))
    if len(manifest["modules"]) != 127:
        raise RuntimeError("expected 127 canonical manifest modules")
    if len(strict.get("entries", {})) != 29:
        raise RuntimeError("expected 29 strict-effective entries")
    if file_pin(behavior_path)["sha256"] != strict["registry"]["sha256"]:
        raise RuntimeError("strict index references a different behavior registry")

    selected: dict[str, dict] = {}
    for module_key, row in manifest["modules"].items():
        path = ROOT / row["source"]
        actual = sha(path.read_bytes())
        if actual != row["source_sha256"]:
            raise RuntimeError(f"canonical source pin mismatch: {row['source']}")
        selected[row["source"]] = {
            "kind": "canonical", "module": module_key,
            "sha256": actual, "size": path.stat().st_size,
        }

    strict_sources = {}
    for name, row in strict["entries"].items():
        receipt_path = ROOT / row["path"]
        receipt_raw = receipt_path.read_bytes()
        if sha(receipt_raw) != row["sha256"]:
            raise RuntimeError(f"strict receipt pin mismatch: {name}")
        receipt = json.loads(receipt_raw.decode("utf-8"))
        if receipt.get("status") != "BEHAVIOR_EXACT_CONFIRMED":
            raise RuntimeError(f"strict receipt not confirmed: {name}")
        source = receipt.get("source_override") or receipt["registered_source"]
        path = ROOT / source["path"]
        actual = sha(path.read_bytes())
        if actual != source["sha256"]:
            raise RuntimeError(f"strict effective source pin mismatch: {name}")
        selected[source["path"]] = {
            "kind": "strict_effective", "entry": name,
            "sha256": actual, "size": path.stat().st_size,
            "receipt_path": row["path"], "receipt_sha256": row["sha256"],
        }
        strict_sources[name] = {
            "path": source["path"], "sha256": actual,
            "receipt_path": row["path"], "receipt_sha256": row["sha256"],
        }
    if len(selected) != 156:
        raise RuntimeError(f"expected 156 unique selected sources, found {len(selected)}")

    ident_re = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(TOKEN) + r"(?![A-Za-z0-9_])", re.I)
    numeric_re = re.compile(
        r"(?i)(?<![A-Za-z0-9_])(?:0x0*9fc|0*9fch)(?![A-Za-z0-9_])|"
        r"(?<![A-Za-z0-9_])50f6\s*:\s*0*9fc(?![A-Za-z0-9_])|"
        r"\[\s*0*9fc\s*\]"
    )
    refs, numeric, escapes = [], [], []
    for rel, meta in selected.items():
        path = ROOT / rel
        if path.suffix.lower() not in (".c", ".asm"):
            continue
        for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if ident_re.search(line):
                refs.append({"source": rel, "line": line_no, "text": line.strip(), "kind": meta["kind"]})
                if re.search(r"(?<!&)&(?!&)\s*" + re.escape(TOKEN), line, re.I):
                    escapes.append({"source": rel, "line": line_no, "text": line.strip()})
            if numeric_re.search(line):
                numeric.append({"source": rel, "line": line_no, "text": line.strip(), "kind": meta["kind"]})

    symbols = json.loads(symbols_path.read_text(encoding="utf-8"))["data"]
    target = symbols.get(TOKEN)
    if not target or target.get("seg") != 0x50F6 or target.get("off") != 0x09FC:
        raise RuntimeError("registered exact-base row changed")
    interior = [
        {"name": name, "offset": f"{row['off']:04X}", "grounding": row.get("grounding")}
        for name, row in symbols.items()
        if row.get("seg") == 0x50F6 and 0x09FC <= row.get("off", -1) < 0x0A00
    ]

    member = None
    routing = json.loads(ROUTING.read_text(encoding="utf-8"))
    for family in routing["families"]:
        for row in family["members"]:
            if row.get("name", "").lower() == TOKEN.lower():
                member = {"family": family["id"], **row}
                break
    if not member or member["typed_extent_bytes"] != 4 or member["source_declaration_conflict_flag"]:
        raise RuntimeError("candidate-routing-v23 lacks the expected clean four-byte typed proof")
    if len(refs) != 7 or escapes or numeric:
        raise RuntimeError(f"source reference census changed: refs={len(refs)} escapes={len(escapes)} numeric={len(numeric)}")
    if interior != [{"name": TOKEN, "offset": "09FC", "grounding": target.get("grounding")}]:
        raise RuntimeError(f"registered names inside 4-byte interval changed: {interior}")

    source_path = ROOT / "src/S22/m3BBD.c"
    lines = source_path.read_text(encoding="utf-8").splitlines()
    indexed = [
        {"line": n, "text": line.strip()}
        for n, line in enumerate(lines, 1) if ident_re.search(line)
    ]
    writes = [r for r in indexed if re.search(r"fd_50F6_09FC\s*\[\s*[01]\s*\]\s*=", r["text"])]
    reads = [r for r in indexed if re.search(r"fd_50F6_09FC\s*\[\s*[01]\s*\]", r["text"]) and r not in writes]
    if len(writes) != 4 or len(reads) != 3:
        # Includes declaration in indexed census; classify exact C reads below.
        c_reads = [r for r in reads if re.search(r"\b(?:DropWall|ExpDig)\s*\(", r["text"])]
        if len(writes) != 4 or len(c_reads) != 2:
            raise RuntimeError("processExp/DoTool lifecycle source lines changed")
    c_reads = [r for r in reads if re.search(r"\b(?:DropWall|ExpDig)\s*\(", r["text"])]
    process_writes = [r for r in writes if 1 <= r["line"] < 80]
    if len(process_writes) != 4 or len(c_reads) != 2:
        raise RuntimeError("expected four processExp slot writes and two DoTool reads")

    return {
        "schema": "simant-experiment-anchor-source-audit-v23",
        "scope": "127 canonical manifest sources plus all 29 confirmed strict-effective source paths; superseded experiments excluded",
        "source_count": len(selected),
        "selected_sources": selected,
        "strict_effective_sources": strict_sources,
        "source_pins": {
            "layout/manifest.json": file_pin(manifest_path),
            "layout/symbols.json": file_pin(symbols_path),
            "evidence/behavior/manifest.json": file_pin(behavior_path),
            "work/source-only-dos/static-completeness/index-v1.json": file_pin(strict_path),
            "build/workers/dos_far_word_inventory_v23_plan/candidate-routing-v23.json": file_pin(ROUTING),
        },
        "candidate": {
            "name": TOKEN, "registered_segment": "50F6", "registered_offset": "09FC",
            "declared_type": "int far[2]", "typed_extent_bytes": 4,
            "registered_names_within_extent": interior,
            "source_views": refs, "reference_count": len(refs),
            "numeric_address_spellings": numeric,
            "pointer_escapes": escapes,
            "save_record_rows": member.get("save_rec_rows", []),
            "save_record_or_pointer_table_escape": bool(escapes or member.get("save_rec_rows")),
            "routing_family": member["family"],
            "routing_proof_pin": file_pin(ROUTING),
            "processExp_slot_writes": process_writes,
            "DoTool_indexed_reads": c_reads,
            "explicit_source_startup_initialization": False,
            "lifecycle_scope": "source proves producer writes and consumer reads only; test CRT-zero startup is kept separate and does not claim historical game pre-main contents",
        },
    }


def compile_c(run_dir: Path, name: str, source: str) -> dict:
    fixture_dir = run_dir / "fixtures"
    src_path = fixture_dir / f"{name}.c"
    obj_path = fixture_dir / f"{name}.OBJ"
    src_path.write_bytes(source.encode("ascii"))
    result = compiler.compile_c(source, "msc600ax", OWNER_FLAGS, basename=name)
    if not result.ok or result.obj is None:
        raise RuntimeError(f"{name} compile failed:\n{result.log}")
    obj_path.write_bytes(result.obj)
    omf = OmfReader(communals=True).read(result.obj)
    return {
        "source": file_pin(src_path), "object": file_pin(obj_path), "object_bytes": result.obj,
        "flags": OWNER_FLAGS, "communals": list(omf.communals),
        "matching_communals": [r for r in omf.communals if r["name"].lower() == PUBLIC],
        "publics": list(omf.publics),
        "segments": [{k: r.get(k) for k in ("index", "name", "class", "length", "alignment", "combine", "big")} for r in omf.segment_defs],
    }


def positive_source() -> str:
    return f'''extern int far {TOKEN}[2];
extern int far {ALIAS_C}[2];
extern int far puts(char far *text);
int main(void)
{{
    unsigned char far *raw;
    if (sizeof({TOKEN}[0]) != 2 || sizeof({TOKEN}) != 4) {{ puts("REJECTED_SIZE"); return 0; }}
    if ((void far *)&{TOKEN}[0] != (void far *)&{ALIAS_C}[0]) {{ puts("REJECTED_BASE"); return 0; }}
    if ({TOKEN}[0] != 0 || {TOKEN}[1] != 0) {{ puts("REJECTED_CRT_ZERO"); return 0; }}
    {TOKEN}[0] = -1;
    {TOKEN}[1] = 0x2345;
    raw = (unsigned char far *)&{TOKEN}[0];
    if ({TOKEN}[0] != -1 || {TOKEN}[1] != 0x2345 ||
        raw[0] != 0xff || raw[1] != 0xff || raw[2] != 0x45 || raw[3] != 0x23) {{
        puts("REJECTED_TYPED_OR_BYTE_VIEW"); return 0;
    }}
    puts("PASS"); return 0;
}}
'''


def unsigned_source() -> str:
    return f'''extern unsigned int far {TOKEN}[2];
extern int far {ALIAS_C}[2];
extern int far puts(char far *text);
int main(void)
{{
    if ((void far *)&{TOKEN}[0] != (void far *)&{ALIAS_C}[0]) {{ puts("REJECTED_BASE"); return 0; }}
    {TOKEN}[0] = -1;
    if ({TOKEN}[0] < 0) {{ puts("FAIL_UNEXPECTED_SIGNED"); return 0; }}
    puts("REJECTED_UNSIGNED_VIEW"); return 0;
}}
'''


def address(row: dict) -> tuple[int, int]:
    return int(row["segment"], 16), int(row["offset"], 16)


def address_text(row: dict) -> str:
    s, o = address(row)
    return f"{s:04X}:{o:04X}"


def parse_sections(text: str) -> dict:
    result = {"Name": {}, "Value": {}}
    section = None
    pattern = re.compile(r"\s*([0-9A-Fa-f]{4}):([0-9A-Fa-f]{4})\s+(Res|Ovl|U)\s+(_\S+)")
    for line in text.splitlines():
        if "Publics by Name" in line:
            section = "Name"
            continue
        if "Publics by Value" in line:
            section = "Value"
            continue
        match = pattern.match(line)
        if section and match:
            name = match.group(4).lower()
            result[section].setdefault(name, []).append({
                "segment": match.group(1), "offset": match.group(2), "state": match.group(3),
            })
    return result


def runtime_case(run_dir: Path, profile: str, spec: dict, owner_obj: bytes,
                 consumer_obj: bytes, runtime_rows: list[dict], linker: dict,
                 runner: dict, tool_dir: Path) -> dict:
    case_dir = run_dir / "rtlink" / profile / spec["case"]
    case_dir.mkdir(parents=True, exist_ok=False)
    (case_dir / "CRT.OBJ").write_bytes(consumer_obj)
    (case_dir / "OWNER.OBJ").write_bytes(owner_obj)
    for row in runtime_rows:
        shutil.copyfile(row["path"], case_dir / Path(row["path"]).name.upper())

    delta = spec.get("alias_delta", 0)
    offset = f" + {delta:X}" if delta else ""
    link = ("OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n"
            "LIBRARY LLIBCR, LIBH\r\nFILE CRT\r\nBEGINAREA\r\n"
            "SECTION FILE OWNER\r\nENDAREA\r\n"
            f"DEFINE {ALIAS} = {PUBLIC}{offset}\r\n")
    (case_dir / "PROBE.LNK").write_bytes(link.encode("ascii"))
    (case_dir / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (case_dir / "RUN.BAT").write_bytes(
        (f"@echo off\r\nD:\\{linker['executable']} @PROBE.LNK < NUL > LINK.LOG\r\n"
         "PROBE.EXE > RUN.LOG\r\n").encode("ascii"))
    conf = []
    for section, settings in runner["conf"].items():
        conf.append("[" + section + "]")
        conf.extend(f"{key}={value}" for key, value in settings.items())
    conf += ["[autoexec]", f'mount c "{case_dir}"', f'mount d "{tool_dir}" -ro',
             "c:", "call RUN.BAT", "exit"]
    conf_path = case_dir / "dosbox.conf"
    conf_path.write_text("\n".join(conf) + "\n", encoding="ascii")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    timed_out = False
    try:
        proc = subprocess.run(
            [runner["path"], "-conf", str(conf_path), "-fastlaunch", "-exit", "-nomenu"],
            cwd=case_dir, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            timeout=60, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        host_bytes, host_return = proc.stdout, proc.returncode
    except subprocess.TimeoutExpired as error:
        timed_out = True
        host_bytes, host_return = (error.stdout or b"") + (error.stderr or b""), -1
    (case_dir / "DOSBOX-HOST.LOG").write_bytes(host_bytes)
    run_path, link_path, map_path = case_dir / "RUN.LOG", case_dir / "LINK.LOG", case_dir / "PROBE.MAP"
    run_bytes = run_path.read_bytes() if run_path.exists() else b""
    run_text = run_bytes.decode("latin1").strip()
    link_text = link_path.read_text(encoding="latin1", errors="replace") if link_path.exists() else ""
    map_text = map_path.read_text(encoding="latin1", errors="replace") if map_path.exists() else ""
    sections = parse_sections(map_text)
    missing = {}
    matrix = {}
    alias_relations = []
    map_ok = True
    for section in ("Name", "Value"):
        rows = sections[section]
        missing[section] = [s for s in (PUBLIC, ALIAS_NORMALIZED) if len(rows.get(s, [])) != 1]
        if missing[section]:
            map_ok = False
            continue
        target, alias = rows[PUBLIC][0], rows[ALIAS_NORMALIZED][0]
        same_seg = target["segment"] == alias["segment"]
        delta_actual = int(alias["offset"], 16) - int(target["offset"], 16) if same_seg else None
        relation_pass = same_seg and delta_actual == delta and target["state"] == alias["state"] == "Res"
        map_ok = map_ok and relation_pass
        matrix[section] = {PUBLIC: address_text(target), ALIAS_NORMALIZED: address_text(alias)}
        alias_relations.append({
            "section": section, "target": PUBLIC, "alias": ALIAS_NORMALIZED,
            "expected_offset_delta": delta, "actual_offset_delta": delta_actual,
            "target_address": address_text(target), "alias_address": address_text(alias),
            "same_segment": same_seg, "both_resident": target["state"] == alias["state"] == "Res",
            "passed": relation_pass,
            "claim_limit": "test-owned relative alias only; no historical absolute placement or adjacency claim",
        })
    diagnostics = re.findall(r"(?im)^.*(?:warning\s+wrt|undefined symbol|error\s+wrt).*$", link_text)
    clean = not diagnostics and bool(link_text)
    expected = spec["expected_output"]
    passed = (run_text == expected and host_return == 0 and not timed_out and
              (case_dir / "PROBE.EXE").exists() and clean and map_ok)
    files = [file_pin(p) for p in sorted(case_dir.iterdir()) if p.is_file()]
    return {
        "linker": profile, "case": spec["case"], "expected": expected, "actual": run_text,
        "passed": passed, "timed_out": timed_out, "runner_returncode": host_return,
        "linker_diagnostics": diagnostics, "linker_produced_executable": (case_dir / "PROBE.EXE").exists(),
        "linker_produced_map": map_path.exists(), "expected_owner_publics": [PUBLIC],
        "owner_publics_found_in_map": [PUBLIC] if map_ok else [],
        "map_public_sections": {
            s: {"heading_present": "Publics by " + s in map_text,
                "missing_required_publics": missing[s]} for s in ("Name", "Value")},
        "public_address_matrix": matrix, "alias_map_relations": alias_relations,
        "expected_marker_verbatim": (expected + "\r\n"),
        "actual_marker_verbatim": run_bytes.decode("latin1"),
        "actual_marker_bytes_hex": run_bytes.hex(), "actual_marker_sha256": sha(run_bytes),
        "run_log_pin": file_pin(run_path) if run_path.exists() else None,
        "link_log_pin": file_pin(link_path) if link_path.exists() else None,
        "map_input_pin": file_pin(map_path) if map_path.exists() else None,
        "raw_case_artifact_pins": files,
        "claim_limit": "test-owned CRT/runtime and relative alias fixture; no historical object ownership, initialization, placement, or adjacency claim",
    }


def main() -> int:
    provider_text = PROVIDER.read_text(encoding="ascii")
    if len(re.findall(r"(?m)^\s*int\s+far\s+fd_50F6_09FC\[2\]\s*;\s*$", provider_text)) != 1:
        raise RuntimeError("provider must be exactly one natural int far[2] data definition")
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"run-{stamp}-{uuid.uuid4().hex[:12]}"
    run_dir = WORKER / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "fixtures").mkdir()

    audit = source_inventory()
    audit_path = run_dir / "source-audit.json"
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    toolchain = compiler.toolchain()
    compiler_profile = toolchain["profiles"]["msc600ax"]
    runner = toolchain["runners"]["dosbox-x"]
    manifest = modules.load_manifest()
    runtime_rows = list(manifest["runtime"]["libraries"].values())
    for row in runtime_rows:
        if sha(Path(row["path"]).read_bytes()) != row["sha256"]:
            raise RuntimeError(f"pinned runtime library hash mismatch: {row['path']}")

    fixtures = {
        "OWNER": compile_c(run_dir, "OWNER", provider_text),
        "SHORT_INT_1": compile_c(run_dir, "SHORT", "int far fd_50F6_09FC[1];\n"),
        "BYTE_4": compile_c(run_dir, "BYTE", "unsigned char far fd_50F6_09FC[4];\n"),
        "LONG_2": compile_c(run_dir, "LONGS", "long far fd_50F6_09FC[2];\n"),
        "UNSIGNED_2": compile_c(run_dir, "UNSIGNED", "unsigned int far fd_50F6_09FC[2];\n"),
        "INITIALIZED": compile_c(run_dir, "INIT", "int far fd_50F6_09FC[2] = { 0x1357, 0x2468 };\n"),
        "CRTGOOD": compile_c(run_dir, "CRTGOOD", positive_source()),
        "CRTSIGNED": compile_c(run_dir, "CRTSIGN", unsigned_source()),
    }

    def one_common(name: str):
        rows = fixtures[name]["matching_communals"]
        return rows[0] if len(rows) == 1 else None

    expected_common = one_common("OWNER")
    short_common = one_common("SHORT_INT_1")
    byte_common = one_common("BYTE_4")
    long_common = one_common("LONG_2")
    unsigned_common = one_common("UNSIGNED_2")
    initialized_common = one_common("INITIALIZED")
    if not expected_common or (expected_common["count"], expected_common["element_size"], expected_common["length"]) != (2, 2, 4):
        raise RuntimeError(f"natural int far[2] expected 2x2/4-byte common, observed {expected_common}")
    if not short_common or (short_common["count"], short_common["element_size"], short_common["length"]) != (1, 2, 2):
        raise RuntimeError(f"int far[1] OMF control mismatch: {short_common}")
    if not byte_common or (byte_common["count"], byte_common["element_size"], byte_common["length"]) != (4, 1, 4):
        raise RuntimeError(f"unsigned char far[4] OMF control mismatch: {byte_common}")
    if not long_common or (long_common["count"], long_common["element_size"], long_common["length"]) != (2, 4, 8):
        raise RuntimeError(f"long far[2] OMF control mismatch: {long_common}")
    if not unsigned_common or (unsigned_common["count"], unsigned_common["element_size"], unsigned_common["length"]) != (2, 2, 4):
        raise RuntimeError(f"unsigned int far[2] OMF contrast mismatch: {unsigned_common}")
    if initialized_common is not None:
        raise RuntimeError("initialized owner unexpectedly remained a far common")

    cases = [
        {"case": "positive_crt_zero_all_slots_typed_and_byte_views", "owner": "OWNER", "consumer": "CRTGOOD", "expected_output": "PASS", "alias_delta": 0},
        {"case": "wrong_test_base_plus_two_bytes", "owner": "OWNER", "consumer": "CRTGOOD", "expected_output": "REJECTED_BASE", "alias_delta": 2},
        {"case": "wrong_initialized_data_owner", "owner": "INITIALIZED", "consumer": "CRTGOOD", "expected_output": "REJECTED_CRT_ZERO", "alias_delta": 0},
        {"case": "wrong_unsigned_consumer_view", "owner": "OWNER", "consumer": "CRTSIGNED", "expected_output": "REJECTED_UNSIGNED_VIEW", "alias_delta": 0},
    ]
    runtime_results = []
    for profile in ("rtlink400", "rtlink610"):
        linker = toolchain["linkers"][profile]
        tool_dir = compiler.pinned_tree(linker)
        for spec in cases:
            runtime_results.append(runtime_case(
                run_dir, profile, spec, fixtures[spec["owner"]]["object_bytes"],
                fixtures[spec["consumer"]]["object_bytes"], runtime_rows, linker, runner, tool_dir))
    if len(runtime_results) != 8 or not all(row["passed"] for row in runtime_results):
        failed = [{k: row.get(k) for k in ("linker", "case", "actual", "passed", "runner_returncode",
                                            "timed_out", "linker_diagnostics", "linker_produced_executable",
                                            "linker_produced_map", "map_public_sections", "public_address_matrix",
                                            "alias_map_relations")} for row in runtime_results if not row["passed"]]
        raise RuntimeError("fresh two-linker runtime case matrix did not pass: " + json.dumps(failed))

    helper_paths = [ROOT / "tools/compiler.py", ROOT / "tools/modules.py", ROOT / "tools/omf.py",
                    ROOT / "layout/toolchain.json", ROOT / "layout/manifest.json"]
    profile_dir = Path(compiler_profile["directory"])
    profile_files = []
    for rel, expected_hash in compiler_profile.get("files", {}).items():
        path = profile_dir / rel
        pin = file_pin(path)
        if pin["sha256"] != expected_hash:
            raise RuntimeError(f"compiler profile input pin mismatch: {path}")
        profile_files.append(pin)
    for rel, expected_hash in compiler_profile.get("include_files", {}).items():
        path = Path(compiler_profile["include_directory"]) / rel
        pin = file_pin(path)
        if pin["sha256"] != expected_hash:
            raise RuntimeError(f"compiler profile input pin mismatch: {path}")
        profile_files.append(pin)
    linker_pins = {}
    for name in ("rtlink400", "rtlink610"):
        linker = toolchain["linkers"][name]
        pins = []
        linker_dir = Path(linker["directory"])
        for rel, expected_hash in linker.get("files", {}).items():
            path = linker_dir / rel
            pin = file_pin(path)
            if pin["sha256"] != expected_hash:
                raise RuntimeError(f"linker input pin mismatch: {path}")
            pins.append(pin)
        linker_pins[name] = pins
    runtime_toolchain = {
        "compiler_profile": {"name": "msc600ax", "product": compiler_profile.get("product"),
                             "directory": compiler_profile.get("directory"), "flags": OWNER_FLAGS,
                             "profile_files": profile_files,
                             "include_files": compiler_profile.get("include_files", [])},
        "compiler_and_probe_helpers": [file_pin(p) for p in helper_paths],
        "runner": {"path": runner["path"], "sha256": runner["sha256"], "conf": runner.get("conf")},
        "linkers": linker_pins,
        "runtime_libraries": [{**row, "actual_sha256": sha(Path(row["path"]).read_bytes())} for row in runtime_rows],
    }

    receipt = {
        "schema": "simant-experiment-anchor-storage-probe-v23",
        "status": "SCRATCH_ONLY_UNADMITTED_NO_PROMOTION",
        "root_reviewed": False,
        "run_id": run_id,
        "source_audit": file_pin(audit_path),
        "candidate_routing": file_pin(ROUTING),
        "provider": {**file_pin(PROVIDER), "declaration": EXPECTED_DECLARATION,
                     "compiler_profile": "msc600ax", "flags": OWNER_FLAGS,
                     "omf_common": expected_common,
                     "historical_owner_tu_or_order_claimed": False,
                     "historical_absolute_layout_claimed": False,
                     "original_initializer_claimed": False},
        "omf_controls": {
            "int_far_1": {"common": short_common, "expected_source_rejection": True,
                          "runtime_attempted": False, "reason": "two-byte extent control only; no short-object overrun is tested"},
            "unsigned_char_far_4": {"common": byte_common, "expected_source_rejection": True,
                                    "runtime_attempted": False, "reason": "same byte length but wrong element width/count"},
            "long_far_2": {"common": long_common, "expected_source_rejection": True,
                           "runtime_attempted": False, "reason": "two four-byte longs yield an eight-byte common"},
            "unsigned_int_far_2": {"common": unsigned_common, "expected_source_rejection": True,
                                   "runtime_abi_distinguishable": False,
                                   "reason": "OMF does not encode signedness; source pins int and a runtime consumer view supplies the type contrast"},
            "initialized_int_far_2": {"commons": fixtures["INITIALIZED"]["communals"],
                                      "publics": fixtures["INITIALIZED"]["publics"],
                                      "segments": fixtures["INITIALIZED"]["segments"],
                                      "expected_source_rejection": True,
                                      "reason": "initialized FAR_DATA replaces uninitialized common"},
        },
        "compiled_fixture_inputs": {
            name: {"source": item["source"], "object": item["object"], "flags": item["flags"],
                   "matching_communals": item["matching_communals"], "publics": item["publics"], "segments": item["segments"]}
            for name, item in fixtures.items()
        },
        "runtime_cases": runtime_results,
        "case_summary": {"required_cases": 8, "passed_cases": sum(r["passed"] for r in runtime_results),
                         "all_required_cases_passed": all(r["passed"] for r in runtime_results)},
        "lifecycle_limit": audit["candidate"]["lifecycle_scope"],
        "toolchain": runtime_toolchain,
        "input_policy": "Selected canonical and strict-effective sources, registries, tool metadata, pinned MSC/RTLink/CRT inputs, candidate and test fixtures only; no original executable/build input or original data bytes.",
        "receipt_files": [file_pin(PROVIDER), file_pin(Path(__file__)), file_pin(ROUTING), file_pin(audit_path)],
    }
    receipt_path = run_dir / "candidate-receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    candidate = {
        "schema": "simant-experiment-anchor-owner-candidate-v23",
        "category": "CANDIDATE_SOURCE_FUNCTIONAL_STORAGE",
        "status": "PARENT_REVIEW_PENDING_UNADMITTED",
        "root_reviewed": False,
        "admitted": False,
        "module": "source-owned:experiment-anchor-pair",
        "provider": {"path": PROVIDER.relative_to(ROOT).as_posix(),
                     "sha256": file_pin(PROVIDER)["sha256"], "basename": "EXPANCHR", "owner": None,
                     "compiler_profile": "msc600ax", "flags": OWNER_FLAGS,
                     "declaration": EXPECTED_DECLARATION,
                     "communal": {"name": "_fd_50F6_09FC", "kind": "far", "count": 2,
                                  "element_size": 2, "length": 4},
                     "historical_tu_order_or_absolute_placement_claimed": False,
                     "original_initializer_claimed": False},
        "source_proof": {"path": audit_path.relative_to(ROOT).as_posix(), "sha256": file_pin(audit_path)["sha256"],
                         "source_count": audit["source_count"], "reference_count": audit["candidate"]["reference_count"],
                         "pointer_escapes": audit["candidate"]["pointer_escapes"],
                         "numeric_address_spellings": audit["candidate"]["numeric_address_spellings"],
                         "registered_names_within_extent": audit["candidate"]["registered_names_within_extent"],
                         "routing_proof": file_pin(ROUTING)},
        "runtime_receipt": {"path": receipt_path.relative_to(ROOT).as_posix(), "sha256": sha(receipt_path.read_bytes()),
                            "run_id": run_id, "case_count": 8, "passed_case_count": 8,
                            "linkers": ["rtlink400", "rtlink610"]},
        "lifecycle_limit": "processExp source writes both int slots; DoTool reads both slots. No source-level startup default/reset was found. Fresh CRT-zero fixture verifies test startup only and does not claim original pre-main or historical game-owner values.",
        "limits": [
            "No historical COMDEF owner TU/order, absolute placement, or original initializer is claimed.",
            "The source has no explicit startup reset/default for this pair; fresh CRT-zero behavior is only a candidate-runtime control.",
            "No short-extent out-of-bounds access or adjacency-based extent inference is used.",
        ],
    }
    candidate_path = WORKER / "candidate-v23.json"
    candidate_path.write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = {"run": run_dir.relative_to(ROOT).as_posix(),
               "candidate": candidate_path.relative_to(ROOT).as_posix(),
               "receipt": receipt_path.relative_to(ROOT).as_posix(),
               "source_count": audit["source_count"], "reference_count": audit["candidate"]["reference_count"],
               "all_runtime_pass": receipt["case_summary"]["all_required_cases_passed"],
               "cases": [(r["linker"], r["case"], r["actual"], r["passed"]) for r in runtime_results]}
    print(json.dumps(summary, indent=2))
    return 0 if summary["all_runtime_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
