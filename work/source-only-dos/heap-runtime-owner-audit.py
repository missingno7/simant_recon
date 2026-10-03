#!/usr/bin/env python3
"""Audit the pinned __fheap archive candidate without reading the original EXE."""
from __future__ import annotations

import hashlib
import argparse
import json
from pathlib import Path
import sys


def find_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if ((parent / "README.md").is_file()
                and (parent / "tools/source_only_dos.py").is_file()
                and (parent / "src").is_dir()):
            return parent
    raise SystemExit("could not locate repository root")


ROOT = find_root()
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--build-report", type=Path,
                    default=Path("build/workers/dos_fheap_runtime_ownership/compile-v1/build-report.json"),
                    help="guarded source-only object-compile report to audit")
parser.add_argument("--out", required=True, type=Path,
                    help="fresh ignored JSON receipt under repository build/")
args = parser.parse_args()
BUILD_REPORT = args.build_report if args.build_report.is_absolute() else ROOT / args.build_report
BUILD_REPORT = BUILD_REPORT.resolve()
OUT = args.out if args.out.is_absolute() else ROOT / args.out
OUT = OUT.resolve()
BUILD_ROOT = (ROOT / "build").resolve()
if not BUILD_REPORT.is_relative_to(BUILD_ROOT) or not BUILD_REPORT.is_file():
    raise SystemExit("--build-report must be an existing file under repository build/")
if not OUT.is_relative_to(BUILD_ROOT):
    raise SystemExit("--out must resolve below repository build/")
if OUT.exists():
    raise SystemExit("output file already exists; choose a fresh ignored build/ path")
OUT.parent.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "tools"))
import source_only_dos as dos  # noqa: E402
from omf import OmfReader  # noqa: E402

DENIED_ORACLE_READS = dos.install_input_guard()
MANIFEST_PATH = ROOT / "layout/manifest.json"
SOURCE_PATH = ROOT / "src/root/m171C.c"
RUNTIME_PATH = Path(r"C:/tools/msc-6.00/LIB/llibcr.lib")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pin(path: Path) -> dict:
    raw = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT)
            else path.as_posix(), "size": len(raw), "sha256": sha(raw)}


def load_obj(path_value: str, name: str, reader: OmfReader):
    path = Path(path_value)
    if not path.is_absolute():
        path = ROOT / path
    return reader.read(path.read_bytes(), name)


report = json.loads(BUILD_REPORT.read_text(encoding="utf-8"))
manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
runtime = manifest["runtime"]
library_pin = pin(RUNTIME_PATH)
expected_library = runtime["libraries"]["llibcr.lib"]
if library_pin["sha256"] != expected_library["sha256"]:
    raise SystemExit("selected LLIBCR identity differs from the pinned manifest")

unresolved = next(row for row in report["unresolved_data"] if row["id"] == "dgroup_79f0")
if (report["status"] != "INCOMPLETE"
        or len(report["translation_units"]) != 138
        or len(report.get("unresolved_symbols", [])) != 368
        or any(report["original_exe_bytes_used"].values())
        or report.get("denied_oracle_reads") not in (None, [])):
    raise SystemExit("expected historical checkpoint a9b1d1a (v12, 138 TUs/368 symbols) with zero oracle use")

rd = OmfReader(communals=True)
library_blobs = rd.split_library(RUNTIME_PATH.read_bytes())
by_index = {i: (name, blob, rd.read(blob, name))
            for i, (name, blob) in enumerate(library_blobs)}

fdata = [(i, name, blob, obj) for i, (name, blob, obj) in by_index.items()
         if name.lower() == "fdata.asm"]
if len(fdata) != 1:
    raise SystemExit(f"expected one pinned fdata.asm module, found {len(fdata)}")
fdata_index, fdata_name, fdata_blob, fdata_obj = fdata[0]
fdata_segments = {name: len(data) for name, data in fdata_obj.segments.items()}
fdata_publics = [row for row in fdata_obj.publics if row["name"] == "__fheap"]
if (fdata_index != 51 or fdata_segments.get("_DATA") != 14
        or len(fdata_publics) != 1 or fdata_publics[0]["offset"] != 0
        or fdata_obj.linker_fixups or fdata_obj.externals):
    raise SystemExit("pinned fdata.asm shape/publics changed")

selected_code = {(row["library"].lower(), row["module_index"]): row
                 for row in runtime["members"]}
selected_data = {(row["library"].lower(), row["module_index"]): row
                 for row in runtime.get("data_members", [])}

