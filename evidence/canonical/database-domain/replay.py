#!/usr/bin/env python3
"""Static/corpus proof and negative controls for the DOS database-slot gates.

This permanent probe never builds or runs the whole game. It checks the active
canonical inventory, lexes every listed C/ASM source for relevant identifiers,
uses the repository C AST to classify calls/declarations, verifies the pinned
resource corpus, and exercises source/domain rejection controls in memory.
"""
from __future__ import annotations

import hashlib
import argparse
import json
import re
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'src/program.json').is_file())
sys.path.insert(0, str(ROOT / "tools"))
sys.dont_write_bytecode = True
if not __debug__:
    raise RuntimeError('Run proof checks without Python -O')
import csrc  # noqa: E402
import behavior as b
import exe
import functions
import types
import importlib.util

TARGETS = (
    "main",
    "db_SetDataBase",
    "IBMInitStuff",
    "f_205F_0004",
    "OpenDB",
    "GetFreeHandle",
    "db_CloseDataBase",
    "CloseDB", "OpenIndex", "CreateIndex", "CloseIndex", "DBRecall", "FindIndex",
)

EXPECTED_CALLERS = {
    "main": {},
    "db_SetDataBase": {"IBMInitStuff": 3, "main": 1, "f_205F_0004": 1},
    "IBMInitStuff": {"main": 1},
    "f_205F_0004": {"IBMInitStuff": 1},
    "OpenDB": {"db_SetDataBase": 1},
    "GetFreeHandle": {"OpenDB": 1},
    "db_CloseDataBase": {},
    "CloseDB": {"db_CloseDataBase": 1},
    "OpenIndex": {"OpenDB": 1}, "CreateIndex": {"OpenDB": 1},
    "CloseIndex": {"CloseDB": 1}, "DBRecall": {"db_LoadObject": 1},
    "FindIndex": {"DBRecall": 1},
}

EXPECTED_DECLARATIONS = {
    "main": {("src/root/m15F8.c", "definition")},
    "db_SetDataBase": {
        ("src/S20/m39F1.c", "prototype"),
        ("src/root/m15F8.c", "prototype"),
        ("src/root/m205F.c", "prototype"),
        ("src/root/m1A53.c", "definition"),
    },
    "IBMInitStuff": {
        ("src/root/m15F8.c", "prototype"),
        ("src/S20/m39F1.c", "definition"),
    },
    "f_205F_0004": {
        ("src/S20/m39F1.c", "prototype"),
        ("src/root/m205F.c", "definition"),
    },
    "OpenDB": {
        ("src/root/m1A53.c", "prototype"),
        ("src/root/m1A28.c", "definition"),
    },
    "GetFreeHandle": {
        ("src/root/m1A28.c", "prototype"),
        ("src/root/m1A28.c", "definition"),
    },
    "db_CloseDataBase": {("src/root/m1A53.c", "definition")},
    "CloseDB": {("src/root/m1A53.c", "prototype"), ("src/root/m1A28.c", "definition")},
    "OpenIndex": {("src/root/m1A28.c", "prototype"), ("src/root/m1986.c", "definition")},
    "CreateIndex": {("src/root/m1A28.c", "prototype"), ("src/root/m1986.c", "definition")},
    "CloseIndex": {("src/root/m1A28.c", "prototype"), ("src/root/m1986.c", "definition")},
    "DBRecall": {("src/root/m1A53.c", "prototype"), ("src/root/m19A9.c", "definition")},
    "FindIndex": {("src/root/m19A9.c", "prototype"), ("src/root/m1986.c", "definition")},
}

SOURCE_PINS = {
    'src/root/m00F8.c': '4ee148ec616e199f61b671df89da8a21f1789c4177d3dbc7b76a478acb98184a',
    'src/root/m1A96.c': 'c57124b9d75ea77eb30158c09a71550862cf7081ceed625a2550a26a262bfdfa',
    'src/S15/m384C.c': '7ed6c428f141619affc175e550142bdd8810b217fa0564dd32099d00e22f9172',
    'src/S20/m39F1.c': '547996c143a5f2a0833e585732e5a22ebaa65b350b5392f847f64419c45a35f3',
    'src/root/m15F8.c': 'd6d4daddab943ee3436ca0e9c8dbc866a9d67659f7448f3c307f858abe06b70a',
    'src/root/m205F.c': '225326bdd127dd3825035ae0fe8434e6677c0ee81203fee2e16bac0cf90fffc6',
    'src/root/m1A53.c': '6bb066ea34c3721c90956a5b7e8849cb3c5916628a842c2684a8c0137154b698',
    'src/root/m1A28.c': '5db49039ef64717680153a4b9445554b58ab2abf8a3c3fd9d67e6573af58a740',
    'src/root/m1986.c': '47f058da6d58a4aca3a1c8485ef2c927f53cea58bca9c3a892642b2820361bff',
    'src/root/m19A9.c': '552ca373a3a3721885915acd0a95e2126b8405b0c555f02d1833381331cda523',
    'src/root/m1B28.c': '9e1c31226eae71d8ab1cc1e2de68bfd7840ba678b02dd72a4ba7757e25543343',
    'src/S09/m35F5.c': '028e1575990d5d45233f9102a0d2a060810349bd2f1297182c4af435ecbe912a',
    'src/state/database-record-state.c': '6af09ce9166c8af6114e95a374c791e9d01056c3209de0d6cd1b5006401c022a',
}

