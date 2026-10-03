#!/usr/bin/env python3
"""Translate a deliberately narrow set of PUBLIC initialized ASM scalars.

This is an exploratory whole-program provider generator, not part of the
production build.  It accepts only PUBLIC byte/word variables whose initializer
is a literal integer and whose computed DGROUP address matches both the frozen
symbol catalog and that module's accepted _DATA placement.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MIGRATION = ROOT / "build/workers/whole_program/generated/migration.json"
DEFAULT_OUTPUT = ROOT / "portable/whole_program/state/asm_shared_state"

# Reviewed scope: EMS scalar facts only. Pointer-bearing EMS state and unrelated
# graphics/font/audio/input data stay outside this provider.
REVIEWED_SCALARS = {
    "fd_55B3_360C": {"directive": "db", "ctype": "int8_t", "size": 1},
    "fd_55B3_3612": {"directive": "dw", "ctype": "int16_t", "size": 2},
    "fd_55B3_3614": {"directive": "dw", "ctype": "int16_t", "size": 2},
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def masm_int(token: str) -> int:
    token = token.strip()
    if re.fullmatch(r"(?:0[0-9A-F]+h|[0-9A-F]+h)", token, re.I):
        return int(token[:-1], 16)
    if re.fullmatch(r"\d+", token):
        return int(token, 10)
    raise ValueError(f"not a literal MASM integer: {token!r}")


def scan_data_declarations(text: str) -> list[dict]:
    """Read labelled declarations and address increments in _DATA only.

    The parser intentionally supports only the data syntax needed for this
    review. Unknown storage directives fail closed rather than guessing sizes.
    """
    rows: list[dict] = []
    in_data = False
    offset = 0
    public_names: set[str] = set()
    pending: list[dict] = []
    for lineno, original in enumerate(text.splitlines(), 1):
        line = original.split(";", 1)[0].strip()
        if not line:
            continue
        if re.match(r"^_DATA\s+segment\b", line, re.I):
            in_data = True
            continue
        if re.match(r"^_DATA\s+ends\b", line, re.I):
            in_data = False
            continue
        if not in_data:
            continue
        pm = re.match(r"^public\s+(.+)$", line, re.I)
        if pm:
            public_names.update(x.strip().lstrip("_") for x in pm.group(1).split(","))
            continue
        # Declaration line, with an optional leading label.
        dm = re.match(r"^(?:(\w+)\s+)?(db|dw|dd)\s+(.+)$", line, re.I)
        if dm:
            label, directive, operands = dm.groups()
            directive = directive.lower()
            operand = operands.strip()
            if label:
                pending.append({"name": label.lstrip("_"), "line": lineno,
                                "offset": offset, "directive": directive,
                                "operand": operand})
            # Count storage conservatively. This source contains a leading
            # byte string and then simple scalar directives before the targets.
            if directive == "db" and operand.startswith("'"):
                parts = re.findall(r"'([^']*)'|([^,]+)", operand)
                size = sum(len(a.encode("latin-1")) if a else 1
                           for a, b in parts if a or b.strip())
            elif re.fullmatch(r"\d+\s+dup\s*\(\s*0\s*\)", operand, re.I):
                count = int(re.match(r"\d+", operand).group())
                size = count * {"db": 1, "dw": 2, "dd": 4}[directive]
            else:
                vals = [v.strip() for v in operand.split(",")]
                # Only literal scalar storage affects our accepted offset path.
                # Symbolic values have known width but are not emitted as state.
                size = len(vals) * {"db": 1, "dw": 2, "dd": 4}[directive]
            offset += size
            rows.extend(pending)
            pending.clear()
            continue
        # An unlabelled data directive still contributes bytes to later offsets.
        um = re.match(r"^(db|dw|dd)\s+(.+)$", line, re.I)
        if um:
            directive, operand = um.groups()
            directive = directive.lower()
            operand = operand.strip()
            if directive == "db" and operand.startswith("'"):
                parts = re.findall(r"'([^']*)'|([^,]+)", operand)
                offset += sum(len(a.encode("latin-1")) if a else 1
                              for a, b in parts if a or b.strip())
            elif re.fullmatch(r"\d+\s+dup\s*\(\s*0\s*\)", operand, re.I):
                offset += int(re.match(r"\d+", operand).group()) * {"db": 1, "dw": 2, "dd": 4}[directive]
            else:
                offset += len(operand.split(",")) * {"db": 1, "dw": 2, "dd": 4}[directive]
            continue
        if re.match(r"^\w+\s+equ\b|^\w+\s+label\b|^extrn\b", line, re.I):
            continue
        # Align/other data syntax is intentionally not guessed.
        raise ValueError(f"unsupported _DATA statement at line {lineno}: {line}")
    for row in rows:
        row["public"] = row["name"] in public_names
    return rows


def collect(migration_path: Path, *, asm_text: str | None = None,
            manifest: dict | None = None, symbols: dict | None = None) -> list[dict]:
    migration = json.loads(migration_path.read_text(encoding="utf-8")) if migration_path.exists() else {}
    if manifest is None:
        manifest = json.loads((ROOT / "layout/manifest.json").read_text(encoding="utf-8"))["modules"]
    if symbols is None:
        symbols = json.loads((ROOT / "layout/symbols.json").read_text(encoding="utf-8"))["data"]
    if asm_text is None:
        asm_text = (ROOT / "src/root/m195A.asm").read_text(encoding="utf-8")
    contracts = migration.get("unprovided_symbol_contracts", {})
    mod = manifest.get("root:195A")
    if not mod or mod.get("lang") != "asm" or mod.get("source") != "src/root/m195A.asm":
        raise ValueError("root:195A is not the accepted source-backed ASM module")
    placement = mod.get("placements", {}).get("_DATA")
    if not placement:
        raise ValueError("root:195A lacks accepted _DATA placement")
    rows = scan_data_declarations(asm_text)
    by_name = {row["name"]: row for row in rows}
    output = []
    for name, spec in REVIEWED_SCALARS.items():
        contract = contracts.get(name)
        if not contract or contract.get("classification") != "GLOBAL_STATE":
            raise ValueError(f"{name} is not currently an unprovided GLOBAL_STATE contract")
        decl = by_name.get(name)
        if not decl or not decl["public"]:
            raise ValueError(f"{name} has no PUBLIC _DATA declaration")
        if decl["directive"] != spec["directive"]:
            raise ValueError(f"{name}: expected {spec['directive']}, found {decl['directive']}")
        value = masm_int(decl["operand"])
        if value != 0:
            raise ValueError(f"{name}: reviewed initializer changed from literal zero")
        address = [placement["seg"], placement["off"] + decl["offset"]]
        expected = symbols.get(name)
        if expected is None or [expected["seg"], expected["off"]] != address:
            raise ValueError(f"{name}: source-derived address {address} disagrees with accepted PUBLIC address")
        views = contract.get("source_views", [])
        if not views or any(view.get("layout_address") != address for view in views):
            raise ValueError(f"{name}: migration source views disagree with accepted address")
        output.append({"name": name, **spec, "initial_value": value,
                       "source": "src/root/m195A.asm", "source_line": decl["line"],
                       "module": "root:195A", "public": True,
                       "computed_address": address, "size": spec["size"],
                       "initializer": decl["operand"]})
    return output


def render_header(rows: list[dict]) -> str:
    declarations = "\n".join(f"extern {r['ctype']} {r['name']};" for r in rows)
    return ("/* Generated by portable/tools/asm_state_provider.py; diagnostic-only. */\n"
            "#ifndef SIMANT_ASM_SHARED_STATE_H\n#define SIMANT_ASM_SHARED_STATE_H\n"
            "#include <stdint.h>\n"
            "_Static_assert(sizeof(int8_t) == 1, \"8-bit state\");\n"
            "_Static_assert(sizeof(int16_t) == 2, \"DOS word state\");\n"
            f"{declarations}\n#endif\n")


def render_source(rows: list[dict]) -> str:
    definitions = "\n".join(f"{r['ctype']} {r['name']} = ({r['ctype']}){r['initial_value']};"
                             for r in rows)
    return ("/* Source-derived scalar initializers from root:m195A _DATA. */\n"
            "#include \"asm_shared_state.h\"\n"
            f"{definitions}\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--migration", type=Path, default=DEFAULT_MIGRATION)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    rows = collect(args.migration)
    expected = {args.out.with_suffix(".h"): render_header(rows),
                args.out.with_suffix(".c"): render_source(rows)}
    if args.check:
        for path, text in expected.items():
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                raise SystemExit(f"provider output stale: {path}")
    else:
        for path, text in expected.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps({"provider_state_count": len(rows), "states": [r["name"] for r in rows]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
