#!/usr/bin/env python3
"""Independent source audit and scratch SOURCE_ONLY_DOS probe for history scalars.

The only generated files are kept under build/workers/dos_history_scalar_words_v21.
No original executable, object, or data bytes are inputs. This is a candidate
source-functional owner only; it does not claim historical COMDEF ownership.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def find_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "layout" / "manifest.json").is_file():
            return candidate
    raise RuntimeError("cannot locate repository root")


ROOT = find_root()
OUT = ROOT / "build/workers/dos_history_scalar_words_v21"
RUNTIME = OUT / "runtime"
FIXTURES = RUNTIME / "fixtures"
REPORT = OUT / "report-v21.json"
AUDIT = OUT / "source-audit-v21.json"
PROVIDER = OUT / "history-scalar-state.c"
PROFILE = "msc600ax"
PROVIDER_FLAGS = ["/AL", "/Os", "/Gs"]
CONSUMER_FLAGS = ["/AL", "/Os", "/Zi"]
FAMILY_ID = "history_reset_scalars"
SAVE_SOURCE = "src/S09/m35F5.c"
OWNER_SOURCE = "src/S24/m39C7.c"
SAVE_ARRAY = "fd_4E4B_0000"
MUTABLE_OBSERVATIONS = (
    "build/source-only-dos/build-report.json",
    "work/source-only-dos/current-intake.json",
    "tools/source_only_dos.py",
    "tools/dos_source_bindings.py",
)

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "tools"))
import compiler  # noqa: E402
import csrc  # noqa: E402
import dos_source_bindings as bindings  # noqa: E402
import source_only_dos as dos  # noqa: E402
from omf import OmfReader  # noqa: E402

compiler.WORK = RUNTIME / "compiler-work"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin(path: Path, expected: str | None = None) -> dict:
    path = path.resolve()
    raw, identity = dos.pin(path, expected)
    try:
        label = path.relative_to(ROOT).as_posix()
    except ValueError:
        label = str(path).replace("\\", "/")
    return {"path": label, "sha256": identity["sha256"], "size": identity["size"]}


def read_json(path: Path, expected: str | None = None):
    raw, identity = dos.pin(path, expected)
    return json.loads(raw.decode("utf-8")), identity


def project_path(path: str) -> Path:
    return ROOT / path.replace("\\", "/")


def mask_comments_literals(text: str) -> str:
    rx = re.compile(r"/\*.*?\*/|//[^\n]*|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'", re.S)
    return rx.sub(lambda m: "".join("\n" if c == "\n" else " " for c in m.group(0)), text)


def mask_source_comments(text: str, source_path: str) -> str:
    masked = mask_comments_literals(text)
    if source_path.lower().endswith(".asm"):
        # MASM uses ';' line comments. Quoted strings and character literals
        # have already been blanked while preserving line positions.
        masked = re.sub(r";[^\n]*", lambda m: " " * len(m.group(0)), masked)
    return masked


def line_function_ranges(text: str):
    try:
        src = csrc.Source(text)
        return sorted((fn.s, fn.e, fn.name) for fn in src.functions())
    except Exception:
        return []


def source_rows(intake_path: Path, index_path: Path):
    intake, intake_pin = read_json(intake_path)
    canonical = []
    for tu in intake["translation_units"]:
        source = tu["source"]
        path = source["path"].replace("\\", "/")
        receipt = pin(project_path(path), source["sha256"])
        if receipt["size"] != source["size"]:
            raise RuntimeError("canonical source size changed: " + path)
        canonical.append(receipt | {"module": tu["module"], "set": "canonical_127",
                                    "role": "canonical manifest TU"})
    if len(canonical) != 127:
        raise RuntimeError(f"expected 127 canonical TUs, got {len(canonical)}")

    index, index_pin = read_json(index_path)
    if index.get("schema") != "simant-dos-strict-static-index-v1" or len(index.get("entries", {})) != 29:
        raise RuntimeError("expected the pinned 29-entry strict-effective index")
    effective = []
    receipt_pins = []
    for function, reference in sorted(index["entries"].items()):
        receipt_path = project_path(reference["path"])
        receipt = pin(receipt_path, reference["sha256"])
        receipt_pins.append(receipt)
        receipt_data, _ = read_json(receipt_path, reference["sha256"])
        selected = receipt_data.get("registered_source", {})
        role = "registered effective whole module"
        if function == "DrawBalloons":
            selected = receipt_data.get("audit", {}).get("source", {})
            role = "corrected effective whole module"
        if not selected.get("whole_module") or not selected.get("path"):
            raise RuntimeError("missing complete effective module source: " + function)
        path = selected["path"].replace("\\", "/")
        source_receipt = pin(project_path(path), selected["sha256"])
        effective.append(source_receipt | {"module": selected.get("module"),
                                           "function": function,
                                           "set": "effective_strict_29", "role": role})
    if len(effective) != 29:
        raise RuntimeError(f"expected 29 strict-effective sources, got {len(effective)}")
    unique = {}
    for row in canonical + effective:
        old = unique.get(row["path"])
        if old and old["sha256"] != row["sha256"]:
            raise RuntimeError("source path has conflicting hashes: " + row["path"])
        unique.setdefault(row["path"], row)
    rows = sorted(unique.values(), key=lambda row: row["path"])
    if len(rows) != 156:
        raise RuntimeError(f"expected 156 unique graph sources, got {len(rows)}")
    return rows, {"canonical_127": canonical, "effective_strict_29": effective}, [
        intake_pin, index_pin, *receipt_pins]


def aliases_for_target(name: str, offset: int, symbols: dict, alias_map: dict):
    aliases = {name}
    exact = []
    for table in ("data", "code"):
        for candidate, row in symbols.get(table, {}).items():
            if row.get("seg") == 0x50F6 and row.get("off") == offset:
                aliases.add(candidate)
                exact.append({"table": table, "name": candidate,
                              "seg": row.get("seg"), "off": row.get("off"),
                              "alias_of": row.get("alias_of")})
    for old, target in alias_map.items():
        if target == name:
            aliases.add(old)
    return sorted(aliases), exact


def classify_identifier(line: str, name: str, save_rows: set[tuple[str, int]],
                         path: str, line_no: int, in_asm: bool) -> str:
    q = re.escape(name)
    lhs = r"\b" + q + r"\b(?:\s*(?:\[[^\]]+\]|\.\w+|->\w+))*"
    if re.search(r"(?:\+\+|--)\s*" + lhs + r"|" + lhs + r"\s*(?:\+\+|--)", line):
        return "read_modify_write_increment"
    if re.search(lhs + r"\s*(?:[+*/%&|^\-]?=)(?!=)", line):
        return "write_assignment"
    if re.search(r"(?<!&)&(?!&)\s*" + q + r"\b", line):
        if (path, line_no) in save_rows:
            return "SaveRec_raw_byte_address_view"
        return "non_SaveRec_address_escape"
    if re.match(r"\s*(?:extern|static|typedef)\b", line):
        return "declaration_view"
    if re.search(r"\b" + q + r"\s*(?:\[|\.|->)", line):
        return "array_or_aggregate_view"
    if in_asm:
        return "assembly_symbol_reference"
    return "read_or_expression"


HEX_LITERAL = re.compile(r"(?<![A-Za-z0-9_])(?:0[xX]([0-9A-Fa-f]+)|([0-9A-Fa-f]+)[hH])(?![A-Za-z0-9_])")
DEC_LITERAL = re.compile(r"(?<![A-Za-z0-9_])([0-9]{3,5})(?![A-Za-z0-9_])")
ASM_WORDS = re.compile(r"\b(?:mov|lea|push|pop|call|jmp|j[a-z]{1,3}|cmp|test|and|or|xor|inc|dec|int|retf?|retn|les|lds)\b", re.I)


def in_assembly_lines(code_lines: list[str], source_path: str):
    result = []
    active_depth = 0
    for line_no, line in enumerate(code_lines, 1):
        if source_path.lower().endswith(".asm"):
            result.append(True)
            continue
        start = bool(re.search(r"\b_?asm\b", line, re.I))
        if active_depth or start:
            result.append(True)
            active_depth += line.count("{") - line.count("}")
            if active_depth <= 0:
                active_depth = 0
            continue
        # MASM instruction lines are relevant in a C file only if the file uses
        # a source-line assembler construct; do not label C calls as assembly.
        result.append(False)
    return result


def save_rows_by_target(save_text: str, target_names: set[str]):
    lines = save_text.splitlines()
    start = next((i for i, line in enumerate(lines, 1)
                  if re.match(r"\s*struct\s+SaveRec\s+far\s+" + SAVE_ARRAY + r"\s*\[", line)), None)
    if start is None:
        raise RuntimeError("could not find the canonical SaveRec table start")
    rows = {name: [] for name in target_names}
    seen_rows = []
    initializer_count = 0
    unparsed_initializers = []
    table_open = False
    for line_no in range(start, len(lines) + 1):
        line = lines[line_no - 1]
        if line_no == start:
            table_open = "{" in line
            continue
        if not table_open:
            if "{" in line:
                table_open = True
            continue
        if re.match(r"\s*\{\s*0\s*,\s*0\s*,\s*0\s*\}", line):
            break
        if "};" in line:
            break
        if re.match(r"\s*\{", line):
            initializer_count += 1
        m = re.fullmatch(r"\s*\{\s*(\d+)\s*,\s*(\d+)\s*,\s*\(void\s+far\s+\*\)\s*&([A-Za-z_]\w*)\s*\},?\s*", line)
        if m:
            size, count, name = int(m.group(1)), int(m.group(2)), m.group(3)
            # This source's table index is the one-based source row position
            # (initializer line minus the pinned declaration line); the
            # mechanical v20 inventory records the same convention.
            row = {"source": SAVE_SOURCE, "line": line_no, "table_index_1based": line_no - start,
                   "text": line.strip(), "size": size, "count": count,
                   "serialized_bytes": size * count, "target": name}
            seen_rows.append(row)
            if name in rows:
                rows[name].append(row)
        elif re.match(r"\s*\{", line):
            unparsed_initializers.append({"line": line_no, "text": line.strip()})
    return start, rows, seen_rows, initializer_count, unparsed_initializers


def owned_intervals(current_intake: dict, history_bindings: dict,
                    spider_bindings: dict):
    rows = []
    def visit(value, source):
        if isinstance(value, dict):
            addr = value.get("historical_address")
            length = value.get("length")
            if (isinstance(addr, list) and len(addr) == 2 and
                    isinstance(addr[0], int) and isinstance(addr[1], int) and
                    isinstance(length, int) and length > 0):
                rows.append({"source": source, "name": value.get("name") or value.get("symbol"),
                             "seg": addr[0], "off": addr[1], "length": length})
            for child in value.values():
                visit(child, source)
        elif isinstance(value, list):
            for child in value:
                visit(child, source)
    for field in ("source_owned_far_scalars", "source_owned_history_arrays",
                  "source_owned_water_arrays", "source_owned_far_data"):
        if field in current_intake:
            visit(current_intake[field], "current-intake:" + field)
    visit(history_bindings, "history-storage-bindings-v1.json")
    visit(spider_bindings, "spider-counter-bindings-v1.json")
    # The review table remains an independent exclusion receipt if bindings
    # encode a target by symbol rather than historical_address.
    spider_addresses = {
        "DeathCnt": 0x109A, "EatCnt": 0x1054, "SCorpseBase": 0x105A,
        "Scycle": 0x1042, "Scycle2": 0x1072, "SpidBurpCnt": 0x1076,
        "SpidRevenge": 0x108A,
    }
    rows.extend({"source": "spider-counter-review-v1.md", "name": name,
                 "seg": 0x50F6, "off": off, "length": 2}
                for name, off in spider_addresses.items())
    return rows


def numeric_candidates(source_rows, source_cache, target_offsets):
    out = {offset: [] for offset in target_offsets}
    for source in source_rows:
        path = source["path"]
        code = source_cache[path]["masked"]
        lines = code.splitlines()
        original = source_cache[path]["text"].splitlines()
        asm_flags = source_cache[path]["asm_lines"]
        for line_no, line in enumerate(lines, 1):
            nums = []
            for m in HEX_LITERAL.finditer(line):
                token = m.group(1) or m.group(2)
                nums.append((int(token, 16), token, "hex"))
            for m in DEC_LITERAL.finditer(line):
                nums.append((int(m.group(1), 10), m.group(1), "decimal"))
            for value, token, notation in nums:
                if value not in out:
                    continue
                original_line = original[line_no - 1].strip() if line_no <= len(original) else ""
                asm = asm_flags[line_no - 1] if line_no <= len(asm_flags) else path.lower().endswith(".asm")
                colon_pair = bool(re.search(r"(?:50F6[hH]?\s*:\s*(?:0[xX])?0*" + format(value, "x") + r"[hH]?)|(?:0[xX]50F6\s*:\s*0[xX]?0*" + format(value, "x") + r")", line, re.I))
                memory_shape = bool(re.search(r"\b(?:es|ds|cs|ss)\s*:|\[[^\]]*\]|\b(?:MK_FP|FP_SEG|FP_OFF)\b|\b(?:far|huge)\s*\*", line, re.I))
                if colon_pair:
                    category = "explicit_50F6_far_address_candidate"
                elif asm and memory_shape:
                    category = "assembly_numeric_address_or_displacement_candidate"
                elif memory_shape:
                    category = "C_numeric_pointer_or_index_candidate"
                elif asm:
                    category = "assembly_numeric_literal_value_match"
                else:
                    category = "numeric_literal_value_match_only"
                # The numeric token's position, rather than its value, selects
                # the enclosing C function.
                token_match = next((m for m in HEX_LITERAL.finditer(line)
                                    if (m.group(1) or m.group(2)) == token), None)
                if notation == "decimal":
                    token_match = next((m for m in DEC_LITERAL.finditer(line)
                                        if m.group(1) == token), token_match)
                absolute_pos = sum(len(x) + 1 for x in lines[:line_no - 1]) + (token_match.start() if token_match else 0)
                out[value].append({"set": source["set"], "path": path, "module": source.get("module"),
                                   "function": next((name for lo, hi, name in source_cache[path]["functions"]
                                                     if lo <= absolute_pos < hi), None),
                                   "line": line_no, "literal": token, "notation": notation,
                                   "classification": category, "assembly_context": asm,
                                   "text": original_line})
    return out


def audit_sources(rows, family, symbols, current_intake, old_history_bindings,
                  spider_bindings, current_unresolved):
    save_path = ROOT / SAVE_SOURCE
    save_text = save_path.read_text(encoding="latin1")
    member_names = [m["exact_base_aliases"][0] for m in family["members"]]
    name_to_member = {n: m for n, m in zip(member_names, family["members"])}
    (save_start, save_rows, all_save_rows, save_initializer_count,
     unparsed_save_initializers) = save_rows_by_target(save_text, set(member_names))
    save_line_keys = {(SAVE_SOURCE, r["line"]) for rowset in save_rows.values() for r in rowset}
    address_to_member = {tuple(map(lambda x: int(x, 16), m["address"].split(":"))): m
                         for m in family["members"]}

    alias_map = dos.identifier_aliases(symbols)
    aliases = {}
    exact_registry = {}
    for name, member in name_to_member.items():
        seg, off = tuple(int(x, 16) for x in member["address"].split(":"))
        aliases[name], exact_registry[name] = aliases_for_target(name, off, symbols, alias_map)

    source_cache = {}
    source_receipts = []
    for row in rows:
        path = row["path"]
        if path in source_cache:
            continue
        raw, actual = dos.pin(project_path(path), row["sha256"])
        text = raw.decode("latin1")
        masked = mask_source_comments(text, path)
        source_cache[path] = {"text": text, "masked": masked,
                              "functions": line_function_ranges(text),
                              "asm_lines": in_assembly_lines(masked.splitlines(), path)}
        source_receipts.append({"path": path, "sha256": actual["sha256"], "size": actual["size"],
                                "module": row.get("module"), "set": row["set"],
                                "role": row.get("role"), "function": row.get("function")})

    refs = {name: [] for name in member_names}
    for source in rows:
        path = source["path"]
        cache = source_cache[path]
        lines = cache["masked"].splitlines()
        original = cache["text"].splitlines()
        for name in member_names:
            for spelling in aliases[name]:
                token = re.compile(r"\b" + re.escape(spelling) + r"\b")
                for match in token.finditer(cache["masked"]):
                    line_no = cache["masked"].count("\n", 0, match.start()) + 1
                    code_line = lines[line_no - 1] if line_no <= len(lines) else ""
                    original_line = original[line_no - 1].strip() if line_no <= len(original) else ""
                    asm = cache["asm_lines"][line_no - 1] if line_no <= len(cache["asm_lines"]) else path.lower().endswith(".asm")
                    function = next((fn for lo, hi, fn in cache["functions"]
                                     if lo <= match.start() < hi), None)
                    mode = classify_identifier(code_line, spelling, save_line_keys, path, line_no, asm)
                    refs[name].append({"set": source["set"], "path": path, "module": source.get("module"),
                                       "function": function, "line": line_no, "spelling": spelling,
                                       "access": mode, "assembly_context": asm, "text": original_line})

    numeric = numeric_candidates(rows, source_cache,
                                 {int(m["address"].split(":")[1], 16) for m in family["members"]})
    owned = owned_intervals(current_intake, old_history_bindings, spider_bindings)

    members = []
    for member in family["members"]:
        name = member["exact_base_aliases"][0]
        seg, off = (int(x, 16) for x in member["address"].split(":"))
        type_decl = member["typed_declaration_forms"]
        size = member["complete_view_bytes"][0]
        rows_for_name = save_rows[name]
        if len(rows_for_name) != 1:
            raise RuntimeError(f"{name}: expected exactly one direct SaveRec row, got {len(rows_for_name)}")
        sr = rows_for_name[0]
        if sr["serialized_bytes"] != size or sr["count"] != 1:
            raise RuntimeError(f"{name}: SaveRec {sr['size']}x{sr['count']} differs from typed {size}-byte scalar")
        expected_v20 = member["save_rec_count_pairs"]
        if (len(expected_v20) != 1 or expected_v20[0]["line"] != sr["line"] or
                expected_v20[0]["table_index"] != sr["table_index_1based"]):
            raise RuntimeError(f"{name}: independently parsed SaveRec row differs from v20 shortlist: "
                               f"prior={expected_v20!r}, parsed={sr!r}")
        exact = [row for row in exact_registry[name]]
        interiors = []
        for table in ("data", "code"):
            for candidate, row in symbols.get(table, {}).items():
                if row.get("seg") == seg and off < row.get("off", -1) < off + size:
                    interiors.append({"table": table, "name": candidate, "offset": row["off"],
                                      "delta": row["off"] - off})
        is_owned = []
        for owner in owned:
            if owner.get("seg") == seg and off < owner.get("off", -1) + owner.get("length", 0) and owner.get("off", 0) < off + size:
                is_owned.append(owner)
        unresolved_match = any(
            (str(row.get("name", "")).lstrip("_@") == name or
             (row.get("registry") or {}).get("seg") == seg and
             (row.get("registry") or {}).get("off") == off)
            for row in current_unresolved)
        all_refs = sorted(refs[name], key=lambda r: (r["set"], r["path"], r["line"], r["spelling"]))
        escapes = [r for r in all_refs if r["access"] in ("SaveRec_raw_byte_address_view", "non_SaveRec_address_escape")]
        non_save_escapes = [r for r in escapes if r["access"] == "non_SaveRec_address_escape"]
        producers = [r for r in all_refs if r["access"] in ("write_assignment", "read_modify_write_increment")]
        consumers = [r for r in all_refs if r["access"] in ("read_or_expression", "array_or_aggregate_view")]
        members.append({
            "name": name, "address": member["address"], "bytes": size,
            "dos_type": "signed int far" if size == 2 else "signed long far",
            "canonical_declaration_forms_from_prior_candidate": type_decl,
            "registry_exact_base_views": exact,
            "registry_interior_views_within_complete_type": interiors,
            "existing_owner_overlap_exclusions": is_owned,
            "still_unresolved_selection_snapshot": unresolved_match,
            "provider_eligible": unresolved_match and not is_owned and not interiors and not non_save_escapes,
            "SaveRec_raw_view": sr,
            "all_source_identifier_references": all_refs,
            "producer_or_update_receipts": producers,
            "consumer_receipts": consumers,
            "address_escape_receipts": escapes,
            "non_SaveRec_address_escapes": non_save_escapes,
            "numeric_value_match_receipts": numeric[int(member["address"].split(":")[1], 16)],
            "source_reference_count": len(all_refs),
            "producer_or_update_count": len(producers),
            "consumer_count": len(consumers),
        })
    return {"source_set": {"canonical_tus": 127, "strict_effective_modules": 29,
                           "unique_paths": len(source_receipts),
                           "DrawBalloons_uses_corrected_effective_whole_module": True,
                           "source_receipts": source_receipts},
            "SaveRec_table": {"source": SAVE_SOURCE, "array": SAVE_ARRAY,
                              "array_start_line": save_start,
                              "initializer_row_count_before_terminator": save_initializer_count,
                              "direct_symbol_rows_parsed": len(all_save_rows),
                              "other_initializer_forms": unparsed_save_initializers},
            "existing_owner_inventory_rows": owned,
            "members": members}


def mk_type_decl(member, unsigned=False):
    t = member["dos_type"].removeprefix("signed ")
    if unsigned:
        t = "unsigned " + t
    return f"extern {t} {member['name']};"


def test_values(member):
    if member["bytes"] == 2:
        n = int(member["address"].split(":")[1], 16)
        return (-1 if n % 4 == 0 else -12345)
    n = int(member["address"].split(":")[1], 16)
    return (-1234567 if n % 8 == 0 else -19088743)


def byte_tuple(value: int, width: int):
    return [(value >> (8 * i)) & 0xFF for i in range(width)]


def make_positive_sources(members):
    n = len(members)
    targets = [m["name"] for m in members]
    typed_aliases = [f"ProbeTyped{i}" for i in range(n)]
    save_aliases = [f"ProbeSave{i}" for i in range(n)]
    typed = [*(mk_type_decl(m) for m in members),
             *(f"extern {m['dos_type']} {alias};" for m, alias in zip(members, typed_aliases)),
             "extern int far puts(char far *text);", "int main(void)", "{"]
    typed.append("    if (sizeof(int) != 2 || sizeof(long) != 4) { puts(\"FAIL_ABI_WIDTH\"); return 1; }")
    for m, alias in zip(members, typed_aliases):
        typed.append(f"    if (&{m['name']} != &{alias}) {{ puts(\"FAIL_TYPED_ALIAS\"); return 2; }}")
        typed.append(f"    if ({m['name']} != 0) {{ puts(\"FAIL_STARTUP_ZERO\"); return 3; }}")
    # Every consecutive communal is checked against its independently typed
    # width, so shortening any long or widening any int changes observable layout.
    for left, right in zip(members, members[1:]):
        typed.append(f"    if ((unsigned char far *)&{right['name']} != "
                     f"(unsigned char far *)&{left['name']} + {left['bytes']}) "
                     "{ puts(\"FAIL_COMMUNAL_WIDTH_LAYOUT\"); return 4; }")
    values = [test_values(m) for m in members]
    for m, value in zip(members, values):
        suffix = "L" if m["bytes"] == 4 else ""
        typed.append(f"    {m['name']} = ({m['dos_type'].replace(' far', '')})({value}{suffix});")
        typed.append(f"    if ({m['name']} != ({value}{suffix}) || {m['name']} >= 0) "
                     "{ puts(\"FAIL_SIGNED_TYPED_ROUNDTRIP\"); return 5; }")
        raw = byte_tuple(value, m["bytes"])
        typed.append(f"    if (((unsigned char far *)&{m['name']})[0] != 0x{raw[0]:02x} || "
                     f"((unsigned char far *)&{m['name']})[{m['bytes'] - 1}] != 0x{raw[-1]:02x}) "
                     "{ puts(\"FAIL_TYPED_RAW_READ\"); return 6; }")
    typed.extend(["    puts(\"PASS_TYPED_SIGNED_STARTUP\");", "    return 0;", "}"])

    raw = [*(mk_type_decl(m) for m in members),
           *(f"extern {m['dos_type']} {alias};" for m, alias in zip(members, save_aliases)),
           "extern int far puts(char far *text);",
           "struct SaveRec { int size; int count; void far *data; };",
           f"struct SaveRec far ProbeRecords[{n}] = {{"]
    raw.extend(f"    {{ {m['bytes']}, 1, (void far *)&{alias} }}{',' if i + 1 < n else ''}"
               for i, (m, alias) in enumerate(zip(members, save_aliases)))
    raw.extend(["};", "int main(void)", "{", "    unsigned char far *p;"])
    raw.extend([f"    if (ProbeRecords[{i}].size != {m['bytes']} || ProbeRecords[{i}].count != 1) "
                "{ puts(\"FAIL_SAVEREC_SHAPE\"); return 1; }"
                for i, m in enumerate(members)])
    raw.extend([f"    if (ProbeRecords[{i}].data != (void far *)&{m['name']}) "
                "{ puts(\"FAIL_SAVEREC_BASE\"); return 2; }"
                for i, m in enumerate(members)])
    for i, m in enumerate(members):
        raw.append(f"    p = (unsigned char far *)ProbeRecords[{i}].data;")
        raw.append(f"    if (" + " || ".join(f"p[{b}] != 0" for b in range(m["bytes"])) +
                   ") { puts(\"FAIL_RAW_STARTUP_ZERO\"); return 3; }")
    # Raw saved bytes include signed extremes and are then observed by typed
    # lvalues. Values remain arbitrary because the real LoadGame path is unchecked.
    for i, m in enumerate(members):
        pattern = [0xFF] * m["bytes"]
        raw.append(f"    p = (unsigned char far *)ProbeRecords[{i}].data;")
        for byte_i, value in enumerate(pattern):
            raw.append(f"    p[{byte_i}] = 0x{value:02x};")
        raw.append(f"    if ({m['name']} != -1" + ("L" if m["bytes"] == 4 else "") +
                   f" || {m['name']} >= 0) {{ puts(\"FAIL_RAW_TO_SIGNED\"); return 4; }}")
        value = test_values(m)
        raw.append(f"    {m['name']} = ({m['dos_type'].replace(' far', '')})({value}{'L' if m['bytes'] == 4 else ''});")
        bts = byte_tuple(value, m["bytes"])
        raw.append(f"    p = (unsigned char far *)ProbeRecords[{i}].data;")
        raw.append("    if (" + " || ".join(f"p[{j}] != 0x{b:02x}" for j, b in enumerate(bts)) +
                   ") { puts(\"FAIL_SIGNED_TO_RAW\"); return 5; }")
    raw.extend(["    puts(\"PASS_RAW_SAVEREC_SIGNED\");", "    return 0;", "}"])
    return {"typed_positive": "\n".join(typed) + "\n",
            "raw_saverec_positive": "\n".join(raw) + "\n",
            "typed_aliases": typed_aliases, "save_aliases": save_aliases,
            "test_values": values}


def make_width_consumer(members):
    lines = [*(mk_type_decl(m) for m in members), "extern int far puts(char far *text);", "int main(void)", "{"]
    for left, right in zip(members, members[1:]):
        lines.append(f"    if ((unsigned char far *)&{right['name']} != "
                     f"(unsigned char far *)&{left['name']} + {left['bytes']}) "
                     "{ puts(\"WIDTH_LAYOUT_CONTRAST_DETECTED\"); return 0; }")
    lines.extend(["    puts(\"FAIL_WIDTH_LAYOUT_CONTRAST\");", "    return 0;", "}"])
    return "\n".join(lines) + "\n"


def make_unsigned_consumer(members):
    lines = [*(mk_type_decl(m, unsigned=True) for m in members),
             "extern int far puts(char far *text);", "int main(void)", "{"]
    for m in members:
        suffix = "L" if m["bytes"] == 4 else ""
        lines.append(f"    {m['name']} = -1{suffix};")
        lines.append(f"    if ({m['name']} <= {32767 if m['bytes'] == 2 else 2147483647}U) "
                     "{ puts(\"FAIL_UNSIGNED_VIEW\"); return 1; }")
    lines.extend(["    puts(\"UNSIGNED_SIGN_CONTRAST_DETECTED\");", "    return 0;", "}"])
    return "\n".join(lines) + "\n"


def make_initializer_consumer(members):
    lines = [*(mk_type_decl(m) for m in members),
             "extern int far puts(char far *text);", "int main(void)", "{"]
    lines.append(f"    if ({members[0]['name']} == 1) {{ puts(\"NONZERO_INITIALIZER_DETECTED\"); return 0; }}")
    lines.extend(["    puts(\"FAIL_INITIALIZER_NOT_VISIBLE\");", "    return 0;", "}"])
    return "\n".join(lines) + "\n"


def make_shifted_saverec_consumer(members, shifted_aliases):
    n = len(members)
    lines = [*(mk_type_decl(m) for m in members),
             *(f"extern {m['dos_type']} {alias};" for m, alias in zip(members, shifted_aliases)),
             "extern int far puts(char far *text);",
             "struct SaveRec { int size; int count; void far *data; };",
             f"struct SaveRec far ProbeRecords[{n}] = {{"]
    lines.extend(f"    {{ {m['bytes']}, 1, (void far *)&{alias} }}{',' if i + 1 < n else ''}"
                 for i, (m, alias) in enumerate(zip(members, shifted_aliases)))
    lines.extend(["};", "int main(void)", "{"])
    for i, m in enumerate(members):
        if i == 0:
            lines.append(f"    if (ProbeRecords[{i}].data != "
                         f"(void far *)((unsigned char far *)&{m['name']} + 2)) "
                         "{ puts(\"FAIL_SHIFTED_ALIAS_MAP\"); return 1; }")
            lines.append(f"    if (ProbeRecords[{i}].data == (void far *)&{m['name']}) "
                         "{ puts(\"FAIL_SHIFTED_SAVE_BASE\"); return 2; }")
        else:
            lines.append(f"    if (ProbeRecords[{i}].data != (void far *)&{m['name']}) "
                         "{ puts(\"FAIL_OTHER_SAVE_BASE\"); return 3; }")
    lines.extend(["    puts(\"SHIFTED_SAVEREC_BASE_DETECTED\");", "    return 0;", "}"])
    return "\n".join(lines) + "\n"


def compile_source(stem: str, source: str, flags: list[str]):
    if len(stem) > 8:
        raise ValueError("MSC 8.3 object basename too long: " + stem)
    source_path = FIXTURES / (stem + ".c")
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(source, encoding="ascii", newline="")
    result = compiler.compile_c(source, PROFILE, flags, basename=stem, keep=True)
    if not result.ok or result.obj is None:
        raise RuntimeError(f"MSC compile failed for {stem}:\n{result.log}")
    object_path = FIXTURES / (stem + ".OBJ")
    object_path.write_bytes(result.obj)
    log_path = FIXTURES / (stem + ".COMPILE.LOG")
    log_path.write_text(result.log, encoding="latin1", newline="")
    return {"stem": stem, "source_path": source_path, "object_path": object_path,
            "object": result.obj, "log_path": log_path, "log": result.log,
            "source": source}


def provider_source(members, overrides: dict[str, str] | None = None,
                    initializer: tuple[str, int] | None = None):
    overrides = overrides or {}
    lines = ["/* Candidate source-functional individual scalar owners; no history struct. */"]
    for m in members:
        name, width = m["name"], m["bytes"]
        type_name = overrides.get(name, "int" if width == 2 else "long")
        suffix = " = " + str(initializer[1]) if initializer and initializer[0] == name else ""
        lines.append(f"{type_name} far {name}{suffix};")
    return "\n".join(lines) + "\n"


def summarize_omf(raw: bytes):
    obj = OmfReader(communals=True).read(raw)
    return obj


def parse_public_sections(map_text: str):
    headings = list(re.finditer(r"(?im)^\s*Address\s+Publics by (Name|Value)\s*$", map_text))
    result = {"Name": {}, "Value": {}}
    for i, match in enumerate(headings):
        section = match.group(1)
        end = headings[i + 1].start() if i + 1 < len(headings) else len(map_text)
        for line in map_text[match.end():end].splitlines():
            row = re.match(r"\s*([0-9A-Fa-f]+:[0-9A-Fa-f]+)\s+(?:Res|Abs)\s+(\S+)", line)
            if row:
                result[section][row.group(2).lower()] = row.group(1).upper()
    return result


def addr_pair(value: str):
    seg, off = value.split(":")
    return int(seg, 16), int(off, 16)


def case_public_requirements(case: str, members, aliases):
    target_symbols = ["_" + m["name"] for m in members]
    required = target_symbols + ["_" + name for name, _ in aliases]
    relations = [(("_" + name).lower(), ("_" + m["name"]).lower(), delta)
                 for m, (name, delta) in zip(members, aliases)] if aliases else []
    return [value.lower() for value in required], relations


def clean_link_log(text: str, exe_exists: bool, timed_out: bool):
    bad = ("unresolved external", "undefined symbol", "link error", "fatal error",
           "cannot open", "not found", "warning:")
    return exe_exists and not timed_out and not any(term in text.lower() for term in bad)


def runtime_case(linker_name: str, linker: dict, tool_dir: Path, runner: dict,
                 runtime_files: list[dict], consumer: bytes, owner: bytes,
                 case_name: str, expected_marker: str, alias_lines: list[str],
                 members, aliases_by_case, expected_layout: bool | None,
                 shifted_case: bool = False):
    folder = FIXTURES / linker_name / case_name
    folder.mkdir(parents=True, exist_ok=True)
    folder.resolve().relative_to(FIXTURES.resolve())
    for leaf in ("PROBE.EXE", "PROBE.MAP", "RUN.LOG", "LINK.LOG"):
        (folder / leaf).unlink(missing_ok=True)
    (folder / "CRT.OBJ").write_bytes(consumer)
    (folder / "OWNER.OBJ").write_bytes(owner)
    for row in runtime_files:
        shutil.copyfile(row["path"], folder / Path(row["path"]).name.upper())
    lnk = ("OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\n"
           "LIBRARY LLIBCR, LIBH\r\nFILE CRT\r\nBEGINAREA\r\n"
           "SECTION FILE OWNER\r\nENDAREA\r\n" + "\r\n".join(alias_lines) + "\r\n")
    (folder / "PROBE.LNK").write_bytes(lnk.encode("ascii"))
    (folder / "RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
    (folder / "RUN.BAT").write_bytes((
        f"@echo off\r\nD:\\{linker['executable']} @PROBE.LNK < NUL > LINK.LOG\r\n"
        "PROBE.EXE > RUN.LOG\r\n").encode("ascii"))
    conf = []
    for section, values in runner["conf"].items():
        conf.append("[" + section + "]")
        conf.extend(f"{key}={value}" for key, value in values.items())
    conf.extend(["[autoexec]", f'mount c "{folder}"', f'mount d "{tool_dir}" -ro',
                 "c:", "call RUN.BAT", "exit"])
    (folder / "dosbox.conf").write_text("\n".join(conf) + "\n", encoding="ascii")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    timed_out = False
    try:
        done = subprocess.run([runner["path"], "-conf", str(folder / "dosbox.conf"),
                               "-fastlaunch", "-exit", "-nomenu"], cwd=folder,
                              env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                              timeout=90, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return_code = done.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
        return_code = -1
    run_path, link_path, map_path = folder / "RUN.LOG", folder / "LINK.LOG", folder / "PROBE.MAP"
    run_bytes = run_path.read_bytes() if run_path.exists() else b""
    link_bytes = link_path.read_bytes() if link_path.exists() else b""
    map_bytes = map_path.read_bytes() if map_path.exists() else b""
    run_text = run_bytes.decode("latin1")
    link_text = link_bytes.decode("latin1")
    map_text = map_bytes.decode("latin1")
    sections = parse_public_sections(map_text)
    required, relations = case_public_requirements(case_name, members, aliases_by_case)
    section_receipts = {name: {"heading_present": bool(sections[name]),
                               "missing_required_publics": [p for p in required if p not in sections[name]]}
                        for name in ("Name", "Value")}
    publics_both = all(not section_receipts[section]["missing_required_publics"]
                       for section in ("Name", "Value"))
    relation_results = []
    relation_ok = True
    for alias, target, delta in relations:
        na, nt = sections["Name"].get(alias), sections["Name"].get(target)
        va, vt = sections["Value"].get(alias), sections["Value"].get(target)
        okay = bool(na and nt and va and vt)
        if okay:
            an, tn, av, tv = map(addr_pair, (na, nt, va, vt))
            okay = an[0] == tn[0] and an[1] == tn[1] + delta and av[0] == tv[0] and av[1] == tv[1] + delta
        relation_ok &= okay
        relation_results.append({"alias": alias, "target": target, "expected_delta": delta,
                                 "Name_alias": na, "Name_target": nt,
                                 "Value_alias": va, "Value_target": vt, "passed": okay})
    # In the positives, all source-order publics must reflect each individually
    # typed communal length. For a width-negative owner the expected mismatch is
    # itself the contrast receipt.
    layout_receipts = []
    targets = [("_" + m["name"]).lower() for m in members]
    target_addresses = []
    if publics_both:
        for target in targets:
            target_addresses.append(addr_pair(sections["Value"].get(target, "0:0")))
        layout_ok = bool(target_addresses) and all(target_addresses[i][0] == target_addresses[0][0]
                    and target_addresses[i][1] == target_addresses[0][1] + sum(m["bytes"] for m in members[:i])
                    for i in range(len(members)))
        for i, (m, address) in enumerate(zip(members, target_addresses)):
            expected_delta = sum(prior["bytes"] for prior in members[:i])
            layout_receipts.append({"public": targets[i], "expected_delta_from_first": expected_delta,
                                    "actual_address_value_section": sections["Value"].get(targets[i]),
                                    "passed": bool(address and target_addresses[0] and
                                                   address[0] == target_addresses[0][0] and
                                                   address[1] == target_addresses[0][1] + expected_delta)})
    else:
        layout_ok = False
    if expected_layout is True:
        layout_test_ok = layout_ok
    elif expected_layout is False:
        layout_test_ok = not layout_ok
    else:
        layout_test_ok = True
    exe = (folder / "PROBE.EXE").is_file()
    clean = clean_link_log(link_text, exe, timed_out)
    marker_ok = run_text.strip() == expected_marker
    passed = (marker_ok and return_code == 0 and clean and publics_both and relation_ok and layout_test_ok)
    artifacts = []
    for path in sorted(folder.iterdir(), key=lambda p: p.name.lower()):
        if path.is_file():
            artifacts.append(pin(path))
    return {"linker": linker_name, "case": case_name,
            "expected_marker": expected_marker, "actual_output_verbatim": run_text,
            "actual_output_bytes_hex": run_bytes.hex(), "expected_outcome_passed": passed,
            "runner_returncode": return_code, "timed_out": timed_out,
            "exe_created": exe, "clean_link_log": clean,
            "link_log_verbatim": link_text, "link_log_bytes_hex": link_bytes.hex(),
            "map_public_sections": section_receipts,
            "all_required_publics_in_both_sections": publics_both,
            "required_publics": required, "alias_map_relations": relation_results,
            "typed_communal_layout": {"expected_layout": expected_layout,
                                      "layout_matches_individual_widths": layout_ok,
                                      "target_addresses_and_deltas": layout_receipts},
            "alias_definitions": alias_lines, "artifacts": artifacts}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    FIXTURES.mkdir(parents=True, exist_ok=True)
    denied = dos.install_input_guard()

    mutable_before = {path: pin(ROOT / path) for path in MUTABLE_OBSERVATIONS}
    family_path = ROOT / "build/workers/dos_far_word_inventory_v20/family-shortlist-v20.json"
    review_path = ROOT / "build/workers/dos_far_word_inventory_v20/review-v20.md"
    intake_path = ROOT / "work/source-only-dos/compile-and-intake-v1.json"
    index_path = ROOT / "work/source-only-dos/static-completeness/index-v1.json"
    symbols_path = ROOT / "layout/symbols.json"
    manifest_path = ROOT / "layout/manifest.json"
    toolchain_path = ROOT / "layout/toolchain.json"
    current_path = ROOT / "work/source-only-dos/current-intake.json"
    history_binding_path = ROOT / "work/source-only-dos/history-storage-bindings-v1.json"
    spider_binding_path = ROOT / "work/source-only-dos/spider-counter-bindings-v1.json"

    shortlist, shortlist_pin = read_json(family_path)
    family = next(row for row in shortlist["families"] if row["id"] == FAMILY_ID)
    if family["member_count"] != 12:
        raise RuntimeError("rank-3 family no longer contains twelve members")
    review_pin = pin(review_path)
    rows, sets, source_basis_pins = source_rows(intake_path, index_path)
    symbols_doc, symbols_pin = read_json(symbols_path)
    symbols = {"code": symbols_doc["code"], "data": symbols_doc["data"]}
    manifest, manifest_pin = read_json(manifest_path)
    toolchain, toolchain_pin = read_json(toolchain_path)
    current_intake, current_pin = read_json(current_path)
    history_bindings, history_binding_pin = read_json(history_binding_path)
    spider_bindings, spider_binding_pin = read_json(spider_binding_path)
    build_report, build_report_pin = read_json(ROOT / MUTABLE_OBSERVATIONS[0])

    unresolved = build_report.get("unresolved_symbols", [])
    owned_addresses = {(_row.get("seg"), _row.get("off")) for _row in []}
    member_rows = family["members"]
    member_addresses = {(int(m["address"].split(":")[0], 16), int(m["address"].split(":")[1], 16))
                        for m in member_rows}
    unresolved_addresses = set()
    for row in unresolved:
        reg = row.get("registry") or {}
        if reg.get("seg") is not None and reg.get("off") is not None:
            unresolved_addresses.add((reg["seg"], reg["off"]))
    audit = audit_sources(rows, family, symbols, current_intake, history_bindings,
                          spider_bindings, unresolved)
    candidate_by_name = {m["name"]: m for m in audit["members"]}
    active_members = [m for m in audit["members"] if m["provider_eligible"]]
    if len(active_members) != len(member_rows):
        # The report remains useful even if a concurrently admitted owner or a
        # current build selection removes one candidate; never shadow its owner.
        if active_members:
            pass
        else:
            audit["status"] = "NO_UNRESOLVED_UNOWNED_TARGETS"
            AUDIT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
            raise RuntimeError("no rank-3 member remains both unresolved and unowned")

    # Rank-3 lifecycle, SaveRec, and call-path anchors are recorded from complete
    # canonical/effective source views. SaveRec remains an unchecked raw byte load.
    owner_text = (ROOT / OWNER_SOURCE).read_text(encoding="latin1")
    save_text = (ROOT / SAVE_SOURCE).read_text(encoding="latin1")
    clear_start = owner_text.index("void far ClearHistory(int newGame)")
    clear_end = owner_text.index("\nvoid far win_DrawHistoryWindow", clear_start)
    clear_body = owner_text[clear_start:clear_end]
    clear_lines = clear_body.splitlines()
    conditional_targets = ["fd_50F6_0ADA", "fd_50F6_0A90", "fd_50F6_0AC4",
                           "fd_50F6_0A9E", "fd_50F6_0AC8"]
    conditional_rows = []
    for i, line in enumerate(clear_lines, 1):
        if any(name in line for name in conditional_targets):
            conditional_rows.append({"line": owner_text[:clear_start].count("\n") + i,
                                     "text": line.strip(), "under_newGame_equals_1": True})
    all_clear_resets = []
    for m in active_members:
        for i, line in enumerate(clear_lines, 1):
            if re.search(r"\b" + re.escape(m["name"]) + r"\s*(?:=|\+\+|--)", line):
                all_clear_resets.append({"name": m["name"],
                                         "line": owner_text[:clear_start].count("\n") + i,
                                         "text": line.strip(),
                                         "conditional_newGame_reset": m["name"] in conditional_targets})
    clear_calls = []
    clear_spellings = {"ClearHistory", "o24_39C7_01B8"}
    for source in rows:
        text = (ROOT / source["path"]).read_text(encoding="latin1")
        for line_no, line in enumerate(text.splitlines(), 1):
            for spelling in clear_spellings:
                if re.search(r"\b" + spelling + r"\s*\(", line) and not re.match(r"\s*(?:extern\s+)?void\b", line):
                    clear_calls.append({"set": source["set"], "path": source["path"],
                                       "module": source.get("module"), "line": line_no,
                                       "spelling": spelling, "text": line.strip()})
    raw_load_line = next((i for i, line in enumerate(save_text.splitlines(), 1)
                          if "read(fd, p->data, n = p->count * p->size)" in line), None)
    raw_save_line = next((i for i, line in enumerate(save_text.splitlines(), 1)
                          if "write(fd, p->data, p->count * p->size)" in line), None)

    audit["lifecycle"] = {
        "ClearHistory_definition": {"source": OWNER_SOURCE, "signature": "void far ClearHistory(int newGame)",
                                    "full_body_sha256": sha(clear_body.encode("latin1")),
                                    "all_candidate_reset_rows": all_clear_resets,
                                    "conditional_newGame_equals_1_rows": conditional_rows},
        "ClearHistory_source_call_sites": clear_calls,
        "ClearHistory_call_alias_identity": "o24_39C7_01B8 is registered at S24:39C7:01B8, same entry as ClearHistory",
        "SaveRec_generic_save_raw_write_line": raw_save_line,
        "SaveRec_generic_load_raw_read_line": raw_load_line,
        "raw_load_semantics": "LoadGame reads count*size bytes into each saved data pointer without validating values; SaveRec establishes serialized byte views and raw pointer use, not legal value ranges.",
        "newGame_reset_limit": "Five totals/flags reset only under newGame == 1. Other candidate stores are unconditional inside ClearHistory, but both call-path coverage and raw SaveRec replacement prevent claiming universal lifecycle or bounded values.",
    }

    audit["selection"] = {
        "mutable_build_report_pin_selection_only": build_report_pin,
        "unresolved_family_members": [m["name"] for m in active_members],
        "excluded_already_owned_or_resolved": [
            {"name": m["name"], "address": m["address"],
             "owned": bool(m["existing_owner_overlap_exclusions"],),
             "unresolved": m["still_unresolved_selection_snapshot"]}
            for m in audit["members"] if not m["provider_eligible"]],
        "selection_authority": "v20 family shortlist selects the bounded rank-3 cohort; mutable current build-report is only used to omit no-longer-unresolved imports. Existing owner intervals from current intake, history-array bindings and spider-counter bindings are exclusions.",
    }
    AUDIT.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if not active_members:
        raise RuntimeError("empty source-functional candidate provider")
    provider_text = provider_source(active_members)
    PROVIDER.write_text(provider_text, encoding="ascii", newline="")

    provider = compile_source("HISTOTAL", provider_text, PROVIDER_FLAGS)
    provider_omf_obj = summarize_omf(provider["object"])
    expected_commons = sorted(("_" + m["name"], "far", m["bytes"], 1, m["bytes"])
                              for m in active_members)
    actual_commons = sorted(bindings.communal_key(row) for row in provider_omf_obj.communals)
    live_segments = {name: length for name, length in provider_omf_obj.segment_lengths.items() if length}
    provider_clean = (actual_commons == expected_commons and not live_segments and
                      not provider_omf_obj.fixups and not provider_omf_obj.linker_fixups and
                      not provider_omf_obj.publics and not provider_omf_obj.local_publics)
    if not provider_clean:
        raise RuntimeError("candidate OMF is not the exact per-scalar typed communal set: " + repr(actual_commons))

    # Fresh source-shaped mixed-width controls: one 4-byte object shortened and
    # one 2-byte object widened. These are independent compile-only OMF contrasts
    # plus the same offset-layout observation under both actual RTLink profiles.
    long_member = next(m for m in active_members if m["bytes"] == 4)
    word_member = next(m for m in active_members if m["bytes"] == 2)
    short_provider_text = provider_source(active_members, {long_member["name"]: "int"})
    wide_provider_text = provider_source(active_members, {word_member["name"]: "long"})
    short_provider = compile_source("HISTSHRT", short_provider_text, PROVIDER_FLAGS)
    wide_provider = compile_source("HISTWIDE", wide_provider_text, PROVIDER_FLAGS)
    initialized_text = provider_source(active_members, initializer=(active_members[0]["name"], 1))
    initialized_provider = compile_source("HISTINIT", initialized_text, PROVIDER_FLAGS)
    source_specs = make_positive_sources(active_members)
    consumers = {
        "typed_positive": compile_source("HISTTYPE", source_specs["typed_positive"], CONSUMER_FLAGS),
        "raw_saverec_positive": compile_source("HISTSAVE", source_specs["raw_saverec_positive"], CONSUMER_FLAGS),
        "width_contrast": compile_source("HISTWCON", make_width_consumer(active_members), CONSUMER_FLAGS),
        "unsigned_contrast": compile_source("HISTUNSG", make_unsigned_consumer(active_members), CONSUMER_FLAGS),
        "initializer_contrast": compile_source("HISTICON", make_initializer_consumer(active_members), CONSUMER_FLAGS),
    }
    shifted_aliases = [f"ProbeShift{i}" for i in range(len(active_members))]
    consumers["shifted_saverec_contrast"] = compile_source(
        "HISTSFT", make_shifted_saverec_consumer(active_members, shifted_aliases), CONSUMER_FLAGS)

    # OMF rows are checked individually. This distinguishes long vs int even
    # though both are represented as byte-element FAR commons by MSC 6.00AX.
    wrong_short_obj = summarize_omf(short_provider["object"])
    wrong_wide_obj = summarize_omf(wide_provider["object"])
    init_obj = summarize_omf(initialized_provider["object"])
    expected_after_short = sorted(("_" + m["name"], "far",
                                   2 if m["name"] == long_member["name"] else m["bytes"], 1,
                                   2 if m["name"] == long_member["name"] else m["bytes"])
                                  for m in active_members)
    expected_after_wide = sorted(("_" + m["name"], "far",
                                  4 if m["name"] == word_member["name"] else m["bytes"], 1,
                                  4 if m["name"] == word_member["name"] else m["bytes"])
                                 for m in active_members)
    if sorted(bindings.communal_key(row) for row in wrong_short_obj.communals) != expected_after_short:
        raise RuntimeError("short-long-width OMF contrast did not encode the requested changed object")
    if sorted(bindings.communal_key(row) for row in wrong_wide_obj.communals) != expected_after_wide:
        raise RuntimeError("wide-int-width OMF contrast did not encode the requested changed object")
    expected_init_commons = sorted(("_" + m["name"], "far", m["bytes"], 1, m["bytes"])
                                   for m in active_members[1:])
    init_commons = sorted(bindings.communal_key(row) for row in init_obj.communals)
    init_publics = [row.get("name", "").lower() for row in init_obj.publics]
    if init_commons != expected_init_commons or ("_" + active_members[0]["name"]).lower() not in init_publics:
        raise RuntimeError("initialized contrast OMF did not move the selected object out of tentative common storage")

    aliases_by_case = {
        "typed_positive": [(name, 0) for name in source_specs["typed_aliases"]],
        "raw_saverec_positive": [(name, 0) for name in source_specs["save_aliases"]],
        "width_contrast": [], "unsigned_contrast": [], "initializer_contrast": [],
        "short_width_owner": [], "wide_width_owner": [],
        "shifted_saverec_contrast": [(name, 2 if i == 0 else 0)
                                      for i, name in enumerate(shifted_aliases)],
    }
    maps = []
    alias_defs = {
        "typed_positive": [f"DEFINE _{alias} = _{m['name']}" for m, alias in zip(active_members, source_specs["typed_aliases"])],
        "raw_saverec_positive": [f"DEFINE _{alias} = _{m['name']}" for m, alias in zip(active_members, source_specs["save_aliases"])],
        "width_contrast": [], "unsigned_contrast": [], "initializer_contrast": [],
        "short_width_owner": [], "wide_width_owner": [],
        "shifted_saverec_contrast": [f"DEFINE _{alias} = _{m['name']}{'+2' if i == 0 else ''}"
                                      for i, (m, alias) in enumerate(zip(active_members, shifted_aliases))],
    }
    runtime_libraries = []
    for name, row in manifest["runtime"]["libraries"].items():
        runtime_libraries.append({"name": name, "path": Path(row["path"]), "sha256": row["sha256"]})
    runner = toolchain["runners"]["dosbox-x"]
    pinned_linker_tools = {}
    for linker_name in ("rtlink400", "rtlink610"):
        linker = toolchain["linkers"][linker_name]
        for rel, expected in linker["files"].items():
            pin(Path(linker["directory"]) / rel, expected)
        tool_dir = compiler.pinned_tree(linker)
        pinned_linker_tools[linker_name] = [
            pin(Path(tool_dir) / rel, expected) for rel, expected in linker["files"].items()]
        case_specs = [
            ("typed_positive", consumers["typed_positive"]["object"], provider["object"], "PASS_TYPED_SIGNED_STARTUP", True),
            ("raw_saverec_positive", consumers["raw_saverec_positive"]["object"], provider["object"], "PASS_RAW_SAVEREC_SIGNED", True),
            ("width_contrast", consumers["width_contrast"]["object"], short_provider["object"], "WIDTH_LAYOUT_CONTRAST_DETECTED", False),
            ("width_contrast", consumers["width_contrast"]["object"], wide_provider["object"], "WIDTH_LAYOUT_CONTRAST_DETECTED", False),
            ("unsigned_contrast", consumers["unsigned_contrast"]["object"], provider["object"], "UNSIGNED_SIGN_CONTRAST_DETECTED", None),
            ("initializer_contrast", consumers["initializer_contrast"]["object"], initialized_provider["object"], "NONZERO_INITIALIZER_DETECTED", None),
            ("shifted_saverec_contrast", consumers["shifted_saverec_contrast"]["object"], provider["object"], "SHIFTED_SAVEREC_BASE_DETECTED", None),
        ]
        for ordinal, (case, consumer_obj, owner_obj, marker, layout_expected) in enumerate(case_specs):
            actual_case = case
            if case == "width_contrast":
                actual_case = "width_short_long" if owner_obj is short_provider["object"] else "width_wide_int"
                aliases_by_case[actual_case] = []
                alias_defs[actual_case] = []
            maps.append(runtime_case(linker_name, linker, tool_dir, runner, runtime_libraries,
                                     consumer_obj, owner_obj, actual_case, marker,
                                     alias_defs.get(actual_case, alias_defs.get(case, [])),
                                     active_members, aliases_by_case.get(actual_case, aliases_by_case[case]),
                                     layout_expected))
    # Each linker has one each of typed/raw/short-width/wide-width/sign/init/shifted.
    case_counts = {}
    for row in maps:
        case_counts.setdefault(row["linker"], []).append(row["case"])
    for linker_name, actual_cases in case_counts.items():
        if len(actual_cases) != 7 or len(set(actual_cases)) != 7:
            raise RuntimeError(f"{linker_name}: unexpected runtime case set {actual_cases}")
    if not all(row["expected_outcome_passed"] for row in maps):
        raise RuntimeError("one or more two-linker candidate/contrast cases failed")

    # Runtime inputs are pinned exactly as executed; input changes are evidence,
    # never silently accepted as a new baseline.
    input_pins = [pin(Path(__file__)), pin(PROVIDER), shortlist_pin, review_pin,
                  manifest_pin, symbols_pin, toolchain_pin, current_pin,
                  history_binding_pin, spider_binding_pin, build_report_pin,
                  *source_basis_pins]
    for path in MUTABLE_OBSERVATIONS:
        input_pins.append(mutable_before[path])
    for row in rows:
        input_pins.append({k: row[k] for k in ("path", "sha256", "size")})
    for source_file in (ROOT / OWNER_SOURCE, ROOT / SAVE_SOURCE):
        input_pins.append(pin(source_file))
    for tool in (ROOT / "tools/compiler.py", ROOT / "tools/omf.py"):
        input_pins.append(pin(tool))
    msc = toolchain["profiles"][PROFILE]
    compiler_tool_pins = [pin(Path(msc["directory"]) / rel, expected)
                          for rel, expected in msc["files"].items()]
    input_pins.extend(compiler_tool_pins)
    input_pins.append(pin(Path(toolchain["runners"][msc["runner"]]["path"]),
                          toolchain["runners"][msc["runner"]]["sha256"]))
    runtime_tool_pins = [pin(row["path"], row["sha256"]) for row in runtime_libraries]
    input_pins.extend(runtime_tool_pins)
    dosbox = runner
    input_pins.append(pin(Path(dosbox["path"]), dosbox["sha256"]))
    for linker_name, linker in toolchain["linkers"].items():
        if linker_name not in ("rtlink400", "rtlink610"):
            continue
        input_pins.extend(pin(Path(linker["directory"]) / rel, expected)
                          for rel, expected in linker["files"].items())
        input_pins.extend(pinned_linker_tools[linker_name])
    unique_pins = {}
    for p in input_pins:
        label = p["path"].replace("\\", "/")
        normalized = dict(p, path=label)
        if label in unique_pins and unique_pins[label] != normalized:
            raise RuntimeError("conflicting recorded input pin for " + label)
        unique_pins[label] = normalized
    all_inputs = [unique_pins[k] for k in sorted(unique_pins)]

    mutable_after = {path: pin(ROOT / path) for path in MUTABLE_OBSERVATIONS}
    mutable_drift = {path: {"before": mutable_before[path], "after": mutable_after[path]}
                     for path in MUTABLE_OBSERVATIONS
                     if mutable_before[path]["sha256"] != mutable_after[path]["sha256"]}
    provider_omf = {
        "communal_records": provider_omf_obj.communals,
        "normalized_communal_rows": [list(row) for row in sorted(bindings.communal_key(x)
                                                                   for x in provider_omf_obj.communals)],
        "expected_normalized_rows": [list(row) for row in expected_commons],
        "live_segment_lengths": provider_omf_obj.segment_lengths,
        "publics": provider_omf_obj.publics, "local_publics": provider_omf_obj.local_publics,
        "fixups": provider_omf_obj.fixups, "linker_fixups": provider_omf_obj.linker_fixups,
        "exact_type_count_element_size_and_byte_length_pass": provider_clean,
    }
    case_artifacts = []
    for entry in [provider, short_provider, wide_provider, initialized_provider, *consumers.values()]:
        case_artifacts.extend([pin(entry["source_path"]), pin(entry["object_path"]), pin(entry["log_path"])])
    for row in maps:
        case_artifacts.extend(row["artifacts"])
    seen_artifacts = {}
    for row in case_artifacts:
        seen_artifacts[row["path"]] = row

    report = {
        "schema": "simant-dos-history-scalar-words-candidate-v21",
        "status": "SCRATCH_CANDIDATE_ROOT_REVIEW_PENDING",
        "root_reviewed": False,
        "source_owner": {
            "module": "source-owned:history-scalar-state",
            "provider_basename": "HISTOTAL",
            "provider_path": PROVIDER.relative_to(ROOT).as_posix(),
            "provider_sha256": sha(provider_text.encode("ascii")),
            "nature": "individual signed int/long far tentative scalar owners; no C struct, functions, initializers, or historical COMDEF claim",
            "members": [{"name": m["name"], "address": m["address"], "dos_type": m["dos_type"],
                         "bytes": m["bytes"]} for m in active_members],
            "omf": provider_omf,
            "compiler_profile": PROFILE, "compiler_flags": PROVIDER_FLAGS,
            "required_profile_flags": msc.get("required_flags", []),
        },
        "source_audit": {"path": AUDIT.relative_to(ROOT).as_posix(),
                         "sha256": sha(AUDIT.read_bytes()),
                         "scope": "fresh exact-token audit of the v20 rank-3 family across 127 canonical TUs and 29 effective strict modules; 156 unique source files, corrected DrawBalloons source substituted"},
        "source_scope": audit["source_set"],
        "lifecycle": audit["lifecycle"],
        "selection": audit["selection"],
        "contrasts": {
            "short_long_owner": {"object_communal_rows": [list(bindings.communal_key(x)) for x in wrong_short_obj.communals],
                                 "target_changed": long_member["name"], "expected_bytes": 4, "measured_bytes": 2},
            "wide_int_owner": {"object_communal_rows": [list(bindings.communal_key(x)) for x in wrong_wide_obj.communals],
                               "target_changed": word_member["name"], "expected_bytes": 2, "measured_bytes": 4},
            "unsigned_consumer": "All candidate data are declared as unsigned int/long in this negative view; writing -1 and observing the high unsigned range must produce the sign contrast marker. OMF cannot distinguish signedness.",
            "initialized_provider": {"source_sha256": sha(initialized_text.encode("ascii")),
                                     "communal_rows": [list(bindings.communal_key(x)) for x in init_obj.communals],
                                     "publics": init_obj.publics,
                                     "initialized_name": active_members[0]["name"], "value": 1},
            "shifted_saverec_base": {"alias": "ProbeShift0", "target": active_members[0]["name"],
                                     "expected_displacement": 2,
                                     "checked_in_both_map_sections": True},
            "per_member_width_enforcement": "The positive MSC 6.00AX object must contain exactly one far communal for every candidate. int is encoded count=2, element_size=1, length=2; long is count=4, element_size=1, length=4. Both mixed-width controls alter one member, and per-target map spacing plus OMF rows detect each change.",
        },
        "runtime": {"linkers": ["rtlink400", "rtlink610"],
                    "runner": runner, "cases": maps,
                    "all_expected_outcomes_pass": all(row["expected_outcome_passed"] for row in maps),
                    "map_contract": "Each linked case requires every candidate owner public and each test alias public in both RTLink Publics by Name and Publics by Value. Alias addresses and expected displacement are checked in each section.",
                    "clean_link_logs_required": True,
                    "only_pinned_MSC_CRT_and_test_owned_consumer_plus_candidate_provider": True,
                    "original_executable_bytes_used": 0,
                    "source_game_object_bytes_used": 0},
        "pins": {"inputs": all_inputs, "generated_artifacts": list(seen_artifacts.values()),
                 "mutable_observations_before": mutable_before,
                 "mutable_observations_after": mutable_after,
                 "mutable_input_drift": mutable_drift},
        "denied_oracle_reads": denied,
        "limits": [
            "No original executable or original object/data bytes were read, compiled, or linked; the SOURCE_ONLY_DOS input guard ran before audit or probe work.",
            "SaveRec stores are raw size/count byte spans and LoadGame does not validate values. This probe establishes typed source widths and test-owned zero startup, not legal game values.",
            "Five ClearHistory stores are guarded by newGame == 1; reset call coverage does not establish universal lifecycle. Save loading can restore arbitrary raw patterns.",
            "The independent history-array owner and seven spider/corpse counter owner were used only as exclusions; none of their owned extents intersects these twelve scalar targets.",
            "This proposes source-functional scalar storage only. It makes no claim about original COMDEF-producing TU, communal order, padding, or physical placement.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"report": REPORT.relative_to(ROOT).as_posix(),
                      "source_audit": AUDIT.relative_to(ROOT).as_posix(),
                      "members": len(active_members), "provider_clean": provider_clean,
                      "runtime_cases": len(maps),
                      "all_expected_outcomes_pass": all(row["expected_outcome_passed"] for row in maps),
                      "mutable_input_drift": mutable_drift,
                      "cases": [{"linker": row["linker"], "case": row["case"],
                                 "actual": row["actual_output_verbatim"].strip(),
                                 "pass": row["expected_outcome_passed"],
                                 "clean_log": row["clean_link_log"],
                                 "publics_both_sections": row["all_required_publics_in_both_sections"]}
                                for row in maps]}, indent=2))


if __name__ == "__main__":
    main()
