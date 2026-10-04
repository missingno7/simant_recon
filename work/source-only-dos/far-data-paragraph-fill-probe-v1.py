#!/usr/bin/env python3
"""Reproduce the root:1F80 FAR_DATA paragraph-fill controls; write binaries only under build/."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


def find_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if ((parent / "README.md").is_file()
                and (parent / "tools/compiler.py").is_file()
                and (parent / "src").is_dir()):
            return parent
    raise SystemExit("could not locate repository root")


ROOT = find_root()
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--out", required=True, type=Path,
                    help="fresh output directory below build/workers/dos_linker_alignment_debt/")
parser.add_argument("--raw-report", type=Path,
                    default=Path("work/source-only-dos/far-data-paragraph-fill-raw-v1.json"),
                    help="durable compact receipt below work/source-only-dos/")
args = parser.parse_args()
OUT = (args.out if args.out.is_absolute() else ROOT / args.out).resolve()
SCRATCH = (ROOT / "build/workers/dos_linker_alignment_debt").resolve()
if not OUT.is_relative_to(SCRATCH) or OUT == SCRATCH:
    raise SystemExit("--out must be a fresh child of build/workers/dos_linker_alignment_debt/")
if OUT.exists():
    raise SystemExit("output directory already exists; choose a fresh scratch directory")
RAW_PATH = (args.raw_report if args.raw_report.is_absolute() else ROOT / args.raw_report).resolve()
RAW_ROOT = (ROOT / "work/source-only-dos").resolve()
if not RAW_PATH.is_relative_to(RAW_ROOT) or RAW_PATH == RAW_ROOT:
    raise SystemExit("--raw-report must be below work/source-only-dos/")

sys.path.insert(0, str(ROOT / "tools"))
import compiler  # noqa: E402
from omf import OmfReader  # noqa: E402


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_rel(relative: str) -> bytes:
    return (ROOT / relative).read_bytes()


def pin_repo(relative: str, role: str) -> dict:
    raw = read_rel(relative)
    return {"path": relative, "role": role, "size": len(raw), "sha256": sha(raw)}


def pin_external(path: Path, expected: str, role: str) -> dict:
    raw = path.read_bytes()
    actual = sha(raw)
    require(actual == expected, f"pinned {role} hash mismatch: {path}")
    return {"path": str(path).replace("\\", "/"), "role": role,
            "size": len(raw), "sha256": actual}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def pin_profile_files(kind: str, profile: dict) -> list[dict]:
    return [pin_external(Path(profile["directory"]) / relative, digest,
                         f"{kind} pinned file")
            for relative, digest in sorted(profile["files"].items())]


def map_rows(text: str) -> list[dict]:
    rows = []
    pattern = re.compile(r"^\s*([0-9A-F]+)H\s+([0-9A-F]+)H\s+([0-9A-F]+)H\s+(\S+)\s+(\S+)", re.I)
    for line in text.splitlines():
        match = pattern.match(line)
        if match:
            rows.append({"start": int(match.group(1), 16),
                         "last_offset": int(match.group(2), 16),
                         "length": int(match.group(3), 16),
                         "name": match.group(4), "class": match.group(5)})
    return rows


def write_dosbox_config(path: Path, mounted: Path, tool_tree: Path, runner: dict) -> None:
    lines = []
    for section, values in runner["conf"].items():
        lines.append(f"[{section}]")
        lines.extend(f"{key}={value}" for key, value in values.items())
    lines.extend(["[autoexec]", f'mount c "{mounted.resolve()}"',
                  f'mount d "{tool_tree}" -ro', "c:", "set LIB=C:\\;D:\\",
                  "call RUN.BAT", "exit"])
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


OUT.mkdir(parents=True)
manifest_path = "layout/manifest.json"
map_path = "work/data/s27_map.json"
ledger_path = "work/takeover/behavioral-oracle/data-debt-disposition-approved-v1.json"
toolchain_path = "layout/toolchain.json"
manifest_raw = read_rel(manifest_path)
manifest = json.loads(manifest_raw)
module = manifest["modules"]["root:1F80"]
source_rel = module["source"]
source_raw = read_rel(source_rel)
map_raw = read_rel(map_path)
ledger_raw = read_rel(ledger_path)
static_input_specs = [
    (source_rel, "accepted root:1F80 C source"),
    (manifest_path, "accepted module/object/placement manifest"),
    (map_path, "S27 range map registry"),
    (ledger_path, "historical data-debt ledger, read-only preservation pin"),
    (toolchain_path, "compiler, assembler, linker and runner identities"),
    ("tools/compiler.py", "historical compiler/assembler driver"),
    ("tools/omf.py", "OMF reader used to inspect SEGDEF and COMDEF records"),
]
input_pins = [pin_repo(path, role) for path, role in static_input_specs]
probe_rel = Path(__file__).resolve().relative_to(ROOT).as_posix()
probe_raw = Path(__file__).read_bytes()
input_pins.append({"path": probe_rel, "role": "reproducer self-pin",
                   "size": len(probe_raw), "sha256": sha(probe_raw)})
require(sha(source_raw) == module["source_sha256"], "accepted root:1F80 source hash differs from manifest")
require(sha(manifest_raw) == next(row["sha256"] for row in input_pins if row["path"] == manifest_path)
        and sha(map_raw) == next(row["sha256"] for row in input_pins if row["path"] == map_path)
        and sha(ledger_raw) == next(row["sha256"] for row in input_pins if row["path"] == ledger_path),
        "a loaded manifest/map/ledger differs from its initial input pin")

# Compile the canonical accepted TU with its registered basename. The expected object hash
# and placement are read from the manifest; no original executable or section bytes are input.
accepted_obj_result = compiler.compile_c(source_raw.decode("ascii"), module["profile"],
                                         module["flags"], basename="UNIT", keep=True)
require(accepted_obj_result.ok and accepted_obj_result.obj is not None,
        "accepted root:1F80 source did not compile")
accepted_object_sha = sha(accepted_obj_result.obj)
require(accepted_object_sha == module["object_sha256"],
        "canonical-basename object does not match root:1F80 manifest object hash")
accepted_omf = OmfReader(communals=True).read(accepted_obj_result.obj)
accepted_seg = next((row for row in accepted_omf.segment_defs if row.get("name") == "UNIT5_DATA"), None)
require(accepted_seg is not None, "accepted object lacks UNIT5_DATA")
accepted_place = module["placements"]["UNIT5_DATA"]
require((accepted_seg.get("class"), accepted_seg.get("alignment"), accepted_seg.get("length"))
        == ("FAR_DATA", "paragraph", 100), "accepted FAR_DATA SEGDEF identity changed")
require((accepted_place["seg"], accepted_place["off"], accepted_place["size"])
        == (0x50EF, 0, 100), "accepted FAR_DATA placement changed")
far_data_end = accepted_place["seg"] * 16 + accepted_place["off"] + accepted_place["size"]
require(far_data_end == 0x50F54, "accepted FAR_DATA exclusive end is not 50F54")

# Verify the actual S27 map schema. Its FAR_DATA map range is a 112-byte envelope ending
# where the next FAR_BSS frame begins; the accepted object itself contributes only 100 bytes.
s27_map = json.loads(map_raw)
far_data_rows = [row for row in s27_map["ranges"] if row.get("cat") == "FAR_DATA" and row.get("frame") == "50EF"]
far_bss_rows = [row for row in s27_map["ranges"] if row.get("cat") == "FAR_BSS" and row.get("frame") == "50F6"]
require(len(far_data_rows) == 1 and len(far_bss_rows) == 1,
        "S27 map does not have unique FAR_DATA/FAR_BSS rows at the expected frames")
far_data_row, far_bss_row = far_data_rows[0], far_bss_rows[0]
require((far_data_row["off"], far_data_row["linear"], far_data_row["size"])
        == ("0000", "50EF0", 112), "S27 FAR_DATA map-envelope fields changed")
require((far_bss_row["off"], far_bss_row["linear"])
        == ("0000", "50F60"), "S27 FAR_BSS base fields changed")
far_bss_base = int(far_bss_row["linear"], 16)
require(far_bss_base - far_data_end == 12, "registry gap is no longer exactly 12 bytes")
require(int(far_data_row["linear"], 16) + far_data_row["size"] == far_bss_base,
        "S27 FAR_DATA envelope no longer ends at the FAR_BSS base")

# Natural MSC controls: source variants differ only in the static FAR_DATA array extent.
fixture_sources = {
    size: (f"static char far text_buffer[{size}];\n"
           "char far tail_common[1];\n"
           "int main(void) { text_buffer[0] = tail_common[0]; return 0; }\n")
    for size in (100, 112)
}
require(fixture_sources[100].replace("[100]", "[112]") == fixture_sources[112],
        "100/112 fixture sources differ beyond their array extent")
require(all(source.count("static char far text_buffer[") == 1
            and source.count("char far tail_common[1];") == 1
            and "pad" not in source.lower() and "[12]" not in source
            for source in fixture_sources.values()),
        "fixture has an unexpected owner or padding declaration")

profile_names = ("msc600ax", "masm510")
toolchain = compiler.toolchain()
runner = toolchain["runners"]["dosbox-x"]
compiler_runner = toolchain["runner"]
tool_pins = [
    pin_repo(toolchain_path, "toolchain profile and expected tool identities"),
    pin_repo("tools/compiler.py", "compiler driver implementation"),
    pin_repo("tools/omf.py", "OMF reader implementation"),
]
tool_pins.append(pin_external(Path(compiler_runner["path"]), compiler_runner["sha256"],
                               "Microsoft tool runner"))
tool_pins.append(pin_external(Path(runner["path"]), runner["sha256"], "DOSBox-X linker runner"))
for name in profile_names:
    profile = toolchain["profiles"][name]
    tool_pins.extend(pin_profile_files(f"{name} profile", profile))
for name in ("rtlink400", "rtlink610"):
    tool_pins.extend(pin_profile_files(f"{name} profile", toolchain["linkers"][name]))

# MSC compiles the two control objects under the same large-model optimisation switches.
control_objects: dict[int, bytes] = {}
control_object_evidence = []
for size, source in fixture_sources.items():
    source_path = OUT / f"fixture_{size}.c"
    source_path.write_text(source, encoding="ascii", newline="\r\n")
    compiled = compiler.compile_c(source, module["profile"], module["flags"],
                                  basename="FIXTURE", keep=True)
    require(compiled.ok and compiled.obj is not None, f"fixture {size} failed to compile")
    object_bytes = compiled.obj
    control_objects[size] = object_bytes
    (OUT / f"fixture_{size}.obj").write_bytes(object_bytes)
    omf = OmfReader(communals=True).read(object_bytes)
    far_defs = [row for row in omf.segment_defs if row.get("class") == "FAR_DATA"]
    require(len(far_defs) == 1, f"fixture {size} does not have exactly one FAR_DATA segment")
    far_def = far_defs[0]
    require((far_def.get("alignment"), far_def.get("length")) == ("paragraph", size),
            f"fixture {size} OMF FAR_DATA SEGDEF is not paragraph-aligned length {size}")
    far_comdefs = [row for row in omf.communals if row.get("kind") == "far"]
    require(len(far_comdefs) == 1 and far_comdefs[0].get("length") == 1,
            f"fixture {size} does not have the natural one-byte far COMDEF")
    control_object_evidence.append({
        "array_size": size,
        "source": {"path": f"build/workers/dos_linker_alignment_debt/{OUT.name}/fixture_{size}.c",
                   "sha256": sha(source_path.read_bytes()), "size": source_path.stat().st_size},
        "object_sha256": sha(object_bytes),
        "far_data_segdef": {key: far_def.get(key) for key in ("name", "class", "alignment", "length", "combine")},
        "far_communal": [{key: row.get(key) for key in ("name", "kind", "count", "element_size", "length")}
                         for row in far_comdefs],
    })

# A tiny readable startup entry is an input to the controlled link only; it owns no data.
startup_source = ("STARTUP_TEXT segment para public 'CODE'\n"
                  "public _probe_start\n"
                  "_probe_start proc far\n"
                  " retf\n"
                  "_probe_start endp\n"
                  "STARTUP_TEXT ends\n"
                  "end _probe_start\n")
startup_result = compiler.assemble(startup_source, "masm510", ["/Mx"], basename="START", keep=True)
require(startup_result.ok and startup_result.obj is not None, "MASM startup control failed to assemble")
startup_object = startup_result.obj
(OUT / "START.OBJ").write_bytes(startup_object)
startup_evidence = {"source_sha256": sha(startup_source.encode("ascii")),
                    "object_sha256": sha(startup_object), "code_bytes_only": True}

link_evidence = []
for linker_name in ("rtlink400", "rtlink610"):
    linker = toolchain["linkers"][linker_name]
    tool_tree = compiler.pinned_tree(linker)
    runner_conf = runner
    per_linker = []
    for size in (100, 112):
        case_dir = OUT / linker_name / f"fixture_{size}"
        case_dir.mkdir(parents=True)
        shutil.copyfile(OUT / f"fixture_{size}.obj", case_dir / "FIXTURE.OBJ")
        shutil.copyfile(OUT / "START.OBJ", case_dir / "START.OBJ")
        (case_dir / "PROBE.LNK").write_text(
            "OUTPUT PROBE\nMAP = PROBE S,N,A,L\nNODEFLIB\nRELOAD FAR 400\n"
            "FILE START\nBEGINAREA\n SECTION FILE FIXTURE\nENDAREA\n", encoding="ascii")
        (case_dir / "RTLINK.CFG").write_text("SYNTAX = FREEFORMAT\n", encoding="ascii")
        (case_dir / "NUL.TXT").write_bytes(b"")
        (case_dir / "RUN.BAT").write_text(
            f"@echo off\r\nD:\\{linker['executable']} @PROBE.LNK < NUL.TXT > LINK.LOG\r\n",
            encoding="ascii", newline="")
        write_dosbox_config(case_dir / "dosbox.conf", case_dir, tool_tree, runner_conf)
        env = os.environ.copy()
        env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
        proc = subprocess.run([runner["path"], "-conf", str(case_dir / "dosbox.conf"),
                               "-fastlaunch", "-exit", "-nomenu"], cwd=case_dir, env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180,
                              creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        map_path_out = case_dir / "PROBE.MAP"
        exe_path_out = case_dir / "PROBE.EXE"
        log_path = case_dir / "LINK.LOG"
        require(map_path_out.is_file() and exe_path_out.is_file(),
                f"{linker_name}/{size} did not produce both map and controlled EXE; rc={proc.returncode}")
        map_text = map_path_out.read_text(encoding="latin1", errors="replace")
        rows = map_rows(map_text)
        far_data_map = [row for row in rows if row["class"] == "FAR_DATA"]
        far_bss_map = [row for row in rows if row["class"] == "FAR_BSS"]
        require(len(far_data_map) == 1 and len(far_bss_map) == 1,
                f"{linker_name}/{size} map must have one FAR_DATA and one FAR_BSS row")
        fd, fb = far_data_map[0], far_bss_map[0]
        end_exclusive = fd["start"] + fd["length"]
        gap = fb["start"] - end_exclusive
        require(fd["length"] == size, f"{linker_name}/{size} linked FAR_DATA length differs from input")
        require(gap == (12 if size == 100 else 0),
                f"{linker_name}/{size} linked gap is {gap}, expected {12 if size == 100 else 0}")
        log_bytes = log_path.read_bytes() if log_path.exists() else proc.stdout
        row = {
            "linker": linker_name,
            "array_size": size,
            "far_data": {"name": fd["name"], "start_offset": fd["start"],
                         "length": fd["length"], "end_exclusive_offset": end_exclusive},
            "far_bss": {"name": fb["name"], "start_offset": fb["start"], "length": fb["length"]},
            "gap_bytes": gap,
            "outputs": {
                "map_sha256": sha(map_path_out.read_bytes()),
                "exe_sha256": sha(exe_path_out.read_bytes()),
                "exe_size": exe_path_out.stat().st_size,
                "link_log_sha256": sha(log_bytes),
                "link_script_sha256": sha((case_dir / "PROBE.LNK").read_bytes()),
                "dosbox_config_sha256": sha((case_dir / "dosbox.conf").read_bytes()),
            },
        }
        per_linker.append(row)
    require(per_linker[0]["far_bss"]["start_offset"] == per_linker[1]["far_bss"]["start_offset"],
            f"{linker_name} moved FAR_BSS when FAR_DATA grew by 12")
    link_evidence.extend(per_linker)

for linker_name in ("rtlink400", "rtlink610"):
    pair = [row for row in link_evidence if row["linker"] == linker_name]
    require([row["gap_bytes"] for row in pair] == [12, 0],
            f"{linker_name} pair is not the exact 12/0 positive/negative contrast")
    require(pair[0]["far_bss"]["start_offset"] == pair[1]["far_bss"]["start_offset"],
            f"{linker_name} pair does not keep the same FAR_BSS start")

ledger = json.loads(ledger_raw)
require(ledger["summary"]["total_explicit_bytes"] == 113,
        "historical approved data-debt ledger no longer reports 113 bytes")
ledger_far = next(row for row in ledger["spans"] if row["id"] == "far_data")
require(ledger_far["size"] == 12 and ledger_far["status"] == "APPROVED_DISPOSITION",
        "historical far_data ledger record changed unexpectedly")

for pinned in input_pins:
    if pinned["path"].startswith("work/") or pinned["path"].startswith("layout/") or pinned["path"].startswith("src/") or pinned["path"].startswith("tools/"):
        require(pin_repo(pinned["path"], pinned["role"]) == pinned,
                f"repository input changed during run: {pinned['path']}")
for pinned in tool_pins:
    require(pin_external(Path(pinned["path"]), pinned["sha256"], pinned["role"]) == pinned,
            f"external tool input changed during run: {pinned['path']}")

receipt = {
    "schema": "simant-far-data-paragraph-fill-evidence-v1",
    "status": "CANDIDATE_FOR_PARENT_REVIEW",
    "root_reviewed": False,
    "admitted": False,
    "scope": "Only the 12-byte functional paragraph-fill candidate at linear 50F54..50F5F.",
    "conclusion": "The accepted 100-byte paragraph-aligned FAR_DATA extent ends at 50F54; the next FAR_BSS frame begins at 50F60. Natural MSC/RTLink 4.00 and 6.10 controls reproduce a 12-byte gap for a 100-byte contribution and no gap for a 112-byte contribution while keeping the following FAR_BSS start fixed.",
    "accepted_module": {
        "module": "root:1F80",
        "source": source_rel,
        "profile": module["profile"],
        "flags": module["flags"],
        "manifest_source_sha256": module["source_sha256"],
        "actual_source_sha256": sha(source_raw),
        "manifest_object_sha256": module["object_sha256"],
        "recompiled_object_sha256": accepted_object_sha,
        "object_hash_matches_manifest": accepted_object_sha == module["object_sha256"],
        "far_data_segdef": {key: accepted_seg.get(key) for key in ("name", "class", "alignment", "length", "combine")},
        "manifest_placement": accepted_place,
        "source_extent_end_linear": f"{far_data_end:05X}",
    },
    "registry_assertions": {
        "source": map_path,
        "schema": "work/data/s27_map.json top-level ranges[] records",
        "range_fields": sorted(far_data_row.keys()),
        "far_data_map_row": {key: far_data_row.get(key) for key in ("frame", "off", "linear", "cat", "size", "owner", "status")},
        "far_bss_map_row": {key: far_bss_row.get(key) for key in ("frame", "off", "linear", "cat", "size", "owner", "status")},
        "accepted_segment_end": f"{far_data_end:05X}",
        "far_bss_base": f"{far_bss_base:05X}",
        "gap_bytes": far_bss_base - far_data_end,
        "map_envelope_end_matches_far_bss": True,
    },
    "controls": {
        "sole_source_variant": "static far array extent 100 versus 112; both use a natural one-byte far COMDEF tail_common",
        "compiler": "MSC 6.00AX, manifest profile msc600ax, accepted root:1F80 flags",
        "fixtures": control_object_evidence,
        "startup_control": startup_evidence,
        "linker_profile_notes": {name: toolchain["linkers"][name].get("status", toolchain["linkers"][name].get("note"))
                                 for name in ("rtlink400", "rtlink610")},
        "compiler_translation_unit_include_inputs": [],
        "linker_results": link_evidence,
        "assertions": {
            "accepted_source_and_object_match_manifest": True,
            "accepted_far_data_end_is_50F54": True,
            "registry_far_bss_base_is_50F60": True,
            "rtlink400_gaps_are_12_then_0_with_same_far_bss_start": True,
            "rtlink610_gaps_are_12_then_0_with_same_far_bss_start": True,
        },
    },
    "historical_boundary": {
        "approved_ledger": ledger_path,
        "total_explicit_bytes_before_and_after": 113,
        "far_data_historical_status": ledger_far["status"],
        "historical_ledger_edited": False,
        "functional_alignment_candidate_does_not_claim_historical_owner_or_rewrite_bytes": True,
    },
    "explicit_exclusions": {
        "common_tail_overlap_3": "UNADMITTED; this packet makes no finding or debt-count change for the three tail-overlap bytes",
        "extra_padding_C_owner": "NONE; fixtures define no C object for the 12-byte gap",
        "original_executable_inputs": 0,
        "canonical_source_or_layout_edits": 0,
        "production_tool_edits": 0,
    },
    "inputs": input_pins,
    "pinned_tool_inputs": tool_pins,
    "scratch_output": OUT.relative_to(ROOT).as_posix(),
    "reproduce": f"python {probe_rel} --out build/workers/dos_linker_alignment_debt/<fresh-run-dir>",
}
receipt_path = OUT / "far-data-paragraph-fill-raw-v1.json"
receipt_bytes = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8")
receipt_path.write_bytes(receipt_bytes)
RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
RAW_PATH.write_bytes(receipt_bytes)
print(json.dumps({"status": receipt["status"], "raw_report": str(RAW_PATH),
                  "scratch_output": str(OUT), "accepted_object_hash_matches": True,
                  "registry_gap_bytes": receipt["registry_assertions"]["gap_bytes"],
                  "link_gaps": [{"linker": row["linker"], "array_size": row["array_size"],
                                 "gap_bytes": row["gap_bytes"],
                                 "far_bss_start": row["far_bss"]["start_offset"]}
                                for row in link_evidence]}, indent=2))
