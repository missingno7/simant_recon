#!/usr/bin/env python3
"""Minimal pinned MSC/RTLink experiment for the __ffree archive lookup case.

Only test-owned C sources are compiled. Test outputs are never executed and
the original game executable is neither opened nor used as a linker input.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent

SOURCES = {
    "natural_public_selfref": r"""/* test-owned model of the C spelling of __ffree */
void far _ffree(char far *p);
void far free(void far *p);

void far * far malloc(unsigned size)
{
    size = 0;
    return (void far *)0;
}

void far _ffree(char far *p)
{
    if (p != 0) *p = *p;
}

void far free(void far *p)
{
    _ffree((char far *)p);
}

int main(void)
{
    return 0;
}
""",
    "unique_internal_control": r"""/* unique game names; helper is internal and never allocates */
static void far game_ffree_inner(char far *p)
{
    if (p != 0) *p = *p;
}

void far * far malloc(unsigned size)
{
    size = 0;
    return (void far *)0;
}

void far game_ffree(char far *p)
{
    game_ffree_inner(p);
}

void far game_free(void far *p)
{
    game_ffree((char far *)p);
}

int main(void)
{
    return 0;
}
""",
    "symbolic_define_owner": r"""/* unresolved API spelling is backed by a differently named game owner */
void far _ffree(char far *p);

void far * far malloc(unsigned size)
{
    size = 0;
    return (void far *)0;
}

void far free(void far *p)
{
    _ffree((char far *)p);
}

void far game_ffree(char far *p)
{
    if (p != 0) *p = *p;
}

