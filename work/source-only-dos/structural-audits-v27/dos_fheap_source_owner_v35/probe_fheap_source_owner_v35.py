#!/usr/bin/env python3
"""Bounded MSC 6.00 source-owner investigation for __fheap; no original EXE reads."""
from __future__ import annotations

import hashlib
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


REPORT = ROOT / "build/source-only-dos/build-report.json"
MANIFEST = ROOT / "layout/manifest.json"
SYMBOLS = ROOT / "layout/symbols.json"
TOOLCHAIN = ROOT / "layout/toolchain.json"
SOURCE = ROOT / "src/root/m171C.c"
RUNTIME_DIR = Path("C:/tools/msc-6.00/LIB")
STARTUP_DIR = Path("C:/tools/msc-6.00/STARTUP")
MALLOC_H = Path("C:/tools/msc-6.00/INCLUDE/malloc.h")
STDLIB_H = Path("C:/tools/msc-6.00/INCLUDE/stdlib.h")
HEAP_INC = STARTUP_DIR / "heap.inc"
CRT0_ASM = STARTUP_DIR / "dos/crt0.asm"
CRT0DAT_ASM = STARTUP_DIR / "dos/crt0dat.asm"
STDALLOC_ASM = STARTUP_DIR / "dos/stdalloc.asm"
API = {"__fheap", "__fmalloc", "__ffree", "__frealloc", "__fexpand",
       "__fheapchk", "__fheapset", "__fheapwalk", "__fheapmin"}
ALLOCATOR_API = API | {"_malloc", "_free"}
ADDR79F0_RE = re.compile(r"(?i)(?<![a-z0-9_])(?:0x0*79f0|79f0h|31216)(?![a-z0-9_])")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin(path: Path) -> dict:
    raw = path.read_bytes()
    try:
        rel = path.relative_to(ROOT).as_posix()
    except ValueError:
        rel = path.as_posix()
    return {"path": rel, "size": len(raw), "sha256": sha(raw)}


def read_object(row: dict, reader: OmfReader):
    path = Path(row["path"])
    if not path.is_absolute():
        path = ROOT / path
    raw = path.read_bytes()
    if len(raw) != row["size"] or sha(raw) != row["sha256"]:
        raise SystemExit(f"build-report object pin mismatch: {path}")
    return reader.read(raw, path.stem)


def module_class_map(obj) -> dict[str, str]:
    return {str(row["name"]): str(row.get("class", ""))
            for row in obj.segment_defs}


def tool_profile_pins(tc: dict) -> dict:
    compiler_profile = tc["profiles"]["msc600ax"]
    runner_key = compiler_profile.get("runner")
    compiler_runner = tc["runners"][runner_key] if runner_key else tc["runner"]
    linker_profiles = {name: tc["linkers"][name] for name in ("rtlink400", "rtlink610")}
    return {
        "compiler_profile": {
            "name": "msc600ax",
            "files": {rel: pin(Path(compiler_profile["directory"]) / rel)
                      for rel in compiler_profile["files"]},
            "runner": pin(Path(compiler_runner["path"])),
        },
        "dosbox_runner": pin(Path(tc["runners"]["dosbox-x"]["path"])),
        "linkers": {
            name: {"executable": pin(Path(profile["directory"]) / profile["executable"]),
                   "files": {rel: pin(Path(profile["directory"]) / rel)
                             for rel in profile["files"]}}
            for name, profile in linker_profiles.items()
        },
    }


def compile_fixture(out: Path, name: str, source: str) -> dict:
    src = out / f"{name}.c"
    src.write_text(source, encoding="ascii", newline="\r\n")
    result = compiler.compile_c(source, "msc600ax", ["/AL", "/Oeg", "/Gs"],
                                basename="MAIN", keep=True)
    if not result.ok or result.obj is None:
        raise SystemExit(f"MSC 6.00AX fixture failed ({name}):\n{result.log}")
    obj_path = out / "MAIN.OBJ"
    obj_path.write_bytes(result.obj)
    obj = OmfReader(communals=True).read(result.obj, "MAIN")
    return {"source": pin(src), "object": pin(obj_path),
            "fixture_role": ("minimal source-owned _malloc symbol-provider contrast; it is a link-control stub, not a recovered allocator"
                             if name == "source_owned_malloc_no_far_heap" else
                             "minimal source-built MSC large-model main; no allocator API use"),
            "interesting_publics": [p for p in obj.publics
                                    if p["name"] in {"_malloc", "_free", "__fmalloc", "__ffree", "__frealloc"}],
            "interesting_external_symbols": sorted(x for x in obj.externals
                                                     if x in API or x in {"_malloc", "_free"}),
            "unresolved_interesting_external_symbols": sorted(
                x for x in obj.externals
                if (x in API or x in {"_malloc", "_free"})
                and x not in {p["name"] for p in obj.publics})}


