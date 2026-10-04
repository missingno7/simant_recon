"""Reproducible scratch-only MSC/RTLink shape and runtime proof for Handle[45].

Inputs are source text written below this directory plus pinned compiler/linker/runtime
tools. No original executable, oracle image, canonical source or repository tool is an
object input. The result concerns the standalone data object only; it does not bind
win_handles or establish invalid-window-ID behavior.
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


def find_root() -> Path:
    for p in Path(__file__).resolve().parents:
        if (p / "layout/manifest.json").is_file():
            return p
    raise RuntimeError("repository root not found")


ROOT = find_root()
OUT = Path(__file__).resolve().parent / "replay05"
WORKER = OUT.parents[2]
PROFILE = "msc600ax"
FLAGS = ["/AL", "/Os", "/Gs"]
NAME = "fd_50F6_3B60"
ALIAS = "fd_50F6_3B61"
TAG = "H45Q4R7"
OWNER_SOURCE = f"""/* Scratch-only natural owner candidate. */
typedef char far * far *Handle;
Handle far {NAME}[45];
"""

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "tools"))
import compiler  # noqa: E402
from omf import OmfReader  # noqa: E402

compiler.WORK = OUT / "compiler-work"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin(path: Path, expected: str | None = None) -> dict:
    raw = path.read_bytes()
    digest = sha(raw)
    if expected is not None and digest != expected:
        raise RuntimeError(f"hash mismatch for {path}: expected {expected}, got {digest}")
    try:
        shown = path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        shown = str(path.resolve())
    return {"path": shown, "sha256": digest, "size": len(raw)}


def compile_source(label: str, source: str, basename: str) -> tuple[bytes, dict, dict]:
    srcdir, objdir = OUT / "sources", OUT / "objects"
    srcdir.mkdir(parents=True, exist_ok=True)
    objdir.mkdir(parents=True, exist_ok=True)
    src = srcdir / f"{label}.c"
    src.write_text(source, encoding="ascii", newline="\r\n")
    result = compiler.compile_c(source, PROFILE, FLAGS, basename=basename, keep=True)
    if not result.ok or result.obj is None:
        raise RuntimeError(f"compile failed for {label}: {result.log}")
    obj = objdir / f"{label}.OBJ"
    obj.write_bytes(result.obj)
    return result.obj, pin(src), pin(obj)


def omf_facts(raw: bytes, symbol: str) -> dict:
    module = OmfReader(communals=True).read(raw, symbol)
    wanted = "_" + symbol
    comms = [r for r in module.communals if r["name"] == wanted]
    return {
        "module_name": module.name,
        "communals": comms,
        "publics": [r for r in module.publics if r["name"].lstrip("_") == symbol],
        "externals": [x for x in module.externals if x.lstrip("_") == symbol],
        "fixups": module.fixups,
        "segments": {k: v.hex() for k, v in sorted(module.segments.items())},
        "segment_lengths": module.segment_lengths,
        "segment_defs": module.segment_defs,
        "groups": module.groups,
        "object_size": len(raw),
        "object_sha256": sha(raw),
    }


def map_sections(text: str) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {"name": [], "value": []}
    active = None
    row_re = re.compile(r"^\s*([0-9A-Fa-f]{4}):([0-9A-Fa-f]{4})\s+\w+\s+([^\s]+)")
    for line in text.splitlines():
        if "Address         Publics by Name" in line:
            active = "name"
            continue
        if "Address         Publics by Value" in line:
            active = "value"
            continue
        if active:
            m = row_re.match(line)
            if m:
                out[active].append({"segment": int(m.group(1), 16), "offset": int(m.group(2), 16),
                                    "name": m.group(3), "text": line.rstrip()})
    return out


def typed_consumer() -> str:
    return f"""#include <memory.h>
