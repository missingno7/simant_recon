"""Replay the signed-MSC-ctype prefix reachability proof.

The probe reads canonical C/ASM through src/program.json, checks that inventory's
source hashes, verifies the selected original/resource/toolchain identities, and
stores facts only (never shipped resource bytes).
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import re
import struct
import sys
from collections import Counter
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents
            if (p / "src/program.json").is_file())
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "tools"))
import canonical
import csrc

SITE_KEYS = {
    ("src/S09/m35F5.c", 429): ("o09_35F5_03C6", "isalnum"),
    ("src/S10/m35F5.c", 305): ("o10_35F5_0384", "islower"),
    ("src/S10/m35F5.c", 325): ("o10_35F5_0384", "isalpha"),
    ("src/S10/m35F5.c", 351): ("o10_35F5_0384", "islower"),
    ("src/S20/m39F1.c", 117): ("IBMInitStuff", "isdigit"),
    ("src/S20/m39F1.c", 189): ("ReadWord", "isspace"),
    ("src/S20/m39F1.c", 193): ("ReadWord", "isspace"),
    ("src/S20/m39F1.c", 255): ("ReadConfig", "isdigit"),
    ("src/S23/m39C7.c", 201): ("win_PrintStyleTextInRect", "direct"),
    ("src/root/m1C62.c", 170): ("f_1C62_00D5", "direct"),
    ("src/root/m1C62.c", 306): ("f_1C62_0415", "direct"),
}
CTYPE_STANDARD = {
    "isalpha", "isupper", "islower", "isdigit", "isxdigit", "isspace",
    "ispunct", "isalnum", "isprint", "isgraph", "iscntrl", "toupper",
    "tolower", "iscsymf", "iscsym", "isascii", "toascii", "_tolower",
    "_toupper",
}
TRIVIA = {"ws", "nl", "cmt", "pp"}
CTYPE_GATE_ID = "ctype-out-of-range-index-layout"
CTYPE_DATA_ID = "dgroup_79f0"
CANONICAL_ONLY_MAP = Path("build/workers/claude/clip-owner/link-trial/link/SOURCE.MAP")
CANONICAL_ONLY_MAP_SHA256 = "e5cb20e25ddd34802d78d26f1e505b86712fa7cd460b17a9b4be3f1865351a0e"
RENDERER_BREAK_BYTES = frozenset(b" \r\n([{!)-.,?]}")
RENDERER_SKIP_BYTES = frozenset(b" \r\n")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def norm(text: str) -> str:
    return " ".join(t.text for t in csrc.tokenize(text)
                    if t.kind not in {"ws", "nl", "cmt", "pp"})


def sig_tokens(text: str):
    return [t for t in csrc.tokenize(text) if t.kind not in TRIVIA]


def token_text(tokens) -> str:
    return " ".join(t.text for t in tokens)


def contains_tokens(text: str, spelling: str) -> bool:
    hay, needle = [t.text for t in sig_tokens(text)], [t.text for t in sig_tokens(spelling)]
    return any(hay[i:i + len(needle)] == needle for i in range(len(hay) - len(needle) + 1))


def renderer_style_spans(text: bytes, runs: list[list[int]], *, expand_left: bool = True) -> list[dict]:
    """Return every possible face-0100 pre-transition argument, conservatively bounded.

    DisplayCard's renderer advances one style at a time before consuming text[pos].
    A wrap can later rewind pos to the most recent brk while retaining styleIdx, so
    the next argument may start before the prior run's declared position. The
    nearest earlier renderer delimiter bounds that rewind.
    """
    positions = [int(run[0]) for run in runs]
    if any(right <= left for left, right in zip(positions, positions[1:])):
        raise ValueError("DisplayCard transformed style positions are not strictly ordered")
    if any(pos < 0 for pos in positions):
        raise ValueError("DisplayCard transformed style position is negative")
    skipped = [i for i, run in enumerate(runs[1:], 1)
               if run[0] < len(text) and text[run[0]] in RENDERER_SKIP_BYTES]
    skipped_ends = {i: _renderer_skip_destination(text, positions[i]) for i in skipped}
    delayed_effects = [i for i in skipped if i + 1 < len(positions)
                       and positions[i + 1] <= skipped_ends[i]]
    if delayed_effects:
        details = [(i, positions[i], f"{text[positions[i]]:02X}", int(runs[i - 1][4]),
                    positions[i + 1] if i + 1 < len(positions) else None)
                   for i in delayed_effects]
        raise ValueError(f"DisplayCard skipped style transition can delay a classified run: {details}")

    spans = []
    for transition in range(1, len(runs)):
        previous = runs[transition - 1]
        if int(previous[4]) != 0x100:
            continue
        declared_start = min(max(positions[transition - 1], 0), len(text))
        declared_end = min(max(positions[transition], 0), len(text))
        end = skipped_ends.get(transition, declared_end)
        end = min(max(end, declared_end), len(text))
        if expand_left and transition - 1 == 0:
            start = 0  # Renderer starts at pos=0, regardless of the first style offset.
        elif expand_left:
            delimiters = [i for i, byte in enumerate(text[:declared_start])
                          if byte in RENDERER_BREAK_BYTES]
            start = delimiters[-1] if delimiters else 0
        else:
            start = declared_start
        if end < start:
            raise ValueError("DisplayCard conservative style span has reversed endpoints")
        span = text[start:end]
        hist = Counter(byte for byte in span if byte >= 0x80)
        ideal = text[declared_start:declared_end]
        ideal_hist = Counter(byte for byte in ideal if byte >= 0x80)
        spans.append({"transition_index": transition,
                      "previous_run_index": transition - 1,
                      "face": int(previous[4]),
                      "declared_interval": [declared_start, declared_end],
                      "conservative_interval": [start, end],
                      "right_extension_after_skipped_bytes": max(0, end - declared_end),
                      "preceding_break": ({"offset": start, "byte": f"{text[start]:02X}"}
                                          if expand_left and start < declared_start else None),
                      "ideal_high_byte_counts": {f"{b:02X}": ideal_hist[b] for b in sorted(ideal_hist)},
                      "high_byte_counts": {f"{b:02X}": hist[b] for b in sorted(hist)}})
    return spans


def _renderer_skip_destination(text: bytes, position: int) -> int:
    """Bound the next pos after the renderer's post-line space and CR/LF skips."""
    if position >= len(text) or text[position] not in RENDERER_SKIP_BYTES:
        return position
    end = position
    while end < len(text) and text[end] == ord(" "):
        end += 1
    if end < len(text) and text[end] in (ord("\r"), ord("\n")):
        end += 1
    return end


def require_renderer_spans_ascii(text: bytes, runs: list[list[int]], label: str) -> list[dict]:
    spans = renderer_style_spans(text, runs)
    high = [row for row in spans if row["high_byte_counts"]]
    if high:
        raise ValueError(f"DisplayCard conservative renderer span contains a high byte: {label}")
    return spans


def renderer_rewind_negative_control() -> dict:
    # At '(' the renderer can retain brk=1; after advancing the face-0100 run at
    # 4, a narrow line may wrap back to 1. styleIdx remains advanced and the
    # later transition at 8 classifies [1,8), including the synthetic D1 at 2.
    text = b"x(\xD1abcDEFz"
    runs = [[0, 0, 0, 0, 0x000], [4, 0, 0, 0, 0x100], [8, 0, 0, 0, 0x000]]
    ideal = renderer_style_spans(text, runs, expand_left=False)
    if any(row["ideal_high_byte_counts"] for row in ideal):
        raise ValueError("synthetic renderer control is not missed by ideal intervals")
    try:
        require_renderer_spans_ascii(text, runs, "synthetic-rewind-prefix")
    except ValueError as exc:
        if "conservative renderer span contains a high byte" not in str(exc):
            raise
        expanded_rejected = True
    else:
        raise ValueError("synthetic rewind-prefix high byte passed the expanded-span check")
    return {"resource": "synthetic only", "text_hex": text.hex(" "),
            "style_positions": [run[0] for run in runs],
            "style_faces": [run[4] for run in runs],
            "renderer_witness": ["brk=1 at '('", "transition at pos=4 advances styleIdx",
                                 "end=1<start=4 rewinds pos/start to 1",
                                 "transition at pos=8 classifies argument [1,8)"],
            "ideal_intervals_have_high_bytes": False,
            "expanded_span_fails_check": expanded_rejected}


def _ctype_program_projection(program: dict) -> str:
    """Hash the canonical inventory while ignoring gate/debt disposition moves."""
    normalized = json.loads(json.dumps(program))
    dos = normalized.get("dos", {})
    for section in ("semantic_gates", "resolved_domain_contracts", "unresolved_data"):
        rows = dos.get(section, [])
        dos[section] = [row for row in rows if row.get("id") not in {CTYPE_GATE_ID, CTYPE_DATA_ID}]
    dos["_ctype_domain_ledger_projection"] = {"gate_id": CTYPE_GATE_ID, "data_id": CTYPE_DATA_ID}
    return sha(json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode())


def _find_ledger_row(program: dict, ident: str, sections: tuple[str, ...]):
    for section in sections:
        for row in program.get("dos", {}).get(section, []):
            if row.get("id") == ident:
                return section, row
    return None, None


