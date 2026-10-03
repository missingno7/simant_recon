#!/usr/bin/env python3
"""Build a conservative, source-grounded inventory of whole-program globals.

This is a research report generator. It does not generate or alter production
state, and a generated object's symbol table is used only as inventory evidence.
Storage ownership and extent are admitted automatically only from a simple,
complete primitive definition in one of the frozen DATA source translation units.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MIGRATION_DEFAULT = ROOT / "build/workers/whole_program/generated/migration.json"
SYMBOLS_DEFAULT = ROOT / "layout/symbols.json"
JSON_DEFAULT = ROOT / "portable/research/whole_program_state_ownership.json"
MD_DEFAULT = ROOT / "portable/research/whole_program_state_ownership.md"

DECL = re.compile(
    r"^\s*(?P<storage>static\s+)?"
    r"(?P<base>(?:(?:unsigned|signed)\s+)?(?:char|short|int|long|float|double))"
    r"(?P<qual>\s+(?:far|near|huge))*\s+"
    r"(?P<name>[A-Za-z_]\w*)"
    r"(?P<dims>(?:\s*\[[^\]]*\])*)\s*(?P<tail>.*)$"
)
DIM = re.compile(r"\[\s*(0[xX][0-9a-fA-F]+|[0-9]+)\s*\]")
ARRAYS = re.compile(r"\[([^\]]*)\]")
COMMENT_BLOCK = re.compile(r"/\*.*?\*/", re.S)
COMMENT_LINE = re.compile(r"//.*")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def load_json(path: Path) -> tuple[Any, str]:
    raw = path.read_bytes()
    return json.loads(raw), sha256(raw)


def parse_dim_list(dims: str) -> tuple[list[int] | None, list[str]]:
    raw = ARRAYS.findall(dims)
    vals: list[int] = []
    for item in raw:
        if not re.fullmatch(r"\s*(?:0[xX][0-9a-fA-F]+|[0-9]+)\s*", item):
            return None, [x.strip() for x in raw]
        vals.append(int(item, 0))
    return vals, [x.strip() for x in raw]


def primitive_size(base: str) -> int | None:
    b = " ".join(base.split())
    if b in {"char", "signed char", "unsigned char"}:
        return 1
    if b in {"short", "signed short", "unsigned short", "int", "signed int", "unsigned int"}:
        return 2  # DOS compiler's source ABI, not the host migration compiler.
    if b in {"long", "signed long", "unsigned long", "float"}:
        return 4
    if b == "double":
        return 8
    return None


def data_definitions(migration: dict[str, Any]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, str]]:
    """Read only declaration headers in DATA TUs; never infer size from symbols."""
    defs: dict[str, list[dict[str, Any]]] = defaultdict(list)
    source_hashes: dict[str, str] = {}
    for module in migration["modules"]:
        if module.get("module_kind") != "DATA":
            continue
        source = ROOT / module["source"]
        raw = source.read_bytes()
        source_hashes[module["source"]] = sha256(raw)
        text = raw.decode("utf-8", errors="replace")
        text = COMMENT_BLOCK.sub("", text)
        offset = 0
        for line_no, line in enumerate(text.splitlines(keepends=True), 1):
            clean = COMMENT_LINE.sub("", line)
            m = DECL.match(clean)
            if not m or not m.group("tail").lstrip().startswith(("=", ";")):
                offset += len(line)
                continue
            # An extern is never an owner, even if its declaration has a bound.
            prefix = clean[:m.start("storage") if m.group("storage") else m.start("base")]
            if re.search(r"\bextern\b", prefix):
                offset += len(line)
                continue
            base = " ".join(m.group("base").split())
            dims, dim_exprs = parse_dim_list(m.group("dims"))
            esize = primitive_size(base)
            exact_count: int | None = 1
            extent_reason = ""
            if m.group("dims"):
                if dims is None:
                    exact_count = None
                    extent_reason = "array bound is not a numeric literal"
                elif any(d == 0 for d in dims):
                    exact_count = None
                    extent_reason = "incomplete array bound"
                else:
                    for d in dims:
                        exact_count *= d
            if esize is None:
                extent_reason = "aggregate, pointer, or unsupported scalar type needs a typed owner"
            elif exact_count is None:
                pass
            if not m.group("dims") and esize is None:
                exact_count = None
            extent = esize * exact_count if esize is not None and exact_count is not None else None
            # Read through the declaration terminator so multiline initializers are
            # classified without interpreting initializer contents as storage size.
            end = text.find(";", offset + m.start("tail"))
            declaration_tail = text[offset + m.start("tail"): end if end >= 0 else offset + len(line)]
            has_initializer = declaration_tail.lstrip().startswith("=")
            init_expr = declaration_tail.lstrip()[1:].strip() if has_initializer else ""
            zero_initialized = (not has_initializer) or bool(re.fullmatch(
                r"(?:\{\s*0(?:\s*,\s*0)*\s*\}|0\s*[uUlL]*)\s*", init_expr, re.S
            ))
            owner = {
                "source": module["source"],
                "line": line_no,
                "name": m.group("name"),
                "base_type": base,
                "array_bounds": dim_exprs,
                "storage_duration": "static" if m.group("storage") else "external-linkage-candidate",
                "initializer_present": has_initializer,
                "zero_initialized": zero_initialized,
                "initializer_kind": "none" if not has_initializer else ("zero" if zero_initialized else "nonzero-or-unparsed"),
                "primitive_element_bytes_dos_abi": esize,
                "element_count": exact_count,
                "extent_bytes": extent,
                "extent_status": "exact-source-literal" if extent is not None else "unresolved",
                "extent_reason": extent_reason or None,
            }
            defs[m.group("name")].append(owner)
            offset += len(line)
    return defs, source_hashes


def name_addr(seg: int, off: int) -> str:
    return f"{seg:04X}:{off:04X}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--migration", type=Path, default=MIGRATION_DEFAULT)
    ap.add_argument("--symbols", type=Path, default=SYMBOLS_DEFAULT)
    ap.add_argument("--json", type=Path, default=JSON_DEFAULT)
    ap.add_argument("--markdown", type=Path, default=MD_DEFAULT)
    ap.add_argument("--emit", type=Path, help="optional scratch C file containing only proven zero/BSS primitive owners")
    args = ap.parse_args()

    migration, migration_hash = load_json(args.migration)
    symbols, symbols_hash = load_json(args.symbols)
    if migration.get("schema") != "simant-whole-program-migration-v1":
        raise SystemExit(f"unsupported migration schema: {migration.get('schema')}")
    if symbols.get("schema") != "simant-symbols-v1":
        raise SystemExit(f"unsupported symbols schema: {symbols.get('schema')}")

    definitions, source_hashes = data_definitions(migration)
    data_module_pins = {m["source"]: m.get("source_sha256") for m in migration["modules"] if m.get("module_kind") == "DATA"}
    for source, actual_hash in source_hashes.items():
        expected_hash = data_module_pins.get(source)
        if expected_hash != actual_hash:
            raise SystemExit(f"DATA source changed since migration inventory: {source} expected={expected_hash} actual={actual_hash}")
    views_by_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in migration.get("object_declaration_views", []):
        views_by_name[row["name"]].append(row)

    # Address is the frozen identity anchor; histories are retained as alias evidence.
    by_addr: dict[str, dict[str, Any]] = {}
    unlocated_names: dict[str, dict[str, Any]] = {}
    for name, rec in symbols.get("data", {}).items():
        seg, off = rec.get("seg"), rec.get("off")
        if not isinstance(seg, int) or not isinstance(off, int):
            unlocated_names[name] = {"name": name, "symbol_record": rec}
            continue
        addr = name_addr(seg, off)
        group = by_addr.setdefault(addr, {"address": addr, "members": [], "symbol_histories": []})
        group["members"].append(name)
        if rec.get("history"):
            group["symbol_histories"].append({"name": name, "history": rec["history"]})

    # Also retain migration-only object names, but do not invent addresses for them.
    for name, rows in views_by_name.items():
        for row in rows:
            addr = row.get("layout_address")
            if isinstance(addr, list) and len(addr) == 2 and all(isinstance(n, int) for n in addr):
                key = name_addr(addr[0], addr[1])
                group = by_addr.setdefault(key, {"address": key, "members": [], "symbol_histories": []})
                if name not in group["members"]:
                    group["members"].append(name)
            elif name not in unlocated_names:
                unlocated_names[name] = {"name": name}

    catalog_groups: list[dict[str, Any]] = []
    group_owners = 0
    for addr, group in sorted(by_addr.items()):
        members = sorted(set(group["members"]))
        view_rows = [r for name in members for r in views_by_name.get(name, [])]
        owner_defs = [d for name in members for d in definitions.get(name, [])]
        # Same-address aliases can yield duplicate references to one definition; de-dupe it.
        dedup = {(d["source"], d["line"], d["name"]): d for d in owner_defs}
        owner_defs = list(dedup.values())
        exact_defs = [d for d in owner_defs if d["extent_bytes"] is not None]
        pointer_like = any("*" in r.get("base", "") for r in view_rows)
        aggregate_like = any("struct" in r.get("base", "") for r in view_rows)
        if len(exact_defs) == 1:
            ownership = "single-source-definition-candidate"
            group_owners += 1
            owner_status = "one exact primitive DATA definition; admission remains separate"
        elif len(exact_defs) > 1:
            ownership = "conflicting-source-definitions"
            owner_status = "multiple exact definitions share this address; typed review required"
        elif owner_defs:
            ownership = "source-definition-needs-typed-owner-or-exact-extent"
            owner_status = "definition exists but primitive extent cannot be proven conservatively"
        else:
            ownership = "no-source-DATA-owner-proven"
            owner_status = "declaration views or symbol identity only; no storage owner inferred"
        if pointer_like or aggregate_like:
            type_debt = "pointer/aggregate views require explicit typed owner and lifetime semantics"
        else:
            type_debt = None

        views = []
        seen_views = set()
        for r in view_rows:
            sig = (r.get("module"), r.get("base"), tuple(r.get("dims", [])), r.get("alias_of"))
            if sig in seen_views:
                continue
            seen_views.add(sig)
            views.append({
                "module": r.get("module"), "base_type": r.get("base"),
                "dimensions": r.get("dims"), "alias_of": r.get("alias_of"),
            })
        group["members"] = members
        group["owner_candidates"] = sorted(owner_defs, key=lambda d: (d["source"], d["line"]))
        group["ownership_status"] = ownership
        group["ownership_note"] = owner_status
        group["typed_view_debt"] = type_debt
        group["declaration_views"] = views
        observed_bases = sorted({v["base_type"] for v in views if v.get("base_type")})
        all_bases = sorted(set(observed_bases) | {d["base_type"] for d in owner_defs})
        group["observed_representation_views"] = {
            "raw_byte_view": {
                "available": bool(exact_defs),
                "meaning": "byte-for-byte storage view over the same owner; extent comes only from the exact source definition",
            },
            "signed_byte_views": [b for b in all_bases if b in {"char", "signed char"}],
            "unsigned_byte_views": [b for b in all_bases if b == "unsigned char"],
            "signed_word_views": [b for b in all_bases if b in {"short", "signed short", "int", "signed int"}],
            "unsigned_word_views": [b for b in all_bases if b in {"unsigned short", "unsigned int"}],
            "word_view_caveat": "A word view is a consumer interpretation over bytes, not an additional owner; endianness and DOS-width conversion must be explicit.",
        }
        group["byte_view_policy"] = (
            "Raw byte access is an explicit representation view only; it is not a second owner."
            if exact_defs else "No byte owner is inferred without source extent evidence."
        )
        group["word_view_policy"] = (
            "16-bit signed/unsigned interpretation must be explicit at each consumer; preserve raw bytes for endian-sensitive serialization."
            if exact_defs else "No word owner or extent is inferred."
        )
        catalog_groups.append(group)

    # Detect exact source-owner byte spans that overlap. Such groups are not
    # independently emitted: a typed aggregate/alias boundary must be reviewed.
    owner_spans: list[tuple[int, int, int, dict[str, Any], dict[str, Any]]] = []
    for group in catalog_groups:
        if group.get("address") is None or group.get("ownership_status") != "single-source-definition-candidate":
            continue
        d = group["owner_candidates"][0]
        if d["extent_bytes"] is None:
            continue
        seg_s, off_s = group["address"].split(":")
        owner_spans.append((int(seg_s, 16), int(off_s, 16), int(off_s, 16) + d["extent_bytes"], group, d))
    overlapping: set[int] = set()
    interior_members: dict[int, list[str]] = defaultdict(list)
    for i, (seg, start, end, g, d) in enumerate(owner_spans):
        for j, (seg2, start2, end2, g2, d2) in enumerate(owner_spans):
            if i >= j or seg != seg2:
                continue
            if max(start, start2) < min(end, end2):
                overlapping.update((i, j))
        for other in catalog_groups:
            if other.get("address") is None or other is g:
                continue
            seg_o, off_o = other["address"].split(":")
            if int(seg_o, 16) == seg and start < int(off_o, 16) < end:
                interior_members[i].extend(other["members"])
        g["interior_symbol_views"] = sorted(set(interior_members[i]))
        g["overlaps_another_exact_owner"] = i in overlapping

    emitted_owners: list[dict[str, Any]] = []
    emit_skips: dict[str, int] = defaultdict(int)
    owner_rows = []
    for i, (seg, start, end, group, d) in enumerate(owner_spans):
        reason = None
        if i in overlapping:
            reason = "source-owner spans overlap; do not emit independent objects"
        elif d["storage_duration"] != "external-linkage-candidate":
            reason = "static/local source object is not an external owner candidate"
        elif not d["zero_initialized"]:
            reason = "source definition has a nonzero or unparsed initializer; BSS zero fallback forbidden"
        elif d["base_type"] not in {"char", "signed char", "unsigned char", "short", "signed short", "unsigned short", "int", "signed int", "unsigned int", "long", "signed long", "unsigned long"}:
            reason = "source type is not an admitted integer primitive owner"
        elif group.get("interior_symbol_views"):
            # Basing bytes is safe; creating linker labels at interior addresses is not.
            # Emit only if all interior views stay unresolved in this C-only scratch output.
            pass
        if reason:
            emit_skips[reason] += 1
            group["emitter_status"] = "skipped"
            group["emitter_blocker"] = reason
            continue
        row = {"address": group["address"], "members": group["members"], "definition": d,
               "interior_symbol_views_left_unprovided": group.get("interior_symbol_views", [])}
        emitted_owners.append(row)
        group["emitter_status"] = "emitted-scratch-owner-candidate"
        group["emitter_note"] = "only the exact source object and same-address aliases are emitted; interior aliases remain unprovided"

    def ctype(base: str) -> str:
        return {
            "char": "int8_t", "signed char": "int8_t", "unsigned char": "uint8_t",
            "short": "int16_t", "signed short": "int16_t", "unsigned short": "uint16_t",
            "int": "int16_t", "signed int": "int16_t", "unsigned int": "uint16_t",
            "long": "int32_t", "signed long": "int32_t", "unsigned long": "uint32_t",
        }[base]

    if args.emit:
        args.emit.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "/* Scratch owner declarations emitted from exact frozen DATA definitions.",
            " * Not production state: unresolved and interior aliases are intentionally absent. */",
            "#include <stdint.h>", "",
        ]
        for row in emitted_owners:
            d = row["definition"]
            primary = d["name"]
            dims = "".join(f"[{v}]" for v in d["array_bounds"])
            if not dims:
                dims = "[1]" if d["element_count"] == 1 else ""
            lines.append(f"{ctype(d['base_type'])} {primary}{dims};")
            for alias in row["members"]:
                if alias == primary:
                    continue
                # GCC's alias attribute is an exact zero-offset linker alias.
                lines.append(f"extern __typeof__({primary}) {alias} __attribute__((alias(\"{primary}\")));" )
            lines.append("")
        args.emit.write_text("\n".join(lines), encoding="utf-8")
        emit_raw = args.emit.read_bytes()
        emitted_c_hash = sha256(emit_raw)
        # Save an adjacent machine-readable roster for diagnostic linker coverage.
        args.emit.with_suffix(args.emit.suffix + ".json").write_text(json.dumps({
            "schema": "simant-whole-program-owner-emission-v1",
            "claim": "Scratch diagnostic only; not linked into production.",
            "emitted_c": {"path": rel(args.emit), "sha256": emitted_c_hash},
            "owners": emitted_owners,
            "skipped": dict(sorted(emit_skips.items())),
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    for name in unlocated_names:
        # Exclude only names also represented by a frozen group.
        if any(name in g["members"] for g in catalog_groups):
            continue
        rec = unlocated_names[name].get("symbol_record", {})
        catalog_groups.append({
            "address": None, "members": [name], "symbol_histories": rec.get("history", []),
            "owner_candidates": definitions.get(name, []),
            "ownership_status": "no-frozen-address", "ownership_note": "name is known but no address-based canonical grouping is possible",
            "typed_view_debt": "pointer/aggregate families remain unresolved until typed owner and alias identity are established",
            "declaration_views": [{"module": r.get("module"), "base_type": r.get("base"), "dimensions": r.get("dims"), "alias_of": r.get("alias_of")} for r in views_by_name.get(name, [])],
            "byte_view_policy": "No owner or extent inferred.",
            "word_view_policy": "No owner or extent inferred.",
        })

    counts: dict[str, int] = defaultdict(int)
    for group in catalog_groups:
        counts[group["ownership_status"]] += 1
    output = {
        "schema": "simant-whole-program-state-ownership-v1",
        "claim": "Research inventory only. Source definitions and frozen addresses support owner candidates; compilation and symbol presence do not admit behavior or production state.",
        "inputs": {
            "migration": {"path": rel(args.migration), "sha256": migration_hash, "claim": migration.get("claim")},
            "frozen_symbols": {"path": rel(args.symbols), "sha256": symbols_hash, "schema": symbols.get("schema")},
            "data_source_files": [{"path": p, "sha256": h} for p, h in sorted(source_hashes.items())],
        },
        "method": {
            "identity": "Group by frozen segment:offset; retain history aliases and migration declaration views.",
            "extent": "Exact byte extents are emitted only for simple primitive definitions in migration DATA source TUs with literal complete dimensions. No next-symbol or object-file size inference.",
            "ownership": "At most one exact source-definition candidate is called a single-owner candidate. It is not an admission or permission to create a second runtime state copy.",
            "views": "Byte and 16-bit interpretations are recorded as consumer views over one owner. Pointer and aggregate families remain explicit debt.",
        },
        "summary": {
            "addressed_groups": sum(1 for g in catalog_groups if g["address"] is not None),
            "unlocated_groups": sum(1 for g in catalog_groups if g["address"] is None),
            "groups_with_single_exact_primitive_owner_candidate": group_owners,
            "scratch_owner_emission_count": len(emitted_owners),
            "scratch_owner_emission_skips": dict(sorted(emit_skips.items())),
            "groups_by_status": dict(sorted(counts.items())),
            "migration_declaration_view_count": len(migration.get("object_declaration_views", [])),
            "frozen_data_symbol_count": len(symbols.get("data", {})),
            "compile_pass_count_is_diagnostic_only": migration.get("compile_pass_count"),
            "scratch_owner_emission_count": len(emitted_owners),
            "scratch_owner_emission_skips": dict(sorted(emit_skips.items())),
        },
        "groups": sorted(catalog_groups, key=lambda g: (g["address"] is None, g["address"] or "", g["members"])),
    }
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    exact = [g for g in output["groups"] if g["ownership_status"] == "single-source-definition-candidate"]
    md = [
        "# Whole-program state ownership inventory",
        "",
        "> Research inventory only; no state is admitted to production by this report.",
        "",
        f"Inputs: migration `{migration_hash}` and frozen symbols `{symbols_hash}`.",
        "",
        "The tool groups views by frozen segment:offset and follows retained alias history. It assigns an owner candidate only when a primitive complete declaration occurs in an actual DATA source TU. Generated object symbols, compilation, adjacency, and inferred capacities are not extent evidence.",
        "",
        "## Coverage",
        "",
        f"- Addressed groups: {output['summary']['addressed_groups']}",
        f"- Unlocated groups: {output['summary']['unlocated_groups']}",
        f"- Single exact primitive owner candidates: {len(exact)}",
        f"- Scratch BSS owners emitted with `--emit`: {len(emitted_owners)}",
        f"- Declaration views: {output['summary']['migration_declaration_view_count']}",
        f"- Frozen data symbols: {output['summary']['frozen_data_symbol_count']}",
        "",
        "## Exact primitive DATA owner candidates",
        "",
        "Each row is still a candidate for review, not an admission. Alias members share one address group and must not become duplicate runtime state.",
        "",
        "| Address | Names | Source definition | Type / exact extent |",
        "|---|---|---|---|",
    ]
    for g in exact:
        d = g["owner_candidates"][0]
        md.append(f"| `{g['address']}` | {', '.join('`'+n+'`' for n in g['members'][:5])}{' …' if len(g['members'])>5 else ''} | `{d['source']}:{d['line']}` | `{d['base_type']}` × {d['element_count']} = {d['extent_bytes']} bytes |")
    md += [
        "",
        "The optional `--emit` path writes a scratch-only native C owner file. It emits only zero/BSS integer objects with exact literal extents and same-address aliases. It skips nonzero or undecoded initializers; interior symbols stay unprovided. The emitted object is not safe to add beside current module objects where symbols are already defined. See the separate `build/workers/whole_program/state_owner_compile_diagnostic.json` for a GCC syntax compile and symbol-name intersection; it is not a whole-program link result.",
        "",
        "## Remaining ownership debt",
        "",
        "All other address groups are preserved in the JSON with their declaration views and concrete reason for unresolved ownership. Pointer and structure families require typed owners with source-defined lifetime/layout semantics. Primitive views with incomplete or nonliteral bounds remain unbounded. Signed byte/word interpretations are consumer views; raw bytes remain available when representation or endian matters.",
        "",
        "Regenerate with `python portable/whole_program/state_catalog.py`.",
        "",
    ]
    args.markdown.write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(output["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
