#!/usr/bin/env python3
"""Resolve proven C DATA aliases without creating second storage owners.

The aliases here are DOS public address views over initialized canonical C
objects.  This diagnostic transform rewrites extern views/references toward
the canonical owner; it does not edit the whole-program generator or any source.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "build/workers/whole_program/generated/migration.json"
SYMBOLS = ROOT / "layout/symbols.json"
MANIFEST = ROOT / "layout/manifest.json"
M0250 = ROOT / "src/root/m0250.c"
M15F8 = ROOT / "src/root/m15F8.c"

SCALAR_ALIASES = {
    "fd_55B3_19C0": ("g_19C0", "int", "root:0250", 6592),
    "fd_55B3_19C6": ("g_19C6", "char *", "root:0250", 6598),
    "fd_55B3_19CA": ("g_19CA", "long", "root:0250", 6602),
    "fd_55B3_19CE": ("g_19CE", "int", "root:0250", 6606),
}
POINTER_TABLE = "fd_55B3_1CD4"
POINTER_ALIASES = {
    f"fd_55B3_{0x1CD4 + 4 * i:04X}": i for i in (3, 4)
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _masked_code(source: str) -> str:
    """Blank comments and literals while retaining offsets/newlines."""
    out = list(source)
    i = 0
    while i < len(source):
        if source.startswith("//", i):
            j = source.find("\n", i)
            j = len(source) if j < 0 else j
            for k in range(i, j): out[k] = " "
            i = j
        elif source.startswith("/*", i):
            j = source.find("*/", i + 2)
            j = len(source) if j < 0 else j + 2
            for k in range(i, j):
                if source[k] != "\n": out[k] = " "
            i = j
        elif source[i] in {'"', "'"}:
            quote = source[i]
            j = i + 1
            while j < len(source):
                if source[j] == "\\": j += 2; continue
                if source[j] == quote: j += 1; break
                j += 1
            for k in range(i, min(j, len(source))):
                if source[k] != "\n": out[k] = " "
            i = j
        else:
            i += 1
    return "".join(out)


def collect_aliases() -> list[dict]:
    migration = json.loads(MIGRATION.read_text(encoding="utf-8"))
    symbols = json.loads(SYMBOLS.read_text(encoding="utf-8"))["data"]
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))["modules"]
    contracts = migration["unprovided_symbol_contracts"]
    source = M0250.read_text(encoding="utf-8")
    expected_globals = {
        "g_19BE": ("int", "16", 2), "g_19C0": ("int", "16", 2),
        "g_19C6": ("char far *", "0", 4), "g_19CA": ("long", "0", 4),
        "g_19CE": ("int", "1", 2),
    }
    decls = {}
    data_offset = 6590
    # These declarations begin the accepted DOS _DATA block. Count DOS widths;
    # far pointers occupy four bytes even though the native build uses host ptrs.
    for line in source.splitlines():
        match = re.match(r"\s*(int|long|char\s+far\s*\*)\s*(g_19\w+)\s*=\s*([^;]+);", line)
        if not match:
            if decls:
                break
            continue
        ctype, name, init = match.groups()
        ctype = " ".join(ctype.split())
        width = 4 if ctype in {"long", "char far *"} else 2
        decls[name] = {"type": ctype, "initializer": init.strip(),
                       "offset": data_offset, "width": width}
        data_offset += width
    data_place = manifest["root:0250"]["placements"]["_DATA"]
    if data_place["seg"] != 21939 or data_place["off"] != 6590:
        raise ValueError("root:0250 canonical DATA placement changed")
    output = []
    for alias, (canonical, ctype, module, off) in SCALAR_ALIASES.items():
        contract = contracts.get(alias)
        if not contract or contract.get("classification") != "GLOBAL_STATE":
            raise ValueError(f"{alias} is not a current missing GLOBAL_STATE alias")
        sym = symbols.get(alias)
        if not sym or [sym["seg"], sym["off"]] != [data_place["seg"], off]:
            raise ValueError(f"{alias}: source/accepted address mismatch")
        if any(v.get("layout_address") != [data_place["seg"], off]
               for v in contract.get("source_views", [])):
            raise ValueError(f"{alias}: migration view address mismatch")
        ctype_expected, init_expected, width_expected = expected_globals[canonical]
        decl = decls.get(canonical)
        if not decl or (decl["type"], decl["initializer"], decl["width"]) != (
                ctype_expected, init_expected, width_expected):
            raise ValueError(f"canonical source definition changed: {canonical}")
        if decl["offset"] != off:
            raise ValueError(f"canonical source declaration offset changed: {canonical}")
        module_row = next((r for r in migration["modules"] if r["source"] == "src/root/m0250.c"), None)
        if not module_row or not any(s.get("name") == canonical and s.get("kind") in {"D", "B"}
                                     for s in module_row.get("object_symbols", [])):
            raise ValueError(f"canonical generated object symbol absent: {canonical}")
        output.append({"alias": alias, "canonical": canonical, "kind": "scalar-lvalue",
                       "type": ctype, "initializer": decl["initializer"],
                       "address": [sym["seg"], sym["off"]], "canonical_module": module,
                       "canonical_offset": off, "storage_owner": canonical})

    ptr_source = M15F8.read_text(encoding="utf-8")
    table_match = re.search(r"(?s)char\s+far\s*\*\s*(fd_55B3_1CD4)\s*\[\s*\]\s*=\s*\{(.*?)\};", ptr_source)
    if not table_match:
        raise ValueError("canonical initialized pointer table declaration absent")
    table_items = re.findall(r'"(?:\\.|[^"\\])*"', table_match.group(2))
    if len(table_items) != 5:
        raise ValueError(f"expected five source string pointers, found {len(table_items)}")
    base = symbols.get(POINTER_TABLE)
    if not base:
        raise ValueError("pointer table lacks accepted source PUBLIC/address")
    owner_row = next((r for r in migration["modules"] if r["source"] == "src/root/m15F8.c"), None)
    if not owner_row or not any(s.get("name") == POINTER_TABLE and s.get("kind") in {"D", "R"}
                                for s in owner_row.get("object_symbols", [])):
        raise ValueError("canonical pointer table has no generated C DATA owner")
    output.append({"alias": POINTER_TABLE, "canonical": f"{POINTER_TABLE}[0]",
                   "kind": "pointer-table-element", "type": "char *",
                   "initializer": table_items[0], "address": [base["seg"], base["off"]],
                   "canonical_module": "root:15F8", "canonical_offset": base["off"],
                   "storage_owner": POINTER_TABLE, "index": 0,
                   "status": "accepted-base-view-type-reconciliation"})
    for alias, index in POINTER_ALIASES.items():
        contract = contracts.get(alias)
        sym = symbols.get(alias)
        expected_address = [base["seg"], base["off"] + index * 4]
        if contract is None:
            raise ValueError(f"{alias} is not a current missing GLOBAL_STATE alias")
        if contract.get("classification") != "GLOBAL_STATE":
            raise ValueError(f"{alias} is not a current missing GLOBAL_STATE alias")
        if not sym or [sym["seg"], sym["off"]] != expected_address:
            raise ValueError(f"{alias}: pointer slot does not match accepted address")
        if any(v.get("layout_address") != expected_address
               for v in contract.get("source_views", [])):
            raise ValueError(f"{alias}: migration view address mismatch")
        output.append({"alias": alias, "canonical": f"{POINTER_TABLE}[{index}]",
                       "kind": "pointer-table-element", "type": "char *",
                       "initializer": table_items[index], "address": expected_address,
                       "canonical_module": "root:15F8", "canonical_offset": expected_address[1],
                       "storage_owner": POINTER_TABLE, "index": index})
    return output


def transform(source: str, aliases: list[dict]) -> tuple[str, dict]:
    """Rename prototypes and uses; do not alter control/dataflow statements."""
    scalar = {row["alias"]: row["canonical"] for row in aliases
              if row["kind"] == "scalar-lvalue"}
    pointer = {row["alias"]: row["index"] for row in aliases
               if row["kind"] == "pointer-table-element"}
    all_aliases = {**scalar, **pointer}
    masked = _masked_code(source)
    removed_or_rewritten = []
    # Convert each external alias declaration to the actual owning declaration.
    for alias in sorted(all_aliases, key=len, reverse=True):
        for match in list(re.finditer(rf"(?m)^([^\n;]*\bextern\b[^\n;]*\b{re.escape(alias)}\b[^\n;]*);", masked)):
            original = source[match.start():match.end()]
            if alias in pointer:
                replacement = f"extern char * {POINTER_TABLE}[];"
            else:
                replacement = re.sub(rf"\b{re.escape(alias)}\b", scalar[alias], original)
            source = source[:match.start()] + replacement + source[match.end():]
            masked = _masked_code(source)
            removed_or_rewritten.append({"alias": alias, "operation": "canonical-extern-view"})
    # Rename identifier tokens only (strings, comments, and transformed extern
    # declarations are preserved). This avoids turning the canonical array
    # prototype itself into an invalid element prototype.
    for alias in sorted(all_aliases, key=len, reverse=True):
        replacement = (f"({POINTER_TABLE}[{pointer[alias]}])" if alias in pointer
                       else scalar[alias])
        masked = _masked_code(source)
        spans = []
        for m in re.finditer(rf"\b{re.escape(alias)}\b", masked):
            line_start = masked.rfind("\n", 0, m.start()) + 1
            line_end = masked.find("\n", m.end())
            line_end = len(masked) if line_end < 0 else line_end
            if re.search(r"\bextern\b", masked[line_start:line_end]):
                continue
            if alias == POINTER_TABLE and re.match(r"\s*\[", masked[m.end():]):
                # whole-program's source-table lowering has already made this
                # a canonical table element expression; do not turn [i] into
                # element-zero followed by a character subscript.
                continue
            spans.append((m.start(), m.end()))
        for start, end in reversed(spans):
            source = source[:start] + replacement + source[end:]
        if spans:
            removed_or_rewritten.append({"alias": alias, "operation": "canonical-reference",
                                         "count": len(spans)})
    return source, {"rewrites": removed_or_rewritten,
                    "control_flow_preserved": True,
                    "storage_owners_created": 0}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", type=Path)
    args = ap.parse_args()
    rows = collect_aliases()
    report = {"schema": "simant-source-state-aliases-v1", "claim": "DIAGNOSTIC_ONLY",
              "alias_count": len(rows), "storage_owner_count": len({r['storage_owner'] for r in rows}),
              "aliases": rows}
    text = json.dumps(report, indent=2) + "\n"
    if args.inventory:
        args.inventory.parent.mkdir(parents=True, exist_ok=True)
        args.inventory.write_text(text, encoding="utf-8", newline="\n")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