def ctype_ledger_facts(program: dict) -> tuple[dict, dict]:
    gate_section, gate = _find_ledger_row(
        program, CTYPE_GATE_ID, ("semantic_gates", "resolved_domain_contracts"))
    data_section, data = _find_ledger_row(
        program, CTYPE_DATA_ID, ("unresolved_data", "resolved_domain_contracts"))
    if gate is None:
        raise ValueError("ctype gate missing from unresolved/resolved ledger")
    if gate_section == "semantic_gates":
        if gate.get("status") != "UNRESOLVED" or gate.get("overlapping_data_debt") != CTYPE_DATA_ID:
            raise ValueError("ctype unresolved gate inventory changed")
    elif gate.get("status") not in {"RESOLVED_SUPPORTED_DOMAIN", "RESOLVED"}:
        raise ValueError("ctype resolved gate status changed")
    if data is None:
        # Some integrations fold the debt row into the resolved gate record.
        if gate.get("overlapping_data_debt") != CTYPE_DATA_ID and \
           CTYPE_DATA_ID not in gate.get("resolved_data_ids", []):
            raise ValueError("ctype resolved gate no longer names dgroup_79f0")
        bytes_count = int(gate.get("overlapping_data_bytes", 14))
    else:
        bytes_count = int(data.get("bytes", 0))
    if bytes_count != 14:
        raise ValueError("dgroup_79f0 inventory changed")
    gate_fact = {"id": CTYPE_GATE_ID, "overlapping_data_debt": CTYPE_DATA_ID,
                 "ledger_state": "UNRESOLVED_OR_RESOLVED_SUPPORTED_DOMAIN"}
    data_fact = {"id": CTYPE_DATA_ID, "bytes": 14,
                 "ledger_state": "UNRESOLVED_OR_RESOLVED_SUPPORTED_DOMAIN"}
    return gate_fact, data_fact


def load_program_override(program_override):
    if program_override is None:
        return canonical.load(), (ROOT / "src/program.json").read_bytes()
    if isinstance(program_override, (str, Path)):
        raw = Path(program_override).read_bytes()
        return json.loads(raw), raw
    if isinstance(program_override, dict):
        raw = (json.dumps(program_override, indent=2) + "\n").encode("utf8")
        return program_override, raw
    raise TypeError("program_override must be a mapping or JSON path")


def inventory(program_override=None, source_overrides=None):
    # Verify the canonical baseline first, even when a test supplies overlays.
    base = canonical.load()
    baseline_raw = (ROOT / "src/program.json").read_bytes()
    base_hashes = {}
    baseline_texts = {}
    for module in base["modules"]:
        rel = module["source"]
        raw = (ROOT / rel).read_bytes()
        if sha(raw) != module["source_sha256"]:
            raise ValueError("canonical source hash mismatch: " + rel)
        base_hashes[rel] = module["source_sha256"]
        baseline_texts[rel] = raw.decode("latin1")

    program, program_raw = load_program_override(program_override)
    overrides = source_overrides or {}
    unknown = set(overrides) - set(base_hashes)
    if unknown:
        raise ValueError("source override outside canonical inventory: " + sorted(unknown)[0])
    texts = dict(baseline_texts)
    for rel, replacement in overrides.items():
        raw = replacement.encode("latin1") if isinstance(replacement, str) else bytes(replacement)
        texts[rel] = raw.decode("latin1")
    modules = {m["source"]: m for m in program["modules"]}
    if set(modules) != set(base_hashes):
        raise ValueError("program override changes canonical source inventory set")
    for rel, module in modules.items():
        if rel not in overrides and module["source_sha256"] != base_hashes[rel]:
            raise ValueError("program override source hash differs from canonical: " + rel)
    return texts, program, base_hashes, baseline_raw, program_raw


def ctype_macro_facts():
    toolchain = json.loads((ROOT / "layout/toolchain.json").read_text())
    profile = toolchain["profiles"]["msc600"]
    header_path = Path(profile["directory"]) / profile["include"] / "ctype.h"
    raw = header_path.read_bytes()
    expected = profile["include_files"]["ctype.h"]
    if sha(raw) != expected:
        raise ValueError("pinned MSC 6.00 ctype.h hash mismatch")
    text = raw.decode("latin1")
    definitions = {}
    for line in text.splitlines():
        m = re.match(r"\s*#\s*define\s+([A-Za-z_][A-Za-z_0-9]*)\s*\(([^)]*)\)\s*(.*)$", line)
        if m:
            definitions[m.group(1)] = {"params": m.group(2).strip(), "body": m.group(3).strip()}
    indexed = set()
    changed = True
    while changed:
        changed = False
        for name, row in definitions.items():
            body = row["body"]
            direct = "_ctype" in body and re.search(r"_ctype\s*\+\s*1", body)
            nested = any(re.search(r"\b" + re.escape(n) + r"\s*\(", body) for n in indexed)
            if (direct or nested) and name not in indexed:
                indexed.add(name)
                changed = True
    expected_indexed = {"isalpha", "isupper", "islower", "isdigit", "isxdigit", "isspace",
                        "ispunct", "isalnum", "isprint", "isgraph", "iscntrl", "toupper",
                        "tolower", "iscsymf", "iscsym"}
    if indexed != expected_indexed:
        raise ValueError("pinned MSC ctype macro dependency set changed")
    for name in expected_indexed:
        body = definitions[name]["body"]
        if "(unsigned)" in body or "(unsigned char)" in body:
            raise ValueError("ctype macro casts its argument unsigned: " + name)
    non_indexed = {name: definitions[name]["body"] for name in
                   ("_tolower", "_toupper", "isascii", "toascii") if name in definitions}
    return {"path": str(header_path).replace("\\", "/"), "sha256": sha(raw),
            "macro_definitions_sha256": sha(json.dumps(definitions, sort_keys=True,
                separators=(",", ":")).encode()),
            "indexed_macros": sorted(indexed),
            "non_indexing_macros": non_indexed,
            "unsigned_conversions_in_indexed_macros": []}


def _function_for(funcs, offset):
    return next((f for f in funcs if f.s <= offset < f.e), None)


def _balanced_end(tokens, start, left, right):
    depth = 0
    for i in range(start, len(tokens)):
        if tokens[i].text == left:
            depth += 1
        elif tokens[i].text == right:
            depth -= 1
            if depth == 0:
                return i
    raise ValueError("unbalanced source tokens")


def source_census(texts):
    rows, asm_rows = [], []
    table_readers = set(ctype_macro_facts_cached()["indexed_macros"])
    for path, text in sorted(texts.items()):
        if path.endswith(".asm"):
            for line_no, line in enumerate(text.splitlines(), 1):
                code = line.split(";", 1)[0]
                if re.search(r"(?i)(?<![A-Za-z0-9_])_ctype(?![A-Za-z0-9_])", code):
                    asm_rows.append([path, line_no, "_ctype"])
                for name in table_readers:
                    if re.search(r"(?i)\b" + re.escape(name) + r"\s*\(", code):
                        asm_rows.append([path, line_no, name])
            continue
        if not path.endswith(".c"):
            continue
        tokens = sig_tokens(text)
        funcs = csrc.Source(text).functions()
        uses_ctype_header = bool(re.search(r"(?im)^\s*#\s*include\s*[<\"]ctype\.h[>\"]", text))
        for i, tok in enumerate(tokens):
            fn = _function_for(funcs, tok.s)
            if fn is None:
                continue
            if tok.kind == "id" and tok.text == "_ctype":
                j = i + 1
                if j >= len(tokens):
                    continue
                if tokens[j].text == "[" and j + 1 < len(tokens) and tokens[j + 1].text == "]":
                    continue  # extern _ctype[] declaration
                if tokens[j].text not in {"[", "+"}:
                    continue
                if tokens[j].text == "+":
                    k = j + 1
                    while k < len(tokens) and tokens[k].text not in {"[", ";"}:
                        k += 1
                    if k >= len(tokens) or tokens[k].text != "[":
                        continue
                    bracket = k
                else:
                    bracket = j
                end = _balanced_end(tokens, bracket, "[", "]")
                start = i - 1 if tokens[j].text == "+" and i > 0 and tokens[i - 1].text == "(" else i
                expr = token_text(tokens[start:end + 1])
                rows.append({"source": path, "line": text.count("\n", 0, tok.s) + 1,
                             "function": fn.name, "kind": "direct", "callee": "direct",
                             "index_expression": expr, "offset": tok.s})
            elif tok.kind == "id" and tok.text in table_readers and i + 1 < len(tokens) and tokens[i + 1].text == "(":
                close = _balanced_end(tokens, i + 1, "(", ")")
                arg = token_text(tokens[i + 2:close])
                rows.append({"source": path, "line": text.count("\n", 0, tok.s) + 1,
                             "function": fn.name, "kind": "macro" if uses_ctype_header else "runtime", "callee": tok.text,
                             "index_expression": tok.text + "(" + arg + ")", "offset": tok.s})
    rows.sort(key=lambda r: (r["source"], r["line"], r["offset"]))
    asm_rows.sort()
    return rows, asm_rows


def _function_text(texts, path, name):
    text = texts[path]
    fn = csrc.Source(text).function(name)
    return text, fn, text[fn.head_s:fn.body.e]


def _line_function(texts, path, line):
    text = texts[path]
    funcs = csrc.Source(text).functions()
    at = 0
    for n, piece in enumerate(text.splitlines(keepends=True), 1):
        if n == line:
            fn = _function_for(funcs, at)
            return text, fn
        at += len(piece)
    raise ValueError("expected source line absent: " + path + ":" + str(line))


def _case_value(tokens):
    spelling = token_text(tokens)
    if len(tokens) == 1 and tokens[0].kind == "chr":
        value = ast.literal_eval(tokens[0].text)
        if len(value) != 1:
            raise ValueError("multi-character switch label unsupported")
        return ord(value)
    if len(tokens) == 1 and tokens[0].kind == "num":
        return int(re.sub(r"[uUlL]+$", "", tokens[0].text), 0)
    if len(tokens) == 2 and tokens[0].text == "-" and tokens[1].kind == "num":
        return -int(re.sub(r"[uUlL]+$", "", tokens[1].text), 0)
    raise ValueError("unmodeled switch case label: " + spelling)


