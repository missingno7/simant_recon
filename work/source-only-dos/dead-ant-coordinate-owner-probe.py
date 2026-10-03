"""Review-only source ownership and clean DOS runtime probe for the dead-ant rings."""
from __future__ import annotations

from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


def find_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "layout/manifest.json").is_file():
            return candidate
    raise RuntimeError("repository root not found")


ROOT = find_root()
OUT = ROOT / "build/workers/dos_dead_ant_coordinate_owners"
OUT.mkdir(parents=True, exist_ok=True)
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "tools"))

import compiler  # noqa: E402
import source_only_dos as dos  # noqa: E402
from omf import OmfReader  # noqa: E402


NAMES = ("fd_50F6_037C", "fd_50F6_0404")
RING_INDEX = "fd_50F6_0476"
SAVE_PATH = "src/S09/m35F5.c"
PROFILE = "msc600ax"
FIXTURE_FLAGS = ["/AL", "/Os", "/Gs"]

OWNER_SOURCE = """unsigned char far fd_50F6_037C[100];
unsigned char far DeadAntXGuard;
unsigned char far fd_50F6_0404[100];
unsigned char far DeadAntYGuard;
"""
PROVIDER_PATH = ROOT / 'work/source-only-dos/providers/dead-ant-coordinate-rings.c'
PROVIDER_CANDIDATE_SOURCE = PROVIDER_PATH.read_text(encoding='ascii')
WRONG_EXTENT_SOURCE = """unsigned char far fd_50F6_037C[101];
unsigned char far DeadAntXGuard;
unsigned char far fd_50F6_0404[100];
unsigned char far DeadAntYGuard;
"""
INITIALIZED_SOURCE = """unsigned char far fd_50F6_037C[100] = { 1 };
unsigned char far DeadAntXGuard;
unsigned char far fd_50F6_0404[100];
unsigned char far DeadAntYGuard;
"""
WRONG_ELEMENT_SOURCE = """unsigned int far fd_50F6_037C[100];
unsigned char far DeadAntXGuard;
unsigned int far fd_50F6_0404[100];
unsigned char far DeadAntYGuard;
"""

DIRECT_CONSUMER = r"""extern unsigned char far fd_50F6_037C[100];
extern unsigned char far fd_50F6_0404[100];
extern unsigned char far probeDeadAntX[100];
extern unsigned char far probeDeadAntY[100];
extern unsigned char far DeadAntXGuard;
extern unsigned char far DeadAntYGuard;
extern int far puts(char far *text);
int main(void)
{
    int i;
    if (&fd_50F6_037C[0] != &probeDeadAntX[0] ||
        &fd_50F6_0404[0] != &probeDeadAntY[0]) {
        puts("FAIL"); return 1;
    }
    if (&fd_50F6_0404[0] != &fd_50F6_037C[100] ||
        &DeadAntYGuard != &fd_50F6_0404[100]) {
        puts("FAIL"); return 1;
    }
    for (i = 0; i < 100; i++) {
        if (fd_50F6_037C[i] != 0 || fd_50F6_0404[i] != 0) {
            puts("FAIL"); return 1;
        }
        fd_50F6_037C[i] = (unsigned char)i;
        fd_50F6_0404[i] = (unsigned char)(255 - i);
    }
    if (fd_50F6_037C[99] != 99 || fd_50F6_0404[0] != 255 ||
        fd_50F6_0404[99] != 156) {
        puts("FAIL"); return 1;
    }
    puts("PASS"); return 0;
}
"""

SAVEREC_CONSUMER = r"""extern unsigned char far fd_50F6_037C[100];
extern unsigned char far fd_50F6_0404[100];
extern int far puts(char far *text);
struct SaveRec { int size; int count; void far *data; };
struct SaveRec far SaveRecTable[2] = {
    { 1, 100, (void far *)&fd_50F6_037C },
    { 1, 100, (void far *)&fd_50F6_0404 }
};
int main(void)
{
    int i;
    unsigned char far *x;
    unsigned char far *y;
    x = (unsigned char far *)SaveRecTable[0].data;
    y = (unsigned char far *)SaveRecTable[1].data;
    if (SaveRecTable[0].size != 1 || SaveRecTable[0].count != 100 ||
        SaveRecTable[1].size != 1 || SaveRecTable[1].count != 100 ||
        x != &fd_50F6_037C[0] || y != &fd_50F6_0404[0]) {
        puts("FAIL"); return 1;
    }
    for (i = 0; i < 100; i++) {
        x[i] = (unsigned char)(i + 1);
        y[i] = (unsigned char)(254 - i);
    }
    if (fd_50F6_037C[0] != 1 || fd_50F6_037C[99] != 100 ||
        fd_50F6_0404[0] != 254 || fd_50F6_0404[99] != 155) {
        puts("FAIL"); return 1;
    }
    puts("PASS"); return 0;
}
"""

SIGNED_VIEW_CONSUMER = r"""extern unsigned char far fd_50F6_037C[100];
extern signed char far probeDeadAntX[100];
extern int far puts(char far *text);
int main(void)
{
    fd_50F6_037C[0] = 0x80;
    if (probeDeadAntX[0] >= 0) {
        puts("PASS"); return 0;
    }
    puts("FAIL"); return 1;
}
"""

