"""Isolated MSC/RTLink controls for the typed screen-list initializer candidate.

This runner reads project metadata and pinned tool/runtime files only. It never
opens SIMANT.EXE or another original oracle input. All generated C, objects,
link fixtures, executables, logs, and the report stay beside this script under
probe-run-v1/. Run explicitly with:

    python build/workers/dos_screen_list_initializer_v35/probe-v1.py

The result is a test-owned functional/source representation check, not a
historical owner, placement, or exact-byte claim.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def find_root() -> Path:
    for path in Path(__file__).resolve().parents:
        if (path / "layout" / "manifest.json").is_file():
            return path
    raise RuntimeError("cannot find repository root")


ROOT = find_root()
WORKER = Path(__file__).resolve().parent
RUN = WORKER / "probe-run-v3"
PROFILE = "msc600ax"
FLAGS = ["/AL", "/Os", "/Gs"]
SOURCE_RECEIPT = ROOT / "build" / "workers" / "dos_readonly_bss_semantics_v33" / "receipt-v33.json"

if RUN.exists():
    raise RuntimeError(f"refusing to overwrite existing probe output: {RUN}")
RUN.mkdir(parents=True)
SRC = RUN / "sources"
OBJ = RUN / "objects"
CC = RUN / "cc"
for path in (SRC, OBJ, CC):
    path.mkdir()

sys.path.insert(0, str(ROOT / "tools"))
import compiler  # noqa: E402
from omf import OmfReader  # noqa: E402

compiler.WORK = CC


def verify_source_pins() -> tuple[list[dict], str]:
    receipt_bytes = SOURCE_RECEIPT.read_bytes()
    receipt = json.loads(receipt_bytes)
    census = receipt["source_census"]
    rows = census["files"]
    if census.get("count") != 156 or len(rows) != 156:
        raise RuntimeError("the accepted-source census is not the expected 156-entry set")
    checked = []
    for row in rows:
        rel = Path(row["path"])
        if rel.is_absolute() or ".." in rel.parts:
            raise RuntimeError(f"source census contains an unsafe path: {row['path']}")
        source_path = ROOT / rel
        body = source_path.read_bytes()
        actual_hash = hashlib.sha256(body).hexdigest()
        if len(body) != row["size"] or actual_hash != row["sha256"]:
            raise RuntimeError(f"accepted-source pin changed: {row['path']}")
        checked.append({"path": row["path"], "sha256": actual_hash,
                        "size": len(body), "verified": True})
    out = RUN / "source-census-v1.json"
    out.write_text(json.dumps({
        "schema": "simant-screen-list-source-census-v1",
        "source_receipt": SOURCE_RECEIPT.relative_to(ROOT).as_posix(),
        "source_receipt_sha256": hashlib.sha256(receipt_bytes).hexdigest(),
        "count": len(checked), "files": checked,
    }, indent=2) + "\n", encoding="utf-8")
    return checked, hashlib.sha256(out.read_bytes()).hexdigest()


RECT = """struct Rect { int left; int top; int right; int bottom; };
#define RECT_END ((int)0x8000)
"""


def owner_source(case: str) -> str:
    if case == "positive":
        return RECT + """struct Rect near g_5A9C[2] = {
    { 0, 0, 349, 639 },
    { RECT_END, RECT_END, RECT_END, RECT_END }
};
"""
    if case == "wrong_fields":
        return """struct WrongRect { int left; int top; int bottom; int right; };
#define RECT_END ((int)0x8000)
struct WrongRect near g_5A9C[2] = {
    { 0, 0, 639, 349 },
    { RECT_END, RECT_END, RECT_END, RECT_END }
};
"""
    if case == "wrong_order":
        return RECT + """struct Rect near g_5A9C[2] = {
    { RECT_END, RECT_END, RECT_END, RECT_END },
    { 0, 0, 349, 639 }
};
"""
    if case == "partial_sentinel":
        return RECT + """struct Rect near g_5A9C[2] = {
    { 0, 0, 349, 639 },
    { 0, RECT_END, 0, 0 }
};
"""
    if case == "wide_fields":
        return """struct WideRect { long left; long top; long right; long bottom; };
