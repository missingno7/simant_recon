"""Rebuild a bounded source audit and fresh MSC/RTLink owner fixtures.

No original executable/data bytes are read. Every run writes to a unique,
immutable directory under build/workers/dos_ant_histogram_v22/.
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

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "work/source-only-dos"
PROVIDER = PACKAGE / "providers/ant-class-histogram.c"
OUT_ROOT = ROOT / "build/workers/dos_ant_histogram_v22"
OWNER_FLAGS = ["/AL", "/Os", "/Gs"]
CONSUMER_FLAGS = ["/AL", "/Os", "/Gs"]
TOKEN = "fd_50F6_0EB6"
COMMUNAL = "_fd_50f6_0eb6"
EXPECTED_SOURCE_DECLARATION = "int far fd_50F6_0EB6[32];"

sys.path.insert(0, str(ROOT / "tools"))
import compiler  # noqa: E402
import modules  # noqa: E402
from omf import OmfReader  # noqa: E402


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def path_sha(path: Path) -> str:
    return sha(path.read_bytes())


def receipt(path: Path, label: str | None = None) -> dict:
    raw = path.read_bytes()
    if label is None:
        try:
            label = path.relative_to(ROOT).as_posix()
        except ValueError:
            label = str(path)
    return {"path": label, "sha256": sha(raw), "size": len(raw)}


def file_receipt(path: Path) -> dict:
    return receipt(path)


def source_inventory() -> dict:
    manifest_path = ROOT / "layout/manifest.json"
    symbols_path = ROOT / "layout/symbols.json"
    behavior_path = ROOT / "evidence/behavior/manifest.json"
    strict_path = PACKAGE / "static-completeness/index-v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    strict = json.loads(strict_path.read_text(encoding="utf-8"))
    if len(manifest["modules"]) != 127:
        raise RuntimeError("expected 127 canonical manifest modules")
    if len(strict.get("entries", {})) != 29:
        raise RuntimeError("expected 29 strict-effective entries")
    if path_sha(behavior_path) != strict["registry"]["sha256"]:
        raise RuntimeError("strict index references a different behavior registry")

    selected: dict[str, dict] = {}
    for module_key, row in manifest["modules"].items():
        path = ROOT / row["source"]
        actual = path_sha(path)
        if actual != row["source_sha256"]:
            raise RuntimeError(f"canonical source pin mismatch: {row['source']}")
        selected[row["source"]] = {"kind": "canonical", "module": module_key,
                                    "sha256": actual, "size": path.stat().st_size}

    strict_sources = {}
    for name, row in strict["entries"].items():
        receipt_path = ROOT / row["path"]
        if path_sha(receipt_path) != row["sha256"]:
            raise RuntimeError(f"strict receipt pin mismatch: {name}")
        item = json.loads(receipt_path.read_text(encoding="utf-8"))
        if item.get("status") != "BEHAVIOR_EXACT_CONFIRMED":
            raise RuntimeError(f"strict receipt is not confirmed: {name}")
        source = item.get("source_override") or item["registered_source"]
        source_path = ROOT / source["path"]
        actual = path_sha(source_path)
        if actual != source["sha256"]:
            raise RuntimeError(f"strict effective source pin mismatch: {name}")
        selected[source["path"]] = {"kind": "strict_effective", "entry": name,
                                     "sha256": actual, "size": source_path.stat().st_size,
                                     "receipt_path": row["path"],
                                     "receipt_sha256": row["sha256"]}
        strict_sources[name] = {"path": source["path"], "sha256": actual,
                                "receipt_path": row["path"],
                                "receipt_sha256": row["sha256"]}
    if len(selected) != 156:
        raise RuntimeError(f"expected 156 unique selected sources, found {len(selected)}")

    hits = []
    numeric_hits = []
    declaration_hits = []
    pointer_escapes = []
    name_re = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(TOKEN) + r"(?![A-Za-z0-9_])")
    # Direct symbolic/hex spellings that could name this indexed origin in C,
    # inline assembly, or readable MASM. Decimal/layout interpretation is not
    # guessed from unrelated immediates.
    numeric_re = re.compile(
        r"(?i)(?<![A-Za-z0-9_])(?:0x0*eb6|0*eb6h)(?![A-Za-z0-9_])|"
        r"(?<![A-Za-z0-9_])50f6\s*:\s*0*eb6(?![A-Za-z0-9_])"
    )
    for rel_path, meta in selected.items():
        path = ROOT / rel_path
        if path.suffix.lower() not in (".c", ".asm"):
            continue
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for line_no, line in enumerate(lines, 1):
            if name_re.search(line):
                item = {"source": rel_path, "line": line_no, "text": line.strip(),
                        "kind": meta["kind"]}
                hits.append(item)
                if re.search(r"^\s*(?:extern\s+)?int\s+far\s+" + re.escape(TOKEN) + r"\s*\[", line):
                    declaration_hits.append(item)
                if re.search(r"(?<!&)\&(?!&)\s*" + re.escape(TOKEN), line):
                    pointer_escapes.append(item)
            if numeric_re.search(line):
                numeric_hits.append({"source": rel_path, "line": line_no,
                                     "text": line.strip(), "kind": meta["kind"]})

    symbol_table = json.loads(symbols_path.read_text(encoding="utf-8"))["data"]
    target = symbol_table.get(TOKEN)
    if not target or target.get("seg") != 0x50F6 or target.get("off") != 0x0EB6:
        raise RuntimeError("registered histogram symbol row changed")
    extent_end = 0x0EB6 + 32 * 2
    internal_names = [
        {"name": name, "offset": f"{row['off']:04X}"}
        for name, row in symbol_table.items()
        if row.get("seg") == 0x50F6 and 0x0EB6 <= row.get("off", -1) < extent_end
    ]

    # CountAnts is the only named consumer in the selected set. Keep the
    # source-derived expression facts separate from a legal-input guarantee.
    countants_path = ROOT / "src/root/m0BE8.c"
    countants_lines = countants_path.read_text(encoding="utf-8").splitlines()
    direct_lines = [
        {"line": n, "text": line.strip()}
        for n, line in enumerate(countants_lines, 1)
        if name_re.search(line)
    ]
    canonical_decl = [item for item in declaration_hits
                      if item["source"] == "src/root/m0BE8.c"]
    if len(canonical_decl) != 1 or len(hits) != 21:
        raise RuntimeError("histogram source view count changed; inspect before use")

    return {
        "scope": "127 exact manifest module sources + 29 confirmed strict-effective source paths; superseded experiments excluded",
        "source_count": len(selected),
        "selected_sources": selected,
        "strict_effective_sources": strict_sources,
        "source_pins": {
            "layout/manifest.json": receipt(manifest_path),
            "layout/symbols.json": receipt(symbols_path),
            "evidence/behavior/manifest.json": receipt(behavior_path),
            "work/source-only-dos/static-completeness/index-v1.json": receipt(strict_path),
        },
        "registered_symbol": {"name": TOKEN, "segment": "50F6", "offset": "0EB6",
                               "grounding": target["grounding"]},
        "candidate_interval": {"start": "50F6:0EB6", "end_exclusive": "50F6:0EF6",
                               "bytes_from_c_declaration": 64},
        "registered_names_inside_interval": internal_names,
        "named_source_views": hits,
        "numeric_address_spellings": numeric_hits,
        "address_taken_lines": pointer_escapes,
        "unindexed_or_decayed_name_occurrences": [
            item for item in hits
            if not re.search(r"\b" + re.escape(TOKEN) + r"\s*\[", item["text"])
        ],
        "direct_source_lines": direct_lines,
        "declaration": canonical_decl[0],
        "save_record_or_pointer_table_escape": False,
        "index_domain": {
            "list_value_path": "CountAnts assigns unsigned-char AlistT/BlistT/RlistT values to signed int v, skips zero, then indexes v >> 3; byte values 1..255 map to 0..31",
            "other_index_path": "CountAnts also indexes with fd_50F6_04C2 >> 3 and (fd_50F6_04C2 | 0x80) >> 3",
            "other_index_bound": "not established by this owner/type/extent audit; malformed state and out-of-range indices are not used as storage evidence",
        },
        "historical_layout_or_initialization_claim": False,
    }


def compile_c(run_dir: Path, name: str, text: str, flags: list[str]) -> dict:
    fixture_dir = run_dir / "fixtures"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    src_path = fixture_dir / f"{name}.c"
    obj_path = fixture_dir / f"{name}.OBJ"
    src_path.write_bytes(text.encode("ascii"))
    result = compiler.compile_c(text, "msc600ax", flags, basename=name)
    if not result.ok or result.obj is None:
        raise RuntimeError(f"{name} compile failed:\n{result.log}")
    obj_path.write_bytes(result.obj)
    omf = OmfReader(communals=True).read(result.obj)
    return {
        "source": file_receipt(src_path),
        "object": file_receipt(obj_path),
        "object_bytes": result.obj,
        "flags": list(flags),
        "communals": list(omf.communals),
        "matching_communals": [row for row in omf.communals
                               if row["name"].lower() == COMMUNAL],
        "publics": list(omf.publics),
        "segments": [{k: row.get(k) for k in
                      ("index", "name", "class", "length", "alignment", "combine", "big")}
                     for row in omf.segment_defs],
    }


def main_source(alias: bool = True) -> str:
    alias_decl = "extern int far HistogramProbeAlias[32];\n" if alias else ""
    alias_check = (
        "if ((void far *)&fd_50F6_0EB6[0] != (void far *)&HistogramProbeAlias[0]) {\n"
        "        puts(\"REJECTED_BASE\"); return 0;\n    }\n" if alias else ""
    )
    return f'''extern int far fd_50F6_0EB6[32];
{alias_decl}extern int far puts(char far *text);
int main(void)
{{
    int i;
    int value;
    unsigned char far *raw;
    if (sizeof(fd_50F6_0EB6[0]) != 2 || sizeof(fd_50F6_0EB6) != 64) {{
        puts("REJECTED_SIZE"); return 0;
    }}
    {alias_check}for (i = 0; i < 32; i++) {{
        if (fd_50F6_0EB6[i] != 0) {{ puts("REJECTED_CRT_ZERO"); return 0; }}
    }}
    fd_50F6_0EB6[0] = -1;
    for (i = 1; i < 32; i++) fd_50F6_0EB6[i] = 0x0102 + i * 7;
    raw = (unsigned char far *)&fd_50F6_0EB6[0];
    if (fd_50F6_0EB6[0] != -1 || raw[0] != 0xff || raw[1] != 0xff) {{
        puts("REJECTED_SIGNED_OR_RAW"); return 0;
    }}
    for (i = 1; i < 32; i++) {{
        value = 0x0102 + i * 7;
        if (fd_50F6_0EB6[i] != value || raw[2 * i] != (value & 0xff) ||
            raw[2 * i + 1] != ((value >> 8) & 0xff)) {{
            puts("REJECTED_WORD_OR_RAW"); return 0;
        }}
    }}
    puts("PASS"); return 0;
}}
'''


def unsigned_view_source() -> str:
    return r'''extern unsigned int far fd_50F6_0EB6[32];
extern int far HistogramProbeAlias[32];
extern int far puts(char far *text);
int main(void)
{
    if ((void far *)&fd_50F6_0EB6[0] != (void far *)&HistogramProbeAlias[0]) {
        puts("REJECTED_BASE"); return 0;
    }
    fd_50F6_0EB6[0] = -1;
    if (fd_50F6_0EB6[0] < 0) { puts("FAIL_UNEXPECTED_SIGNED"); return 0; }
    puts("REJECTED_UNSIGNED_VIEW"); return 0;
}
'''


def map_symbols(map_text: str, names: tuple[str, ...]) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = {}
    pattern = re.compile(r"\s*([0-9A-Fa-f]{4}):([0-9A-Fa-f]{4})\s+(Res|Ovl|U)\s+(_\S+)")
    for line in map_text.splitlines():
        match = pattern.match(line)
        if match and match.group(4) in names:
            result.setdefault(match.group(4), []).append({
                "segment": int(match.group(1), 16),
                "offset": int(match.group(2), 16),
                "state": match.group(3),
            })
    return result


def run_case(run_dir: Path, profile: str, case: dict, owner_obj: bytes,
             consumer_obj: bytes, runtime_rows: list[dict], linker: dict,
             runner: dict, tool_dir: Path) -> dict:
    case_dir = run_dir / "rtlink" / profile / case["name"]
    case_dir.mkdir(parents=True, exist_ok=False)
    (case_dir / "CRT.OBJ").write_bytes(consumer_obj)
    (case_dir / "OWNER.OBJ").write_bytes(owner_obj)
    for row in runtime_rows:
        shutil.copyfile(row["path"], case_dir / Path(row["path"]).name.upper())

    alias_delta = case.get("alias_delta", 0)
    alias_expr = f" + {alias_delta:X}" if alias_delta else ""
    link_text = (
        "OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n"
        "LIBRARY LLIBCR, LIBH\r\nFILE CRT\r\nBEGINAREA\r\n"
        "SECTION FILE OWNER\r\nENDAREA\r\n"
        f"DEFINE _HistogramProbeAlias = {COMMUNAL}{alias_expr}\r\n"
    )
    (case_dir / "PROBE.LNK").write_bytes(link_text.encode("ascii"))
    (case_dir / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (case_dir / "RUN.BAT").write_bytes(
        (f"@echo off\r\nD:\\{linker['executable']} @PROBE.LNK < NUL > LINK.LOG\r\n"
         "PROBE.EXE > RUN.LOG\r\n").encode("ascii"))
    conf_lines = []
    for section, settings in runner["conf"].items():
        conf_lines.append("[" + section + "]")
        conf_lines.extend(f"{key}={value}" for key, value in settings.items())
    conf_lines += ["[autoexec]", f'mount c "{case_dir}"', f'mount d "{tool_dir}" -ro',
                   "c:", "call RUN.BAT", "exit"]
    conf_path = case_dir / "dosbox.conf"
    conf_path.write_text("\n".join(conf_lines) + "\n", encoding="ascii")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    timed_out = False
    try:
        proc = subprocess.run(
            [runner["path"], "-conf", str(conf_path), "-fastlaunch", "-exit", "-nomenu"],
            cwd=case_dir, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            timeout=60, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        host_output, host_return = proc.stdout, proc.returncode
    except subprocess.TimeoutExpired as error:
        timed_out = True
        host_output = (error.stdout or b"") + (error.stderr or b"")
        host_return = -1
    (case_dir / "DOSBOX-HOST.LOG").write_bytes(host_output)
    run_log = case_dir / "RUN.LOG"
    link_log = case_dir / "LINK.LOG"
    map_path = case_dir / "PROBE.MAP"
    actual = run_log.read_text(encoding="latin1").strip() if run_log.exists() else "NO RUN.LOG"
    link_output = link_log.read_text(encoding="latin1", errors="replace") if link_log.exists() else ""
    map_text = map_path.read_text(encoding="latin1", errors="replace") if map_path.exists() else ""
    names = (COMMUNAL, "_HistogramProbeAlias")
    rows = map_symbols(map_text, names)
    unresolved = [name for name in names if not rows.get(name) or
                  any(row["state"] != "Res" for row in rows[name])]
    clean_link = not re.search(r"warning\s+wrt|undefined symbol|error\s+wrt", link_output, re.I)

    def unique_position(symbol: str):
        positions = {(r["segment"], r["offset"], r["state"]) for r in rows.get(symbol, [])}
        return next(iter(positions)) if len(positions) == 1 else None

    owner_pos, alias_pos = unique_position(COMMUNAL), unique_position("_HistogramProbeAlias")
    expected_alias = (owner_pos[0], owner_pos[1] + alias_delta, owner_pos[2]) if owner_pos else None
    map_relation_ok = owner_pos is not None and alias_pos == expected_alias
    expected = case["expected_output"]
    passed = (actual == expected and host_return == 0 and not timed_out and
              (case_dir / "PROBE.EXE").exists() and clean_link and not unresolved and map_relation_ok)
    files = [file_receipt(path) for path in sorted(case_dir.iterdir()) if path.is_file()]
    return {
        "linker": profile,
        "case": case["name"],
        "expected_output": expected,
        "actual_output": actual,
        "host_returncode": host_return,
        "timed_out": timed_out,
        "exe_created": (case_dir / "PROBE.EXE").exists(),
        "link_clean": clean_link,
        "map_relation_ok": map_relation_ok,
        "owner_position": owner_pos,
        "test_alias_position": alias_pos,
        "test_alias_delta_bytes": alias_delta,
        "unresolved_or_nonresident_symbols": unresolved,
        "map_rows": [line.strip() for line in map_text.splitlines()
                     if COMMUNAL in line or "_HistogramProbeAlias" in line],
        "link_log_tail": link_output[-1200:],
        "passed": passed,
        "files": files,
        "claim_limit": "relative test alias and runtime fixture only; no historical absolute placement or adjacency is inferred",
    }


def main() -> int:
    provider_text = PROVIDER.read_text(encoding="ascii")
    declaration_matches = re.findall(
        r"(?m)^\s*int\s+far\s+fd_50F6_0EB6\[32\]\s*;\s*$", provider_text)
    if len(declaration_matches) != 1:
        raise RuntimeError("candidate provider must contain one exact natural int far[32] definition")

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"run-{stamp}-{uuid.uuid4().hex[:12]}"
    run_dir = OUT_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "fixtures").mkdir()
    inventory = source_inventory()
    (run_dir / "source-audit.json").write_text(
        json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    toolchain = compiler.toolchain()
    compiler_profile = toolchain["profiles"]["msc600ax"]
    runner = toolchain["runners"]["dosbox-x"]
    manifest = modules.load_manifest()
    runtime_rows = list(manifest["runtime"]["libraries"].values())
    for row in runtime_rows:
        if path_sha(Path(row["path"])) != row["sha256"]:
            raise RuntimeError(f"pinned runtime library hash mismatch: {row['path']}")

    fixtures = {
        "OWNER": compile_c(run_dir, "OWNER", provider_text, OWNER_FLAGS),
        "SHORT": compile_c(run_dir, "SHORT", "int far fd_50F6_0EB6[31];\n", OWNER_FLAGS),
        "BYTE": compile_c(run_dir, "BYTE", "unsigned char far fd_50F6_0EB6[64];\n", OWNER_FLAGS),
        "UNSIGNED": compile_c(run_dir, "UNSIGNED", "unsigned int far fd_50F6_0EB6[32];\n", OWNER_FLAGS),
        "INITIALIZED": compile_c(run_dir, "INIT",
                                  "int far fd_50F6_0EB6[32] = { 0x1357 };\n", OWNER_FLAGS),
        "CRTGOOD": compile_c(run_dir, "CRTGOOD", main_source(alias=True), CONSUMER_FLAGS),
        "CRTSIGNED": compile_c(run_dir, "CRTSIGN", unsigned_view_source(), CONSUMER_FLAGS),
    }

    def only_communal(name: str) -> dict | None:
        rows = fixtures[name]["matching_communals"]
        return rows[0] if len(rows) == 1 else None

    exact = only_communal("OWNER")
    short = only_communal("SHORT")
    byte = only_communal("BYTE")
    unsigned = only_communal("UNSIGNED")
    initialized_communal = only_communal("INITIALIZED")
    if not exact or (exact["count"], exact["element_size"], exact["length"]) != (32, 2, 64):
        raise RuntimeError(f"MSC OMF did not encode expected far int[32] common: {exact}")
    if not short or (short["count"], short["element_size"], short["length"]) != (31, 2, 62):
        raise RuntimeError(f"short-extent contrast was not distinct in OMF: {short}")
    if not byte or (byte["count"], byte["element_size"], byte["length"]) != (64, 1, 64):
        raise RuntimeError(f"byte-width contrast was not distinct in OMF: {byte}")
    if not unsigned or (unsigned["count"], unsigned["element_size"], unsigned["length"]) != (32, 2, 64):
        raise RuntimeError(f"unsigned source contrast OMF shape unexpected: {unsigned}")
    if initialized_communal is not None:
        raise RuntimeError("initialized control unexpectedly remained an uninitialized common")

    cases = [
        {"name": "positive_crt_zero_all_32_signed_words_raw_bytes", "owner": "OWNER",
         "consumer": "CRTGOOD", "expected_output": "PASS", "alias_delta": 0},
        {"name": "wrong_test_base_plus_one_word", "owner": "OWNER",
         "consumer": "CRTGOOD", "expected_output": "REJECTED_BASE", "alias_delta": 2},
        {"name": "wrong_initialized_data_owner", "owner": "INITIALIZED",
         "consumer": "CRTGOOD", "expected_output": "REJECTED_CRT_ZERO", "alias_delta": 0},
        {"name": "wrong_unsigned_consumer_view", "owner": "OWNER",
         "consumer": "CRTSIGNED", "expected_output": "REJECTED_UNSIGNED_VIEW", "alias_delta": 0},
    ]

    results = []
    for profile in ("rtlink400", "rtlink610"):
        linker = toolchain["linkers"][profile]
        tool_dir = compiler.pinned_tree(linker)
        for spec in cases:
            result = run_case(run_dir, profile, spec,
                              fixtures[spec["owner"]]["object_bytes"],
                              fixtures[spec["consumer"]]["object_bytes"],
                              runtime_rows, linker, runner, tool_dir)
            results.append(result)

    tool_paths = [ROOT / "tools/compiler.py", ROOT / "tools/modules.py", ROOT / "tools/omf.py",
                  ROOT / "layout/toolchain.json", ROOT / "layout/manifest.json"]
    runtime_pins = [{**row, "actual_sha256": path_sha(Path(row["path"]))} for row in runtime_rows]
    toolchain_receipt = {
        "compiler_profile": {"name": "msc600ax", "product": compiler_profile["product"],
                             "directory": compiler_profile["directory"],
                             "executable": compiler_profile["executable"],
                             "flags": OWNER_FLAGS, "profile_files": compiler_profile["files"],
                             "include_files": compiler_profile.get("include_files", [])},
        "consumer_flags": CONSUMER_FLAGS,
        "compiler_and_probe_helpers": [file_receipt(path) for path in tool_paths],
        "runner": {k: runner.get(k) for k in ("path", "sha256", "conf")},
        "runtime_libraries": runtime_pins,
        "linkers": {name: {"directory": toolchain["linkers"][name]["directory"],
                            "executable": toolchain["linkers"][name]["executable"],
                            "files": toolchain["linkers"][name]["files"],
                            "profile_note": toolchain["linkers"][name].get("status")}
                     for name in ("rtlink400", "rtlink610")},
    }
    report = {
        "schema": "simant-ant-class-histogram-owner-probe-v22",
        "status": "SCRATCH_ONLY_UNADMITTED_NO_PROMOTION",
        "root_reviewed": False,
        "run_id": run_id,
        "source_audit": {"path": (run_dir / "source-audit.json").relative_to(ROOT).as_posix(),
                         "sha256": path_sha(run_dir / "source-audit.json"),
                         "source_count": inventory["source_count"],
                         "named_hit_count": len(inventory["named_source_views"]),
                         "numeric_address_hit_count": len(inventory["numeric_address_spellings"]),
                         "address_taken_count": len(inventory["address_taken_lines"]),
                         "internal_registered_names": inventory["registered_names_inside_interval"]},
        "provider": {**file_receipt(PROVIDER),
                     "declaration": EXPECTED_SOURCE_DECLARATION,
                     "role": "one natural source-functional far int[32] object; no functions",
                     "flags": OWNER_FLAGS, "compiler_profile": "msc600ax",
                     "omf_common": exact,
                     "historical_owner_tu_or_order_claimed": False,
                     "historical_absolute_layout_claimed": False,
                     "original_initializer_claimed": False},
        "omf_controls": {
            "short_int_far_31": {"common": short, "expected_source_rejection": True,
                                  "runtime_attempted": False,
                                  "reason": "62-byte COMDEF is a type/extent contrast; no out-of-range access or adjacency is tested"},
            "unsigned_char_far_64": {"common": byte, "expected_source_rejection": True,
                                     "runtime_attempted": False,
                                     "reason": "same total bytes, wrong element width/count"},
            "unsigned_int_far_32": {"common": unsigned, "expected_source_rejection": True,
                                    "runtime_abi_distinguishable": False,
                                    "reason": "signedness is not represented by this OMF common; source pins carry that part of the candidate type"},
            "initialized_int_far_32": {"commons": fixtures["INITIALIZED"]["communals"],
                                       "publics": fixtures["INITIALIZED"]["publics"],
                                       "segments": fixtures["INITIALIZED"]["segments"],
                                       "expected_source_rejection": True,
                                       "reason": "initialized far data replaces the uninitialized far common"},
        },
        "compiled_fixture_inputs": {
            name: {
                "source": item["source"],
                "object": item["object"],
                "flags": item["flags"],
                "matching_communals": item["matching_communals"],
                "publics": item["publics"],
                "segments": item["segments"],
            }
            for name, item in fixtures.items()
        },
        "runtime_cases": results,
        "case_summary": {"required_cases": 8,
                         "passed_cases": sum(1 for row in results if row["passed"]),
                         "all_required_cases_passed": len(results) == 8 and all(row["passed"] for row in results)},
        "index_domain_and_limits": inventory["index_domain"],
        "layout_limits": "The runtime alias is test-owned and relative to this fixture only. The registered address row is source evidence for the symbol name/offset; no object order, absolute FAR_BSS placement, neighboring owner, alignment fill, or historical initializer is inferred.",
        "toolchain": toolchain_receipt,
        "input_policy": "Reads canonical and selected strict-effective C/ASM text, source manifests, tool metadata and pinned runtime libraries only. No original executable, original data bytes, original compiler inputs, or simulator/game stubs are read or built.",
        "files": [file_receipt(PROVIDER), file_receipt(Path(__file__)),
                  file_receipt(run_dir / "source-audit.json")],
    }
    report_path = run_dir / "candidate-receipt.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = {
        "run": run_dir.relative_to(ROOT).as_posix(),
        "receipt": report_path.relative_to(ROOT).as_posix(),
        "source_audit": report["source_audit"],
        "omf_candidate": exact,
        "runtime_cases": [(row["linker"], row["case"], row["actual_output"], row["passed"])
                          for row in results],
        "all_pass": report["case_summary"]["all_required_cases_passed"],
    }
    print(json.dumps(summary, indent=2))
    return 0 if report["case_summary"]["all_required_cases_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