INITIALIZER_CONSUMER = r"""extern unsigned char far fd_50F6_037C[100];
extern unsigned char far fd_50F6_0404[100];
extern int far puts(char far *text);
int main(void)
{
    if (fd_50F6_037C[0] != 0 || fd_50F6_0404[0] != 0) {
        puts("FAIL"); return 1;
    }
    puts("PASS"); return 0;
}
"""


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin(path: Path, expected: str | None = None) -> dict:
    return dos.pin(path, expected)[1]


def visible_lines(lines: list[str]) -> list[str]:
    """Mask C comments and literals while retaining source line structure."""
    result = []
    in_block = False
    for line in lines:
        out = []
        i = 0
        quote = None
        escaped = False
        while i < len(line):
            c = line[i]
            nxt = line[i + 1] if i + 1 < len(line) else ""
            if in_block:
                out.append(" ")
                if c == "*" and nxt == "/":
                    out.append(" ")
                    i += 2
                    in_block = False
                    continue
            elif quote:
                out.append(" ")
                if escaped:
                    escaped = False
                elif c == "\\":
                    escaped = True
                elif c == quote:
                    quote = None
            elif c == "/" and nxt == "*":
                out.extend("  ")
                i += 2
                in_block = True
                continue
            elif c == "/" and nxt == "/":
                out.extend(" " * (len(line) - i))
                break
            elif c in ('"', "'"):
                quote = c
                out.append(" ")
            else:
                out.append(c)
            i += 1
        result.append("".join(out))
    return result


def source_inventory(manifest: dict, manifest_pin: dict) -> tuple[list[dict], list[dict]]:
    rows = []
    for module, entry in manifest["modules"].items():
        rows.append({"path": entry["source"], "sha256": entry["source_sha256"],
                     "role": f"canonical:{module}"})

    index_path = ROOT / "work/source-only-dos/static-completeness/index-v1.json"
    index_raw, index_pin = dos.pin(index_path)
    index = json.loads(index_raw)
    if index.get("schema") != "simant-dos-strict-static-index-v1" or len(index.get("entries", {})) != 29:
        raise RuntimeError("strict source scan requires the reviewed 29-entry index")
    receipt_pins = [manifest_pin, index_pin]
    for function, ref in sorted(index["entries"].items()):
        raw, receipt_pin = dos.pin(ROOT / ref["path"], ref["sha256"])
        receipt_pins.append(receipt_pin)
        receipt = json.loads(raw)
        registered = receipt.get("registered_source", {})
        if not registered.get("whole_module") or not registered.get("path") or not registered.get("sha256"):
            raise RuntimeError(f"strict-29 source is not pinned as a whole module: {function}")
        rows.append({"path": registered["path"], "sha256": registered["sha256"],
                     "role": f"strict29:{function}"})
        if function == "DrawBalloons":
            corrected = receipt.get("audit", {}).get("source", {})
            if not corrected.get("path") or not corrected.get("sha256"):
                raise RuntimeError("corrected strict DrawBalloons source pin is absent")
            rows.append({"path": corrected["path"], "sha256": corrected["sha256"],
                         "role": "strict29-corrected:DrawBalloons"})

    merged = {}
    for row in rows:
        prior = merged.get(row["path"])
        if prior and prior["sha256"] != row["sha256"]:
            raise RuntimeError(f"source pin disagreement for {row['path']}")
        if not prior:
            merged[row["path"]] = {"path": row["path"], "sha256": row["sha256"], "roles": []}
        merged[row["path"]]["roles"].append(row["role"])
    return [merged[key] for key in sorted(merged)], receipt_pins


def scan_sources(source_rows: list[dict]) -> tuple[dict, dict[str, list[dict]]]:
    refs = {name: [] for name in (*NAMES, RING_INDEX)}
    source_pins = []
    token = re.compile(r"(?<![A-Za-z0-9_])(" + "|".join(map(re.escape, refs)) + r")(?![A-Za-z0-9_])")
    for row in source_rows:
        path = ROOT / row["path"]
        raw, source_pin = dos.pin(path, row["sha256"])
        source_pins.append(source_pin)
        lines = raw.decode("latin1").splitlines()
        clean = visible_lines(lines)
        for line_no, (original, code) in enumerate(zip(lines, clean), 1):
            for match in token.finditer(code):
                name = match.group(1)
                category = "expression"
                if re.search(r"\bextern\b", code):
                    category = "extern_declaration"
                elif (row["path"] == SAVE_PATH and re.fullmatch(
                        r"\{\s*\d+\s*,\s*\d+\s*,\s*\(void\s+far\s*\*\)\s*&" +
                        re.escape(name) + r"\s*\},?", code.strip())):
                    category = "SaveRec_exact_base"
                elif name != RING_INDEX and re.search(
                        r"\b" + re.escape(name) + r"\s*\[([^\]]+)\]", code):
                    category = "array_index:" + re.search(
                        r"\b" + re.escape(name) + r"\s*\[([^\]]+)\]", code).group(1).strip()
                elif re.search(r"(?<!&)&\s*" + re.escape(name) + r"\b", code):
                    category = "address_escape"
                refs[name].append({"source": row["path"], "line": line_no,
                                   "text": original.strip(), "category": category,
                                   "roles": row["roles"]})
    summary = {}
    for name, uses in refs.items():
        counts = defaultdict(int)
        for use in uses:
            counts[use["category"]] += 1
        summary[name] = {"line_hits": len(uses), "categories": dict(sorted(counts.items())),
                         "references": uses}
    return summary, source_pins


