"""Fresh natural owner shape and RTLink runtime controls for terrain words.

All compiler/linker/runtime inputs are test-owned sources or hash-pinned tools and
libraries. Outputs stay under this worker directory; no original executable is read.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "build/workers/dos_v17_fresh/terrn"
OUT.mkdir(parents=True, exist_ok=True)
PROVIDER = ROOT / "work/source-only-dos/providers/terrain-state.c"
REPORT_PATH = OUT / "TERRN.V17.JSON"
PROFILE = "msc600ax"
FLAGS = ["/AL", "/Os", "/Gs"]
NAMES = ("Barrier", "TERRAINset")
OWNER = PROVIDER.read_text(encoding="ascii")
EXPECTED_OWNER = ("/* Scratch-only candidate for the persistent terrain-selection state pair.\n"
                  " * Both objects remain uninitialized, as in FAR_BSS; no initial value is inferred.\n"
                  " */\nint far Barrier;\nint far TERRAINset;\n")

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "tools"))
import compiler  # noqa: E402
from omf import OmfReader  # noqa: E402


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin(path: Path, expected: str | None = None) -> dict:
    raw = path.read_bytes()
    got = sha(raw)
    if expected is not None and got != expected:
        raise RuntimeError(f"hash mismatch: {path}")
    return {"path": str(path), "sha256": got, "size": len(raw)}


def compile_source(label: str, source: str, basename: str, root: Path):
    srcdir, objdir = root / "sources", root / "objects"
    srcdir.mkdir(parents=True, exist_ok=True)
    objdir.mkdir(parents=True, exist_ok=True)
    src = srcdir / f"{label}.c"
    src.write_text(source, encoding="ascii", newline="\r\n")
    result = compiler.compile_c(source, PROFILE, FLAGS, basename=basename, keep=True)
    if not result.ok or result.obj is None:
        raise RuntimeError(f"compile failed ({label}): {result.log}")
    obj = objdir / f"{label}.OBJ"
    obj.write_bytes(result.obj)
    return result.obj, pin(src), pin(obj), result.log


def consumer_source(bad_save_view: bool = False, unsigned_view: bool = False) -> str:
    word_type = "unsigned int" if unsigned_view else "int"
    decl = "\n".join(f"extern {word_type} far {name};" for name in NAMES)
    rows = ",\n".join(f"    {{ 2, 1, (void far *)&{name} }}" for name in NAMES)
    mutate = ("    views[0].data = (void far *)((unsigned char far *)views[0].data + 1);\n"
              if bad_save_view else "")
    if unsigned_view:
        checks = r'''
    words[0][0] = (unsigned int)0xffff;
    if (words[0][0] != 0xffffU) { puts("FAIL_UNSIGNED_CONTROL"); return 0; }
    puts("TYPE_NEGATIVE_UNSIGNED_VIEW"); return 0;
'''
    else:
        checks = r'''
    words[0][0] = -2;
    if (bytes[0][0] != 0xfe || bytes[0][1] != 0xff || words[0][0] != -2) {
        puts("FAIL_SIGNED_BYTE_VIEW"); return 0;
    }
    bytes[1][0] = 0; bytes[1][1] = 0x80;
    if (words[1][0] != -32768) { puts("FAIL_SIGNED_MIN"); return 0; }
    words[1][0] = 1;
    if (bytes[1][0] != 1 || bytes[1][1] != 0) { puts("FAIL_BYTE_ORDER"); return 0; }
    puts("PASS"); return 0;
'''
    return f'''{decl}
extern int far puts(char far *text);
struct SaveRec {{ int size; int count; void far *data; }};
struct SaveRec views[2] = {{
{rows}
}};
int main(void)
{{
    int i;
    {word_type} far *words[2] = {{ &Barrier, &TERRAINset }};
    unsigned char far *bytes[2];
{mutate}    for (i = 0; i < 2; ++i) {{
        if (views[i].size != 2 || views[i].count != 1) {{ puts("FAIL_SHAPE"); return 0; }}
        if ((void far *)views[i].data != (void far *)words[i]) {{ puts("FAIL_PTR"); return 0; }}
        bytes[i] = (unsigned char far *)views[i].data;
        if (words[i][0] != 0 || bytes[i][0] != 0 || bytes[i][1] != 0) {{ puts("FAIL_ZERO"); return 0; }}
    }}
{checks}}}
'''


def source_controls():
    return {
        "signed_int_far_owner": OWNER,
        "unsigned_int_same_extent_control": "unsigned int far Barrier;\nunsigned int far TERRAINset;\n",
        "byte_array_same_extent_control": "unsigned char far Barrier[2];\nunsigned char far TERRAINset[2];\n",
        "int_array_wrong_extent_control": "int far Barrier[2];\nint far TERRAINset[2];\n",
        "long_wrong_width_control": "long far Barrier;\nlong far TERRAINset;\n",
        "near_int_control": "int near Barrier;\nint near TERRAINset;\n",
        "initialized_nonzero_control": "int far Barrier = 1;\nint far TERRAINset;\n",
    }


def target_commons(module):
    rows = []
    for row in module.communals:
        name = row["name"].lstrip("_")
        if name in NAMES:
            rows.append({"name": name, "kind": row["kind"], "count": row.get("count"),
                         "element_size": row.get("element_size"), "length": row["length"]})
    return sorted(rows, key=lambda x: x["name"])


def runtime_link(out: Path, linker_name: str, linker: dict, linker_dir: Path,
                 runner: dict, runtime_files, test_obj: bytes, owner_obj: bytes,
                 case_name: str, expected: str):
    directory = out / "runtime" / linker_name / case_name
    directory.mkdir(parents=True, exist_ok=True)
    for name in ("PROBE.EXE", "PROBE.MAP", "RUN.LOG", "LINK.LOG"):
        (directory / name).unlink(missing_ok=True)
    (directory / "TEST.OBJ").write_bytes(test_obj)
    (directory / "OWNER.OBJ").write_bytes(owner_obj)
    for row in runtime_files:
        shutil.copyfile(row["physical_path"], directory / row["name"].upper())
    (directory / "PROBE.LNK").write_bytes((
        "OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n"
        "LIBRARY LLIBCR, LIBH\r\nFILE TEST\r\n"
        "BEGINAREA\r\nSECTION FILE OWNER\r\nENDAREA\r\n").encode("ascii"))
    (directory / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (directory / "RUN.BAT").write_bytes((
        f"@echo off\r\nD:\\{linker['executable']} @PROBE.LNK < NUL > LINK.LOG\r\n"
        "PROBE.EXE > RUN.LOG\r\n").encode("ascii"))
    conf = []
    for section, values in runner["conf"].items():
        conf.append("[" + section + "]")
        conf.extend(f"{key}={value}" for key, value in values.items())
    conf.extend(["[autoexec]", f'mount c "{directory.resolve()}"',
                 f'mount d "{linker_dir}" -ro', "c:", "call RUN.BAT", "exit"])
    config = directory / "dosbox.conf"
    config.write_text("\n".join(conf) + "\n", encoding="ascii")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    try:
        proc = subprocess.run([runner["path"], "-conf", str(config), "-fastlaunch", "-exit", "-nomenu"],
                              cwd=directory, env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=90,
                              creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        exit_code, timed_out, host_output = proc.returncode, False, proc.stdout.decode("latin1", "replace")
    except subprocess.TimeoutExpired as error:
        exit_code, timed_out = -1, True
        host_output = (error.stdout or b"").decode("latin1", "replace") if isinstance(error.stdout, bytes) else str(error.stdout)
    raw_run_log = ((directory / "RUN.LOG").read_bytes().decode("latin1")
                   if (directory / "RUN.LOG").exists() else "NO RUN.LOG")
    actual = raw_run_log.strip()
    link_log = (directory / "LINK.LOG").read_text(encoding="latin1", errors="replace") if (directory / "LINK.LOG").exists() else ""
    map_path = directory / "PROBE.MAP"
    map_text = map_path.read_text(encoding="latin1", errors="replace") if map_path.exists() else ""
    expected_publics = ["_Barrier", "_TERRAINset"]
    found_publics = [name for name in expected_publics
                     if re.search(r"(?<![A-Za-z0-9_])" + re.escape(name) +
                                  r"(?![A-Za-z0-9_])", map_text)]
    linker_diagnostics = re.findall(
        r"(?im)^.*(?:unresolved|undefined|unknown external|not defined|symbol not found).*$",
        link_log)
    exe_exists = (directory / "PROBE.EXE").is_file()
    map_exists = map_path.is_file()
    passed = (actual == expected and exit_code == 0 and not timed_out and exe_exists and
              map_exists and not linker_diagnostics and found_publics == expected_publics)
    artifacts = [pin(path) for path in sorted(directory.iterdir()) if path.is_file()]
    return {"linker": linker_name, "case": case_name, "expected": expected, "actual": actual,
            "raw_run_log_latin1": raw_run_log,
            "exit_code": exit_code, "timed_out": timed_out, "passed": passed,
            "linker_produced_executable": exe_exists, "linker_produced_map": map_exists,
            "expected_owner_publics": expected_publics, "owner_publics_found_in_map": found_publics,
            "linker_diagnostics": linker_diagnostics,
            "link_log_tail": link_log[-1600:], "host_output_tail": host_output[-800:],
            "artifacts": artifacts}


def audited_source_pins(inventory_path: Path):
    """Verify and carry the exact source set read by the terrain audit."""
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    expected = {}
    for group in ("canonical", "strict_effective"):
        for row in inventory["source_inputs"][group]:
            rel = row.get("path")
            if not rel:
                continue
            previous = expected.setdefault(rel, row["sha256"])
            if previous != row["sha256"]:
                raise RuntimeError(f"conflicting source audit pins for {rel}")
    pins = [pin(ROOT / rel, digest) for rel, digest in sorted(expected.items())]
    source_sets = inventory["source_sets"]
    if len(pins) != source_sets["unique_scanned_source_files"]:
        raise RuntimeError("audited source pin count differs from terrain inventory")
    return {
        "inventory": {"path": inventory_path.relative_to(ROOT).as_posix(),
                      "sha256": sha(inventory_path.read_bytes()),
                      "size": inventory_path.stat().st_size,
                      "source_sets": source_sets},
        "unique_source_count": len(pins),
        "sources": pins,
    }


def main():
    if REPORT_PATH.exists():
        raise RuntimeError(f"refusing to overwrite existing fresh report: {REPORT_PATH}")
    out = Path(tempfile.mkdtemp(prefix="terrain-owner-", dir=OUT))
    compiler.WORK = out / "compiler-work"
    compiler.WORK.mkdir(parents=True, exist_ok=True)
    toolchain = compiler.toolchain()
    profile = compiler.verify_profile(PROFILE)
    effective_flags = [*FLAGS, *profile.get("required_flags", [])]
    if "/Zi" in effective_flags:
        raise RuntimeError("shape fixture must compile without /Zi")
    profile_runner = toolchain["runners"][profile["runner"]] if profile.get("runner") else toolchain["runner"]
    profile_pins = [pin(Path(profile["directory"]) / rel, digest)
                    for rel, digest in profile["files"].items()]
    compiler_runner_pin = pin(Path(profile_runner["path"]), profile_runner["sha256"])
    compiler_tree = compiler.pinned_tree(profile)
    omf_reader_pin = pin(ROOT / "tools/omf.py")
    compiler_wrapper_pin = pin(ROOT / "tools/compiler.py")
    toolchain_pin = pin(ROOT / "layout/toolchain.json")
    manifest = json.loads((ROOT / "layout/manifest.json").read_text(encoding="utf-8"))
    manifest_pin = pin(ROOT / "layout/manifest.json")
    inventory_path = ROOT / "build/workers/dos_terrain_state_owners/inventory.json"
    source_audit_pins = audited_source_pins(inventory_path)
    provider_pin = pin(PROVIDER)
    if OWNER != EXPECTED_OWNER:
        raise RuntimeError("candidate provider source changed from bounded signed-word declarations")

    compiled = {}
    owner_obj = None
    for index, (label, source) in enumerate(source_controls().items()):
        raw, source_pin, object_pin, log = compile_source(label, source, f"TST{index:04d}", out)
        module = OmfReader(communals=True).read(raw, label.upper())
        compiled[label] = {"source": source_pin, "object": object_pin,
                           "object_sha256": sha(raw), "object_size": len(raw),
                           "communals": target_commons(module),
                           "publics": [row["name"] for row in module.publics
                                       if row["name"].lstrip("_") in NAMES],
                           "segment_rows": [{"name": s["name"], "length": s["length"],
                                             "class": s["class"], "combine": s["combine"],
                                             "alignment": s["alignment"]}
                                            for s in module.segment_defs],
                           "log_tail": log.splitlines()[-12:]}
        if label == "signed_int_far_owner":
            owner_obj = raw
    assert owner_obj is not None

    exact = [{"name": name, "kind": "far", "count": 2, "element_size": 1, "length": 2}
             for name in NAMES]
    near = [{"name": name, "kind": "near", "count": None, "element_size": None, "length": 2}
            for name in NAMES]
    wrong4 = [{"name": name, "kind": "far", "count": 4, "element_size": 1, "length": 4}
              for name in NAMES]
    wrong_array = [{"name": name, "kind": "far", "count": 2, "element_size": 2, "length": 4}
                   for name in NAMES]
    shape_checks = {
        "signed_int_far_owner_is_exact_two_byte_communal": compiled["signed_int_far_owner"]["communals"] == exact,
        "unsigned_int_same_omf_extent_is_not_a_signedness_proof": compiled["unsigned_int_same_extent_control"]["communals"] == exact,
        "byte_array_same_omf_extent_is_not_a_semantic_type_proof": compiled["byte_array_same_extent_control"]["communals"] == exact,
        "two_element_int_array_is_four_bytes": compiled["int_array_wrong_extent_control"]["communals"] == wrong_array,
        "long_is_four_bytes": compiled["long_wrong_width_control"]["communals"] == wrong4,
        "near_control_is_not_far": compiled["near_int_control"]["communals"] == near,
        "initialized_barrier_has_no_communal": (all(row["name"] != "Barrier"
                                                       for row in compiled["initialized_nonzero_control"]["communals"]) and
                                                   compiled["initialized_nonzero_control"]["publics"] == ["_Barrier"]),
    }
    if not all(shape_checks.values()):
        raise RuntimeError("one or more compiler shape controls failed: " + json.dumps(shape_checks))

    test_positive, _, positive_obj_pin, positive_log = compile_source(
        "semantic_word_and_byte_view_consumer", consumer_source(), "TESTPOS", out)
    test_bad, _, bad_obj_pin, bad_log = compile_source(
        "one_byte_interior_save_view_control", consumer_source(bad_save_view=True), "TESTBAD", out)
    test_unsigned, _, unsigned_obj_pin, unsigned_log = compile_source(
        "unsigned_consumer_type_control", consumer_source(unsigned_view=True), "TESTUNSG", out)
    initialized_obj = next(
        (Path(row["object"]["path"]).read_bytes() for label, row in compiled.items()
         if label == "initialized_nonzero_control"), None)
    if initialized_obj is None:
        raise RuntimeError("initialized negative-control object absent")

    runtime_files = []
    for library_name, row in manifest["runtime"]["libraries"].items():
        p = Path(row["path"])
        runtime_files.append({"name": library_name, "physical_path": p,
                              "pin": pin(p, row["sha256"])})
    runner = toolchain["runners"]["dosbox-x"]
    runner_pin = pin(Path(runner["path"]), runner["sha256"])
    link_pins, link_trees = {}, {}
    for linker_name in ("rtlink400", "rtlink610"):
        linker = toolchain["linkers"][linker_name]
        link_pins[linker_name] = [pin(Path(linker["directory"]) / rel, digest)
                                  for rel, digest in linker["files"].items()]
        link_trees[linker_name] = compiler.pinned_tree(linker)

    runtime_cases = []
    for linker_name in ("rtlink400", "rtlink610"):
        linker = toolchain["linkers"][linker_name]
        controls = [
            ("signed_word_exact_two_byte_save_view", test_positive, owner_obj, "PASS"),
            ("one_byte_interior_save_view_rejected", test_bad, owner_obj, "FAIL_PTR"),
            ("initialized_nonzero_owner_rejected", test_positive, initialized_obj, "FAIL_ZERO"),
            ("unsigned_consumer_is_semantically_different", test_unsigned, owner_obj,
             "TYPE_NEGATIVE_UNSIGNED_VIEW"),
        ]
        for case_name, test_obj, data_obj, expected in controls:
            result = runtime_link(out, linker_name, linker, link_trees[linker_name], runner,
                                  runtime_files, test_obj, data_obj, case_name, expected)
            runtime_cases.append(result)
            print(linker_name, case_name, result["actual"], "pass=" + str(result["passed"]), flush=True)
            if not result["passed"]:
                raise RuntimeError(f"runtime control failed {linker_name}/{case_name}: {result}")

    report = {
        "schema": "dos-terrain-state-owner-runtime-proof-v17",
        "admission": {"root_reviewed": False, "admitted": False},
        "scope": "scratch-only typed natural provider/consumer controls; no historical owner placement or initial-value claim",
        "provider": {**provider_pin, "source_type": "uninitialized signed int far Barrier and TERRAINset"},
        "probe_source": pin(Path(__file__)),
        "profile": {"name": PROFILE, "product": profile.get("product"), "flags": FLAGS,
                    "effective_flags": effective_flags,
                    "runner": compiler_runner_pin, "pinned_compiler_files": profile_pins,
                    "pinned_tree": str(compiler_tree.relative_to(ROOT)),
                    "compiler_wrapper": compiler_wrapper_pin, "omf_reader": omf_reader_pin,
                    "toolchain": toolchain_pin},
        "manifest": manifest_pin,
        "terrain_source_audit": source_audit_pins,
        "linker_profile": {"runner": runner_pin,
                           "profiles": {name: {"files": link_pins[name],
                                               "pinned_tree": str(link_trees[name].relative_to(ROOT)),
                                               "status": toolchain["linkers"][name].get("status")}
                                        for name in link_pins}},
        "shape_controls": compiled,
        "shape_checks": shape_checks,
        "runtime_source_objects": {
            "positive_consumer": {"source": "semantic_word_and_byte_view_consumer.c",
                                  "object": positive_obj_pin, "log_tail": positive_log.splitlines()[-12:]},
            "interior_control": {"source": "one_byte_interior_save_view_control.c",
                                 "object": bad_obj_pin, "log_tail": bad_log.splitlines()[-12:]},
            "unsigned_type_control": {"source": "unsigned_consumer_type_control.c",
                                      "object": unsigned_obj_pin, "log_tail": unsigned_log.splitlines()[-12:]},
        },
        "runtime_cases": runtime_cases,
        "interpretation": [
            "OMF COMDEF extent does not distinguish int from unsigned int or a two-byte unsigned-char array; canonical semantic declarations/uses establish int, while byte array is only a SaveRec view.",
            "The runtime type control demonstrates that an unsigned consumer changes negative-word interpretation even though its symbol layout still links.",
            "RTLink 4.00 and 6.10 are pinned experimental instruments, not claims about the historical SimAnt linker.",
            "Barrier and TERRAINset initial values are intentionally not supplied by this provider. Runtime zero checks test only uninitialized FAR common allocation in the isolated control program.",
            "DROPdir and Tindex also have source declarations as signed int far scalars; this provider omits them because first-write/CRT-zero dominance and their raw-alias integration have not been closed in this proof. Their gameplay value domains, Tindex nesting/clobber bounds, and map/load lifecycle are separate integration questions, not conclusions about scalar object type or extent.",
        ],
        "no_original_executable_or_oracle_input_read": True,
        "all_shape_checks_pass": all(shape_checks.values()),
        "all_runtime_cases_pass": all(x["passed"] for x in runtime_cases),
    }
    report_path = REPORT_PATH
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (OUT / "LATEST.V17.TXT").write_text(report_path.relative_to(ROOT).as_posix() + "\n",
                                        encoding="ascii")
    print("proof", report_path.relative_to(ROOT).as_posix(), flush=True)
    print("all shape checks", report["all_shape_checks_pass"], "runtime cases",
          len(runtime_cases), "all passed", report["all_runtime_cases_pass"], flush=True)
    return 0 if report["all_shape_checks_pass"] and report["all_runtime_cases_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