typedef char far * far *Handle;
extern Handle far {NAME}[45];
extern unsigned char far {ALIAS};
extern int far puts(char far *text);
int main(void)
{{
    int i, j;
    unsigned char far *raw = (unsigned char far *){NAME};
    union H45Value {{ Handle value; unsigned char byte[4]; }} u;
    puts("START_TYPED");
    if (sizeof({NAME}) != 180) {{ puts("FAIL_TYPED_SIZE"); return 0; }}
    if ((void far *)&{ALIAS} != (void far *)(raw + 1)) {{ puts("FAIL_ALIAS_GEOMETRY"); return 0; }}
    for (i = 0; i < 45; ++i)
        if ({NAME}[i] != (Handle)0L) {{ puts("FAIL_TYPED_START_ZERO"); return 0; }}
    for (i = 0; i < 45; ++i)
        {NAME}[i] = (Handle)(0x10000000L + (unsigned long)i * 0x010101L);
    for (i = 0; i < 45; ++i)
        if ((unsigned long){NAME}[i] != (0x10000000UL + (unsigned long)i * 0x010101UL))
            {{ puts("FAIL_TYPED_CELL_ROUNDTRIP"); return 0; }}
    u.value = (Handle)0x12345678L;
    {NAME}[0] = u.value;
    for (j = 0; j < 4; ++j)
        if (raw[j] != u.byte[j]) {{ puts("FAIL_TYPED_FIRST_BYTE_VIEW"); return 0; }}
    u.value = (Handle)0x6a5b4c3dL;
    {NAME}[44] = u.value;
    for (j = 0; j < 4; ++j)
        if (raw[176 + j] != u.byte[j]) {{ puts("FAIL_TYPED_LAST_BYTE_VIEW"); return 0; }}
    _fmemset({NAME}, 0, sizeof({NAME}));
    for (i = 0; i < 45; ++i)
        if ({NAME}[i] != (Handle)0L) {{ puts("FAIL_TYPED_FMEMSET_WORD"); return 0; }}
    for (i = 0; i < 180; ++i)
        if (raw[i] != 0) {{ puts("FAIL_TYPED_FMEMSET_BYTE"); return 0; }}
    puts("PASS_TYPED_45_180_FMEMSET"); return 0;
}}
"""


def byte_consumer() -> str:
    return f"""#include <memory.h>
extern unsigned char far {NAME}[180];
extern unsigned char far {ALIAS};
extern int far puts(char far *text);
int main(void)
{{
    int i;
    puts("START_BYTE");
    if (sizeof({NAME}) != 180) {{ puts("FAIL_BYTE_SIZE"); return 0; }}
    if ((void far *)&{ALIAS} != (void far *)({NAME} + 1))
        {{ puts("FAIL_ALIAS_GEOMETRY"); return 0; }}
    for (i = 0; i < 180; ++i)
        if ({NAME}[i] != 0) {{ puts("FAIL_BYTE_START_ZERO"); return 0; }}
    for (i = 0; i < 180; ++i)
        {NAME}[i] = (unsigned char)((i * 37 + 11) & 255);
    if ({NAME}[0] != 11 || {NAME}[1] != 48 || {NAME}[176] != 123 || {NAME}[179] != 234)
        {{ puts("FAIL_BYTE_PATTERN_ENDPOINTS"); return 0; }}
    if ({ALIAS} != {NAME}[1]) {{ puts("FAIL_ALIAS_BYTE_VALUE"); return 0; }}
    _fmemset({NAME}, 0, 180);
    for (i = 0; i < 180; ++i)
        if ({NAME}[i] != 0) {{ puts("FAIL_BYTE_FMEMSET_SPAN"); return 0; }}
    puts("PASS_BYTE_180_FMEMSET"); return 0;
}}
"""


def short_overrun_consumer() -> str:
    return f"""typedef char far * far *Handle;
extern Handle far {NAME}[45];
extern int far puts(char far *text);
int main(void)
{{
    {NAME}[44] = (Handle)0x12345678L;
    if ((unsigned long){NAME}[44] == 0x12345678UL)
        puts("SHORT_ACCESS_COMPLETED_NO_TEXTENT_PROOF");
    else puts("SHORT_ACCESS_VALUE_DIFFERED_NO_TEXTENT_PROOF");
    return 0;
}}
"""


def init_consumer() -> str:
    return f"""typedef char far * far *Handle;
