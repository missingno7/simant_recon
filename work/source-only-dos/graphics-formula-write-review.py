"""Read-only source reachability receipt for the unadmitted graphics formulas.

This deliberately does not read the original executable, historical data bytes,
or any build image.  It checks a small set of source/evidence inputs and emits
only a JSON receipt below build/workers/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "build/workers/dos_graphics_formula_write_review/receipt.json"
STRICT = ROOT / "work/source-only-dos/static-completeness/f_1E57_038E.json"
EVIDENCE = ROOT / "evidence/behavior/functions/f_1E57_038E/contracts/window-valid-v1/evidence.json"
REGISTERED_SOURCE = ROOT / "evidence/behavior/functions/f_1E57_038E/contracts/window-valid-v1/module.c"
CLIP_SOURCE = ROOT / "src/root/m1E57.c"
SYMBOLS = ROOT / "layout/symbols.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(path: Path) -> dict:
    raw = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(raw).hexdigest(), "size": len(raw)}


def function_body(source: str, name: str) -> tuple[str, int, int]:
    lines = source.splitlines()
    starts = [i for i, line in enumerate(lines) if re.search(
        rf"^\s*(?:void|int)\s+far\s+{re.escape(name)}\s*\(", line)]
    if len(starts) != 1:
        raise RuntimeError(f"expected one definition/declaration occurrence for {name}, saw {len(starts)}")
    start = starts[0]
    brace_line = next((i for i in range(start, len(lines)) if "{" in lines[i]), None)
    if brace_line is None:
        raise RuntimeError(f"no body found for {name}")
    depth = 0
    for i in range(brace_line, len(lines)):
        # These reviewed function bodies contain no brace characters in strings
        # relevant to the brace count; this is an anchor extractor, not a C parser.
        depth += lines[i].count("{") - lines[i].count("}")
        if depth == 0:
            return "\n".join(lines[brace_line:i + 1]), start + 1, i + 1
    raise RuntimeError(f"unterminated body for {name}")


def evidence_audit() -> dict:
    strict = json.loads(STRICT.read_text(encoding="utf-8"))
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    source_hash = digest(REGISTERED_SOURCE)
    evidence_hash = digest(EVIDENCE)
    if strict.get("status") != "BEHAVIOR_EXACT_CONFIRMED":
        raise RuntimeError("registered f_1E57_038E status is not confirmed")
    if strict["registered_source"]["path"] != REGISTERED_SOURCE.relative_to(ROOT).as_posix():
        raise RuntimeError("strict receipt does not point at the registered whole-module source")
    if strict["registered_source"]["sha256"] != source_hash:
        raise RuntimeError("registered source differs from strict receipt")
    if strict["registered_evidence"]["sha256"] != evidence_hash:
        raise RuntimeError("registered behavior evidence differs from strict receipt")
    domain = evidence.get("contract", {}).get("input_domain") or evidence.get("input_domain")
    limits = evidence.get("contract", {}).get("limits") or evidence.get("limits")
    if not domain:
        # Current evidence keeps the contract fields at its top level.
        domain = evidence.get("input_domain")
    if not limits:
        limits = evidence.get("limits", [])
    return {
        "status": strict["status"],
        "whole_module": strict["registered_source"].get("whole_module"),
        "source": pin(REGISTERED_SOURCE),
        "evidence": pin(EVIDENCE),
        "input_domain": domain,
        "limits": limits,
        "interpretation": (
            "Valid-input behavior is accepted for its finite recorded domain. "
            "That does not exclude malformed/overflow continuations or establish Punt as noreturn."
        ),
    }


def build_receipt() -> dict:
    source = CLIP_SOURCE.read_text(encoding="latin1")
    function_names = [
        "clip_SetWin", "f_1E57_0296", "clip_SubInclude", "f_1E57_08F5",
        "clip_SubExclude", "f_1E57_0C2D", "clip_Push", "clip_Pop",
    ]
    required = {
        "clip_SetWin": [r"for\s*\(size\s*=\s*8", r"_fmemcpy\(fd_50F6_3C14,\s*p,\s*size\)"],
        "f_1E57_0296": [r"for\s*\(size\s*=\s*8", r"_fmemcpy\(fd_50F6_3C14,\s*p,\s*size\)"],
        "clip_SubInclude": [r"\(n\s*=\s*p\s*-\s*buf\)\s*>=\s*256", r"Punt\(", r"_fmemcpy\(g_5AAC,.*\(n\s*\+\s*1\)\s*<<\s*3\)"],
        "f_1E57_08F5": [r"\(n\s*=\s*p\s*-\s*buf\)\s*>=\s*256", r"Punt\(", r"_fmemcpy\(g_5AAC,.*\(n\s*\+\s*1\)\s*<<\s*3\)"],
        "clip_SubExclude": [r"\(n\s*=\s*p\s*-\s*buf\)\s*>=\s*256", r"Punt\(", r"_fmemcpy\(g_5AAC,.*\(n\s*\+\s*1\)\s*<<\s*3\)"],
        "f_1E57_0C2D": [r"\(n\s*=\s*p\s*-\s*buf\)\s*>=\s*256", r"Punt\(", r"_fmemcpy\(g_5AAC,\s*buf,\s*\(n\s*\+\s*1\)\s*<<\s*3\)"],
        "clip_Push": [r"_fmemcpy\(node\s*\+\s*2,\s*g_5AAC,\s*size\)"],
        "clip_Pop": [r"_fmemcpy\(fd_50F6_3C14,\s*g_5AAC,\s*size\)"],
    }
    rows = []
    for name in function_names:
        body, first, last = function_body(source, name)
        missing = [pattern for pattern in required[name] if not re.search(pattern, body, re.S)]
        if missing:
            raise RuntimeError(f"source anchor changed in {name}: {missing}")
        row = {"function": name, "lines": [first, last],
               "verified_source_patterns": required[name]}
        overflow_pattern = {
            "clip_SubInclude": r'Punt\("CL074:Temp clip overflow in SubInclude"\)',
            "f_1E57_08F5": r'Punt\("CL074:Temp clip overflow in SubInclude"\)',
            "clip_SubExclude": r'Punt\("CL074:Temp clip overflow in SubExclude"\)',
            "f_1E57_0C2D": r'Punt\("CL174:Temp clip overflow in SubExclude"\)',
        }.get(name)
        if overflow_pattern:
            guard = re.search(overflow_pattern, body)
            copy = re.search(r"_fmemcpy\(", body)
            if not guard or not copy or guard.start() >= copy.start():
                raise RuntimeError(f"overflow guard/copy order changed in {name}")
            row["overflow_guard_precedes_copy"] = True
            row["guard_semantics"] = "calls Punt, then source control flow continues to the copy if Punt returns"
        rows.append(row)

    # The object map grounds segment/offset, not an inferred extent for the
    # 18-byte graphics candidate.
    symbols = json.loads(SYMBOLS.read_text(encoding="utf-8"))["data"]
    clip_buffer = symbols["fd_50F6_3C14"]
    owner = symbols["g_5AAC"]
    dgroup_base = 0x55B3 * 16
    far_bss_base = int(clip_buffer["seg"]) * 16
    far_buffer_linear = far_bss_base + int(clip_buffer["off"])
    first_candidate_linear = dgroup_base + 0x2100
    gap = first_candidate_linear - far_buffer_linear
    threshold_n = (gap + 7) // 8 - 1
    candidate_intersections = []
    for name, first, last in (("selector", 0x2100, 0x2107),
                              ("byte_residue_masks", 0x68AC, 0x68B3),
                              ("packed_parity_masks", 0x68B4, 0x68B5)):
        linear = dgroup_base + first
        distance = linear - far_buffer_linear
        n_at_first_byte = (distance + 7) // 8 - 1
        candidate_intersections.append({
            "family": name, "interval": f"DGROUP:{first:04X}..{last:04X}",
            "first_byte_linear": f"0x{linear:X}",
            "distance_from_clip_buffer": distance,
            "minimum_n_for_generated_copy": n_at_first_byte,
            "within_signed_16_bit_generated_count": n_at_first_byte <= 0x7FFF,
        })
    if (clip_buffer["seg"], clip_buffer["off"]) != (0x50F6, 0x3C14):
        raise RuntimeError("registered clip-buffer address changed")
    if (owner["seg"], owner["off"]) != (0x55B3, 0x5AAC):
        raise RuntimeError("registered g_5AAC address changed")

    pointer_assignments = []
    for number, line in enumerate(source.splitlines(), 1):
        if re.search(r"\bg_5AAC\s*=", line):
            pointer_assignments.append({"line": number, "text": line.strip()})
    if not pointer_assignments:
        raise RuntimeError("no g_5AAC assignments found")

    return {
        "schema": "simant-dos-graphics-formula-write-review-v1",
        "admission": False,
        "original_executable_read": False,
        "candidate": {
            "intervals": ["DGROUP:2100..2107", "DGROUP:68AC..68B3", "DGROUP:68B4..68B5"],
            "source_initializer_and_historical_TU": "unknown",
            "formula_probe_result": "functional formulas are separately test-owned; this receipt does not assign original ownership",
        },
        "pins": [pin(CLIP_SOURCE), pin(REGISTERED_SOURCE), pin(EVIDENCE),
                 pin(STRICT), pin(SYMBOLS)],
        "registered_window_contract": evidence_audit(),
        "clip_pointer_slot": {
            "symbol": "g_5AAC", "segment": f"{owner['seg']:04X}",
            "offset": f"{owner['off']:04X}", "source_semantics": "mutable near slot containing a far Rect-list pointer",
            "assignments_in_canonical_owner": pointer_assignments,
        },
        "variable_clip_writers": rows,
        "linear_reachability": {
            "far_buffer": f"{clip_buffer['seg']:04X}:{clip_buffer['off']:04X}",
            "far_buffer_linear": f"0x{far_buffer_linear:X}",
            "dgroup_base_linear": f"0x{dgroup_base:X}",
            "candidate_intersections": candidate_intersections,
            "earliest_candidate": "55B3:2100",
            "earliest_candidate_linear": f"0x{first_candidate_linear:X}",
            "earliest_distance_bytes": gap,
            "copy_length_expression": "(n + 1) << 3",
            "first_candidate_intersection_at_n": threshold_n,
            "reachability_status": "unknown for all three intervals: computed thresholds are representable, but no evidence proves the required lists reachable or excludes them on malformed/Punt-return paths",
        },
        "conclusion": (
            "The source-only closure is open. The exact blocker is a sentinel-list or generated-list "
            "copy into FAR_BSS:50F6:3C14 with a variable length; the registered valid-domain "
            "f_1E57_038E proof does not certify malformed overflow continuations. No debt byte, "
            "candidate value, owner, or extent is claimed."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
                        help="fresh receipt path below build/workers/dos_graphics_formula_write_review")
    args = parser.parse_args()
    out = args.out.resolve()
    allowed = (ROOT / "build/workers/dos_graphics_formula_write_review").resolve()
    if out != allowed and allowed not in out.parents:
        raise SystemExit("refusing output outside build/workers/dos_graphics_formula_write_review")
    if out.exists():
        raise SystemExit(f"refusing to overwrite existing receipt: {out}")
    report = build_receipt()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"receipt": str(out), "pins": len(report["pins"]),
                      "admission": report["admission"],
                      "clip_list_writer_closure": "OPEN"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
