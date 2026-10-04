"""Full-extent hard-tail diagnostics. This module never participates in acceptance.

Examples::
    python tools/hardtail.py S15:384C:0239
    python tools/hardtail.py --triage --catalog build/workers/hardtail/catalog.json
    python tools/hardtail.py FUNCTION --source draft.c --json build/workers/NAME/report.json

All reports retain the strict ``modules.verify_module`` verdict separately from
the diagnostic stream analysis. CFG results are conservative: indirect jumps,
unrecognized switch tables, and undecodable bytes are called out explicitly.
The dense-switch recognizer preserves table extents and all case edges separately.
"""
from __future__ import annotations

import argparse
import collections
import difflib
import hashlib
import json
import re
import sys
from pathlib import Path

import autosearch
import codecfg
import diag
import match
import mismatch
import modctx
import modules
import variants

ROOT = Path(__file__).resolve().parents[1]
GPRS = {
    "ax", "bx", "cx", "dx", "si", "di", "ah", "al", "bh", "bl", "ch", "cl",
    "dh", "dl", "eax", "ebx", "ecx", "edx", "esi", "edi", "rax", "rbx", "rcx", "rdx",
}
FRAME_REGS = {"bp", "ebp", "sp", "esp", "cs", "ds", "es", "ss", "fs", "gs"}
TAIL_CLASSES = ('ALLOCATOR_TAIL', 'CONTROL_FLOW_TAIL', 'EXPRESSION_TAIL',
                'DECLARATION_CONTEXT_TAIL', 'WIDTH_TYPE_TAIL', 'RELOCATION_RECORD_TAIL',
                'STRUCTURAL_TAIL', 'POSSIBLE_ASM')


def _register_role(name):
    name = (name or "").lower()
    if name in {"ah", "bh", "ch", "dh"}:
        return "<gpr8_hi>"
    if name in {"al", "bl", "cl", "dl"}:
        return "<gpr8_lo>"
    if name in {"ax", "bx", "cx", "dx", "si", "di"}:
        return "<gpr16>"
    if name in {"eax", "ebx", "ecx", "edx", "esi", "edi"}:
        return "<gpr32>"
    if name in {"rax", "rbx", "rcx", "rdx", "rsi", "rdi"}:
        return "<gpr64>"
    return name


def load_catalog(path: Path | None) -> dict:
    if path is None:
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data if isinstance(data, list) else data.get("records", data.get("functions", data.get("rows", [])))
    result = {}
    if isinstance(data, dict) and not rows:
        rows = [dict(v, function=k) for k, v in data.items() if isinstance(v, dict)]
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = row.get("function", row.get("name", row.get("target")))
        if name:
            result[str(name)] = row
    return result


def _source_text(ctx, source: Path | None):
    if source is None:
        return ctx.text
    return source.read_text(encoding="latin1")


def _bound_full(ctx, obj, row):
    """Bind from function public through its next object public, retaining candidate tail."""
    pub, prec = match.public_in(obj, row["name"])
    if prec is None:
        return None, None
    body = obj.segments.get(prec["segment"], b"")
    pubs = [p["offset"] for p in obj.publics + getattr(obj, "local_publics", [])
            if p["segment"] == prec["segment"]]
    pub_off = prec["offset"]
    later = [off for off in pubs if off > pub_off]
    end = min(later, default=len(body))
    if end == len(body) and end - pub_off == row["size"] + 1 and body[-1:] == b"\x90" and end % 2 == 0:
        end -= 1
    extent = end - pub_off
    if extent < 0:
        return None, prec
    target = match.Target(row["unit"], row["seg"], row["off"], extent)
    bound = match.Binder(target, obj, prec["segment"], pub, ctx.placements_bind).bind()
    return bound, prec


def _branch_target(ins):
    if ins["control"] not in ("jump", "call"):
        return None
    if len(ins["operands"]) != 1 or ins["operands"][0]["kind"] != "imm":
        return "indirect"
    op = ins["operands"][0]
    # In 16-bit Capstone, relative immediates are reported as absolute addresses.
    return int(op["value"])


def _conditional_jump(mnemonic):
    m = mnemonic.lower()
    return (m.startswith("loop") or m in {"jcxz", "jecxz"} or
            (m.startswith("j") and m != "jmp"))


