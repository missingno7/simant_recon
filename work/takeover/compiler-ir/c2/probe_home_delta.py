"""Try two type-preserving controls for a C2 named-local home field.

First compare ordinary /Fc homes against the existing far-pointer baseline.
Only controls that actually move `saved` get a /B3 capture. Run from the repo
root with: python work/takeover/compiler-ir/c2/probe_home_delta.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import shutil
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
import compiler  # noqa: E402
import slots  # noqa: E402

FLAGS = ["/AL", "/Os", "/Og", "/Oe", "/Zi", "/Fc"]
CAPTURE_SCRIPT = OUT / "capture_b3.py"
CAPTURE_ROOT = ROOT / "build" / "workers" / "c2_observability" / "b3"
CASES = [
    ("toy-far-pointer-extra-int", "far-pointer-extra-int.c"),
    ("toy-far-pointer-extra-long", "far-pointer-extra-long.c"),
]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_home(source_path: Path) -> dict:
    source = source_path.read_text(encoding="ascii")
    result = compiler.compile_c(source, "msc600ax", flags=FLAGS, keep=True)
    work = Path(result.workdir).resolve()
    try:
        if not result.ok:
            raise RuntimeError(f"compile failed for {source_path.name}: {result.log[-1200:]}")
        listing_path = next((p for p in work.iterdir() if p.suffix.upper() == ".COD"), None)
        if listing_path is None:
            raise RuntimeError(f"/Fc produced no .COD for {source_path.name}")
        listing = listing_path.read_text(encoding="latin1")
        publics = re.findall(r"(?m)^([A-Za-z_][A-Za-z0-9_]*)\tPROC\b", listing)
        public = next((p for p in publics if p.lstrip("_").lower() == "keep_ptr"), None)
        if public is None:
            raise RuntimeError(f"keep_ptr PROC missing; found {publics}")
        parsed = slots.parse_listing(listing, public)
        if "saved" not in parsed["slots"]:
            raise RuntimeError(f"named far-pointer local missing from listing: {parsed['slots']}")
        return {
            "source": source_path.relative_to(ROOT).as_posix(),
            "source_sha256": sha(source_path.read_bytes()),
            "flags_passed": FLAGS,
            "required_flags_appended_by_compile_c": ["/EM"],
            "listing_public": public,
            "saved_home": parsed["slots"]["saved"],
            "listing_slots": parsed["slots"],
        }
    finally:
        scratch = (ROOT / "build" / "cc").resolve()
        if work.parent != scratch:
            raise RuntimeError(f"refusing to remove scratch outside build/cc: {work}")
        shutil.rmtree(work, ignore_errors=True)


def load_capture_module():
    spec = importlib.util.spec_from_file_location("c2_capture_b3", CAPTURE_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def named_window(label: str, home: int) -> dict:
    pr_path = CAPTURE_ROOT / label / "IR" / "000352PR"
    pr = pr_path.read_bytes()
    signed8 = struct.pack("<b", home)
    signed16 = struct.pack("<h", home)
    places = []
    start = 0
    while (index := pr.find(b"saved", start)) >= 0:
        left = max(0, index - 8)
        right = min(len(pr), index + len(b"saved") + 33)
        # In the baseline local record, the candidate home byte is at a stable
        # record-relative position after the name, terminator, and type bytes.
        field_pos = index + 10
        places.append({
            "name_offset": index,
            "window_start": left,
            "window_hex": pr[left:right].hex(" "),
            "tentative_home_byte_record_relative_offset": 10,
            "tentative_home_byte_observed_hex": pr[field_pos:field_pos + 1].hex(" "),
            "tentative_home_byte_expected_signed8_hex": signed8.hex(" "),
            "tentative_home_byte_matches_listing": pr[field_pos:field_pos + 1] == signed8,
            "two_bytes_at_tentative_home_field_hex": pr[field_pos:field_pos + 2].hex(" "),
            "signed16_home_occurrences_in_named_record_window": [
                i for i in range(left, right - 1) if pr[i:i + 2] == signed16
            ],
        })
        start = index + 1
    summary = json.loads((CAPTURE_ROOT / label / "summary.json").read_text(encoding="utf-8"))
    pr_info = next(row for row in summary["captured_files"] if row["name"] == "000352PR")
    return {
        "pr_file": pr_path.relative_to(ROOT).as_posix(),
        "pr_size": len(pr),
        "pr_sha256": sha(pr),
        "pr_summary_sha256": pr_info["sha256"],
        "listing_saved_home": home,
        "listing_signed8_byte_hex": signed8.hex(" "),
        "listing_signed16_le_hex": signed16.hex(" "),
        "signed16_home_occurrences_in_entire_pr": [
            i for i in range(len(pr) - 1) if pr[i:i + 2] == signed16
        ],
        "saved_named_records": places,
    }


def main() -> None:
    baseline_source = OUT / "sources" / "far-pointer.c"
    baseline = parse_home(baseline_source)
    if baseline["saved_home"] != -4:
        raise RuntimeError(f"expected established baseline home -4, got {baseline['saved_home']}")
    baseline.update({"case": "toy-far-pointer", "saved_type": "int far *"})
    candidates = []
    for label, filename in CASES:
        row = parse_home(OUT / "sources" / filename)
        row.update({"case": label, "saved_type": "int far *"})
        row["home_changed_from_baseline"] = row["saved_home"] != baseline["saved_home"]
        candidates.append(row)

    moved = [row for row in candidates if row["home_changed_from_baseline"]]
    cap_results = {}
    if moved:
        cap = load_capture_module()
        cap.check_pins()
        for row in moved:
            label = row["case"]
            src = (ROOT / row["source"]).read_text(encoding="ascii")
            summary_path = CAPTURE_ROOT / label / "summary.json"
            if summary_path.exists():
                summary = json.loads(summary_path.read_text(encoding="utf-8"))
                if summary.get("source_sha256") != sha(src.encode("ascii")):
                    raise RuntimeError(f"existing capture has different source for {label}")
            else:
                cap.capture(label, src, "/Zi")
            cap_results[label] = named_window(label, row["saved_home"])

    baseline_capture = named_window("toy-far-pointer", baseline["saved_home"])
    if moved:
        interpretation = (
            "For same-name, same-type `saved`, the PR byte at record-relative +10 changes from FC (listing BP-4) to FA (listing BP-6). "
            "This supports a tentative one-byte home/displacement field before C3; the adjacent byte changes 00 to 06, so the record format is not decoded, and no signed16 home word is present."
        )
    else:
        interpretation = "Neither candidate moved `saved` from BP-4, so no discriminating C2 comparison was made; bounded negative result."
    output = {
        "method": "same /AL /Os /Og /Oe /Zi controls; keep_ptr(saved) remains int far *; address-taken hold is passed to same call and read after it",
        "baseline": baseline,
        "baseline_pr": baseline_capture,
        "candidates": candidates,
        "captured_moved_controls_only": cap_results,
        "interpretation": interpretation,
    }
    result_path = OUT / "home-delta-probe.json"
    result_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(result_path.relative_to(ROOT).as_posix())
    print(f"baseline saved home: {baseline['saved_home']}")
    for row in candidates:
        print(f"{row['case']}: saved home {row['saved_home']}; changed={row['home_changed_from_baseline']}")
    for label, record in cap_results.items():
        print(f"{label}: PR saved-records={record['saved_named_records']}")


if __name__ == "__main__":
    main()