def save_table_rows() -> dict[str, list[dict]]:
    path = ROOT / SAVE_PATH
    lines = path.read_text(encoding="ascii").splitlines()
    start = next(i for i, line in enumerate(lines)
                 if "struct SaveRec far fd_4E4B_0000[308] = {" in line)
    rows = {name: [] for name in (*NAMES, RING_INDEX)}
    record = 0
    active = False
    row_re = re.compile(r"\{\s*(\d+)\s*,\s*(\d+)\s*,\s*\(void\s+far\s*\*\)\s*&([A-Za-z_][A-Za-z0-9_]*)\s*\},?")
    for i in range(start + 1, len(lines)):
        text = lines[i].strip()
        if text == "};":
            break
        if not text or text.startswith("/*") or text.startswith("//"):
            continue
        active = True
        if text.startswith("{"):
            record += 1
            match = row_re.fullmatch(text)
            if match and match.group(3) in rows:
                size, count, name = int(match.group(1)), int(match.group(2)), match.group(3)
                rows[name].append({"row_1based": record, "line": i + 1,
                                   "size": size, "count": count,
                                   "bytes": size * count, "text": text})
    if (not active or any(len(rows[name]) != 1 or
                          (rows[name][0]["size"], rows[name][0]["count"], rows[name][0]["bytes"]) != (1, 100, 100)
                          for name in NAMES) or
            len(rows[RING_INDEX]) != 1 or
            (rows[RING_INDEX][0]["size"], rows[RING_INDEX][0]["count"], rows[RING_INDEX][0]["bytes"]) != (2, 1, 2)):
        raise RuntimeError(f"coordinate rings lack one exact byte[100] SaveRec row: {rows}")
    return rows


def registry_audit(symbols: dict) -> dict:
    ranges = {
        NAMES[0]: (892, 992),
        NAMES[1]: (1028, 1128),
    }
    out = {}
    for name, (start, end) in ranges.items():
        rows = [{"table": table, "name": other, "off": row.get("off"), "alias_of": row.get("alias_of")}
                for table in ("data", "code") for other, row in symbols[table].items()
                if row.get("seg") == 0x50F6 and isinstance(row.get("off"), int)
                and start <= row["off"] < end]
        same_base = [row for row in rows if row["off"] == start]
        interior = [row for row in rows if start < row["off"] < end]
        boundary = sorted((table, other) for table in ("data", "code")
                          for other, row in symbols[table].items()
                          if row.get("seg") == 0x50F6 and row.get("off") == end)
        out[name] = {"range_half_open": [start, end], "registered_within_extent": rows,
                     "same_base_names": same_base, "registered_interior_names": interior,
                     "exact_end_boundary_names": boundary}
        if [row["name"] for row in same_base] != [name] or interior:
            raise RuntimeError(f"registered alias/interior overlap for {name}: {out[name]}")
    return out


def fixup_key(row: dict) -> tuple:
    return tuple(row[k] for k in (
        "segment", "offset", "width", "loc", "self_relative", "target_kind",
        "target", "displacement", "frame_kind", "frame", "encoded_addend"))


def object_packet(obj) -> dict:
    return {
        "segment_defs": obj.segment_defs,
        "segment_lengths": obj.segment_lengths,
        "groups": obj.groups,
        "segments": {name: {"length": len(data), "sha256": sha(bytes(data))}
                     for name, data in sorted(obj.segments.items())},
        "publics": obj.publics,
        "local_publics": getattr(obj, "local_publics", []),
        "ordered_fixups": [fixup_key(row) for row in obj.linker_fixups],
        "externals": obj.externals,
        "external_scopes": obj.external_scopes,
        "communals": obj.communals,
    }