def cfg(rows, data_size, tables=()):
    """Create basic blocks and typed edges; only codecfg-proven tables add switch edges."""
    if not rows:
        return {"blocks": [], "edges": [], "limitations": ["no decoded instructions"], "complete": False}
    offsets = [int(r["load_offset"]) for r in rows]
    index_at = {off: i for i, off in enumerate(offsets)}
    boundaries = {0}
    limitations = []
    if sum(len(bytes.fromhex(r['bytes'])) for r in rows) + sum(t['end']-t['start'] for t in tables) != data_size:
        limitations.append('incomplete decode; undecoded bytes are not CFG nodes')
    for i, ins in enumerate(rows):
        target = _branch_target(ins)
        if ins.get('switch_targets'):
            for target in ins['switch_targets']:
                boundaries.add(target)
                if target not in index_at:
                    limitations.append('recognized switch enters undecoded bytes or instruction interior')
        elif target == "indirect":
            if ins["mnemonic"].startswith("j"):
                limitations.append(f"indirect jump at +0x{ins['load_offset']:X}; switch/table target unresolved")
        elif target is not None and ins['control'] == 'jump' and 0 <= target < data_size:
            boundaries.add(target)
            if target not in index_at:
                limitations.append(f"branch at +0x{ins['load_offset']:X} enters undecoded bytes or instruction interior")
        if ins["control"] in ("jump", "return") and i + 1 < len(rows):
            boundaries.add(offsets[i + 1])
    sorted_bounds = sorted(b for b in boundaries if b in index_at)
    blocks = []
    ins_to_block = {}
    for n, start in enumerate(sorted_bounds):
        ix = index_at[start]
        stop = index_at[sorted_bounds[n + 1]] if n + 1 < len(sorted_bounds) else len(rows)
        if stop <= ix:
            continue
        bid = len(blocks)
        block = {"id": bid, "start": start, "end": offsets[stop] if stop < len(rows) else data_size,
                 "instructions": [ix, stop],
                 "first_mnemonic": rows[ix]["mnemonic"], "last_mnemonic": rows[stop - 1]["mnemonic"]}
        blocks.append(block)
        for j in range(ix, stop):
            ins_to_block[j] = bid
    edges = []
    for b in blocks:
        ix, stop = b["instructions"]
        for call_ix in range(ix, stop):
            if rows[call_ix]["control"] == "call":
                edges.append({"from": b["id"], "to": None, "kind": "call",
                              'mnemonic': rows[call_ix]['mnemonic'], 'instruction_index': call_ix})
        last = rows[stop - 1]
        target = _branch_target(last)
        fall = stop < len(rows) and stop in ins_to_block
        if last["control"] == "return":
            continue
        if last["control"] == "jump":
            if last.get('switch_targets'):
                for case, destination in enumerate(last['switch_targets']):
                    edges.append({'from': b['id'], 'to': ins_to_block.get(index_at.get(destination)),
                                  'kind': 'switch', 'case_index': case})
            elif target == "indirect":
                edges.append({"from": b["id"], "to": None, "kind": "indirect"})
            elif target in index_at:
                edges.append({"from": b["id"], "to": ins_to_block[index_at[target]], "kind": "branch"})
            else:
                edges.append({"from": b["id"], "to": None, "kind": "external_or_data_target"})
            if _conditional_jump(last["mnemonic"]) and fall:
                edges.append({"from": b["id"], "to": ins_to_block[stop], "kind": "fallthrough"})
        elif last["control"] == "call":
            if fall:
                edges.append({"from": b["id"], "to": ins_to_block[stop], "kind": "fallthrough"})
        else:
            if fall:
                edges.append({"from": b["id"], "to": ins_to_block[stop], "kind": "fallthrough"})
    reachable = {0} if blocks else set()
    changed = True
    while changed:
        changed = False
        for edge in edges:
            if edge["from"] in reachable and edge["to"] is not None and edge["to"] not in reachable:
                reachable.add(edge["to"])
                changed = True
    non_nop_unreachable = [b for b in blocks if b['id'] not in reachable and
                           any(rows[i]['mnemonic'] != 'nop' for i in range(*b['instructions']))]
    nop_unreachable = [b['id'] for b in blocks if b['id'] not in reachable and
                       all(rows[i]['mnemonic'] == 'nop' for i in range(*b['instructions']))]
    if non_nop_unreachable:
        limitations.append("unreachable decoded bytes may contain embedded data or switch tables")
    return {"blocks": blocks, "edges": edges, "limitations": sorted(set(limitations)),
            'tables': list(tables),
            'unreachable_nop_blocks': nop_unreachable,
            "complete": not limitations}


def cfg_comparison(left, right):
    """Indexed block topology is independent of instruction counts and byte layout.

    This is deliberately not a graph-isomorphism or semantic-equivalence proof.
    Indirect edges and embedded/undecoded bytes prevent a topology MATCH assertion.
    """
    a, b = _cfg_signature(left), _cfg_signature(right)
    available = left['complete'] and right['complete']
    return {'match': a == b if available else None,
            'status': ('MATCH' if a == b else 'MISMATCH') if available else 'UNKNOWN',
            'similarity': round(difflib.SequenceMatcher(a=a[1], b=b[1], autojunk=False).ratio(), 4)
                          if available else None,
            'target': left, 'candidate': right,
            'limitations': sorted(set(left['limitations'] + right['limitations'])),
            'basis': 'block order and typed edges; instruction counts are a separate skeleton metric'}