def run_fixture(out: Path, name: str, source: str, linker: str) -> dict:
    case = out / "natural-controls" / linker / name
    case.mkdir(parents=True, exist_ok=True)
    fixture = compile_fixture(case, name, source)
    (case / "T.LNK").write_text(
        "OUTPUT PROBE\nMAP = PROBE S,N,A,L,V,X\nNODEFLIB\n"
        "FILE MAIN\nLIBRARY LLIBCR, LIBH\nVERBOSE\n",
        encoding="ascii", newline="\r\n")
    rc = rtlink.run_link(case, profile=linker, timeout=240)
    log_path = case / "LINK.LOG"
    map_path = case / "PROBE.MAP"
    log = log_path.read_text(encoding="latin1", errors="replace") if log_path.exists() else ""
    map_text = map_path.read_text(encoding="latin1", errors="replace") if map_path.exists() else ""
    if rc != 0 or not map_text or "OUTPUT PROBE" not in log.upper():
        raise SystemExit(f"RTLink {linker} fixture {name} failed rc={rc}; log={log[-1600:]}")
    def mapped_address(symbol: str) -> str | None:
        match = re.search(rf"^\s*([0-9A-Fa-f]+:[0-9A-Fa-f]+)\s+{re.escape(symbol)}(?:\s|$)",
                          map_text, re.MULTILINE)
        return match.group(1) if match else None

    map_public_addresses = {name: mapped_address(name)
                            for name in ("_malloc", "_free", "__ffree", "__frealloc",
                                         "__fmalloc", "__fheap")}
    contains_fmalloc = map_public_addresses["__fmalloc"] is not None
    contains_fdata = map_public_addresses["__fheap"] is not None
    fheap_map_rows = [line.strip() for line in map_text.splitlines()
                      if "__fheap" in line.lower() or "m=fdata.asm" in line.lower()]
    if not contains_fdata or not any("__fheap" in line.lower() and "fdata.asm" in line.lower()
                                    for line in fheap_map_rows):
        raise SystemExit(f"RTLink {linker} map does not bind __fheap to fdata.asm")
    selected_member_names = re.findall(r"LLIBCR\.LIB\(([^)]+)\)", log, re.IGNORECASE)
    archive_rows = OmfReader(communals=True).split_library(
        (RUNTIME_DIR / "llibcr.lib").read_bytes())
    selected_by_name = {n.lower(): (n, blob) for n, blob in archive_rows}
    selected_heap_importers = []
    selected_allocator_chain = []
    archive_indices = {n.lower(): i for i, (n, _) in enumerate(archive_rows)}
    for member_name in selected_member_names:
        row = selected_by_name.get(member_name.lower())
        if row is None:
            raise SystemExit(f"selected LLIBCR member absent from pinned archive: {member_name}")
        real_name, blob = row
        obj = OmfReader(communals=True).read(blob, real_name)
        imports = sorted({fix["target"] for fix in obj.linker_fixups
                          if fix["target_kind"] == "external"})
        publics = sorted({p["name"] for p in obj.publics})
        external_declarations = sorted(set(obj.externals) & ALLOCATOR_API)
        if (set(imports) | set(external_declarations) | set(publics)) & ALLOCATOR_API:
            selected_allocator_chain.append({
                "member": real_name,
                "module_index": archive_indices[real_name.lower()],
                "allocator_publics": sorted(set(publics) & ALLOCATOR_API),
                "allocator_imports": sorted(set(imports) & ALLOCATOR_API),
                "allocator_external_declarations": external_declarations})
        if "__fheap" in imports:
            selected_heap_importers.append({"member": real_name,
                                            "module_index": archive_indices[real_name.lower()],
                                            "imports___fheap": True})
    if name == "natural_main_no_heap_import" and not contains_fdata:
        raise SystemExit(f"RTLink {linker} natural CRT fixture did not pull the __fheap provider")
    if fixture["unresolved_interesting_external_symbols"]:
        raise SystemExit("minimal natural-main fixture unexpectedly imports heap APIs")
    if (name == "source_owned_malloc_no_far_heap"
            and "_malloc" not in {p["name"] for p in fixture["interesting_publics"]}):
        raise SystemExit("source-owned malloc contrast does not define _malloc")
    if any(re.search(r"\bwarning\b|\berror\b", line, re.IGNORECASE)
           for line in log.splitlines()):
        raise SystemExit(f"RTLink {linker} natural CRT fixture is not clean; see {log_path}")
    return {"linker": linker, "case": name, "return_code": rc,
            "control_role": "minimal natural MSC CRT startup; fixture imports no heap API",
            "map_contains_fmalloc": contains_fmalloc,
            "map_contains_fdata": contains_fdata,
            "map_sha256": pin(map_path)["sha256"],
            "map_owner_rows": fheap_map_rows,
            "log_sha256": pin(log_path)["sha256"],
            "linked_output_exe": pin(case / "PROBE.EXE") if (case / "PROBE.EXE").exists() else None,
            "linked_output_exe_executed": False,
            "selected_llibcr_member_names": selected_member_names,
            "selected_allocator_chain": selected_allocator_chain,
            "selected_members_directly_importing___fheap": selected_heap_importers,
            "diagnostic_warnings": [line.strip() for line in log.splitlines()
                                    if re.search(r"\bwarning\b|\berror\b", line, re.IGNORECASE)],
            "link_script": pin(case / "T.LNK"),
            "rtlink_config": pin(case / "RTLINK.CFG"),
            "dosbox_config": pin(case / "dosbox.conf"),
            "runner_batch": pin(case / "RUN.BAT"),
            "runtime_library_copies": {
                name: pin(case / name.upper()) for name in ("llibcr.lib", "libh.lib")},
            "fixture": fixture,
            "map_public_addresses": map_public_addresses}