int main(void)
{
    return 0;
}
""",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(path: Path) -> dict:
    data = path.read_bytes()
    return {"path": str(path.resolve()), "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest()}


def main() -> int:
    sys.path.insert(0, str(ROOT / "tools"))
    import compiler
    import rtlink
    from omf import OmfReader

    manifest_path = ROOT / "layout/manifest.json"
    toolchain_path = ROOT / "layout/toolchain.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    tc = json.loads(toolchain_path.read_text(encoding="utf-8"))
    source_cases = dict(SOURCES)
    for case, source in list(SOURCES.items()):
        suffix = "_no_main" if case != "symbolic_define_owner" else "_no_define_no_main"
        source_cases[case + suffix] = source.split("int main(void)", 1)[0].rstrip() + "\n"
    out = OUT / "runs-v34"
    if out.exists():
        raise RuntimeError(f"refusing to overwrite existing output {out}")
    out.mkdir()
    compiler.WORK = OUT / "compiler-work"
    compiler.WORK.mkdir(exist_ok=True)

    pins: dict[str, dict] = {}
    for path in (Path(__file__), manifest_path, toolchain_path,
                 ROOT / "tools/compiler.py", ROOT / "tools/rtlink.py",
                 ROOT / "tools/omf.py"):
        pins[str(path.resolve()).lower()] = pin(path)
    compiler_profile = tc["profiles"]["msc600ax"]
    for rel, expected in compiler_profile["files"].items():
        path = Path(compiler_profile["directory"]) / rel
        assert sha(path) == expected
        pins[str(path.resolve()).lower()] = pin(path)
    compiler_runner = tc["runner"]
    compiler_runner_path = Path(compiler_runner["path"])
    assert sha(compiler_runner_path) == compiler_runner["sha256"]
    pins[str(compiler_runner_path.resolve()).lower()] = pin(compiler_runner_path)
    for lib in ("llibcr.lib", "libh.lib"):
        path = Path(manifest["runtime"]["libraries"][lib]["path"])
        expected = manifest["runtime"]["libraries"][lib]["sha256"]
        assert sha(path) == expected
        pins[str(path.resolve()).lower()] = pin(path)
    runner = tc["runners"]["dosbox-x"]
    runner_path = Path(runner["path"])
    assert sha(runner_path) == runner["sha256"]
    pins[str(runner_path.resolve()).lower()] = pin(runner_path)
    for profile in ("rtlink400", "rtlink610"):
        lp = tc["linkers"][profile]
        for rel, expected in lp["files"].items():
            path = Path(lp["directory"]) / rel
            assert sha(path) == expected
            pins[str(path.resolve()).lower()] = pin(path)

    reader = OmfReader(communals=True)
    built: dict[str, dict] = {}
    for case, source in source_cases.items():
        source_path = OUT / f"{case}.c"
        source_path.write_text(source, encoding="ascii", newline="\r\n")
        result = compiler.compile_c(source, "msc600ax", basename=case[:8].upper(), keep=True)
        (OUT / f"{case}.compiler.log").write_text(result.log, encoding="latin1")
        if not result.ok or result.obj is None:
            raise RuntimeError(f"MSC failed for {case}: {result.log}")
        obj_path = OUT / f"{case}.obj"
        obj_path.write_bytes(result.obj)
        obj = reader.read(result.obj, case)
        built[case] = {"source": pin(source_path), "compiler_log": pin(OUT / f"{case}.compiler.log"),
                       "object": pin(obj_path), "object_publics": obj.publics,
                       "compiler_profile": "msc600ax", "compiler_flags": compiler_profile["flags"],
                       "compiler_argv": result.argv,
                       "object_externals": obj.externals, "object_communals": obj.communals,
                       "object_fixups___ffree": [f for f in obj.linker_fixups
                           if f.get("target_kind") == "external" and f.get("target") == "__ffree"],
                       "object_fixups___malloc": [f for f in obj.linker_fixups
                           if f.get("target_kind") == "external" and f.get("target") == "_malloc"],
                       "segment_defs": obj.segment_defs}
        pins[str(source_path.resolve()).lower()] = built[case]["source"]
        pins[str(OUT.joinpath(f"{case}.compiler.log").resolve()).lower()] = built[case]["compiler_log"]
        pins[str(obj_path.resolve()).lower()] = built[case]["object"]

    natural = built["natural_public_selfref"]
    assert any(p["name"] == "__ffree" for p in natural["object_publics"])
    assert "__ffree" in natural["object_externals"]
    assert any(p["name"] == "_malloc" for p in natural["object_publics"])
    assert not natural["object_fixups___malloc"]
    assert any(f.get("self_relative") for f in natural["object_fixups___ffree"])
    unique = built["unique_internal_control"]
    assert not any(p["name"] in ("__ffree", "_free") for p in unique["object_publics"])
    assert "__ffree" not in unique["object_externals"]
    assert any(p["name"] == "_malloc" for p in unique["object_publics"])
    alias_obj = built["symbolic_define_owner"]
    assert "__ffree" in alias_obj["object_externals"]
    assert any(p["name"] == "_game_ffree" for p in alias_obj["object_publics"])
    assert not any(p["name"] == "__ffree" for p in alias_obj["object_publics"])
    assert any(p["name"] == "_malloc" for p in alias_obj["object_publics"])

    # Preserve actual library member PUBDEF/EXTDEF records for every selected
    # archive component seen in the raw logs.
    archive_members: dict[tuple[str, str], dict] = {}
    for lib in ("llibcr.lib", "libh.lib"):
        path = Path(manifest["runtime"]["libraries"][lib]["path"])
        for member_name, raw in reader.split_library(path.read_bytes()):
            obj = reader.read(raw, member_name)
            archive_members[(lib.lower(), member_name.lower())] = {
                "library": lib, "member": member_name,
                "raw_sha256": hashlib.sha256(raw).hexdigest(),
                "publics": obj.publics, "externals": obj.externals,
                "communals": obj.communals, "segment_defs": obj.segment_defs,
                "linker_fixups___ffree": [f for f in obj.linker_fixups
                    if f.get("target_kind") == "external" and f.get("target") == "__ffree"],
            }
    assert any(p["name"] == "__ffree" for p in
               archive_members[("llibcr.lib", "fmalloc.asm")]["publics"])

    runs: dict[str, dict] = {}
    old_work = compiler.WORK
    compiler.WORK = OUT / "link-tool-scratch"
    try:
        for case in source_cases:
            runs[case] = {}
            for profile in ("rtlink400", "rtlink610"):
                link_dir = out / case / profile
                link_dir.mkdir(parents=True)
                shutil.copyfile(OUT / f"{case}.obj", link_dir / "OWNER.OBJ")
                lines = ["OUTPUT PROBE", "MAP = PROBE S,N,A,L,V,X", "NODEFLIB",
                         "LIBRARY LLIBCR, LIBH", "VERBOSE", "FILE OWNER"]
                if case == "symbolic_define_owner":
                    lines.append("DEFINE __ffree = _game_ffree")
                (link_dir / "T.LNK").write_bytes(("\r\n".join(lines) + "\r\n").encode("ascii"))
                rc = rtlink.run_link(link_dir, profile, timeout=900)
                log_path, map_path, image_path = (link_dir / "LINK.LOG", link_dir / "PROBE.MAP",
                                                   link_dir / "PROBE.EXE")
                log = log_path.read_text(encoding="latin1", errors="replace") if log_path.exists() else ""
                map_text = map_path.read_text(encoding="latin1", errors="replace") if map_path.exists() else ""
                selected_pairs = re.findall(r"(LLIBCR|LIBH)\.LIB\(([^)]+)\)", log, re.IGNORECASE)
                selected = [member for _, member in selected_pairs]
                selected_lower = {name.lower() for name in selected}
                selected_audit = []
                for library, member in selected_pairs:
                    record = archive_members.get((library.lower() + ".lib", member.lower()))
                    if record:
                        selected_audit.append(record)
                diagnostics = [line.strip() for line in log.splitlines()
                               if re.search(r"wrt\d{4}|warning|error|fatal|undefined|duplicate|multiply defined",
                                            line, re.IGNORECASE)]
                symbol_rows = {}
                for name in ("__ffree", "_free", "_game_ffree", "_malloc"):
                    symbol_rows[name] = [line.strip() for line in map_text.splitlines()
                                         if re.search(r"\b" + re.escape(name) + r"\b", line, re.IGNORECASE)]
                runs[case][profile] = {
                    "runner_returncode": rc,
                    "script": pin(link_dir / "T.LNK"),
                    "link_log": pin(log_path) if log_path.exists() else None,
                    "map": pin(map_path) if map_path.exists() else None,
                    "image_quarantined_never_executed": pin(image_path) if image_path.exists() else None,
                    "selected_members": selected,
                    "selected_member_omf_audit": selected_audit,
                    "selected_fmalloc": "fmalloc.asm" in selected_lower,
                    "selected_free": "free.asm" in selected_lower,
                    "selected_malloc": "malloc.asm" in selected_lower,
                    "selected_fdata": "fdata.asm" in selected_lower,
                    "wrt0011_duplicate_ffree": any("wrt0011" in d.lower() and "__ffree" in d.lower()
                                                    for d in diagnostics),
                    "diagnostics": diagnostics,
                    "map_symbol_rows": symbol_rows,
                    "exe_executed": False,
                }
                pins[str((link_dir / "T.LNK").resolve()).lower()] = runs[case][profile]["script"]
                for raw_path in (log_path, map_path, image_path):
                    if raw_path.exists():
                        pins[str(raw_path.resolve()).lower()] = pin(raw_path)
    finally:
        compiler.WORK = old_work

    # A compact byte-free receipt: all source inputs are test-authored C and
    # every compiler/linker result is pinned; raw logs/maps remain beside it.
    receipt = {
        "schema": "simant-dos-ffree-archive-selection-v29-v1",
        "root_reviewed": False,
        "admitted": False,
        "scope": "Minimal test-owned allocator-wrapper symbol contract; not a game build or full game behavior claim.",
        "source_cases": built,
        "archive_member_reference_audit": {
            "llibcr_fmalloc_asm": archive_members[("llibcr.lib", "fmalloc.asm")],
            "llibcr_malloc_asm": archive_members[("llibcr.lib", "malloc.asm")],
            "llibcr_free_asm": archive_members[("llibcr.lib", "free.asm")],
        },
        "link_cases": runs,
        "observations": {
            "natural_object_has_same_module_public_and_external___ffree": True,
            "natural_object_self_reference_fixup_is_self_relative": True,
            "natural_rtl400_extracts_fmalloc_and_warns_duplicate": runs["natural_public_selfref"]["rtlink400"]["selected_fmalloc"] and runs["natural_public_selfref"]["rtlink400"]["wrt0011_duplicate_ffree"],
            "natural_rtl610_positive_avoids_fmalloc_duplicate": (not runs["natural_public_selfref"]["rtlink610"]["selected_fmalloc"] and not runs["natural_public_selfref"]["rtlink610"]["wrt0011_duplicate_ffree"]),
            "natural_no_main_reproduces_version_contrast": (
                runs["natural_public_selfref_no_main"]["rtlink400"]["selected_fmalloc"]
                and runs["natural_public_selfref_no_main"]["rtlink400"]["wrt0011_duplicate_ffree"]
                and not runs["natural_public_selfref_no_main"]["rtlink610"]["selected_fmalloc"]
                and not runs["natural_public_selfref_no_main"]["rtlink610"]["wrt0011_duplicate_ffree"]),
            "unique_internal_control_still_extracts_fmalloc_without_game___ffree": all(
                runs["unique_internal_control_no_main"][p]["selected_fmalloc"]
                and not runs["unique_internal_control_no_main"][p]["wrt0011_duplicate_ffree"]
                for p in ("rtlink400", "rtlink610")),
            "symbolic_define_alias_does_not_prevent_fmalloc_selection": all(
                runs["symbolic_define_owner"][p]["selected_fmalloc"]
                for p in ("rtlink400", "rtlink610")),
            "all_images_quarantined": all(x["image_quarantined_never_executed"] and not x["exe_executed"]
                                           for case in runs.values() for x in case.values()),
        },
        "inputs": sorted(pins.values(), key=lambda x: x["path"].lower()),
        "no_original_executable_input": True,
        "no_production_source_or_tool_changes": True,
        "no_game_image_execution": True,
        "conclusion": "Selection behavior is demonstrated for this source-owned symbol contract only. It does not establish full game allocator semantics or resolve functional __fheap debt.",
    }
    receipt_path = OUT / "receipt-v34.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({case: {p: {
        "selected_fmalloc": v["selected_fmalloc"],
        "selected_free": v["selected_free"],
        "selected_malloc": v["selected_malloc"],
        "duplicate_wrt0011": v["wrt0011_duplicate_ffree"],
        "has_exe_quarantined": bool(v["image_quarantined_never_executed"]),
        "map_owner_ffree": v["map_symbol_rows"]["__ffree"][:2],
        "diagnostics": v["diagnostics"][:6]}
        for p, v in profiles.items()} for case, profiles in runs.items()}, indent=2))
    print(f"receipt={receipt_path} input_pins={len(pins)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
