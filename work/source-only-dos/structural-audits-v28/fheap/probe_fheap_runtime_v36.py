#!/usr/bin/env python3
"""Natural typed __fheap runtime probe; no original image or allocator stubs."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
import compiler  # noqa: E402
import rtlink  # noqa: E402
from omf import OmfReader  # noqa: E402

SOURCE = OUT / "fheap_runtime_probe_v36.c"
compiler.WORK = OUT / "tool-scratch"
source = SOURCE.read_text(encoding="ascii")
compiled = compiler.compile_c(source, "msc600ax", ["/AL", "/Oeg", "/Gs"],
                              basename="PROBE", keep=True)
if not compiled.ok or compiled.obj is None:
    raise SystemExit(f"MSC compile failed:\n{compiled.log}")
reader = OmfReader(communals=True)
obj = reader.read(compiled.obj, "PROBE")
object_path = OUT / "PROBE.OBJ"
object_path.write_bytes(compiled.obj)
references = sorted({fix["target"] for fix in obj.linker_fixups
                     if fix["target_kind"] == "external"})
expected = {"_malloc", "_free", "__fmalloc", "__frealloc", "__ffree", "__fheap"}
if not expected.issubset(set(references)):
    raise SystemExit(f"natural fixture missing runtime references: {sorted(expected-set(references))}; got {references}")

results = []
for linker in ("rtlink400", "rtlink610"):
    case = OUT / "links" / linker
    case.mkdir(parents=True, exist_ok=True)
    (case / "PROBE.OBJ").write_bytes(compiled.obj)
    (case / "T.LNK").write_text(
        "OUTPUT PROBE\nMAP = PROBE S,N,A,L,V,X\nNODEFLIB\n"
        "FILE PROBE\nLIBRARY LLIBCR, LIBH\nVERBOSE\n",
        encoding="ascii", newline="\r\n")
    rc = rtlink.run_link(case, profile=linker, timeout=240)
    log_path = case / "LINK.LOG"
    map_path = case / "PROBE.MAP"
    log = log_path.read_text(encoding="latin1", errors="replace") if log_path.exists() else ""
    map_text = map_path.read_text(encoding="latin1", errors="replace") if map_path.exists() else ""
    if rc != 0 or not map_text or "OUTPUT PROBE" not in log.upper():
        raise SystemExit(f"RTLink {linker} failed rc={rc}: {log[-1200:]}")
    members = re.findall(r"LLIBCR\.LIB\(([^)]+)\)", log, re.IGNORECASE)
    public_addresses = {}
    for symbol in ("_malloc", "_free", "__fmalloc", "__frealloc", "__ffree", "__fheap"):
        found = re.search(rf"^\s*([0-9A-Fa-f]+:[0-9A-Fa-f]+)\s+{re.escape(symbol)}(?:\s|$)",
                          map_text, re.MULTILINE)
        public_addresses[symbol] = found.group(1) if found else None
    if any(address is None for address in public_addresses.values()):
        raise SystemExit(f"RTLink {linker} map lacks runtime publics: {public_addresses}")
    if not any("fdata.asm" == name.lower() for name in members):
        raise SystemExit(f"RTLink {linker} did not select fdata.asm")
    selected = []
    library = Path("C:/tools/msc-6.00/LIB/llibcr.lib")
    archive = {name.lower(): (name, blob) for name, blob in reader.split_library(library.read_bytes())}
    for member in members:
        if member.lower() not in archive:
            raise SystemExit(f"selected member missing from pinned archive: {member}")
        real_name, blob = archive[member.lower()]
        linked_obj = reader.read(blob, real_name)
        pub = sorted({p["name"] for p in linked_obj.publics})
        refs = sorted({fix["target"] for fix in linked_obj.linker_fixups
                       if fix["target_kind"] == "external"})
        if real_name.lower() in {"malloc.asm", "free.asm", "fmalloc.asm",
                                 "frealloc.asm", "fdata.asm"}:
            selected.append({"member": real_name,
                             "publics": [x for x in pub if x in expected],
                             "external_fixups": [x for x in refs if x in expected],
                             "data_lengths": {k: len(v) for k, v in linked_obj.segments.items()
                                              if k in {"_DATA", "CONST", "_BSS"}},
                             "fheap_initializer_hex": linked_obj.segments.get("_DATA", b"").hex()
                             if real_name.lower() == "fdata.asm" else None})
    results.append({"linker": linker, "return_code": rc, "selected_members": members,
                    "runtime_public_addresses": public_addresses,
                    "runtime_heap_members": selected,
                    "linked_exe_executed": False})

trigger_source_path = OUT / "fheap_api_trigger_v36.c"
trigger_source = trigger_source_path.read_text(encoding="ascii")
trigger_compiled = compiler.compile_c(trigger_source, "msc600ax", ["/AL", "/Oeg", "/Gs"],
                                      basename="APIONLY", keep=True)
if not trigger_compiled.ok or trigger_compiled.obj is None:
    raise SystemExit(f"MSC compile failed for API-only control:\n{trigger_compiled.log}")
trigger_obj = reader.read(trigger_compiled.obj, "APIONLY")
trigger_refs = sorted({fix["target"] for fix in trigger_obj.linker_fixups
                       if fix["target_kind"] == "external"})
if "__fheap" in trigger_refs:
    raise SystemExit("API-only control unexpectedly has a direct __fheap field reference")
trigger_object_path = OUT / "APIONLY.OBJ"
trigger_object_path.write_bytes(trigger_compiled.obj)
trigger_results = []
for linker in ("rtlink400", "rtlink610"):
    case = OUT / "api-only" / linker
    case.mkdir(parents=True, exist_ok=True)
    (case / "APIONLY.OBJ").write_bytes(trigger_compiled.obj)
    (case / "T.LNK").write_text(
        "OUTPUT APIONLY\nMAP = APIONLY S,N,A,L,V,X\nNODEFLIB\n"
        "FILE APIONLY\nLIBRARY LLIBCR, LIBH\nVERBOSE\n",
        encoding="ascii", newline="\r\n")
    rc = rtlink.run_link(case, profile=linker, timeout=240)
    log_path = case / "LINK.LOG"
    map_path = case / "APIONLY.MAP"
    log = log_path.read_text(encoding="latin1", errors="replace") if log_path.exists() else ""
    map_text = map_path.read_text(encoding="latin1", errors="replace") if map_path.exists() else ""
    if rc != 0 or not map_text or "OUTPUT APIONLY" not in log.upper():
        raise SystemExit(f"RTLink {linker} API-only control failed rc={rc}: {log[-1200:]}")
    members = re.findall(r"LLIBCR\.LIB\(([^)]+)\)", log, re.IGNORECASE)
    if not any(x.lower() == "fmalloc.asm" for x in members):
        raise SystemExit(f"RTLink {linker} API-only control did not select fmalloc.asm")
    if not any(x.lower() == "fdata.asm" for x in members):
        raise SystemExit(f"RTLink {linker} API-only control did not select fdata.asm")
    if not re.search(r"^\s*[0-9A-Fa-f]+:[0-9A-Fa-f]+\s+__fheap(?:\s|$)",
                     map_text, re.MULTILINE):
        raise SystemExit(f"RTLink {linker} API-only map has no __fheap public")
    trigger_results.append({"linker": linker, "return_code": rc,
                            "selected_members": members,
                            "object_external_fixups": trigger_refs,
                            "direct_app___fheap_fixup": False,
                            "selected_fmalloc": True, "selected_fdata": True,
                            "linked_exe_executed": False})

report = {"status": "LINKED_NOT_EXECUTED", "source": SOURCE.relative_to(ROOT).as_posix(),
          "object": object_path.relative_to(ROOT).as_posix(),
          "object_external_fixups": references,
          "typed_heap_source_shape": [
              "startseg: far pointer at +0", "roverseg: far pointer at +4",
              "lastseg: far pointer at +8", "segflags: unsigned word at +12"],
          "link_runs": results,
          "api_only_extraction_control": {
              "source": trigger_source_path.relative_to(ROOT).as_posix(),
              "object": trigger_object_path.relative_to(ROOT).as_posix(),
              "link_runs": trigger_results,
              "trigger_chain": [
                  "API-only main has direct OMF fixups to _malloc, _free, __fmalloc and __ffree; no direct __fheap fixup",
                  "pinned LLIBCR malloc.asm imports __fmalloc, selecting fmalloc.asm",
                  "pinned LLIBCR fmalloc.asm imports __fheap, selecting fdata.asm",
                  "pinned LLIBCR fdata.asm defines __fheap at _DATA+0 with 14 initialized bytes"]}}
(OUT / "fheap-runtime-probe-v36.json").write_text(json.dumps(report, indent=2) + "\n",
                                                     encoding="utf-8")
print(json.dumps(report, indent=2))