def _normalized(rows, fixups, *, ignore_registers=False, ignore_bp=False,
                ignore_relocations=False, ignore_branch_destinations=False):
    by_at = collections.defaultdict(list)
    out = []
    for r in rows:
        offset = int(r["load_offset"])
        instruction_fixups = []
        for f in fixups:
            at = int(f.get("at", -1))
            width = int(f.get("width", {"offset16": 2, "base16": 2, "pointer32": 4,
                                         "loader-offset16": 2}.get(f.get("loc"), 0)))
            if offset <= at < offset + len(bytes.fromhex(r["bytes"])) or offset < at + width <= offset + len(bytes.fromhex(r["bytes"])):
                instruction_fixups.append(f)
        encoded_fields = r.get("operand_fields", [])
        imm_field = encoded_fields[0] if encoded_fields else None
        disp_field = encoded_fields[-1] if len(encoded_fields) > 1 else None
        def overlaps(f, field):
            if not field:
                return False
            start, end = offset + field[0], offset + field[1]
            at = int(f.get("at", -1))
            width = int(f.get("width", {"offset16": 2, "base16": 2, "pointer32": 4,
                                         "loader-offset16": 2}.get(f.get("loc"), 0)))
            return at < end and at + width > start
        imm_relocated = any(overlaps(f, imm_field) for f in instruction_fixups)
        disp_relocated = any(overlaps(f, disp_field) for f in instruction_fixups)
        operands = []
        for original in r["operands"]:
            op = dict(original)
            if op["kind"] == "reg" and ignore_registers and op.get("reg", "").lower() in GPRS:
                op["reg"] = _register_role(op.get("reg"))
            if op["kind"] == "mem":
                if ignore_branch_destinations and r.get('switch_targets'):
                    op['disp'] = '<switch-table-address>'
                for key in ("base", "index"):
                    val = op.get(key, "") or ""
                    if ignore_registers and val.lower() in GPRS:
                        op[key] = _register_role(val)
                    if ignore_bp and val.lower() in {"bp", "ebp"}:
                        op[key] = "<bp>"
                if ignore_bp and (op.get("base") or "").lower() in ("<bp>", "bp"):
                    op["disp"] = "<home>"
                if ignore_relocations and op["kind"] == "mem" and disp_relocated:
                    op["disp"] = "<reloc>"
            if op["kind"] == "imm" and ignore_branch_destinations and r["control"] in ("jump", "call"):
                op["value"] = "<target>"
            if ignore_relocations and op["kind"] == "imm" and imm_relocated:
                # Keep the fixup's symbolic identity below while ignoring only its
                # already-bound numeric field value in the instruction signature.
                op["value"] = "<reloc>"
            operands.append(op)
        fields = [{"bound_fixup": True} for f in instruction_fixups]
        out.append({"mnemonic": r["mnemonic"], "control": r["control"], "operands": operands,
                    "fixups": fields})
    return out


def _similarity(left, right):
    if not left and not right:
        return 1.0
    # Levenshtein similarity is diagnostic and bounded to instruction signatures.
    n, m = len(left), len(right)
    prev = list(range(m + 1))
    for i in range(1, n + 1):
        cur = [i] + [0] * m
        for j in range(1, m + 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1,
                         prev[j - 1] + (left[i - 1] != right[j - 1]))
        prev = cur
    return round(1 - prev[m] / max(n, m, 1), 4)


def _difference_detail(a, b, decoded=None):
    """Align strict decoded rows and expose insertions, widths, branches, fixups."""
    if decoded:
        left, right = decoded
        pairs, _ = mismatch._align(left, right, [])
        cmp = {'alignment': [{'target_index': i, 'candidate_index': j, 'level': level} for i, j, level in pairs],
               'target_instructions': left, 'candidate_instructions': right,
               'decode_complete': sum(len(bytes.fromhex(r['bytes'])) for r in left) <= len(a) and
                                  sum(len(bytes.fromhex(r['bytes'])) for r in right) <= len(b)}
    else:
        cmp = mismatch.compare_streams(a, b)
    pairs = cmp["alignment"]
    left, right = cmp["target_instructions"], cmp["candidate_instructions"]
    missing, extra, widths, branches, relocation = [], [], [], [], []
    for pair in pairs:
        i, j = pair["target_index"], pair["candidate_index"]
        if i is None:
            extra.append({"candidate_index": j, "instruction": right[j]["instruction"]})
            continue
        if j is None:
            missing.append({"target_index": i, "instruction": left[i]["instruction"]})
            continue
        x, y = left[i], right[j]
        if x["mnemonic"] == y["mnemonic"]:
            if [z.get("width") for z in x["operands"]] != [z.get("width") for z in y["operands"]]:
                widths.append({"target": x["instruction"], "candidate": y["instruction"]})
            if x["control"] == 'jump' and (_branch_target(x) != _branch_target(y) or x['mnemonic'] != y['mnemonic']):
                branches.append({"target": x["instruction"], "candidate": y["instruction"]})
        elif x['control'] == y['control'] == 'jump':
            branches.append({'target': x['instruction'], 'candidate': y['instruction']})
    n = min(len(a), len(b))
    return {"missing_instructions": missing, "extra_instructions": extra,
            "width_differences": widths, "branch_layout_differences": branches,
            "alignment": cmp["alignment"], "decode_complete": cmp["decode_complete"],
            "relocation_differences": relocation,
            'byte_differences': sum(a[i] != b[i] for i in range(n)) + abs(len(a)-len(b)),
            'extent_delta': len(b)-len(a)}