#define RECT_END ((long)0x8000L)
struct WideRect near g_5A9C[2] = {
    { 0L, 0L, 349L, 639L },
    { RECT_END, RECT_END, RECT_END, RECT_END }
};
"""
    if case == "far_data":
        return RECT + """struct Rect far g_5A9C[2] = {
    { 0, 0, 349, 639 },
    { RECT_END, RECT_END, RECT_END, RECT_END }
};
"""
    raise ValueError(case)


HANDLE_OK = RECT + """extern struct Rect near g_5A9C[];
char far * near g_574E = (char far *)&g_5A9C[0];
"""
HANDLE_WRONG = RECT + """extern struct Rect near g_5A9C[];
char far * near g_574E = (char far *)&g_5A9C[1];
"""
ACTIVE_OK = RECT + """extern struct Rect near g_5A9C[];
struct Rect far * near g_5AAC = 0;
"""
ACTIVE_WRONG = RECT + """extern struct Rect near g_5A9C[];
struct Rect far * near g_5AAC = &g_5A9C[0];
"""

CONSUMER = RECT + """extern struct Rect near g_5A9C[];
extern char far * near g_574E;
extern struct Rect far * near g_5AAC;
extern unsigned int near g_5AAE;
extern int far fd_55B3_5AA0[2];
extern int far puts(char far *text);