def main() -> None:
    # Keep compiler/linker helper scratch in this bounded worker directory.
    compiler.WORK = OUT / "tool-scratch"

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    symbols = json.loads(SYMBOLS.read_text(encoding="utf-8"))
    build = json.loads(REPORT.read_text(encoding="utf-8"))
    runtime = manifest["runtime"]
    libs = {}
    for name, expected in runtime["libraries"].items():
        actual = pin(RUNTIME_DIR / name)
        if actual["sha256"] != expected["sha256"]:
            raise SystemExit(f"{name} differs from layout/manifest.json runtime pin")
        libs[name] = actual

    if build.get("target") != "SOURCE_ONLY_DOS" or build.get("status") != "INCOMPLETE":
        raise SystemExit("expected current incomplete guarded SOURCE_ONLY_DOS build")
    if any(build.get("original_exe_bytes_used", {}).values()):
        raise SystemExit("current source-only build claims an original executable read")
    if build.get("denied_oracle_reads") not in (None, []):
        raise SystemExit("source-only report records denied oracle reads")

    rd = OmfReader(communals=True)
    built = {}
    source_object_pins = []
    address79f0_source_hits = []
    address79f0_object_word_hits = []
    address79f0_symbol_hits = []
    for row in build["translation_units"]:
        if not row.get("object") or not str(row.get("status", "")).startswith("COMPILED"):
            continue
        obj = read_object(row["object"], rd)
        built[row["module"]] = (row, obj)
        source_object_pins.append({"module": row["module"], **pin(
            Path(row["object"]["path"]) if Path(row["object"]["path"]).is_absolute()
            else ROOT / row["object"]["path"])})
        source_info = row.get("source", {})
        source_path = Path(source_info["path"]) if Path(source_info.get("path", "")).is_absolute() \
            else ROOT / source_info.get("path", "")
        if source_path.is_file():
            for line_no, line in enumerate(source_path.read_text(encoding="latin1").splitlines(), 1):
                if ADDR79F0_RE.search(line):
                    address79f0_source_hits.append({"module": row["module"],
                                                    "source": source_path.relative_to(ROOT).as_posix(),
                                                    "line": line_no, "text": line.strip()})
        for seg_name, seg_bytes in obj.segments.items():
            for marker_name, marker in (("little_endian_0x79f0", b"\xF0\x79"),
                                        ("big_endian_0x79f0", b"\x79\xF0")):
                start = 0
                while True:
                    at = seg_bytes.find(marker, start)
                    if at < 0:
                        break
                    if len(address79f0_object_word_hits) < 64:
                        address79f0_object_word_hits.append({"module": row["module"],
                                                             "segment": seg_name,
                                                             "segment_offset": at,
                                                             "byte_order_pattern": marker_name})
                    start = at + 1
        for symbol in sorted(set(obj.externals) | {p["name"] for p in obj.publics}):
            if "79f0" in symbol.lower():
                address79f0_symbol_hits.append({"module": row["module"], "symbol": symbol})

    # This report is tied to the current accepted root module source/hash.
    root_row = build_row = built.get("root:171C")
    if not root_row:
        raise SystemExit("current source-only build has no root:171C object")
    root_obj = root_row[1]
    manifest_root = manifest["modules"].get("root:171C")
    if (manifest_root is None or manifest_root.get("source") != "src/root/m171C.c"
            or manifest_root.get("source_sha256") != pin(SOURCE)["sha256"]
            or root_row[0].get("source", {}).get("sha256") != manifest_root["source_sha256"]):
        raise SystemExit("root:171C source object is not tied to the accepted source identity")

    app_refs = []
    app_defs = []
    for module, (row, obj) in built.items():
        code_names = {seg for seg, cls in module_class_map(obj).items()
                      if cls.upper().endswith("CODE")}
        for fix in obj.linker_fixups:
            if (fix["segment"] in code_names and fix["target_kind"] == "external"
                    and fix["target"] in API):
                app_refs.append({"module": module, "target": fix["target"],
                                 "offset": fix["offset"], "segment": fix["segment"]})
        for public in obj.publics:
            if public["name"] in {"_malloc", "_free", "__ffree", "__frealloc", "__fmalloc"}:
                app_defs.append({"module": module, "name": public["name"],
                                 "segment": public["segment"], "offset": public["offset"]})

    root_api_defs = [x for x in app_defs if x["module"] == "root:171C"]
    if not {"_malloc", "_free", "__ffree", "__frealloc"}.issubset(
            {x["name"] for x in root_api_defs}):
        raise SystemExit("source-built root allocator API publics differ from expected")
    game_far_heap_refs = [x for x in app_refs if x["target"] in API - {"__ffree", "__frealloc"}]
    if game_far_heap_refs:
        raise SystemExit("source-built application imports a CRT far-heap symbol")
    source_anchors = []
    for line_no, line in enumerate(SOURCE.read_text(encoding="latin1").splitlines(), 1):
        if any(term in line for term in ("malloc(unsigned size)",
                                         "return f_171C_21CC(size);",
                                         "_ffree(char far *p)", "_ffree(p);",
                                         "_frealloc(char far *p, unsigned size)")):
            source_anchors.append({"line": line_no, "text": line.strip()})

    selected = {(x["library"].lower(), x["module_index"]): x
                for x in runtime["members"]}
    selected.update({(x["library"].lower(), x["module_index"]): x
                     for x in runtime.get("data_members", [])})
    runtime_modules = {lib: rd.split_library((RUNTIME_DIR / lib).read_bytes())
                       for lib in runtime["libraries"]}
    runtime_far_heap_refs = []
    runtime_malloc_users = []
    for (lib, index), row in selected.items():
        if lib not in runtime_modules or index >= len(runtime_modules[lib]):
            raise SystemExit(f"accepted runtime selection outside pinned archive: {lib}#{index}")
        name, blob = runtime_modules[lib][index]
        obj = rd.read(blob, name)
        refs = {fix["target"] for fix in obj.linker_fixups
                if fix["target_kind"] == "external"}
        family_refs = sorted(refs & API)
        if family_refs:
            runtime_far_heap_refs.append({"library": lib, "module_index": index,
                                          "member": name, "references": family_refs})
        if refs & {"_malloc", "_free"}:
            runtime_malloc_users.append({"library": lib, "module_index": index,
                                         "member": name,
                                         "references": sorted(refs & {"_malloc", "_free"})})
    if runtime_far_heap_refs:
        raise SystemExit("accepted runtime code/data members directly import the MSC far-heap API")

    lib_blobs = runtime_modules["llibcr.lib"]
    provider_rows = []
    fheap_consumers = []
    archive_family_members = []
    for index, (name, blob) in enumerate(lib_blobs):
        obj = rd.read(blob, name)
        refs = sorted({fix["target"] for fix in obj.linker_fixups
                       if fix["target_kind"] == "external"})
        family_publics = sorted({p["name"] for p in obj.publics if p["name"] in API})
        if (set(refs) & API) or family_publics or (set(refs) & {"_malloc", "_free"}):
            archive_family_members.append({
                "module_index": index, "member": name,
                "references": sorted(set(refs) & (API | {"_malloc", "_free"})),
                "publics": family_publics,
                "selected_in_accepted_runtime": ("llibcr.lib", index) in selected,
            })
        if any(p["name"] == "__fheap" for p in obj.publics):
            provider_rows.append({"module_index": index, "member": name,
                                  "member_sha256": sha(blob),
                                  "data_segments": {n: len(b) for n, b in obj.segments.items()},
                                  "data_segment_defs": [seg for seg in obj.segment_defs
                                                        if seg["name"] in obj.segments],
                                  "publics": [p for p in obj.publics if p["name"] == "__fheap"],
                                  "selected_in_accepted_runtime":
                                      ("llibcr.lib", index) in selected})
        if any(f["target_kind"] == "external" and f["target"] == "__fheap"
               for f in obj.linker_fixups):
            fheap_consumers.append({"module_index": index, "member": name,
                                    "selected_in_accepted_runtime":
                                        ("llibcr.lib", index) in selected})
    if len(provider_rows) != 1 or provider_rows[0]["member"].lower() != "fdata.asm":
        raise SystemExit("pinned LLIBCR __fheap provider changed")
    if not fheap_consumers or any(x["selected_in_accepted_runtime"] for x in fheap_consumers):
        raise SystemExit("pinned LLIBCR __fheap consumers changed/selected")

    fdata_member = next((rd.read(blob, name) for name, blob in lib_blobs
                         if name.lower() == "fdata.asm"), None)
    if fdata_member is None or "_DATA" not in fdata_member.segments:
        raise SystemExit("pinned fdata.asm object/segment missing")
    fdata_bytes = fdata_member.segments["_DATA"]
    if len(fdata_bytes) != 14:
        raise SystemExit("pinned fdata.asm _DATA length changed")

    # Read the installed MSC source text, not a reconstructed layout guess.  The
    # record below states the literal MASM declaration shape and offsets.
    heap_inc_text = HEAP_INC.read_text(encoding="latin1")
    crt0_text = CRT0_ASM.read_text(encoding="latin1")
    malloc_h_text = MALLOC_H.read_text(encoding="latin1")
    stdlib_h_text = STDLIB_H.read_text(encoding="latin1")
    list_markers = [
        "_heap_list_desc struc", "startseg\tdd\t0", "roverseg\tdd\t0",
        "lastseg \tdd\t0", "segflags\tdw\t0", "_heap_list_desc ends",
        "_HEAP_MODIFY\tequ\t01h", "_HEAP_FREE\tequ\t02h",
    ]
    if not all(marker in heap_inc_text for marker in list_markers):
        raise SystemExit("installed MSC heap.inc no longer contains expected list descriptor/flag declarations")
    heap_api_lines = {str(i): line.strip() for i, line in enumerate(malloc_h_text.splitlines(), 1)
                      if re.search(r"\b(_fmalloc|_ffree|_frealloc|_fheapchk|_fheapset|_fheapwalk|_fheapmin)\b", line)}
    if "__fheap" in malloc_h_text.lower() or "__fheap" in stdlib_h_text.lower():
        raise SystemExit("public headers now declare internal __fheap; revisit source-owner conclusion")
    startup_lines = {str(i): line.strip() for i, line in enumerate(crt0_text.splitlines(), 1)
                     if any(term in line.lower() for term in
                            ("__qczrinit", "initializer prior", "far heap allocations", "_nheap_desc", "_heap_seg_desc"))}

    # Minimal, natural CRT startup controls: ordinary main has no allocator API
    # import; a second link supplies only _malloc to isolate the stdalloc chain
    # without creating the RTLink 4.00 duplicate-__ffree case.
    fixtures = {
        "natural_main_no_heap_import": "int main(void) { return 0; }\n",
        "source_owned_malloc_no_far_heap": (
            "void far *malloc(unsigned n) { static char far block[16]; "
            "(void)n; return block; }\n"
            "int main(void) { return malloc(1) == 0; }\n"),
    }
    controls = []
    for linker in ("rtlink400", "rtlink610"):
        for name, source in fixtures.items():
            controls.append(run_fixture(OUT, name, source, linker))

    manifest_pin = pin(MANIFEST)
    toolchain = json.loads(TOOLCHAIN.read_text(encoding="utf-8"))
    source_object_set = sorted(source_object_pins, key=lambda row: row["module"])
    source_object_set_sha = sha(json.dumps(source_object_set, sort_keys=True,
                                           separators=(",", ":")).encode("utf-8"))
    prior_v28_receipt = ROOT / "build/workers/dos_fheap_production_plan_v28/diagnostic-receipt-v28.json"
    prior_v28_link = ROOT / "build/workers/dos_fheap_production_plan_v28/run-v5/baseline/rtlink610"
    prior_v28_partial = {
        "receipt": pin(prior_v28_receipt),
        "link_log": pin(prior_v28_link / "LINK.LOG"),
        "map": pin(prior_v28_link / "SOURCE.MAP"),
        "link_script": pin(prior_v28_link / "T.LNK"),
        "reported_object_count": 178,
        "reported_selected_fdata": True,
        "reported_selected_members_importing___fheap": [],
        "exe_executed": False,
        "qualification": "Preserved expected-failure v28 partial-link snapshot. It predates this v35 build-report/source-object set (178 vs 182 TUs); it is cross-evidence, not a fresh v35 run or historical address proof.",
    }
    report = {
        "schema": "simant-dgroup-fheap-source-owner-v35",
        "root_reviewed": False,
        "admitted": False,
        "status": "KNOWN_PINNED_RUNTIME_DATA_OWNER; HISTORICAL_DGROUP_79F0_RANGE_OPEN",
        "scope": "current accepted source-object imports, pinned LLIBCR provider/consumers, installed MSC 6.00 CRT source/header semantics, and natural RTLink controls; no original executable reads",
        "image_executed": False,
        "debt": {"id": "dgroup_79f0", "bytes": 14,
                 "functional_owner_disposition": "accounted as pinned third-party runtime data member llibcr.lib(fdata.asm), the sole __fheap provider",
                 "historical_disposition": "open: original DGROUP:79F0 placement, neighbor/order, and original byte identity are not proved by this source-only owner investigation"},
        "inputs": {"manifest": manifest_pin, "symbols": pin(SYMBOLS),
                   "source_only_build_report": pin(REPORT), "root_allocator_source": pin(SOURCE),
                   "toolchain": pin(TOOLCHAIN), "runtime_libraries": libs,
                   "prior_quarantined_production_partial_link": prior_v28_partial,
                   "msc_source_and_headers": {str(path): pin(path) for path in
                                               (HEAP_INC, CRT0_ASM, CRT0DAT_ASM, STDALLOC_ASM,
                                                MALLOC_H, STDLIB_H)},
                   "source_object_set": {"count": len(source_object_set),
                                         "sha256": source_object_set_sha,
                                         "root_allocator_object": root_row[0]["object"]},
                   "omf_reader": pin(ROOT / "tools/omf.py"),
                   "runtime_gate": pin(ROOT / "tools/runtime.py"),
                   "link_runner": pin(ROOT / "tools/rtlink.py"),
                   "compiler_runner": pin(ROOT / "tools/compiler.py"),
                   "probe_script": pin(Path(__file__))},
        "tool_inputs": tool_profile_pins(toolchain),
        "current_guarded_build": {
            "target": build["target"], "status": build["status"],
            "translation_unit_count": len(build["translation_units"]),
            "compiled_source_object_count": len(source_object_pins),
            "original_exe_bytes_used": build.get("original_exe_bytes_used"),
            "denied_oracle_reads": build.get("denied_oracle_reads", []),
            "linker_components": build.get("linker_components"),
            "link_unavailable_reason": build.get("errors", [])},
        "accepted_source_allocator_path": {
            "root_module": "root:171C", "source": pin(SOURCE),
            "manifest_module_sha256": manifest_root["source_sha256"],
            "source_anchors": source_anchors,
            "root_allocator_publics": root_api_defs,
            "source_object_imports_of_crt_far_heap_api": game_far_heap_refs,
            "current_import_scan_complete_for_compiled_tus": True,
            "interpretation": "Compiled accepted game objects define _malloc/_free and __ffree/__frealloc in root:171C; no compiled game code imports the MSC far-heap API. This static link graph is not a completed whole-program link.",
        },
        "original_79f0_reliance_census": {
            "scope": "all 182 currently compiled accepted source TUs and parsed OMF segment payloads; does not inspect original executable bytes",
            "source_numeric_address_literals": address79f0_source_hits,
            "object_symbol_names_containing_79f0": address79f0_symbol_hits,
            "object_segments_containing_79f0_word_patterns": address79f0_object_word_hits,
            "source_literal_hit_count": len(address79f0_source_hits),
            "object_symbol_hit_count": len(address79f0_symbol_hits),
            "object_word_pattern_hit_count_reported": len(address79f0_object_word_hits),
            "compiled_game_external_fixups_to___fheap": game_far_heap_refs,
            "interpretation": "The accepted source/object graph has no numeric source reference or symbol name for the historical 79F0 anchor and no symbolic __fheap import. Raw 16-bit object-word patterns, if any, are recorded as byte coincidences only and are not treated as address references without a relocation/symbol anchor.",
        },
        "accepted_runtime_library_membership": {
            "selected_member_count": len(selected),
            "selected_runtime_members_importing_far_heap_api": runtime_far_heap_refs,
            "selected_runtime_members_importing_malloc_free": runtime_malloc_users,
            "pinned_fdata_provider": provider_rows[0],
            "archive_members_in_allocator_dependency_family": archive_family_members,
            "all_direct___fheap_consumers": fheap_consumers,
            "all_direct_consumers_unselected": all(not x["selected_in_accepted_runtime"]
                                                     for x in fheap_consumers),
            "fdata_selected_in_current_runtime_manifest": provider_rows[0]["selected_in_accepted_runtime"],
            "functional_owner_accounting": "Known pinned third-party component: llibcr.lib(fdata.asm) is the sole __fheap DATA owner. The current selected-runtime manifest does not include it or a direct consumer; the preserved v28 RTLink 6.10 partial map separately selected fdata with no direct __fheap-importing member.",
        },
        "installed_msc_source_semantics": {
            "heap_list_descriptor": {
                "source": pin(HEAP_INC),
                "fields": [
                    {"name": "startseg", "width_bytes": 4, "offset": 0,
                     "comment": "pointer to first heap descriptor"},
                    {"name": "roverseg", "width_bytes": 4, "offset": 4,
                     "comment": "rover pointer"},
                    {"name": "lastseg", "width_bytes": 4, "offset": 8,
                     "comment": "pointer to last heap descriptor"},
                    {"name": "segflags", "width_bytes": 2, "offset": 12,
                     "comment": "flags word for init'ing new segs"}],
                "declared_total_bytes": 14,
                "flag_constants": {"_HEAP_MODIFY": 1, "_HEAP_FREE": 2,
                                    "combined_word": 3},
                "source_text_markers": list_markers,
            },
            "fdata_object": {
                "archive_member": "llibcr.lib(fdata.asm)",
                "segment": "_DATA", "byte_count": len(fdata_bytes),
                "initialized_bytes_hex": fdata_bytes.hex(),
                "publics": [p for p in fdata_member.publics if p["name"] == "__fheap"],
                "interpretation": "The archive object is 14 bytes and is structurally compatible with the installed heap-list descriptor: three null far pointers followed by segflags=3 (_HEAP_MODIFY|_HEAP_FREE). The shipped source does not name __fheap in heap.inc or the public headers, so this is a strong layout/value compatibility observation, not a direct source declaration binding.",
            },
            "public_headers": {
                "malloc_h": pin(MALLOC_H), "stdlib_h": pin(STDLIB_H),
                "far_heap_prototypes": heap_api_lines,
                "declare_internal___fheap": False,
            },
            "crt_startup_source": {
                "crt0_asm": pin(CRT0_ASM), "crt0dat_asm": pin(CRT0DAT_ASM),
                "stdalloc_asm": pin(STDALLOC_ASM),
                "relevant_crt0_lines": startup_lines,
                "interpretation": "CRT startup zeroes BSS and invokes __qczrinit before argv/environment allocation, with a comment requiring that initializer before far-heap allocations. The available source does not tie that initializer or a startup writer to __fheap; crt0's explicit _heap_seg_desc is the distinct near-heap descriptor.",
            },
        },
        "natural_link_controls": {
            "runs": controls,
            "interpretation": "The ordinary no-heap main fixture links cleanly under both RTLink versions, has no direct far-heap import, and maps __fheap to fdata.asm. Its verbose archive log exposes the natural CRT chain dos\\stdalloc.asm -> malloc.asm -> fmalloc.asm -> fdata.asm. In the source-owned-_malloc contrast, malloc.asm drops out but fmalloc.asm and fdata.asm remain selected; the selected fmalloc member itself imports __fheap, yet no other selected member in that contrast is a direct __fheap importer, so that contrast does not identify the extraction trigger. The fixture is a link-control stub, not an accepted allocator. Neither control establishes that the source-only application selected the same chain or proves DGROUP placement.",
        },
        "conclusion": {
            "current_source_objects_do_not_request_msc_far_heap": True,
            "accepted_selected_runtime_members_do_not_request_msc_far_heap_api": True,
            "logical_stock_runtime_owner_accounted": True,
            "current_game_graph_has_no_direct_fheap_use": True,
            "current_game_reliance_on_original_79f0_bytes_or_order": False,
            "clean_minimal_natural_crt_controls_select_fdata_without_direct_application_heap_import": True,
            "clean_control_allocator_publics": {
                linker: {y["case"]: {"fmalloc_public": y["map_contains_fmalloc"],
                                     "fdata_public": y["map_contains_fdata"]}
                         for y in controls if y["linker"] == linker}
                for linker in sorted({y["linker"] for y in controls})
            },
            "whole_application_independent_link_completed": False,
            "stock_crt_14_byte_layout_candidate_supported": True,
            "fdata_public_identified_by_pinned_runtime_and_selected_symbol_as___fheap": True,
            "startup_initialization_of___fheap_proven_by_installed_source": False,
            "dgroup_79f0_bytes_closed": 0,
            "reason": "The owner is accounted as a known pinned runtime component rather than a guessed C declaration: fdata.asm is the sole LLIBCR member defining the symbolic public __fheap, current linker evidence maps that public back to this member, and a clean natural CRT link in both RTLink versions demonstrates the stock malloc.asm -> fmalloc.asm -> __fheap -> fdata.asm dependency. The heap.inc match is corroborative only. The current game source and accepted runtime graph have no direct __fheap use, and the accepted-TU source/OMF census finds no numeric 79F0 anchor dependency; the preserved production partial map selected fdata without selected consumers. The source-owned-_malloc control also selects fmalloc/fdata but leaves the extraction trigger unexplained. This supports accounting the pinned runtime component independently while leaving historical DGROUP:79F0 bytes, order, and original identity open. The partial application link is still incomplete; no runnable whole-source build is claimed.",
        },
    }
    out_path = OUT / "fheap-source-owner-v35.json"
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": out_path.relative_to(ROOT).as_posix(),
                      "source_objects": len(source_object_pins),
                      "game_far_heap_imports": len(game_far_heap_refs),
                      "accepted_runtime_far_heap_importers": len(runtime_far_heap_refs),
                      "archive_consumers": len(fheap_consumers),
                      "controls": [{"linker": x["linker"], "case": x["case"],
                                    "fdata": x["map_contains_fdata"]} for x in controls],
                      "status": report["status"]}, indent=2))


if __name__ == "__main__":
    main()
