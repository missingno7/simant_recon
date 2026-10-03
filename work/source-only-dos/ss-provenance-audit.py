#!/usr/bin/env python3
"""Regenerate the bounded display-driver SS/frame audit from pinned sources.

No generated build report, prior OBJ, listing, or original executable is an input.
Fresh MASM objects/listings are made from canonical modules after source-bindings-v1.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import compiler  # noqa: E402
import dos_source_bindings as bindings  # noqa: E402
import source_only_dos as dos  # noqa: E402
from omf import OmfReader  # noqa: E402

OUT = ROOT / "build/workers/dos_assembly_frame_inventory"
AUDIT_JSON = OUT / "driver-ss-provenance-audit-v1.json"
SOURCE_BINDINGS = ROOT / "work/source-only-dos/source-bindings-v1.json"
QUEUE_CONTRACT = ROOT / "work/source-only-dos/queue-lifetime-contract-v1.json"
STATIC_INDEX = ROOT / "work/source-only-dos/static-completeness/index-v1.json"
DRAWBALLOONS_CORRECTED = ROOT / "work/source-only-dos/corrections/DrawBalloons/module.c"
MODULES = [
    {"module": "S00:31AD", "source": "src/S00/m31AD.asm", "expected": 64},
    {"module": "S01:3126", "source": "src/S01/m3126.asm", "expected": 36},
    {"module": "S02:3126", "source": "src/S02/m3126.asm", "expected": 2},
    {"module": "S03:3126", "source": "src/S03/m3126.asm", "expected": 26},
]
PROC_BEGIN = re.compile(r"^\s*([\w.$?@]+)\s+proc\s+(far|near)\b", re.I)
PROC_END = re.compile(r"^\s*([\w.$?@]+)\s+endp\b", re.I)
SS_GLOBAL = re.compile(r"\bss\s*:\s*(_g_[a-z0-9_]+)\b", re.I)
SS_WRITE = re.compile(r"\b(?:(?P<mov>mov)\s+ss\s*,|(?P<pop>pop)\s+ss\b|(?P<lss>lss)\s+)", re.I)
ASM_MARK = re.compile(r"\b(?:__asm|_asm|asm)\b", re.I)
LISTING_ADDRESS = re.compile(r"^\s*([0-9a-f]{4,8})\b", re.I)
FRAME_FIELDS = {"frame_method", "frame_kind", "frame"}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise SystemExit("SS provenance audit failed closed: " + message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pin(path: Path, expected: str | None = None) -> dict:
    return dos.pin(path, expected)[1]


def norm(text: str) -> str:
    return " ".join(text.strip().lower().split())


def line_text(path: Path) -> str:
    return path.read_text(encoding="latin1").replace("\r\n", "\n")


def source_ss_rows(text: str, source: str) -> list[dict]:
    rows = []
    procedure = None
    distance = None
    for number, raw in enumerate(text.splitlines(), 1):
        code = raw.split(";", 1)[0]
        begin = PROC_BEGIN.match(code)
        if begin:
            procedure, distance = begin.group(1), begin.group(2).upper()
        match = SS_GLOBAL.search(code)
        if match:
            rows.append({"source": source, "source_line": number,
                         "instruction": raw.strip(), "target": match.group(1),
                         "procedure": procedure, "distance": distance})
        if PROC_END.match(code):
            procedure = distance = None
    return rows


def module_code_segments(text: str) -> list[str]:
    return re.findall(r"(?im)^\s*([\w.$?@]+)\s+segment\b[^\n]*'CODE'", text)


def listing_ss_rows(listing: str) -> tuple[list[dict], list[int]]:
    rows = []
    addresses = []
    for raw in listing.splitlines():
        address = LISTING_ADDRESS.match(raw)
        if address:
            addresses.append(int(address.group(1), 16))
        code = raw.split(";", 1)[0]
        target = SS_GLOBAL.search(code)
        if target:
            require(address is not None,
                    "MASM listing SS operand has no instruction address: " + raw)
            rows.append({"listing_line": raw.rstrip(),
                         "offset": int(address.group(1), 16),
                         "target": target.group(1)})
    return rows, sorted(set(addresses))


def find_instruction_fixup(row: dict, next_offset: int, obj, code_segment: str) -> list[dict]:
    return [dict(fixup) for fixup in obj.linker_fixups
            if fixup["segment"] == code_segment
            and fixup["offset"] >= row["offset"]
            and fixup["offset"] < next_offset
            and fixup["target"] == row["target"]
            and fixup["target_kind"] == "external"]


def body(text: str, procedure: str) -> str:
    pattern = re.compile(rf"(?ims)^\s*{re.escape(procedure)}\s+proc\b(.*?)"
                         rf"^\s*{re.escape(procedure)}\s+endp\b")
    found = pattern.search(text)
    require(found is not None, "missing procedure " + procedure)
    return found.group(1)


def ordered(text: str, snippets: list[str], label: str) -> None:
    current = 0
    for snippet in snippets:
        pos = text.lower().find(snippet.lower(), current)
        require(pos >= 0, f"{label}: missing/out-of-order {snippet!r}")
        current = pos + len(snippet)


def source_line(text: str, fragment: str, occurrence: int = 0) -> int:
    hits = [i for i, line in enumerate(text.splitlines(), 1)
            if fragment.lower() in line.lower()]
    require(0 <= occurrence < len(hits), f"missing source anchor {fragment!r}")
    return hits[occurrence]


def source_line_in_proc(text: str, procedure: str, fragment: str) -> int:
    lines = text.splitlines()
    begin = next((i for i, line in enumerate(lines)
                  if re.match(rf"^\s*{re.escape(procedure)}\s+proc\b", line, re.I)), None)
    require(begin is not None, "missing source procedure " + procedure)
    end = next((i for i in range(begin + 1, len(lines))
                if re.match(rf"^\s*{re.escape(procedure)}\s+endp\b", lines[i], re.I)), None)
    require(end is not None, "missing source endp " + procedure)
    matches = [i + 1 for i in range(begin + 1, end)
               if fragment.lower() in lines[i].lower()]
    require(len(matches) == 1, f"{procedure}: expected one {fragment!r}, got {matches}")
    return matches[0]


def static_behavior_sources() -> tuple[list[dict], list[dict]]:
    """Resolve the reviewed whole-module registrations from the pinned index.

    The DrawBalloons registration source is included as registered, then the
    corrected whole module is added as a separate input. No build receipt or
    ignored worker report participates in this source inventory.
    """
    index_raw = STATIC_INDEX.read_bytes()
    index = json.loads(index_raw.decode("utf-8"))
    require(index.get("schema") == "simant-dos-strict-static-index-v1"
            and len(index.get("entries", {})) == 29,
            "static-completeness index no longer has the reviewed 29 entries")
    inputs = [{"path": "work/source-only-dos/static-completeness/index-v1.json",
               "sha256": sha(index_raw), "size": len(index_raw), "role": "registration index"}]
    sources = []
    for function, reference in index["entries"].items():
        receipt_path = ROOT / reference["path"]
        receipt_raw = receipt_path.read_bytes()
        require(sha(receipt_raw) == reference["sha256"],
                f"static-completeness receipt pin changed for {function}")
        receipt = json.loads(receipt_raw.decode("utf-8"))
        registered = receipt["registered_source"]
        require(registered.get("whole_module") is True,
                f"registered behavior source is not a whole module: {function}")
        source_path = ROOT / registered["path"]
        raw = source_path.read_bytes()
        require(sha(raw) == registered["sha256"],
                f"registered behavior source pin changed for {function}")
        sources.append({"function": function, "module": registered["module"],
                        "path": registered["path"], "sha256": sha(raw),
                        "size": len(raw), "role": "registered whole-module source"})
        inputs.append({"path": reference["path"], "sha256": sha(receipt_raw),
                       "size": len(receipt_raw), "role": "static-completeness receipt"})

    draw = json.loads((ROOT / index["entries"]["DrawBalloons"]["path"])
                      .read_text(encoding="utf-8"))
    corrected = draw["audit"]["source"]
    require(corrected.get("path") == DRAWBALLOONS_CORRECTED.relative_to(ROOT).as_posix()
            and corrected.get("whole_module") is True
            and corrected.get("module") == "root:0250",
            "DrawBalloons correction receipt no longer identifies the reviewed whole module")
    raw = DRAWBALLOONS_CORRECTED.read_bytes()
    require(sha(raw) == corrected["sha256"], "corrected DrawBalloons source pin changed")
    sources.append({"function": "DrawBalloons", "module": corrected["module"],
                    "path": corrected["path"], "sha256": sha(raw), "size": len(raw),
                    "role": "corrected whole-module source"})
    inputs.extend([pin(DRAWBALLOONS_CORRECTED, corrected["sha256"])])
    return sources, inputs


def c_code_without_comments_or_literals(text: str) -> str:
    """Blank comments and literals while preserving lines and inline-asm code."""
    text = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"),
                  text, flags=re.S)
    text = re.sub(r"//[^\n]*", "", text)
    return re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
                  lambda m: "\n" * m.group(0).count("\n"), text)


def inline_asm_inventory(path: Path, text: str, rel: str) -> tuple[list[dict], list[dict]]:
    """Inventory C inline-ASM markers and SS setters in their code blocks."""
    code = c_code_without_comments_or_literals(text)
    markers = []
    setters = []
    for match in ASM_MARK.finditer(code):
        line = code.count("\n", 0, match.start()) + 1
        tail = code[match.end():]
        start = len(tail) - len(tail.lstrip())
        tail = tail[start:]
        block = ""
        if tail.startswith("{"):
            depth = 0
            for pos, char in enumerate(tail):
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        block = tail[:pos + 1]
                        break
        elif tail.startswith("("):
            # C's asm("...") spelling is uncommon here; retain the literal
            # argument separately below, while balancing its parentheses.
            depth = 0
            end = 0
            for end, char in enumerate(tail):
                if char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                    if depth == 0:
                        block = tail[:end + 1]
                        break
        else:
            block = tail.split("\n", 1)[0].split(";", 1)[0]
        markers.append({"path": rel, "line": line, "marker": match.group(0),
                        "block_excerpt": " ".join(block.strip().split())[:240]})
        for offset, body_line in enumerate(block.splitlines() or [block]):
            hit = SS_WRITE.search(body_line)
            if hit:
                setters.append({"path": rel, "line": line + offset,
                                "instruction": body_line.strip(),
                                "kind": "MOV SS" if hit.group("mov") else
                                ("POP SS" if hit.group("pop") else "LSS"),
                                "inside_inline_asm": True})
    return markers, setters


def procedure_cfg(text: str, procedure: str) -> tuple[list[dict], dict[str, int]]:
    """Build a bounded instruction CFG for one MASM procedure's local branches."""
    lines = text.splitlines()
    begin = next((i for i, line in enumerate(lines)
                  if re.match(rf"^\s*{re.escape(procedure)}\s+proc\b", line, re.I)), None)
    require(begin is not None, "missing CFG procedure " + procedure)
    end = next((i for i in range(begin + 1, len(lines))
                if re.match(rf"^\s*{re.escape(procedure)}\s+endp\b", lines[i], re.I)), None)
    require(end is not None, "missing CFG endp " + procedure)
    nodes: list[dict] = []
    labels: dict[str, int] = {}
    for source_line_num in range(begin + 1, end):
        code = lines[source_line_num].split(";", 1)[0].strip()
        if not code:
            continue
        label = re.match(r"^([\w.$?@]+):?$", code)
        if label:
            labels[label.group(1).lower()] = len(nodes)
            continue
        nodes.append({"line": source_line_num + 1, "text": code, "successors": []})
    require(bool(nodes), "empty CFG procedure " + procedure)
    conditional = re.compile(r"^(?:j(?!mp)[a-z]{1,3}|loop\w*)\s+(?:(?:short|near|far)\s+(?:ptr\s+)?)?([\w.$?@]+)", re.I)
    unconditional = re.compile(r"^(?:jmp|ljmp)\s+(?:(?:short|near|far)\s+(?:ptr\s+)?)?([\w.$?@]+)", re.I)
    terminal = re.compile(r"^(?:retf?|iret|iretw)\b", re.I)
    for index, node in enumerate(nodes):
        code = node["text"]
        if terminal.match(code):
            continue
        jump = unconditional.match(code)
        if jump:
            target = labels.get(jump.group(1).lower())
            if target is not None:
                node["successors"].append(target)
            continue
        branch = conditional.match(code)
        if branch:
            target = labels.get(branch.group(1).lower())
            if target is not None:
                node["successors"].append(target)
            if index + 1 < len(nodes):
                node["successors"].append(index + 1)
            continue
        if index + 1 < len(nodes):
            node["successors"].append(index + 1)
    return nodes, labels