DATA_USERS = {
    'db_handles': {'src/root/m1A53.c', 'src/state/database-record-state.c'},
    'fd_50F6_3958': {'src/root/m1A28.c', 'src/root/m1986.c', 'src/root/m19A9.c',
                    'src/state/database-record-state.c'},
}


class Reject(RuntimeError):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_pin(rel: str) -> dict:
    data = (ROOT / rel).read_bytes()
    return {"path": rel, "size": len(data), "sha256": sha(data)}


def line_col(text: str, offset: int) -> tuple[int, int]:
    line = text.count("\n", 0, offset) + 1
    prev = text.rfind("\n", 0, offset)
    return line, offset - prev


def is_prototype_line(line: str, name: str) -> bool:
    # All allowed declarations are ordinary one-line C function prototypes.
    return bool(
        re.fullmatch(
            rf"\s*(?:extern\s+)?[^;{{}}]*\b{re.escape(name)}\s*\([^;{{}}]*\)\s*;\s*",
            line,
        )
    )


def tokens_in_c(text: str, targets: set[str]):
    for tok in csrc.tokenize(text):
        if tok.kind == "id" and tok.text in targets:
            yield tok.text, tok.s, tok.e
        elif tok.kind == "pp":
            found = [name for name in targets if re.search(rf"\b{re.escape(name)}\b", tok.text)]
            if found:
                raise Reject(f"target identifier in preprocessor directive: {found}")


def tokens_in_asm(text: str, targets: set[str]):
    # MASM comments and quoted strings are not executable identifiers.
    for line_no, line in enumerate(text.splitlines(), 1):
        code = line.split(";", 1)[0]
        code = re.sub(r'"(?:""|[^"])*"', "", code)
        for match in re.finditer(r"[A-Za-z_][A-Za-z0-9_]*", code):
            spelling = match.group(0)
            name = spelling[1:] if spelling.startswith('_') else spelling
            if name in targets:
                yield name, line_no, match.start() + 1


def scan_identifiers(source_texts: dict[str, str]) -> dict:
    target_set = set(TARGETS)
    uses = {name: [] for name in TARGETS}
    calls = {name: [] for name in TARGETS}
    declarations = {name: [] for name in TARGETS}
    loop_calls = []

    for rel, text in sorted(source_texts.items()):
        if rel.lower().endswith(".asm"):
            for name, line, col in tokens_in_asm(text, target_set):
                raise Reject(f'unreviewed database-chain assembly reference {name} at {rel}:{line}:{col}')
            continue
        if not rel.lower().endswith((".c", ".h")):
            continue

        file_tokens = list(tokens_in_c(text, target_set))
        if not file_tokens:
            continue
        source = csrc.Source(text)
        functions = source.functions()
        call_positions = {}
        calls_by_pos = {}
        for fn in functions:
            for node in csrc.walk(fn.body):
                if isinstance(node, csrc.Call) and isinstance(node.f, csrc.Id) and node.f.name in target_set:
                    call_positions[node.f.s] = (node.f.name, fn.name, node)
                    calls_by_pos[node.f.s] = node
                    active_loops = [
                        loop for loop in csrc.walk(fn.body)
                        if type(loop).__name__ in {"For", "While", "DoWhile"}
                        and loop.s <= node.s < loop.e
                    ]
                    if active_loops:
                        loop_calls.append({"path": rel, "function": fn.name, "target": node.f.name})

        for name, start, end in file_tokens:
            line, col = line_col(text, start)
            if start in call_positions:
                _, caller, node = call_positions[start]
                item = {"path": rel, "line": line, "column": col, "caller": caller}
                calls[name].append(item)
                uses[name].append({**item, "kind": "direct-call"})
                continue

            definition = next(
                (
                    fn for fn in functions
                    if fn.name == name and fn.head_s <= start < fn.params_e
                ),
                None,
            )
            if definition is not None:
                item = {"path": rel, "line": line, "column": col, "kind": "definition"}
                declarations[name].append((rel, "definition"))
                uses[name].append(item)
                continue

            source_line = text.splitlines()[line - 1]
            if is_prototype_line(source_line, name):
                declarations[name].append((rel, "prototype"))
                uses[name].append({"path": rel, "line": line, "column": col, "kind": "prototype"})
                continue

            raise Reject(
                f"unclassified/address-taken/non-direct use {name} at {rel}:{line}:{col}: "
                f"{source_line.strip()}"
            )

    for name in TARGETS:
        got_callers = Counter(item["caller"] for item in calls[name])
        if dict(got_callers) != EXPECTED_CALLERS[name]:
            raise Reject(f"caller set for {name}: got {dict(got_callers)}, expected {EXPECTED_CALLERS[name]}")
        got_decls = Counter(declarations[name])
        want_decls = Counter(EXPECTED_DECLARATIONS[name])
        if got_decls != want_decls:
            raise Reject(f"declarations for {name}: got {dict(got_decls)}, expected {dict(want_decls)}")
    expected_loops = [
        {'path': 'src/root/m1A53.c', 'function': 'db_LoadObject', 'target': 'DBRecall'},
        {'path': 'src/root/m1A53.c', 'function': 'db_CloseDataBase', 'target': 'CloseDB'},
    ]
    if loop_calls != expected_loops:
        raise Reject(f"database-chain loop set changed: {loop_calls}")

    return {
        "uses": uses,
        "callers": {name: dict(Counter(x["caller"] for x in calls[name])) for name in TARGETS},
        "database_chain_calls_in_loops": loop_calls,
    }


