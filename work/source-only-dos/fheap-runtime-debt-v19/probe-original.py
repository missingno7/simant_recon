#!/usr/bin/env python3
"""Bounded __fheap selection probe; does not read the original executable."""
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
API = {"__fheap", "__fmalloc", "__ffree", "__frealloc", "__fexpand",
       "__fheapchk", "__fheapset", "__fheapwalk", "__fheapmin"}


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
            "fixture_role": ("synthetic symbol-provider control; bodies are link stubs, not the accepted allocator implementation"
                             if name == "source_owned_malloc_free" else
                             "synthetic no-heap or positive far-heap library-selection control"),
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
        "OUTPUT PROBE\nMAP = PROBE S,N,A,L\nNODEFLIB\n"
        "FILE MAIN\nLIBRARY LLIBCR, LIBH\n",
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
    expected = name == "positive_far_heap_api"
    if expected and not (contains_fmalloc and contains_fdata):
        raise SystemExit(f"RTLink {linker} positive far-heap control did not pull the provider")
    if not contains_fdata:
        raise SystemExit(f"RTLink {linker} changed the observed no-import fdata selection control")
    if name == "source_owned_malloc_free":
        required = {"_malloc", "_free", "__ffree", "__frealloc"}
        if not required.issubset({p["name"] for p in fixture["interesting_publics"]}):
            raise SystemExit("source-owner contrast does not define the root allocator symbol set")
        if fixture["unresolved_interesting_external_symbols"]:
            raise SystemExit("source-owner contrast imports the MSC far-heap API")
    if name == "plain_main_no_heap_import" and fixture["unresolved_interesting_external_symbols"]:
        raise SystemExit("plain-main negative contrast unexpectedly imports heap APIs")
    return {"linker": linker, "case": name, "return_code": rc,
            "control_role": "positive explicit far-heap API import" if expected else
                            "selection contrast; observed result retained without assumption",
            "map_contains_fmalloc": contains_fmalloc,
            "map_contains_fdata": contains_fdata,
            "map_sha256": pin(map_path)["sha256"],
            "log_sha256": pin(log_path)["sha256"],
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
    for row in build["translation_units"]:
        if not row.get("object") or not str(row.get("status", "")).startswith("COMPILED"):
            continue
        obj = read_object(row["object"], rd)
        built[row["module"]] = (row, obj)
        source_object_pins.append({"module": row["module"], **pin(
            Path(row["object"]["path"]) if Path(row["object"]["path"]).is_absolute()
            else ROOT / row["object"]["path"])})

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

    # Positive and negative no-oracle fixtures test actual library extraction in each RTLink.
    fixtures = {
        "source_owned_malloc_free": (
            "void far *malloc(unsigned n) { static char far block[16]; "
            "return n ? block : block; }\n"
            "void far _ffree(char far *p) { (void)p; }\n"
            "char far * far _frealloc(char far *p, unsigned n) { (void)n; return p; }\n"
            "void far free(void far *p) { _ffree((char far *)p); }\n"
            "void far main(void) { char far *p; p=(char far *)malloc(1); free(p); }\n"),
        "plain_main_no_heap_import": "void far main(void) { }\n",
        "positive_far_heap_api": (
            "extern char far * far _fmalloc(unsigned n);\n"
            "void far main(void) { (void)_fmalloc(1); }\n"),
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
    report = {
        "schema": "simant-dgroup-fheap-runtime-debt-v19",
        "root_reviewed": False,
        "status": "CURRENT_SOURCE_GRAPH_HAS_NO_FHEAP_IMPORT; ORIGINAL_DGROUP_RANGE_UNRESOLVED",
        "scope": "current accepted source-object imports, accepted RTLink runtime membership, and clean MSC/RTLink library-selection controls; no original executable reads",
        "debt": {"id": "dgroup_79f0", "bytes": 14,
                 "classification": "unresolved historical placement/selection; not admitted source owner"},
        "inputs": {"manifest": manifest_pin, "symbols": pin(SYMBOLS),
                   "source_only_build_report": pin(REPORT), "root_allocator_source": pin(SOURCE),
                   "toolchain": pin(TOOLCHAIN), "runtime_libraries": libs,
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
        "accepted_runtime_library_membership": {
            "selected_member_count": len(selected),
            "selected_runtime_members_importing_far_heap_api": runtime_far_heap_refs,
            "selected_runtime_members_importing_malloc_free": runtime_malloc_users,
            "pinned_fdata_provider": provider_rows[0],
            "archive_members_in_allocator_dependency_family": archive_family_members,
            "all_direct___fheap_consumers": fheap_consumers,
            "all_direct_consumers_unselected": all(not x["selected_in_accepted_runtime"]
                                                     for x in fheap_consumers),
        },
        "natural_link_controls": {
            "runs": controls,
            "interpretation": "All three clean controls map __fheap under RTLink 4.00 and 6.10. The source-owned contrast exports _malloc/_free/__ffree/__frealloc and has no unresolved MSC far-heap import; the plain-main contrast imports none. The positive direct-__fmalloc control maps both __fmalloc and __fheap. In the other controls __fmalloc presence varies (the 6.10 source-owned case omits it while still mapping __fheap), so a simple direct fmalloc chain does not explain all extraction. These clean runs show a CRT/archive trigger in the minimal link and do not prove full-application member selection or DGROUP placement.",
        },
        "conclusion": {
            "current_source_objects_do_not_request_msc_far_heap": True,
            "accepted_selected_runtime_members_do_not_request_msc_far_heap_api": True,
            "clean_rtlink_controls_select_fdata_for_explicit_far_heap_api_import": True,
            "clean_rtlink_controls_also_select_fdata_without_direct_application_heap_import": True,
            "clean_control_effect_of_source_owned_malloc_free": {
                linker: {y["case"]: {"fmalloc_public": y["map_contains_fmalloc"],
                                     "fdata_public": y["map_contains_fdata"]}
                         for y in controls if y["linker"] == linker}
                for linker in sorted({y["linker"] for y in controls})
            },
            "whole_application_independent_link_completed": False,
            "dgroup_79f0_bytes_closed": 0,
            "reason": "Current compiled game objects import no MSC far-heap API, and accepted runtime code/data rows import none; root:171C provides the application's _malloc/_free/__ffree/__frealloc path. Both RTLinks nevertheless extract the __fheap provider in the plain-main and source-owned allocator control, exposing an automatic CRT/archive dependency not visible from direct application imports. The guarded whole-source preflight is incomplete, so the production selected-member chain and the _DATA placement/file-boundary proof at DGROUP:79F0 remain unavailable. Keep all 14 bytes as unresolved historical debt; do not claim harmless padding or an owner.",
        },
    }
    out_path = OUT / "fheap-runtime-debt-v19.json"
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
