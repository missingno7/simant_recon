"""Focused OMF/RTLink source-owner proof for the four mode-population vectors.

This is scratch evidence only. It selects names from the v23 report snapshot and
derives ownership from the complete pinned static source graph; it does not edit
canonical sources, build bindings, or the promotion journal.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
import compiler  # noqa: E402
import modules  # noqa: E402
from omf import OmfReader  # noqa: E402

IMPORTS = {
    "fd_50F6_0B12": {"type": "signed int[6]", "bytes": 12},
    "fd_50F6_0C2A": {"type": "signed int[6]", "bytes": 12},
    "fd_50F6_0D40": {"type": "signed int[20]", "bytes": 40},
    "fd_50F6_0D72": {"type": "signed int[20]", "bytes": 40},
}
NAMES = list(IMPORTS)
FAILURES = {
    "FAIL_STARTUP_NOT_ZERO", "FAIL_SAVE_REC_SHAPE", "FAIL_SAVE_REC_BASE",
    "FAIL_ALIAS_GEOMETRY", "FAIL_TYPED_RAW_VIEW", "FAIL_TYPED_VECTOR",
    "FAIL_GUARD_WITNESS",
}
DOS_BASES = {
    "mode_population_owner": "MPVOWNR",
    "runtime_positive": "MPVPOS",
    "runtime_wrong_type_consumer": "MPVWTCNS",
    "runtime_wrong_extent_consumer": "MPVWECNS",
    "runtime_wrong_b12_base_consumer": "MPWB12CS",
    "runtime_wrong_c2a_base_consumer": "MPWC2ACS",
    "control_short_extent": "CTL5WORD",
    "control_wrong_element_width": "CTLBYTE",
    "control_unsigned_element": "CTLUNSGN",
    "control_initialized_storage": "CTLINIT",
    "control_signed_comparison": "CTLSIGN",
    "control_unsigned_comparison": "CTLUNSG2",
    "runtime_wrong_type_owner": "MPVWTO",
    "runtime_wrong_extent_owner": "MPVWEO",
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def hash_file(path: Path) -> dict:
    raw = path.read_bytes()
    return {"path": str(path), "sha256": sha(raw), "size": len(raw)}


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def compile_source(run_root: Path, key: str, body: str, flags: list[str]) -> dict:
    src_path = run_root / "sources" / f"{key}.c"
    src_path.parent.mkdir(parents=True, exist_ok=True)
    src_path.write_text(body, encoding="ascii", newline="\n")
    result = compiler.compile_c(body, "msc600ax", flags, basename=DOS_BASES[key])
    log_path = run_root / "compiler-logs" / f"{key}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_bytes(result.log.encode("latin1", "replace"))
    if not result.ok or result.obj is None:
        raise RuntimeError(f"{key}: MSC compile failed; see {log_path}:\n{result.log}")
    obj_path = run_root / "objects" / f"{key}.OBJ"
    obj_path.parent.mkdir(parents=True, exist_ok=True)
    obj_path.write_bytes(result.obj)
    omf = OmfReader(communals=True).read(result.obj)
    return {
        "key": key,
        "source": str(src_path.relative_to(run_root)),
        "source_sha256": sha(src_path.read_bytes()),
        "object": str(obj_path.relative_to(run_root)),
        "object_sha256": sha(result.obj),
        "object_size": len(result.obj),
        "compile_log": str(log_path.relative_to(run_root)),
        "compile_log_sha256": sha(log_path.read_bytes()),
        "communals": list(omf.communals),
        "segments": [{k: d.get(k) for k in ("index", "name", "class", "length", "alignment", "combine", "big")}
                     for d in omf.segment_defs],
        "publics": list(omf.publics),
        "linker_fixups": list(omf.linker_fixups),
        "external_scopes": [{"name": n, "scope": s} for n, s in zip(omf.externals, omf.external_scopes)],
        "segment_bytes": {n: b.hex() for n, b in omf.segments.items()},
        "_object_bytes": result.obj,
        "_omf": omf,
    }


def arrays_owner(b12: str = "int far fd_50F6_0B12[6];", initialized: bool = False) -> str:
    b12_decl = ("int far fd_50F6_0B12[6] = { 1 };" if initialized else b12)
    return "\n".join([
        b12_decl,
        "int far fd_50F6_0C2A[6];",
        "int far fd_50F6_0D40[20];",
        "int far fd_50F6_0D72[20];",
    ]) + "\n"


def runtime_consumer(case: str) -> str:
    b12_target = "SaveB12Alias" if case == "wrong_base_b12" else "fd_50F6_0B12"
    c2a_target = "SaveC2AAlias" if case == "wrong_base_c2a" else "fd_50F6_0C2A"
    save_rows = f'''struct SaveRec far SaveRows[2] = {{
    {{ 2, 6, (void far *)&{b12_target}[0] }},
    {{ 2, 6, (void far *)&{c2a_target}[0] }}
}};'''
    if case == "wrong_element_type":
        pre_tally = '''SeedWrongElement();
    for (i = 0; i < 6; i++) {
        if (fd_50F6_0B12[i] != 0x0100 + i) {
            puts("REJECTED_WRONG_ELEMENT_TYPE"); return 0;
        }
    }
    puts("FAIL_TYPED_VECTOR"); return 0;'''
    elif case == "wrong_extent":
        pre_tally = '''if (ModePopulationGuardWasWritten()) {
        puts("FAIL_GUARD_WITNESS"); return 0;
    }
    fd_50F6_0B12[5] = 0x3579;
    if (!ModePopulationGuardWasWritten()) {
        puts("FAIL_GUARD_WITNESS"); return 0;
    }
    puts("REJECTED_SIXTH_WORD_HITS_DECLARED_GUARD"); return 0;'''
    elif case in ("wrong_base_b12", "wrong_base_c2a"):
        target = "0B12" if case == "wrong_base_b12" else "0C2A"
        pre_tally = f'''if (SaveRows[{0 if case == 'wrong_base_b12' else 1}].data ==
        (void far *)&fd_50F6_{target}[0]) {{
        puts("FAIL_ALIAS_GEOMETRY"); return 0;
    }}
    puts("REJECTED_WRONG_BASE_{target}"); return 0;'''
    else:
        pre_tally = '''/* Raw SaveRec bytes must alias typed int elements at both six-word bases. */
    b12[0] = 0x34; b12[1] = 0x12;
    b12[10] = 0x68; b12[11] = 0x24;
    c2a[0] = 0x78; c2a[1] = 0x56;
    c2a[10] = 0xbc; c2a[11] = 0x6a;
    if (fd_50F6_0B12[0] != 0x1234 || fd_50F6_0B12[5] != 0x2468 ||
        fd_50F6_0C2A[0] != 0x5678 || fd_50F6_0C2A[5] != 0x6abc ||
        b12[10] != 0x68 || b12[11] != 0x24 ||
        c2a[10] != 0xbc || c2a[11] != 0x6a) {
        puts("FAIL_TYPED_RAW_VIEW"); return 0;
    }
    fd_50F6_0B12[1] = -2;
    fd_50F6_0C2A[4] = -2;
    if (b12[2] != 0xfe || b12[3] != 0xff || c2a[8] != 0xfe || c2a[9] != 0xff) {
        puts("FAIL_TYPED_RAW_VIEW"); return 0;
    }
    fd_50F6_0D40[0] = -1; fd_50F6_0D40[10] = 0x4567; fd_50F6_0D40[19] = 0x5678;
    fd_50F6_0D72[0] = 0x6789; fd_50F6_0D72[10] = -2; fd_50F6_0D72[19] = 0x1234;
    if (fd_50F6_0D40[0] != -1 || fd_50F6_0D40[10] != 0x4567 ||
        fd_50F6_0D40[19] != 0x5678 || fd_50F6_0D72[0] != 0x6789 ||
        fd_50F6_0D72[10] != -2 || fd_50F6_0D72[19] != 0x1234) {
        puts("FAIL_TYPED_VECTOR"); return 0;
    }
    puts("PASS_MODE_POPULATION_TYPED_RAW_SAVE_REC_STARTUP_ZERO"); return 0;'''
    return f'''extern int far fd_50F6_0B12[6];
extern int far fd_50F6_0C2A[6];
extern int far fd_50F6_0D40[20];
extern int far fd_50F6_0D72[20];
extern int far SaveB12Alias[6];
extern int far SaveC2AAlias[6];
extern int far puts(char far *text);
extern int far ModePopulationGuardWasWritten(void);
extern void far SeedWrongElement(void);
struct SaveRec {{ int size; int count; void far *data; }};
{save_rows}
int main(void)
{{
    int i;
    unsigned char far *b12;
    unsigned char far *c2a;
    if (SaveRows[0].size != 2 || SaveRows[0].count != 6 ||
        SaveRows[1].size != 2 || SaveRows[1].count != 6) {{
        puts("FAIL_SAVE_REC_SHAPE"); return 0;
    }}
    if (SaveRows[0].data != (void far *)&SaveB12Alias[0] ||
        SaveRows[1].data != (void far *)&SaveC2AAlias[0]) {{
        puts("FAIL_SAVE_REC_BASE"); return 0;
    }}
    b12 = (unsigned char far *)SaveRows[0].data;
    c2a = (unsigned char far *)SaveRows[1].data;
    for (i = 0; i < 6; i++)
        if (fd_50F6_0B12[i] != 0 || fd_50F6_0C2A[i] != 0) {{
            puts("FAIL_STARTUP_NOT_ZERO"); return 0;
        }}
    for (i = 0; i < 20; i++)
        if (fd_50F6_0D40[i] != 0 || fd_50F6_0D72[i] != 0) {{
            puts("FAIL_STARTUP_NOT_ZERO"); return 0;
        }}
    {pre_tally}
}}
'''


def short_extent_owner() -> str:
    return '''struct ModePopulationShortBlock { int words[5]; int guard; };
struct ModePopulationShortBlock far fd_50F6_0B12;
int far fd_50F6_0C2A[6];
int far fd_50F6_0D40[20];
int far fd_50F6_0D72[20];
int far ModePopulationGuardWasWritten(void)
{ return fd_50F6_0B12.guard == 0x3579; }
'''


def wrong_element_owner() -> str:
    return '''unsigned char far fd_50F6_0B12[12];
int far fd_50F6_0C2A[6];
int far fd_50F6_0D40[20];
int far fd_50F6_0D72[20];
void far SeedWrongElement(void)
{
    int i;
    for (i = 0; i < 12; i++) fd_50F6_0B12[i] = i + 1;
}
'''


def initialized_owner() -> str:
    return '''int far fd_50F6_0B12[6] = { 1 };
int far fd_50F6_0C2A[6];
int far fd_50F6_0D40[20];
int far fd_50F6_0D72[20];
'''


def signedness_source(unsigned: bool) -> str:
    type_name = "unsigned int" if unsigned else "int"
    return f'''extern {type_name} far fd_50F6_0B12[6];
int far ModePopulationSignProbe(void)
{{ return fd_50F6_0B12[0] < 0; }}
'''


def map_sections(map_raw: bytes) -> tuple[dict[str, list[dict]], list[dict], list[dict]]:
    text = map_raw.decode("latin1", "replace")
    names: dict[str, list[dict]] = {"name": [], "value": []}
    section = None
    row_re = re.compile(r"^\s*([0-9A-Fa-f]{4}):([0-9A-Fa-f]{4})\s+(Res|Ovl|U|Abs)\s+(\S+)\s*$")
    for line in text.splitlines():
        if "Publics by Name" in line:
            section = "name"
            continue
        if "Publics by Value" in line:
            section = "value"
            continue
        if line.strip().startswith(("Start  Stop", "Origin", "Section#")):
            section = None
        if section:
            m = row_re.match(line)
            if m:
                names[section].append({"segment": int(m.group(1), 16), "offset": int(m.group(2), 16),
                                       "state": m.group(3), "name": m.group(4), "raw": line.rstrip()})
    seg_re = re.compile(r"^\s*([0-9A-Fa-f]+)H\s+([0-9A-Fa-f]+)H\s+([0-9A-Fa-f]+)H\s+(\S+)\s+(\S+)")
    far_bss = []
    for line in text.splitlines():
        m = seg_re.match(line)
        if m and m.group(5) == "FAR_BSS":
            start, end, size = (int(m.group(i), 16) for i in (1, 2, 3))
            far_bss.append({"start_linear": start, "end_linear": end, "length": size,
                            "frame_segment": start >> 4, "name": m.group(4), "class": m.group(5), "raw": line.rstrip()})
    return names, far_bss, [{"line": x} for x in text.splitlines()
                            if re.search(r"\b(?:warning|fatal error|error code)\b", x, re.I)]


def run_link_case(run_root: Path, case: str, owner: dict, consumer: dict, owner_body: str,
                  case_expectation: dict, profile: str, manifest: dict, tc: dict) -> dict:
    linker = tc["linkers"][profile]
    runner = tc["runners"]["dosbox-x"]
    tool_dir = compiler.pinned_tree(linker)
    case_dir = run_root / "rtlink" / profile / case
    if case_dir.exists():
        raise RuntimeError(f"case directory exists; refusing to overwrite: {case_dir}")
    case_dir.mkdir(parents=True)
    (case_dir / "OWNER.OBJ").write_bytes(owner["_object_bytes"])
    (case_dir / "CRT.OBJ").write_bytes(consumer["_object_bytes"])
    copied_runtime = []
    for row in manifest["runtime"]["libraries"].values():
        lib = Path(row["path"])
        if not lib.is_file() or sha(lib.read_bytes()) != row["sha256"]:
            raise RuntimeError(f"runtime library pin mismatch: {lib}")
        dst = case_dir / lib.name.upper()
        shutil.copyfile(lib, dst)
        copied_runtime.append({"source": str(lib), "destination": dst.name, "sha256": sha(dst.read_bytes()), "size": dst.stat().st_size})
    alias_b12 = case_expectation.get("b12_alias_delta", 0)
    alias_c2a = case_expectation.get("c2a_alias_delta", 0)
    b12_expr = f"_fd_50F6_0B12 + {alias_b12:X}" if alias_b12 else "_fd_50F6_0B12"
    c2a_expr = f"_fd_50F6_0C2A + {alias_c2a:X}" if alias_c2a else "_fd_50F6_0C2A"
    link_text = ("OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n"
                 "LIBRARY LLIBCR, LIBH\r\nFILE CRT\r\nBEGINAREA\r\nSECTION FILE OWNER\r\nENDAREA\r\n"
                 f"DEFINE _SaveB12Alias = {b12_expr}\r\n"
                 f"DEFINE _SaveC2AAlias = {c2a_expr}\r\n")
    (case_dir / "PROBE.LNK").write_bytes(link_text.encode("ascii"))
    (case_dir / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    batch = (f"@echo off\r\nD:\\{linker['executable']} @PROBE.LNK < NUL > LINK.LOG\r\n"
             "PROBE.EXE > RUN.LOG\r\n")
    (case_dir / "RUN.BAT").write_bytes(batch.encode("ascii"))
    conf_lines = []
    for section, opts in runner["conf"].items():
        conf_lines.append("[" + section + "]")
        conf_lines.extend(f"{k}={v}" for k, v in opts.items())
    conf_lines.extend(["[autoexec]", f'mount c "{case_dir}"', f'mount d "{tool_dir}" -ro',
                       "c:", "call RUN.BAT", "exit"])
    (case_dir / "dosbox.conf").write_text("\n".join(conf_lines) + "\n", encoding="ascii")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    argv = [runner["path"], "-conf", str(case_dir / "dosbox.conf"), "-fastlaunch", "-exit", "-nomenu"]
    timed_out = False
    try:
        process = subprocess.run(argv, cwd=case_dir, env=env, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, timeout=90,
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        host_output = process.stdout
        return_code = process.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        host_output = exc.stdout or b""
        return_code = -1
    (case_dir / "DOSBOX-HOST.LOG").write_bytes(host_output)
    link_raw = (case_dir / "LINK.LOG").read_bytes() if (case_dir / "LINK.LOG").exists() else b""
    run_raw = (case_dir / "RUN.LOG").read_bytes() if (case_dir / "RUN.LOG").exists() else b""
    map_raw = (case_dir / "PROBE.MAP").read_bytes() if (case_dir / "PROBE.MAP").exists() else b""
    map_sections_data, far_bss, map_warnings = map_sections(map_raw)
    expected_marker = case_expectation["expected_marker"].encode("ascii")
    run_lines = run_raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n").split(b"\n")
    marker_lines = [line for line in run_lines if line == expected_marker]
    failure_lines = [line.decode("latin1") for line in run_lines if any(x.encode("ascii") in line for x in FAILURES)]
    exact_symbols = ["_fd_50F6_0B12", "_fd_50F6_0C2A", "_fd_50F6_0D40", "_fd_50F6_0D72",
                     "_SaveB12Alias", "_SaveC2AAlias"]
    filtered = {}
    for sect, rows in map_sections_data.items():
        filtered[sect] = {symbol: [r for r in rows if r["name"] == symbol] for symbol in exact_symbols}
    by_name_rows = {s: filtered["name"].get(s, []) for s in exact_symbols}
    exact_publics = all(len(by_name_rows[s]) == 1 and by_name_rows[s][0]["state"] == "Res" for s in exact_symbols)
    alias_geometry = {}
    for exact, alias, delta in (("_fd_50F6_0B12", "_SaveB12Alias", alias_b12),
                                ("_fd_50F6_0C2A", "_SaveC2AAlias", alias_c2a)):
        b = by_name_rows.get(exact, [])
        a = by_name_rows.get(alias, [])
        alias_geometry[alias] = {
            "exact_base": b[0] if len(b) == 1 else None,
            "alias": a[0] if len(a) == 1 else None,
            "expected_delta_bytes": delta,
            "observed_delta_bytes": ((a[0]["segment"] == b[0]["segment"]) and a[0]["offset"] - b[0]["offset"])
                                    if len(a) == len(b) == 1 else None,
        }
    alias_ok = all(x["observed_delta_bytes"] == x["expected_delta_bytes"] for x in alias_geometry.values())
    communal_geometry = []
    far_bss_ok = len(far_bss) == 1
    bases = []
    for name, typed in IMPORTS.items():
        rows = by_name_rows.get("_" + name, [])
        if len(rows) != 1:
            far_bss_ok = False
            communal_geometry.append({"name": name, "missing_or_duplicate": len(rows)})
            continue
        row = rows[0]
        matching_frame = len(far_bss) == 1 and row["segment"] == far_bss[0]["frame_segment"]
        within = matching_frame and row["offset"] + typed["bytes"] <= far_bss[0]["length"]
        far_bss_ok = far_bss_ok and matching_frame and within
        communal_geometry.append({"name": name, "type": typed["type"], "bytes_from_source": typed["bytes"],
                                  "segment": row["segment"], "offset": row["offset"], "matches_far_bss": matching_frame,
                                  "within_far_bss_length": within})
        bases.append((row["segment"], row["offset"], row["offset"] + typed["bytes"], name))
    pairwise_disjoint = True
    for i, a in enumerate(bases):
        for b in bases[i + 1:]:
            if a[0] == b[0] and max(a[1], b[1]) < min(a[2], b[2]):
                pairwise_disjoint = False
    link_text_log = link_raw.decode("latin1", "replace")
    link_clean = bool(link_raw) and not re.search(r"undefined symbol|error\s+wrt|L20\d\d|fatal", link_text_log, re.I)
    output_file = case_dir / "PROBE.EXE"
    exact_publics_both = all(
        len(filtered[section].get(symbol, [])) == 1 for section in ("name", "value") for symbol in exact_symbols)
    passed = (not timed_out and return_code == 0 and output_file.is_file() and bool(map_raw) and
              bool(marker_lines) and not failure_lines and link_clean and exact_publics and exact_publics_both and alias_ok and
              far_bss_ok and pairwise_disjoint)
    def raw_receipt(name: str, raw: bytes) -> dict:
        return {"file": name, "sha256": sha(raw), "size": len(raw), "base64": base64.b64encode(raw).decode("ascii")}
    files = [hash_file(p) for p in sorted(case_dir.iterdir()) if p.is_file()]
    return {
        "linker": profile,
        "case": case,
        "expected_marker_exact_line": case_expectation["expected_marker"],
        "observed_exact_marker_lines": [x.decode("ascii") for x in marker_lines],
        "negative_marker_lines": failure_lines,
        "runtime_log_raw": raw_receipt("RUN.LOG", run_raw),
        "link_log_raw": raw_receipt("LINK.LOG", link_raw),
        "host_output_raw": raw_receipt("DOSBOX-HOST.LOG", host_output),
        "runner_returncode": return_code,
        "timed_out": timed_out,
        "link_clean": link_clean,
        "map_sections_exact_publics": filtered,
        "exact_publics_in_name_and_value_sections": exact_publics_both,
        "alias_geometry": alias_geometry,
        "far_bss_segments": far_bss,
        "typed_communal_geometry": communal_geometry,
        "typed_intervals_pairwise_disjoint": pairwise_disjoint,
        "map_warnings_and_errors": map_warnings,
        "map_sha256": sha(map_raw),
        "map_size": len(map_raw),
        "exe_sha256": sha(output_file.read_bytes()) if output_file.is_file() else None,
        "exe_size": output_file.stat().st_size if output_file.is_file() else None,
        "runtime_libraries": copied_runtime,
        "run_directory": str(case_dir),
        "input_files": files,
        "passed": passed,
    }


def main() -> int:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:12]
    run_root = OUT / "runs" / run_id
    run_root.mkdir(parents=True, exist_ok=False)
    inventory_path = ROOT / "build/workers/dos_far_word_inventory_v23_plan/inventory-v23.json"
    candidate_path = ROOT / "build/workers/dos_far_word_inventory_v23_plan/candidate-routing-v23.json"
    numeric_path = ROOT / "build/workers/dos_far_word_inventory_v23_plan/numeric-alias-asm-v23.json"
    overlaps_path = ROOT / "build/workers/dos_far_word_inventory_v23_plan/provider-overlap-v23.json"
    inv = json.loads(inventory_path.read_text(encoding="utf-8"))
    candidate_packet = json.loads(candidate_path.read_text(encoding="utf-8"))
    numeric_packet = json.loads(numeric_path.read_text(encoding="utf-8"))
    overlap_packet = json.loads(overlaps_path.read_text(encoding="utf-8"))
    report_path = ROOT / "build/source-only-dos/build-report.json"
    report_raw = report_path.read_bytes()
    report = json.loads(report_raw)
    if len(inv["source_receipts"]) != 156 or len({x["path"] for x in inv["source_receipts"]}) != 156:
        raise RuntimeError("v23 static source graph is not exactly 156 unique receipts")
    if len(inv["imports"]) != 226:
        raise RuntimeError("v23 complete source index does not retain its original 226 FAR name-selection set")
    source_pin_rows = []
    for row in inv["source_receipts"]:
        path = ROOT / row["path"]
        raw = path.read_bytes()
        if len(raw) != row["size"] or sha(raw) != row["sha256"]:
            raise RuntimeError("pinned source graph member changed: " + row["path"])
        source_pin_rows.append({"path": row["path"], "source_set": row["set"], "sha256": row["sha256"], "size": row["size"]})
    if sum(x["source_set"] == "canonical_127" for x in source_pin_rows) != 127 or \
       sum(x["source_set"] == "effective_strict_29" for x in source_pin_rows) != 29:
        raise RuntimeError("pinned static graph must contain the 127 canonical + 29 strict effective source split")
    family = next(x for x in candidate_packet["families"] if x["id"] == "mode_population_vectors")
    if set(x["name"] for x in family["members"]) != set(IMPORTS):
        raise RuntimeError("v23 source candidate receipt is not the assigned four-vector family")
    if any(x["current_compiled_provider_overlaps"] for x in family["members"]):
        raise RuntimeError("current mapped provider intersects a candidate extent")
    report_imports = {x.get("name", "").lstrip("_") for x in report.get("unresolved_symbols", [])}
    if not set(IMPORTS).issubset(report_imports):
        raise RuntimeError("one or more assigned candidates is no longer in the report's unresolved import list")

    # Retain the source views and citations used by the source-owner review.
    selected_source_paths = sorted({
        *(x["path"] for x in family["source_owner"]),
        *(r["path"] for m in family["members"] for r in m["reference_paths_functions_lines"]),
        *(d[0] for m in family["members"] for d in m["declarations"]),
        "src/S09/m35F5.c",
    })
    copied_views = []
    for rel in selected_source_paths:
        source = ROOT / rel
        dest = run_root / "source_views" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
        copied_views.append({"path": rel, "sha256": sha(source.read_bytes()), "size": source.stat().st_size,
                             "copied_path": str(dest.relative_to(run_root))})

    manifest = modules.load_manifest()
    tc = compiler.toolchain()
    provider_text = arrays_owner()
    provider_source = OUT / "provider" / "mode-population-vectors.c"
    provider_source.parent.mkdir(parents=True, exist_ok=True)
    if provider_source.exists() and provider_source.read_text(encoding="ascii") != provider_text:
        raise RuntimeError("existing natural provider source differs; refusing to overwrite")
    provider_source.write_text(provider_text, encoding="ascii", newline="\n")

    owner_flags = ["/AL", "/Os", "/Oe", "/Og", "/Zi"]
    consumer_flags = ["/AL", "/Os", "/Zi"]
    compiled: dict[str, dict] = {}
    compiled["natural_owner"] = compile_source(run_root, "mode_population_owner", provider_text, owner_flags)
    compiled["runtime_positive"] = compile_source(run_root, "runtime_positive", runtime_consumer("positive"), consumer_flags)
    compiled["runtime_wrong_type_consumer"] = compile_source(run_root, "runtime_wrong_type_consumer", runtime_consumer("wrong_element_type"), consumer_flags)
    compiled["runtime_wrong_extent_consumer"] = compile_source(run_root, "runtime_wrong_extent_consumer", runtime_consumer("wrong_extent"), consumer_flags)
    compiled["runtime_wrong_b12_base_consumer"] = compile_source(run_root, "runtime_wrong_b12_base_consumer", runtime_consumer("wrong_base_b12"), consumer_flags)
    compiled["runtime_wrong_c2a_base_consumer"] = compile_source(run_root, "runtime_wrong_c2a_base_consumer", runtime_consumer("wrong_base_c2a"), consumer_flags)
    compiled["wrong_short_extent"] = compile_source(run_root, "control_short_extent", "int far fd_50F6_0B12[5];\n", owner_flags)
    compiled["wrong_element_width"] = compile_source(run_root, "control_wrong_element_width", "unsigned char far fd_50F6_0B12[12];\n", owner_flags)
    compiled["wrong_unsigned_element"] = compile_source(run_root, "control_unsigned_element", "unsigned int far fd_50F6_0B12[6];\n", owner_flags)
    compiled["initialized_storage"] = compile_source(run_root, "control_initialized_storage", initialized_owner(), owner_flags)
    compiled["signedness_signed"] = compile_source(run_root, "control_signed_comparison", signedness_source(False), consumer_flags)
    compiled["signedness_unsigned"] = compile_source(run_root, "control_unsigned_comparison", signedness_source(True), consumer_flags)

    # Inspect OMF for canonical S09's actual SaveRec table initializer rather than relying only
    # on a hand-written fixture. This is evidence for the two raw 12-byte persistence views.
    save_module = manifest["modules"]["S09:35F5"]
    save_src_raw = (ROOT / save_module["source"]).read_bytes()
    save_src = save_src_raw.decode("latin1")
    if sha(save_src_raw) != save_module["source_sha256"]:
        raise RuntimeError("S09:35F5 canonical source hash differs from the manifest")
    save_compiled_result = compiler.compile_c(save_src, save_module["profile"], list(save_module["flags"]),
                                              basename="M35F5SV", keep=False)
    if not save_compiled_result.ok or save_compiled_result.obj is None:
        raise RuntimeError("pinned S09:35F5 compile failed:\n" + save_compiled_result.log)
    save_obj_path = run_root / "objects" / "canonical-S09-m35F5.OBJ"
    save_obj_path.write_bytes(save_compiled_result.obj)
    save_log_path = run_root / "compiler-logs" / "canonical-S09-m35F5.log"
    save_log_path.write_bytes(save_compiled_result.log.encode("latin1", "replace"))
    save_omf = OmfReader(communals=True).read(save_compiled_result.obj)
    save_table = next((p for p in save_omf.publics if p["name"] == "_fd_4E4B_0000"), None)
    if save_table is None:
        raise RuntimeError("compiled canonical SaveRec table public _fd_4E4B_0000 was not found")
    row_data = {}
    for name, line in (("fd_50F6_0B12", 986), ("fd_50F6_0C2A", 987)):
        row_index = line - 894
        expected_fixup_offset = save_table["offset"] + row_index * 8 + 4
        found_all = [x for x in save_omf.linker_fixups if x.get("target") == "_" + name]
        found = [x for x in found_all if x.get("segment") == save_table["segment"] and
                 x.get("offset") == expected_fixup_offset]
        if len(found) != 1:
            raise RuntimeError(f"expected one canonical SaveRec data-segment pointer fixup for {name}, got {found_all}")
        fixup = found[0]
        row_data[name] = {
            "source_path": save_module["source"], "source_line": line,
            "source_text": save_src.splitlines()[line - 1].strip(),
            "save_table_public": save_table,
            "save_row_index_from_initializer": row_index,
            "expected_pointer_field_offset": expected_fixup_offset,
            "actual_fixup": fixup,
            "all_same_target_fixups_including_codeview_records": found_all,
            "actual_matches_8_byte_save_rec_layout": fixup.get("offset") == expected_fixup_offset,
            "raw_view": {"element_size_bytes": 2, "count": 6, "byte_extent": 12},
            "fixup_target": fixup.get("target"),
            "encoded_addend": fixup.get("encoded_addend"),
        }
        if fixup.get("offset") != expected_fixup_offset or fixup.get("encoded_addend") != "00000000":
            raise RuntimeError(f"canonical SaveRec row/fixup mismatch for {name}: {row_data[name]}")

    # Verify candidate compile-time communal shapes and a real signedness codegen contrast.
    def selected_communal(key: str) -> list:
        return [x for x in compiled[key]["communals"] if x.get("name") == "_fd_50F6_0B12"]
    control_receipts = {}
    for key, label in (("natural_owner", "signed_int6_natural_owner"), ("wrong_short_extent", "int5"),
                       ("wrong_element_width", "unsigned_char12"), ("wrong_unsigned_element", "unsigned_int6"),
                       ("initialized_storage", "initialized_int6")):
        control_receipts[label] = {
            "source": compiled[key]["source"], "source_sha256": compiled[key]["source_sha256"],
            "object_sha256": compiled[key]["object_sha256"], "communals_for_B12": selected_communal(key),
            "segments": compiled[key]["segments"], "publics": compiled[key]["publics"],
            "segment_bytes": compiled[key]["segment_bytes"],
        }
    signed_code = compiled["signedness_signed"]["segment_bytes"]
    unsigned_code = compiled["signedness_unsigned"]["segment_bytes"]
    signedness_code_differs = signed_code != unsigned_code
    if not signedness_code_differs:
        raise RuntimeError("signed versus unsigned '< 0' control generated identical OMF segment bytes")

    runtime_specs = [
        ("typed_raw_SaveRec_startup_zero", "runtime_positive", "PASS_MODE_POPULATION_TYPED_RAW_SAVE_REC_STARTUP_ZERO", arrays_owner(), {}),
        ("wrong_element_type_same_extent", "runtime_wrong_type_consumer", "REJECTED_WRONG_ELEMENT_TYPE", wrong_element_owner(), {}),
        ("short_five_words_guarded", "runtime_wrong_extent_consumer", "REJECTED_SIXTH_WORD_HITS_DECLARED_GUARD", short_extent_owner(), {}),
        ("wrong_SaveRec_base_B12_plus_one_word", "runtime_wrong_b12_base_consumer", "REJECTED_WRONG_BASE_0B12", arrays_owner(), {"b12_alias_delta": 2}),
        ("wrong_SaveRec_base_C2A_plus_one_word", "runtime_wrong_c2a_base_consumer", "REJECTED_WRONG_BASE_0C2A", arrays_owner(), {"c2a_alias_delta": 2}),
    ]
    cases = []
    for profile in ("rtlink400", "rtlink610"):
        for case_name, consumer_key, marker, owner_body, geometry in runtime_specs:
            owner_key = "natural_owner" if case_name not in ("wrong_element_type_same_extent", "short_five_words_guarded") else (
                "runtime_wrong_type_owner" if case_name == "wrong_element_type_same_extent" else "runtime_wrong_extent_owner")
            if owner_key not in compiled:
                source_key = "runtime_wrong_type_owner" if case_name == "wrong_element_type_same_extent" else "runtime_wrong_extent_owner"
                compiled[source_key] = compile_source(run_root, source_key, owner_body, owner_flags)
            owner = compiled[owner_key]
            consumer = compiled[consumer_key]
            cases.append(run_link_case(run_root, case_name, owner, consumer, owner_body,
                                       {"expected_marker": marker, **geometry}, profile, manifest, tc))

    # Capture verified compiler, linker, runner, runtime, graph and repository inputs.
    toolchain_path = ROOT / "layout/toolchain.json"
    manifest_path = ROOT / "layout/manifest.json"
    symbols_path = ROOT / "layout/symbols.json"
    tc_files = []
    profile = tc["profiles"]["msc600ax"]
    for rel, expected in profile.get("files", {}).items():
        p = Path(profile["directory"]) / rel
        if not p.is_file() or sha(p.read_bytes()) != expected:
            raise RuntimeError(f"MSC 6.00AX tool input changed: {p}")
        tc_files.append({"path": str(p), "sha256": expected, "size": p.stat().st_size, "role": "msc600ax_pinned_file"})
    linker_inputs = []
    for linker_name in ("rtlink400", "rtlink610"):
        linker = tc["linkers"][linker_name]
        for rel, expected in linker["files"].items():
            p = Path(linker["directory"]) / rel
            if not p.is_file() or sha(p.read_bytes()) != expected:
                raise RuntimeError(f"{linker_name} tool input changed: {p}")
            linker_inputs.append({"path": str(p), "sha256": expected, "size": p.stat().st_size, "role": linker_name + "_pinned_file"})
    runner = tc["runners"]["dosbox-x"]
    runner_path = Path(runner["path"])
    if not runner_path.is_file() or sha(runner_path.read_bytes()) != runner["sha256"]:
        raise RuntimeError("pinned DOSBox-X runner changed")
    runtime_inputs = []
    for row in manifest["runtime"]["libraries"].values():
        p = Path(row["path"])
        if not p.is_file() or sha(p.read_bytes()) != row["sha256"]:
            raise RuntimeError("pinned runtime library changed: " + str(p))
        runtime_inputs.append({"path": str(p), "sha256": row["sha256"], "size": p.stat().st_size})
    repo_tool_inputs = [ROOT / "tools/compiler.py", ROOT / "tools/modules.py", ROOT / "tools/omf.py",
                        ROOT / "tools/source_only_dos.py", ROOT / "tools/csrc.py"]
    repo_tool_receipts = [hash_file(p) for p in repo_tool_inputs if p.is_file()]

    # Reverify all source inputs after tests to detect concurrent mutation.
    for row in source_pin_rows:
        p = ROOT / row["path"]
        if sha(p.read_bytes()) != row["sha256"]:
            raise RuntimeError("pinned source changed while running: " + row["path"])

    owner_omf = compiled["natural_owner"]["_omf"]
    positive_consumer_omf = compiled["runtime_positive"]["_omf"]
    fixture_save_table = next((p for p in positive_consumer_omf.publics if p["name"] == "_SaveRows"), None)
    if fixture_save_table is None:
        raise RuntimeError("positive fixture lacks public SaveRows table")
    save_rec_fixture_fixups = []
    for name, row_index in (("fd_50F6_0B12", 0), ("fd_50F6_0C2A", 1)):
        field_offset = fixture_save_table["offset"] + row_index * 8 + 4
        candidates = [f for f in positive_consumer_omf.linker_fixups if f.get("segment") == fixture_save_table["segment"] and
                      f.get("offset") == field_offset]
        if len(candidates) != 1 or candidates[0].get("target") != "_" + name or candidates[0].get("encoded_addend") != "00000000":
            raise RuntimeError(f"fixture SaveRec row {row_index} does not have exact base+zero-addend fixup: {candidates}")
        save_rec_fixture_fixups.append({"row_index": row_index, "pointer_field_offset": field_offset,
                                        "source_table_public": fixture_save_table, "fixup": candidates[0]})
    provider_report = {
        "provider_source": {"path": str(provider_source.relative_to(ROOT)), "sha256": sha(provider_source.read_bytes()),
                            "text": provider_source.read_text(encoding="ascii"),
                            "kind": "natural data-only source; four ordinary signed int array definitions; no initializer, functions, padding, or gap-derived span"},
        "object": {k: v for k, v in compiled["natural_owner"].items() if not k.startswith("_")},
        "expected_communal_shapes": [{"name": "_" + n, "type": t["type"], "count": 6 if "[6]" in t["type"] else 20,
                                      "element_size": 2, "length": t["bytes"]} for n, t in IMPORTS.items()],
    }
    actual_communal_by_name = {x["name"]: x for x in owner_omf.communals}
    if any(actual_communal_by_name.get("_" + name, {}).get("length") != data["bytes"] for name, data in IMPORTS.items()):
        raise RuntimeError("natural provider OMF COMDEF lengths do not match source-declared arrays")
    if any(actual_communal_by_name.get("_" + name, {}).get("element_size") != 2 for name in IMPORTS):
        raise RuntimeError("natural provider OMF COMDEF element sizes are not all two bytes")
    for control, expected in (("wrong_short_extent", 10), ("wrong_element_width", 12), ("wrong_unsigned_element", 12)):
        rows = selected_communal(control)
        if len(rows) != 1:
            raise RuntimeError(f"expected exactly one B12 COMDEF in {control}: {rows}")
        if control == "wrong_short_extent" and (rows[0].get("count"), rows[0].get("element_size"), rows[0].get("length")) != (5, 2, expected):
            raise RuntimeError("short array contrast lacks 5 x 2 = 10 OMF shape")
        if control == "wrong_element_width" and (rows[0].get("count"), rows[0].get("element_size"), rows[0].get("length")) != (12, 1, expected):
            raise RuntimeError("byte-array contrast lacks 12 x 1 = 12 OMF shape")
        if control == "wrong_unsigned_element" and (rows[0].get("count"), rows[0].get("element_size"), rows[0].get("length")) != (6, 2, expected):
            raise RuntimeError("unsigned int array contrast lacks 6 x 2 = 12 OMF shape")
    init_b12_common = selected_communal("initialized_storage")
    if init_b12_common:
        raise RuntimeError("initialized owner unexpectedly remained a COMDEF")
    if not save_rec_fixture_fixups or any(f["fixup"].get("encoded_addend") != "00000000" for f in save_rec_fixture_fixups):
        raise RuntimeError("fixture SaveRec raw views do not fix up to exact bases with zero encoded addend")

    report_obj = {
        "schema": "simant-mode-population-vectors-owner-proof-v23",
        "status": "SCRATCH_ONLY_NO_ADMISSION",
        "run_id": run_id,
        "selection_snapshot": {"path": str(report_path.relative_to(ROOT)), "sha256": sha(report_raw),
                               "unresolved_imports_observed": len(report["unresolved_symbols"]),
                               "v23_far_name_selection_snapshot": 226,
                               "v23_inventory_report_sha256": next(x["sha256"] for x in inv["input_pins"] if x["path"] == "build/source-only-dos/build-report.json"),
                               "translation_units_observed": len(report["translation_units"]),
                               "current_candidate_names_still_unresolved": sorted(report_imports & set(IMPORTS)),
                               "role": "mutable observational name-selection input only; source types and ownership come from the pinned 156-source graph"},
        "source_graph": {"source_graph": "127 canonical + 29 strict effective static sources", "unique_paths": len(source_pin_rows),
                         "hashes": source_pin_rows, "all_match_before_and_after": True,
                         "inventory_path": str(inventory_path.relative_to(ROOT)), "inventory_sha256": sha(inventory_path.read_bytes()),
                         "source_owner_receipts": family["source_owner"], "four_member_complete_receipts": family["members"],
                         "numeric_alias_asm_receipts": numeric_packet["members"],
                         "provider_overlap_receipt": overlap_packet,
                         "selected_source_views_copied": copied_views},
        "source_ownership": {"family_id": family["id"], "name": family["name"], "ownership_basis": family["ownership_basis"],
                             "source_types_and_spans": family["type_and_extent"], "typed_bytes": family["source_typed_bytes"],
                             "save_rec_review": family["save_rec"], "source_limits": family["limits"],
                             "domain_separation": "The four fixed source extents do not prove every AlistM/RlistM/task-state index is in 0..19. That dynamic index-domain condition remains a separate game-behavior limit; no index bound is inferred from adjacent storage or this proof."},
        "natural_provider": provider_report,
        "compiler_controls": {"flags_owner": owner_flags, "flags_consumer": consumer_flags,
                              "types_and_omf": control_receipts,
                              "signedness_codegen_contrast": {"signed_source": compiled["signedness_signed"]["source"],
                                  "signed_object_sha256": compiled["signedness_signed"]["object_sha256"],
                                  "signed_segment_bytes": signed_code,
                                  "unsigned_source": compiled["signedness_unsigned"]["source"],
                                  "unsigned_object_sha256": compiled["signedness_unsigned"]["object_sha256"],
                                  "unsigned_segment_bytes": unsigned_code, "bytes_differ": signedness_code_differs},
                              "initialized_storage_control": "B12 initialized to {1}; compiler emitted initialized public data rather than COMDEF. This distinguishes the intended common-zero natural definition from initialized storage."},
        "canonical_save_rec_object": {"module": "S09:35F5", "source": save_module["source"],
            "source_sha256": save_module["source_sha256"], "profile": save_module["profile"], "flags": save_module["flags"],
            "object": str(save_obj_path.relative_to(run_root)), "object_sha256": sha(save_compiled_result.obj),
            "object_size": len(save_compiled_result.obj), "compile_log": str(save_log_path.relative_to(run_root)),
            "compile_log_sha256": sha(save_log_path.read_bytes()), "table_public": save_table,
            "rows": row_data, "all_two_rows_exact_target_zero_addend": True},
        "runtime_fixture_save_rec_fixups": save_rec_fixture_fixups,
        "runtime": {"compiler_profile": "msc600ax", "linkers": ["rtlink400", "rtlink610"],
                    "cases_per_linker": 5, "cases": cases,
                    "all_cases_pass": len(cases) == 10 and all(x["passed"] for x in cases),
                    "positive_case": "all 104 bytes are checked zero before any write; typed writes cover each vector ends/interior; two SaveRec rows are checked as {element-size=2,count=6,base} and then exercised through raw bytes and signed typed words.",
                    "negative_cases": ["12 unsigned bytes at B12 with same raw 12-byte span fail signed-int element interpretation", "an explicit int[5] plus named guard in one struct detects index 5 overwriting the guard, with no allocation-gap assumption", "separate SaveRec bases shifted by one int are rejected for each six-word vector"],
                    "raw_log_bytes_preserved": True,
                    "map_contract": "Each run stores full MAP and both filtered Name and Value public sections. Exact publics must resolve, SaveAlias geometry must equal the LNK expression, and candidate typed spans must be pairwise disjoint within the map's FAR_BSS segment. No gap is used to infer an extent."},
        "historical_provenance": "Unknown and not claimed: no original COMDEF-producing translation unit, communal allocation order, historical FAR_BSS coordinates, or intervening padding is inferred. The candidate is a source-functional data-only owner.",
        "input_pins": {"v23_inventory": hash_file(inventory_path), "candidate_routing": hash_file(candidate_path),
                       "numeric_alias_asm": hash_file(numeric_path), "provider_overlap": hash_file(overlaps_path),
                       "report": hash_file(report_path), "manifest": hash_file(manifest_path),
                       "symbols": hash_file(symbols_path), "toolchain": hash_file(toolchain_path),
                       "tools": repo_tool_receipts, "msc600ax_files": tc_files, "rtlink_files": linker_inputs,
                       "dosbox_runner": hash_file(runner_path), "runtime_libraries": runtime_inputs,
                       "probe_script": hash_file(Path(__file__)), "run_provider_source": hash_file(provider_source)},
    }
    write_json(run_root / "runtime-review-v23.json", report_obj)
    review = [
        "# Mode population vector owner proof (v23)", "",
        f"Run `{run_id}` is scratch-only. It observes the v23 report at `{sha(report_raw)}` for names; the complete 156-file static graph supplies source types and ownership.", "",
        "The source-functional data-only owner consists of exactly four naturally declared signed `int` arrays: `fd_50F6_0B12[6]` and `fd_50F6_0C2A[6]` (12 bytes each), plus `fd_50F6_0D40[20]` and `fd_50F6_0D72[20]` (40 bytes each), for 104 bytes. `ClrModePop` clears both twenty-word vectors. A/R/B-list producers update them; `TallyModePop` writes all six elements of both summary arrays. The canonical S09 SaveRec table has exact `{2,6}` rows for the two summaries.", "",
        "The dynamic producer indexes still depend on ant/list/task-state values. Their full legal range is not established here; that remains separate from the strongly typed 20-element storage extent.", "",
        "MSC OMF controls distinguish signed `int[6]` as 6×2 bytes from `int[5]` (10 bytes), `unsigned char[12]` (12 bytes but wrong elements), and initialized data (not a COMDEF). Signed and unsigned comparison fixtures produce different code bytes. The actual compiled S09 SaveRec table fixups for rows 986–987 target the exact vector symbols with zero encoded addends.", "",
        "Five fresh runtime cases ran with each pinned RTLink: startup-zero and typed/raw SaveRec positive; same-span wrong element type; `int[5]` plus explicit guard; B12 base shifted by one word; and C2A base shifted by one word. Each case preserves exact raw RUN.LOG/LINK.LOG bytes, map file, exact Name/Value publics, and alias geometry. See `runtime-review-v23.json` for per-case results and all hashes.", "",
        "Historical COMDEF source/order/communal placement/padding are not claimed. No original executable was read; no canonical, production, binding, or Git files were changed.", "",
    ]
    (run_root / "source-review-v23.md").write_text("\n".join(review), encoding="utf-8")
    print(json.dumps({"run": str(run_root), "report": str(run_root / "runtime-review-v23.json"),
                      "all_cases_pass": report_obj["runtime"]["all_cases_pass"],
                      "cases": [(x["linker"], x["case"], x["observed_exact_marker_lines"], x["passed"]) for x in cases],
                      "provider_commons": compiled["natural_owner"]["communals"],
                      "canonical_save_rec_rows": row_data}, indent=2))
    return 0 if report_obj["runtime"]["all_cases_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