def check_unobservable_switch(text: str):
    fn = csrc.Source(text).function("f_1C62_00D5")
    switches = [n for n in csrc.walk(fn.body) if isinstance(n, csrc.Switch)]
    if len(switches) != 1:
        raise ValueError("m1C62:170 lemma requires one switch")
    sw = switches[0]
    switch_expr = norm(text[sw.c.s:sw.c.e])
    arms = [t.text for t in sig_tokens(text[sw.c.s:sw.c.e])]
    expected_tokens = ["(", "_ctype", "[", "c", "+", "1", "]", "&", "2", ")", "?",
                       "c", "-", "0x20", ":", "c"]
    if arms != expected_tokens:
        raise ValueError("m1C62:170 conditional arms changed")
    labels = []
    for node in csrc.walk(sw.body):
        if isinstance(node, csrc.Case):
            if node.x is None:
                labels.append({"tokens": "default", "value": None})
            else:
                case_tokens = sig_tokens(text[node.x.s:node.x.e])
                value = _case_value(case_tokens)
                if -128 <= value <= -1:
                    raise ValueError("m1C62:170 lemma broken by a negative case label")
                labels.append({"tokens": token_text(case_tokens), "value": value})
    labels.sort(key=lambda r: (r["value"] is None, r["value"] if r["value"] is not None else 0))
    expected = [{"tokens": "'\\n'", "value": 10}, {"tokens": "'\\r'", "value": 13},
                {"tokens": "'C'", "value": 67}]
    if labels != expected:
        raise ValueError("m1C62:170 switch case-label set changed")
    # Prove the local c has no other token-visible write or address escape.
    body_tokens = [t.text for t in sig_tokens(text[fn.body.s:fn.body.e])]
    assignment = ["c", "=", "f_1F58_005A", "(", ")"]
    writes = []
    assignment_ops = {"=", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "<<=", ">>="}
    for i, token in enumerate(body_tokens):
        if token != "c":
            continue
        following = body_tokens[i + 1] if i + 1 < len(body_tokens) else None
        preceding = body_tokens[i - 1] if i else None
        if following in assignment_ops | {"++", "--"} or preceding in {"++", "--"}:
            writes.append(body_tokens[i:i + 5])
        if preceding == "&":
            raise ValueError("m1C62:170 c address escapes its local producer")
    if writes != [assignment]:
        raise ValueError("m1C62:170 c producer changed")
    if not contains_tokens(text[fn.body.s:fn.body.e], "if ( ( c = f_1F58_005A ( ) ) == 0 ) f_1F58_005A ( )"):
        raise ValueError("m1C62:170 zero-key producer path changed")
    return {"switch_expression": switch_expr, "conditional_arms": ["c - 0x20", "c"],
            "case_labels": labels, "c_producer": "f_1F58_005A only",
            "c_write_tokens": ["c = f_1F58_005A ( )"],
            "producer_range": [-128, 255], "negative_input_range": [-128, -1],
            "arm_bounds_for_negative_input": {"c_minus_0x20": [-160, -33], "c": [-128, -1]},
            "unobservable": True}


