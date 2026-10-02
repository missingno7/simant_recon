"""Tie existing S15 /B3 streams to normal /Fc local-home listings.

Run from the repository root with:
    python work/takeover/compiler-ir/c2/inspect_s15_context.py

The two S15 /B3 captures are existing context (fleet baseline and same-line
top-level extern). This script compiles those same sources normally with /Fc,
then records text-name PR/GS windows and raw differences. It does not decode
unnamed records or change either source.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
import compiler  # noqa: E402
import slots  # noqa: E402

FLAGS = ["/AL", "/Os", "/Og", "/Oe", "/Zi", "/Fc"]
CONTEXTS = [
    ("s15-fleet-base", ROOT / "work" / "takeover" / "fleet-lifetimes" / "fleet_s15" / "s15-base.c"),
    ("s15-same-line-top-extern", ROOT / "build" / "workers" / "compiler_ir" / "sources" / "s15-top-extern-plus-one.c"),
]
CAPTURE_ROOT = ROOT / "build" / "workers" / "c2_observability" / "b3"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def occurrences(data: bytes, needle: bytes) -> list[int]:
    out, start = [], 0
    while True:
        pos = data.find(needle, start)
        if pos < 0:
            return out
        out.append(pos)
        start = pos + 1


def runs(offsets: list[int]) -> list[list[int]]:
    if not offsets:
        return []
    result, start, end = [], offsets[0], offsets[0]
    for value in offsets[1:]:
        if value == end + 1:
            end = value
        else:
            result.append([start, end])
            start = end = value
    result.append([start, end])
    return result


def normal_listing(label: str, source_path: Path) -> dict:
    source_bytes = source_path.read_bytes()
    result = compiler.compile_c(source_bytes.decode("latin1"), "msc600ax", flags=FLAGS, keep=True)
    work = Path(result.workdir).resolve()
    try:
        if not result.ok:
            raise RuntimeError(f"{label}: normal compile failed: {result.log[-1200:]}")
        listing_path = next((p for p in work.iterdir() if p.suffix.upper() == ".COD"), None)
        if listing_path is None:
            raise RuntimeError(f"{label}: no .COD listing")
        listing_bytes = listing_path.read_bytes()
        listing = listing_bytes.decode("latin1")
        publics = re.findall(r"(?m)^([A-Za-z_][A-Za-z0-9_]*)\tPROC\b", listing)
        public = next((p for p in publics if p.lstrip("_").lower() == "o15_384c_0239"), None)
        if public is None:
            raise RuntimeError(f"{label}: target PROC missing; found {publics}")
        parsed = slots.parse_listing(listing, public)
        start = listing.find(f"{public}\tPROC")
        end = listing.find(f"{public}\tENDP", start)
        body = listing[start:end if end >= 0 else len(listing)]
        focus = [line.rstrip() for line in body.splitlines() if "text" in line.lower()]
        code = [line.rstrip() for line in body.splitlines() if "\t*** " in line]
        return {
            "source": source_path.relative_to(ROOT).as_posix(),
            "source_file_bytes_sha256": sha(source_bytes),
            "normalized_source_sha256": sha(source_bytes.replace(b"\r\n", b"\n").replace(b"\r", b"\n")),
            "normal_listing_sha256": sha(listing_bytes),
            "normal_flags_passed": FLAGS,
            "required_flags_appended_by_compile_c": ["/EM"],
            "public": public,
            "text_home": parsed["slots"].get("text"),
            "slots": parsed["slots"],
            "registers": parsed["regs"],
            "bpname_map": {str(k): sorted(v) for k, v in parsed["bpnames"].items()},
            "text_mentions_in_proc": focus,
            "all_proc_instructions": code,
        }
    finally:
        scratch = (ROOT / "build" / "cc").resolve()
        if work.parent != scratch:
            raise RuntimeError(f"refusing cleanup outside build/cc: {work}")
        shutil.rmtree(work, ignore_errors=True)


def capture_info(label: str) -> dict:
    case_dir = CAPTURE_ROOT / label
    summary = json.loads((case_dir / "summary.json").read_text(encoding="utf-8"))
    source = (case_dir / "UNIT.C").read_bytes()
    if sha(source.replace(b"\r\n", b"\n")) != summary["source_sha256"]:
        raise RuntimeError(f"{label}: captured source hash does not match summary")
    records = {}
    streams = {}
    for key in ("000352PR", "000352GS"):
        path = case_dir / "IR" / key
        data = path.read_bytes()
        text_pos = occurrences(data, b"text")
        windows = []
        for pos in text_pos:
            lo, hi = max(0, pos - 16), min(len(data), pos + 40)
            windows.append({"name_offset": pos, "window_start": lo, "hex": data[lo:hi].hex(" ")})
        records[key] = {"size": len(data), "sha256": sha(data), "text_offsets": text_pos,
                        "text_windows": windows}
        streams[key] = data
    return {
        "label": label,
        "capture_source_sha256": summary["source_sha256"],
        "capture_flags": summary["command"],
        "streams": records,
        "_raw": streams,
    }


def main() -> None:
    listings = {}
    captures = {}
    for label, source_path in CONTEXTS:
        listings[label] = normal_listing(label, source_path)
        captures[label] = capture_info(label)

    pair_diffs = {}
    a, b = captures[CONTEXTS[0][0]], captures[CONTEXTS[1][0]]
    for key in ("000352PR", "000352GS"):
        left, right = a["_raw"][key], b["_raw"][key]
        max_len = max(len(left), len(right))
        offsets_differing = [i for i in range(max_len)
                             if (left[i] if i < len(left) else None) !=
                             (right[i] if i < len(right) else None)]
        pair_diffs[key] = {
            "lengths": [len(left), len(right)],
            "differing_offsets_count": len(offsets_differing),
            "first_differing_offsets": offsets_differing[:32],
            "first_differing_offset_runs": runs(offsets_differing)[:16],
            "text_windows_present_in_both": bool(a["streams"][key]["text_windows"] and b["streams"][key]["text_windows"]),
            "text_windows_equal_when_present": bool(
                a["streams"][key]["text_windows"] and b["streams"][key]["text_windows"]
                and a["streams"][key]["text_windows"] == b["streams"][key]["text_windows"]
            ),
        }
    for label, source_path in CONTEXTS:
        if listings[label]["normalized_source_sha256"] != captures[label]["capture_source_sha256"]:
            raise RuntimeError(f"{label}: normal listing source does not match existing B3 capture source")
    for capture in captures.values():
        del capture["_raw"]
    output = {
        "method": "normal /Fc listing for the same two sources as existing /B3 captures; compare raw C2 PR and GS streams around `text` and between captures",
        "listings": listings,
        "existing_b3_captures": captures,
        "base_vs_extern_raw_diffs": pair_diffs,
        "limit": "PR/GS record grammar for unnamed fields is unavailable; equal/changed bytes cannot be assigned to the segment half from this comparison alone.",
    }
    path = OUT / "s15-segment-context.json"
    path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(path.relative_to(ROOT).as_posix())
    for label, row in listings.items():
        print(f"{label}: text home={row['text_home']} regs={row['registers']} slots={row['slots']}")
    for key, diff in pair_diffs.items():
        print(f"{key}: diff-count={diff['differing_offsets_count']} "
              f"text-windows-present={diff['text_windows_present_in_both']} "
              f"equal={diff['text_windows_equal_when_present']}")


if __name__ == "__main__":
    main()