def inventory_and_scan() -> tuple[dict, dict[str, str]]:
    program_bytes = (ROOT / "src/program.json").read_bytes()
    program = json.loads(program_bytes)
    modules = program["modules"]
    sources = [m["source"] for m in modules]
    if len(sources) != len(set(sources)):
        raise Reject("duplicate source paths in src/program.json")

    pins = []
    source_texts = {}
    module_paths = set()
    for module in modules:
        rel = module["source"]
        module_paths.add(rel.replace("\\", "/"))
        data = (ROOT / rel).read_bytes()
        digest = sha(data)
        if digest != module["source_sha256"]:
            raise Reject(f"active source hash mismatch: {rel}")
        if rel in SOURCE_PINS and digest != SOURCE_PINS[rel]:
            raise Reject(f"reviewed source pin differs: {rel}")
        pins.append({"path": rel, "size": len(data), "sha256": digest})
        try:
            source_texts[rel.replace("\\", "/")] = data.decode("utf-8")
        except UnicodeDecodeError:
            # Original assembly bytes are ASCII in this corpus; a binary source is unexpected.
            raise Reject(f"non-UTF8 canonical source: {rel}")

    discovered = {
        p.relative_to(ROOT).as_posix()
        for p in (ROOT / "src").rglob("*")
        if p.is_file() and p.suffix.lower() in {".c", ".asm"}
    }
    canonical_c_asm = {p for p in module_paths if p.lower().endswith((".c", ".asm"))}
    if discovered != canonical_c_asm:
        raise Reject(
            f"src C/ASM inventory mismatch; unlisted={sorted(discovered-canonical_c_asm)}, "
            f"missing={sorted(canonical_c_asm-discovered)}"
        )

    program_pin = {"path": "src/program.json", "size": len(program_bytes), "sha256": sha(program_bytes)}
    if not SOURCE_PINS.keys() <= source_texts.keys():
        raise Reject('reviewed database source missing from inventory')
    scan = scan_identifiers(source_texts)
    inventory = {
        "program_json": program_pin,
        "module_count": len(modules),
        "all_module_source_hashes_match_inventory": True,
        "discovered_c_asm_files_equal_program_inventory": True,
        "identifier_scan_source_count": len(source_texts),
        "all_canonical_source_pin_index_sha256": sha(json.dumps(sorted(pins, key=lambda x: x['path']), sort_keys=True).encode()),
        "reviewed_source_pins": [p for p in pins if p['path'] in SOURCE_PINS],
        "identifier_scan": scan,
    }
    return inventory, source_texts


def c_function(text: str, name: str):
    found = [f for f in csrc.Source(text).functions() if f.name == name]
    if len(found) != 1:
        raise Reject(f"expected exactly one {name} definition, got {len(found)}")
    return found[0]