def _relocation_delta(original, candidate):
    # Identity includes address, location class, target spelling and binding kind.
    def key(x):
        return (x.get("at"), x.get("loc"), x.get("target"), x.get("kind"))
    a, b = collections.Counter(map(key, original)), collections.Counter(map(key, candidate))
    return {"missing": [list(k) for k, n in (a - b).items() for _ in range(n)],
            "extra": [list(k) for k, n in (b - a).items() for _ in range(n)]}


def compare_streams(target_bytes, candidate_bytes, target_fixups=(), candidate_fixups=(), options=None):
    """Pure stream comparison for already-bound inputs; never changes strict verdicts.

    ``options`` may set ignore_registers, ignore_bp, ignore_relocations and
    ignore_branch_destinations for a secondary normalized similarity only.
    """
    target_bytes, candidate_bytes = bytes(target_bytes), bytes(candidate_bytes)
    left, right = mismatch._decode(target_bytes), mismatch._decode(candidate_bytes)
    strict = mismatch.compare_streams(target_bytes, candidate_bytes)
    normalized_defaults = {"ignore_registers": True, "ignore_bp": True,
                          "ignore_relocations": True, "ignore_branch_destinations": True}
    options = {**normalized_defaults, **(options or {})}
    lnorm = _normalized(left, target_fixups, **options)
    rnorm = _normalized(right, candidate_fixups, **options)
    c_left, c_right = cfg(left, len(target_bytes)), cfg(right, len(candidate_bytes))
    detail = _difference_detail(target_bytes, candidate_bytes)
    detail["relocation_differences"] = _relocation_delta(target_fixups, candidate_fixups)
    return {"semantic_skeleton": "MATCH" if _normalized(left, target_fixups, **options) == _normalized(right, candidate_fixups, **options) else "MISMATCH",
            "cfg": cfg_comparison(c_left, c_right),
            "normalized_instruction_similarity": _similarity(lnorm, rnorm),
            "allocator": {"target": _allocator_signature(left), "candidate": _allocator_signature(right)},
            "differences": detail, "instruction_report": strict,
            "fixup_identity_obligations": {"target": "caller supplied symbolic identities",
                                           "candidate": list(candidate_fixups)},
            "strict_acceptance": "NOT_EVALUATED; this function has no authority to accept code"}


def _classify_hardtail(strict_bound, target_size, candidate_size, detail, skeleton_match, cfg_match,
                       normalized_similarity, exhausted):
    """Assign a diagnostic family; uncertainty is explicit and no class accepts code."""
    rel = detail.get("relocation_differences", {})
    if not detail.get("decode_complete", False):
        return "STRUCTURAL_TAIL"
    classes = set(strict_bound.get('classes', []))
    # Different encoded length can result from register-specific encodings while
    # every normalized instruction and topology remains unchanged. Extent still fails.
    if skeleton_match and cfg_match is True and classes.intersection({'STACK_SLOT_ALLOCATION', 'REGISTER_ALLOCATION'}):
        if strict_bound.get('causal_context_probe'):
            return 'DECLARATION_CONTEXT_TAIL'
        return 'ALLOCATOR_TAIL'
    # Inserted instructions also move relocation sites and branch addresses.
    # Those numeric changes alone do not establish a relocation-record or CFG tail.
    if skeleton_match and (rel.get("missing") or rel.get("extra") or
                           rel.get("missing_sites") or rel.get("extra_sites")):
        return "RELOCATION_RECORD_TAIL"
    if cfg_match is False:
        return "CONTROL_FLOW_TAIL" if normalized_similarity >= .9 else "STRUCTURAL_TAIL"
    if cfg_match is None:
        return 'STRUCTURAL_TAIL'
    if detail.get("width_differences"):
        return "WIDTH_TYPE_TAIL"
    if not skeleton_match:
        return 'EXPRESSION_TAIL' if normalized_similarity >= .9 or detail.get('single_block_pair') else 'STRUCTURAL_TAIL'
    if classes.intersection({"STACK_SLOT_ALLOCATION", "REGISTER_ALLOCATION"}):
        return "ALLOCATOR_TAIL"
    return "EXPRESSION_TAIL"


