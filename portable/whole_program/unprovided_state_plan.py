#!/usr/bin/env python3
"""Plan/scratch-emit exact primitive storage for unresolved whole-program state.

This lane consumes the diagnostic whole-program migration inventory and frozen
symbol aliases. It never edits source or a production target. Alias rewrites and
scratch BSS allocations remain proposals until separately reviewed for behavior
and initialization semantics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "build/workers/whole_program/generated/migration.json"
SYMBOLS = ROOT / "layout/symbols.json"
OUT_JSON = ROOT / "portable/research/whole_program_unprovided_owners.json"
OUT_MD = ROOT / "portable/research/whole_program_unprovided_owners.md"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    return json.loads(raw), digest(raw)


def path_rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def scalar_type(base: str) -> dict[str, Any] | None:
    """Recognize only DOS scalar integer storage; signedness is a view contract."""
    b = " ".join(base.split())
    table = {
        "char": (1, "signed-char-target"),
        "signed char": (1, "signed"),
        "unsigned char": (1, "unsigned"),
        "short": (2, "signed"),
        "signed short": (2, "signed"),
        "unsigned short": (2, "unsigned"),
        "int": (2, "signed"),
        "signed int": (2, "signed"),
        "unsigned": (2, "unsigned"),
        "unsigned int": (2, "unsigned"),
        "long": (4, "signed"),
        "signed long": (4, "signed"),
        "unsigned long": (4, "unsigned"),
    }
    row = table.get(b)
    if row is None or "*" in b or "struct " in b or "union " in b:
        return None
    return {"bytes": row[0], "signedness": row[1], "base": b}


def parse_int_literal(token: str) -> int | None:
    t = token.strip()
    t = re.sub(r"(?i)(u|l)+$", "", t)
    if not re.fullmatch(r"(?:0[xX][0-9a-fA-F]+|[0-9]+)", t):
        return None
    if t.lower().startswith("0x"):
        return int(t, 16)
    if len(t) > 1 and t.startswith("0"):
        return int(t, 8)
    return int(t, 10)


def extent_of(view: dict[str, Any], ty: dict[str, Any]) -> tuple[int | None, dict[str, Any]]:
    dims = view.get("dims", [])
    if not isinstance(dims, list):
        return None, {"kind": "malformed", "dimensions": dims}
    if not dims:
        return ty["bytes"], {"kind": "scalar", "shape": [], "element_count": 1}
    shape: list[int] = []
    if any(not isinstance(expr, str) or not expr.strip() for expr in dims):
        if len(dims) == 1 and isinstance(dims[0], str) and not dims[0].strip():
            return None, {"kind": "incomplete-or-unknown-array", "dimensions": dims, "element_view": "one-dimensional primitive elements"}
        return None, {"kind": "incomplete-multidimensional-array-view", "dimensions": dims}
    for expr in dims:
        if not isinstance(expr, str) or not expr.strip():
            return None, {"kind": "incomplete-multidimensional-array-view", "dimensions": dims}
        # Accept only explicit positive integer products. No sizeof, macros,
        # arithmetic sums, or segment-neighbor extent inference.
        tokens = [t.strip() for t in expr.split("*")]
        if not tokens or any(parse_int_literal(t) is None for t in tokens):
            return None, {"kind": "nonliteral-array-bound", "dimensions": dims}
        value = 1
        for token in tokens:
            v = parse_int_literal(token)
            assert v is not None
            value *= v
        if value <= 0:
            return None, {"kind": "nonpositive-array-bound", "dimensions": dims}
        shape.append(value)
    count = 1
    for n in shape:
        count *= n
    return count * ty["bytes"], {"kind": "array", "shape": shape, "element_count": count}


def assess_views(views: list[dict[str, Any]], *, allow_incomplete: bool = False) -> dict[str, Any]:
    """Return fail-closed representation assessment for declaration views."""
    if not views:
        return {"ok": False, "reason": "no-declaration-views"}
    rows = []
    for v in views:
        ty = scalar_type(str(v.get("base", "")))
        if ty is None:
            return {"ok": False, "reason": "pointer-struct-or-nonscalar-view", "view": v}
        size, extent = extent_of(v, ty)
        if size is None:
            if allow_incomplete and extent.get("kind") == "incomplete-or-unknown-array":
                rows.append({"view": v, "type": ty, "extent_bytes": None, "extent": extent})
                continue
            return {"ok": False, "reason": extent["kind"], "view": v, "extent": extent}
        rows.append({"view": v, "type": ty, "extent_bytes": size, "extent": extent})
    widths = sorted({r["type"]["bytes"] for r in rows})
    extents = sorted({r["extent_bytes"] for r in rows if r["extent_bytes"] is not None})
    kinds = {"array" if r["extent"]["kind"] == "incomplete-or-unknown-array" else r["extent"]["kind"] for r in rows}
    scalar_or_array = sorted(kinds)
    ranks = sorted({len(r["extent"].get("shape", [])) for r in rows if r["extent"]["kind"] != "incomplete-or-unknown-array"})
    if len(widths) != 1:
        return {"ok": False, "reason": "conflicting-DOS-element-widths", "view_rows": rows, "widths": widths}
    if len(extents) > 1:
        return {"ok": False, "reason": "conflicting-complete-extents", "view_rows": rows, "extents": extents}
    if len(scalar_or_array) != 1 or (scalar_or_array[0] == "scalar" and ranks not in ([], [0])):
        return {"ok": False, "reason": "scalar-array-shape-conflict", "view_rows": rows}
    if not allow_incomplete and any(r["extent_bytes"] is None for r in rows):
        return {"ok": False, "reason": "incomplete-array-view", "view_rows": rows}
    return {
        "ok": True,
        "width_bytes": widths[0],
        "extent_bytes": extents[0] if len(extents) == 1 else None,
        "extent_kind": scalar_or_array[0],
        "signedness_views": sorted({r["type"]["signedness"] for r in rows}),
        "source_shapes": sorted({tuple(r["extent"].get("shape", [])) for r in rows}),
        "view_rows": rows,
        "signedness_note": "Signed and unsigned views may share the same fixed-width bit representation; each consumer's signed interpretation remains source-specific.",
        "storage_note": "The owner is byte storage of the proven extent. Numeric access on non-little-endian hosts requires explicit conversion; this scratch emitter makes no host-endian semantic claim.",
    }


def canonical_alias(name: str, data: dict[str, Any]) -> tuple[str | None, list[str]]:
    chain: list[str] = []
    seen = {name}
    current = name
    while True:
        rec = data.get(current, {})
        target = rec.get("alias_of")
        if not isinstance(target, str):
            return (current if current != name else None), chain
        chain.append(target)
        if target in seen:
            return None, chain
        seen.add(target)
        current = target


def alias_compatibility(alias_views: list[dict[str, Any]], target_views: list[dict[str, Any]], *,
                        same_address: bool, target_defined: bool) -> dict[str, Any]:
    """Check a primitive alias against a complete, compiled owner view set."""
    if not same_address:
        return {"ok": False, "reason": "alias-target-address-mismatch"}
    if not target_defined:
        return {"ok": False, "reason": "alias-target-has-no-compiled-definition"}
    alias = assess_views(alias_views, allow_incomplete=True)
    target = assess_views(target_views, allow_incomplete=True)
    if not alias.get("ok") or not target.get("ok"):
        return {"ok": False, "reason": "unresolved-nonprimitive-or-conflicting-view", "alias": alias, "target": target}
    if target.get("extent_bytes") is None:
        return {"ok": False, "reason": "target-has-no-complete-extent", "alias": alias, "target": target}
    if alias["width_bytes"] != target["width_bytes"]:
        return {"ok": False, "reason": "different-element-width", "alias": alias, "target": target}
    incomplete = any(row["extent_bytes"] is None for row in alias["view_rows"])
    if incomplete:
        explicit_alias_extents = [row["extent_bytes"] for row in alias["view_rows"] if row["extent_bytes"] is not None]
        if any(n != target["extent_bytes"] for n in explicit_alias_extents):
            return {"ok": False, "reason": "incomplete-alias-view-conflicts-with-complete-alias-extent", "alias": alias, "target": target}
        return {"ok": True, "reason": "incomplete-primitive-element-view-bound-by-complete-owner", "alias": alias, "target": target}
    if alias.get("extent_bytes") != target.get("extent_bytes"):
        return {"ok": False, "reason": "different-complete-byte-extents", "alias": alias, "target": target}
    return {"ok": True, "reason": "equal-primitive-width-and-complete-byte-extent", "alias": alias, "target": target}


def group_key(address: Any) -> str | None:
    if not isinstance(address, list) or len(address) != 2 or not all(isinstance(x, int) for x in address):
        return None
    return f"{address[0]:04X}:{address[1]:04X}"


def member_access_lines(name: str, source_paths: set[str]) -> list[dict[str, Any]]:
    """Reject variable-as-record/pointer member uses in a proposed alias group."""
    hits = []
    pattern = re.compile(r"\b" + re.escape(name) + r"\b(?:\s*\[[^\]]+\])*\s*(?:->|\.)\s*[A-Za-z_]\w*")
    comments_strings = re.compile(r"/\*.*?\*/|//[^\n]*|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'", re.S)
    for src in sorted(source_paths):
        path = ROOT / src
        text = path.read_text(encoding="utf-8", errors="replace")
        masked = comments_strings.sub(lambda m: "\n" * m.group().count("\n"), text)
        for match in pattern.finditer(masked):
            hits.append({"source": src, "line": masked.count("\n", 0, match.start()) + 1,
                         "token_form": match.group()})
    return hits


def controls() -> dict[str, Any]:
    def view(base: str, dims: list[str]) -> dict[str, Any]:
        return {"base": base, "dims": dims}

    positives = {
        "signed_unsigned_same_word": assess_views([view("int", []), view("unsigned int", [])])["ok"],
        "same_byte_extent_flat_multidim": assess_views([view("unsigned char", ["128", "64"]), view("char", ["8192"])])["ok"],
        "incomplete_primitive_alias_view_can_be_bound_later": assess_views([view("unsigned char", [""])], allow_incomplete=True)["ok"],
        "registered_incomplete_alias_to_complete_owner": alias_compatibility(
            [view("unsigned char", [""])], [view("unsigned char", ["8"])], same_address=True, target_defined=True)["ok"],
        "multidimensional_alias_same_extent": alias_compatibility(
            [view("unsigned char", ["2", "4"])], [view("char", ["8"])], same_address=True, target_defined=True)["ok"],
    }
    negatives = {
        "different_width": not assess_views([view("int", []), view("unsigned char", [])])["ok"],
        "different_extent": not assess_views([view("unsigned char", ["8"]), view("char", ["9"])])["ok"],
        "incomplete_owner_array": not assess_views([view("unsigned char", [""])])["ok"],
        "pointer_view": not assess_views([view("void *", [])])["ok"],
        "struct_view": not assess_views([view("struct Rect", [])])["ok"],
        "alias_width_conflict": not alias_compatibility(
            [view("unsigned char", ["8"])], [view("int", ["4"])], same_address=True, target_defined=True)["ok"],
        "alias_extent_conflict": not alias_compatibility(
            [view("unsigned char", ["7"])], [view("unsigned char", ["8"])], same_address=True, target_defined=True)["ok"],
        "alias_address_conflict": not alias_compatibility(
            [view("unsigned char", ["8"])], [view("unsigned char", ["8"])], same_address=False, target_defined=True)["ok"],
        "alias_missing_target": not alias_compatibility(
            [view("unsigned char", ["8"])], [view("unsigned char", ["8"])], same_address=True, target_defined=False)["ok"],
    }
    return {"positive": positives, "negative": negatives,
            "passed": all(positives.values()) and all(negatives.values()),
            "purpose": "Planner guard controls only; they do not establish any production alias or state semantics."}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--migration", type=Path, default=MIGRATION)
    ap.add_argument("--symbols", type=Path, default=SYMBOLS)
    ap.add_argument("--json", type=Path, default=OUT_JSON)
    ap.add_argument("--markdown", type=Path, default=OUT_MD)
    ap.add_argument("--emit", type=Path, help="scratch C file for owner-only BSS candidates")
    args = ap.parse_args()
    migration, migration_hash = read_json(args.migration)
    symbols, symbols_hash = read_json(args.symbols)
    if migration.get("schema") != "simant-whole-program-migration-v1" or symbols.get("schema") != "simant-symbols-v1":
        raise SystemExit("unexpected migration or symbols schema")
    data = symbols.get("data", {})

    definitions: dict[str, list[dict[str, Any]]] = defaultdict(list)
    module_by_source = {r["source"]: r for r in migration.get("modules", [])}
    module_by_source.update({r["source"]: r for r in migration.get("native_support", [])})
    generator_path = ROOT / "portable/tools/whole_program.py"
    if migration.get("generator_sha256") != digest(generator_path.read_bytes()):
        raise SystemExit("whole-program generator changed since migration inventory; regenerate migration first")
    for module in list(migration.get("modules", [])) + list(migration.get("native_support", [])):
        source_path = ROOT / module["source"]
        if module.get("source_sha256") and digest(source_path.read_bytes()) != module["source_sha256"]:
            raise SystemExit(f"source changed since migration inventory: {module['source']}")
        compile_row = module.get("compile", {})
        object_rel = compile_row.get("object")
        object_sha = compile_row.get("object_sha256")
        if object_rel and object_sha:
            object_path = ROOT / object_rel
            if not object_path.is_file() or digest(object_path.read_bytes()) != object_sha:
                raise SystemExit(f"compiled object missing or changed since migration inventory: {object_rel}")
        for sym in module.get("object_symbols", []):
            if sym.get("kind") in {"B", "D", "R", "C"}:
                definitions[sym["name"]].append({"source": module["source"], "kind": sym["kind"],
                                                   "object": module.get("compile", {}).get("object"),
                                                   "object_sha256": module.get("compile", {}).get("object_sha256")})

    candidates_by_addr: dict[str, list[dict[str, Any]]] = defaultdict(list)
    unresolved: list[dict[str, Any]] = []
    for name, contract in sorted(migration.get("unprovided_symbol_contracts", {}).items()):
        if contract.get("classification") != "GLOBAL_STATE":
            continue
        views = contract.get("source_views", [])
        addrs = {group_key(v.get("layout_address")) for v in views}
        if len(addrs) != 1 or None in addrs:
            unresolved.append({"name": name, "reason": "declaration-views-have-no-single-frozen-address", "views": views})
            continue
        addr = next(iter(addrs))
        symrec = data.get(name)
        if symrec is None or group_key([symrec.get("seg"), symrec.get("off")]) != addr:
            unresolved.append({"name": name, "address": addr, "reason": "source-view-address-does-not-match-frozen-symbol"})
            continue
        candidates_by_addr[addr].append({"name": name, "contract": contract, "views": views, "symbol": symrec})

    plan_groups = []
    bss_owners = []
    rename_map: dict[str, str] = {}
    counts: dict[str, int] = defaultdict(int)

    # All registered symbols at an address participate in owner/alias decisions.
    registered_at: dict[str, list[str]] = defaultdict(list)
    for n, rec in data.items():
        addr = group_key([rec.get("seg"), rec.get("off")])
        if addr:
            registered_at[addr].append(n)

    for addr, rows in sorted(candidates_by_addr.items()):
        names = sorted(r["name"] for r in rows)
        views = [v for r in rows for v in r["views"]]
        assessment = assess_views(views, allow_incomplete=True)
        provided_here = sorted(n for n in registered_at.get(addr, []) if definitions.get(n))
        alias_edges = []
        for row in rows:
            target, chain = canonical_alias(row["name"], data)
            if target:
                target_rec = data.get(target, {})
                target_addr = group_key([target_rec.get("seg"), target_rec.get("off")])
                alias_edges.append({"name": row["name"], "target": target, "chain": chain,
                                    "target_address": target_addr})
        group = {"address": addr, "unprovided_members": names,
                 "registered_address_members": sorted(registered_at.get(addr, [])),
                 "provided_members_at_address": provided_here,
                 "alias_edges": alias_edges,
                 "view_count": len(views), "view_modules": sorted({v.get("module", "") for v in views}),
                 "assessment": assessment}

        grounding_runtime = sorted({
            str(data.get(n, {}).get("grounding", ""))
            for n in registered_at.get(addr, [])
            if "runtime" in str(data.get(n, {}).get("grounding", "")).lower()
        })
        if grounding_runtime:
            group["decision"] = "unresolved"
            group["reason"] = "frozen symbol grounding identifies runtime-owned storage; do not create an application BSS owner"
            group["runtime_owner_grounding"] = grounding_runtime
            plan_groups.append(group); counts["runtime-owner-debt"] += 1
            continue

        if not assessment.get("ok"):
            group["decision"] = "unresolved"
            group["reason"] = assessment.get("reason")
            plan_groups.append(group); counts["unresolved-view-contract"] += 1
            continue

        # An alias can be rewritten only to an actual compiled owner at the same
        # frozen address and only when every declaration view agrees in primitive
        # width and complete byte extent (or is incomplete over that proven owner).
        mapped = False
        for edge in alias_edges:
            target = edge["target"]
            if edge["target_address"] != addr or not definitions.get(target):
                continue
            target_views = [v for v in migration.get("object_declaration_views", []) if v.get("name") == target]
            compat = alias_compatibility(views, target_views, same_address=edge["target_address"] == addr,
                                         target_defined=bool(definitions.get(target)))
            if not compat.get("ok"):
                continue
            member_uses = []
            for alias_name in names:
                member_uses.extend(member_access_lines(alias_name, set(group["view_modules"])))
            if member_uses:
                group["decision"] = "unresolved"
                group["reason"] = "candidate alias is used as a structure/pointer member base"
                group["member_access_uses"] = member_uses
                plan_groups.append(group); counts["alias-member-access-rejected"] += 1
                mapped = True
                break
            group["member_access_scan"] = {"source_modules": sorted(group["view_modules"]),
                                           "field_or_pointer_member_uses": []}
            target_assessment = compat["target"]
            target_extent = target_assessment["extent_bytes"]
            # Reject aliases whose registered group includes a nonprimitive owner
            # or a symbol with a conflicting source view; only this unresolved alias
            # is renamed, never the actual provider symbol.
            for n in names:
                if n != target:
                    rename_map[n] = target
            group["decision"] = "registered-alias-rename-candidate"
            group["owner"] = target
            group["owner_extent_bytes"] = target_extent
            group["alias_compatibility"] = {k: v for k, v in compat.items() if k not in {"alias", "target"}}
            group["reason"] = "registered alias, same address, primitive width, and byte extent proven against compiled owner"
            group["owner_definitions"] = definitions[target]
            group["target_views"] = target_views
            mapped = True
            counts["alias-rename-candidate"] += 1
            break
        if mapped:
            if group.get("decision") == "unresolved":
                continue
            plan_groups.append(group)
            continue

        if assessment["extent_bytes"] is None or any(r["extent_bytes"] is None for r in assessment["view_rows"]):
            group["decision"] = "unresolved"
            group["reason"] = "incomplete declaration extent lacks a registered complete owner"
            plan_groups.append(group); counts["unowned-incomplete-extent"] += 1
            continue

        if provided_here:
            group["decision"] = "unresolved"
            group["reason"] = "address group already has a compiled owner but no safe registered primitive alias mapping was proven"
            plan_groups.append(group); counts["provided-address-needs-alias-review"] += 1
            continue

        group["decision"] = "scratch-BSS-owner-candidate"
        group["owner"] = names[0]
        group["extent_bytes"] = assessment["extent_bytes"]
        group["reason"] = "all unprovided declaration views agree on primitive width and explicit complete extent; zero-initialized C storage remains only a scratch allocation proposal"
        for alias in names[1:]:
            rename_map[alias] = names[0]
        bss_owners.append(group)
        plan_groups.append(group)
        counts["scratch-BSS-owner-candidate"] += 1

    # Overlap rejection for proposed BSS objects: no address inside an object is
    # silently converted into another independent scalar/array object.
    for group in list(bss_owners):
        seg_s, off_s = group["address"].split(":")
        seg, start, end = int(seg_s, 16), int(off_s, 16), int(off_s, 16) + group["extent_bytes"]
        interior = []
        for addr, members in registered_at.items():
            s2, o2 = addr.split(":")
            if int(s2, 16) == seg and start < int(o2, 16) < end:
                interior.extend(members)
        if interior:
            group["decision"] = "unresolved"
            group["reason"] = "proposed owner extent contains distinct registered symbol addresses; possible interior fields/aliases require review"
            group["interior_symbols"] = sorted(set(interior))
            counts["scratch-BSS-overlap-rejected"] += 1
            counts["scratch-BSS-owner-candidate"] -= 1
            bss_owners.remove(group)

    # Do not emit or rewrite any symbol already defined in the current scratch
    # module/support objects. BSS candidate filtering is repeated here as a guard.
    for group in list(bss_owners):
        duplicates = [n for n in group["unprovided_members"] if definitions.get(n)]
        if duplicates:
            group["decision"] = "unresolved"
            group["reason"] = "candidate name is already defined by compiled source/native support"
            group["defined_names"] = duplicates
            bss_owners.remove(group)
            counts["duplicate-provider-rejected"] += 1
            counts["scratch-BSS-owner-candidate"] -= 1

    test_controls = controls()
    if not test_controls["passed"]:
        raise SystemExit("planner positive/negative controls failed")

    input_sources = {}
    for g in plan_groups:
        for src in g.get("view_modules", []):
            row = module_by_source.get(src)
            if row:
                input_sources[src] = row.get("source_sha256")
        for d in g.get("owner_definitions", []):
            row = module_by_source.get(d["source"])
            if row:
                input_sources[d["source"]] = row.get("source_sha256")

    unresolved_reasons = Counter(g.get("reason", "unspecified") for g in plan_groups if g.get("decision") == "unresolved")
    unresolved_reasons.update(g.get("reason", "unspecified") for g in unresolved)

    emitted_path = None
    emitted_hash = None
    if args.emit:
        args.emit.parent.mkdir(parents=True, exist_ok=True)
        c_lines = [
            "/* Scratch unresolved-state owner candidates. Not production state.",
            " * Zero initialization is an unavoidable C storage property here, not a",
            " * source-derived initial value or behavior claim. */",
            "#include <stdint.h>", "",
        ]
        for group in bss_owners:
            primary = group["owner"]
            size = group["extent_bytes"]
            c_lines.append(f"uint8_t {primary}[{size}];")
            for alias in group["unprovided_members"]:
                if alias != primary:
                    c_lines.append(f"extern __typeof__({primary}) {alias} __attribute__((alias(\"{primary}\")));" )
            c_lines.append("")
        args.emit.write_text("\n".join(c_lines), encoding="utf-8")
        emitted_path = path_rel(args.emit)
        emitted_hash = digest(args.emit.read_bytes())

    report = {
        "schema": "simant-whole-program-unprovided-state-plan-v1",
        "claim": "Scratch planning/emission only. Alias rewrites and BSS allocation candidates are not source behavior or production state admission.",
        "inputs": {
            "migration": {"path": path_rel(args.migration), "sha256": migration_hash,
                          "generator_sha256": migration.get("generator_sha256"),
                          "claim": migration.get("claim")},
            "frozen_symbols": {"path": path_rel(args.symbols), "sha256": symbols_hash},
            "view_source_pins": [{"path": p, "sha256": h} for p, h in sorted(input_sources.items())],
            "compiled_definition_objects": [{"source": r["source"],
                                              "source_sha256": r.get("source_sha256"),
                                              "object": r.get("compile", {}).get("object"),
                                              "object_sha256": r.get("compile", {}).get("object_sha256")}
                                             for r in list(migration.get("modules", [])) + list(migration.get("native_support", []))
                                             if r.get("compile", {}).get("object")],
            "compiled_native_support": [{"source": r["source"], "source_sha256": r.get("source_sha256"),
                                          "object": r.get("compile", {}).get("object"),
                                          "object_sha256": r.get("compile", {}).get("object_sha256")}
                                         for r in migration.get("native_support", [])],
        },
        "method": {
            "primitive_types": "DOS char=8-bit; short/int=16-bit; long=32-bit. Signed/unsigned views can share same-width storage, recorded per view; pointers, structs, handles, function pointers, and unknown typedefs are excluded.",
            "extents": "Only scalar declarations or explicit positive integer-literal array dimensions (including products) are accepted. Incomplete array views are not BSS extents; they may map only through a registered alias to a complete compiled primitive owner of matching width.",
            "aliases": "Requires layout alias_of chain, exact address agreement, a compiled target owner, and compatible primitive element width and total byte extent. Multidimensional shapes may differ only where complete byte extents agree; per-TU declaration shapes remain a caller-side compile concern.",
            "storage": "Scratch BSS has zero-initialized C storage by language rules; this does not claim the historical initial value. No existing object name is emitted again.",
        },
        "controls": test_controls,
        "summary": {"unprovided_global_state_names": sum(1 for c in migration.get("unprovided_symbol_contracts", {}).values() if c.get("classification") == "GLOBAL_STATE"),
                    "address_groups": len(plan_groups), "decision_counts": dict(sorted(counts.items())),
                    "alias_rename_count": len(rename_map), "scratch_bss_owner_count": len(bss_owners),
                    "unresolved_reason_counts": dict(sorted(unresolved_reasons.items())),
                    "unresolved_count": len(unresolved) + sum(g["decision"] == "unresolved" for g in plan_groups)},
        "rename_map": dict(sorted(rename_map.items())),
        "groups": sorted(plan_groups, key=lambda g: (g["address"], g["unprovided_members"])),
        "unresolved_without_group": unresolved,
        "scratch_emitted_c": {"path": emitted_path, "sha256": emitted_hash} if emitted_path else None,
    }
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md = ["# Unprovided whole-program primitive state plan", "",
          "> Scratch lane only. It does not establish source behavior or production state admission.", "",
          f"Migration SHA-256: `{migration_hash}`; frozen symbols SHA-256: `{symbols_hash}`.", "",
          "## Results", "",
          f"- Unprovided global-state names: {report['summary']['unprovided_global_state_names']}",
          f"- Address groups: {len(plan_groups)}",
          f"- Safe registered alias rename candidates: {len(rename_map)} names",
          f"- Scratch BSS owner candidates: {len(bss_owners)}",
          f"- Unresolved groups/names: {report['summary']['unresolved_count']}",
          "- Planner controls: positive and negative controls passed.", "",
          "Registered aliases point to an already compiled owner, so they produce a lexical rename proposal rather than a duplicate object. Scratch BSS allocations contain no initializer because initial values are not established by declarations; C zero initialization is an unavoidable implementation property, not an oracle claim. Existing provider names are never emitted again.", "",
          "## Alias rename candidates", "",
          "| Address | Missing alias | Existing owner | Extent bytes | Width |",
          "|---|---|---|---:|---:|"]
    for g in plan_groups:
        if g["decision"] != "registered-alias-rename-candidate":
            continue
        for n in g["unprovided_members"]:
            md.append(f"| `{g['address']}` | `{n}` | `{g['owner']}` | {g['owner_extent_bytes']} | {g['assessment']['width_bytes']} |")
    md += ["", "## Scratch BSS candidates", "", "| Address | Owner | Extent bytes | Width | Source views |", "|---|---|---:|---:|---|"]
    for g in bss_owners:
        md.append(f"| `{g['address']}` | `{g['owner']}` | {g['extent_bytes']} | {g['assessment']['width_bytes']} | {len(g['view_modules'])} modules |")
    md += ["", "## Debt", "", "Every rejected group retains its views and a machine-readable reason in the JSON. Incomplete unowned arrays, conflicting DOS widths/extents, nonprimitive types, provider collisions, and ranges containing distinct registered addresses remain unresolved. The emitter creates no pointers, structures, callable stubs, capacity guesses, or duplicate provider names.", "",
           "Reason counts:", ""]
    for reason, count in sorted(unresolved_reasons.items()):
        md.append(f"- {count}: {reason}")
    md += ["",
           "Regenerate with `python portable/whole_program/unprovided_state_plan.py`. For a local scratch C candidate, add `--emit build/workers/whole_program/unprovided_state.c`.", ""]
    args.markdown.write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