def ss_group_dataflow(nodes: list[dict]) -> list[set[tuple[bool, bool, bool]]]:
    """Propagate (SS-is-DGROUP, BX-is-DGROUP, DX-is-DGROUP) to each node."""
    incoming: list[set[tuple[bool, bool, bool]]] = [set() for _ in nodes]
    incoming[0].add((False, False, False))
    queue = [0]
    nonwrites = {"cmp", "test", "push", "call", "jmp", "je", "jne", "jz", "jnz",
                 "ja", "jae", "jb", "jbe", "jg", "jge", "jl", "jle", "js", "jns",
                 "jo", "jno", "jp", "jnp", "loop", "loope", "loopne", "cld", "std",
                 "cli", "sti", "clc", "stc", "cmc", "nop", "int", "iret", "ret", "retf"}
    while queue:
        index = queue.pop(0)
        node = nodes[index]
        code = node["text"]
        op = code.split(None, 1)[0].lower()
        operands = code[len(op):].strip()
        for state in tuple(incoming[index]):
            ss_group, bx_group, dx_group = state
            new_state = (ss_group, bx_group, dx_group)
            if re.match(r"^mov\s+ss\s*,", code, re.I):
                source = operands.split(",", 1)[1].strip().lower()
                value = bx_group if source == "bx" else dx_group if source == "dx" else False
                new_state = (value, bx_group, dx_group)
            else:
                parts = operands.split(",", 1)
                destination = re.sub(r"\b(?:byte|word|dword)\s+ptr\s+", "", parts[0].lower()).strip() if parts else ""
                # Any unrecognized write to BX/DX destroys the DGROUP value.
                if op not in nonwrites and destination in {"bx", "bl", "bh"}:
                    bx_group = False
                elif op not in nonwrites and destination in {"dx", "dl", "dh"}:
                    dx_group = False
                if op == "mov" and len(parts) == 2:
                    source = parts[1].strip().lower()
                    if destination in {"bx", "bl", "bh"}:
                        bx_group = source == "dgroup" or (source == "dx" and dx_group)
                    elif destination in {"dx", "dl", "dh"}:
                        dx_group = source == "dgroup" or (source == "bx" and bx_group)
                new_state = (ss_group, bx_group, dx_group)
            for successor in node["successors"]:
                if new_state not in incoming[successor]:
                    incoming[successor].add(new_state)
                    queue.append(successor)
    return incoming