def counter_and_owner_proof(source_texts: dict[str, str]) -> dict:
    path = "src/root/m1A53.c"
    text = source_texts[path]
    set_fn = c_function(text, "db_SetDataBase")
    close_fn = c_function(text, "db_CloseDataBase")
    writes = []
    counter_tokens = []
    owner_uses = []
    for rel, source_unit in sorted(source_texts.items()):
        if rel.lower().endswith(".asm"):
            for line_no, line_text in enumerate(source_unit.splitlines(), 1):
                if re.search(r"\bdb_numOfHandles\b", line_text.split(";", 1)[0]):
                    raise Reject(f"db_numOfHandles identifier in assembly at {rel}:{line_no}")
            continue
        if not rel.lower().endswith((".c", ".h")):
            continue
        matching = [tok for tok in csrc.tokenize(source_unit) if tok.kind == "id" and tok.text == "db_numOfHandles"]
        if matching and rel != path:
            raise Reject(f"db_numOfHandles appears outside its sole canonical owner TU: {rel}")
        if rel == path:
            for tok in matching:
                line, col = line_col(source_unit, tok.s)
                owner_uses.append({"path": rel, "line": line, "column": col})
            counter_tokens = [(tok.s, *line_col(source_unit, tok.s)) for tok in matching]
    for fn in csrc.Source(text).functions():
        for node in csrc.walk(fn.body):
            if isinstance(node, csrc.Post) and isinstance(node.x, csrc.Id) and node.x.name == "db_numOfHandles":
                line, col = line_col(text, node.s)
                writes.append({"function": fn.name, "kind": f"post{node.op}", "line": line, "column": col})
            elif isinstance(node, csrc.Unary) and node.op in {"++", "--"} and isinstance(node.x, csrc.Id) and node.x.name == "db_numOfHandles":
                line, col = line_col(text, node.s)
                writes.append({"function": fn.name, "kind": f"pre{node.op}", "line": line, "column": col})
            elif isinstance(node, csrc.Assign) and isinstance(node.l, csrc.Id) and node.l.name == "db_numOfHandles":
                line, col = line_col(text, node.s)
                writes.append({"function": fn.name, "kind": f"assignment{node.op}", "line": line, "column": col})
            elif isinstance(node, csrc.Unary) and node.op == "&" and isinstance(node.x, csrc.Id) and node.x.name == "db_numOfHandles":
                line, col = line_col(text, node.s)
                writes.append({"function": fn.name, "kind": "address-taken", "line": line, "column": col})
    expected_writes = [
        {"function": "db_SetDataBase", "kind": "post++", "line": 52},
        {"function": "db_CloseDataBase", "kind": "pre--", "line": 162},
    ]
    compact_writes = [{k: v for k, v in x.items() if k != "column"} for x in sorted(writes, key=lambda x: (x["line"], x["column"]))]
    if compact_writes != expected_writes:
        raise Reject(f"db_numOfHandles write set changed: {writes}")
    if len(counter_tokens) != 13:
        raise Reject(f"unexpected db_numOfHandles identifier count in its owner TU: {len(counter_tokens)}")
    if not re.search(r"\bint\s+db_numOfHandles\s*=\s*0\s*;", text):
        raise Reject("explicit source initialization of db_numOfHandles to zero missing")

    state_path = "src/state/database-record-state.c"
    state_text = source_texts[state_path]
    if not re.search(r"\bOpenDBRec\s+far\s+fd_50F6_3958\s*\[\s*4\s*\]\s*;", state_text):
        raise Reject("source-owned four-record array declaration changed")
    if not re.search(r"\bint\s+far\s+db_handles\s*\[\s*4\s*\]\s*;", state_text):
        raise Reject("source-owned four-handle array declaration changed")
    for name in ("fd_50F6_3958", "db_handles"):
        if re.search(rf"\b{name}\s*\[[^]]+\]\s*=", state_text):
            raise Reject(f"source owner for {name} now has an explicit nonzero initializer")

    program = json.loads((ROOT / "src/program.json").read_text(encoding="utf-8"))
    state_inv = next((m for m in program["modules"] if m["source"] == state_path), None)
    contract = (state_inv or {}).get("storage_contract", {})
    communals = {x["name"]: x for x in contract.get("communals", [])}
    if contract.get("status") != "PASS" or contract.get("live_initialized_bytes") != 0:
        raise Reject("source-owned storage contract no longer confirms data-only, no live initialized bytes")
    if communals.get("_fd_50F6_3958", {}).get("count") != 4 or communals.get("_db_handles", {}).get("count") != 4:
        raise Reject("source-owned storage contract no longer says both arrays have four elements")

    free_text = source_texts["src/root/m1A28.c"]
    if not re.search(r"static\s+int\s+s_394E\s*=\s*0\s*;", free_text):
        raise Reject("GetFreeHandle first-use flag lost its zero initializer")
    free_fn = c_function(free_text, "GetFreeHandle")
    free_body = free_text[free_fn.body.s:free_fn.body.e]
    if not re.search(r"for\s*\(\s*i\s*=\s*0\s*;\s*i\s*<\s*4\s*;\s*i\+\+\s*\)\s*fd_50F6_3958\s*\[\s*i\s*\]\.name\s*\[\s*0\s*\]\s*=\s*0\s*;", free_body):
        raise Reject("first GetFreeHandle pass no longer clears the four name[0] free markers")

    return {
        "counter_source_initializer": "db_numOfHandles = 0",
        "all_canonical_db_numOfHandles_uses": owner_uses,
        "counter_writes": expected_writes,
        "db_CloseDataBase_direct_callers": [],
        "source_owner": {
            "records": "OpenDBRec far fd_50F6_3958[4]",
            "handles": "int far db_handles[4]",
            "explicit_initializers": 0,
            "storage_contract": {
                "status": contract["status"],
                "data_only": contract.get("data_only"),
                "live_initialized_bytes": contract["live_initialized_bytes"],
                "record_elements": communals["_fd_50F6_3958"]["count"],
                "handle_elements": communals["_db_handles"]["count"],
            },
            "C_static_storage_zero_initialization": True,
            "free_marker_first_use_clear": "GetFreeHandle sets name[0]=0 for each of four slots when s_394E is initially zero",
        },
    }