def verify_source_assumptions(texts):
    # Guard and producer checks are deliberately statement-shaped token checks.
    for path in ("src/S09/m35F5.c", "src/S10/m35F5.c"):
        if not re.search(r"(?im)^\s*#\s*include\s*[<\"]ctype\.h[>\"]", texts[path]):
            raise ValueError("MSC ctype.h macro user lost its pinned include: " + path)
    if re.search(r"(?im)^\s*#\s*include\s*[<\"]ctype\.h[>\"]", texts["src/S20/m39F1.c"]):
        raise ValueError("S20 runtime ctype calls unexpectedly became header macros")
    s09, f09, f09text = _function_text(texts, "src/S09/m35F5.c", "o09_35F5_03C6")
    if not contains_tokens(f09text, "!( key & 0x800 ) && isalnum ( key )"):
        raise ValueError("S09 key guard before isalnum changed")
    if not contains_tokens(f09text, "key = f_1F58_0090 ( )"):
        raise ValueError("S09 isalnum key is no longer the BIOS key result")
    s10, f10, f10text = _function_text(texts, "src/S10/m35F5.c", "o10_35F5_0384")
    if not contains_tokens(f10text, "!( key & 0x800 ) && islower ( key )"):
        raise ValueError("S10 lower-key guard before islower changed")
    if not contains_tokens(f10text, "if ( key & 0x800 ) goto flush"):
        raise ValueError("S10 high-key flush guard changed")
    t10 = [t.text for t in sig_tokens(f10text)]
    isalpha_pos = t10.index("isalpha")
    high_guard_pos = max(i for i in range(isalpha_pos) if t10[i:i + 3] == ["key", "&", "0x800"])
    if high_guard_pos >= isalpha_pos:
        raise ValueError("S10 isalpha site precedes high-key guard")
    if not contains_tokens(f10text, "c = items [ k ] [ 1 ]"):
        raise ValueError("S10 mnemonic producer changed")
    if not contains_tokens(f10text, "key = f_1F58_0090 ( )"):
        raise ValueError("S10 key producer changed")
    if not contains_tokens(f10text, "int far o10_35F5_0384 ( char far * sel , char far * far * items )"):
        raise ValueError("S10 items parameter type changed")
    s10caller = csrc.Source(texts["src/S10/m35F5.c"]).function("o10_35F5_01C3")
    if not contains_tokens(texts["src/S10/m35F5.c"][s10caller.head_s:s10caller.body.e],
                           "o10_35F5_0384 ( & sel , fd_55B3_6054 [ m + 1 ] )"):
        raise ValueError("S10 keyboard-menu caller no longer supplies the loaded item list")

    shared_startup = csrc.Source(texts["src/S20/m39F1.c"]).function("IBMInitStuff")
    shared_startup_text = texts["src/S20/m39F1.c"][shared_startup.head_s:shared_startup.body.e]
    if not contains_tokens(shared_startup_text, 'db_SetDataBase ( "shared" )'):
        raise ValueError("S10 menu resource database producer changed")
    menu_loader = csrc.Source(texts["src/S17/m384C.c"]).function("o17_384C_0039")
    menu_loader_text = texts["src/S17/m384C.c"][menu_loader.head_s:menu_loader.body.e]
    if not contains_tokens(menu_loader_text, "db_LoadObject ( id , 6 )") or \
       not contains_tokens(menu_loader_text, "fd_55B3_6054 = * h"):
        raise ValueError("S10 SHARED kind-6 menu loader producer changed")
    if not contains_tokens(shared_startup_text,
            "if ( g_3DB2 != 320 || ! o17_384C_0039 ( 1 ) ) if ( ! o17_384C_0039 ( 0 ) ) Punt"):
        raise ValueError("S10 kind-6 menu ID 1 fallback to ID 0 changed")

    s20, f20, f20text = _function_text(texts, "src/S20/m39F1.c", "IBMInitStuff")
    if not contains_tokens(f20text, "v = argv [ i ] [ 2 ]"):
        raise ValueError("S20 /s argv-byte producer changed")
    if not contains_tokens(f20text, "if ( isdigit ( v ) )"):
        raise ValueError("S20 /s ctype call changed")
    readword = csrc.Source(texts["src/S20/m39F1.c"]).function("ReadWord")
    readword_text = texts["src/S20/m39F1.c"][readword.head_s:readword.body.e]
    if readword_text.count("isspace(c)") != 2 or not contains_tokens(readword_text, "char c"):
        raise ValueError("S20 ReadWord byte producer/calls changed")
    config = csrc.Source(texts["src/S20/m39F1.c"]).function("ReadConfig")
    config_text = texts["src/S20/m39F1.c"][config.head_s:config.body.e]
    if not contains_tokens(config_text, "open ( fd_55B3_1CE4 , 0 )"):
        raise ValueError("S20 fixed SIMANT.CFG producer changed")
    root_startup = texts["src/root/m15F8.c"]
    root_startup_tokens = sig_tokens(root_startup)
    if not contains_tokens(root_startup, '"simant.cfg"'):
        raise ValueError("S20 configuration filename initializer changed")
    string_array = next(i for i, token in enumerate(root_startup_tokens)
                        if token.kind == "id" and token.text == "fd_55B3_1CD4")
    brace = next(i for i in range(string_array, len(root_startup_tokens))
                 if root_startup_tokens[i].text == "{")
    end_brace = _balanced_end(root_startup_tokens, brace, "{", "}")
    config_string_slots = [t.text for t in root_startup_tokens[brace + 1:end_brace] if t.kind == "str"]
    if len(config_string_slots) != 5 or config_string_slots[4] != '"simant.cfg"':
        raise ValueError("S20 config pointer is not the fifth root filename slot")
    symbols_raw = (ROOT / "layout/symbols.json").read_bytes()
    symbol_doc = json.loads(symbols_raw)
    symbol_map = {}
    for section in symbol_doc.values():
        if isinstance(section, dict):
            symbol_map.update({k: v for k, v in section.items() if isinstance(v, dict) and "seg" in v and "off" in v})
    base_name = symbol_map.get("fd_55B3_1CD4")
    config_name = symbol_map.get("fd_55B3_1CE4")
    if not (base_name and config_name and base_name["seg"] == config_name["seg"] and
            config_name["off"] - base_name["off"] == 0x10):
        raise ValueError("S20 config path alias is not root filename-array slot four")
    if not contains_tokens(config_text, "SkipWords ( fd , 2 ) ; read ( fd , & mode , 1 )") or \
       not contains_tokens(config_text, "SkipWords ( fd , 2 ) ; read ( fd , & lang , 1 )"):
        raise ValueError("S20 config stream positions changed")

    renderer, frender, renderer_text = _function_text(texts, "src/S23/m39C7.c", "win_PrintStyleTextInRect")
    if not contains_tokens(renderer_text, "if ( record && styles [ styleIdx - 1 ] . face == 0x100 )"):
        raise ValueError("S23 face-0100 record guard changed")
    if not contains_tokens(renderer_text, "( _ctype + 1 ) [ buf [ start ] ] & 2"):
        raise ValueError("S23 direct index expression changed")
    renderer_requirements = (
        ("if ( styl && * styl > styleIdx + 1 && styles [ styleIdx + 1 ] . pos <= ( long ) pos )",
         "style transition is no longer a single conditional per iteration"),
        ("styleIdx ++ ; n = pos - start",
         "style transition no longer advances once before classifying the preceding run"),
        ("start = pos ; } w += f_24AB_0367 ( text [ pos ] )",
         "renderer transition/character-consumption order changed"),
        ("case ' ' : case '(' : case '[' : case '{' : brk = pos",
         "renderer brk-at delimiters changed"),
        ("case '!' : case ')' : case ',' : case '-' : case '.' : case '?' : case ']' : case '}' : brk = pos + 1",
         "renderer brk-after delimiters changed"),
        ("if ( end < start ) start = end",
         "renderer no longer resets start when a line rewinds"),
        ("while ( text [ end ] == ' ' ) end ++",
         "renderer post-line space skipping changed"),
        ("if ( text [ end ] == '\\n' || text [ end ] == '\\r' ) end ++",
         "renderer post-line CR/LF skipping changed"),
        ("pos = end",
         "renderer no longer rewinds/advances pos from end"),
    )
    for spelling, message in renderer_requirements:
        if not contains_tokens(renderer_text, spelling):
            raise ValueError(message)
    displaycard = csrc.Source(texts["src/S23/m39C7.c"]).function("DisplayCard")
    display_text = texts["src/S23/m39C7.c"][displaycard.head_s:displaycard.body.e]
    for spelling in ("f_1A53_00F0 ( card , 0x11 , 1 )",
                     "f_1A53_00F0 ( rez , 10 , 1 )",
                     "f_1A53_00F0 ( rez , 0x15 , 1 )",
                     "win_PrintStyleTextInRect ( text , styl , & tr . r , 0 , 2 , 5 , 1 )",
                     "while ( ( nul = _fmemchr ( text , 0 , tlen - 4 ) ) != 0 )",
                     "while ( * q < ' ' && off < tlen - 4 )"):
        if not contains_tokens(display_text, spelling):
            raise ValueError("S23 DisplayCard resource/cleanup producer changed: " + spelling)
    popup = [f for f in csrc.Source(texts["src/S23/m39C7.c"]).functions()]
    call_args = []
    for fn in popup:
        for node in csrc.walk(fn.body):
            if isinstance(node, csrc.Call) and isinstance(node.f, csrc.Id) and node.f.name == "win_PrintStyleTextInRect":
                args = [norm(texts["src/S23/m39C7.c"][a.s:a.e]) for a in node.args]
                call_args.append([fn.name, args])
    if sorted((x[0], x[1][-1]) for x in call_args) != sorted([
            ("DisplayCard", "1"), ("PopUpInfoWindow", "0")]):
        raise ValueError("S23 style-renderer caller/record set changed")

    root, froot, root_text = _function_text(texts, "src/root/m1C62.c", "f_1C62_00D5")
    lemma = check_unobservable_switch(root_text)
    if not contains_tokens(root_text,
            "if ( f_1F58_0038 ( ) ) { if ( ( c = f_1F58_005A ( ) ) == 0 ) f_1F58_005A ( ) ; switch"):
        raise ValueError("m1C62:170 keyboard input reaches switch without the reviewed branch shape")
    wrapper = csrc.Source(texts["src/root/m1C62.c"]).function("f_1C62_00C0")
    wrapper_text = texts["src/root/m1C62.c"][wrapper.head_s:wrapper.body.e]
    if not contains_tokens(wrapper_text, "f_1C62_00D5 ( msg , 1 )"):
        raise ValueError("m1C62 timed alert wrapper changed")
    savefn = csrc.Source(texts["src/S09/m35F5.c"]).function("o09_35F5_0188")
    save_text = texts["src/S09/m35F5.c"][savefn.head_s:savefn.body.e]
    if not contains_tokens(save_text, 'sprintf ( msg , "%s\\nSaved correctly" , name )') or \
       not contains_tokens(save_text, "f_1C62_00C0 ( msg )"):
        raise ValueError("successful-save alert producer changed")
    root_choice = csrc.Source(texts["src/root/m1C62.c"]).function("f_1C62_0415")
    choice_text = texts["src/root/m1C62.c"][root_choice.head_s:root_choice.body.e]
    if not contains_tokens(choice_text, "( c = f_1F58_0090 ( ) ) > 0"):
        raise ValueError("root choice-key positive guard changed")
    expected_calls = {
        "ReadConfig": [("src/S20/m39F1.c", "IBMInitStuff", 1)],
        "SkipWords": [("src/S20/m39F1.c", "ReadConfig", 2)],
        "ReadWord": [("src/S20/m39F1.c", "SkipWords", 1)],
        "DisplayCard": [("src/S23/m39C7.c", "win_DrawInfoWindow", 1)],
        "o10_35F5_0384": [("src/S10/m35F5.c", "o10_35F5_01C3", 1)],
        "o17_384C_0039": [("src/S20/m39F1.c", "IBMInitStuff", 2)],
    }
    call_graph = {target: [] for target in expected_calls}
    for path, source in sorted(texts.items()):
        if not path.endswith(".c"):
            continue
        for caller in csrc.Source(source).functions():
            for node in csrc.walk(caller.body):
                if isinstance(node, csrc.Call) and isinstance(node.f, csrc.Id) and node.f.name in call_graph:
                    call_graph[node.f.name].append({"source": path,
                        "line": source.count("\n", 0, node.s) + 1, "caller": caller.name,
                        "callee": node.f.name,
                        "arguments": [norm(source[arg.s:arg.e]) for arg in node.args]})
    for target, expected_rows in expected_calls.items():
        observed_counts = Counter((r["source"], r["caller"]) for r in call_graph[target])
        observed_rows = sorted((source, caller, count)
                               for (source, caller), count in observed_counts.items())
        if observed_rows != sorted(expected_rows):
            raise ValueError("direct producer call census changed for " + target)
    if sorted(r["arguments"] for r in call_graph["o17_384C_0039"]) != [["0"], ["1"]]:
        raise ValueError("S20 menu resource ID call set changed")
    call_graph["win_PrintStyleTextInRect"] = call_args
    config_filename = {
        "array": "fd_55B3_1CD4",
        "slot_index": 4,
        "string": "simant.cfg",
        "array_symbol": {"seg": base_name["seg"], "off": base_name["off"]},
        "config_pointer_symbol": {"seg": config_name["seg"], "off": config_name["off"]},
        "far_pointer_width_bytes": 4,
        "symbols_sha256": sha(symbols_raw),
    }
    renderer_contract = {
        "source": "src/S23/m39C7.c:179-267",
        "transition": "one styleIdx++ in one if per loop iteration, before text[pos] is consumed",
        "rewind": "end=brk; if end<start then start=end; pos=end; styleIdx is not rewound",
        "brk_at_bytes": ["20", "28", "5B", "7B"],
        "brk_after_bytes": ["21", "29", "2C", "2D", "2E", "3F", "5D", "7D"],
        "post_line_skips": ["spaces", "one CR or LF"],
        "expanded_span_break_bytes": [f"{b:02X}" for b in sorted(RENDERER_BREAK_BYTES)],
        "right_extension_bound": "a transition inside skipped whitespace extends through its post-skip destination; the next style position is strictly beyond that destination, so the one-transition-per-iteration rule cannot delay a later transition",
        "initial_run": "renderer starts at text offset 0; its first classified argument is conservatively bounded from 0",
        "final_run": "no ctype call occurs after the last style transition; the final style has no outgoing transition",
    }
    return {"guards": {
        "S09_429": "!(key & 0x800) before isalnum(key)",
        "S10_305": "!(key & 0x800) before islower(key)",
        "S10_325": "key & 0x800 -> flush before isalpha(key)",
        "S10_351": "c = items[k][1]; main selects SHARED; kind-6 loader populates fd_55B3_6054",
        "S20_117": "v = argv[i][2]",
        "S20_189_193": "ReadConfig opens simant.cfg -> SkipWords -> ReadWord -> read stream",
        "S20_255": "ReadConfig reads lang after two SkipWords",
        "S23_201": "record && previous face == 0x100",
        "root_170": "c from f_1F58_005A; no byte range guard",
        "root_306": "c = f_1F58_0090() > 0 before table test",
    }, "renderer_contract": renderer_contract,
       "m1C62_170_lemma": lemma,
       "producer_call_census": call_graph,
        "save_alert_chain": ["o09_35F5_0188", "f_1C62_00C0(msg)", "f_1C62_00D5(msg,1)"],
        "configuration_filename": config_filename}