def prove_ss_dominance(text: str, procedure: str, switch_line: int,
                       dispatch_fragments: list[str]) -> dict:
    nodes, labels = procedure_cfg(text, procedure)
    incoming = ss_group_dataflow(nodes)
    switch_nodes = [i for i, node in enumerate(nodes)
                    if node["line"] == switch_line and re.match(r"mov\s+ss\s*,", node["text"], re.I)]
    require(len(switch_nodes) == 1, f"{procedure}: expected exactly one SS=DGROUP switch at line {switch_line}")
    results = []
    for fragment in dispatch_fragments:
        selected = [(i, node) for i, node in enumerate(nodes)
                    if fragment.lower() in node["text"].lower()]
        require(selected, f"{procedure}: dispatch instruction missing from CFG: {fragment}")
        for index, node in selected:
            states = sorted(incoming[index])
            require(states and all(state[0] for state in states),
                    f"{procedure}:{node['line']} dispatch is reachable without SS=DGROUP: {states}")
            results.append({"line": node["line"], "instruction": node["text"],
                            "incoming_ss_states": ["DGROUP" if state[0] else "not-proven-DGROUP"
                                                   for state in states],
                            "cfg_reachable": True, "all_reaching_paths_after_switch": True})
    return {"procedure": procedure, "switch_line": switch_line,
            "switch_instruction": nodes[switch_nodes[0]]["text"],
            "dispatches": results,
            "cfg_instruction_nodes": len(nodes), "local_labels": len(labels),
            "method": "instruction-level local-branch CFG with forward may-state propagation; entry SS unknown, SS becomes DGROUP only on mov ss from a BX/DX register whose value is DGROUP; arbitrary saved-SS restores are not credited."}