extern Handle far {NAME}[45];
extern int far puts(char far *text);
int main(void)
{{
    if ({NAME}[0] == (Handle)0x12345678L) puts("INIT_CONTROL_NONZERO");
    else puts("INIT_CONTROL_ZERO_OR_UNRESOLVED");
    return 0;
}}
"""


def write_link_fixture(case: str, linker_name: str, linker: dict, runner: dict,
                       tool_dir: Path, runtime_files: list[dict], consumer_obj: bytes,
                       owner_obj: bytes, alias_delta: int | None, run_exe: bool = True) -> dict:
    directory = OUT / "fixtures" / linker_name / case
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "TEST.OBJ").write_bytes(consumer_obj)
    (directory / "OWNER.OBJ").write_bytes(owner_obj)
    for r in runtime_files:
        shutil.copyfile(r["physical_path"], directory / r["name"].upper())
    link_text = ("OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n"
                 "LIBRARY LLIBCR, LIBH\r\nFILE TEST\r\n"
                 "BEGINAREA\r\nSECTION FILE OWNER\r\nENDAREA\r\n")
    if alias_delta is not None:
        link_text += f"DEFINE _{ALIAS} = _{NAME} + {alias_delta:X}\r\n"
    (directory / "PROBE.LNK").write_bytes(link_text.encode("ascii"))
    (directory / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    run_lines = [f"@echo off", f"D:\\{linker['executable']} @PROBE.LNK < NUL > LINK.LOG"]
    if run_exe:
        run_lines += ["echo BEFORE > STATUS.LOG",
                      "PROBE.EXE > RUN.LOG",
                      "echo AFTER >> STATUS.LOG"]
    else:
        run_lines += ["if exist PROBE.EXE echo UNEXPECTED_LINKED_EXE > RUN.LOG",
                      "if not exist PROBE.EXE echo BASE_CONTROL_NO_LINKED_EXE > RUN.LOG"]
    (directory / "RUN.BAT").write_bytes(("\r\n".join(run_lines) + "\r\n").encode("ascii"))
    config = []
    for section, settings in runner["conf"].items():
        config.append("[" + section + "]")
        config.extend(f"{k}={v}" for k, v in settings.items())
    config.extend(["[autoexec]", f'mount c "{directory.resolve()}"',
                   f'mount d "{tool_dir}" -ro', "c:", "call RUN.BAT", "exit"])
    (directory / "dosbox.conf").write_text("\n".join(config) + "\n", encoding="ascii")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    timed_out = False
    try:
        proc = subprocess.run([runner["path"], "-conf", str(directory / "dosbox.conf"),
                               "-fastlaunch", "-exit", "-nomenu"], cwd=directory, env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120,
                              creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        host_out, host_err, exit_code = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as e:
        timed_out, exit_code = True, -1
        host_out = e.stdout if isinstance(e.stdout, bytes) else b""
        host_err = e.stderr if isinstance(e.stderr, bytes) else b""
    (directory / "DOSBOX.OUT").write_bytes(host_out or b"")
    (directory / "DOSBOX.ERR").write_bytes(host_err or b"")
    run_bytes = (directory / "RUN.LOG").read_bytes() if (directory / "RUN.LOG").exists() else b""
    link_bytes = (directory / "LINK.LOG").read_bytes() if (directory / "LINK.LOG").exists() else b""
    status_bytes = (directory / "STATUS.LOG").read_bytes() if (directory / "STATUS.LOG").exists() else b""
    map_bytes = (directory / "PROBE.MAP").read_bytes() if (directory / "PROBE.MAP").exists() else b""
    map_text = map_bytes.decode("latin1", "replace")
    sections = map_sections(map_text)
    name_rows = {r["name"]: r for r in sections["name"]}
    value_rows = {r["name"]: r for r in sections["value"]}
    public_maps = {}
    for symbol in ("_" + NAME, "_" + ALIAS):
        if symbol in name_rows or symbol in value_rows:
            public_maps[symbol] = {"name_map": name_rows.get(symbol), "value_map": value_rows.get(symbol)}
    alias_geometry = None
    if ("_" + NAME) in public_maps and ("_" + ALIAS) in public_maps:
        nm_base, nm_alias = name_rows.get("_" + NAME), name_rows.get("_" + ALIAS)
        vm_base, vm_alias = value_rows.get("_" + NAME), value_rows.get("_" + ALIAS)
        alias_geometry = {
            "expected_delta_bytes": alias_delta,
            "name_map_delta_bytes": (nm_alias["offset"] - nm_base["offset"]
                                     if nm_base and nm_alias and nm_alias["segment"] == nm_base["segment"] else None),
            "value_map_delta_bytes": (vm_alias["offset"] - vm_base["offset"]
                                      if vm_base and vm_alias and vm_alias["segment"] == vm_base["segment"] else None),
            "same_segment_in_both_maps": bool(nm_base and nm_alias and vm_base and vm_alias and
                                              nm_base["segment"] == nm_alias["segment"] and
                                              vm_base["segment"] == vm_alias["segment"]),
        }
        alias_geometry["matches_directive_in_both_maps"] = (
            alias_geometry["same_segment_in_both_maps"] and
            alias_geometry["name_map_delta_bytes"] == alias_delta and
            alias_geometry["value_map_delta_bytes"] == alias_delta)
    artifacts = [pin(p) for p in sorted(directory.iterdir()) if p.is_file()]
    return {
        "linker": linker_name, "case": case, "exit_code": exit_code, "timed_out": timed_out,
        "exe_created": (directory / "PROBE.EXE").is_file(),
        "run_stdout_bytes_hex": run_bytes.hex(), "run_stdout_sha256": sha(run_bytes),
        "run_stdout_latin1": run_bytes.decode("latin1", "replace"),
        "batch_status_stdout_bytes_hex": status_bytes.hex(),
        "batch_status_stdout_latin1": status_bytes.decode("latin1", "replace"),
        "dosbox_stdout_sha256": sha(host_out or b""), "dosbox_stderr_sha256": sha(host_err or b""),
        "link_log_sha256": sha(link_bytes), "link_log_latin1": link_bytes.decode("latin1", "replace"),
        "map_sha256": sha(map_bytes), "map_publics_in_both_indexes": public_maps,
        "alias_geometry": alias_geometry,
        "map_far_bss_segments": [line.rstrip() for line in map_text.splitlines()
                                  if re.search(r"\bFAR_BSS\b", line)],
        "artifacts": artifacts,
    }


def main() -> int:
    # The prior bounded source receipt carries the canonical and strict-effective source
    # corpus pins and exact line text. Reverify those source bytes before using its claims.
    OUT.mkdir(parents=True, exist_ok=False)
    audit_path = WORKER / "receipt.json"
    audit_receipt = json.loads(audit_path.read_text(encoding="utf-8"))
    source_pins = []
    for row in audit_receipt["source_pins"]:
        source_pins.append(pin(ROOT / row["path"], row["sha256"]))
    if len(source_pins) != audit_receipt["source_sets"]["unique_source_count"]:
        raise RuntimeError("source audit pin count mismatch")

    # All candidate and contrast source programs are fixed below and saved verbatim.
    shape_sources = {
        "natural_handle_45": OWNER_SOURCE,
        "wrong_near_nested_handle_45": f"typedef char near * near *NearHandle;\nNearHandle far {NAME}[45];\n",
        "wrong_pointer_depth_same_four_byte_cell": f"typedef char far *FarCharPointer;\nFarCharPointer far {NAME}[45];\n",
        "short_handle_44": f"typedef char far * far *Handle;\nHandle far {NAME}[44];\n",
        "byte_array_same_180_extent": f"unsigned char far {NAME}[180];\n",
        "initialized_handle_nonzero_control": f"typedef char far * far *Handle;\nHandle far {NAME}[45] = {{ (Handle)0x12345678L }};\n",
        "wrong_base_name_equal_type": f"typedef char far * far *Handle;\nHandle far {TAG}_WrongBase[45];\n",
    }
    shape = {}
    shape_objects = {}
    for i, (label, source) in enumerate(shape_sources.items(), 1):
        raw, source_pin, object_pin = compile_source(label, source, f"{TAG[:3]}{i:05d}")
        facts = omf_facts(raw, NAME if label != "wrong_base_name_equal_type" else TAG + "_WrongBase")
        shape[label] = {"source": source_pin, "object": object_pin, "omf": facts}
        shape_objects[label] = raw

    typed_src, byte_src, short_src, init_src = (typed_consumer(), byte_consumer(),
                                                short_overrun_consumer(), init_consumer())
    typed_obj, typed_source_pin, typed_obj_pin = compile_source("typed_runtime_consumer", typed_src, "H45POS1")
    byte_obj, byte_source_pin, byte_obj_pin = compile_source("independent_byte_runtime_consumer", byte_src, "H45BYT1")
    short_obj, short_source_pin, short_obj_pin = compile_source("short_extent_overrun_consumer", short_src, "H45SHT1")
    init_obj, init_source_pin, init_obj_pin = compile_source("initialized_owner_control_consumer", init_src, "H45INI1")

    # Retain complete expanded source text exactly as passed to compiler as well as the
    # unexpanded source files/hashes written by compile_source.
    runtime_src_dir = OUT / "runtime_sources"
    runtime_src_dir.mkdir(exist_ok=True)
    runtime_sources = {}
    for label, source in (("typed_runtime_consumer", typed_src), ("independent_byte_runtime_consumer", byte_src),
                          ("short_extent_overrun_consumer", short_src), ("initialized_owner_control_consumer", init_src)):
        path = runtime_src_dir / f"{label}.c"
        path.write_text(source, encoding="ascii", newline="\r\n")
        runtime_sources[label] = pin(path)

    # Shape assertions distinguish source syntax from what OMF's name/type-neutral
    # COMDEF records can actually encode.
    def comm(label: str) -> list[dict]:
        return [{k: r.get(k) for k in ("name", "kind", "count", "element_size", "length")}
                for r in shape[label]["omf"]["communals"]]

    expected_180 = [{"name": "_" + NAME, "kind": "far", "count": 45, "element_size": 4, "length": 180}]
    expected_176 = [{"name": "_" + NAME, "kind": "far", "count": 44, "element_size": 4, "length": 176}]
    expected_90 = [{"name": "_" + NAME, "kind": "far", "count": 45, "element_size": 2, "length": 90}]
    expected_bytes = [{"name": "_" + NAME, "kind": "far", "count": 180, "element_size": 1, "length": 180}]
    natural = shape["natural_handle_45"]["omf"]
    shape_checks = {
        "natural_is_far_communal_45_cells_x_four_bytes": comm("natural_handle_45") == expected_180,
        "candidate_has_only_empty_segments_no_initialized_bytes_code_or_fixups": (
            not any(natural["segments"].values()) and
            all(length == 0 for length in natural["segment_lengths"].values()) and
            not natural["publics"] and not natural["fixups"]),
        "wrong_near_nested_pointer_extent_is_90": comm("wrong_near_nested_handle_45") == expected_90,
        "wrong_depth_control_has_same_extent_only": comm("wrong_pointer_depth_same_four_byte_cell") == expected_180,
        "short_bound_has_176_byte_extent": comm("short_handle_44") == expected_176,
        "byte_view_same_extent_does_not_prove_handle_type": comm("byte_array_same_180_extent") == expected_bytes,
        "nonzero_initialized_control_is_not_candidate_common": (
            not shape["initialized_handle_nonzero_control"]["omf"]["communals"] and
            bool(shape["initialized_handle_nonzero_control"]["omf"]["segments"])),
        "wrong_name_control_does_not_define_candidate_symbol": (
            comm("wrong_base_name_equal_type") == [{"name": "_" + TAG + "_WrongBase", "kind": "far",
                                                       "count": 45, "element_size": 4, "length": 180}]),
    }
    if not all(shape_checks.values()):
        raise RuntimeError("OMF source-shape checks failed: " + json.dumps(shape_checks, default=str))

    tc = compiler.toolchain()
    profile = compiler.verify_profile(PROFILE)
    effective_flags = [*FLAGS, *profile.get("required_flags", [])]
    runner = tc["runners"]["dosbox-x"]
    manifest = json.loads((ROOT / "layout/manifest.json").read_text(encoding="utf-8"))
    runtime_files = [{"name": key, "physical_path": Path(row["path"]),
                      "pin": pin(Path(row["path"]), row["sha256"])}
                     for key, row in manifest["runtime"]["libraries"].items()]
    compiler_tree = compiler.pinned_tree(profile)
    profile_files = [pin(Path(profile["directory"]) / rel, digest)
                     for rel, digest in profile["files"].items()]
    tool_pins = {
        "compiler_wrapper": pin(ROOT / "tools/compiler.py"),
        "omf_reader": pin(ROOT / "tools/omf.py"),
        "toolchain": pin(ROOT / "layout/toolchain.json"),
        "manifest_runtime_library_index": pin(ROOT / "layout/manifest.json"),
        "runner": pin(Path(runner["path"]), runner["sha256"]),
        "compiler_profile_files": profile_files,
        "compiler_pinned_tree": str(compiler_tree.relative_to(ROOT)),
        "runtime_libraries": [{"name": r["name"], **r["pin"]} for r in runtime_files],
    }
    linkers = {}
    runtime_cases = []
    for linker_name in ("rtlink400", "rtlink610"):
        linker = tc["linkers"][linker_name]
        linker_files = [pin(Path(linker["directory"]) / rel, digest)
                        for rel, digest in linker["files"].items()]
        linker_tree = compiler.pinned_tree(linker)
        linkers[linker_name] = {"files": linker_files, "pinned_tree": str(linker_tree.relative_to(ROOT)),
                                "status": linker.get("status")}
        for case, test_obj, owner_obj, alias_delta, run_exe in (
            ("typed_full_180_and_fmemset", typed_obj, shape_objects["natural_handle_45"], 1, True),
            ("independent_byte_full_180_and_fmemset", byte_obj, shape_objects["natural_handle_45"], 1, True),
            # Deliberately access cell 44 against an OMF owner bounded to 44 cells.
            # The result is evidence that this linker/runtime pair does not encode a
            # source-level array bound; it is NOT extent proof or a safety claim.
            ("short_44_owner_cell44_access_NO_TEXTENT_PROOF", short_obj, shape_objects["short_handle_44"], 1, True),
            ("initialized_nonzero_owner_control", init_obj, shape_objects["initialized_handle_nonzero_control"], 1, True),
            ("wrong_alias_base_plus_zero_control", typed_obj, shape_objects["natural_handle_45"], 0, True),
            ("wrong_base_name_unresolved_control", typed_obj, shape_objects["wrong_base_name_equal_type"], None, False),
        ):
            row = write_link_fixture(case, linker_name, linker, runner, linker_tree,
                                     runtime_files, test_obj, owner_obj, alias_delta, run_exe)
            runtime_cases.append(row)
            print(linker_name, case, row["run_stdout_latin1"].strip(), "exe=" + str(row["exe_created"]), flush=True)

    # Assert the positive and negative control outcomes using the exact DOS stdout bytes,
    # not a normalized console transcript. The short write is a deliberate out-of-bound
    # control and is only required to retain its explicit NO_TEXTENT_PROOF marker.
    by_key = {(r["linker"], r["case"]): r for r in runtime_cases}
    expected_stdout = {
        "typed_full_180_and_fmemset": b"START_TYPED\r\nPASS_TYPED_45_180_FMEMSET\r\n",
        "independent_byte_full_180_and_fmemset": b"START_BYTE\r\nPASS_BYTE_180_FMEMSET\r\n",
        "short_44_owner_cell44_access_NO_TEXTENT_PROOF": b"SHORT_ACCESS_COMPLETED_NO_TEXTENT_PROOF\r\n",
        "initialized_nonzero_owner_control": b"INIT_CONTROL_NONZERO\r\n",
        "wrong_alias_base_plus_zero_control": b"START_TYPED\r\nFAIL_ALIAS_GEOMETRY\r\n",
    }
    runtime_checks = {}
    for linker_name in ("rtlink400", "rtlink610"):
        for case, expected in expected_stdout.items():
            runtime_checks[f"{linker_name}_{case}_exact_stdout"] = (
                bytes.fromhex(by_key[(linker_name, case)]["run_stdout_bytes_hex"]) == expected)
        for case in ("typed_full_180_and_fmemset", "independent_byte_full_180_and_fmemset"):
            row = by_key[(linker_name, case)]
            runtime_checks[f"{linker_name}_{case}_name_and_value_alias_plus_one"] = (
                bool(row["alias_geometry"]) and row["alias_geometry"]["matches_directive_in_both_maps"] and
                row["alias_geometry"]["name_map_delta_bytes"] == 1 and
                row["alias_geometry"]["value_map_delta_bytes"] == 1)
        short_row = by_key[(linker_name, "short_44_owner_cell44_access_NO_TEXTENT_PROOF")]
        runtime_checks[f"{linker_name}_short_map_reports_176_not_180"] = any(
            "000B0H FAR_BSS" in line for line in short_row["map_far_bss_segments"])
        base_row = by_key[(linker_name, "wrong_base_name_unresolved_control")]
        base_entry = base_row["map_publics_in_both_indexes"].get("_" + NAME, {})
        runtime_checks[f"{linker_name}_wrong_base_is_reported_undefined"] = (
            "UNDEFINED SYMBOL(S)" in base_row["link_log_latin1"] and
            "warning wrt0022" in base_row["link_log_latin1"] and
            " U " in (base_entry.get("name_map") or {}).get("text", "") and
            " U " in (base_entry.get("value_map") or {}).get("text", ""))
    if not all(runtime_checks.values()):
        raise RuntimeError("runtime evidence assertions failed: " + json.dumps(runtime_checks))

    # Re-check the reusable source audit receipt and every current source hash, then
    # include its complete corpus pins in this replay receipt.
    audit_pin = pin(audit_path)
    self_pin = pin(Path(__file__))
    report = {
        "schema": "dos-handle45-runtime-owner-proof-v1",
        "scope": "scratch-only source-typed data owner shape and isolated runtime controls; ownership only",
        "candidate": {"source_text": OWNER_SOURCE, "natural_type": "typedef char far * far *Handle;",
                      "declaration": f"Handle far {NAME}[45];", "registered_data_address": "50F6:3B60",
                      "source_extent": {"cells": 45, "cell_bytes": 4, "bytes": 180, "end_exclusive": "50F6:3C14"},
                      "no_initial_values_claimed": True},
        "source_audit": {"receipt": audit_pin, "source_sets": audit_receipt["source_sets"],
                         "source_pins_reverified": source_pins,
                         "source_owner_anchors": [
                             {"path": "src/root/m1E57.c", "lines": {"typedef": 3, "array_reference": 114,
                               "first_call_reset": 230, "release_loop": 244, "allocation_store": 253}},
                             {"path": "evidence/behavior/functions/f_1E57_038E/contracts/window-valid-v1/module.c",
                              "lines": {"typedef": 3, "array_reference": 114, "first_call_reset": 226,
                                        "release_loop": 240, "allocation_store": 249}}],
                         "canonical_vs_effective_limit": "canonical byte-exact function remains scaffold; strict-effective whole-module function supplies current behavioral source; no historical TU identity claim"},
        "replay": {"probe_script": self_pin, "complete_runtime_source_files": runtime_sources,
                   "compiler_input_sources_and_objects": [
                       {"source": row["source"], "object": row["object"], "omf": row["omf"]}
                       for row in shape.values()],
                   "compiler_profile": {"name": PROFILE, "product": profile.get("product"), "flags": FLAGS,
                                        "effective_flags": effective_flags,
                                        "pinned_tree": tool_pins["compiler_pinned_tree"],
                                        "files": profile_files},
                   "tool_pins": tool_pins, "linker_profiles": linkers},
        "shape_controls": shape,
        "shape_checks": shape_checks,
        "runtime_checks": runtime_checks,
        "runtime_consumer_objects": {"typed": {"source": typed_source_pin, "object": typed_obj_pin},
                                      "independent_byte": {"source": byte_source_pin, "object": byte_obj_pin},
                                      "short_overrun": {"source": short_source_pin, "object": short_obj_pin},
                                      "initialized_control": {"source": init_source_pin, "object": init_obj_pin}},
        "runtime_cases": runtime_cases,
        "interpretation": [
            "The previous int[45] description was wrong. The source-selected type is Handle far[45], where Handle is a two-level far pointer typedef; MSC 6.00AX emits 45 four-byte cells (180 bytes).",
            "OMF extent alone cannot distinguish this Handle nesting from a one-level far character pointer array or an unsigned-byte array of length 180. The exact natural source declaration and all typed uses establish the source type; the controls demonstrate this limitation.",
            "The independent byte consumer checks all 180 initial bytes, writes distinct values across the complete span, validates endpoints and the +1 byte alias, then zeros/verifies all 180 bytes with _fmemset. The typed consumer independently checks all 45 cells, endpoint pointer/byte agreement and _fmemset over sizeof(array).",
            "The 44-cell run is deliberately an out-of-bound control. It is reported as NO_TEXTENT_PROOF even if the access completes; linker allocation success does not enforce a C array bound.",
            "The map aliases are test directives in the isolated harness only. Their Name and Value index entries validate the test's byte offset geometry; they do not establish the historical game's linker placement or any registered neighboring object ownership.",
            "This proof does not claim the distinct DGROUP win_handles object, invalid-window-ID safety, canonical byte-exact reset body, or original startup/lifecycle closure beyond the reviewed strict-effective behavior source.",
            "RTLink 4.00 and 6.10 are pinned experimental linkers, not identified as the historical SimAnt linker. No original executable or oracle bytes are a compiler, linker, or runtime input.",
        ],
        "no_original_executable_or_oracle_input_read": True,
        "all_shape_checks_pass": all(shape_checks.values()),
        "all_runtime_checks_pass": all(runtime_checks.values()),
        "runtime_cases_count": len(runtime_cases),
        "outputs_root": OUT.relative_to(ROOT).as_posix(),
    }
    proof = OUT / "runtime-proof.json"
    proof.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    summary = OUT / "summary.md"
    summary.write_text(
        "# Handle[45] standalone data-owner proof\n\n"
        "Natural declaration: `typedef char far * far *Handle; Handle far fd_50F6_3B60[45];`. "
        "MSC 6.00AX OMF should report one far COMDEF of 45 four-byte elements (180 bytes). "
        "The prior `int[45]` interpretation is superseded.\n\n"
        f"Shape assertions: **{sum(shape_checks.values())}/{len(shape_checks)} passed**. "
        f"Runtime fixtures: **{len(runtime_cases)}** across RTLink 4.00 and 6.10; inspect exact raw stdout, "
        "hashes, Name/Value maps, alias geometry, and artifacts in `runtime-proof.json`.\n\n"
        "The 44-cell access is explicitly `NO_TEXTENT_PROOF`, not a valid bound or safe access. "
        "The proof concerns standalone source-typed object ownership only; it does not claim `win_handles`, "
        "invalid-ID semantics, original placement, or canonical historical function recovery.\n",
        encoding="utf-8")
    print("proof", proof.relative_to(ROOT).as_posix(), flush=True)
    print("shape checks", sum(shape_checks.values()), "/", len(shape_checks),
          "runtime cases", len(runtime_cases), flush=True)
    return 0 if all(shape_checks.values()) and all(runtime_checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
