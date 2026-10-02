"""Tie named C2 PR records to MSC /Fc stack-home entries for four controls.

Run from the repository root with:
    python work/takeover/compiler-ir/c2/verify_homes.py

The script first confirms the four /B3 captures, then compiles the same sources
normally with /Fc, parses the resulting listings using tools/slots.py, and
compares signed 16-bit home offsets around the matching PR name records. Raw
compiler outputs remain in ignored build/ scratch and are removed after parse.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
import compiler  # noqa: E402
import slots  # noqa: E402

FLAGS = ["/AL", "/Os", "/Og", "/Oe", "/Zi", "/Fc"]
CAPTURE_SCRIPT = OUT / "capture_b3.py"
CAPTURE_ROOT = ROOT / "build" / "workers" / "c2_observability" / "b3"
CASES = [
    ("toy-far-pointer", "far-pointer.c", "keep_ptr", "saved"),
    ("toy-far-pointer-renamed", "far-pointer-renamed.c", "keep_ptr", "payload"),
    ("toy-long-home", "long-home.c", "keep_long", "saved"),
    ("toy-word-home", "word-home.c", "keep_word", "saved"),
]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def offsets(data: bytes, needle: bytes) -> list[int]:
    found = []
    start = 0
    while True:
        i = data.find(needle, start)
        if i < 0:
            return found
        found.append(i)
        start = i + 1


def main() -> None:
    cap = subprocess.run([sys.executable, str(CAPTURE_SCRIPT)], cwd=ROOT,
                         check=True, capture_output=True, text=True)
    print(cap.stdout.strip())
    results = []
    for label, source_name, func, local in CASES:
        source_path = OUT / "sources" / source_name
        source = source_path.read_text(encoding="ascii")
        result = compiler.compile_c(source, "msc600ax", flags=FLAGS, keep=True)
        work = Path(result.workdir).resolve()
        try:
            if not result.ok:
                raise RuntimeError(f"{label}: compile failed: {result.log[-1200:]}")
            listing_path = next((p for p in work.iterdir() if p.suffix.upper() == ".COD"), None)
            if listing_path is None:
                raise RuntimeError(f"{label}: /Fc did not produce a .COD listing in {work}")
            listing = listing_path.read_text(encoding="latin1")
            public_names = re.findall(r"(?m)^([A-Za-z_][A-Za-z0-9_]*)\tPROC\b", listing)
            public = next((name for name in public_names
                           if name.lstrip("_").lower() == func.lower()), None)
            if public is None:
                raise RuntimeError(f"{label}: no PROC for {func}; found {public_names}")
            parsed = slots.parse_listing(listing, public)
            if local not in parsed["slots"]:
                raise RuntimeError(f"{label}: /Fc local {local!r} not parsed; slots={parsed['slots']}")
            home = parsed["slots"][local]
            encoded = struct.pack("<h", home)
            pr_path = CAPTURE_ROOT / label / "IR" / "000352PR"
            pr = pr_path.read_bytes()
            name_bytes = local.encode("ascii")
            name_positions = offsets(pr, name_bytes)
            if len(name_positions) != 1:
                raise RuntimeError(f"{label}: expected one PR name {local!r}, found {name_positions}")
            name_pos = name_positions[0]
            record_start = max(0, name_pos - 8)
            record_end = min(len(pr), name_pos + len(name_bytes) + 33)
            nearby = [i for i in offsets(pr, encoded)
                      if record_start <= i and i + len(encoded) <= record_end]
            all_home_fields = offsets(pr, encoded)
            summary_path = CAPTURE_ROOT / label / "summary.json"
            capture_summary = json.loads(summary_path.read_text(encoding="utf-8"))
            pr_file = next(f for f in capture_summary["captured_files"] if f["name"] == "000352PR")
            results.append({
                "case": label,
                "source": source_path.relative_to(ROOT).as_posix(),
                "source_sha256": sha(source_path.read_bytes()),
                "profile": "msc600ax",
                "flags_passed": FLAGS,
                "required_flags_appended_by_compile_c": ["/EM"],
                "listing_public": public,
                "listing_local_home": home,
                "listing_home_signed16_le_hex": encoded.hex(" "),
                "listing_slots": parsed["slots"],
                "pr_file": pr_path.relative_to(ROOT).as_posix(),
                "pr_size": len(pr),
                "pr_sha256": sha(pr),
                "pr_summary_sha256": pr_file["sha256"],
                "pr_name": local,
                "pr_name_offset": name_pos,
                "pr_named_record_window_start": record_start,
                "pr_named_record_window_hex": pr[record_start:record_end].hex(" "),
                "full_signed16_home_occurrences_in_named_record_window": nearby,
                "full_signed16_home_occurrences_in_entire_pr": all_home_fields,
                "matched_near_name_record": bool(nearby),
            })
        finally:
            # compile_c owns this scratch directory; enforce that cleanup stays under build/cc.
            scratch = (ROOT / "build" / "cc").resolve()
            if work.parent != scratch:
                raise RuntimeError(f"refusing to remove compiler scratch outside build/cc: {work}")
            shutil.rmtree(work, ignore_errors=True)
    output = {
        "method": "normal MSC600AX compile with /Fc; tools/slots.py parse_listing; compare signed 16-bit local home against /B3 pre-C3 PR named record",
        "flags_passed": FLAGS,
        "compile_c_required_flags": ["/EM"],
        "cases": results,
    }
    result_path = OUT / "home-tieout.json"
    result_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(result_path.relative_to(ROOT).as_posix())
    for case in results:
        print(f"{case['case']}: {case['pr_name']} PR+{case['pr_name_offset']} "
              f"listing home={case['listing_local_home']} "
              f"({case['listing_home_signed16_le_hex']}); "
              f"near-record offsets={case['full_signed16_home_occurrences_in_named_record_window']}; "
              f"whole-PR offsets={case['full_signed16_home_occurrences_in_entire_pr']}")


if __name__ == "__main__":
    main()