def startup_evidence() -> tuple[dict, dict]:
    packet = json.loads(QUEUE_CONTRACT.read_text(encoding="utf-8"))
    startup = packet["startup_clear"]
    pins = packet["pins"]
    crt = pins["crt0_member"]
    instructions = startup["symbolic_instructions"]
    texts = [row["text"] for row in instructions]
    require(crt["accepted_manifest_match"] and crt["exact_runtime_verifier_result"]
            and crt["member"] == "dos\\crt0.asm"
            and crt["sha256"] == "2e9a254b9bd00ea59884089e78e951f0e40343e11d24976f32d9582f4ded259d",
            "queue contract no longer pins accepted CRT startup")
    require(texts.index("mov di, 0x55b3") < texts.index("mov ss, di"),
            "CRT does not load the registered DGROUP selector before SS")
    main_call = startup["main_call"]
    require(main_call["occurs_after_clear"] and main_call["canonical_symbol"] == "main"
            and int(main_call["instruction_linear"], 16) >
            int(instructions[texts.index("mov ss, di")]["linear"], 16),
            "accepted far call to main does not follow the startup SS setup")
    require(not any(SS_WRITE.search(item)
                    for item in startup["main_path_symbolic_instructions"]),
            "accepted CRT main path contains an SS setter after startup")
    return ({"contract": "work/source-only-dos/queue-lifetime-contract-v1.json",
             "crt_member": crt, "dg_group_selector": "0x55b3",
             "instruction_order": ["mov di, 0x55b3", "mov ss, di"],
             "ds_at_main": ["push ss", "pop ds"],
             "main_call": main_call,
             "conclusion": "SS=DGROUP before the accepted far call to main; the main path preserves that SS."},
            pin(QUEUE_CONTRACT))