def verify_resource_domain() -> dict:
    lock_path = "layout/oracle.lock.json"
    lock_bytes = (ROOT / lock_path).read_bytes()
    lock = json.loads(lock_bytes)
    locked = lock["inputs"]
    asset_names = {p.name.upper() for p in (ROOT / "assets").iterdir() if p.is_file()}
    locked_names = set(locked)
    if asset_names != locked_names:
        raise Reject(f"asset directory differs from pinned oracle inputs: missing={sorted(locked_names-asset_names)}, extra={sorted(asset_names-locked_names)}")

    checks = {}
    counts = {}
    for stem in ("SHARED", "HCEGANT", "SOUND"):
        for suffix in ("DAT", "NDX"):
            name = f"{stem}.{suffix}"
            pin = locked.get(name)
            if not pin:
                raise Reject(f"oracle lock lacks required package member {name}")
            data = (ROOT / "assets" / name).read_bytes()
            if len(data) != pin["size"] or sha(data) != pin["sha256"]:
                raise Reject(f"asset does not match oracle lock: {name}")
            checks[name] = {"size": len(data), "sha256": sha(data), "matches_oracle_lock": True}
        dat = (ROOT / "assets" / f"{stem}.DAT").read_bytes()
        ndx = (ROOT / "assets" / f"{stem}.NDX").read_bytes()
        if len(dat) < 14 or struct.unpack_from("<I", dat, 0)[0] != 0x12345678:
            raise Reject(f"bad {stem}.DAT 14-byte OpenDB header/magic")
        if len(ndx) < 20:
            raise Reject(f"short {stem}.NDX header")
        count = struct.unpack_from("<h", ndx, 0)[0]
        unread_trailer = len(ndx) - (20 + count * 8)
        # Shipped NDX files carry a 256-byte tail after the indexed rows; OpenIndex
        # reads only count*8, so this trailer does not become allocated index rows.
        if count < 0 or unread_trailer != 256:
            raise Reject(f"{stem}.NDX count/record length mismatch")
        keys = []
        for i in range(count):
            row = ndx[20 + i * 8:28 + i * 8]
            # On-disk IndexEntry: far pointer(4), signed id(2), kind(1), spare(1).
            object_id = struct.unpack_from("<h", row, 4)[0]
            kind = row[6]
            keys.append((kind, object_id))
        if keys != sorted(keys):
            raise Reject(f"{stem}.NDX keys do not satisfy FindIndex (kind,id) order")
        counts[stem] = {"ndx_rows": count, "ndx_bytes": len(ndx), "unread_trailer_bytes": unread_trailer, "dat_bytes": len(dat), "magic": "0x12345678", "keys_sorted_kind_then_id": True}

    optional = {"LANGUAGE.DAT", "LANGUAGE.NDX", "LRSHARE.DAT", "LRSHARE.NDX"}
    present_optional = sorted(asset_names & optional)
    if present_optional:
        raise Reject(f"optional language/lrshare resources unexpectedly in pinned corpus: {present_optional}")
    config = (ROOT / "assets/SIMANT.CFG").read_bytes()
    if config != b"Display Mode: V\r\nSound Mode: 6\r\n":
        raise Reject("SIMANT.CFG bytes changed from the pinned VGA default")
    if locked.get("SIMANT.CFG", {}).get("sha256") != sha(config):
        raise Reject("SIMANT.CFG does not match oracle lock")

    # Evidence gates scope cannot prove runtime argv or CWD contents. Those are explicit
    # preconditions below; command-line /d modes are separately bounded when language.dat
    # remains absent.
    return {
        "oracle_lock": {"path": lock_path, "size": len(lock_bytes), "sha256": sha(lock_bytes)},
        "asset_directory_equals_all_locked_inputs": True,
        "resource_pairs_match_lock_and_structure": checks,
        "resource_index_census": counts,
        "foreign_language_or_lrshare_members_in_pinned_assets": present_optional,
        "config": {"bytes": config.decode("ascii"), "mode_letter": "V", "ReadConfig_g_5A97": 8, "sound_mode": "6"},
        "external_cwd_or_supplied_resource_precondition": "No unmanifested language.dat or lrshare resource is present in the game's working/resource directory.",
    }


def domain_count(mode: int, language_present: bool) -> int:
    # IBMInitStuff conditionals plus its one f_205F_0004 call, followed by main's sound call.
    return 1 + int(mode in {2, 4}) + 1 + 1 + int(language_present)


def negative_controls(baseline_texts: dict[str, str]) -> list[dict]:
    results = []
    # Source control: inject two calls so the otherwise default VGA launch would make
    # five opens. This is an in-memory variant and does not touch canonical source.
    main_path = "src/root/m15F8.c"
    source = baseline_texts[main_path]
    needle = '    db_SetDataBase("sound");'
    if source.count(needle) != 1:
        raise Reject("cannot construct generated five-call negative control")
    mutant = source.replace(needle, '    db_SetDataBase("extra1");\n    db_SetDataBase("extra2");\n' + needle, 1)
    variant = dict(baseline_texts)
    variant[main_path] = mutant
    try:
        scan_identifiers(variant)
    except Reject as exc:
        results.append({"control": "generated_invalid5calls_source_variant", "expected": "reject", "observed": "rejected", "reason": str(exc)})
    else:
        raise Reject("generated five-call source variant unexpectedly passed")

    # Corpus-domain control: a valid foreign language package plus mode 2 (the lrshare
    # selector) reaches five syntactic acquisitions. Model only the path predicate.
    five = domain_count(mode=2, language_present=True)
    if five != 5:
        raise Reject(f"domain negative-control arithmetic changed: {five}")
    results.append({
        "control": "generated_external_language_plus_mode2_domain",
        "expected": "reject-outside-supported-scope",
        "observed": "rejected",
        "mode": 2,
        "foreign_language_resource_assumed_valid": True,
        "foreign_lrshare_resource_assumed_valid": True,
        "syntactic_open_count": five,
        "reason": "External language package plus a mode-2/4 override is outside the exact corpus gate and permits db_handles[4] if all prior opens return.",
    })

    # Inventory/caller control: a new translation unit with a direct caller must fail
    # the exact call graph even when the original canonical inventory remains unchanged.
    variant = dict(baseline_texts)
    variant["generated-extra-caller.c"] = (
        'void external_resource_owner(void) { db_SetDataBase("foreign"); }\n'
    )
    try:
        scan_identifiers(variant)
    except Reject as exc:
        results.append({"control": "generated_extra_caller", "expected": "reject", "observed": "rejected", "reason": str(exc)})
    else:
        raise Reject("generated extra caller unexpectedly passed")
    return results