def resource_facts():
    spec = importlib.util.spec_from_file_location("ctype_resource_domains", ROOT / "tools/resource_domains.py")
    domains = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(domains)
    report = domains.collect()  # checks all six .DAT/.NDX hashes against oracle.lock.json
    decoder = domains.decoder()
    records = {}
    all_rows = []
    for database in ("SHARED", "HCEGANT", "SOUND"):
        _, rows = decoder.parse_records(database)
        records[database] = rows
        for row in rows:
            if row["kind"] not in {6, 10, 17, 21}:
                continue
            payload = row["payload"]
            raw_hist = Counter(b for b in payload if b >= 0x80)
            item = {"database": database, "id": row["id"], "kind": row["kind"],
                    "payload_bytes": len(payload), "payload_sha256": sha(payload),
                    "raw_high_byte_counts": {f"{b:02X}": raw_hist[b] for b in sorted(raw_hist)}}
            if row["kind"] == 6:
                detail = domains.menu_domain(payload)
                strings = bytearray()
                for pointer_list in detail["lists"]:
                    for pos in pointer_list["string_offsets"]:
                        end = payload.find(b"\0", pos)
                        if end < 0:
                            raise ValueError("unterminated SHARED kind-6 menu string")
                        strings.extend(payload[pos:end])
                text_hist = Counter(b for b in strings if b >= 0x80)
                item.update(menu_text_bytes=len(strings), menu_text_high_byte_counts={
                    f"{b:02X}": text_hist[b] for b in sorted(text_hist)},
                    menu_string_count=sum(len(x["string_offsets"]) for x in detail["lists"]),
                    menu_completely_tiled=detail["completely_tiled"])
            elif row["kind"] == 10:
                leading = payload.split(b"\0", 1)[0]
                hist = Counter(b for b in leading if b >= 0x80)
                item.update(leading_text_bytes=len(leading), leading_text_high_byte_counts={
                    f"{b:02X}": hist[b] for b in sorted(hist)},
                    leading_text_high_byte_offsets=[i for i, b in enumerate(leading) if b >= 0x80])
            all_rows.append(item)

    shared = {(r["id"], r["kind"]): r["payload"] for r in records["SHARED"]}
    cards = []
    text_ids = set()
    for row in records["SHARED"]:
        if row["kind"] != 17:
            continue
        payload = row["payload"]
        pos, ids = 4, []
        while pos < len(payload):
            if pos + 4 > len(payload):
                raise ValueError("short kind-17 card record header")
            tag = payload[pos]
            pos += 4
            if tag == ord("P"):
                if pos + 12 > len(payload):
                    raise ValueError("short kind-17 picture record")
                nlinks = int.from_bytes(payload[pos + 10:pos + 12], "big")
                pos += 12 + nlinks * 10
            elif tag == ord("T"):
                if pos + 10 > len(payload):
                    raise ValueError("short kind-17 text record")
                frames = int.from_bytes(payload[pos + 8:pos + 10], "big")
                pos += 10
                if pos + frames * 2 > len(payload):
                    raise ValueError("short kind-17 text id list")
                ids.extend(int.from_bytes(payload[pos + i * 2:pos + i * 2 + 2], "big")
                           for i in range(frames))
                pos += frames * 2
            else:
                raise ValueError("unknown kind-17 record tag")
            if pos > len(payload):
                raise ValueError("kind-17 record exceeds resource extent")
        if pos != len(payload):
            raise ValueError("kind-17 record tail")
        for ident in ids:
            if (ident, 10) not in shared:
                raise ValueError("kind-17 record references absent kind-10 text")
        text_ids.update(ids)
        cards.append({"id": row["id"], "text_ids": ids})
    unique_text = sorted(text_ids)
    styled_text = []
    face_ranges = []
    renderer_rows = []
    cleanup_summary = []
    for ident in unique_text:
        raw = shared[(ident, 10)]
        style_raw = shared.get((ident, 21))
        if style_raw is None:
            styled_text.append({"id": ident, "style_present": False})
            continue
        if len(style_raw) < 2:
            raise ValueError("short kind-21 style header")
        n = struct.unpack_from(">H", style_raw)[0]
        if len(style_raw) != 2 + 20 * n:
            raise ValueError("kind-21 style extent mismatch")
        runs = [list(struct.unpack_from(">I8H", style_raw, 2 + 20 * i)) for i in range(n)]
        if [r[0] for r in runs] != sorted(r[0] for r in runs):
            raise ValueError("kind-21 style positions are not ordered")
        text = bytearray(raw)
        tlen, edits = len(text), 0
        while True:
            stop = max(0, tlen - 4)
            try:
                nul = text.index(0, 0, stop)
            except ValueError:
                break
            off = q = nul
            while q < tlen - 4 and (text[q] if text[q] < 0x80 else text[q] - 0x100) < 0x20:
                q += 1
                off += 1
            removed = q - nul
            moved = bytes(text[q:tlen])
            text[nul:nul + len(moved)] = moved
            del text[nul + len(moved):]
            for run in runs:
                if run[0] >= off:
                    run[0] -= removed
            tlen -= removed
            edits += 1
        first_nul = text.find(0)
        visible = bytes(text if first_nul < 0 else text[:first_nul])
        original_runs = [list(struct.unpack_from(">I8H", style_raw, 2 + 20 * i)) for i in range(n)]
        high_ranges = []
        for i in range(1, len(runs)):
            if original_runs[i - 1][4] != 0x100:
                continue
            start = max(0, min(runs[i - 1][0], len(visible)))
            end = max(0, min(runs[i][0], len(visible)))
            span = visible[start:end] if end >= start else b""
            hist = Counter(b for b in span if b >= 0x80)
            face_ranges.append({"id": ident, "start": start, "end": end,
                                "high_byte_counts": {f"{b:02X}": hist[b] for b in sorted(hist)}})
            if hist:
                high_ranges.append({"start": start, "end": end,
                                   "high_byte_counts": {f"{b:02X}": hist[b] for b in sorted(hist)}})
        try:
            conservative_spans = require_renderer_spans_ascii(visible, runs, f"SHARED kind-10 ID {ident}")
        except ValueError as exc:
            raise ValueError(f"SHARED kind-10 text ID {ident}: {exc}") from exc
        skipped_transitions = [{"run_index": i, "position": run[0], "byte": f"{visible[run[0]]:02X}",
                               "skip_destination": _renderer_skip_destination(visible, run[0]),
                               "next_style_position": runs[i + 1][0] if i + 1 < len(runs) else None,
                               "previous_face": int(runs[i - 1][4]),
                               "classifies_face_0100": int(runs[i - 1][4]) == 0x100}
                                for i, run in enumerate(runs[1:], 1)
                                if run[0] < len(visible) and visible[run[0]] in RENDERER_SKIP_BYTES]
        run_facts = [{"index": i, "position": int(run[0]), "face": int(run[4])}
                     for i, run in enumerate(runs)]
        renderer_rows.append({"id": ident, "visible_bytes": len(visible),
                              "transformed_style_positions": [row["position"] for row in run_facts],
                              "style_positions_strictly_ordered": True,
                              "skipped_transition_positions": skipped_transitions,
                              "initial_run": run_facts[0] if run_facts else None,
                              "final_run": run_facts[-1] if run_facts else None,
                              "transition_count": max(0, len(runs) - 1),
                              "face_0100_arguments": conservative_spans})
        styled_text.append({"id": ident, "style_present": True,
                            "raw_bytes": len(raw), "visible_bytes": len(visible),
                            "cleanup_edits": edits, "face_0100_range_count": sum(
                                1 for x in face_ranges if x["id"] == ident),
                            "face_0100_ranges_with_high_bytes": high_ranges})
        cleanup_summary.append({"id": ident, "edits": edits, "visible_bytes": len(visible)})

    ids_by_kind = {}
    for database in ("SHARED", "HCEGANT", "SOUND"):
        for kind in (6, 10, 17, 21):
            ids_by_kind[f"{database}:{kind}"] = sorted(r["id"] for r in records[database] if r["kind"] == kind)
    cfg_raw = (ROOT / "assets/SIMANT.CFG").read_bytes()
    cfg_hist = Counter(b for b in cfg_raw if b >= 0x80)
    menu = next((x for x in all_rows if x["database"] == "SHARED" and x["kind"] == 6), None)
    if menu is None or menu["id"] != 0 or menu["menu_text_bytes"] != 262:
        raise ValueError("SHARED kind-6 menu domain changed")
    rewind_control = renderer_rewind_negative_control()
    renderer_high = [{"id": row["id"], "transition_index": span["transition_index"],
                      "high_byte_counts": span["high_byte_counts"]}
                     for row in renderer_rows for span in row["face_0100_arguments"]
                     if span["high_byte_counts"]]
    return {"asset_identities": report["assets"],
            "corpus": report["corpus"],
            "record_ids_by_database_kind": ids_by_kind,
            "resource_high_bytes": all_rows,
            "consumer_domains": {"SHARED_kind6_menu": {
                    "id": 0, "decoded_text_bytes": menu["menu_text_bytes"],
                    "text_high_byte_counts": menu["menu_text_high_byte_counts"],
                    "raw_payload_high_byte_counts": menu["raw_high_byte_counts"],
                    "text_strings": menu["menu_string_count"],
                    "completely_tiled": menu["menu_completely_tiled"]},
                "SHARED_kind17_cards": {"ids": [x["id"] for x in cards], "count": len(cards),
                    "unique_kind10_text_ids": unique_text,
                    "text_reference_sha256": sha(json.dumps(cards, sort_keys=True,
                        separators=(",", ":")).encode()),
                    "unique_kind21_style_ids": sorted(i for i in unique_text if (i, 21) in shared),
                    "kind10_without_kind21": sorted(i for i in unique_text if (i, 21) not in shared)},
                "DisplayCard_transformed_texts": styled_text,
                "DisplayCard_cleanup_summary": cleanup_summary,
                "DisplayCard_face_0100_ranges": face_ranges,
                "DisplayCard_face_0100_ranges_with_high_bytes": [x for x in face_ranges if x["high_byte_counts"]],
                "DisplayCard_renderer_coverage": {"model": "conservative expanded spans",
                    "records": renderer_rows,
                    "face_0100_arguments_with_high_bytes": renderer_high,
                    "transition_order": "strictly increasing positions after cleanup",
                    "one_transition_per_iteration": "source if advances one style index before consuming one text byte",
                    "skipped_characters": "renderer skips spaces and one CR/LF after a line; each crossed transition's candidate includes its post-skip destination, and the next style position is beyond that destination",
                    "initial_and_final_runs": "first argument extends from renderer offset 0; the final run has no outgoing transition",
                    "rewind_negative_control": rewind_control}},
            "SIMANT_CFG": {"path": "assets/SIMANT.CFG", "bytes": len(cfg_raw),
                "sha256": sha(cfg_raw), "high_byte_counts": {f"{b:02X}": cfg_hist[b] for b in sorted(cfg_hist)},
                "all_bytes_ascii": all(b < 0x80 for b in cfg_raw)}}