def interrupt_evidence() -> tuple[list[dict], dict[str, list[dict]]]:
    mouse_path = ROOT / "src/root/m1B73.asm"
    mouse_text = line_text(mouse_path)
    cases = [
        {"procedure": "_f_1B73_0445", "route": "INT 33h callback, active path",
         "setup": ["mov bx, DGROUP", "mov ds, bx", "mov word ptr _g_53B4, ss",
                   "mov word ptr _g_53B6, sp", "mov ss, bx",
                   "mov sp, offset DGROUP:_g_4FAA"],
         "dispatch": ["call far ptr _f_1B73_04BB", "call word ptr _g_5FFA"],
         "restore": ["mov ss, word ptr _g_53B4", "mov sp, word ptr _g_53B6"]},
        {"procedure": "_f_1B73_051F", "route": "INT 08h timer display path",
         "setup": ["mov bx, DGROUP", "mov ds, bx", "mov word ptr _g_53B8, ss",
                   "mov word ptr _g_53BA, sp", "mov ss, bx",
                   "mov sp, offset DGROUP:_g_51AC"],
         "dispatch": ["call far ptr _f_1B73_04BB", "call far ptr _f_1B73_00D9",
                      "call near ptr _f_1B73_09F7"],
         "restore": ["mov ss, word ptr _g_53B8", "mov sp, word ptr _g_53BA"]},
        {"procedure": "_f_1B73_065A", "route": "INT 15h keyboard intercept",
         "setup": ["mov dx, DGROUP", "mov ds, dx", "mov word ptr _g_53B2, ss",
                   "mov word ptr _g_53B0, sp", "mov ss, dx",
                   "mov sp, offset DGROUP:_g_53AE"],
         "dispatch": ["call near ptr _f_1B73_0747"],
         "restore": ["mov ss, word ptr _g_53B2", "mov sp, word ptr _g_53B0"]},
        {"procedure": "_f_1B73_06E3", "route": "INT 09h keyboard handler",
         "setup": ["mov dx, DGROUP", "mov ds, dx", "mov word ptr _g_53B2, ss",
                   "mov word ptr _g_53B0, sp", "mov ss, dx",
                   "mov sp, offset DGROUP:_g_53AE"],
         "dispatch": ["call near ptr _f_1B73_0747"],
         "restore": ["mov ss, word ptr _g_53B2", "mov sp, word ptr _g_53B0"]},
    ]
    for case in cases:
        proc_text = body(mouse_text, case["procedure"])
        ordered(proc_text, case["setup"] + case["dispatch"] + case["restore"],
                case["route"])
        case["source"] = "src/root/m1B73.asm"
        case["procedure_line"] = source_line(mouse_text,
                                              case["procedure"] + "\tproc\tfar")
        switch_line = source_line_in_proc(mouse_text, case["procedure"],
                                          next(row for row in case["setup"]
                                               if re.match(r"mov ss,", row, re.I)))
        case["ss_switch_lines"] = [switch_line]
        case["stack_pointer_lines"] = [source_line(mouse_text, row)
                                       for row in case["setup"] if row.startswith("mov sp,")]
        case["result"] = "All listed display calls are dominated by SS=DGROUP and return through restoration of the interrupted SS:SP; source's nested/inactive branches chain without dispatch."
        case["cfg_ss_dominance"] = prove_ss_dominance(
            mouse_text, case["procedure"], switch_line, case["dispatch"])
    callback = body(mouse_text, "_f_1B73_03EE")
    require("je _f_1B73_0445" in callback and "call " not in callback.lower(),
            "INT 33h entry no longer reaches active handler without a pre-switch call")
    cases[0]["callback_entry_line"] = source_line(mouse_text,
                                                   "_f_1B73_03EE\tproc\tfar")

    sound_text = line_text(ROOT / "src/root/m28BC.asm")
    require(re.search(r"(?im)^\s*isr_ss\s+dw\s+DGROUP\b", sound_text)
            and re.search(r"(?im)^\s*isr_sp\s+dw\s+offset\s+DGROUP:isr_stack_top\b", sound_text)
            and re.search(r"(?im)^\s*isr_stack\s+db\s+200h\s+dup", sound_text),
            "timer private stack is no longer explicitly DGROUP-owned")
    require(not any(name in sound_text for name in
                    ("_g_9128", "_g_9148", "_g_9160", "_g_9164", "_g_9168", "_g_9184")),
            "sound ISR unexpectedly references display dispatch slots")
    sound_case = {"source": "src/root/m28BC.asm", "route": "INT 08h sound/MIDI timer",
                  "stack_segment_owner": "isr_ss dw DGROUP in TIMER_TEXT",
                  "stack_pointer_owner": "isr_sp dw offset DGROUP:isr_stack_top",
                  "stack_storage": "isr_stack db 200h dup (0) inside _DATA grouped into DGROUP",
                  "lines": {"isr_ss": source_line(sound_text, "isr_ss"),
                            "isr_sp": source_line(sound_text, "isr_sp"),
                            "isr_stack": source_line(sound_text, "isr_stack")},
                  "display_dispatch": "none; sound ISR dispatches MIDI and restores interrupted SS:SP."}
    cases.append(sound_case)
    return cases, {"src/root/m1B73.asm": [pin(mouse_path)],
                   "src/root/m28BC.asm": [pin(ROOT / "src/root/m28BC.asm")]}