def storage_use_census(texts):
    uses = {name: set() for name in DATA_USERS}
    for rel, text in texts.items():
        if rel.endswith('.asm'):
            for name, _, _ in tokens_in_asm(text, set(DATA_USERS)):
                uses[name].add(rel)
        else:
            for name, _, _ in tokens_in_c(text, set(DATA_USERS)):
                uses[name].add(rel)
    if uses != DATA_USERS:
        raise Reject('database storage consumer set changed: ' + str(uses))
    return {name: sorted(paths) for name, paths in uses.items()}


def first_flag_proof(texts):
    owner = 'src/root/m1A28.c'
    references = []
    for rel, text in texts.items():
        if rel.endswith('.asm'):
            for _, line, _ in tokens_in_asm(text, {'s_394E'}):
                raise Reject(f'first-use flag assembly reference at {rel}:{line}')
        else:
            for name, start, _ in tokens_in_c(text, {'s_394E'}):
                if rel != owner:
                    raise Reject('first-use flag reference outside owner: ' + rel)
                references.append(line_col(text, start)[0])
    if references != [39, 104, 105]:
        raise Reject('first-use flag consumer count/locations differ')
    if not re.search(r'static\s+int\s+s_394E\s*=\s*0\s*;', texts[owner]):
        raise Reject('first-use flag zero initializer differs')
    writes = []
    for fn in csrc.Source(texts[owner]).functions():
        for node in csrc.walk(fn.body):
            if isinstance(node, csrc.Assign) and isinstance(node.l, csrc.Id) and node.l.name == 's_394E':
                writes.append((fn.name, node.op, node.r.value if isinstance(node.r, csrc.Num) else None))
            if isinstance(node, csrc.Unary) and isinstance(node.x, csrc.Id) and node.x.name == 's_394E' and node.op in {'&', '++', '--'}:
                raise Reject('first-use flag escapes or has extra mutation')
            if isinstance(node, csrc.Post) and isinstance(node.x, csrc.Id) and node.x.name == 's_394E':
                raise Reject('first-use flag has post mutation')
    if writes != [('GetFreeHandle', '=', 1)]:
        raise Reject('first-use flag write set differs: ' + str(writes))
    return {'initializer': 0, 'sole_write': {'function': 'GetFreeHandle', 'value': 1},
            'owner': owner, 'source_reference_lines': references, 'address_taken': False}


def oracle_machine(name):
    image = exe.load()
    return b.Machine(types.SimpleNamespace(function=functions.get(name),
        vectors={exe.MANAGER_SEG * 16 + v.offset: v for v in image.vectors}))


def original_first_use_clear():
    result = []
    for initialized in [0, 1]:
        machine = oracle_machine('GetFreeHandle')
        flag = 0x55B30 + 0x394E
        counter = 0x55B30 + 0x39F4
        assert machine.word(flag) == 0 and machine.word(counter) == 0
        records = b.symbol_address('fd_50F6_3958')
        slots = bytearray([0xA7] * (4 * 124))
        for i in range(4):
            slots[i * 124] = ord('A') + i
        observation = machine.run(b.Case('first-use-flag-' + str(initialized),
            writes=[(flag, b.words(initialized)), (records, bytes(slots))],
            max_instructions=10000))
        expected = bytearray(slots)
        if not initialized:
            for i in range(4):
                expected[i * 124] = 0
        assert machine.read(records, len(slots)) == expected
        assert machine.word(flag) == 1
        assert observation['return'] == (-1 if initialized else 0)
        result.append({'incoming_flag': initialized, 'returned_slot': observation['return'],
            'name_markers_after': [expected[i * 124] for i in range(4)],
            'all_other_record_bytes_preserved': True})
    return {'original_counter_and_first_flag_initializers_zero': True, 'cases': result}