def original_disassembly(site_rows):
    try:
        import capstone
        import exe
        import functions
    except ImportError as exc:
        raise RuntimeError("run with PYTHONPATH=C:/tools/capstone-5.0.3") from exc
    oracle = json.loads((ROOT / "layout/oracle.lock.json").read_text())
    machine = exe.load()
    if machine.sha256 != oracle["executable"]["sha256"]:
        raise ValueError("original executable differs from oracle lock")
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_16)
    md.detail = True
    grouped = {}
    for row in site_rows:
        if row["callee"] == "direct" or row["callee"] in CTYPE_STANDARD:
            grouped.setdefault(row["function"], []).append(row)
    by_function = {}
    site_anchors = {}
    for name, rows in grouped.items():
        info = functions.get(name)
        code = machine.read(info["unit"], info["seg"] * 16 + info["off"], info["size"])
        instructions = list(md.disasm(code, info["off"]))
        rendered = [{"address": ins.address, "mnemonic": ins.mnemonic, "operands": ins.op_str}
                    for ins in instructions]
        table_reads = [x["address"] for x in rendered if "0x7a1f" in x["operands"].lower()]
        bit_0800_tests = [x["address"] for x in rendered if x["mnemonic"] == "test" and
                          ("0x800" in x["operands"].lower() or x["operands"].lower() == "ah, 8")]
        runtime_calls = []
        symbols = json.loads((ROOT / "layout/symbols.json").read_text())
        symbol_map = {**symbols.get("runtime", {}), **symbols.get("code", {})}
        for ins in rendered:
            if ins["mnemonic"] not in {"lcall", "call"}:
                continue
            for target in ("_isdigit", "_isspace"):
                sym = symbol_map.get(target)
                if sym and f"0x{sym['off']:x}" in ins["operands"].lower():
                    runtime_calls.append({"address": ins["address"], "target": target})
        direct_rows = [r for r in rows if r["kind"] != "runtime"]
        expected_direct = len(direct_rows)
        if table_reads and len(table_reads) < expected_direct:
            raise ValueError("original direct ctype lookup count is short: " + name)
        if direct_rows and len(table_reads) != expected_direct:
            raise ValueError("original direct ctype lookup/site count differs: " + name)
        for row, address in zip(direct_rows, table_reads):
            previous_cwde = [x["address"] for x in rendered
                             if x["mnemonic"] == "cwde" and x["address"] < address]
            site_anchors[f"{row['source']}:{row['line']}"] = {
                "compiled_function": name, "original_index_instruction": address,
                "nearest_preceding_cwde": previous_cwde[-1] if previous_cwde else None,
                "disassembly_sha256": sha(json.dumps(rendered, separators=(",", ":")).encode())}
        runtime_rows = [r for r in rows if r["kind"] == "runtime"]
        for row in runtime_rows:
            target = "_" + row["callee"]
            calls = [x for x in runtime_calls if x["target"] == target]
            consumed = sum(1 for earlier in runtime_rows
                           if earlier["callee"] == row["callee"] and earlier["line"] < row["line"])
            if consumed >= len(calls):
                raise ValueError("original runtime ctype call/site count differs: " + name)
            call_address = calls[consumed]["address"]
            prior_cwde = [x["address"] for x in rendered
                          if x["mnemonic"] == "cwde" and x["address"] < call_address]
            site_anchors[f"{row['source']}:{row['line']}"] = {
                "compiled_function": name, "original_runtime_call_instruction": call_address,
                "target": target, "nearest_preceding_cwde": prior_cwde[-1] if prior_cwde else None,
                "disassembly_sha256": sha(json.dumps(rendered, separators=(",", ":")).encode())}
        by_function[name] = {"unit": info["unit"], "segment": info["seg"], "offset": info["off"],
            "size": info["size"], "disassembly_sha256": sha(json.dumps(rendered, separators=(",", ":")).encode()),
            "table_read_addresses": table_reads, "runtime_ctype_calls": runtime_calls,
            "bit_0800_test_addresses": bit_0800_tests,
            "cwde_addresses": [x["address"] for x in rendered if x["mnemonic"] == "cwde"]}

    def fn_instructions(name):
        info = functions.get(name)
        code = machine.read(info["unit"], info["seg"] * 16 + info["off"], info["size"])
        return info, list(md.disasm(code, info["off"]))
    inp, ins = fn_instructions("f_1F58_005A")
    if not any(i.mnemonic == "int" and i.op_str == "0x16" for i in ins) or not any(i.mnemonic == "cwde" for i in ins):
        raise ValueError("original BIOS character reader lacks INT16/CBW proof")
    pending_clear = next((i for i in ins if i.address == 0x72), None)
    if not (pending_clear and pending_clear.mnemonic == "xor" and pending_clear.op_str == "ah, ah"):
        raise ValueError("original pending-key path does not clear AH before return")
    wrapper_info, wrapper_ins = fn_instructions("f_1F58_0090")
    if not any(i.mnemonic in {"lcall", "call"} and "0x5a" in i.op_str.lower() for i in wrapper_ins):
        raise ValueError("original keyboard wrapper no longer calls f_1F58_005A")
    for key in ("src/S09/m35F5.c:429", "src/S10/m35F5.c:305", "src/S10/m35F5.c:325"):
        site_anchors[key]["keyboard_conversion"] = "f_1F58_005A INT16+CBW; f_1F58_0090 propagates result"
    site_anchors["src/root/m1C62.c:170"]["keyboard_conversion"] = "f_1F58_005A INT16+CBW; c is assigned from this return"
    site_anchors["src/root/m1C62.c:306"]["keyboard_conversion"] = "f_1F58_005A INT16+CBW via f_1F58_0090; source c>0 guard"
    # v is a long: original code sign-extends argv[i][2] to DX:AX before the runtime call.
    ibm_info = by_function["IBMInitStuff"]
    ibm_code = machine.read(ibm_info["unit"], ibm_info["segment"] * 16 + ibm_info["offset"], ibm_info["size"])
    ibm_ins = {i.address: i for i in md.disasm(ibm_code, ibm_info["offset"])}
    if not (ibm_ins.get(0x3D) and ibm_ins[0x3D].mnemonic == "mov" and
            ibm_ins.get(0x41) and ibm_ins[0x41].mnemonic == "cwde" and
            ibm_ins.get(0x42) and ibm_ins[0x42].mnemonic == "cdq"):
        raise ValueError("original /s argument is not sign-extended into long v")
    site_anchors["src/S20/m39F1.c:117"]["argv_byte_load_cwde_cdq"] = [0x3D, 0x41, 0x42]
    for key, name, load_address in (("src/S20/m39F1.c:189", "ReadWord", 0x3FF),
                                    ("src/S20/m39F1.c:193", "ReadWord", 0x433),
                                    ("src/S20/m39F1.c:255", "ReadConfig", 0x569)):
        info = by_function[name]
        code = machine.read(info["unit"], info["segment"] * 16 + info["offset"], info["size"])
        instructions = {i.address: i for i in md.disasm(code, info["offset"])}
        if not (instructions.get(load_address) and instructions[load_address].mnemonic == "mov" and
                instructions.get(load_address + 3) and instructions[load_address + 3].mnemonic == "cwde"):
            raise ValueError("original config/local char lacks byte-load CWDE: " + key)
        site_anchors[key]["byte_load_cwde"] = [load_address, load_address + 3]
    # S10's final table site indexes a signed resource byte loaded from AL then widened by CWDE.
    s10_anchor = site_anchors["src/S10/m35F5.c:351"]
    s10_cwde = s10_anchor["nearest_preceding_cwde"]
    if s10_cwde is None or s10_anchor["original_index_instruction"] - s10_cwde > 8:
        raise ValueError("original menu mnemonic byte is not sign-extended before ctype")
    # Both S10 keyboard guards and the S09 guard survive as original test instructions.
    for name in ("o09_35F5_03C6", "o10_35F5_0384"):
        if not by_function[name]["bit_0800_test_addresses"]:
            raise ValueError("original key high-bit guard test missing: " + name)
    for key in ("src/S09/m35F5.c:429", "src/S10/m35F5.c:305", "src/S10/m35F5.c:325"):
        anchor = site_anchors[key]
        guards = by_function[anchor["compiled_function"]]["bit_0800_test_addresses"]
        if not any(g < anchor["original_index_instruction"] for g in guards):
            raise ValueError("original 0x800 test does not precede indexed site: " + key)
    root_choice = by_function["f_1C62_0415"]
    choice_code = machine.read(root_choice["unit"], root_choice["segment"] * 16 + root_choice["offset"], root_choice["size"])
    choice_ins = {i.address: i for i in md.disasm(choice_code, root_choice["offset"])}
    choice_reads = root_choice["table_read_addresses"]
    if not (choice_reads and choice_ins.get(0x5EF) and choice_ins[0x5EF].mnemonic == "jle" and
            choice_ins.get(0x5F1) and "0x7a1f" in choice_ins[0x5F1].op_str.lower()):
        raise ValueError("original root choice positive branch missing before ctype")
    site_anchors["src/root/m1C62.c:306"]["original_positive_guard_branch"] = 0x5EF
    # The common CRT lookup is the implementation reached by S20's non-macro calls.
    common = machine.read("root", 0x29F4 * 16 + 0x2959, 56)
    common_ins = list(md.disasm(common, 0x2959))
    lookup = [i.address for i in common_ins if "0x7a1f" in i.op_str.lower()]
    if not lookup:
        raise ValueError("original MSC runtime common ctype lookup missing")
    return {"oracle_sha256": machine.sha256,
        "BIOS_reader": {"unit": inp["unit"], "segment": inp["seg"], "offset": inp["off"],
            "cbw_addresses": [i.address for i in ins if i.mnemonic == "cwde"],
            "int16_addresses": [i.address for i in ins if i.mnemonic == "int" and i.op_str == "0x16"],
            "pending_path_AH_clear": pending_clear.address,
            "value_range_basis": {"normal_nonzero_AL": [-128, 127], "pending_low_AL_after_AH_clear": [0, 255],
                "combined_return_range": [-128, 255]}},
        "key_wrapper": {"unit": wrapper_info["unit"], "segment": wrapper_info["seg"], "offset": wrapper_info["off"],
            "disassembly_sha256": sha(json.dumps([(i.address, i.mnemonic, i.op_str) for i in wrapper_ins],
                separators=(",", ":")).encode())},
        "source_site_functions": by_function,
        "source_site_anchors": site_anchors,
        "runtime_common": {"unit": "root", "segment": 0x29F4, "offset": 0x2959,
            "table_read_addresses": lookup,
            "disassembly_sha256": sha(json.dumps([(i.address, i.mnemonic, i.op_str) for i in common_ins],
                separators=(",", ":")).encode())}}