def _allocator_signature(rows):
    homes = collections.defaultdict(list)
    registers = collections.Counter()
    accesses = collections.defaultdict(list)
    for ins in rows:
        for operand_index, op in enumerate(ins["operands"]):
            if op["kind"] == "mem" and (op.get("base") or "").lower() in ("bp", "ebp"):
                homes[str(op.get("disp"))].append(ins["mnemonic"])
                accesses[op.get('disp')].append({'offset': ins['load_offset'],
                    'mnemonic': ins['mnemonic'], 'operand': operand_index, 'width': op['width'],
                    'address_taken': ins['mnemonic'] == 'lea'})
            if op["kind"] == "reg":
                r = op.get("reg", "").lower()
                if r in GPRS:
                    registers[r] += 1
    return {"stack_homes": dict(sorted(homes.items())), "register_uses": dict(sorted(registers.items())),
            'stack_slots': [{'displacement': disp, 'first_use_offset': sites[0]['offset'],
                             'use_count': len(sites), 'access_widths': sorted({s['width'] for s in sites}),
                             'address_taken_count': sum(s['address_taken'] for s in sites),
                             'sites': sites} for disp, sites in sorted(accesses.items())],
            'limit': 'observed machine accesses; source local identities and C2 liveness are not inferred'}


def analyze_bound(ctx, obj, function, strict_verdict=None, catalog_entry=None):
    """Analyze an already compiled OMF object. No compiler invocation is performed."""
    f = ctx.function(function) if isinstance(function, str) else function
    name = f["name"]
    full, _ = _bound_full(ctx, obj, f)
    row = {"function": name, "module": ctx.key, "profile": ctx.profile, "flags": ctx.flags,
           "authority": "DIAGNOSTIC_ONLY; strict acceptance is the separate verifier verdict"}
    if strict_verdict is not None:
        row["strict"] = {"exact": strict_verdict.get("exact"), "reasons": strict_verdict.get("reasons", []),
                         "reloc_order": strict_verdict.get("reloc_order"),
                         "candidate_bytes": strict_verdict.get("candidate_extent_size"),
                         "target_bytes": f["size"], "module_exact": strict_verdict.get("module_exact"),
                         "peer_losses": strict_verdict.get("peer_losses", []),
                         "data_losses": strict_verdict.get("data_losses", [])}
    if full is None or full.unbound:
        row.update({"diagnostic_error": "full-extent binding unavailable or unresolved",
                    "unbound": getattr(full, "unbound", [])})
        return row
    exe = match.exemod.load()
    target = exe.read(f["unit"], f["seg"] * 16 + f["off"], f["size"])
    candidate = full.candidate
    candidate_fixups = [dict(x) for x in full.fixups]
    target_base = f["seg"] * 16 + f["off"]
    target_sites = [s * 16 + o - target_base for s, o in exe.unit_relocs(f["unit"])
                    if target_base <= s * 16 + o < target_base + f["size"]]
    candidate_sites = [int(site) - target_base for site in full.relocs_candidate]
    site_missing = sorted(set(target_sites) - set(candidate_sites))
    site_extra = sorted(set(candidate_sites) - set(target_sites))
    # Oracle relocation records identify sites only. The original symbol identity is
    # unavailable; candidate fixup target names remain visible in candidate_fixups.
    target_fx = [{"at": int(x), "loc": "oracle-site", "target": "unknown", "kind": "bound", "width": 2}
                 for x in target_sites]
    candidate_fixups = [{**x, "width": {"pointer32": 4, "base16": 2, "offset16": 2,
                                        "loader-offset16": 2}.get(x.get("loc"), 0)}
                        for x in candidate_fixups]
    candidate_reloc_fx = [{"at": int(site) - target_base, "width": 2, "loc": "oracle-site",
                           "target": "unknown", "kind": "bound"}
                          for site in full.relocs_candidate]
    try:
        flow_target, flow_candidate = codecfg.decode(target, f['off']), codecfg.decode(candidate, f['off'])
        decoded_target, decoded_candidate = flow_target['instructions'], flow_candidate['instructions']
        table_aware = bool(flow_target['tables'] or flow_candidate['tables'])
        report = mismatch.compare_streams(target, candidate)
        report["function_extent"] = {"target_bytes": f["size"], "candidate_bytes": len(candidate),
                                     "candidate_payload_complete": len(candidate) == full.candidate_extent_size}
        compact = mismatch.compact(report)
        detail = _difference_detail(target, candidate, (decoded_target, decoded_candidate) if table_aware else None)
        detail['decode_complete'] = flow_target['complete'] and flow_candidate['complete']
        detail['instruction_alignment_basis'] = 'recognized code/table separation' if table_aware else 'linear decode'
        detail["relocation_differences"] = {"missing_sites": site_missing, "extra_sites": site_extra,
                                            "identity": "oracle relocation table records sites; original target names unavailable"}
        cfg_target = cfg(decoded_target, len(target), flow_target['tables'])
        cfg_candidate = cfg(decoded_candidate, len(candidate), flow_candidate['tables'])
        cfg_report = cfg_comparison(cfg_target, cfg_candidate)
        cfg_match = cfg_report['match']
        detail['single_block_pair'] = len(cfg_target['blocks']) == len(cfg_candidate['blocks']) == 1
        skeleton_options = {"ignore_registers": True, "ignore_bp": True,
                            "ignore_relocations": True, "ignore_branch_destinations": True}
        skeleton_match = (_normalized(decoded_target, target_fx, **skeleton_options) ==
                          _normalized(decoded_candidate, candidate_reloc_fx, **skeleton_options))
        options = {"ignore_registers": True, "ignore_bp": True,
                   "ignore_relocations": True, "ignore_branch_destinations": True}
        similarity = _similarity(_normalized(decoded_target, target_fx, **options),
                                 _normalized(decoded_candidate, candidate_reloc_fx, **options))
        exhausted = (catalog_entry or {}).get("exhausted_dimensions", (catalog_entry or {}).get("exhausted", []))
        likely = _classify_hardtail({"classes": compact.get("classifications", [])}, len(target),
                                    len(candidate), detail, skeleton_match, cfg_match, similarity, exhausted)
        peer_losses = strict_verdict.get("peer_losses", []) if strict_verdict else []
        data_losses = strict_verdict.get("data_losses", []) if strict_verdict else []
        valid_context = not peer_losses and not data_losses
        row.update({"target_size": len(target),
                    "candidate_size": len(candidate), "best_valid_candidate_size": len(candidate) if valid_context else None,
                    'bound_code_sha256': {'target': hashlib.sha256(target).hexdigest(),
                                          'candidate': hashlib.sha256(candidate).hexdigest()},
                    "candidate_full_extent_size": full.candidate_extent_size,
                    "semantic_skeleton": "MATCH" if skeleton_match else "MISMATCH",
                    "cfg": cfg_report,
                    "normalized_instruction_similarity": similarity, "likely_class": likely,
                    'cause_status': 'unresolved; instruction residue alone cannot distinguish allocator, lifetime and declaration-history causes',
                    "allocator": {"target": _allocator_signature(decoded_target),
                                  "candidate": _allocator_signature(decoded_candidate)},
                    "differences": detail,
                    "stack_slot_mapping": _slot_observations(report),
                    "register_role_mapping": _register_observations(report),
                    "best_archived_source": (catalog_entry or {}).get("best_source", (catalog_entry or {}).get("source", (catalog_entry or {}).get("path"))),
                    "already_exhausted_search_dimensions": exhausted,
                    "recommended_next_hypothesis": (catalog_entry or {}).get("recommended_next_hypothesis",
                        "Use the first structural divergence to choose one source-form or compiler-context probe."),
                    "instruction_report": report,
                    "candidate_fixups": candidate_fixups,
                    'code_table_separation': {'target': {k: v for k, v in flow_target.items() if k != 'instructions'},
                                              'candidate': {k: v for k, v in flow_candidate.items() if k != 'instructions'}},
                    'normalized_instructions': {'target': normalized_representation(decoded_target, target_fx, **skeleton_options),
                                                'candidate': normalized_representation(decoded_candidate, candidate_reloc_fx, **skeleton_options)},
                    'target_relocation_sites': target_sites,
                    "relocation_differences": detail["relocation_differences"]})
        row['allocator']['target']['frame_bytes'] = _frame_size(decoded_target)
        row['allocator']['candidate']['frame_bytes'] = _frame_size(decoded_candidate)
        row['stack_slot_mapping_obligations'] = [f for f in report['patterns']['families'] if f['kind'] == 'BP_DISPLACEMENT']
        row['register_role_mapping_obligations'] = [f for f in report['patterns']['families'] if f['kind'] == 'REGISTER_ROLE']
        row['allocator_operand_residue'] = allocator_operand_residue(decoded_target, decoded_candidate) if skeleton_match else None
    except Exception as exc:
        row["diagnostic_error"] = f"{type(exc).__name__}: {exc}"
    return row


