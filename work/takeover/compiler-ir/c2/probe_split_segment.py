"""Compile and capture four focused split far-pointer controls.

Run from the repository root with:
    python work/takeover/compiler-ir/c2/probe_split_segment.py

It first confirms the /Fc split representation and removes normal compiler
scratch, then uses the research-only /B3 hook to retain C2 streams in ignored
build scratch. Persistent output contains source hashes and compact summaries,
not raw binaries.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
import compiler  # noqa: E402
import slots  # noqa: E402

FLAGS = ["/AL", "/Os", "/Og", "/Oe", "/Zi", "/Fc"]
CASES = [
    ("split-far-base", "split-far-base.c"),
    ("split-far-whitespace", "split-far-whitespace.c"),
    ("split-far-extra-int", "split-far-extra-int.c"),
    ("split-far-extra-long", "split-far-extra-long.c"),
]
CAPTURE_LABELS = {
    "split-far-base": "toy-split-far-base",
    "split-far-whitespace": "toy-split-far-whitespace",
    "split-far-extra-int": "toy-split-far-extra-int",
    "split-far-extra-long": "toy-split-far-extra-long",
}
CAPTURE_ROOT = ROOT / "build" / "workers" / "c2_observability" / "b3"
STREAM_NAMES = ("000352DB", "000352EX", "000352GS", "000352IN", "000352LS", "000352PR", "000352ST", "000352SY")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_case(label: str, filename: str) -> dict:
    source_path = OUT / "sources" / filename
    source = source_path.read_text(encoding="ascii")
    result = compiler.compile_c(source, "msc600ax", flags=FLAGS, keep=True)
    work = Path(result.workdir).resolve()
    try:
        if not result.ok:
            raise RuntimeError(f"{label}: compile failed: {result.log[-1200:]}")
        listing_path = next((p for p in work.iterdir() if p.suffix.upper() == ".COD"), None)
        if listing_path is None:
            raise RuntimeError(f"{label}: /Fc listing missing")
        listing_bytes = listing_path.read_bytes()
        listing = listing_bytes.decode("latin1")
        publics = re.findall(r"(?m)^([A-Za-z_][A-Za-z0-9_]*)\tPROC\b", listing)
        public = next((p for p in publics if p.lstrip("_").lower() == "use_text"), None)
        if public is None:
            raise RuntimeError(f"{label}: use_text PROC missing; found {publics}")
        parsed = slots.parse_listing(listing, public)
        start = listing.find(f"{public}\tPROC")
        end = listing.find(f"{public}\tENDP", start)
        body = listing[start:end if end >= 0 else len(listing)]
        focus = [line.rstrip() for line in body.splitlines()
                 if "text" in line.lower() or "hold" in line.lower()]
        code = [line.rstrip() for line in body.splitlines() if "\t*** " in line]
        segment_store = next((line for line in code
                              if "mov\tWORD PTR [bp-" in line and line.endswith(",dx")), None)
        segment_load = next((line for line in code if "mov\tes,WORD PTR [bp-" in line), None)
        def bp_disp(line):
            match = re.search(r"\[bp-([0-9a-f]+)\]", line or "", re.I)
            return -int(match.group(1), 16) if match else None
        calls = [i for i, line in enumerate(code) if "\tcall\t" in line]
        si_definition = next((i for i, line in enumerate(code) if "\tmov\tsi,ax" in line), None)
        si_use = next((i for i, line in enumerate(code) if "[si]" in line), None)
        segment_store_i = code.index(segment_store) if segment_store in code else None
        segment_load_i = code.index(segment_load) if segment_load in code else None
        split_evidence = {
            "offset_loaded_into_si_from_ax": si_definition is not None,
            "offset_used_via_si": si_use is not None,
            "segment_stored_from_dx_to_bp_home": segment_store is not None,
            "segment_reloaded_from_bp_home_to_es": segment_load is not None,
            "segment_home_bp_offset": bp_disp(segment_store),
            "segment_reload_bp_offset": bp_disp(segment_load),
            "far_call_instruction_indexes": calls,
            "si_definition_before_call_and_use_after_call": bool(
                si_definition is not None and si_use is not None and any(
                    si_definition < call_index < si_use for call_index in calls
                )
            ),
            "segment_store_before_call_and_reload_after_call": bool(
                segment_store_i is not None and segment_load_i is not None and any(
                    segment_store_i < call_index < segment_load_i for call_index in calls
                )
            ),
        }
        return {
            "case": label,
            "source": source_path.relative_to(ROOT).as_posix(),
            "source_sha256": sha(source_path.read_bytes()),
            "profile": "msc600ax",
            "flags_passed": FLAGS,
            "required_flags_appended_by_compile_c": ["/EM"],
            "listing_sha256": sha(listing_bytes),
            "listing_public": public,
            "slots": parsed["slots"],
            "registers": parsed["regs"],
            "bpname_map": {str(k): sorted(v) for k, v in parsed["bpnames"].items()},
            "text_mentions_in_proc": focus,
            "all_proc_instructions": code,
            "split_representation_check": split_evidence,
        }
    finally:
        scratch = (ROOT / "build" / "cc").resolve()
        if work.parent != scratch:
            raise RuntimeError(f"refusing cleanup outside build/cc: {work}")
        shutil.rmtree(work, ignore_errors=True)


def load_capture_module():
    path = OUT / "capture_b3.py"
    spec = importlib.util.spec_from_file_location("c2_capture_b3", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def capture_case(label: str, filename: str, capture_module) -> dict:
    source_path = OUT / "sources" / filename
    source = source_path.read_text(encoding="ascii")
    capture_label = CAPTURE_LABELS[label]
    summary_path = CAPTURE_ROOT / capture_label / "summary.json"
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if summary.get("source_sha256") != sha(source.encode("ascii")):
            raise RuntimeError(f"existing /B3 source hash differs for {capture_label}")
    else:
        capture_module.capture(capture_label, source, "/Zi")
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    streams = {}
    raw = {}
    for name in STREAM_NAMES:
        path = CAPTURE_ROOT / capture_label / "IR" / name
        data = path.read_bytes()
        raw[name] = data
        text_pos = []
        start = 0
        while True:
            pos = data.find(b"text", start)
            if pos < 0:
                break
            text_pos.append(pos)
            start = pos + 1
        hold_pos = []
        start = 0
        while True:
            pos = data.find(b"hold", start)
            if pos < 0:
                break
            hold_pos.append(pos)
            start = pos + 1
        windows = []
        for pos in text_pos:
            lo, hi = max(0, pos - 12), min(len(data), pos + 48)
            windows.append({"offset": pos, "window_start": lo, "hex": data[lo:hi].hex(" ")})
        streams[name] = {"size": len(data), "sha256": sha(data), "text_offsets": text_pos,
                         "hold_offsets": hold_pos, "text_windows": windows}
    if summary.get("source_sha256") != sha(source.encode("ascii")):
        raise RuntimeError(f"/B3 summary source hash mismatch for {capture_label}")
    return {"case": label, "capture_label": capture_label,
            "capture_source_sha256": summary["source_sha256"],
            "streams": streams, "_raw": raw}


def diff(a: bytes, b: bytes) -> dict:
    n = max(len(a), len(b))
    offsets = [i for i in range(n) if (a[i] if i < len(a) else None) != (b[i] if i < len(b) else None)]
    return {"sizes": [len(a), len(b)], "different_offsets": len(offsets),
            "first_differing_offsets": offsets[:48]}


def main() -> None:
    results = [compile_case(label, source) for label, source in CASES]
    cap_module = load_capture_module()
    cap_module.check_pins()
    captures = [capture_case(label, source, cap_module) for label, source in CASES]
    by_case = {row["case"]: row for row in captures}
    comparisons = {}
    for target in ("split-far-whitespace", "split-far-extra-int", "split-far-extra-long"):
        comparisons[f"split-far-base__vs__{target}"] = {
            name: diff(by_case["split-far-base"]["_raw"][name], by_case[target]["_raw"][name])
            for name in ("000352GS", "000352PR")
        }
    for capture in captures:
        del capture["_raw"]
    has_split = all(
        row["split_representation_check"]["offset_loaded_into_si_from_ax"]
        and row["split_representation_check"]["segment_stored_from_dx_to_bp_home"]
        and row["split_representation_check"]["si_definition_before_call_and_use_after_call"]
        and row["split_representation_check"]["segment_store_before_call_and_reload_after_call"]
        for row in results
    )
    output = {
        "method": "normal pinned MSC600AX /Fc listings plus C2 /B3 captures; tiny split-pointer controls differ only by whitespace or a volatile local live across the calls",
        "flags_passed": FLAGS,
        "required_flags_appended_by_compile_c": ["/EM"],
        "normal_listings": results,
        "b3_captures": captures,
        "base_vs_control_stream_diffs": comparisons,
        "all_controls_meet_split_requirement": has_split,
    }
    path = OUT / "split-far-listings.json"
    path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(path.relative_to(ROOT).as_posix())
    for case in results:
        print(f"{case['case']}: slots={case['slots']} registers={case['registers']}")
        print(f"  split={case['split_representation_check']}")
        for line in case["text_mentions_in_proc"]:
            print(f"  {line}")
    for name, rows in comparisons.items():
        print(f"{name}: GS={rows['000352GS']['different_offsets']} PR={rows['000352PR']['different_offsets']}")


if __name__ == "__main__":
    main()