int main(void)
{
    struct Rect copy[2];
    union PointerWords {
        struct { unsigned offset; unsigned segment; } words;
        struct Rect far *pointer;
    } pointer_parts;

    if (sizeof(int) != 2 || sizeof(struct Rect) != 8)
        goto fail;
    if (g_5A9C[0].left != 0 || g_5A9C[0].top != 0 ||
        g_5A9C[0].right != 349 || g_5A9C[0].bottom != 639)
        goto fail;
    if (fd_55B3_5AA0[0] != 349 || fd_55B3_5AA0[1] != 639)
        goto fail;
    if (g_5A9C[1].left != RECT_END || g_5A9C[1].top != RECT_END ||
        g_5A9C[1].right != RECT_END || g_5A9C[1].bottom != RECT_END)
        goto fail;
    if (g_574E != (char far *)&g_5A9C[0] || g_5AAC != 0)
        goto fail;
    if ((char near *)&g_5AAE != (char near *)&g_5AAC + 2)
        goto fail;

    copy[0] = g_5A9C[0];
    copy[1] = g_5A9C[1];
    if (copy[1].left != RECT_END || copy[1].top != RECT_END ||
        copy[1].right != RECT_END || copy[1].bottom != RECT_END)
        goto fail;

    g_5AAC = &g_5A9C[0];
    pointer_parts.pointer = g_5AAC;
    if (g_5AAE != pointer_parts.words.segment)
        goto fail;
    g_5A9C[0].right = 347;
    g_5A9C[0].bottom = 637;
    if (fd_55B3_5AA0[0] != 347 || fd_55B3_5AA0[1] != 637)
        goto fail;
    puts("PASS");
    return 0;
fail:
    puts("FAIL");
    return 0;
}
"""


def compile_source(stem: str, source: str, dos_name: str | None = None) -> tuple[bytes, Path, str]:
    source_path = SRC / f"{stem}.c"
    source_path.write_text(source, encoding="ascii")
    object_name = (dos_name or stem).upper()
    if len(object_name) > 8:
        raise RuntimeError(f"DOS compiler basename exceeds 8.3 limit: {object_name}")
    result = compiler.compile_c(source, PROFILE, FLAGS, basename=object_name, keep=True)
    if not result.ok:
        raise RuntimeError(f"MSC compile failed for {stem}: {result.log[-1500:]}")
    object_path = OBJ / f"{object_name}.OBJ"
    object_path.write_bytes(result.obj)
    (CC / f"{stem}.log").write_text(result.log, encoding="latin1")
    return result.obj, source_path, result.log


def pinned_file(path: Path, expected_sha: str, role: str) -> dict:
    actual = digest(path)
    if actual != expected_sha:
        raise RuntimeError(f"{role} tool hash mismatch: {path}")
    return {"role": role, "path": str(path), "sha256": actual,
            "size": path.stat().st_size, "verified": True}


def project_paths() -> tuple[dict, dict, dict]:
    manifest = json.loads((ROOT / "layout" / "manifest.json").read_text(encoding="utf-8"))
    toolchain = json.loads((ROOT / "layout" / "toolchain.json").read_text(encoding="utf-8"))
    return manifest, toolchain, toolchain["runners"]["dosbox-x"]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture(linker_name: str, linker: dict, dosbox: dict, libraries: list[Path],
            objects: dict[str, bytes], case: str, expected: str, alias_delta: int,
            rect_alias_delta: int) -> dict:
    directory = RUN / "fixtures" / linker_name / case
    directory.mkdir(parents=True)
    file_names = {"CONSUMER": "CRT.OBJ", "SCREEN": "SCREEN.OBJ",
                  "HANDLE": "HANDLE.OBJ", "ACTIVE": "ACTIVE.OBJ"}
    for key, data in objects.items():
        (directory / file_names[key]).write_bytes(data)
    for path in libraries:
        shutil.copyfile(path, directory / path.name.upper())

    link_text = (
        "OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n"
        "LIBRARY LLIBCR, LIBH\r\nFILE CRT\r\nBEGINAREA\r\n"
        "SECTION FILE SCREEN\r\nSECTION FILE HANDLE\r\nSECTION FILE ACTIVE\r\n"
        "ENDAREA\r\n"
        f"DEFINE _g_5AAE = _g_5AAC + {alias_delta}\r\n"
        f"DEFINE _fd_55B3_5AA0 = _g_5A9C + {rect_alias_delta}\r\n"
    )
    (directory / "PROBE.LNK").write_bytes(link_text.encode("ascii"))
    (directory / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    tool_dir = Path(linker["directory"])
    (directory / "RUN.BAT").write_bytes((
        f"@echo off\r\nD:\\{linker['executable']} @PROBE.LNK < NUL > LINK.LOG\r\n"
        "PROBE.EXE > RUN.LOG\r\n").encode("ascii"))
    config = []
    for section, options in dosbox["conf"].items():
        config.append("[" + section + "]")
        config.extend(f"{key}={value}" for key, value in options.items())
    config.extend(["[autoexec]", f'mount c "{directory.resolve()}"',
                   f'mount d "{tool_dir}" -ro', "c:", "call RUN.BAT", "exit"])
    (directory / "dosbox.conf").write_text("\n".join(config) + "\n", encoding="ascii")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    try:
        run = subprocess.run([dosbox["path"], "-conf", str(directory / "dosbox.conf"),
                              "-fastlaunch", "-exit", "-nomenu"], cwd=directory, env=env,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             timeout=75, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        timed_out = False
    except subprocess.TimeoutExpired:
        run = type("Timeout", (), {"returncode": -1})()
        timed_out = True
    actual = ((directory / "RUN.LOG").read_text(encoding="latin1").strip()
              if (directory / "RUN.LOG").exists() else "NO RUN.LOG")
    return {"linker": linker_name, "case": case, "expected": expected,
            "actual": actual, "passed": actual == expected and run.returncode == 0 and
            (directory / "PROBE.EXE").is_file() and not timed_out,
            "alias_delta": alias_delta, "rect_alias_delta": rect_alias_delta,
            "timeout": timed_out,
            "linker_log_present": (directory / "LINK.LOG").is_file(),
            "map_present": (directory / "PROBE.MAP").is_file()}


def main() -> int:
    manifest, toolchain, dosbox = project_paths()
    runtime = manifest["runtime"]["libraries"]
    libraries = [Path(runtime[name]["path"]) for name in ("llibcr.lib", "libh.lib")]
    cases = {
        "positive": ("positive", "handle_ok", "active_ok", "PASS", 2, 4),
        "far_data_owner": ("far_data", "handle_ok", "active_ok", "FAIL", 2, 4),
        "wrong_fields": ("wrong_fields", "handle_ok", "active_ok", "FAIL", 2, 4),
        "wrong_order": ("wrong_order", "handle_ok", "active_ok", "FAIL", 2, 4),
        "partial_sentinel": ("partial_sentinel", "handle_ok", "active_ok", "FAIL", 2, 4),
        "wide_fields": ("wide_fields", "handle_ok", "active_ok", "FAIL", 2, 4),
        "wrong_static_handle": ("positive", "handle_wrong", "active_ok", "FAIL", 2, 4),
        "wrong_active_pointer": ("positive", "handle_ok", "active_wrong", "FAIL", 2, 4),
        "wrong_segment_alias": ("positive", "handle_ok", "active_ok", "FAIL", 4, 4),
        "wrong_rect_alias": ("positive", "handle_ok", "active_ok", "FAIL", 2, 6),
    }
    owner_objs: dict[str, bytes] = {}
    compile_names = {"positive": "SCPOS", "far_data": "SCFAR",
                     "wrong_fields": "SCFLD", "wrong_order": "SCORD",
                     "partial_sentinel": "SCSEN", "wide_fields": "SCWID"}
    for case, dos_name in compile_names.items():
        owner_objs[case] = compile_source("screen_" + case,
                                          owner_source(case), dos_name)[0]
    handle_objs = {
        "handle_ok": compile_source("handle_ok", HANDLE_OK, "HNDOK")[0],
        "handle_wrong": compile_source("handle_wrong", HANDLE_WRONG, "HNDWR")[0],
    }
    active_objs = {
        "active_ok": compile_source("active_ok", ACTIVE_OK, "ACTOK")[0],
        "active_wrong": compile_source("active_wrong", ACTIVE_WRONG, "ACTWR")[0],
    }
    consumer_obj = compile_source("consumer", CONSUMER, "CONSUM")[0]

    # Check the candidate's typed values semantically from its freshly compiled
    # OMF contribution. The report never stores an object-byte dump.
    screen = OmfReader().read(owner_objs["positive"])
    public = next((p for p in screen.publics if p["name"].lower() == "_g_5a9c"), None)
    if public is None:
        raise RuntimeError("candidate screen public is absent from its object")
    group_members = {
        group["name"]: {screen.segment_defs[index - 1]["name"]
                        for index in group["segment_indices"]}
        for group in screen.groups
    }
    candidate_in_dgroup = public["segment"] in group_members.get("DGROUP", set())
    if not candidate_in_dgroup:
        raise RuntimeError(
            f"near candidate is not emitted in DGROUP: {public['segment']}; groups={group_members}")
    payload = screen.segments.get(public["segment"], b"")
    start = public["offset"]
    if len(payload) < start + 16:
        raise RuntimeError("candidate object does not contribute the complete two-Rect initializer")
    observed = [int.from_bytes(payload[i:i + 2], "little", signed=True)
                for i in range(start, start + 16, 2)]
    if observed != [0, 0, 349, 639, -32768, -32768, -32768, -32768]:
        raise RuntimeError("candidate OMF words differ from its typed semantic initializer")
    if screen.fixups:
        raise RuntimeError("the two-Rect initialized object unexpectedly contains relocations")
    handle = OmfReader().read(handle_objs["handle_ok"])
    handle_public = next((p for p in handle.publics if p["name"].lower() == "_g_574e"), None)
    if handle_public is None:
        raise RuntimeError("static screen-handle public is absent from its object")
    handle_fixups = [f for f in handle.fixups
                     if f["segment"] == handle_public["segment"]
                     and handle_public["offset"] <= f["offset"] < handle_public["offset"] + 4]
    if not any(f["loc"] == "pointer32"
               and f["target_kind"] == "external"
               and f["target"].lower() == "_g_5a9c"
               for f in handle_fixups):
        raise RuntimeError("static far handle does not carry a symbolic relocation to the screen owner")
    active = OmfReader().read(active_objs["active_ok"])
    active_public = next((p for p in active.publics if p["name"].lower() == "_g_5aac"), None)
    if active_public is None:
        raise RuntimeError("initial active clip-pointer public is absent from its object")
    active_payload = active.segments.get(active_public["segment"], b"")
    if active_payload[active_public["offset"]:active_public["offset"] + 4] != b"\0\0\0\0":
        raise RuntimeError("initial active clip pointer is not a four-byte zero value")
    if any(f["segment"] == active_public["segment"]
           and active_public["offset"] <= f["offset"] < active_public["offset"] + 4
           for f in active.fixups):
        raise RuntimeError("initial active clip pointer unexpectedly has a static relocation")
    far_screen = OmfReader().read(owner_objs["far_data"])
    far_public = next((p for p in far_screen.publics if p["name"].lower() == "_g_5a9c"), None)
    if far_public is None:
        raise RuntimeError("far-data contrast screen public is absent from its object")
    far_group_members = {
        group["name"]: {far_screen.segment_defs[index - 1]["name"]
                        for index in group["segment_indices"]}
        for group in far_screen.groups
    }
    far_owner_in_dgroup = far_public["segment"] in far_group_members.get("DGROUP", set())
    if far_owner_in_dgroup:
        raise RuntimeError("far-data contrast unexpectedly belongs to DGROUP")

    toolchain_pins = []
    profile = toolchain["profiles"][PROFILE]
    runner = toolchain["runners"][profile["runner"]]
    toolchain_pins.append(pinned_file(Path(runner["path"]), runner["sha256"], "DOSBox-X runner"))
    for rel, expected_sha in profile["files"].items():
        path = Path(profile["directory"]) / rel
        toolchain_pins.append(pinned_file(path, expected_sha, "MSC 6.00AX compiler"))
    for path in libraries:
        expected = next(row["sha256"] for name, row in runtime.items()
                        if Path(row["path"]) == path)
        toolchain_pins.append(pinned_file(path, expected, "C runtime library"))
    for linker_name in ("rtlink400", "rtlink610"):
        row = toolchain["linkers"][linker_name]
        for rel, expected_sha in row["files"].items():
            path = Path(row["directory"]) / rel
            toolchain_pins.append(pinned_file(path, expected_sha, linker_name))
    # DOSBox-X is the same runner as the profile runner; keep its role explicit.
    if digest(Path(dosbox["path"])) != dosbox["sha256"]:
        raise RuntimeError("DOSBox-X tool hash mismatch")
    toolchain_pins.append(pinned_file(Path(dosbox["path"]), dosbox["sha256"], "DOSBox-X DOS runtime"))
    source_pins, source_census_sha = verify_source_pins()
    pin_report = RUN / "input-pins-v1.json"
    pin_report.write_text(json.dumps({
        "schema": "simant-screen-list-probe-input-pins-v1",
        "source_census": {"count": len(source_pins),
                          "census_sha256": source_census_sha},
        "tool_inputs": toolchain_pins,
        "runtime_libraries_copied_into_each_link_fixture": [
            {"path": str(path), "sha256": digest(path), "size": path.stat().st_size}
            for path in libraries],
    }, indent=2) + "\n", encoding="utf-8")

    observations = []
    for linker_name in ("rtlink400", "rtlink610"):
        linker = toolchain["linkers"][linker_name]
        for name, (owner_key, handle_key, active_key, expected, alias_delta,
                   rect_alias_delta) in cases.items():
            obs = fixture(linker_name, linker, dosbox, libraries,
                          {"CONSUMER": consumer_obj, "SCREEN": owner_objs[owner_key],
                           "HANDLE": handle_objs[handle_key], "ACTIVE": active_objs[active_key]},
                          name, expected, alias_delta, rect_alias_delta)
            observations.append(obs)
            print(f"{linker_name}/{name}: {obs['actual']} (expected {expected})")
    if len(observations) != 20 or not all(row["passed"] for row in observations):
        raise RuntimeError("one or more MSC/RTLink symbolic initializer controls failed")

    artifact_index = []
    for path in sorted(RUN.rglob("*")):
        if path.is_file() and path.name != "report.json":
            artifact_index.append({"path": path.relative_to(RUN).as_posix(),
                                   "sha256": digest(path), "size": path.stat().st_size})

    report = {
        "schema": "simant-screen-list-initializer-probe-v1",
        "status": "TEST_OWNED_FUNCTIONAL_SOURCE_CONTROL_ONLY",
        "historical_owner_or_placement_claimed": False,
        "oracle_asset_read": False,
        "compiler": PROFILE,
        "flags": FLAGS + toolchain["profiles"][PROFILE].get("required_flags", []),
        "candidate_semantic_words": observed,
        "candidate_two_rect_extent": 16,
        "candidate_fixup_count": len(screen.fixups),
        "candidate_storage": {"public_segment": public["segment"],
                              "dgroup_members": sorted(group_members.get("DGROUP", set())),
                              "candidate_is_dgroup_member": candidate_in_dgroup,
                              "far_control_segment": far_public["segment"],
                              "far_control_dgroup_members": sorted(far_group_members.get("DGROUP", set())),
                              "far_control_is_dgroup_member": far_owner_in_dgroup},
        "static_handle_fixups": [
            {key: fixup[key] for key in ("segment", "offset", "loc", "target_kind", "target", "displacement")}
            for fixup in handle_fixups],
        "active_pointer_initial_state": {"public_segment": active_public["segment"],
                                          "bytes_are_zero": True,
                                          "relocation_count": 0},
        "linkers": ["rtlink400", "rtlink610"],
        "cases": observations,
        "toolchain_pins": toolchain_pins,
        "accepted_source_census_count": len(source_pins),
        "accepted_source_census_sha256": source_census_sha,
        "input_pin_manifest": "input-pins-v1.json",
        "artifact_index": artifact_index,
        "limitations": [
            "These are isolated test-owned data objects and symbolic aliases, not SimAnt's historical object link order.",
            "A passing positive case supports source representation and the listed field/pointer contrasts only.",
            "No game function is linked or executed; source-consumer and full-copy evidence remains in review-v35.md.",
            "The candidate initializer values come from approved typed metadata, never an original-byte fallback."
        ]
    }
    report_path = RUN / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"report: {report_path.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