def allocator_operand_residue(target, candidate):
    """Local use-site signature, never a global register renaming or liveness proof."""
    result = []
    for index, (left, right) in enumerate(zip(target, candidate)):
        for operand, (a, b) in enumerate(zip(left['operands'], right['operands'])):
            changes = []
            if a['kind'] == b['kind'] == 'reg' and a.get('reg') != b.get('reg'):
                changes.append({'kind': 'register', 'target': a['reg'], 'candidate': b['reg']})
            if a['kind'] == b['kind'] == 'mem':
                for key in ['base', 'index']:
                    if a.get(key) != b.get(key):
                        changes.append({'kind': 'memory_' + key, 'target': a.get(key), 'candidate': b.get(key)})
                if a.get('base') == b.get('base') == 'bp' and a.get('disp') != b.get('disp'):
                    changes.append({'kind': 'stack_home', 'target': a['disp'], 'candidate': b['disp']})
            for change in changes:
                result.append({**change, 'instruction_index': index, 'operand_index': operand,
                    'target_offset': left['load_offset'], 'candidate_offset': right['load_offset'],
                    'width': a.get('width'), 'target_instruction': left['instruction'],
                    'candidate_instruction': right['instruction']})
    return {'sites': result,
            'basis': 'same normalized instruction skeleton; substitutions apply only to listed operand uses',
            'limit': 'a physical register can hold multiple values; unchanged uses elsewhere do not contradict this local signature; no liveness inference'}