fheap_consumers = []
for index, (name, blob, obj) in by_index.items():
    sites = [row for row in obj.linker_fixups
             if row["target_kind"] == "external" and row["target"] == "__fheap"]
    if sites:
        key = ("llibcr.lib", index)
        fheap_consumers.append({"module_index": index, "member": name,
                                "selected_runtime_code": key in selected_code,
                                "selected_runtime_data": key in selected_data,
                                "__fheap_fixup_sites": [
                                    {k: row[k] for k in ("segment", "offset", "loc", "displacement")}
                                    for row in sites]})

selected_fheap_refs = []
for key, row in selected_code.items():
    library_name, module_index = key
    if library_name != "llibcr.lib" or module_index not in by_index:
        continue
    name, _blob, obj = by_index[module_index]
    for fixup in obj.linker_fixups:
        if fixup["target_kind"] == "external" and fixup["target"] == "__fheap":
            selected_fheap_refs.append({"member": name, "module_index": module_index,
                                        "offset": fixup["offset"]})

app_refs = []
app_publics = {}
for unit in report["translation_units"]:
    if unit.get("status") != "COMPILED" or not unit.get("object"):
        continue
    obj = load_obj(unit["object"]["path"], unit["module"], rd)
    code_names = {row["name"] for row in obj.segment_defs
                  if str(row.get("class", "")).upper().endswith("CODE")}
    for public in obj.publics:
        if public["name"] in {"_malloc", "_free", "__ffree", "__frealloc", "__fmalloc"}:
            app_publics.setdefault(public["name"], []).append({
                "module": unit["module"], "segment": public["segment"],
                "offset": public["offset"], "object_sha256": unit["object"]["sha256"]})
    for fixup in obj.linker_fixups:
        if (fixup["segment"] in code_names and fixup["target_kind"] == "external"
                and fixup["target"] in {"_malloc", "_free", "__ffree", "__frealloc",
                                        "__fheap", "__fmalloc", "__fexpand", "__fheapchk",
                                        "__fheapwalk", "__fheapmin"}):
            app_refs.append({"module": unit["module"], "segment": fixup["segment"],
                             "offset": fixup["offset"], "target": fixup["target"],
                             "loc": fixup["loc"], "object_sha256": unit["object"]["sha256"]})

if app_publics.get("_malloc") is None or app_publics.get("_free") is None:
    raise SystemExit("source-built game allocator definitions are missing")
far_heap_api_names = {"__fheap", "__fmalloc", "__fexpand", "__fheapchk",
                      "__fheapwalk", "__fheapmin"}
unresolved_far_heap_imports = sorted({row["target"] for row in app_refs
                                      if row["target"] in far_heap_api_names
                                      and row["target"] not in app_publics})
if unresolved_far_heap_imports:
    raise SystemExit("source-built application has unresolved far-heap API imports: "
                     + ", ".join(unresolved_far_heap_imports))
if selected_fheap_refs:
    raise SystemExit("selected runtime code imports __fheap")
if not fheap_consumers or all(
        row["selected_runtime_code"] or row["selected_runtime_data"] for row in fheap_consumers):
    raise SystemExit("fheap consumer/member selection result changed; review audit")

source_bytes = SOURCE_PATH.read_bytes()
source_text = source_bytes.decode("latin1")
source_lines = source_text.splitlines()
source_anchors = []
for line_number, line in enumerate(source_lines, 1):
    if ("malloc(unsigned size)" in line or "_ffree(char far *p)" in line
            or "return f_171C_21CC(size);" in line or "f_171C_13CA" in line
            or "void far free(void far *p)" in line or "_ffree(p);" in line):
        source_anchors.append({"line": line_number, "text": line.strip()})

runtime_users = []
for index, (name, _blob, obj) in by_index.items():
    refs = [row for row in obj.linker_fixups
            if row["target_kind"] == "external" and row["target"] in {"_malloc", "_free"}]
    if refs and ("llibcr.lib", index) in selected_code:
        runtime_users.append({"member": name, "module_index": index,
                              "publics": [p["name"] for p in obj.publics],
                              "references": sorted({r["target"] for r in refs})})