def save_table_proof(texts, raw=None):
    machine = oracle_machine('OpenDB')
    start = b.symbol_address('fd_4E4B_0000')
    if raw is None:
        raw = machine.read(start, 308 * 8)
    if len(raw) != 308 * 8:
        raise Reject('save table extent changed')
    initializer = texts['src/S09/m35F5.c'].split(
        'struct SaveRec far fd_4E4B_0000[308] = {', 1)[1].split('};', 1)[0]
    descriptors = re.findall(r'\{\s*(\d+),\s*(\d+),\s*\(void far \*\)(?:&(\w+)|\((\w+)\s*\+\s*(\d+)\))\s*\}', initializer)
    if len(descriptors) != 307 or not initializer.rstrip().endswith('{ 0, 0, 0 }'):
        raise Reject('save table source shape differs')
    protected = {
        'database counter/cache/closed state': (0x55B30 + 0x39F4, 8),
        'GetFreeHandle first-use flag': (0x55B30 + 0x394E, 2),
        'open records': (b.symbol_address('fd_50F6_3958'), 4 * 124),
        'database handles': (b.symbol_address('db_handles'), 4 * 2),
    }
    for i, (source_size, source_count, direct, arithmetic, offset) in enumerate(descriptors):
        size, count, off, seg = struct.unpack_from('<HHHH', raw, i * 8)
        at = seg * 16 + off
        bound = b.symbol(direct or arithmetic)
        if (size, count, off, seg) != (int(source_size), int(source_count), bound['off'] + int(offset or 0), bound['seg']):
            raise Reject('save table source/original descriptor differs: ' + str(i))
        if size * count > 0xFFFF or not size or not count or off + size * count > 0x10000:
            raise Reject('invalid/wrapping save descriptor: ' + str(i))
        end = at + size * count
        for name, (target, width) in protected.items():
            if at < target + width and target < end:
                raise Reject('save table reaches database lifetime state: ' + name)
    if raw[-8:] != bytes(8):
        raise Reject('save table terminator differs')
    return {'descriptors': 307, 'source_original_symbolic_descriptors_match': True,
            'protected_ranges': {n: {'linear': at, 'bytes': size} for n, (at, size) in protected.items()},
            'protected_ranges_intersected': 0,
            'descriptor_bytes_sha256': sha(raw),
            'scope': 'All successful S09 LoadGame read destinations and SaveGame read sources; no arbitrary corrupt save file/pointer-table claim.'}


def original_frontend_sequence():
    """Regress store-before-check at an explicit successful OpenDB boundary."""
    machine = oracle_machine('db_SetDataBase')
    counter = 0x55B30 + 0x39F4
    handles = b.symbol_address('db_handles')
    boundary_returns = [0, 1, 2, 3, -1]
    results = []
    def opened(cpu, args):
        index = cpu.word(counter)
        assert 0 <= index < len(boundary_returns)
        return boundary_returns[index]
    for i in range(5):
        case = b.Case('frontend-store-' + str(i), args=[0, 0x7000],
            writes=[] if i else [(counter, b.words(0)),
                (0x55B30 + 0x39F6, b.words(0, 0x7000)),
                (0x55B30 + 0x54F8, b.words(1)), (0x70000, b'guard-probe\0')],
            callbacks={'OpenDB': b.Callback(2, opened)}, max_instructions=10000)
        result = machine.run(case, preserve=i > 0)
        assert result['return'] == boundary_returns[i]
        assert machine.word(counter) == i + 1
        assert machine.word(handles + i * 2) == (boundary_returns[i] & 0xFFFF)
        results.append({'acquisition': i + 1, 'counter_after': i + 1,
            'slot_written': i, 'returned_db_handle': result['return'],
            'within_four_slot_owner': i < 4,
            'store_address': f'50F6:{0x3B50 + i * 2:04X}'})
    return {'scope': 'Original db_SetDataBase and genuine empty f_1B28_0068/Punt guard; OpenDB output is an explicit boundary, not an actual DOS open.',
            'cache_fixture': 'Existing nonnull cache table; its creation/lifetime is outside this caller-store check.',
            'supported_steps': results[:3], 'fourth_capacity_control': results[3],
            'fifth_returning_failure_negative': results[4]}


def original_recall_iteration():
    machine = oracle_machine('db_LoadObject')
    recalled = []
    def absent(cpu, args):
        recalled.append(args[0])
        return (0, 0)
    result = machine.run(b.Case('successful-three-slot-lookup-frontier', args=[99, 18],
        writes=[(0x55B30 + 0x39F4, b.words(3)),
                (b.symbol_address('db_handles'), b.words(0, 1, 2, 0x7777))],
        callbacks={'ch_LookUpId': b.Callback(4, lambda cpu, args: (0, 0)),
                   'DBRecall': b.Callback(5, absent),
                   'WinPrintf': b.Callback(4, lambda cpu, args: 0)},
        return_kind='farptr', max_instructions=10000))
    assert result['return'] == 0 and recalled == [0, 1, 2]
    return {'original_db_LoadObject_recall_handles': recalled,
            'unused_slot3_canary': '7777', 'unused_slot3_recalled': False,
            'scope': 'Real iteration with explicit cache-miss, DBRecall-miss, and diagnostic boundaries; no FindIndex correctness claim.'}