def normalized_representation(rows, fixups, **options):
    """Export normalized operands together with every original encoded position.

    Skeleton comparison uses the operand signature alone; placement and extent
    remain explicit obligations even when register-specific encodings differ.
    """
    return [{**signature, 'placement': {'instruction_index': index,
                'offset': row['load_offset'], 'encoded_length': len(bytes.fromhex(row['bytes']))}}
            for index, (row, signature) in enumerate(zip(rows, _normalized(rows, fixups, **options)))]


def _slot_observations(report):
    result = []
    for island in report.get("islands", []):
        for c in island.get("classifications", []):
            if c.get("class") == "STACK_SLOT_ALLOCATION":
                result.extend(c.get("evidence", []))
    return result


def _register_observations(report):
    result = []
    for island in report.get("islands", []):
        for c in island.get("classifications", []):
            if c.get("class") == "REGISTER_ALLOCATION":
                result.extend(c.get("evidence", []))
    return result


def analyze_module(names, out: Path, source: Path | None = None, catalog=None):
    ctx = modctx.resolve(func=names[0], source=source)
    text = _source_text(ctx, source)
    for name in names:
        text = autosearch.unscaffold(text, name)
    ctx.text = text
    source_hash = hashlib.sha256(text.encode('latin1')).hexdigest()
    draft = out / (ctx.key.replace(":", "_").replace("@", "_") + '_' + source_hash[:12] + ".c")
    draft.write_text(text, encoding="latin1")
    claims = variants.check_set(ctx, names, claims_only=True, text=text)
    collected = {}
    strict_module = modules.verify_module(text, ctx.module_dict(), claims, collect=collected)
    if not strict_module.get("compile_ok"):
        return [{"function": n, "module": ctx.key, "strict": strict_module.get("claims", {}).get(n),
                 "compile_ok": False, "error": strict_module.get("log", "")[-2000:],
                 "authority": "DIAGNOSTIC_ONLY; acceptance remains modules.verify_module"} for n in names]
    obj = modctx.read_obj(collected["object"])
    object_path = draft.with_suffix('.obj')
    object_path.write_bytes(collected['object'])
    rows = []
    for name in names:
        verdict = dict(strict_module["claims"][name])
        strict_bound, _ = modctx.bind_function(ctx, obj, ctx.function(name))
        verdict.update(candidate_extent_size=getattr(strict_bound, "candidate_extent_size", None),
                       module_exact=strict_module.get("exact"),
                       peer_losses=[c["name"] for c in ctx.claims if not strict_module["claims"].get(c["name"], {}).get("exact")],
                       data_losses=[s for s, r in strict_module.get("data", {}).items() if not r.get("exact")])
        row = analyze_bound(ctx, obj, ctx.function(name), verdict, (catalog or {}).get(name))
        row.update(source_sha256=source_hash, compiled_source=str(draft),
                   compiled_object=str(object_path), object_sha256=hashlib.sha256(collected['object']).hexdigest(),
                   diagnostic_engine_sha256=diagnostic_engine_hash())
        rows.append(row)
    return rows


def _cfg_signature(value):
    return (len(value['blocks']),
            tuple((e["from"], e["to"], e["kind"], e.get('mnemonic'), e.get('case_index')) for e in value["edges"]))


def _frame_size(rows):
    # Framed modules either subtract SP directly or pass frame bytes to chkstk.
    if not any(r['mnemonic'] == 'push' and r['operands'] and r['operands'][0].get('reg') == 'bp'
               for r in rows[:3]):
        return 0
    for r in rows[:7]:
        ops = r['operands']
        if len(ops) == 2 and ops[1]['kind'] == 'imm' and (
                r['mnemonic'] == 'sub' and ops[0].get('reg') == 'sp' or
                r['mnemonic'] == 'mov' and ops[0].get('reg') == 'ax'):
            return ops[1]['value']
    return 0