result = {
    "schema": "simant-dgroup-fheap-runtime-selection-research-v1",
    "status": "NO_FUNCTIONAL_OWNER_PROVEN",
    "scope": "source-only runtime ownership audit for approved dgroup_79f0 14-byte debt; no historical image bytes used",
    "debt": {k: unresolved.get(k) for k in ("id", "classification", "size", "semantic_assessment")},
    "source_only_compile": {
        "report": pin(BUILD_REPORT), "status": report["status"],
        "source_checkpoint": {
            "label": "historical checkpoint a9b1d1a (v12)",
            "git_commit": "a9b1d1ab7438dcfb9b608843e22999104bea2b27",
            "snapshot_note": "138-TU / 368-unresolved-symbol compile snapshot; not the concurrently preparing v13 working tree",
        },
        "translation_unit_count": len(report["translation_units"]),
        "compiled_translation_unit_count": sum(row.get("status") == "COMPILED"
                                                for row in report["translation_units"]),
        "unresolved_symbol_count": len(report.get("unresolved_symbols", [])),
        "original_exe_bytes_used": report["original_exe_bytes_used"],
        "denied_oracle_reads": report.get("denied_oracle_reads", []),
        "errors": report["errors"],
        "link_attempted": False,
        "source_only_runtime_link_proof": "NOT_PRODUCED",
        "why_no_link": "The guarded compile report is INCOMPLETE: unresolved data dispositions, source symbols and address/layout contracts fail the link preflight.",
    },
    "pinned_runtime_candidate": {
        "library": library_pin,
        "manifest_runtime_identity": expected_library,
        "member": fdata_name,
        "module_index": fdata_index,
        "member_object_sha256": sha(fdata_blob),
        "text_extent": fdata_obj.segment_lengths.get("_TEXT", 0),
        "data_segments": fdata_segments,
        "publics": fdata_publics,
        "external_symbols": fdata_obj.externals,
        "fixups": fdata_obj.linker_fixups,
        "selected_runtime_member": False,
        "selected_runtime_data_member": False,
    },
    "candidate_member_call_graph": {
        "direct_consumers_of___fheap": fheap_consumers,
        "selected_runtime_code_references_to___fheap": selected_fheap_refs,
        "none_of_direct_consumers_selected": all(
            not row["selected_runtime_code"] and not row["selected_runtime_data"]
            for row in fheap_consumers),
    },
    "source_built_game_allocator_path": {
        "source": pin(SOURCE_PATH),
        "source_anchors": source_anchors,
        "public_definitions": app_publics,
        "application_object_callsites": app_refs,
        "selected_runtime_members_that_call_game_malloc_free": runtime_users,
        "interpretation": "Application objects import _malloc/_free, whose public definitions are emitted by root:171C. The source wrappers route malloc to f_171C_21CC/Ralloc and free to _ffree; root:171C also supplies __ffree/__frealloc, so those similarly spelled fixups stay within the game allocator. The already accepted runtime members stdalloc/_getbuf/_sftbuf/getcwd have _malloc imports and _freebuf has an _free import; the source-built game object provides those publics. The complete SOURCE_ONLY_DOS link was not reached, so this is object/import-graph evidence rather than a linked-image claim. No app object has an unresolved far-heap API import, and no selected runtime member imports __fheap.",
    },
    "conclusion": {
        "runtime_archive_contains_matching_candidate": True,
        "independent_selection_or_game_call_path_proven": False,
        "initializer_semantics_source_proven_for_source_only_game_path": False,
        "debt_bytes_to_close": 0,
        "reason": "The pinned library has a one-public data-only fdata.asm member, but it is absent from the selected runtime code/data members. Its __fheap consumers (fmalloc/frealloc/fexpand/fheap helpers) are also unselected and have no source-built application imports. The game's malloc/free path is instead owned by root:171C Ralloc. Candidate byte similarity alone cannot transfer ownership.",
    },
    "pins": {
        "manifest": pin(MANIFEST_PATH),
        "source": pin(SOURCE_PATH),
        "runtime_member_sha256": sha(fdata_blob),
    },
    "denied_oracle_reads": list(DENIED_ORACLE_READS),
}
if DENIED_ORACLE_READS:
    raise SystemExit("analysis attempted an original oracle read")
OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"report": OUT.relative_to(ROOT).as_posix(),
                  "status": result["status"],
                  "application_allocator_callsites": len(app_refs),
                  "runtime___fheap_consumers": len(fheap_consumers),
                  "selected_runtime___fheap_references": len(selected_fheap_refs),
                  "original_exe_bytes_used": report["original_exe_bytes_used"],
                  "denied_oracle_reads": DENIED_ORACLE_READS}, indent=2))