_CTYPE_MACROS_CACHE = None
def ctype_macro_facts_cached():
    global _CTYPE_MACROS_CACHE
    if _CTYPE_MACROS_CACHE is None:
        _CTYPE_MACROS_CACHE = ctype_macro_facts()
    return _CTYPE_MACROS_CACHE


def _site_semantics(census, resources):
    semantics = {
        ("src/S09/m35F5.c", 429): ("BIOS INT16 key; guard rejects key&0x800", "UNREACHABLE-IN-SHIPPED-DOMAIN", [], "guard"),
        ("src/S10/m35F5.c", 305): ("BIOS INT16 key; guard rejects key&0x800", "UNREACHABLE-IN-SHIPPED-DOMAIN", [], "guard"),
        ("src/S10/m35F5.c", 325): ("BIOS INT16 key; high-key branch goes to flush", "UNREACHABLE-IN-SHIPPED-DOMAIN", [], "guard"),
        ("src/S10/m35F5.c", 351): ("SHARED kind 6 ID 0 menu mnemonic items[k][1]", "UNREACHABLE-IN-SHIPPED-DOMAIN", [], "resource enumeration"),
        ("src/S20/m39F1.c", 117): ("DOS PSP command tail -> pinned MSC stdargv -> argv[i][2]", "UNREACHABLE-IN-SHIPPED-DOMAIN", [], "supported launch arguments are []"),
        ("src/S20/m39F1.c", 189): ("ReadConfig -> SkipWords -> ReadWord -> SIMANT.CFG stream", "UNREACHABLE-IN-SHIPPED-DOMAIN", [], "configuration byte enumeration"),
        ("src/S20/m39F1.c", 193): ("ReadConfig -> SkipWords -> ReadWord -> SIMANT.CFG stream", "UNREACHABLE-IN-SHIPPED-DOMAIN", [], "configuration byte enumeration"),
        ("src/S20/m39F1.c", 255): ("SIMANT.CFG final language byte", "UNREACHABLE-IN-SHIPPED-DOMAIN", [], "configuration byte enumeration"),
        ("src/S23/m39C7.c", 201): ("DisplayCard SHARED kind17 -> kind10 text + kind21 style", "UNREACHABLE-IN-SHIPPED-DOMAIN", [], "conservative rewind-expanded face-0100 spans contain no high bytes"),
        ("src/root/m1C62.c", 170): ("BIOS INT16 byte -> CBW in f_1F58_005A", "REACHABLE", list(range(0xD1, 0xDF)), "switch outcome unobservable for negative c"),
        ("src/root/m1C62.c", 306): ("BIOS INT16 byte -> f_1F58_0090; c>0 guard", "UNREACHABLE-IN-SHIPPED-DOMAIN", [], "positive guard excludes signed high bytes"),
    }
    out = []
    external_control_bytes = {("src/S20/m39F1.c", 117): list(range(0xD1, 0xDF))}
    for row in census:
        key = (row["source"], row["line"])
        producer, conclusion, actual, basis = semantics[key]
        actual_offsets = [f"{0x791F + b:04X}" for b in actual]
        external_bytes = external_control_bytes.get(key, [])
        any_prefix_bytes = list(range(0x80, 0xFF)) if key == ("src/root/m1C62.c", 170) else []
        out.append({k: row[k] for k in ("source", "line", "function", "kind", "callee", "index_expression")} | {
            "potential_prefix_input_bytes": "0x80..0xFE; 0xFF indexes _ctype[0]",
            "potential_prefix_offsets": "DGROUP:799F..7A1D",
            "supported_domain_bytes_reaching_any_prefix": [f"{b:02X}" for b in any_prefix_bytes],
            "supported_domain_prefix_offsets_read": "DGROUP:799F..7A1D" if any_prefix_bytes else [],
            "dgroup_79f0_input_bytes": "0xD1..0xDE",
            "dgroup_79f0_byte_to_offset": [[f"{b:02X}", f"{0x791F + b:04X}"]
                                             for b in range(0xD1, 0xDF)],
            "dgroup_79f0_offsets_read_in_supported_domain": actual_offsets,
            "dgroup_79f0_bytes_reaching_read_in_supported_domain": [f"{b:02X}" for b in actual],
            "outside_domain_negative_control_bytes": [f"{b:02X}" for b in external_bytes],
            "outside_domain_negative_control_offsets": [f"{0x791F + b:04X}" for b in external_bytes],
            "sign_extension": "signed-byte promotion; original disassembly is hash-pinned",
            "producer_chain": producer,
            "conclusion": conclusion, "basis": basis})
    return out


def source_and_link_audits(texts):
    references = []
    literal_hits = []
    literal_re = re.compile(r"(?<![0-9A-Za-z])(?:0x)?([0-9a-f]{4})h?(?![0-9A-Za-z])", re.I)
    for path, text in sorted(texts.items()):
        if path.endswith(".asm"):
            lines = [(i, line.split(";", 1)[0]) for i, line in enumerate(text.splitlines(), 1)]
            for line_no, code in lines:
                for hit in re.finditer(r"(?i)(?<![A-Za-z0-9_])_{0,2}fheap(?![A-Za-z0-9_])", code):
                    references.append([path, line_no, hit.group(0)])
                for m in literal_re.finditer(code):
                    if 0x799F <= int(m.group(1), 16) <= 0x7A1F:
                        literal_hits.append([path, line_no, m.group(0)])
        elif path.endswith(".c"):
            for tok in csrc.tokenize(text):
                if tok.kind == "id" and tok.text.lower() in {"fheap", "_fheap", "__fheap"}:
                    references.append([path, text.count("\n", 0, tok.s) + 1, tok.text])
                if tok.kind == "pp":
                    for m in re.finditer(r"(?i)(?<![A-Za-z0-9_])_{0,2}fheap(?![A-Za-z0-9_])", tok.text):
                        references.append([path, text.count("\n", 0, tok.s) + 1, m.group(0)])
                    for m in literal_re.finditer(tok.text):
                        if 0x799F <= int(m.group(1), 16) <= 0x7A1F:
                            literal_hits.append([path, text.count("\n", 0, tok.s) + 1, m.group(0)])
                elif tok.kind == "num":
                    literal = re.sub(r"[uUlL]+$", "", tok.text)
                    try:
                        value = int(literal, 0)
                    except ValueError:
                        continue
                    if 0x799F <= value <= 0x7A1F:
                        literal_hits.append([path, text.count("\n", 0, tok.s) + 1, tok.text])
    if references:
        raise ValueError("canonical C/ASM contains _fheap reference")
    manifest_raw = (ROOT / "layout/manifest.json").read_bytes()
    manifest = json.loads(manifest_raw)
    runtime = manifest["runtime"]
    selected = runtime["members"] + runtime.get("data_members", [])
    fdata = [row["member"] for row in selected if Path(row["member"].replace("\\", "/")).name.lower() == "fdata.asm"]
    if fdata:
        raise ValueError("canonical DOS link selects fdata.asm")
    names = [row["member"] for row in selected]
    stdargv = [row for row in selected if Path(row["member"].replace("\\", "/")).name.lower() == "stdargv.asm"]
    if len(stdargv) != 1:
        raise ValueError("canonical DOS runtime selection lacks unique stdargv.asm")
    return {"canonical_fheap_source_references": references,
            "literal_ctype_window_source_references": literal_hits,
            "canonical_dos_link": {"manifest_sha256": sha(manifest_raw),
                "selected_runtime_members": len(runtime["members"]),
                "selected_runtime_data_members": len(runtime.get("data_members", [])),
                "selected_member_name_set_sha256": sha(json.dumps(sorted(names), separators=(",", ":")).encode()),
                "selected_stdargv_member": {k: stdargv[0][k] for k in ("library", "member", "module_index", "member_sha256")},
                "selected_fdata_members": fdata,
                "claim": "canonical DOS link selects no fdata.asm member; no __fheap source reference"},
            "canonical_only_link_map_receipt": {"path": str(CANONICAL_ONLY_MAP).replace("\\", "/"),
                "sha256": CANONICAL_ONLY_MAP_SHA256, "fdata_or_fheap_entries": [],
                "moved_ctype_symbol": "5409:775C __ctype",
                "selection_basis": "independent canonical-only real-link SOURCE.MAP; rechecked by verify_link_maps() when present"}}


LINK_MAPS = (Path("build/current/dos/link/SOURCE.MAP"), CANONICAL_ONLY_MAP)


def verify_link_maps() -> list[str]:
    """Check every available real-link map for fdata/fheap selection.

    Link maps are ignored build products, so the durable facts do not depend
    on them; when present they must agree with the recorded selection.
    """
    checked = []
    for rel in LINK_MAPS:
        path = ROOT / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="latin1")
        if re.search(r"(?i)\bfdata(?:\.asm)?\b|\bfheap\b", text):
            raise ValueError(f"{rel} selects fdata/fheap")
        if not re.search(r"(?im)^\s*[0-9A-F]{4}:[0-9A-F]{4}\s+Res\s+__ctype\b", text):
            raise ValueError(f"{rel} lacks the __ctype runtime table")
        checked.append(str(rel).replace("\\", "/"))
    return checked