def format_row(row):
    if row.get("diagnostic_error") or row.get("error"):
        return f"{row['function']}: diagnostic unavailable: {row.get('diagnostic_error') or row.get('error')}"
    strict = row.get("strict", {})
    d = row.get("differences", {})
    return (f"{row['function']}: class={row.get('likely_class', 'unknown')} "
            f"skeleton={row.get('semantic_skeleton', 'unknown')} cfg={row.get('cfg', {}).get('match', 'unknown')} "
            f"size={row.get('target_size', strict.get('target_bytes'))}/{row.get('best_valid_candidate_size', strict.get('candidate_bytes'))} "
            f"normalized={row.get('normalized_instruction_similarity', 'unknown')} "
            f"strict_exact={strict.get('exact')} missing={len(d.get('missing_instructions', []))} "
            f"extra={len(d.get('extra_instructions', []))} width={len(d.get('width_differences', []))} "
            f"branch={len(d.get('branch_layout_differences', []))}")


def context_pins():
    return {p: hashlib.sha256((modctx.ROOT / p).read_bytes()).hexdigest() for p in (
        'layout/manifest.json', 'layout/functions.json', 'layout/symbols.json',
        'layout/toolchain.json', 'layout/oracle.lock.json', 'tools/modules.py',
        'tools/match.py', 'tools/compiler.py', 'tools/omf.py', 'tools/modctx.py')}


def diagnostic_engine_hash():
    parts = {p: hashlib.sha256((ROOT / 'tools' / p).read_bytes()).hexdigest()
             for p in ['hardtail.py', 'mismatch.py', 'codecfg.py']}
    return hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("function", nargs="?")
    ap.add_argument("--source", type=Path)
    ap.add_argument("--triage", action="store_true")
    ap.add_argument("--reanalyze", type=Path, help="refresh diagnostics from hash-pinned retained objects; no compile or acceptance")
    ap.add_argument("--catalog", type=Path)
    ap.add_argument("--json", type=Path, help="write machine-readable report")
    ap.add_argument("--out", type=Path, default=Path("build/workers/hardtail_tool"))
    a = ap.parse_args(argv)
    if sum([bool(a.function), a.triage, bool(a.reanalyze)]) != 1 or (a.triage and a.source):
        ap.error("use FUNCTION [--source candidate.c], --triage, or --reanalyze report.json")
    out = modctx.under_build(a.out)
    out.mkdir(parents=True, exist_ok=True)
    catalog = load_catalog(a.catalog)
    if a.reanalyze:
        previous = json.loads(a.reanalyze.read_text(encoding='utf-8'))
        pins = previous.get('context_pins')
        if pins != context_pins():
            ap.error('retained report context pins absent or changed; run fresh strict triage')
        rows = []
        for old in previous['functions']:
            source_path, object_path = Path(old['compiled_source']), Path(old['compiled_object'])
            source = source_path.read_text(encoding='latin1')
            object_bytes = object_path.read_bytes()
            if hashlib.sha256(source.encode('latin1')).hexdigest() != old['source_sha256'] or hashlib.sha256(object_bytes).hexdigest() != old['object_sha256']:
                ap.error(f"retained source/object changed for {old['function']}")
            ctx = modctx.resolve(func=old['function'], source=source_path)
            row = analyze_bound(ctx, modctx.read_obj(object_bytes), old['function'], old['strict'], catalog.get(old['function']))
            row.update({k: old[k] for k in ['compiled_source', 'compiled_object', 'source_sha256', 'object_sha256']})
            row['diagnostic_engine_sha256'] = diagnostic_engine_hash()
            row['strict_provenance'] = 'reused unchanged strict verdict from retained compile; diagnostic reanalysis only'
            rows.append(row)
    else:
        names = diag.open_functions() if a.triage else [modctx.resolve(func=a.function).function(a.function)["name"]]
        groups = collections.OrderedDict()
        for n in names:
            key = modctx.resolve(func=n).key
            selected = a.source
            if selected is None and a.triage:
                candidate = (catalog.get(n) or {}).get("best_source")
                if candidate and Path(candidate).exists():
                    selected = Path(candidate)
            groups.setdefault((key, str(selected) if selected else None), []).append(n)
        rows = [r for (key, source_name), group in groups.items()
                for r in analyze_module(group, out, Path(source_name) if source_name else None, catalog)]
    report = {"schema": 1, "authority": "DIAGNOSTIC_ONLY; strict acceptance is unchanged",
              'classification_vocabulary': list(TAIL_CLASSES),
              'classification_policy': 'DECLARATION_CONTEXT requires a causal context probe; POSSIBLE_ASM requires positive compiler-exclusion evidence. Neither is inferred from failed C searches.',
              "context_pins": context_pins(),
              "functions": rows}
    dest = modctx.under_build(a.json) if a.json else out / 'index.json'
    dest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for row in rows:
        print(format_row(row))
    print(f"JSON: {dest}")
    return 0 if all(r.get("strict", {}).get("exact") for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
