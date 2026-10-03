#!/usr/bin/env python3
"""Reproduce the fixed source-phase initialized-data alias adapter controls."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
ADAPTER_PATH = ROOT / "portable/whole_program/conversions/initialized_data_aliases_v1.py"
spec = importlib.util.spec_from_file_location("initialized_data_aliases_v1", ADAPTER_PATH)
adapter = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = adapter
spec.loader.exec_module(adapter)
sys.path.insert(0, str(ROOT / "portable/whole_program/conversions"))
import history as history_adapter
import startup_bundle as startup_adapter


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def main() -> int:
    out = ROOT / "build/workers/initialized_data_aliases_v7_20261003"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    plan = adapter._load_plan()
    composition_paths = [ROOT / "portable/whole_program/conversions/startup_bundle.py",
                         ROOT / "portable/whole_program/conversions/main_preflight.py",
                         ROOT / "portable/whole_program/conversions/history.py"]
    composition_before = {p.relative_to(ROOT).as_posix(): sha_bytes(p.read_bytes())
                          for p in composition_paths}
    outputs = {}
    total_tokens = 0
    for rel in plan["units"]:
        source = (ROOT / rel).read_text(encoding="utf-8")
        transformed, receipt = adapter.adapt(source, rel)
        if receipt is None:
            raise SystemExit(f"expected adapter for {rel}")
        if receipt["lexical_passes"] != 1:
            raise SystemExit(f"identifier rewrite was not a single pass: {rel}")
        total_tokens += sum(receipt["identifier_rewrites"].values())
        outputs[rel] = {"source_sha256": receipt["source_sha256"],
                        "output_sha256": receipt["output_sha256"],
                        "identifier_rewrites": receipt["identifier_rewrites"]}
        reviewed, reviewed_receipt = adapter.adapt_reviewed(source, rel)
        if reviewed != transformed or reviewed_receipt is None:
            raise SystemExit(f"reviewed-input API differs on original source: {rel}")

    # Positive source-shape assertions: owners preserve DOS byte images while
    # consumers use typed native array/interior expressions.
    data = adapter.adapt((ROOT / "src/data/d3D57.c").read_text(encoding="utf-8"),
                         "src/data/d3D57.c")[0]
    assert "int far fd_3D57_07CC[7] = { 1, 21, 7, 0, -1, 256, 770 };" in data
    assert "int far fd_3D57_0C1A[2] = { 40, 0 };" in data
    words_07cc = [1, 21, 7, 0, -1, 256, 770]
    image_07cc = b"".join((value & 0xffff).to_bytes(2, "little") for value in words_07cc)
    assert image_07cc == bytes([1, 0, 21, 0, 7, 0, 0, 0, 255, 255, 0, 1, 2, 3])
    image_0c1a = b"".join(value.to_bytes(2, "little") for value in [40, 0])
    assert image_0c1a == bytes([40, 0, 0, 0])
    assert "unsigned char far fd_3D57_07CC[14]" not in data
    assert "unsigned char far fd_3D57_0C1A[4]" not in data
    s05 = adapter.adapt((ROOT / "src/S05/m3663.c").read_text(encoding="utf-8"),
                        "src/S05/m3663.c")[0]
    assert "((int8_t *)ExpSubStates)[cur]" in s05
    m15f8 = adapter.adapt((ROOT / "src/root/m15F8.c").read_text(encoding="utf-8"),
                          "src/root/m15F8.c")[0]
    assert "extern int far fd_3D57_07CC[];" in m15f8
    assert "extern int far (fd_3D57_07CC[0])[];" not in m15f8
    assert "(fd_3D57_07CC + 1)[(fd_3D57_07CC[0])]" in m15f8
    s24 = adapter.adapt((ROOT / "src/S24/m39C7.c").read_text(encoding="utf-8"),
                        "src/S24/m39C7.c")[0]
    assert "((int far * far *)(fd_3D57_082A + 10))[graph]" in s24
    s09 = adapter.adapt((ROOT / "src/S09/m35F5.c").read_text(encoding="utf-8"),
                        "src/S09/m35F5.c")[0]
    assert "(void far *)(unsigned char far *)&fd_3D57_0C1A[1]" in s09

    # Negative controls: comments, string/character literals remain unchanged;
    # a source edit and a foreign module cannot silently receive the adapter.
    lexical_input = 'fd_3D57_07CC[0]; /* fd_3D57_07CC */ "fd_3D57_07CC" \'f\'; // fd_3D57_07CC\n'
    lexical_output, lexical_counts = adapter._lexical_replace(
        lexical_input, {"fd_3D57_07CC": "owner[0]"})
    assert lexical_output == 'owner[0][0]; /* fd_3D57_07CC */ "fd_3D57_07CC" \'f\'; // fd_3D57_07CC\n'
    assert lexical_counts == {"fd_3D57_07CC": 1}
    try:
        adapter.adapt((ROOT / "src/S05/m3663.c").read_text(encoding="utf-8") + "\n/* drift */\n",
                      "src/S05/m3663.c")
    except ValueError as exc:
        if "source changed" not in str(exc):
            raise
    else:
        raise SystemExit("mutated source was accepted")
    changed_plan = json.loads(adapter.PLAN_PATH.read_text(encoding="utf-8"))
    changed_plan["addresses"]["fd_3D57_0852"][1] += 1
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json",
                                     dir=ROOT / "build/workers", delete=False) as f:
        json.dump(changed_plan, f)
        bad_plan_path = Path(f.name)
    original_plan_path = adapter.PLAN_PATH
    try:
        adapter.PLAN_PATH = bad_plan_path
        try:
            adapter._load_plan()
        except ValueError as exc:
            if "offset" not in str(exc) and "address" not in str(exc):
                raise
        else:
            raise SystemExit("mutated layout anchor was accepted")
    finally:
        adapter.PLAN_PATH = original_plan_path
        bad_plan_path.unlink()
    untouched, no_receipt = adapter.adapt("int unrelated;\n", "src/unmapped.c")
    assert untouched == "int unrelated;\n" and no_receipt is None

    # Exercise the public post-overlay API in the same order used by the
    # producer: source-aware startup/history conversion first, alias views next.
    startup_sources, _ = startup_adapter.convert_startup_sources(
        (ROOT / "src/root/m15F8.c").read_text(encoding="utf-8"),
        (ROOT / "src/S15/m384C.c").read_text(encoding="utf-8"))
    composed_main, main_receipt = adapter.adapt_reviewed(
        startup_sources["src/root/m15F8.c"], "src/root/m15F8.c")
    history_source, _ = history_adapter.adapt(
        (ROOT / "src/S24/m39C7.c").read_text(encoding="utf-8"))
    composed_hist, hist_receipt = adapter.adapt_reviewed(history_source, "src/S24/m39C7.c")
    assert "(fd_3D57_07CC + 1)[(fd_3D57_07CC[0])]" in composed_main
    assert "((int far * far *)(fd_3D57_082A + 10))[graph]" in composed_hist
    assert main_receipt["input_sha256"] != main_receipt["source_sha256"]
    assert hist_receipt["input_sha256"] != hist_receipt["source_sha256"]
    try:
        adapter.adapt_reviewed(composed_main, "src/root/m15F8.c")
    except ValueError:
        pass
    else:
        raise SystemExit("already-adapted source was accepted a second time")

    out.mkdir(parents=True)
    composition_after = {p.relative_to(ROOT).as_posix(): sha_bytes(p.read_bytes())
                         for p in composition_paths}
    if composition_before != composition_after:
        raise SystemExit("startup/history adapter changed during composition probe")
    receipt = {
        "schema": "initialized-data-alias-source-probe-v3",
        "status": "PASS",
        "claim": "source-phase diagnostic adapter only; not behavior proof or historical acceptance",
        "plan_sha256": sha_bytes(adapter.PLAN_PATH.read_bytes()),
        "adapter_sha256": sha_bytes(ADAPTER_PATH.read_bytes()),
        "test_sha256": sha_bytes(Path(__file__).read_bytes()),
        "source_outputs": outputs,
        "composition_inputs": composition_before,
        "units_adapted": len(outputs),
        "identifier_tokens_rewritten": total_tokens,
        "positive_controls": ["exact initialized word values preserve complete owner byte images",
                              "signed byte view uses int8_t over canonical unsigned owner",
                              "07CE uses owner element offset one",
                              "0852 uses native pointer slot ten",
                              "0C1C points to word owner element one"],
        "negative_controls": ["altered source rejected", "mutated owner/address plan rejected", "foreign path unchanged",
                              "comments, literals, and character literals not rewritten"],
        "composition_controls": ["startup conversion then initialized aliases",
                                 "history lowering then initialized aliases"],
        "diagnostic_v6_report_sha256": "fdd38e6f72d16e2e001d43e29928e88e324637820127c97a4ded0e7bc7b5c505"
    }
    (out / "report.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