def run_audit() -> tuple[dict, dict[str, dict]]:
    """Return audit data and fresh bound module source/object controls in memory."""
    denied = dos.install_input_guard()
    packet_raw = SOURCE_BINDINGS.read_bytes()
    packet = json.loads(packet_raw.decode("utf-8"))
    binding_by_module = {row["module"]: row for row in packet["bindings"]}
    require(all(module["module"] in binding_by_module for module in MODULES),
            "source-bindings-v1 is missing one of the four driver modules")
    tc = compiler.toolchain()
    builds = {}
    driver_rows = []
    unresolved_rows = []
    counts = {}

    for item in MODULES:
        path = ROOT / item["source"]
        raw_source = path.read_bytes()
        binding = binding_by_module[item["module"]]
        require(binding["source"].replace("\\", "/") == item["source"]
                and sha(raw_source) == binding["source_sha256"],
                f"{item['module']} canonical source no longer matches its pinned source binding")
        canonical = raw_source.decode("latin1").replace("\r\n", "\n")
        bound = bindings.apply_binding(canonical, binding)
        canonical_rows = source_ss_rows(canonical, item["source"])
        bound_rows = source_ss_rows(bound, item["source"])
        require(len(canonical_rows) == len(bound_rows)
                and [norm(r["instruction"]) for r in canonical_rows] ==
                [norm(r["instruction"]) for r in bound_rows],
                f"{item['module']} source binding altered SS operand instructions")
        code_segments = module_code_segments(bound)
        require(len(code_segments) == 1,
                f"{item['module']} expected one code segment, found {code_segments}")

        result = compiler.assemble(bound, "masm510", ["/Mx", "/L"],
                                   basename=item["module"].replace(":", "_"), keep=True)
        require(result.ok, f"MASM 5.10 failed for {item['module']}: {result.log}")
        listing_path = result.workdir / (item["module"].replace(":", "_") + ".LST")
        require(listing_path.is_file(), f"MASM /L did not produce listing for {item['module']}")
        listing = listing_path.read_text(encoding="latin1", errors="replace")
        listed_rows, all_addresses = listing_ss_rows(listing)
        require(len(listed_rows) == len(bound_rows)
                and [r["target"].lower() for r in listed_rows] ==
                [r["target"].lower() for r in bound_rows],
                f"{item['module']} MASM listing does not preserve source SS operand sequence")
        obj = OmfReader().read(result.obj, item["module"] + "-bound-control")
        code_segment = code_segments[0]
        fixups = []
        associated_rows = []
        for index, listed in enumerate(listed_rows):
            higher = [address for address in all_addresses if address > listed["offset"]]
            stop = min(higher) if higher else obj.segment_lengths[code_segment]
            site_fixups = find_instruction_fixup(listed, stop, obj, code_segment)
            require(len(site_fixups) <= 1,
                    f"{item['module']}:{bound_rows[index]['source_line']} has multiple external fixups in one instruction")
            if not site_fixups:
                unresolved_rows.append({**bound_rows[index], "status": "no matching external fixup"})
                continue
            fixup = site_fixups[0]
            fixups.append(fixup)
            signature = {
                "module": item["module"], "source": item["source"],
                "source_line": canonical_rows[index]["source_line"],
                "bound_source_line": bound_rows[index]["source_line"],
                "instruction": canonical_rows[index]["instruction"],
                "target": bound_rows[index]["target"],
                "procedure": bound_rows[index]["procedure"],
                "distance": bound_rows[index]["distance"],
                "listing_offset": f"0x{listed['offset']:04x}",
                "fixup_site": f"{fixup['segment']}:{fixup['offset']:04X}",
                "fixup": {key: fixup.get(key) for key in
                          ("segment", "offset", "width", "loc", "target_kind", "target",
                           "frame_method", "frame_kind", "frame", "displacement", "encoded_addend")},
            }
            if (fixup["target_kind"] == "external" and fixup["loc"] == "offset16"
                    and fixup["frame_kind"] == "segment" and fixup["frame"] == "_DATA"):
                require(signature["distance"] == "FAR",
                        f"{item['module']} candidate operand is not in a FAR procedure")
                driver_rows.append(signature)
            else:
                unresolved_rows.append({**signature, "status": "SS symbol fixup outside selected 128-site family"})

        counts[item["module"]] = sum(1 for row in driver_rows if row["module"] == item["module"])
        builds[item["module"]] = {"source": item["source"], "binding": binding,
                                  "canonical_text": canonical, "bound_text": bound,
                                  "canonical_rows": canonical_rows, "bound_rows": bound_rows,
                                  "object": result.obj, "object_hash": sha(result.obj),
                                  "listing_hash": sha(listing_path.read_bytes()),
                                  "listing_path": str(listing_path), "code_segment": code_segment,
                                  "object_model": obj}

    expected_counts = {row["module"]: row["expected"] for row in MODULES}
    require(counts == expected_counts and len(driver_rows) == 128,
            f"generated candidate family changed: counts={counts}")
    require(len(unresolved_rows) == 10,
            f"expected 10 separate driver SS symbol operands, found {len(unresolved_rows)}")
    require(all(row["fixup"]["target_kind"] == "external"
                and row["fixup"]["loc"] == "offset16"
                and row["fixup"]["frame_kind"] == "segment"
                and row["fixup"]["frame"] == "_DATA" for row in driver_rows),
            "selected source/fixup site signature contains a noncandidate frame")

    registered_sources, registered_input_pins = static_behavior_sources()
    canonical_paths = [path for path in sorted((ROOT / "src").rglob("*"))
                       if path.is_file() and path.suffix.lower() in {".asm", ".inc", ".c", ".h"}]
    scan_paths: dict[str, Path] = {path.relative_to(ROOT).as_posix(): path
                                   for path in canonical_paths}
    for source in registered_sources:
        scan_paths[source["path"]] = ROOT / source["path"]
    all_files = []
    all_writes = []
    asm_markers = []
    inline_asm_setters = []
    for rel, path in sorted(scan_paths.items()):
        raw = path.read_bytes()
        all_files.append({"path": rel, "sha256": sha(raw), "size": len(raw),
                          "roles": (["canonical source"] if rel.startswith("src/") else []) +
                                   ([row["role"] for row in registered_sources
                                     if row["path"] == rel])})
        text = raw.decode("latin1", errors="replace")
        if path.suffix.lower() in {".asm", ".inc"}:
            cleaned = [line.split(";", 1)[0] for line in text.splitlines()]
        else:
            cleaned = c_code_without_comments_or_literals(text).splitlines()
            markers, setters = inline_asm_inventory(path, text, rel)
            asm_markers.extend(markers)
            inline_asm_setters.extend(setters)
        for number, line in enumerate(cleaned, 1):
            hit = SS_WRITE.search(line)
            if hit:
                all_writes.append({"path": rel, "line": number, "instruction": line.strip(),
                                   "kind": "MOV SS" if hit.group("mov") else
                                   ("POP SS" if hit.group("pop") else "LSS")})
    mutator_modules: dict[str, int] = {}
    for row in all_writes:
        mutator_modules[row["path"]] = mutator_modules.get(row["path"], 0) + 1
    require(mutator_modules == {"src/root/m1B73.asm": 8, "src/root/m28BC.asm": 4}
            and all(row["kind"] == "MOV SS" for row in all_writes)
            and not inline_asm_setters,
            f"global source SS-mutator inventory changed: {mutator_modules}; inline asm setters={inline_asm_setters}")

    startup, startup_pin = startup_evidence()
    interrupt_cases, interrupt_pins = interrupt_evidence()
    numeric_text = line_text(ROOT / "src/S00/m31AD.asm")
    numeric_sites = [{"source": "src/S00/m31AD.asm", "line": number,
                      "instruction": line.strip(), "procedure": "_o00_31AD_013A"}
                     for number, line in enumerate(numeric_text.splitlines(), 1)
                     if re.search(r"\bss\s*:\s*\[\s*si\s*\+\s*41d0h\s*\]", line, re.I)]
    require([row["line"] for row in numeric_sites] == [422, 472, 509],
            "S00 numeric SS:[SI+41D0h] worklist changed")
    root_display = line_text(ROOT / "src/root/m1B4E.asm")
    mouse_text = line_text(ROOT / "src/root/m1B73.asm")
    root_binding = binding_by_module.get("root:1B73")
    require(root_binding is not None
            and root_binding["source"].replace("\\", "/") == "src/root/m1B73.asm"
            and sha((ROOT / "src/root/m1B73.asm").read_bytes()) == root_binding["source_sha256"],
            "root:1B73 source-binding pin changed for the separate pointer gate")
    root_bound = bindings.apply_binding(mouse_text, root_binding)
    root_object_result = compiler.assemble(root_bound, "masm510", ["/Mx", "/L"],
                                           basename="R1B73", keep=True)
    require(root_object_result.ok, "MASM could not freshly reproduce root:1B73 source for the separate pointer gate")
    root_object = OmfReader().read(root_object_result.obj, "root-1B73-pointer-gate")
    pointer_fixups = [dict(row) for row in root_object.linker_fixups
                      if row.get("target") == "_g_5A9C"]
    require(len(pointer_fixups) == 2
            and [(row["loc"], row["frame"]) for row in pointer_fixups] ==
            [("base16", "_DATA"), ("offset16", "DGROUP")],
            "fresh root:1B73 OMF no longer has the expected separate _g_5A9C SEG/OFF pair")
    g5a9c = {"source": "src/root/m1B73.asm", "sites": [
        {"line": source_line(mouse_text, "mov cx, seg _g_5A9C"),
         "instruction": "mov cx, seg _g_5A9C", "fixup": pointer_fixups[0]},
        {"line": source_line(mouse_text, "mov cx, offset DGROUP:_g_5A9C"),
         "instruction": "mov cx, offset DGROUP:_g_5A9C", "fixup": pointer_fixups[1]}],
        "disposition": "Keep unresolved: storage owner, complete segment-address producer, and ES consumer paths are not established by this driver-frame audit."}
    require(re.search(r"(?im)^_g_41c0\s+db\s+0,\s*1,\s*2,\s*3,\s*4,\s*5,\s*6,\s*7,\s*8,\s*9,\s*10,\s*11,\s*12,\s*13,\s*14,\s*15\b", root_display)
            and "; 16-byte fill patterns" in root_display,
            "candidate _g_41C0+16 owner source changed")
    unresolved = {
        "module_local_ss_symbol_operands": {
            "count": len(unresolved_rows), "sites": unresolved_rows,
            "disposition": "Ten SS:_g references outside the 128 selected external OFFSET16/_DATA fixups remain unresolved; do not infer a frame binding from this batch."},
        "_g_5A9C_segment_offset_pair": g5a9c,
        "literal_ss_numeric_family": {
            "count": len(numeric_sites), "sites": numeric_sites,
            "candidate_owner": {"source": "src/root/m1B4E.asm",
                                "symbol_line": source_line(root_display, "_g_41C0\t\tdb"),
                                "symbol": "_g_41C0", "symbol_extent_bytes": 16,
                                "pattern_line": source_line(root_display, "; 16-byte fill patterns"),
                                "candidate_relation": "41D0h is the nominal _g_41C0 address plus its 16-byte color map.",
                                "unproven": ["live SI bounds", "complete reachable storage ownership"]},
            "disposition": "No relocation exists; keep outside the 128 external fixups."},
    }
    source_pins = [pin(SOURCE_BINDINGS), pin(QUEUE_CONTRACT), pin(STATIC_INDEX),
                   pin(ROOT / "layout/toolchain.json"),
                   pin(ROOT / "layout/manifest.json"), startup_pin]
    source_pins.extend(registered_input_pins)
    for module in MODULES:
        source_pins.append(pin(ROOT / module["source"], binding_by_module[module["module"]]["source_sha256"]))
    source_pins += [pin(ROOT / "src/root/m1B73.asm"), pin(ROOT / "src/root/m28BC.asm"),
                    pin(ROOT / "src/root/m1B4E.asm")]
    tool_profile = tc["profiles"]["masm510"]
    source_pins.append(pin(Path(tc["runner"]["path"]), tc["runner"]["sha256"]))
    for relative, expected in tool_profile["files"].items():
        source_pins.append(pin(Path(tool_profile["directory"]) / relative, expected))

    report = {
        "schema": "simant-driver-ss-provenance-audit-v1",
        "scope": "Fresh source-bound MASM controls and accepted CRT/interrupt state proof for S00:31AD, S01:3126, S02:3126, S03:3126.",
        "original_executable_read": False,
        "denied_original_input_reads": denied,
        "source_binding_packet": {"path": "work/source-only-dos/source-bindings-v1.json",
                                  "sha256": sha(packet_raw), "size": len(packet_raw)},
        "startup": startup,
        "interrupt_display_stack_dominance": interrupt_cases,
        "global_ss_mutator_inventory": {"source_files": len(all_files),
                                         "source_inventory_sha256": sha("\n".join(
                                             f"{r['path']} {r['sha256']}" for r in all_files).encode()),
                                         "canonical_source_file_count": len(canonical_paths),
                                         "registered_behavior_whole_module_source_count": len(registered_sources),
                                         "registered_behavior_whole_module_sources": registered_sources,
                                         "inline_asm_construct_count": len(asm_markers),
                                         "inline_asm_constructs": asm_markers,
                                         "inline_asm_ss_setters": inline_asm_setters,
                                         "mutators": all_writes,
                                         "interpretation": "The scan includes canonical source files, all 29 registered behavior whole-module sources, and corrected DrawBalloons as a separate 30th whole module. Only root:m1B73 and root:m28BC write SS; the two behavioral inline-ASM blocks contain no SS setter. Both interrupt modules save and restore interrupted SS:SP; display-driving interrupt branches switch to DGROUP before their listed dispatch calls."},
        "candidate_counts": counts,
        "candidate_fixups": driver_rows,
        "normal_driver_entry": {"entry_distance": "FAR for all 128 sites",
                                "ss_writes_in_four_modules": 0,
                                "proof": "With no MOV SS, POP SS, or LSS in any of the four TUs, all their local control-flow paths and same-TU calls preserve the inherited entry SS.",
                                "candidate_ss_at_entry": "DGROUP is established by CRT before main; each listed async display route switches to a DGROUP private stack before dispatch."},
        "unresolved_families": unresolved,
        "pins": source_pins,
        "all_checks_pass": len(driver_rows) == 128 and counts == expected_counts and not denied,
    }
    return report, builds


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    report, _ = run_audit()
    AUDIT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("driver SS provenance audit", report["candidate_counts"],
          "unresolved local", report["unresolved_families"]["module_local_ss_symbol_operands"]["count"],
          "all_checks_pass", report["all_checks_pass"])
    return 0 if report["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