def full_module_control(manifest: dict) -> dict:
    module = manifest["modules"]["root:0894"]
    source_path = ROOT / module["source"]
    original, source_pin = dos.pin(source_path, module["source_sha256"])
    text = original.decode("ascii")
    edits = []
    candidate = text
    for name in NAMES:
        before = f"extern unsigned char far {name}[100];"
        after = f"unsigned char far {name}[100];"
        if candidate.count(before) != 1:
            raise RuntimeError(f"expected exactly one typed extern in source: {before}")
        candidate = candidate.replace(before, after)
        edits.append({"before": before, "after": after, "count": 1})
    candidate_path = OUT / "root0894-coordinate-owner-candidate.c"
    candidate_path.write_text(candidate, encoding="ascii")
    control_result = compiler.compile_c(text, module["profile"], module["flags"],
                                        basename="UNIT", keep=True)
    candidate_result = compiler.compile_c(candidate, module["profile"], module["flags"],
                                          basename="UNIT", keep=True)
    if not control_result.ok or not candidate_result.ok:
        raise RuntimeError("root:0894 whole-module control/candidate compilation failed")
    control = OmfReader(communals=True).read(control_result.obj)
    owner = OmfReader(communals=True).read(candidate_result.obj)
    cp, op = object_packet(control), object_packet(owner)
    control_scope_map = dict(zip(control.externals, control.external_scopes))
    candidate_scope_map = dict(zip(owner.externals, owner.external_scopes))
    control_names = set(control.externals)
    candidate_names = set(owner.externals)
    removed_externals = sorted(control_names - candidate_names)
    added_externals = sorted(candidate_names - control_names)
    scopes = [{"name": name, "control": control_scope_map.get(name, "external"),
               "candidate": candidate_scope_map.get(name, "communal")}
              for name in sorted(set(control_scope_map) | set(candidate_scope_map))
              if control_scope_map.get(name) != candidate_scope_map.get(name)]
    expected_scopes = [{"name": "_" + name, "control": "external", "candidate": "communal"}
                       for name in sorted(NAMES)]
    communal_rows = [row for row in owner.communals if row["name"] in {"_" + n for n in NAMES}]
    expected_commons = [{"name": "_" + name, "kind": "far", "count": 100,
                         "element_size": 1, "length": 100} for name in NAMES]
    actual_commons = [{"name": row["name"], "kind": row["kind"],
                       "count": row.get("count"), "element_size": row.get("element_size"),
                       "length": row["length"]} for row in communal_rows]
    checks = {
        "all_segment_bytes_equal": cp["segments"] == op["segments"],
        "segment_definitions_extents_groups_equal": all(cp[key] == op[key] for key in
                                                          ("segment_defs", "segment_lengths", "groups")),
        "publics_equal": cp["publics"] == op["publics"],
        "local_publics_equal": cp["local_publics"] == op["local_publics"],
        "ordered_fixups_equal": cp["ordered_fixups"] == op["ordered_fixups"],
        "external_name_sets_equal": control_names == candidate_names,
        "only_requested_external_scopes_changed": scopes == expected_scopes,
        "exact_two_far_byte_array_commons": actual_commons == expected_commons,
    }
    contribution_delta_checks_pass = all(checks.values())
    return {
        "module": "root:0894", "source": source_pin, "manifest_object_sha256": module["object_sha256"],
        "profile": module["profile"], "flags": module["flags"], "declaration_edits": edits,
        "candidate_source": str(candidate_path.relative_to(ROOT)).replace("\\", "/"),
        "control_object_sha256": sha(control_result.obj),
        "fresh_control_matches_manifest_object": sha(control_result.obj) == module["object_sha256"],
        "candidate_object_sha256": sha(candidate_result.obj),
        "candidate_object_size_delta": len(candidate_result.obj) - len(control_result.obj),
        "checks": checks, "contribution_delta_checks_pass": contribution_delta_checks_pass,
        "all_checks_pass": contribution_delta_checks_pass,
        "external_name_order_equal": control.externals == owner.externals,
        "control_segments": cp["segments"], "candidate_segments": op["segments"],
        "communals": actual_commons, "changed_external_scopes": scopes,
        "removed_externals": removed_externals, "added_externals": added_externals,
        "game_module_linked": False,
    }


def compile_fixture(label: str, source: str, flags: list[str], basename: str) -> tuple[bytes, dict, object]:
    source_path = OUT / "sources" / f"{label}.c"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(source, encoding="ascii")
    result = compiler.compile_c(source, PROFILE, flags, basename=basename, keep=True)
    if not result.ok:
        raise RuntimeError(f"{label} compile failed: {result.log}")
    obj = OmfReader(communals=True).read(result.obj)
    return result.obj, pin(source_path), obj


def case_consumer_source(kind: str) -> str:
    return {"direct": DIRECT_CONSUMER, "saverec": SAVEREC_CONSUMER,
            "signed": SIGNED_VIEW_CONSUMER, "initializer": INITIALIZER_CONSUMER}[kind]


