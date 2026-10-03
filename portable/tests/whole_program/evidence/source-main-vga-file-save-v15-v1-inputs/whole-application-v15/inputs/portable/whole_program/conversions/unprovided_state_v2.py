#!/usr/bin/env python3
"""Fail-closed converter for the provenance-reviewed whole-program state v2 plan.

This is a scratch conversion adapter, not build integration. It turns the
reviewed report into (1) exact identifier rename instructions, (2) pointer
table interior expressions, and (3) the byte-owner TU. It refuses stale or
structurally changed inputs and includes source-level positive/negative
controls for rewriting.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REPORT = ROOT / "portable/research/whole_program_unprovided_owners_v2.json"
DEFAULT_OUT = ROOT / "build/workers/whole_program/conversion_v2"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _identifier_rewrite(text: str, mapping: dict[str, str]) -> str:
    """Rewrite C identifiers only, leaving comments and literals byte-stable."""
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        if text.startswith("//", i):
            end = text.find("\n", i)
            if end < 0:
                out.append(text[i:])
                break
            out.append(text[i:end + 1])
            i = end + 1
            continue
        if text.startswith("/*", i):
            end = text.find("*/", i + 2)
            if end < 0:
                raise ValueError("unterminated block comment")
            out.append(text[i:end + 2])
            i = end + 2
            continue
        if text[i] in "\"'":
            quote = text[i]
            j = i + 1
            while j < n:
                if text[j] == "\\":
                    j += 2
                    continue
                if text[j] == quote:
                    j += 1
                    break
                j += 1
            if j > n or (j == n and text[j - 1] != quote):
                raise ValueError("unterminated C literal")
            out.append(text[i:j])
            i = j
            continue
        if text[i].isalpha() or text[i] == "_":
            j = i + 1
            while j < n and (text[j].isalnum() or text[j] == "_"):
                j += 1
            token = text[i:j]
            out.append(mapping.get(token, token))
            i = j
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def rewrite_source(text: str, report: dict[str, Any], source_path: str) -> str:
    """Apply report-backed aliases; pointer interiors require exact declaration removal."""
    expr_rows = [row for row in report["source_expression_aliases"]
                 if source_path in row["consumer_modules"]]
    table_owners = {row["owner"] for row in expr_rows}
    for row in expr_rows:
        name = row["name"]
        decl = re.compile(
            r"(?m)^[ \t]*extern[ \t]+char[ \t]+far[ \t]*\*[ \t]*far[ \t]+"
            + re.escape(name) + r"[ \t]*;[ \t]*(?:\r?\n|$)"
        )
        text, count = decl.subn("", text)
        if row["declaration_removal_required"] and count != 1:
            raise ValueError(f"expected exactly one standalone declaration for {name}; found {count}")
    # The consumer declares the real array owner as a scalar far pointer to its
    # first element. Remove that incompatible declaration and rewrite its uses
    # as [0], while table interior views remain [1]/[2] on the real array.
    mapping: dict[str, str] = {}
    for owner in table_owners:
        decl = re.compile(
            r"(?m)^[ \t]*extern[ \t]+char[ \t]+far[ \t]*\*[ \t]*far[ \t]+"
            + re.escape(owner) + r"[ \t]*;[ \t]*(?:\r?\n|$)"
        )
        text, count = decl.subn("", text)
        if count != 1:
            raise ValueError(f"expected exactly one scalar-owner declaration for {owner}; found {count}")
        mapping[owner] = f"{owner}[0]"
    mapping.update({row["name"]: row["expression"] for row in expr_rows})
    rewritten = _identifier_rewrite(text, mapping)
    return _identifier_rewrite(rewritten, report["rename_map"])


def emit_owner_source(report: dict[str, Any]) -> bytes:
    """Emit typed aliases while retaining the report-proved extents/shapes."""
    lines = ["/* Scratch owners from validated FAR_BSS integer common extents.",
             " * Converted diagnostic source; it is not selected by the production build. */",
             "#include <stdint.h>", ""]

    def c_type(row: dict[str, Any]) -> str:
        info = row["type"]
        base, width, signed = info["base"], info["bytes"], info["signedness"] == "signed"
        if base in {"char", "signed char", "unsigned char"}:
            if width != 1:
                raise ValueError(f"unsupported char width in {row}")
            return "int8_t" if signed else "uint8_t"
        if base in {"int", "unsigned int"}:
            if width not in (2, 4):
                raise ValueError(f"unsupported int width in {row}")
            return ("int" if signed else "uint") + str(width * 8) + "_t"
        if base in {"long", "unsigned long"}:
            if width not in (4, 8):
                raise ValueError(f"unsupported long width in {row}")
            return ("int" if signed else "uint") + str(width * 8) + "_t"
        raise ValueError(f"non-integer source view cannot be emitted: {row}")

    def suffix(row: dict[str, Any]) -> str:
        dims = row["view"]["dims"]
        if not dims:
            return ""
        return "".join(f"[{dim}]" for dim in dims)

    for group in sorted(report["bss_owner_candidates"],
                        key=lambda x: (x["address"], x["owner"])):
        owner = group["owner"]
        if group["decision"] != "validated-farbss-integer-common-owner-candidate":
            raise ValueError(f"unsafe owner decision for {owner}")
        if not group["historical_provenance"].get("no_pointer_or_struct_views"):
            raise ValueError(f"pointer/struct view present for {owner}")
        rows = group["assessment"]["view_rows"]
        views_by_name: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            views_by_name.setdefault(row["view"]["name"], []).append(row)
        owner_rows = views_by_name.get(owner)
        if not owner_rows:
            raise ValueError(f"source type/shape for owner {owner} is missing")
        owner_row = owner_rows[0]
        elem_bytes = owner_row["type"]["bytes"]
        dims = owner_row["view"]["dims"]
        if any(r["type"]["bytes"] != elem_bytes or r["view"]["dims"] != dims for r in rows):
            raise ValueError(f"views for {owner} no longer agree on typed shape/element width")
        extent = elem_bytes
        for dim in dims:
            # Dimensions are source C integer expressions already parsed by the
            # inventory; calculate only simple literal expressions for checking.
            if not re.fullmatch(r"[0-9]+(?:\s*\*\s*[0-9]+)*", dim):
                raise ValueError(f"unsupported nonliteral array extent for {owner}: {dim}")
            extent *= __import__("functools").reduce(
                lambda a, b: a * b,
                (int(piece.strip()) for piece in dim.split("*")), 1)
        if extent != group["owner_extent_bytes"]:
            raise ValueError(f"typed shape extent disagrees with FAR_BSS extent for {owner}")
        lines.append(f"{c_type(owner_row)} {owner}{suffix(owner_row)};")
        aliases = group.get("bss_aliases", group["unprovided_members"])
        for alias in aliases:
            if alias != owner:
                alias_rows = views_by_name.get(alias)
                if not alias_rows:
                    raise ValueError(f"source type/shape for alias {alias} is missing")
                alias_row = alias_rows[0]
                if c_type(alias_row) not in {c_type(x) for x in owner_rows} and alias_row["type"]["bytes"] != elem_bytes:
                    raise ValueError(f"alias view for {alias} has incompatible representation")
                if alias_row["view"]["dims"] != dims:
                    raise ValueError(f"alias view for {alias} has different array shape")
                lines.append(f'extern {c_type(alias_row)} {alias}{suffix(alias_row)} __attribute__((alias("{owner}")));')
        lines.append("")
    # The source emitter that produced the pinned report wrote text with the
    # host's Windows newline convention; preserve that exact emitted input.
    return "\r\n".join(lines).encode("utf-8")


def controls(report: dict[str, Any]) -> dict[str, Any]:
    names = report["rename_map"]
    sample = next(iter(names))
    sample_target = names[sample]
    source = (f"extern int {sample}; // {sample}\n"
              f'const char *s = "{sample}";\n'
              f"int value(void) {{ return {sample}; }}\n")
    renamed = _identifier_rewrite(source, names)
    pointer_rows = report["source_expression_aliases"]
    ptr = pointer_rows[0]
    consumer = ("".join(f"extern char far * far {row['name']};\n" for row in pointer_rows)
                + f"extern char far * far {ptr['owner']};\n"
                + "void f(void) { puts(" + pointer_rows[0]["name"] + "); puts("
                + pointer_rows[1]["name"] + "); db(" + ptr["owner"] + "); }\n")
    consumer_out = rewrite_source(consumer, report, ptr["consumer_modules"][0])
    missing_decl_rejected = False
    try:
        rewrite_source(f"extern int {sample};\n", report, ptr["consumer_modules"][0])
    except ValueError:
        missing_decl_rejected = True
    return {
        "positive": {
            "renames_code_identifier": f"return {sample_target};" in renamed,
            "preserves_comment_and_literal": f"// {sample}\n" in renamed and f'"{sample}"' in renamed,
            "removes_pointer_interior_declaration": f"extern char far * far {ptr['name']}" not in consumer_out,
            "rewrites_pointer_interior_to_indexed_expression": f"puts({ptr['expression']})" in consumer_out,
            "removes_scalar_owner_declaration": f"extern char far * far {ptr['owner']}" not in consumer_out,
            "rewrites_scalar_owner_to_first_element": f"db({ptr['owner']}[0])" in consumer_out,
            "keeps_interior_indexes_on_array_owner": all(
                f"puts({row['expression']})" in consumer_out for row in pointer_rows),
            "typed_owner_source_preserves_all_proved_extents": len(emit_owner_source(report)) > 0,
        },
        "negative": {
            "missing_interior_declaration_fails_closed": missing_decl_rejected,
            "does_not_create_pointer_interior_owner": all(
                row["name"] not in {g["owner"] for g in report["bss_owner_candidates"]}
                for row in pointer_rows),
            "does_not_duplicate_bss_addresses": len({g["address"] for g in report["bss_owner_candidates"]}) == len(report["bss_owner_candidates"]),
            "alias_targets_nonempty": all(bool(k) and bool(v) for k, v in names.items()),
        },
    }


def pinned_consumer_control(report: dict[str, Any]) -> dict[str, Any]:
    """Verify the real consumer source identity and its three rewritten uses."""
    rows = report["source_expression_aliases"]
    if not rows:
        raise ValueError("pointer-table expression inventory is empty")
    source_path = rows[0]["consumer_modules"][0]
    if any(source_path not in row["consumer_modules"] for row in rows):
        raise ValueError("pointer table aliases do not share one consumer source")
    manifest_pin = report["inputs"]["manifest"]
    manifest_path = ROOT / manifest_pin["path"]
    manifest_bytes = manifest_path.read_bytes()
    if sha(manifest_bytes) != manifest_pin["sha256"]:
        raise ValueError("frozen manifest changed since provenance report")
    manifest = json.loads(manifest_bytes)
    module = next((row for row in manifest["modules"].values()
                   if row.get("source") == source_path), None)
    if not module:
        raise ValueError(f"consumer source missing from frozen manifest: {source_path}")
    source_bytes = (ROOT / source_path).read_bytes()
    if sha(source_bytes) != module["source_sha256"]:
        raise ValueError(f"consumer source pin mismatch: {source_path}")
    rewritten = rewrite_source(source_bytes.decode("latin1"), report, source_path)
    owner = rows[0]["owner"]
    expected_indexed = all(f"printf({row['expression']});" in rewritten for row in rows)
    expected_first = f"f_205F_0004({owner}[0]);" in rewritten
    declarations_removed = all(
        f"extern char far * far {name};" not in rewritten
        for name in [owner, *(row["name"] for row in rows)])
    return {
        "source": source_path,
        "source_sha256": module["source_sha256"],
        "manifest_sha256": manifest_pin["sha256"],
        "positive": {"both_message_lookups_keep_correct_table_indices": expected_indexed,
                     "database_name_lookup_uses_element_zero": expected_first,
                     "all_scalar_interior_externs_removed": declarations_removed},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    raw = args.report.read_bytes()
    report = json.loads(raw)
    if report.get("schema") != "simant-whole-program-unprovided-state-provenance-v2":
        raise SystemExit("unexpected provenance report schema")
    if report.get("claim", "").find("does not wire state") < 0:
        raise SystemExit("report no longer states the diagnostic-only boundary")
    owner_source = emit_owner_source(report)
    check = controls(report)
    if not all(check[k][name] for k in check for name in check[k]):
        raise SystemExit(f"conversion controls failed: {check}")
    consumer_check = pinned_consumer_control(report)
    if not all(consumer_check["positive"].values()):
        raise SystemExit(f"pinned source conversion control failed: {consumer_check}")
    alias_map_text = json.dumps({
        "schema": "simant-whole-program-state-conversions-v2",
        "claim": "Diagnostic conversion instructions only; root-controlled source rewrite/build wiring is not performed.",
        "provenance_report": {"path": args.report.resolve().relative_to(ROOT).as_posix(), "sha256": sha(raw)},
        "token_renames": report["rename_map"],
        "source_expression_aliases": report["source_expression_aliases"],
        "pointer_table_owner_first_element_views": [
            {"name": owner, "expression": f"{owner}[0]",
             "consumer_modules": sorted({module for row in report["source_expression_aliases"]
                                          if row["owner"] == owner
                                          for module in row["consumer_modules"]}),
             "scalar_declaration_removal_required": True}
            for owner in sorted({row["owner"] for row in report["source_expression_aliases"]})
        ],
        "pinned_consumer_control": consumer_check,
        "prior_byte_owner_source": {"path": report["owner_source"]["path"],
                                    "sha256": report["owner_source"]["sha256"],
                                    "preserved": True},
        "typed_owner_source": {"path": (args.out_dir / "typed_owners.c").resolve().relative_to(ROOT).as_posix(),
                               "sha256": sha(owner_source)},
        "controls": check,
        "summary": {"token_renames": len(report["rename_map"]),
                    "source_expression_aliases": len(report["source_expression_aliases"]),
                    "bss_owners": len(report["bss_owner_candidates"]),
                    "owner_bytes": sum(x["owner_extent_bytes"] for x in report["bss_owner_candidates"])},
    }, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    if not args.check_only:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        (args.out_dir / "typed_owners.c").write_bytes(owner_source)
        (args.out_dir / "conversions.json").write_bytes(alias_map_text)
    print(json.dumps({"controls": check, "pinned_consumer_control": consumer_check,
                      "owner_sha256": sha(owner_source),
                      "conversion_sha256": sha(alias_map_text),
                      "summary": json.loads(alias_map_text)["summary"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
