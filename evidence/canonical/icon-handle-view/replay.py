"""Replay the current-source minimum mutable icon-handle slot proof.

Run from any working directory with:
  python evidence/canonical/icon-handle-view/replay.py
  python evidence/canonical/icon-handle-view/replay.py --out build/proofs/icon-handle-view-run

Every generated file goes to a new directory below repository build/. The runner
reads current canonical sources and inventories, compiles complete source variants,
and links only the supplied test-owned CRT fixtures. It does not publish or write
canonical files.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True


def find_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "layout" / "toolchain.json").is_file() and (candidate / "src" / "root" / "m208F.c").is_file():
            return candidate
    raise RuntimeError("Cannot locate repository root via layout/toolchain.json and src/root/m208F.c")


ROOT = find_root()
HERE = Path(__file__).resolve().parent
BUILD_ROOT = (ROOT / "build").resolve()
sys.path.insert(0, str(ROOT))

from dos import build as dos_build  # noqa: E402
from tools import compiler, context, exe, match, modules, search  # noqa: E402
from tools.omf import OmfReader  # noqa: E402

MODULE_KEY = "root:208F"
MODULE_SOURCE = ROOT / "src" / "root" / "m208F.c"
HANDLE = "fd_50F6_46D2"
HELPERS = ("f_208F_027F", "f_208F_02F0")
DECL_TYPED = "extern char far * far * far fd_50F6_46D2;"
DECL_RAW = "extern char far * far fd_50F6_46D2;"
DECL_NEAR = "extern char far * near * far fd_50F6_46D2;"
DECL_WORD = "extern int far * far * far fd_50F6_46D2;"
DECL_ARRAY1 = "extern char far * far * far fd_50F6_46D2[1];"
USE_TYPED = "*fd_50F6_46D2 +"
USE_ARRAY1 = "*fd_50F6_46D2[0] +"
FIXTURE_FLAGS = ["/AL", "/Os", "/Gs"]
CONSUMER_CASES = ("positive", "rawfar", "nearcell", "wordpayload", "array1")
EXPECTED_FIXTURE_SHA256 = {
    "INIT.c": "08f4a1e13d04098d6d931f9bb7ab749ea9b43b3c830cc84c3679e4b0ade9bdaf",
    "MAIN.c": "04a15a8d3a9b0a2d90d09c87032b201496d54cad8de36f4e1f284f12f448037b",
    "RAWMAIN.c": "640241d59b51d096f398a822446218aaaa746c15d3a5c26760f0c2c9a2440aa6",
    "RAWOWN.c": "900ce3314b8158d2f4f8b722ab8f0c8a456f1d74e343e0a275b50d53f99f9a74",
    "SHIFT.c": "41d5d9b5aefe66c3741405c130de29e8cb27f40c043228f1b2281ea59a06f033",
}
FIXTURE_CASES = {
    "typedroot": {"objects": ("MAIN", "OWN"), "expected": [
        "PASS_INITIAL_ZERO_4BYTE_VIEW", "PASS_HANDLE_CELL_REPOINT_BYTE_STRIDE",
        "PASS_TYPED_RAW_WRITE_ZERO_RESET"]},
    "movedtypedroot": {"objects": ("SHIFT", "MAIN", "OWN"), "expected": [
        "PASS_INITIAL_ZERO_4BYTE_VIEW", "PASS_HANDLE_CELL_REPOINT_BYTE_STRIDE",
        "PASS_TYPED_RAW_WRITE_ZERO_RESET"]},
    "rawfar": {"objects": ("RAWMAIN", "RAWOWN"), "expected": [
        "PASS_INITIAL_ZERO_4BYTE_VIEW", "FAIL_POINTER_CHAIN_OR_BYTE_STRIDE"]},
    "nonzeroinit": {"objects": ("MAIN", "INIT"), "expected": ["FAIL_INITIAL_ZERO"]},
}
FIXTURE_PROFILE = "msc600ax"
LINK_PROFILES = ("rtlink400", "rtlink610")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin(path: Path, raw: bytes | None = None) -> dict:
    path = Path(path)
    if raw is None:
        raw = path.read_bytes()
    try:
        name = path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        name = str(path.resolve())
    return {"path": name, "size": len(raw), "sha256": sha(raw)}


def write_bytes(path: Path, raw: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return path


def write_text(path: Path, text: str) -> Path:
    return write_bytes(path, text.encode("utf-8"))


def write_json(path: Path, value) -> Path:
    return write_text(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def select_output(argument: str | None) -> Path:
    build = BUILD_ROOT
    if not build.is_relative_to(ROOT.resolve()):
        raise ValueError("repository build/ must remain inside the repository")
    if argument is None:
        parent = build / "proofs"
        parent.mkdir(parents=True, exist_ok=True)
        return Path(tempfile.mkdtemp(prefix="icon-handle-view-", dir=parent))
    raw = Path(argument)
    output = (raw if raw.is_absolute() else ROOT / raw).resolve()
    try:
        relative = output.relative_to(build)
    except ValueError as error:
        raise ValueError("--out must resolve strictly beneath repository build/") from error
    if not relative.parts or any(part.casefold() == "evidence" for part in relative.parts):
        raise ValueError("--out cannot be build/ itself or an evidence path")
    if output.exists():
        raise ValueError("--out must name an absent fresh directory; prior outputs are preserved")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir()
    return output


def read_source(path: Path) -> tuple[bytes, str]:
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    if not text.isascii():
        raise ValueError(f"Compiler source is not ASCII: {path}")
    return raw, text.replace("\r\n", "\n").replace("\r", "\n")


def replace_exact(source: str, old: str, new: str, count: int, label: str) -> str:
    actual = source.count(old)
    if actual != count:
        raise ValueError(f"{label}: expected {count} source matches, found {actual}")
    return source.replace(old, new)


def consumer_sources(base: str) -> dict[str, str]:
    uses = base.count(USE_TYPED)
    if uses != 5:
        raise ValueError(f"m208F pointer-use shape changed: expected five '{USE_TYPED}' sites, found {uses}")
    variants = {"positive": base}
    variants["rawfar"] = replace_exact(
        replace_exact(base, DECL_TYPED, DECL_RAW, 1, "rawfar declaration"),
        USE_TYPED, "fd_50F6_46D2 +", 5, "rawfar pointer uses")
    variants["nearcell"] = replace_exact(base, DECL_TYPED, DECL_NEAR, 1, "near-cell declaration")
    variants["wordpayload"] = replace_exact(base, DECL_TYPED, DECL_WORD, 1, "word-payload declaration")
    variants["array1"] = replace_exact(
        replace_exact(base, DECL_TYPED, DECL_ARRAY1, 1, "one-element declaration"),
        USE_TYPED, USE_ARRAY1, 5, "one-element pointer uses")
    for case, text in variants.items():
        if text.count("fd_50F6_46D2") != base.count("fd_50F6_46D2"):
            raise ValueError(f"{case}: symbol occurrence count changed unexpectedly")
    return variants


def module_source_context(manifest: dict, source_raw: bytes, source_text: str) -> tuple[dict, list[str]]:
    row = manifest.get("modules", {}).get(MODULE_KEY)
    if row is None:
        raise ValueError(f"Current manifest has no {MODULE_KEY} row")
    if row.get("source") != "src/root/m208F.c" or row.get("source_sha256") != sha(source_raw):
        raise ValueError("Current whole m208F source does not match its current manifest source pin")
    if row.get("extent", {}).get("end", 0) - row.get("extent", {}).get("start", 0) != 1415:
        raise ValueError("Current m208F extent is not the reviewed 1,415-byte span")
    claims = row.get("claims", [])
    if len(claims) != 24 or len({c.get("name") for c in claims}) != 24:
        raise ValueError("Current m208F claim inventory is not exactly 24 unique claims")
    definitions = [n for n in modules.FUNC_DEF_RE.findall(source_text) if n.startswith("f_208F_")]
    claim_names = {c["name"] for c in claims}
    if len(definitions) != 24 or len(set(definitions)) != 24 or set(definitions) != claim_names:
        raise ValueError("Current m208F source no longer has one definition for each of its 24 claims")
    if source_text.count(DECL_TYPED) != 1:
        raise ValueError("Current m208F no longer has one exact typed root declaration")
    for helper in HELPERS:
        if helper not in definitions:
            raise ValueError(f"Required consumer helper is missing: {helper}")
    return row, definitions


def claim_public(obj, name: str) -> dict:
    public_name, record = match.public_in(obj, name)
    if record is None:
        raise AssertionError(f"Object lacks expected claim public {public_name}")
    return record


def claim_span(obj, name: str, segment: str) -> tuple[int, int]:
    public = claim_public(obj, name)
    same_segment_offsets = sorted({p["offset"] for p in obj.publics if p["segment"] == segment and p["offset"] > public["offset"]})
    stop = same_segment_offsets[0] if same_segment_offsets else len(obj.segments.get(segment, b""))
    return public["offset"], stop


def function_bytes(obj, name: str, segment: str, size: int) -> bytes:
    public = claim_public(obj, name)
    raw = bytes(obj.segments[segment])
    return raw[public["offset"]:public["offset"] + size]


def check_consumer_results(case: str, base_obj, obj, row: dict, result: dict) -> dict:
    expected_pass = case in ("positive", "array1")
    if result.get("compile_ok") is not True:
        raise RuntimeError(f"m208F {case} did not compile: {result.get('log')}")
    if result.get("exact") is not expected_pass:
        raise AssertionError(f"m208F {case} exact={result.get('exact')} expected {expected_pass}")
    statuses = {name: value.get("exact") for name, value in result.get("claims", {}).items()}
    expected_names = {claim["name"] for claim in row["claims"]}
    if set(statuses) != expected_names:
        raise AssertionError(f"m208F {case} claim result set changed")
    if expected_pass:
        if not all(statuses.values()) or not result.get("extent", {}).get("exact"):
            raise AssertionError(f"m208F {case} did not pass all 24 claims and its full extent")
    else:
        failed = {name for name, exact in statuses.items() if not exact}
        if failed != set(HELPERS):
            raise AssertionError(f"m208F {case} failures are {sorted(failed)}, expected only {HELPERS}")
        if result.get("extent", {}).get("exact"):
            raise AssertionError(f"m208F {case} unexpectedly passed the full historical extent")
    if len(obj.segments) == 0:
        raise AssertionError(f"m208F {case} OMF has no segments")
    code_segment = result.get("_code_segment_name")
    if code_segment is None:
        publics = [claim_public(obj, claim["name"]) for claim in row["claims"]]
        segments = {p["segment"] for p in publics}
        if len(segments) != 1:
            raise AssertionError(f"m208F {case} claims do not occupy one code segment")
        code_segment = segments.pop()
    contribution_bytes = bytes(obj.segments.get(code_segment, b""))
    if expected_pass and len(contribution_bytes) != 1415:
        raise AssertionError(f"m208F {case} code segment length is {len(contribution_bytes)}, expected 1415")
    if case == "rawfar" and len(contribution_bytes) != 1409:
        raise AssertionError(f"rawfar whole code segment length is {len(contribution_bytes)}, expected 1409")
    if case == "nearcell" and len(contribution_bytes) != 1411:
        raise AssertionError(f"nearcell whole code segment length is {len(contribution_bytes)}, expected 1411")
    if case == "wordpayload" and len(contribution_bytes) != 1415:
        raise AssertionError(f"wordpayload whole code segment length is {len(contribution_bytes)}, expected 1415")

    claim_sizes = {claim["name"]: claim["size"] for claim in row["claims"]}
    spans = {}
    for helper in HELPERS:
        start, stop = claim_span(obj, helper, code_segment)
        spans[helper] = {"start": start, "stop": stop, "size": stop - start}
    base_spans = {helper: claim_span(base_obj, helper, code_segment) for helper in HELPERS}
    if case in ("rawfar", "nearcell", "wordpayload"):
        want_delta = {"rawfar": -3, "nearcell": -2, "wordpayload": 0}[case]
        for helper in HELPERS:
            before = base_spans[helper][1] - base_spans[helper][0]
            after = spans[helper]["size"]
            if after - before != want_delta:
                raise AssertionError(f"{case} {helper} body delta is {after - before}, expected {want_delta}")
        for claim in row["claims"]:
            name = claim["name"]
            if name in HELPERS:
                continue
            before = function_bytes(base_obj, name, code_segment, claim_sizes[name])
            after = function_bytes(obj, name, code_segment, claim_sizes[name])
            if before != after:
                raise AssertionError(f"{case} changed non-target function bytes: {name}")
    if case == "wordpayload":
        changed_by_helper = {}
        base_bytes = bytes(base_obj.segments[code_segment])
        case_bytes = bytes(obj.segments[code_segment])
        for helper in HELPERS:
            b0, b1 = base_spans[helper]
            c0, c1 = claim_span(obj, helper, code_segment)
            before = base_bytes[b0:b1]
            after = case_bytes[c0:c1]
            sites = [i for i, (x, y) in enumerate(zip(before, after)) if x != y]
            if len(before) != len(after) or len(sites) != 1:
                raise AssertionError(f"wordpayload {helper} must differ at one shift operand byte; sites={sites}")
            changed_by_helper[helper] = {"offset_in_function": sites[0],
                                         "before": before[sites[0]], "after": after[sites[0]]}
    else:
        changed_by_helper = None
    return {"code_segment": code_segment, "code_segment_length": len(contribution_bytes),
            "helper_spans": spans, "wordpayload_operand_differences": changed_by_helper,
            "only_expected_claim_failures": not expected_pass, "passed": True}


def run_contexts(out: Path) -> dict:
    results = {}
    for name in HELPERS:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            context.show(name, raw=False, no_asm=False)
        text = buffer.getvalue()
        if name not in text or not text.strip():
            raise AssertionError(f"context.py produced no current context for {name}")
        path = write_text(out / "context" / f"{name}.txt", text)
        results[name] = pin(path)
    return results


def run_consumer_reviews(out: Path, manifest: dict, row: dict, base_text: str,
                         results_root: Path) -> dict:
    base_obj = None
    base_contribution = None
    all_results = {}
    claims = row["claims"]
    # The required context packets are produced before any source variant is drafted.
    contexts = run_contexts(out)
    variants = consumer_sources(base_text)
    for case in CONSUMER_CASES:
        text = variants[case]
        source_path = write_text(out / "sources" / "consumers" / f"{case}.c", text)
        collected = {}
        verification = modules.verify_module(text, copy.deepcopy(row), claims, collected, man=manifest)
        if "object" not in collected:
            raise RuntimeError(f"m208F {case} verifier did not return its whole OMF object")
        obj = OmfReader(communals=True).read(collected["object"], source_path.name)
        publics = [claim_public(obj, claim["name"]) for claim in claims]
        segments = {p["segment"] for p in publics}
        if len(segments) != 1:
            raise AssertionError(f"m208F {case} claim publics occupy {sorted(segments)}")
        code_segment = segments.pop()
        verification["_code_segment_name"] = code_segment
        if case == "positive":
            base_obj = obj
            base_contribution = verification["contribution_sha256"]
        if base_obj is None:
            raise AssertionError("positive current-source OMF must be available before contrasts")
        if case == "array1" and verification["contribution_sha256"] != base_contribution:
            raise AssertionError("one-element array diagnostic changed the whole nondebug OMF contribution")
        controls = check_consumer_results(case, base_obj, obj, row, verification)
        object_path = write_bytes(out / "objects" / "consumers" / f"{case}.OBJ", collected["object"])
        verification_path = write_json(out / "module-results" / f"{case}.json", verification)
        search_results = {}
        search_status = "EXACT" if case in ("positive", "array1") else "MISMATCH"
        for helper in HELPERS:
            search.ROOT = results_root / case
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rows = search.run(helper, [source_path], None, None, None, {}, True)
            if len(rows) != 1 or rows[0].get("status") != search_status:
                raise AssertionError(f"search.py {case}/{helper} result was {rows}, expected {search_status}")
            log_path = write_text(out / "search-results" / case / f"{helper}.txt", output.getvalue())
            json_path = write_json(out / "search-results" / case / f"{helper}.json", rows)
            search_results[helper] = {"status": rows[0]["status"], "result": pin(json_path), "log": pin(log_path)}
        all_results[case] = {"verification": verification, "control_checks": controls,
                             "source": pin(source_path), "object": pin(object_path),
                             "search": search_results, "module_result": pin(verification_path)}
        print(f"m208F {case}: exact={verification['exact']} extent={verification.get('extent', {}).get('exact')} "
              f"code-bytes={controls['code_segment_length']}", flush=True)
    return {"context_packets": contexts, "variants": all_results}


def omf_structure(obj) -> dict:
    return {"segments": {name: {"length": len(data), "sha256": sha(bytes(data))}
                          for name, data in sorted(obj.segments.items())},
            "segment_lengths": obj.segment_lengths, "segment_defs": obj.segment_defs,
            "groups": obj.groups, "publics": obj.publics, "local_publics": obj.local_publics,
            "externals": obj.externals, "external_scopes": obj.external_scopes,
            "local_externals": obj.local_externals, "communals": obj.communals,
            "fixups": obj.fixups, "linker_fixups": obj.linker_fixups}


def compile_provider_shapes(out: Path, source_path: Path, source_text: str,
                            inventory_row: dict) -> dict:
    base_decl = "char far * far * far fd_50F6_46D2;"
    if re.sub(r"/\*.*?\*/|//[^\n]*", "", source_text, flags=re.S).strip() != base_decl:
        raise ValueError("Canonical storage TU must contain only the reviewed far Handle slot")
    profile_name, flags = inventory_row.get("profile"), inventory_row.get("flags")
    if profile_name != "msc600ax" or flags != ["/AL", "/Os", "/Gs"]:
        raise ValueError("Canonical slot inventory changed its pinned MSC 6.00AX provider profile")
    compiler.verify_profile(profile_name)
    contract = inventory_row.get("storage_contract")
    if not isinstance(contract, dict):
        raise ValueError("Current program inventory lacks the canonical slot storage contract")
    specs = {"typedroot": (base_decl, 4), "rawfar": ("char far * far fd_50F6_46D2;", 4),
             "nearcell": ("char far * near * far fd_50F6_46D2;", 2),
             "array2": ("char far * far * far fd_50F6_46D2[2];", 8)}
    results, objects = {}, {}
    for case, (declaration, length) in specs.items():
        text = source_text if case == "typedroot" else replace_exact(
            source_text, base_decl, declaration, 1, f"provider {case} declaration")
        source = source_path if case == "typedroot" else write_text(
            out / "sources" / "providers" / f"{case}.c", text)
        result = compiler.compile_c(text, profile_name, flags, basename="ICONV4")
        if not result.ok or result.obj is None:
            raise RuntimeError(f"provider {case} failed to compile:\n{result.log}")
        obj = OmfReader(communals=True).read(result.obj, f"ICONV4-{case}")
        snapshot = dos_build.storage_snapshot(obj)
        comm = snapshot["communals"]
        if len(comm) != 1 or (comm[0].get("name"), comm[0].get("kind"), comm[0].get("length")) != (
                "_fd_50F6_46D2", "far", length):
            raise AssertionError(f"provider {case} communal shape differs: {comm}")
        if (snapshot["code_bytes"] or snapshot["live_initialized_bytes"] or snapshot["publics"] or
                snapshot["fixups"] or snapshot["local_publics"] or snapshot["imports"] or snapshot["live_segments"]):
            raise AssertionError(f"provider {case} has unexpected code/data/public/fixup/import shape")
        verified = dos_build.verify_storage(obj, contract) if case == "typedroot" else snapshot
        if case == "typedroot" and verified.get("status") != "PASS":
            raise AssertionError("canonical provider did not pass dos.build.verify_storage")
        object_path = write_bytes(out / "objects" / "providers" / f"{case}.OBJ", result.obj)
        log_path = write_text(out / "compiler-logs" / "providers" / f"{case}.txt", result.log)
        results[case] = {"expected_communal_length": length, "storage_snapshot": verified,
                         "source": pin(source), "object": pin(object_path), "compiler_log": pin(log_path),
                         "profile": profile_name, "flags": flags}
        objects[case] = obj
        print(f"provider {case}: FAR COMDEF length={length}", flush=True)
    if omf_structure(objects["typedroot"]) != omf_structure(objects["rawfar"]):
        raise AssertionError("typedroot and rawfar providers no longer share the same nondebug OMF shape")
    return results


def compile_fixture_sources(out: Path, storage_path: Path, storage_text: str) -> tuple[dict, dict]:
    sources = {name: HERE / "fixture-sources" / name for name in EXPECTED_FIXTURE_SHA256}
    sources["OWN.c"] = storage_path
    objects = {}
    results = {}
    compiler.verify_profile(FIXTURE_PROFILE)
    for filename in ("MAIN.c", "OWN.c", "SHIFT.c", "RAWMAIN.c", "RAWOWN.c", "INIT.c"):
        path = sources[filename]
        raw, text = read_source(path)
        expected = EXPECTED_FIXTURE_SHA256.get(filename)
        if (filename == "OWN.c" and text != storage_text) or (expected is not None and sha(raw) != expected):
            raise ValueError(f"Supplied test fixture changed or lacks a source pin: {filename}")
        name = Path(filename).stem
        result = compiler.compile_c(text, FIXTURE_PROFILE, FIXTURE_FLAGS, basename=name)
        if not result.ok or result.obj is None:
            raise RuntimeError(f"fixture {filename} failed to compile:\n{result.log}")
        obj = OmfReader(communals=True).read(result.obj, name)
        object_out = write_bytes(out / "objects" / "fixtures" / f"{name}.OBJ", result.obj)
        log_out = write_text(out / "compiler-logs" / "fixtures" / f"{name}.txt", result.log)
        results[name] = {"source": pin(path, raw), "object": pin(object_out),
                         "compiler_log": pin(log_out),
                         "profile": FIXTURE_PROFILE, "flags": FIXTURE_FLAGS}
        objects[name] = obj
    return results, objects


def validate_initializer_object(obj) -> dict:
    pub = claim_public(obj, HANDLE)
    matching = [f for f in obj.linker_fixups if f.get("segment") == pub["segment"] and
                f.get("offset") == pub["offset"] and f.get("width") == 4 and
                f.get("loc") == "pointer32" and f.get("target") == "_fixtureMaster"]
    if len(matching) != 1:
        raise AssertionError(f"INIT must retain one 32-bit far-pointer initializer fixup to fixtureMaster: {matching}")
    return {"public": pub, "pointer_initializer_fixups": matching,
            "one_32bit_far_pointer_fixup_to_fixtureMaster": True}


def parse_map(text: str) -> dict:
    rows = {}
    pattern = re.compile(r"^\s*([0-9A-F]{1,4}):([0-9A-F]{1,4})\s+(\S+)\s*$", re.I | re.M)
    for seg, off, name in pattern.findall(text):
        rows[name.casefold()] = {"segment": int(seg, 16), "offset": int(off, 16)}
    return rows


def parse_mz(raw: bytes) -> tuple[bytes, list[dict], int]:
    if len(raw) < 0x1C or raw[:2] != b"MZ":
        raise ValueError("Linked output is not an MZ executable")
    header_paras = struct.unpack_from("<H", raw, 8)[0]
    header_bytes = header_paras * 16
    reloc_count = struct.unpack_from("<H", raw, 6)[0]
    reloc_offset = struct.unpack_from("<H", raw, 24)[0]
    if header_bytes > len(raw) or reloc_offset + reloc_count * 4 > header_bytes:
        raise ValueError("MZ header or relocation table is outside the executable")
    relocations = []
    for index in range(reloc_count):
        off, seg = struct.unpack_from("<HH", raw, reloc_offset + index * 4)
        relocations.append({"offset": off, "segment": seg, "linear": seg * 16 + off})
    return raw[header_bytes:], relocations, header_bytes


def find_map_symbol(rows: dict, symbol: str) -> dict:
    key = symbol.casefold()
    if key not in rows:
        raise AssertionError(f"Linker map lacks required symbol {symbol}; map names include {list(rows)[:12]}")
    return rows[key]


def has_relocation_overlap(relocations: list[dict], at: int, width: int) -> bool:
    return any(max(at, row["linear"]) < min(at + width, row["linear"] + 2) for row in relocations)


def render_dosbox_conf(runner: dict, case_dir: Path, tools_dir: Path) -> str:
    lines = []
    for section, settings in runner["conf"].items():
        lines.append(f"[{section}]")
        lines.extend(f"{key}={value}" for key, value in settings.items())
    lines.extend(["[autoexec]", f'mount c "{case_dir.resolve()}"',
                  f'mount d "{tools_dir.resolve()}" -ro', "c:", "set LIB=C:\\;D:\\",
                  "call RUN.BAT", "exit"])
    return "\n".join(lines) + "\n"


def link_fixture(out: Path, profile_name: str, case_name: str, spec: dict,
                 fixture_objects: dict, tool: dict, runner: dict, tools_dir: Path,
                 runtime_libraries: dict) -> dict:
    case_dir = out / "links" / profile_name / case_name
    case_dir.mkdir(parents=True)
    ordered_names = list(spec["objects"])
    for name in ordered_names:
        shutil.copyfile(out / "objects" / "fixtures" / f"{name}.OBJ", case_dir / f"{name}.OBJ")
    library_names = []
    for canonical, name in (("llibcr.lib", "LLIBCR.LIB"), ("libh.lib", "LIBH.LIB")):
        raw = runtime_libraries[canonical]["bytes"]
        write_bytes(case_dir / name, raw)
        library_names.append(name)
    link = ["OUTPUT PROBE", "MAP = PROBE S,N,A,L", "NODEFLIB",
            "LIBRARY LLIBCR, LIBH", "FILE " + ", ".join(f"{name}.OBJ" for name in ordered_names)]
    write_bytes(case_dir / "PROBE.LNK", ("\r\n".join(link) + "\r\n").encode("ascii"))
    write_bytes(case_dir / "RTLINK.CFG", b"SYNTAX = FREEFORMAT\r\n")
    executable = Path(tool["executable"])
    if executable.is_absolute() or ".." in executable.parts:
        raise ValueError(f"Unsafe pinned linker executable path: {tool['executable']}")
    dos_executable = "D:\\" + str(executable).replace("/", "\\")
    batch = ("@echo off\r\n" + f"{dos_executable} @PROBE.LNK < NUL > LINK.LOG\r\n" +
             "if not exist PROBE.EXE goto noexe\r\n" +
             "PROBE.EXE > RUN.LOG\r\n" + "goto done\r\n" +
             ":noexe\r\n" + "echo NOEXE > RUN.LOG\r\n" + ":done\r\n")
    write_bytes(case_dir / "RUN.BAT", batch.encode("ascii"))
    conf_path = write_text(case_dir / "dosbox.conf", render_dosbox_conf(runner, case_dir, tools_dir))
    env = os.environ.copy()
    env.update({"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"})
    command = [runner["path"], "-conf", str(conf_path), "-fastlaunch", "-exit", "-nomenu"]
    proc = subprocess.run(command, cwd=case_dir, env=env, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, timeout=120,
                          creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    dosbox_log = write_bytes(case_dir / "DOSBOX.LOG", proc.stdout)
    link_path = case_dir / "LINK.LOG"
    run_path = case_dir / "RUN.LOG"
    exe_path = case_dir / "PROBE.EXE"
    map_path = case_dir / "PROBE.MAP"
    if not exe_path.is_file() or not map_path.is_file() or not link_path.is_file() or not run_path.is_file():
        raise RuntimeError(f"{profile_name}/{case_name}: linker/runtime output is incomplete (DOSBox rc={proc.returncode})")
    link_log = link_path.read_text(encoding="latin1")
    diagnostic = re.search(r"\b(?:warning|warnings|error|errors|fatal|WRT\d*|undefined|unresolved|duplicate)\b|cannot\s+open",
                           link_log, re.I)
    if diagnostic:
        raise AssertionError(f"{profile_name}/{case_name}: linker diagnostic {diagnostic.group(0)!r}: {link_log}")
    run_log = run_path.read_text(encoding="latin1").replace("\r\n", "\n").replace("\r", "\n").strip("\n")
    actual_lines = run_log.split("\n") if run_log else []
    if actual_lines != spec["expected"]:
        raise AssertionError(f"{profile_name}/{case_name}: RUN.LOG {actual_lines!r}, expected {spec['expected']!r}")
    map_text = map_path.read_text(encoding="latin1")
    map_rows = parse_map(map_text)
    slot = find_map_symbol(map_rows, "_fd_50F6_46D2")
    slot_linear = slot["segment"] * 16 + slot["offset"]
    image, relocations, header_bytes = parse_mz(exe_path.read_bytes())
    on_disk_offset = header_bytes + slot_linear
    if on_disk_offset + 4 > exe_path.stat().st_size:
        raise AssertionError(f"{profile_name}/{case_name}: mapped slot is not present in the MZ file image")
    disk_bytes = exe_path.read_bytes()[on_disk_offset:on_disk_offset + 4]
    startup_observation = {"map_symbol": slot, "load_image_linear": slot_linear,
                           "mz_header_bytes": header_bytes, "mz_file_offset": on_disk_offset,
                           "on_disk_bytes_hex": disk_bytes.hex(),
                           "relocation_overlaps_slot": has_relocation_overlap(relocations, slot_linear, 4)}
    if case_name in ("typedroot", "movedtypedroot"):
        if disk_bytes != b"\0\0\0\0" or startup_observation["relocation_overlaps_slot"]:
            raise AssertionError(f"{profile_name}/{case_name}: expected four unrelocated on-disk zero bytes: {startup_observation}")
        startup_observation["passed"] = True
    if case_name == "nonzeroinit":
        segment_relocations = [row for row in relocations if row["linear"] == slot_linear + 2]
        if len(segment_relocations) != 1:
            raise AssertionError(f"{profile_name}/nonzeroinit: initializer lacks one segment-word MZ relocation")
        fixture_master = find_map_symbol(map_rows, "_fixtureMaster")
        disk_offset_word = struct.unpack_from("<H", image, slot_linear)[0]
        if disk_offset_word != fixture_master["offset"]:
            raise AssertionError(f"{profile_name}/nonzeroinit: far-pointer offset initializer does not target fixtureMaster")
        startup_observation["fixtureMaster_map"] = fixture_master
        startup_observation["disk_pointer_offset_word"] = disk_offset_word
        startup_observation["segment_word_relocation"] = segment_relocations[0]
        startup_observation["passed"] = True
    if case_name == "nonzeroinit" and not validate_initializer_object(fixture_objects["INIT"]):
        raise AssertionError("INIT object initializer fixup check failed")
    result = {"link_profile": profile_name, "case": case_name, "ordered_objects": ordered_names,
             "expected_run_log": spec["expected"], "actual_run_log": actual_lines,
             "dosbox_return_code_observed_only": proc.returncode,
             "run_log_is_observation": True, "link_map_slot": slot,
             "slot_startup_check": startup_observation,
             "mz_relocation_entries": relocations,
             "files": [pin(case_dir / name) for name in (
                 "PROBE.LNK", "RTLINK.CFG", "RUN.BAT", "dosbox.conf", "LINK.LOG", "RUN.LOG",
                 "PROBE.MAP", "PROBE.EXE", "DOSBOX.LOG", *[f"{name}.OBJ" for name in ordered_names],
                 *library_names)],
             "tool_tree": str(tools_dir), "passed": True}
    print(f"{profile_name} {case_name}: {actual_lines}", flush=True)
    return result


def pin_toolchain(tc: dict, out: Path) -> tuple[dict, dict, list[dict], dict]:
    compiler_profile = compiler.verify_profile(FIXTURE_PROFILE)
    compiler_runner = tc["runners"][compiler_profile["runner"]]
    tool_pins = [pin(ROOT / "layout" / "toolchain.json"), pin(ROOT / "tools" / "compiler.py"),
                 pin(Path(compiler_runner["path"]))]
    for name, digest in compiler_profile["files"].items():
        path = Path(compiler_profile["directory"]) / name
        item = pin(path)
        if item["sha256"] != digest:
            raise ValueError(f"MSC tool changed after profile verification: {path}")
        tool_pins.append(item)
    if pin(Path(compiler_runner["path"]))["sha256"] != compiler_runner["sha256"]:
        raise ValueError("Current DOSBox-X runner hash differs from the pinned profile")
    linkers = {}
    for profile_name in LINK_PROFILES:
        definition = tc["linkers"][profile_name]
        tools_dir = compiler.pinned_tree(definition)
        runner = tc["runners"][definition["runner"]]
        pins = []
        for name, digest in definition["files"].items():
            source = Path(definition["directory"]) / name
            staged = tools_dir / name
            source_pin = pin(source)
            staged_pin = pin(staged)
            if source_pin["sha256"] != digest or staged_pin["sha256"] != digest:
                raise ValueError(f"{profile_name} pinned linker file changed: {name}")
            pins.extend((source_pin, staged_pin))
        runner_pin = pin(Path(runner["path"]))
        if runner_pin["sha256"] != runner["sha256"]:
            raise ValueError(f"{profile_name} runner hash differs from current toolchain pin")
        pins.append(runner_pin)
        linkers[profile_name] = {"definition": definition, "runner": runner,
                                 "tools_dir": tools_dir, "pins": pins}
        tool_pins.extend(pins)
    return compiler_profile, compiler_runner, tool_pins, linkers


def pin_runtime_libraries(program: dict) -> dict:
    libs = {row["name"].casefold(): row for row in program.get("dos", {}).get("runtime_libraries", [])}
    result = {}
    for name in ("llibcr.lib", "libh.lib"):
        row = libs.get(name)
        if row is None:
            raise ValueError(f"Current program inventory has no runtime library {name}")
        path = Path(row["path"])
        raw = path.read_bytes()
        if len(raw) != row["size"] or sha(raw) != row["sha256"]:
            raise ValueError(f"Current runtime library pin differs: {path}")
        result[name] = {"row": row, "path": path, "bytes": raw, "pin": pin(path, raw)}
    return result


def slot_inventory_context(program: dict, source_raw: bytes, source_text: str) -> dict:
    key = "source-owned:icon-handle-cell-view"
    rows = [row for row in program.get("modules", []) if row.get("key") == key]
    if len(rows) != 1:
        raise ValueError("Current program inventory must contain exactly one canonical icon Handle slot TU")
    row = rows[0]
    if row.get("source") != "src/state/icon-handle-cell-view.c" or row.get("source_sha256") != sha(source_raw):
        raise ValueError("Canonical slot TU does not match its current program inventory source pin")
    if re.sub(r"/\*.*?\*/|//[^\n]*", "", source_text, flags=re.S).strip() != "char far * far * far fd_50F6_46D2;":
        raise ValueError("Canonical storage TU is not exactly the admitted single four-byte Handle slot")
    expected_contract = {
        "status": "PASS", "data_only": True, "code_bytes": 0, "live_initialized_bytes": 0,
        "communals": [{"name": "_fd_50F6_46D2", "kind": "far", "length": 4,
                       "count": 4, "element_size": 1}],
        "publics": [], "fixups": [],
    }
    if row.get("storage_contract") != expected_contract:
        raise ValueError("Current program inventory storage contract is not the reviewed four-byte slot")
    if row.get("profile") != "msc600ax" or row.get("flags") != ["/AL", "/Os", "/Gs"]:
        raise ValueError("Canonical slot TU must retain its pinned MSC 6.00AX /AL /Os /Gs profile")
    return row


def recheck_input_pins(value) -> int:
    pins = []

    def collect(item):
        if isinstance(item, dict):
            if {"path", "size", "sha256"} <= item.keys():
                pins.append(item)
                return
            for child in item.values():
                collect(child)
        elif isinstance(item, list):
            for child in item:
                collect(child)

    collect(value)
    for item in pins:
        path = Path(item["path"])
        if not path.is_absolute():
            path = ROOT / path
        raw = path.read_bytes()
        if len(raw) != item["size"] or sha(raw) != item["sha256"]:
            raise RuntimeError(f"Current input changed during replay: {item['path']}")
    return len(pins)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", help="Fresh absent output directory strictly below repository build/")
    args = parser.parse_args(argv)
    if not __debug__:
        raise RuntimeError("Proof replay requires ordinary Python assertion checks; do not use -O")
    out = select_output(args.out)
    compiler.WORK = out / "cc"
    compiler.WORK.mkdir(parents=True, exist_ok=True)

    manifest_path = ROOT / "layout" / "manifest.json"
    program_path = ROOT / "src" / "program.json"
    manifest_raw = manifest_path.read_bytes()
    program_raw = program_path.read_bytes()
    manifest = json.loads(manifest_raw.decode("utf-8"))
    program = json.loads(program_raw.decode("utf-8"))
    source_raw, source_text = read_source(MODULE_SOURCE)
    module_row, definitions = module_source_context(manifest, source_raw, source_text)
    storage_path = ROOT / "src" / "state" / "icon-handle-cell-view.c"
    if not storage_path.is_file():
        raise ValueError("Current canonical icon Handle storage TU is required")
    storage_raw, storage_text = read_source(storage_path)
    slot_row = slot_inventory_context(program, storage_raw, storage_text)

    tc = compiler.toolchain()
    compiler_profile, compiler_runner, tool_pins, linker_tools = pin_toolchain(tc, out)
    runtime_libraries = pin_runtime_libraries(program)
    library_pins = [item["pin"] for item in runtime_libraries.values()]
    fixture_pins = [pin(HERE / "fixture-sources" / name)
                     for name in sorted(EXPECTED_FIXTURE_SHA256)]
    for item in fixture_pins:
        expected = EXPECTED_FIXTURE_SHA256[Path(item["path"]).name]
        if item["sha256"] != expected:
            raise ValueError(f"Fixture package source pin differs: {item['path']}")

    source_path = write_bytes(out / "sources" / "current" / "m208F.c", source_raw)
    current_inputs = {
        "manifest": pin(manifest_path, manifest_raw), "program": pin(program_path, program_raw),
        "m208F": pin(MODULE_SOURCE, source_raw), "canonical_slot_source": pin(storage_path, storage_raw),
        "runner": pin(Path(__file__)), "fixture_sources": fixture_pins,
        "repository_tools": [pin(ROOT / path) for path in (
            "tools/context.py", "tools/search.py", "tools/modules.py", "tools/compiler.py", "tools/omf.py",
            "tools/match.py", "tools/exe.py", "tools/functions.py", "tools/symbols.py",
            "dos/build.py")],
        "historical_validation_inputs": [pin(path) for path in (
            ROOT / "assets" / "SIMANT.EXE", ROOT / "layout" / "oracle.lock.json",
            ROOT / "layout" / "symbols.json", ROOT / "layout" / "functions.json",
            ROOT / "build" / "inventory" / "functions.json",
            ROOT / "evidence" / "cross_version" / "simantw_correspondence.json",
            *(ROOT / "build" / "search" / name / "best.json" for name in HELPERS),
        ) if path.is_file()],
        "toolchain_pins": tool_pins, "runtime_libraries": library_pins,
        "staged_m208F_source": pin(source_path),
    }
    original = exe.load()
    slot_at = 0x50F6 * 16 + 0x46D2
    slot_bytes = original.read("S27", slot_at, 4)
    overlaps = [at for at in original.reloc_sites("S27")
                if max(at, slot_at) < min(at + 2, slot_at + 4)]
    if slot_bytes != b"\0" * 4 or overlaps:
        raise AssertionError("Original slot must contain four zero bytes without relocation overlap")
    original_slot = {"segment": "50F6", "offset": "46D2", "byte_count": 4,
                     "zero_representation": True, "relocation_overlap_count": len(overlaps),
                     "oracle_sha256": original.sha256,
                     "scope": "Loaded file representation; no game activation, referent or permanent-zero proof."}
    input_path = write_json(out / "input-pins.json", current_inputs)

    consumers = run_consumer_reviews(out, manifest, module_row, source_text, out / "search-output")
    provider_results = compile_provider_shapes(out, storage_path, storage_text, slot_row)
    fixture_results, fixture_objects = compile_fixture_sources(out, storage_path, storage_text)
    init_check = validate_initializer_object(fixture_objects["INIT"])

    linked_runs = []
    for profile_name in LINK_PROFILES:
        link_tool = linker_tools[profile_name]
        for case_name, spec in FIXTURE_CASES.items():
            linked_runs.append(link_fixture(out, profile_name, case_name, spec, fixture_objects,
                                            link_tool["definition"], link_tool["runner"],
                                            link_tool["tools_dir"], runtime_libraries))
    by_profile_case = {(row["link_profile"], row["case"]): row for row in linked_runs}
    moved_pairs = {}
    for profile_name in LINK_PROFILES:
        typed = by_profile_case[(profile_name, "typedroot")]["link_map_slot"]
        moved = by_profile_case[(profile_name, "movedtypedroot")]["link_map_slot"]
        if typed == moved:
            raise AssertionError(f"{profile_name}: prepended SHIFT contribution did not move the mapped slot")
        moved_pairs[profile_name] = {"typedroot": typed, "movedtypedroot": moved, "changed": True}

    input_recheck_count = recheck_input_pins(current_inputs)

    report = {
        "schema": "simant-icon-handle-minimum-slot-current-source-replay-v1",
        "scope": "Current whole root:208F source and extent, a natural four-byte mutable far Handle slot, and stock-CRT startup/pointer controls. This proves the minimum slot view and initial zero representation only. It leaves computed aliases, activation, historical maximal extent, defining TU, physical aliases, and game cell/payload lifetime unresolved.",
        "output_directory": str(out),
        "original_executable_run": False,
        "original_immutable_image_read": True,
        "original_image_read_purpose": "Current context.py and modules.verify_module historical validation only; the game executable is never run by this replay.",
        "canonical_or_evidence_files_written": False,
        "compiler_profile": {"name": FIXTURE_PROFILE, "definition": compiler_profile,
                             "runner": compiler_runner},
        "source_context": {"module_key": MODULE_KEY, "source": pin(MODULE_SOURCE, source_raw),
                           "source_definitions_in_original_order": definitions,
                           "claim_count": len(module_row["claims"]), "extent": module_row["extent"],
                           "canonical_slot_source": current_inputs["canonical_slot_source"],
                           "canonical_storage_contract": slot_row["storage_contract"],
                           "context_packets": consumers["context_packets"]},
        "current_input_pins": current_inputs,
        "input_pin_file": pin(input_path),
        "original_slot_view": original_slot,
        "whole_source_consumer_controls": consumers["variants"],
        "provider_shape_controls": provider_results,
        "fixture_source_compiles": fixture_results,
        "init_object_pointer_fixup_control": init_check,
        "runtime_libraries": library_pins,
        "linker_status": {name: tc["linkers"][name]["status"] for name in LINK_PROFILES},
        "stock_crt_runs": linked_runs,
        "typed_root_map_moves": moved_pairs,
        "current_inputs_rechecked_after_runs": True,
        "current_input_pin_count_rechecked": input_recheck_count,
        "all_required_checks_pass": True,
    }
    receipt = write_json(out / "receipt.json", report)
    summary = {
        "schema": "simant-icon-handle-minimum-slot-current-source-replay-summary-v1",
        "all_required_checks_pass": True,
        "reproduce": "python evidence/canonical/icon-handle-view/replay.py --out build/proofs/icon-handle-view-run",
        "full_receipt": pin(receipt),
        "module_cases": {case: {"exact": row["verification"]["exact"],
                                 "extent_exact": row["verification"].get("extent", {}).get("exact"),
                                 "code_segment_length": row["control_checks"]["code_segment_length"],
                                 "failed_claims": sorted(name for name, value in row["verification"]["claims"].items()
                                                          if not value.get("exact")),
                                 "search_status": {helper: value["status"] for helper, value in row["search"].items()}}
                         for case, row in consumers["variants"].items()},
        "provider_communal_lengths": {case: row["expected_communal_length"] for case, row in provider_results.items()},
        "runtime_run_logs": [{"link_profile": row["link_profile"], "case": row["case"],
                              "actual_run_log": row["actual_run_log"], "mapped_slot": row["link_map_slot"],
                              "passed": row["passed"]} for row in linked_runs],
        "typed_root_map_moves": moved_pairs,
    }
    write_json(out / "summary.json", summary)
    print(f"Receipt: {receipt}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, AssertionError, subprocess.SubprocessError) as error:
        print(f"Icon handle replay failed: {error}", file=sys.stderr)
        raise SystemExit(1)