def run_case(profile: str, case: str, consumer_obj: bytes, owner_obj: bytes,
             runtimes: list[dict], linker: dict, runner: dict, tool_dir: Path,
             aliases: dict[str, int] | None = None) -> dict:
    folder = OUT / profile / case
    folder.mkdir(parents=True, exist_ok=True)
    for name in ("PROBE.EXE", "PROBE.MAP", "RUN.LOG", "LINK.LOG"):
        (folder / name).unlink(missing_ok=True)
    (folder / "CRT.OBJ").write_bytes(consumer_obj)
    (folder / "OWNER.OBJ").write_bytes(owner_obj)
    for row in runtimes:
        shutil.copyfile(row["path"], folder / Path(row["path"]).name.upper())
    alias_rows = aliases or {}
    script = ("OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n"
              "LIBRARY LLIBCR, LIBH\r\nFILE CRT\r\nBEGINAREA\r\n"
              "SECTION FILE OWNER\r\nENDAREA\r\n")
    for alias_name, (target, delta) in {
            "probeDeadAntX": (NAMES[0], alias_rows.get(NAMES[0], 0)),
            "probeDeadAntY": (NAMES[1], alias_rows.get(NAMES[1], 0)),
    }.items():
        if case in {"typed_unsigned_byte_exact_base_and_extent", "wrong_base_plus1",
                    "wrong_extent_101", "wrong_signed_byte_view"}:
            script += f"DEFINE _{alias_name} = _{target}" + (f" + {delta}" if delta else "") + "\r\n"
    (folder / "PROBE.LNK").write_bytes(script.encode("ascii"))
    (folder / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (folder / "RUN.BAT").write_bytes((
        f'@echo off\r\nD:\\{linker["executable"]} @PROBE.LNK < NUL > LINK.LOG\r\n'
        "PROBE.EXE > RUN.LOG\r\n").encode("ascii"))
    config = []
    for section, settings in runner["conf"].items():
        config += ["[" + section + "]"] + [f"{key}={value}" for key, value in settings.items()]
    config += ["[autoexec]", f'mount c "{folder}"', f'mount d "{tool_dir}" -ro',
               "c:", "call RUN.BAT", "exit"]
    config_path = folder / "dosbox.conf"
    config_path.write_text("\n".join(config) + "\n", encoding="utf-8")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    timed_out = False
    try:
        result = subprocess.run([runner["path"], "-conf", str(config_path), "-fastlaunch",
                                 "-exit", "-nomenu"], cwd=folder, env=env,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                timeout=60, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired:
        timed_out = True
        result = type("TimedOut", (), {"returncode": -1})()
    log = folder / "RUN.LOG"
    actual = log.read_text(encoding="latin1").strip() if log.exists() else "NO RUN.LOG"
    link_log = folder / "LINK.LOG"
    return {"linker": profile, "case": case, "actual": actual,
            "expected": "PASS" if case in {"typed_unsigned_byte_exact_base_and_extent", "SaveRec_direct_byte_view"} else "FAIL",
            "passed": actual == ("PASS" if case in {"typed_unsigned_byte_exact_base_and_extent", "SaveRec_direct_byte_view"} else "FAIL")
                      and result.returncode == 0 and not timed_out,
            "host_exit": result.returncode, "timed_out": timed_out,
            "alias_deltas_bytes": alias_rows,
            "link_log_tail": link_log.read_text(encoding="latin1", errors="replace")[-900:]
                            if link_log.exists() else ""}


def runtime_probe(manifest: dict) -> dict:
    toolchain = compiler.toolchain()
    profile_info = compiler.verify_profile(PROFILE)
    flags = FIXTURE_FLAGS + profile_info.get("required_flags", [])
    if "/Zi" in flags:
        raise RuntimeError("clean storage-shape owner fixtures must omit /Zi")
    compiler_pins = [pin(Path(profile_info["directory"]) / rel, digest)
                     for rel, digest in profile_info["files"].items()]
    runner_ref = (toolchain.get("runners", {}).get(profile_info.get("runner"))
                  if profile_info.get("runner") else toolchain.get("runner"))
    if not runner_ref:
        raise RuntimeError("pinned MSC compiler runner is absent")
    compiler_runner_pin = pin(Path(runner_ref["path"]), runner_ref["sha256"])

    owner_raw, owner_pin, owner_obj = compile_fixture("typed_owner", OWNER_SOURCE, flags, "DAOWNER")
    extent_raw, extent_pin, extent_obj = compile_fixture("wrong_extent_101", WRONG_EXTENT_SOURCE, flags, "DAEXTENT")
    initialized_raw, initialized_pin, initialized_obj = compile_fixture(
        "initialized_nonzero", INITIALIZED_SOURCE, flags, "DAINIT")
    wrong_element_raw, wrong_element_pin, wrong_element_obj = compile_fixture(
        "wrong_two_byte_element", WRONG_ELEMENT_SOURCE, flags, "DAWORD")
    owner_rows = [row for row in owner_obj.communals if row["name"] in {"_" + n for n in NAMES}]
    expected_rows = [{"name": "_" + name, "kind": "far", "count": 100,
                      "element_size": 1, "length": 100} for name in NAMES]
    measured_rows = [{"name": row["name"], "kind": row["kind"], "count": row["count"],
                      "element_size": row["element_size"], "length": row["length"]}
                     for row in owner_rows]
    extent_rows = [{"name": row["name"], "kind": row["kind"], "count": row["count"],
                    "element_size": row["element_size"], "length": row["length"]}
                   for row in extent_obj.communals if row["name"] in {"_" + n for n in NAMES}]
    expected_extent = [{"name": "_" + NAMES[0], "kind": "far", "count": 101,
                        "element_size": 1, "length": 101},
                       {"name": "_" + NAMES[1], "kind": "far", "count": 100,
                        "element_size": 1, "length": 100}]
    init_target = "_" + NAMES[0]
    initialized_common_names = {row["name"] for row in initialized_obj.communals}
    initialized_public_names = {row["name"] for row in initialized_obj.publics}
    wrong_element_rows = [{"name": row["name"], "kind": row["kind"], "count": row["count"],
                           "element_size": row["element_size"], "length": row["length"]}
                          for row in wrong_element_obj.communals
                          if row["name"] in {"_" + n for n in NAMES}]
    if measured_rows != expected_rows or extent_rows != expected_extent:
        raise RuntimeError(f"unexpected array communal shape: owner={measured_rows}, extent={extent_rows}")
    if init_target in initialized_common_names or init_target not in initialized_public_names:
        raise RuntimeError("initialized control did not leave far communal storage")

    consumers = {}
    for label, kind, basename in (("direct", "direct", "DABASE"),
                                  ("saverec", "saverec", "DASAVE"),
                                  ("signed", "signed", "DASIGN"),
                                  ("initializer", "initializer", "DAZERO")):
        raw, source_pin, obj = compile_fixture(f"consumer_{label}", case_consumer_source(kind), flags, basename)
        consumers[label] = {"object": raw, "source_pin": source_pin,
                            "object_sha256": sha(raw), "externals": obj.externals}

    runtimes = list(manifest["runtime"]["libraries"].values())
    runtime_pins = [pin(Path(row["path"]), row["sha256"]) for row in runtimes]
    runner = toolchain["runners"]["dosbox-x"]
    dosbox_pin = pin(Path(runner["path"]), runner["sha256"])
    cases = []
    specs = [
        ("typed_unsigned_byte_exact_base_and_extent", consumers["direct"]["object"], owner_raw, {}),
        ("SaveRec_direct_byte_view", consumers["saverec"]["object"], owner_raw, {}),
        ("wrong_base_plus1", consumers["direct"]["object"], owner_raw, {NAMES[0]: 1}),
        ("wrong_extent_101", consumers["direct"]["object"], extent_raw, {}),
        ("wrong_signed_byte_view", consumers["signed"]["object"], owner_raw, {}),
        ("initialized_nonzero_owner", consumers["initializer"]["object"], initialized_raw, {}),
    ]
    linker_pins = {}
    for profile_name in ("rtlink400", "rtlink610"):
        linker = toolchain["linkers"][profile_name]
        linker_pins[profile_name] = [pin(Path(linker["directory"]) / rel, digest)
                                     for rel, digest in linker["files"].items()]
        tool_dir = compiler.pinned_tree(linker)
        for case, consumer, owner, deltas in specs:
            cases.append(run_case(profile_name, case, consumer, owner, runtimes,
                                  linker, runner, tool_dir, deltas))
    per_linker = {}
    for profile_name in ("rtlink400", "rtlink610"):
        rows = [row for row in cases if row["linker"] == profile_name]
        per_linker[profile_name] = {
            "pass_count": sum(row["actual"] == "PASS" for row in rows),
            "fail_count": sum(row["actual"] == "FAIL" for row in rows),
            "all_expected_cases_pass": len(rows) == len(specs) and all(row["passed"] for row in rows),
        }
    return {
        "profile": PROFILE, "flags": flags, "compiler_files": compiler_pins,
        "compiler_runner": compiler_runner_pin, "runtime_libraries": runtime_pins,
        "dosbox_runner": dosbox_pin, "linkers": linker_pins,
        "typed_owner_source": owner_pin, "typed_owner_object_sha256": sha(owner_raw),
        "typed_owner_communals": measured_rows,
        "wrong_extent_source": extent_pin, "wrong_extent_communals": extent_rows,
        "initialized_owner_source": initialized_pin,
        "initialized_owner_has_no_target_communal": init_target not in initialized_common_names,
        "initialized_owner_target_is_public": init_target in initialized_public_names,
        "wrong_element_source": wrong_element_pin, "wrong_element_communals": wrong_element_rows,
        "consumers": {label: {"source": row["source_pin"],
                               "object_sha256": row["object_sha256"],
                               "externals": row["externals"]}
                      for label, row in consumers.items()},
        "cases": cases, "per_linker": per_linker,
        "all_expected_cases_pass": all(row["all_expected_cases_pass"] for row in per_linker.values()),
        "game_stubs": 0, "original_game_objects_linked": False,
    }


def write_markdown(report: dict) -> str:
    own = report["source_ownership"]
    ring = report["ring_index_and_lifecycle"]
    runtime = report["runtime"]
    lines = [
        "# Dead-ant coordinate-ring storage review", "",
        "Status: source-only research in ignored scratch. Canonical files, tools, tests, mandatory packets, and Git state were not modified.", "",
        "## Source ownership and extent", "",
        "`DeadAntHere` in `src/root/m0894.c` is the source-functional owner. It advances the saved ring index, reads the prior x/y bytes, then writes the new coordinates at the same ring slot in both terrain branches. The canonical declarations are `unsigned char far [100]`; S09 exposes unsized unsigned-byte address views only in its persistent SaveRec table.", "",
        f"Each array has one `{own['save_rows'][NAMES[0]][0]['size']} x {own['save_rows'][NAMES[0]][0]['count']}` SaveRec row (100 bytes). The two adjacent registered symbols begin exactly at the measured end offsets; their bases do not establish the extents. Whole-module OMF and runtime fixtures independently measure/check the 100-byte byte arrays.", "",
        f"The source scan covered {own['canonical_module_count']} canonical module sources plus {own['strict_index_entries']} strict-effective sources ({own['unique_scanned_sources']} unique source paths). Registry scan: no alternate exact-base aliases and no registered symbol inside either half-open extent.", "",
        "## Lifecycle and failure domain", "",
        ring["summary"], "",
        "The arrays and ring index have no source reset in `InitSimYard`/`RandYard`; startup tentative-definition zero-fill is a separate clean-runtime result. `LoadGame` calls its yard reset helper before sequential SaveRec reads. A short read may mutate a prefix of a record before the length check fails and bypasses the successful-load rebuild path. Loaded ring/index/coordinate contents are not validated. Negative ring indices and byte coordinates outside `MapA` bounds remain unchecked source/layout concerns; this review establishes storage extent, not safety for arbitrary malformed saves.", "",
        "## Whole-module compile and runtime controls", "",
        f"Fresh {report['whole_module']['profile']} control/candidate contribution comparison: {report['whole_module']['contribution_delta_checks_pass']}. The fresh control hash does not match the manifest object hash, so this probe does not claim historical object reproducibility. Segment payloads/extents, publics, local publics, and ordered fixups are preserved; the external-name set is unchanged, with the two requested scope changes. External-name ordering equal: {report['whole_module']['external_name_order_equal']}. The source candidate adds two far byte-array communals.", "",
        "| Linker | Unsigned byte/base/extent | SaveRec byte view | Wrong base | 101-byte extent | Signed view | Initialized owner |",
        "|---|---|---|---|---|---|---|",
    ]
    for linker, summary in runtime["per_linker"].items():
        rows = [row for row in runtime["cases"] if row["linker"] == linker]
        by_name = {row["case"]: row["actual"] for row in rows}
        lines.append("| " + linker + " | " + " | ".join(by_name[name] for name in (
            "typed_unsigned_byte_exact_base_and_extent", "SaveRec_direct_byte_view",
            "wrong_base_plus1", "wrong_extent_101", "wrong_signed_byte_view",
            "initialized_nonzero_owner")) + " |")
        if not summary["all_expected_cases_pass"]:
            lines.append(f"<!-- unexpected runtime results: {summary} -->")
    lines += ["", "No game module stubs or original code bytes were linked. The deliberately malformed loaded-index/layout domain remains unclosed.", ""]
    return "\n".join(lines)


def main() -> int:
    denied = dos.install_input_guard()
    manifest_raw, manifest_pin = dos.pin(ROOT / "layout/manifest.json")
    symbols_raw, symbols_pin = dos.pin(ROOT / "layout/symbols.json")
    toolchain_pin = pin(ROOT / "layout/toolchain.json")
    manifest = json.loads(manifest_raw)
    symbols = json.loads(symbols_raw)
    source_rows, receipt_pins = source_inventory(manifest, manifest_pin)
    refs, scanned_source_pins = scan_sources(source_rows)
    save_rows = save_table_rows()
    registry = registry_audit(symbols)

    root_source = (ROOT / "src/root/m0894.c").read_text(encoding="ascii")
    root_decls = {}
    for name in NAMES:
        exact = f"extern unsigned char far {name}[100];"
        if root_source.count(exact) != 1:
            raise RuntimeError(f"root source typed extent declaration missing or duplicated: {name}")
        root_decls[name] = exact
    s09_source = (ROOT / SAVE_PATH).read_text(encoding="ascii")
    save_decls = {}
    for name in NAMES:
        exact = f"extern unsigned char far {name}[];"
        if s09_source.count(exact) != 1:
            raise RuntimeError(f"S09 address-only byte declaration missing or duplicated: {name}")
        save_decls[name] = exact
        if not any(row["category"] == "SaveRec_exact_base" for row in refs[name]["references"]):
            raise RuntimeError(f"source-wide scan lacks the exact SaveRec base for {name}")
        unexpected = [row for row in refs[name]["references"]
                      if row["category"] in {"address_escape", "expression"}]
        if unexpected:
            raise RuntimeError(f"unclassified or escaping source view for {name}: {unexpected}")

    dead_ant_body = root_source[root_source.find("void far DeadAntHere("):]
    expected_ring_lines = [
        "if (++fd_50F6_0476 >= 100)",
        "fd_50F6_0476 = 0;",
        "oldX = fd_50F6_037C[fd_50F6_0476];",
        "oldY = fd_50F6_0404[fd_50F6_0476];",
        "fd_50F6_037C[fd_50F6_0476] = x;",
        "fd_50F6_0404[fd_50F6_0476] = y;",
    ]
    if any(dead_ant_body.count(text) < (2 if " = x;" in text or " = y;" in text else 1)
           for text in expected_ring_lines):
        raise RuntimeError("DeadAntHere ring read/write/normalization source changed")
    index_refs = refs[RING_INDEX]["references"]
    assignments = [row["text"] for row in index_refs
                   if row["source"] != SAVE_PATH and
                   re.search(r"\b" + re.escape(RING_INDEX) + r"\s*=(?!=)", row["text"])]
    if assignments != ["fd_50F6_0476 = 0;"]:
        # The only assignment is DeadAntHere's >=100 ring wrap; no lifecycle reset exists.
        raise RuntimeError(f"unexpected independent source reset/assignment to saved ring index: {assignments}")

    module = manifest["modules"]["root:0894"]
    if module.get("scaffold"):
        raise RuntimeError("root:0894 is not a complete source module candidate")
    whole = full_module_control(manifest)
    whole["candidate_source_pin"] = pin(ROOT / whole["candidate_source"])
    runtime = runtime_probe(manifest)
    checks = {
        "both_root_fixed_extent_unsigned_byte_declarations": len(root_decls) == 2,
        "both_s09_unsized_serialization_byte_declarations": len(save_decls) == 2,
        "both_exact_100_byte_saverec_rows": all(len(save_rows[name]) == 1 and save_rows[name][0]["bytes"] == 100 for name in NAMES),
        "source_scan_has_no_extra_pointer_escapes": all(not [r for r in refs[name]["references"] if r["category"] in {"address_escape", "expression"}] for name in NAMES),
        "registered_alias_interior_audit_clear": all(not registry[name]["registered_interior_names"] and
                                                       registry[name]["same_base_names"] == [{"table": "data", "name": name, "off": registry[name]["range_half_open"][0], "alias_of": None}]
                                                       for name in NAMES),
        "whole_module_candidate_preserves_fresh_control_contributions": whole["contribution_delta_checks_pass"],
        "both_linkers_clean_startup_and_byteview_controls_pass": runtime["all_expected_cases_pass"],
        "oracle_reads_denied": not denied,
    }
    report = {
        "schema": "simant-dos-dead-ant-coordinate-owner-review-v1",
        "status": "RESEARCH_ONLY",
        "scope": {"members": list(NAMES), "storage_candidate_type": "unsigned char far [100]",
                  "functional_owner_module": "root:0894", "functional_owner_function": "DeadAntHere",
                  "canonical_source_and_manifest_modified": False, "production_tools_or_tests_modified": False,
                  "mandatory_packet_created": False, "game_stubs": 0, "original_code_bytes_used": False},
        "source_ownership": {
            "canonical_module_count": len(manifest["modules"]),
            "strict_index_entries": 29,
            "unique_scanned_sources": len(source_rows),
            "full_canonical_and_strict_effective_source_pins": scanned_source_pins,
            "strict_receipt_pins": receipt_pins,
            "references": refs,
            "root_owner_declarations": root_decls,
            "S09_serialization_declarations": save_decls,
            "save_rows": save_rows,
            "registry": registry,
            "facts": {
                "functional_owner": "DeadAntHere rotates through an int ring index, reads the old x/y byte at that slot, and replaces both coordinates in each terrain branch. No other canonical/strict source references the arrays except their S09 SaveRec declaration/records.",
                "reset": "No source reset or initializer for either byte array or the ring index was found. The first program startup begins with zero-filled tentative definitions under the tested MSC/RTLink runtimes. RandYard/InitSimYard do not assign these arrays; LoadGame calls RandYard before the SaveRec read loop.",
                "save_load": "S09 records each array as size=1,count=100 at its exact address. Generic SaveGame writes count*size bytes. LoadGame reads records sequentially into those addresses. A short read can mutate an array prefix before reporting failure; failure bypasses the successful-load postprocessing path.",
                "index_and_domain": "Valid ring values 0..99 are maintained by increment and a >=100 wrap. No negative-index guard exists; an invalid loaded value <=-2 can remain negative after increment. Loaded byte coordinates and DeadAntHere arguments are not checked against MapA dimensions. Malformed save/index/map behavior remains an independent layout/safety gate.",
                "extent_basis": "Fixed unsigned-char[100] canonical externs, independent {1,100,&array} SaveRec records, measured MSC far COMDEF element count/size/length, and clean runtime one-past guard adjacency all support exactly 100 bytes. Adjacent registered addresses are recorded only as a boundary cross-check, not as the extent premise.",
            },
        },
        "ring_index_and_lifecycle": {
            "index_symbol": RING_INDEX,
            "source_references": refs[RING_INDEX]["references"],
            "explicit_assignments": assignments,
            "summary": "DeadAntHere increments the saved signed-int ring cursor and only wraps values >=100 to zero before indexing either array. Valid indices therefore rotate through 0..99, but there is no negative-index guard. The cursor is a separate two-byte SaveRec record. No array or cursor reset appears in InitSimYard/RandYard; LoadGame calls RandYard before loading records but does not clear these arrays. SaveRec reads are in-place and sequential: a short read may mutate a byte-array prefix before the error branch skips successful-load postprocessing. Corrupt/partial saved indices and coordinates remain unchecked.",
            "load_order_note": "The two 100-byte coordinate rows precede the separately saved cursor row; failed reads can therefore leave newly loaded coordinate bytes paired with the prior cursor value.",
        },
        "inputs": [manifest_pin, symbols_pin, toolchain_pin, *receipt_pins,
                   *scanned_source_pins, whole["candidate_source_pin"]],
        "whole_module": whole,
        "runtime": runtime,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "denied_oracle_reads": denied,
    }
    provider_path = OUT / "typed-owner-provider-candidate.c"
    provider_path.write_text(PROVIDER_CANDIDATE_SOURCE, encoding="ascii")
    report["probe_source"] = pin(Path(__file__))
    report["typed_owner_provider_candidate"] = pin(provider_path)
    report["typed_owner_provider_source"] = pin(PROVIDER_PATH)
    report["inputs"].extend((report["probe_source"], report["typed_owner_provider_candidate"]))
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (OUT / "report.md").write_text(write_markdown(report), encoding="utf-8")
    print(json.dumps({"all_checks_pass": report["all_checks_pass"], "checks": checks,
                      "whole_module": whole["all_checks_pass"],
                      "runtime_cases": len(runtime["cases"]),
                      "per_linker": runtime["per_linker"],
                      "canonical_source_module_count": len(manifest["modules"]),
                      "unique_source_scan_count": len(source_rows),
                      "denied_oracle_reads": denied,
                      "report": str(OUT / "report.json")}, indent=2))
    return 0 if report["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
