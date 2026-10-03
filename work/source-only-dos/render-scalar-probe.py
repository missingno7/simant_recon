"""Audit and exercise the generated-only DOS render-scalar storage candidate.

The probe consumes canonical admitted sources and registered BEHAVIOR_EXACT
implementation sources for its source inventory. It compiles only this
data-only candidate and test-owned C fixtures, then links/runs them with the
pinned MSC startup libraries and RTLink profiles. Outputs stay under ignored
build/workers/dos_render_scalar_owners/candidate/; no original executable is
read.
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

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "build" / "workers" / "dos_render_scalar_owners" / "candidate"
SOURCES = WORK / "sources"
OBJECTS = WORK / "objects"
FIXTURES = WORK / "fixtures"
LINKS = WORK / "links"
PROBE_PATH = Path(__file__).resolve()
PROVIDER_PATH = ROOT / "work" / "source-only-dos" / "providers" / "render-scalars.c"
TARGETS = ("g_8BD2", "g_8BD4", "g_9126", "g_94E4")
SYMBOL_RE = re.compile(r"(?<![A-Za-z0-9_])_?(?:g_8BD2|g_8BD4|g_9126|g_94E4)\b")
EXPECTED_COMMS = [
    {"name": "_g_8BD2", "kind": "near", "length": 2},
    {"name": "_g_8BD4", "kind": "near", "length": 2},
    {"name": "_g_9126", "kind": "near", "length": 2},
    {"name": "_g_94E4", "kind": "near", "length": 1},
]
EXPECTED_PROVIDER = (
    "int near g_8BD2;\n"
    "int near g_8BD4;\n"
    "unsigned near g_9126;\n"
    "unsigned char near g_94E4;\n"
)
REQUIRED_CASES = {
    "bss_zero_typed_values": "PASS",
    "wrong_byte_view_of_word": "FAIL",
    "initialized_nonzero_owner": "FAIL",
}
sys.path.insert(0, str(ROOT / "tools"))

POSITIVE_MAIN = r'''extern int near g_8BD2;
extern int near g_8BD4;
extern unsigned near g_9126;
extern unsigned char near g_94E4;
extern int far puts(char far *text);

int main(void)
{
    if (g_8BD2 != 0 || g_8BD4 != 0 || g_9126 != 0 || g_94E4 != 0) {
        puts("FAIL");
        return 1;
    }
    g_8BD2 = 2;
    g_8BD4 = 1;
    g_9126 = 0x0388;
    g_94E4 = 0x100;
    if (g_8BD2 != 2 || g_8BD4 != 1 || g_9126 != 0x0388 || g_94E4 != 0) {
        puts("FAIL");
        return 2;
    }
    /* Integer promotion keeps every stored byte below 0x100. */
    if (g_94E4 >= 0x100) {
        puts("FAIL");
        return 3;
    }
    puts("PASS");
    return 0;
}
'''

WRONG_VIEW = r'''extern unsigned char near g_9126;
void far write_low_byte_view(void) { g_9126 = 0xcd; }
'''
WRONG_VIEW_MAIN = r'''extern int near g_8BD2;
extern int near g_8BD4;
extern unsigned near g_9126;
extern unsigned char near g_94E4;
extern void far write_low_byte_view(void);
extern int far puts(char far *text);

int main(void)
{
    if (g_8BD2 != 0 || g_8BD4 != 0 || g_9126 != 0 || g_94E4 != 0) {
        puts("FAIL");
        return 1;
    }
    g_9126 = 0xab00;
    write_low_byte_view();
    if (g_9126 == 0xabcd) {
        puts("FAIL");
        return 2;
    }
    puts("PASS");
    return 0;
}
'''

UNSIGNED_TEST = r'''extern unsigned near g_9126;
int far unsigned_negative_test(void) { return g_9126 < 0; }
'''
SIGNED_TEST = r'''extern int near g_9126;
int far signed_negative_test(void) { return g_9126 < 0; }
'''


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def pin_file(path: Path, declared_sha: str | None = None) -> dict:
    digest = sha_file(path)
    if declared_sha is not None and digest != declared_sha:
        raise ValueError(f"source pin mismatch: {path}")
    try:
        label = path.relative_to(ROOT).as_posix()
    except ValueError:
        label = str(path)
    return {"path": label, "sha256": digest, "size": path.stat().st_size}


def source_refs(path: Path) -> list[dict]:
    rows = []
    for number, line in enumerate(path.read_text(encoding="latin1").splitlines(), 1):
        if SYMBOL_RE.search(line):
            rows.append({"line": number, "text": line.rstrip()})
    return rows


def source_escapes(rows: list[dict]) -> list[dict]:
    found = []
    for row in rows:
        line = row["text"]
        for name in TARGETS:
            token = r"_?" + re.escape(name)
            if (re.search(rf"(?<!&)\&(?!&)\s*{token}\b", line)
                    or re.search(rf"\b{token}\s*\[", line)
                    or re.search(rf"\b(?:offset|lea|les|lds)\b.*\b{token}\b", line, re.I)):
                found.append({"line": row["line"], "symbol": name, "text": line})
    return found


def write_source(name: str, content: str) -> Path:
    path = SOURCES / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content.encode("ascii"))
    return path


def compile_source(compiler, name: str, source: str, flags: list[str] | None = None) -> bytes:
    path = write_source(name + ".c", source)
    basename = name.upper()
    if len(basename) > 8:
        raise ValueError(f"fixture basename exceeds DOS 8.3: {basename}")
    result = compiler.compile_c(source, "msc600ax", flags or ["/AL", "/Os"],
                                basename=basename, keep=False)
    if not result.ok or result.obj is None:
        raise RuntimeError(f"MSC compile failed for {name}:\n{result.log}")
    out = OBJECTS / (basename + ".OBJ")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(result.obj)
    return result.obj


def communal_rows(raw: bytes) -> list[dict]:
    from omf import OmfReader
    mod = OmfReader(communals=True).read(raw)
    return sorted(({"name": row["name"], "kind": row["kind"], "length": row["length"]}
                   for row in mod.communals), key=lambda row: row["name"])


def omf_module(raw: bytes, name: str):
    from omf import OmfReader
    return OmfReader(communals=True).read(raw, name)


def read_text(path: Path) -> str:
    return path.read_text(encoding="latin1", errors="replace") if path.exists() else "<missing>"


def link_case(linker_name: str, linker: dict, runner: dict, runtimes: list[dict],
              compiler, objects: dict[str, bytes], case: str, owner: str,
              expected: str, observed: str, extra_objects: tuple[str, ...] = ()) -> dict:
    directory = LINKS / linker_name / case
    directory.mkdir(parents=True, exist_ok=True)
    for filename in ("PROBE.EXE", "PROBE.MAP", "RUN.LOG", "LINK.LOG"):
        (directory / filename).unlink(missing_ok=True)
    object_names = (owner, *extra_objects, "MAIN")
    for name in object_names:
        (directory / (name.upper() + ".OBJ")).write_bytes(objects[name])
    for row in runtimes:
        shutil.copyfile(row["path"], directory / Path(row["path"]).name.upper())
    (directory / "PROBE.LNK").write_bytes(
        ("OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n"
         "LIBRARY LLIBCR, LIBH\r\nFILE " + ", ".join(n.upper() for n in object_names) + "\r\n").encode("ascii"))
    (directory / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (directory / "RUN.BAT").write_bytes(
        (f"@echo off\r\nD:\\{linker['executable']} @PROBE.LNK < NUL > LINK.LOG\r\n"
         "PROBE.EXE > RUN.LOG\r\n").encode("ascii"))
    config = []
    for section, values in runner["conf"].items():
        config.append("[" + section + "]")
        config.extend(f"{key}={value}" for key, value in values.items())
    tool_dir = compiler.pinned_tree(linker)
    config.extend(("[autoexec]", f'mount c "{directory.resolve()}"',
                   f'mount d "{tool_dir}" -ro', "c:", "call RUN.BAT", "exit"))
    conf_path = directory / "dosbox.conf"
    conf_path.write_text("\n".join(config) + "\n", encoding="ascii")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    result = subprocess.run([runner["path"], "-conf", str(conf_path), "-fastlaunch", "-exit", "-nomenu"],
                            cwd=directory, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=120,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    actual = read_text(directory / "RUN.LOG").strip()
    exe = directory / "PROBE.EXE"
    return {
        "linker": linker_name,
        "case": case,
        "expected": expected,
        "actual": actual,
        "observed_contract": observed,
        "link_succeeded": exe.exists(),
        "dosbox_exit": result.returncode,
        "files": [pin_file(path) for path in sorted(directory.iterdir()) if path.is_file()],
        "passed": exe.exists() and result.returncode == 0 and actual == expected,
    }


def add_input(inputs: list[dict], seen: set[tuple[str, str]], path: Path,
              declared_sha: str | None = None) -> dict:
    row = pin_file(path, declared_sha)
    identity = (row["path"], row["sha256"])
    if identity not in seen:
        seen.add(identity)
        inputs.append(row)
    return row


def main() -> int:
    for directory in (WORK, SOURCES, OBJECTS, FIXTURES, LINKS):
        directory.mkdir(parents=True, exist_ok=True)

    provider_source = PROVIDER_PATH.read_text(encoding="ascii")
    if provider_source.replace("\r\n", "\n") != EXPECTED_PROVIDER:
        raise ValueError("tracked render-scalars provider differs from the parent-reviewed normalized source")

    import compiler
    from omf import OmfReader
    compiler.WORK = WORK / "compiler-work"
    compiler.WORK.mkdir(parents=True, exist_ok=True)

    manifest_path = ROOT / "layout" / "manifest.json"
    symbols_path = ROOT / "layout" / "symbols.json"
    behavior_path = ROOT / "evidence" / "behavior" / "manifest.json"
    toolchain_path = ROOT / "layout" / "toolchain.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    symbols = json.loads(symbols_path.read_text(encoding="utf-8"))["data"]
    behavior = json.loads(behavior_path.read_text(encoding="utf-8"))
    manifest_sources = {row["source"]: row["source_sha256"]
                        for row in manifest["modules"].values() if row.get("source")}
    for rel, digest in manifest_sources.items():
        source_path = ROOT / rel
        if not source_path.is_file() or sha_file(source_path) != digest:
            raise ValueError(f"canonical manifest source pin mismatch: {rel}")

    canonical = []
    for path in sorted((ROOT / "src").rglob("*")):
        if path.suffix.lower() not in (".c", ".asm"):
            continue
        refs = source_refs(path)
        if not refs:
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel not in manifest_sources:
            raise ValueError(f"canonical reference source lacks manifest row: {rel}")
        canonical.append({**pin_file(path, manifest_sources[rel]),
                          "references": refs, "pointer_or_index_escapes": source_escapes(refs)})

    exact_by_path: dict[str, dict] = {}
    exact_evidence = []
    for function, entry in behavior["entries"].items():
        if entry.get("status") != "BEHAVIOR_EXACT":
            continue
        evidence_path = ROOT / entry["evidence_path"]
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        source_row = evidence.get("source", {}) or {}
        rel = source_row.get("path")
        exact_evidence.append({"function": function,
                               **pin_file(evidence_path)})
        if not rel:
            continue
        src = ROOT / rel
        if rel not in exact_by_path:
            exact_by_path[rel] = {**pin_file(src, source_row.get("sha256")),
                                  "functions": [], "references": source_refs(src)}
        exact_by_path[rel]["functions"].append(function)
    exact_hits = [row for row in exact_by_path.values() if row["references"]]
    exact_escapes = [{"path": row["path"], **escape}
                     for row in exact_hits for escape in source_escapes(row["references"])]
    canonical_escapes = [{"path": row["path"], **escape}
                         for row in canonical for escape in row["pointer_or_index_escapes"]]

    addresses = {
        "g_8BD2": {"c_type": "int near", "size": 2, "seg": 0x55B3, "off": 0x8BD2},
        "g_8BD4": {"c_type": "int near", "size": 2, "seg": 0x55B3, "off": 0x8BD4},
        "g_9126": {"c_type": "unsigned near", "size": 2, "seg": 0x55B3, "off": 0x9126},
        "g_94E4": {"c_type": "unsigned char near", "size": 1, "seg": 0x55B3, "off": 0x94E4},
    }
    symbol_views = {}
    for name, spec in addresses.items():
        row = symbols.get(name)
        if row is None or row.get("seg") != spec["seg"] or row.get("off") != spec["off"]:
            raise ValueError(f"symbol registry address changed for {name}: {row}")
        aliases = [other for other, value in symbols.items()
                   if other != name and value.get("seg") == spec["seg"] and value.get("off") == spec["off"]]
        interior = [other for other, value in symbols.items()
                    if value.get("seg") == spec["seg"] and spec["off"] < value.get("off", -1) < spec["off"] + spec["size"]]
        if aliases or interior:
            raise ValueError(f"unexpected registered alias/interior name at {name}: {aliases + interior}")
        symbol_views[name] = {
            "registered_address": {"segment": spec["seg"], "offset": spec["off"]},
            "registered_address_aliases": aliases,
            "registered_interior_names": interior,
            "neighboring_names": [
                {"name": other, "offset": value["off"]}
                for other, value in symbols.items()
                if value.get("seg") == spec["seg"] and other != name
                and abs(value.get("off", -100000) - spec["off"]) <= 4],
        }

    if canonical_escapes or exact_escapes:
        raise ValueError(f"source-level pointer/index/arithmetic escape found: {canonical_escapes + exact_escapes}")

    declaration_patterns = {
        "g_8BD2": r"\bextern\s+int\s+near\s+g_8BD2\s*;",
        "g_8BD4": r"\bextern\s+int\s+near\s+g_8BD4\s*;",
        "g_9126": r"\bextern\s+unsigned\s+near\s+g_9126\s*;",
        "g_94E4": r"\bextern\s+unsigned\s+char\s+near\s+g_94E4\s*;",
    }
    declaration_evidence = {}
    for name, pattern in declaration_patterns.items():
        matching = []
        for row in canonical:
            for hit in row["references"]:
                if re.search(pattern, hit["text"]):
                    matching.append({"path": row["path"], "line": hit["line"], "text": hit["text"]})
        if not matching:
            raise ValueError(f"expected canonical declaration not found for {name}")
        declaration_evidence[name] = matching

    module_controls = []
    for module_key, basename, target_names in (
            ("S04:35F5", "S04MOD", {"_g_8BD2", "_g_8BD4"}),
            ("root:0250", "ROOT0250", {"_g_9126", "_g_94E4"})):
        row = manifest["modules"][module_key]
        module_source = (ROOT / row["source"]).read_text(encoding="latin1")
        module_obj = compile_source(compiler, basename, module_source, row["flags"])
        module = OmfReader().read(module_obj, basename + ".OBJ")
        if not target_names <= set(module.externals):
            raise ValueError(f"whole module {module_key} lost scalar externals")
        target_fixups = [fixup for fixup in module.linker_fixups
                         if fixup.get("target") in target_names]
        runtime_fixups = [fixup for fixup in target_fixups
                          if fixup.get("segment", "").endswith("_TEXT")]
        debug_fixups = [fixup for fixup in target_fixups if fixup not in runtime_fixups]
        if ({fixup.get("target") for fixup in runtime_fixups} != target_names
                or any(fixup.get("loc") != "offset16" or fixup.get("width") != 2
                       for fixup in runtime_fixups)
                or any(not fixup.get("segment", "").startswith("$$") for fixup in debug_fixups)):
            raise ValueError(f"whole module {module_key} scalar references are not near runtime views")
        module_controls.append({"module": module_key, "source": row["source"],
                               "source_sha256": row["source_sha256"], "flags": row["flags"],
                               "target_externals": sorted(target_names),
                               "runtime_fixup_count": len(runtime_fixups),
                               "runtime_fixup_locations": sorted({f["loc"] for f in runtime_fixups}),
                               "runtime_fixup_widths": sorted({f["width"] for f in runtime_fixups}),
                               "debug_metadata_fixups_excluded": len(debug_fixups),
                               "debug_metadata_segments": sorted({f["segment"] for f in debug_fixups})})

    address_spellings = ("8bd2", "8bd4", "9126", "94e4")
    authoritative_paths = set(manifest_sources)
    authoritative_paths.update(row["path"] for row in canonical)
    authoritative_paths.update(row["path"] for row in exact_by_path.values())
    fixed_address_literals = []
    for rel in sorted(authoritative_paths):
        path = ROOT / rel
        if path.suffix.lower() not in (".c", ".asm"):
            continue
        for number, line in enumerate(path.read_text(encoding="latin1").splitlines(), 1):
            lowered = line.lower()
            for address in address_spellings:
                if re.search(rf"(?<![0-9a-f])(?:0x)?{address}h(?![0-9a-f])|0x{address}(?![0-9a-f])", lowered):
                    fixed_address_literals.append({"path": rel, "line": number,
                                                   "address": address, "text": line.rstrip()})

    # Compile and inspect the exact tracked provider plus test-owned fixtures.
    owner_obj = compile_source(compiler, "RSOWNER", provider_source, ["/AL", "/Os", "/Gs"])
    owner_mod = OmfReader(communals=True).read(owner_obj, "RSOWNER.OBJ")
    comms = sorted(({"name": r["name"], "kind": r["kind"], "length": r["length"]}
                    for r in owner_mod.communals), key=lambda row: row["name"])
    if comms != EXPECTED_COMMS:
        raise ValueError(f"candidate provider communal shape mismatch: {comms}")
    if (owner_mod.publics or owner_mod.local_publics or owner_mod.linker_fixups
            or any(owner_mod.segment_lengths.values()) or any(owner_mod.segments.values())):
        raise ValueError("provider emitted code, initialized data, publics, or fixups")

    positive_obj = compile_source(compiler, "MAIN", POSITIVE_MAIN)
    wrong_obj = compile_source(compiler, "WRVIEW", WRONG_VIEW)
    wrong_main_obj = compile_source(compiler, "BADMAIN", WRONG_VIEW_MAIN)
    unsigned_obj = compile_source(compiler, "UNSGNED", UNSIGNED_TEST)
    signed_obj = compile_source(compiler, "SIGNED", SIGNED_TEST)
    wrong_byte_extent_obj = compile_source(
        compiler, "WRG94E4", provider_source.replace("unsigned char near g_94E4;", "unsigned near g_94E4;"),
        ["/AL", "/Os", "/Gs"])
    wrong_word_extent_obj = compile_source(
        compiler, "SHORT912", provider_source.replace("unsigned near g_9126;", "unsigned char near g_9126;"),
        ["/AL", "/Os", "/Gs"])
    initialized_source = provider_source.replace("unsigned char near g_94E4;", "unsigned char near g_94E4 = 1;")
    if initialized_source == provider_source:
        raise ValueError("initialized-owner negative control did not mutate provider source")
    initialized_obj = compile_source(compiler, "RSINIT", initialized_source, ["/AL", "/Os", "/Gs"])

    wrong_byte_rows = communal_rows(wrong_byte_extent_obj)
    wrong_word_rows = communal_rows(wrong_word_extent_obj)
    if ({"name": "_g_94E4", "kind": "near", "length": 2} not in wrong_byte_rows
            or wrong_byte_rows == EXPECTED_COMMS):
        raise ValueError(f"wrong g_94E4 extent control failed: {wrong_byte_rows}")
    if ({"name": "_g_9126", "kind": "near", "length": 1} not in wrong_word_rows
            or wrong_word_rows == EXPECTED_COMMS):
        raise ValueError(f"wrong g_9126 extent control failed: {wrong_word_rows}")
    init_mod = OmfReader(communals=True).read(initialized_obj, "RSINIT.OBJ")
    if any(row["name"] == "_g_94E4" for row in init_mod.communals) or not any(
            row["name"] == "_g_94E4" for row in init_mod.publics):
        raise ValueError("initialized g_94E4 contrast was not emitted as initialized public data")

    # A width-only COMM check cannot distinguish signed and unsigned words.
    # Compile the two comparison views and pin that the source types generate
    # distinct object code; the unsigned comparison folds away its read while
    # the signed comparison retains a near word relocation.
    u_mod = OmfReader().read(unsigned_obj, "UNSGNED.OBJ")
    s_mod = OmfReader().read(signed_obj, "SIGNED.OBJ")
    if "_g_9126" not in u_mod.externals or "_g_9126" not in s_mod.externals:
        raise ValueError("signedness comparison controls lack the expected word reference")
    if (u_mod.segment_length("UNSGNED_TEXT") == s_mod.segment_length("SIGNED_TEXT")
            or u_mod.segments.get("UNSGNED_TEXT") == s_mod.segments.get("SIGNED_TEXT")):
        raise ValueError("signedness contrast lacks an object-code length distinction")
    signed_fixups = [f for f in s_mod.linker_fixups if f.get("target") == "_g_9126"]
    unsigned_fixups = [f for f in u_mod.linker_fixups if f.get("target") == "_g_9126"]
    if (unsigned_fixups or len(signed_fixups) != 1
            or signed_fixups[0].get("loc") != "offset16" or signed_fixups[0].get("width") != 2):
        raise ValueError("signedness object contrast did not yield no unsigned runtime read and one signed near word read")

    tc = compiler.toolchain()
    runner = tc["runners"]["dosbox-x"]
    if sha_file(Path(runner["path"])) != runner["sha256"]:
        raise ValueError("pinned DOSBox-X runner hash mismatch")
    runtime_rows = list(manifest["runtime"]["libraries"].values())
    for runtime in runtime_rows:
        if sha_file(Path(runtime["path"])) != runtime["sha256"]:
            raise ValueError(f"runtime library pin mismatch: {runtime['path']}")

    objects = {"RSOWNER": owner_obj, "MAIN": positive_obj,
               "WRVIEW": wrong_obj, "BADMAIN": wrong_main_obj,
               "RSINIT": initialized_obj}
    cases = []
    linker_inputs = {}
    for linker_name in ("rtlink400", "rtlink610"):
        linker = tc["linkers"][linker_name]
        for rel, digest in linker["files"].items():
            path = Path(linker["directory"]) / rel
            if sha_file(path) != digest:
                raise ValueError(f"linker component pin mismatch: {linker_name}/{rel}")
        linker_inputs[linker_name] = linker["files"]
        for case_name, owner_name, main_name, expected, observed, extra in (
                ("bss_zero_typed_values", "RSOWNER", "MAIN", "PASS",
                 "CRT-entry zero BSS; distinct scalar writes, g_94E4 byte truncation, and byte-promotion range check", ()),
                ("wrong_byte_view_of_word", "RSOWNER", "BADMAIN", "FAIL",
                 "a mismatched unsigned-char view writes only the low byte of g_9126, leaving 0xab in its high byte", ("WRVIEW",)),
                ("initialized_nonzero_owner", "RSINIT", "MAIN", "FAIL",
                 "initialized g_94E4 is nonzero at main entry, violating candidate BSS contract", ())):
            case_objects = dict(objects)
            case_objects["MAIN"] = objects[main_name]
            cases.append(link_case(linker_name, linker, runner, runtime_rows, compiler,
                                   case_objects, case_name, owner_name, expected, observed, extra))
    if len(cases) != 6 or not all(row["passed"] for row in cases):
        raise RuntimeError("required candidate-owned RTLink startup cases did not match")

    # Pin canonical manifest sources and selected BEHAVIOR_EXACT source files.
    inputs: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for path in (manifest_path, symbols_path, behavior_path, toolchain_path,
                 PROVIDER_PATH, PROBE_PATH):
        add_input(inputs, seen, path)
    for generated_source in sorted(SOURCES.glob("*.c")):
        add_input(inputs, seen, generated_source)
    for row in canonical:
        add_input(inputs, seen, ROOT / row["path"], row["sha256"])
    for row in exact_by_path.values():
        add_input(inputs, seen, ROOT / row["path"], row["sha256"])
    for row in exact_evidence:
        add_input(inputs, seen, ROOT / row["path"], row["sha256"])
    profile = tc["profiles"]["msc600ax"]
    for rel, digest in profile["files"].items():
        add_input(inputs, seen, Path(profile["directory"]) / rel, digest)
    for name, digest in (profile.get("include_files") or {}).items():
        add_input(inputs, seen, compiler.include_root(profile) / name, digest)
    for runtime in runtime_rows:
        add_input(inputs, seen, Path(runtime["path"]), runtime["sha256"])
    add_input(inputs, seen, Path(runner["path"]), runner["sha256"])
    for linker_name in ("rtlink400", "rtlink610"):
        linker = tc["linkers"][linker_name]
        for rel, digest in linker["files"].items():
            add_input(inputs, seen, Path(linker["directory"]) / rel, digest)

    source_files = canonical + [
        {**row, "registered_functions": sorted(row["functions"])}
        for row in exact_hits]
    lifecycle = {
        "minimap_scales": {
            "declarations": "src/S04/m35F5.c:89,100",
            "reset_before_use": "src/S04/m35F5.c:317-319 OpenMiniMapWin assigns g_8BD2/g_8BD4 to 2 or 1 before the drawing path",
            "later_uses": "src/S04/m35F5.c:269-366 scalar geometry and coordinate arithmetic",
            "startup_claim": "none; only the cited functional assignment is recorded"},
        "render_cache": {
            "declarations": "src/root/m0250.c:295,297",
            "reset_before_compute": "src/root/m0250.c:748-750 f_0250_1018 clears g_94E4 and g_9126 before deriving map/life values",
            "later_uses": "src/root/m0250.c:313-435,775-834,852-870,1177,2004",
            "byte_semantics": "g_94E4 remains unsigned char; comparisons with 0x100 at src/root/m0250.c:315,367,407 retain integer promotion of the byte",
            "startup_claim": "none; only the cited per-render reset path is recorded"}}
    bindings = {
        "schema": "simant-source-only-dos-render-scalar-bindings-candidate-v1",
        "status": "candidate_only_pending_parent_review",
        "module": "source-owned:render-scalars",
        "basename": "RSOWNER",
        "owner": None,
        "normalized_source": " ".join(EXPECTED_PROVIDER.split()),
        "communals": comms,
        "members": [{"name": name, **spec, **symbol_views[name],
                     "candidate_storage": "independent near tentative definition"}
                    for name, spec in addresses.items()],
        "source_inventory": {
            "canonical_reference_files": canonical,
            "registered_behavior_exact_reference_files": exact_hits,
            "superseded_initial_sources_scanned": False,
            "fixed_address_alias_scan": "Numeric fixed-address spellings in authoritative source are enumerated below.",
            "fixed_address_literals": fixed_address_literals,
            "pointer_or_index_escapes": canonical_escapes + exact_escapes,
            "typed_declarations": declaration_evidence,
            "whole_module_compiler_controls": module_controls,
        },
        "lifecycle": lifecycle,
        "claims": {"historical_tu": False, "historical_order": False,
                   "historical_owner": False, "historical_byte_identity": False,
                   "aggregate": False},
        "pins": inputs,
    }
    bindings_path = WORK / "render-scalar-bindings.json"
    bindings_path.write_text(json.dumps(bindings, indent=2) + "\n", encoding="utf-8")

    contract = {
        "schema": "simant-source-only-dos-render-scalar-contract-candidate-v1",
        "status": "candidate_only_pending_parent_review",
        "root_reviewed": False,
        "module": "source-owned:render-scalars",
        "communals": comms,
        "flat_required_cases": REQUIRED_CASES,
        "cases": cases,
        "all_required_checks_pass": len(cases) == 6 and all(row["passed"] and
            row["actual"] == REQUIRED_CASES[row["case"]] for row in cases),
        "inputs": inputs,
        "omf_controls": {
            "provider_is_data_only_near_common": True,
            "wrong_byte_extent_rows": wrong_byte_rows,
            "wrong_word_extent_rows": wrong_word_rows,
            "initialized_owner_public_rows": init_mod.publics,
            "initialized_owner_has_no_g_94E4_communal": True,
            "signedness_object_control": {
                "unsigned_externals": sorted(u_mod.externals),
                "unsigned_code_bytes": u_mod.segment_length("UNSGNED_TEXT"),
                "unsigned_target_fixups": [f for f in u_mod.linker_fixups if f.get("target") == "_g_9126"],
                "unsigned_code_sha256": sha_bytes(u_mod.segments.get("UNSGNED_TEXT", b"")),
                "signed_externals": sorted(s_mod.externals),
                "signed_code_bytes": s_mod.segment_length("SIGNED_TEXT"),
                "signed_target_fixups": [f for f in s_mod.linker_fixups if f.get("target") == "_g_9126"],
                "signed_code_sha256": sha_bytes(s_mod.segments.get("SIGNED_TEXT", b"")),
            },
        },
    }
    contract_path = WORK / "render-scalar-contract.json"
    contract_path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")

    receipt = {
        "schema": "simant-source-only-dos-render-scalar-receipt-v1",
        "status": "candidate_only_pending_parent_review",
        "bindings_path": pin_file(bindings_path),
        "contract_path": pin_file(contract_path),
        "source_inventory_file_count": len(source_files),
        "canonical_reference_files": len(canonical),
        "registered_behavior_exact_reference_files": len(exact_hits),
        "references": {row["path"]: row["references"] for row in source_files},
        "lifecycle": lifecycle,
        "pins": inputs,
        "runtime_cases": cases,
        "all_required_checks_pass": contract["all_required_checks_pass"],
        "limitations": [
            "Generated-only source storage proposal; no historical TU, owner, allocation order, aggregate, or original byte identity is claimed.",
            "The startup cases demonstrate only the test-owned provider under the pinned MSC CRT and RTLink 4.00/6.10 fixtures.",
            "No original executable, game object, or game stub is read or linked.",
            "Source inventory covers current manifest-backed canonical sources and only registered BEHAVIOR_EXACT evidence.source implementations; superseded experiments are excluded.",
            "The source-level escape scan is lexical and does not establish absent uses outside those authoritative source sets.",
        ],
    }
    receipt_path = WORK / "render-scalar-receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"bindings": str(bindings_path), "contract": str(contract_path),
                      "receipt": str(receipt_path), "all_required_checks_pass": contract["all_required_checks_pass"],
                      "cases": [{"linker": r["linker"], "case": r["case"],
                                 "actual": r["actual"], "passed": r["passed"]} for r in cases]}, indent=2))
    return 0 if contract["all_required_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