def additional_negative_controls(texts):
    cases = []
    for label, rel, suffix in [
        ('address_taken_acquisition', 'generated.c', 'void f(void) { void *p = &OpenDB; }'),
        ('mangled_asm_acquisition', 'generated.asm', 'call _OpenDB'),
        ('additional_record_consumer', 'generated.c', 'extern char fd_50F6_3958[1];'),
        ('main_reentry', 'generated.c', 'void f(void) { main(0, 0); }'),
    ]:
        variant = {**texts, rel: suffix}
        try:
            (storage_use_census if label == 'additional_record_consumer' else scan_identifiers)(variant)
        except Reject:
            cases.append({'control': label, 'observed': 'rejected'})
        else:
            raise Reject('negative control unexpectedly accepted: ' + label)
    variant = dict(texts)
    variant['src/root/m15F8.c'] = variant['src/root/m15F8.c'].replace(
        'db_SetDataBase("sound");', 'while (1) { db_SetDataBase("sound"); }')
    try:
        scan_identifiers(variant)
    except Reject:
        cases.append({'control': 'loop_repeated_acquisition', 'observed': 'rejected'})
    else:
        raise Reject('loop acquisition negative control unexpectedly accepted')
    variant = dict(texts)
    variant['src/root/m1A53.c'] = variant['src/root/m1A53.c'].replace(
        'handle = db_handles[db_numOfHandles++];',
        'handle = db_handles[db_numOfHandles++]; db_numOfHandles = 0;')
    try:
        counter_and_owner_proof(variant)
    except Reject:
        cases.append({'control': 'counter_reset_reacquisition', 'observed': 'rejected'})
    else:
        raise Reject('counter reset negative control unexpectedly accepted')
    variant = dict(texts)
    variant['src/root/m1A28.c'] = variant['src/root/m1A28.c'].replace(
        's_394E = 1;', 's_394E = 1; s_394E = 0;')
    try:
        first_flag_proof(variant)
    except Reject:
        cases.append({'control': 'first_flag_reset', 'observed': 'rejected'})
    else:
        raise Reject('first-use flag reset negative control unexpectedly accepted')
    variant = {**texts, 'generated.c': 'void f(void) { void *p = &s_394E; }'}
    try:
        first_flag_proof(variant)
    except Reject:
        cases.append({'control': 'first_flag_escape', 'observed': 'rejected'})
    else:
        raise Reject('first-use flag escape negative control unexpectedly accepted')
    raw = oracle_machine('OpenDB').read(b.symbol_address('fd_4E4B_0000'), 308 * 8)
    mutated = bytearray(raw)
    struct.pack_into('<HHHH', mutated, 0, 2, 1, 0x39F4, 0x55B3)
    try:
        save_table_proof(texts, mutated)
    except Reject:
        cases.append({'control': 'save_load_destination_mutation', 'observed': 'rejected'})
    else:
        raise Reject('save destination negative control unexpectedly accepted')
    return cases


def probe():
    inventory, texts = inventory_and_scan()
    resource = verify_resource_domain()
    counter = counter_and_owner_proof(texts)
    flag = first_flag_proof(texts)
    users = storage_use_census(texts)
    saves = save_table_proof(texts)
    frontend = original_frontend_sequence()
    first_use = original_first_use_clear()
    recalls = original_recall_iteration()
    spec = importlib.util.spec_from_file_location('database_error_prefix',
        ROOT / 'evidence/canonical/error-continuation/replay.py')
    error = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(error)
    error.verify_inputs()
    prefixes = [error.open_db_prefix(i) for i in range(5)]
    controls = negative_controls(texts) + additional_negative_controls(texts)
    repeat, _ = inventory_and_scan()
    if inventory != repeat or resource != verify_resource_domain():
        raise Reject('inputs changed during proof')
    return {'schema': 'simant-database-supported-domain-v1', 'status': 'PASS',
        'classification': 'SUPPORTED_DOMAIN',
        'domain_id': 'shipped-default-vga-successful-db-lifetime',
        'domain': ['Locked SHARED/HCEGANT/SOUND DAT/NDX and default SIMANT.CFG in the lookup directory',
            'No external language.dat/lrshare, display override, alternate display setup, or /s9',
            'Successful original file/header/index allocation/read and ordinary valid nominal state',
            'Ordinary boot, menus, object release/reload, valid save/load and shutdown'],
        'invariant': {'acquisitions_in_order': ['shared', 'hcegant', 'sound'],
            'maximum_acquisitions_per_main_lifetime': 3, 'db_numOfHandles_after_boot': 3,
            'record_and_frontend_slots': [0, 1, 2],
            'database_slot_release_or_reacquisition_callers': [],
            'minus_one_and_fifth_slot_accesses': 'Excluded within the explicit successful domain'},
        'canonical_inventory': inventory, 'counter_and_owner': counter,
        'first_use_flag_contract': flag, 'original_first_use_clear': first_use,
        'storage_consumer_census': users, 'save_load_destinations': saves,
        'resource_domain': resource, 'original_frontend': frontend,
        'original_lookup_iteration': recalls, 'original_OpenDB_prefixes': prefixes,
        'negative_controls': controls, 'implementation': file_pin('evidence/canonical/database-domain/replay.py'),
        'oracle_sha256': exe.load().sha256,
        'nonclaims': ['No whole-game DOSBox-X execution acceptance',
            'No Punt noreturn, new slots, clamps, padding, or failure-path layout waiver',
            'No discharge of FindIndex/heap/ctype/sound resource or other independent blockers',
            'Optional language plus mode2/4 can produce five opens outside this domain; failures remain source-required']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    out = (args.out if args.out.is_absolute() else ROOT / args.out).resolve()
    if out.exists() or not out.is_relative_to(ROOT / 'build'):
        parser.error('--out must be fresh under build/')
    result = probe()
    out.mkdir(parents=True)
    (out / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS: complete canonical caller/counter/storage/save census bounds successful default VGA DB slots to 0..2')

if __name__ == '__main__':
    main()