def collect(program_override=None, source_overrides=None) -> dict:
    texts, program, source_hashes, canonical_program_raw, observed_program_raw = inventory(
        program_override, source_overrides)
    macro = ctype_macro_facts_cached()
    census, asm_rows = source_census(texts)
    census_keys = {(r["source"], r["line"]): (r["function"], r["callee"]) for r in census}
    if census_keys != SITE_KEYS:
        added = sorted(set(census_keys) - set(SITE_KEYS))
        removed = sorted(set(SITE_KEYS) - set(census_keys))
        raise ValueError(f"complete ctype census changed; added={added}; removed={removed}")
    if asm_rows:
        raise ValueError("canonical .asm ctype site census is no longer empty")
    if len(census) != 11:
        raise ValueError("expected complete 11-site canonical ctype census")

    lock_row, data_row = ctype_ledger_facts(program)
    assumptions = verify_source_assumptions(texts)
    resources = resource_facts()
    if resources["consumer_domains"]["SHARED_kind6_menu"]["text_high_byte_counts"]:
        raise ValueError("SHARED kind-6 decoded menu text contains high bytes")
    if resources["consumer_domains"]["DisplayCard_renderer_coverage"]["face_0100_arguments_with_high_bytes"]:
        raise ValueError("DisplayCard conservative renderer span contains a high byte")
    if resources["SIMANT_CFG"]["high_byte_counts"]:
        raise ValueError("pinned SIMANT.CFG contains high bytes")
    facts_sites = _site_semantics(census, resources)
    asm_path = ROOT / "src/root/m1F58.asm"
    keyboard_asm = asm_path.read_text(encoding="latin1")
    # Check the named assembler procedure and the actual original instructions separately.
    if "_f_1F58_005A\tproc\tfar" not in keyboard_asm or "\tcbw\n\tretf" not in keyboard_asm.lower():
        raise ValueError("canonical BIOS byte reader lacks CBW source")
    orig = original_disassembly(census)
    sign_proofs = {
        ("src/S09/m35F5.c", 429): "yes: signed BIOS byte is returned via f_1F58_005A CBW before integer key use",
        ("src/S10/m35F5.c", 305): "yes: signed BIOS byte is returned via f_1F58_005A CBW before integer key use",
        ("src/S10/m35F5.c", 325): "yes: signed BIOS byte is returned via f_1F58_005A CBW before integer key use",
        ("src/S10/m35F5.c", 351): "yes: signed menu char is loaded from AL and CWDE-promoted before table read",
        ("src/S20/m39F1.c", 117): "yes: argv byte is CWDE/CDQ-extended into long v before _isdigit",
        ("src/S20/m39F1.c", 189): "yes: signed local char is loaded into AL then CWDE before _isspace",
        ("src/S20/m39F1.c", 193): "yes: signed local char is loaded into AL then CWDE before _isspace",
        ("src/S20/m39F1.c", 255): "yes: signed local char is loaded into AL then CWDE before _isdigit",
        ("src/S23/m39C7.c", 201): "yes: signed text char is loaded into AL then CWDE before the direct lookup",
        ("src/root/m1C62.c", 170): "yes: keyboard byte is CBW-extended by f_1F58_005A into int c",
        ("src/root/m1C62.c", 306): "yes: keyboard byte is CBW-extended by f_1F58_005A via f_1F58_0090",
    }
    for row in facts_sites:
        key = f"{row['source']}:{row['line']}"
        row["sign_extension_happens"] = True
        row["sign_extension"] = sign_proofs[(row["source"], row["line"])]
        if key not in orig["source_site_anchors"]:
            raise ValueError("site has no original disassembly anchor: " + key)
        row["original_disassembly_anchor"] = orig["source_site_anchors"][key]
    source_audit = source_and_link_audits(texts)
    supported_hits = [f"{row['source']}:{row['line']}" for row in facts_sites
                      if row["dgroup_79f0_bytes_reaching_read_in_supported_domain"]]
    external_hits = [f"{row['source']}:{row['line']}" for row in facts_sites
                     if row["outside_domain_negative_control_bytes"]]
    if supported_hits != ["src/root/m1C62.c:170"] or external_hits != ["src/S20/m39F1.c:117"]:
        raise ValueError("dgroup_79f0 source read inventory changed")
    source_audit["dgroup_79f0_source_observations"] = {
        "supported_domain_source_site": supported_hits,
        "outside_domain_negative_control_site": external_hits,
        "description": "79F0..79FD is observed through signed _ctype prefix reads; m1C62:170 is the only supported-domain read and its switch effect is unobservable."}
    program_sha = _ctype_program_projection(program)
    canonical_program_sha = _ctype_program_projection(json.loads(canonical_program_raw))
    all_source_sha = sha(json.dumps(source_hashes, sort_keys=True, separators=(",", ":")).encode())
    stdargv_path = Path("C:/tools/msc-6.00/STARTUP/dos/stdargv.asm")
    stdargv_raw = stdargv_path.read_bytes()
    stdargv = stdargv_raw.decode("latin1").lower()
    delim = re.search(r"(?ms)^delim\s+macro\s+target\s*\r?\n(.*?)^\s*endm\b", stdargv)
    argcopy = re.search(r"(?ms)^arg610:\s*\r?\n(.*?)(?=^[a-z_][a-z_0-9]*:)", stdargv)
    normalize_asm = lambda s: " ".join(re.sub(r"\s+", " ", line.split(";", 1)[0].strip())
                                        for line in s.splitlines())
    normalized_stdargv = normalize_asm(stdargv)
    if (not all(x in normalized_stdargv for x in ("mov si,81h", "arg610:", "lodsb", "stosb", "delim arg800")) or
            not delim or not all(x in normalize_asm(delim.group(1)) for x in ("cmp al,c_cr", "or al,al")) or
            not argcopy or not all(x in normalize_asm(argcopy.group(1)) for x in
                ("lodsb", "cmp al,c_blank", "cmp al,c_tab", "delim arg800", "stosb"))):
        raise ValueError("pinned MSC stdargv command-tail copy path changed")
    if source_audit["canonical_dos_link"]["selected_stdargv_member"]["member"] != "dos\\stdargv.asm":
        raise ValueError("pinned DOS stdargv source is not the selected runtime member")
    return {"schema": "simant-ctype-domain-v1",
        "scope": "Canonical inventory and pinned shipped resources; game-domain reads, excluding user-replaced assets and external launch arguments.",
        "inventory": {"program_projection_sha256": program_sha,
            "canonical_program_projection_sha256": canonical_program_sha,
            "source_count": len(source_hashes), "source_hashes_sha256": all_source_sha,
            "source_hashes": source_hashes},
        "inventory_override_used": program_override is not None or bool(source_overrides),
        "gate": lock_row, "data_debt": data_row,
        "ctype_header": macro,
        "site_census": {"count": len(census), "asm_sites": asm_rows,
            "rows": facts_sites,
            "prefix_address_model": {"index_base": "DGROUP:7A1F (_ctype+1)",
                "signed_byte_formula": "offset=0x7A1F+(b-256), for b>=0x80",
                "prefix_byte_range": "0x80..0xFE -> DGROUP:799F..7A1D",
                "0xFF": "DGROUP:7A1E (_ctype[0], not prefix)",
                "dgroup_79f0_mapping": [[f"{b:02X}", f"{0x791F + b:04X}"]
                                         for b in range(0xD1, 0xDF)]},
            "census_sha256": sha(json.dumps(census, sort_keys=True, separators=(",", ":")).encode())},
        "original": orig,
        "resources": resources,
        "input_domains": {
            "supported_launch_arguments": [],
            "startup_slash_s": {"site": "src/S20/m39F1.c:117", "outside_supported_domain": True,
                "negative_control": "At a DOS prompt launch `SIMANT /s` followed immediately by Alt+209. MSC stdargv reads PSP:81h, skips only CR/NUL, blanks and tabs as delimiters, and copies D1 with LODSB/STOSB into argv[1][2]; _isdigit receives -47 and would read 79F0. This is not in launch arguments [].",
                "stdargv_source": str(stdargv_path).replace("\\", "/"),
                "stdargv_sha256": sha(stdargv_raw),
                "selected_runtime_member": source_audit["canonical_dos_link"]["selected_stdargv_member"]},
            "bios_keyboard": {"path": "INT16 AH=00 -> f_1F58_005A -> CBW; f_1F58_0090 preserves signed high bytes",
                "alt_decimal_witness": "During the successful-save timed alert, Alt+209 returns D1 and reads 79F0; Alt+210..222 map D2..DE to 79F1..79FD.",
                "nonzero_signed_range": [-128, 127], "pending_extended_key_range": [0, 255],
                "combined_c_range_at_m1C62_170": [-128, 255]},
            "filename_and_save_inputs": "DOS DTA filenames and save-file bytes do not feed a ctype argument: S09 line 429 classifies the separate BIOS key; S20 ctype inputs are argv/config bytes; other sites consume menu/card text or keyboard bytes."},
        "source_assumptions": assumptions,
        "source_link_audits": source_audit}


def check() -> dict:
    actual = collect()
    expected = json.loads((Path(__file__).parent / "facts.json").read_text())
    if actual != expected:
        raise ValueError("ctype-domain replay differs from reviewed facts.json")
    verify_link_maps()
    return actual


if __name__ == "__main__":
    if "--write-facts" in sys.argv[1:]:
        result = collect()
        (Path(__file__).parent / "facts.json").write_text(json.dumps(result, indent=2) + "\n")
        print(f"wrote {Path(__file__).parent / 'facts.json'}")
    else:
        result = check()
        print("PASS: 11-site ctype census; shipped high-byte domains; m1C62:170 no-effect lemma")
