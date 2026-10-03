#!/usr/bin/env python3
"""Check source-backed lifts of C-private DGROUP words to native extern owners."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
ADAPTER_PATH = ROOT / "portable/whole_program/conversions/private_data_lifts_v1.py"
spec = importlib.util.spec_from_file_location("private_data_lifts_v1", ADAPTER_PATH)
adapter = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = adapter
spec.loader.exec_module(adapter)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    out = ROOT / "build/workers/private_data_lifts_v1_20261003"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    plan = adapter._load_plan()
    pin_paths = [ROOT / rel for rel in plan["pins"]]
    pin_paths += [ADAPTER_PATH, adapter.PLAN_PATH, Path(__file__), ROOT / "tools/exe.py"]
    before = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in pin_paths}

    # The archived DOS image is the final initialized-byte authority; each word
    # lies inside the exact private _DATA placement of its historical C owner.
    sys.path.insert(0, str(ROOT / "tools"))
    import exe  # noqa: E402
    original = exe.load()
    if original.sha256 != plan["oracle_sha256"]:
        raise SystemExit("DOS oracle identity does not match the pinned plan")
    owner_bytes = {}
    for owner in plan["owners"]:
        seg, off = owner["address"]
        got = original.read("S27", seg * 16 + off, owner["width"]).hex()
        if got != owner["image_le"]:
            raise SystemExit(f"DOS initialized word disagrees with private C owner {owner['owner']}: {got}")
        owner_bytes[owner["dos_symbol"]] = got

    transformed = {}
    for rel, spec_row in plan["units"].items():
        source = (ROOT / rel).read_text(encoding="utf-8")
        output, receipt = adapter.adapt(source, rel)
        if receipt is not None:
            transformed[rel] = {"source_sha256": receipt["source_sha256"],
                                "output_sha256": receipt["output_sha256"],
                                "rewrites": receipt["identifier_rewrites"]}
            reviewed, reviewed_receipt = adapter.adapt_reviewed(source, rel)
            if reviewed != output or reviewed_receipt is None:
                raise SystemExit(f"original-source and reviewed-input lanes differ: {rel}")
        elif spec_row.get("replace_lines") or spec_row.get("tokens"):
            raise SystemExit(f"expected a transformation in {rel}")
        transformed[rel] = transformed.get(rel, {"source_sha256": spec_row["source_sha256"],
                                                  "output_sha256": sha(output.encode()),
                                                  "rewrites": {}})

    expected_owner_outputs = {
        "src/S12/m384C.c": "int g_2996 = 0;",
        "src/S20/m39F1.c": "int g_610A = -1;",
    }
    for rel, definition in expected_owner_outputs.items():
        output = adapter.adapt((ROOT / rel).read_text(encoding="utf-8"), rel)[0]
        if definition not in output or "static " + definition in output:
            raise SystemExit(f"public lift lost owner initializer or retained static storage: {rel}")
    consumer_bindings = {
        "src/S04/m35F5.c": ("fd_55B3_2996", "g_2996"),
        "src/root/m15F8.c": ("fd_55B3_38A0", "g_38A0"),
        "src/S10/m35F5.c": ("fd_55B3_604C", "g_604C"),
        "src/S15/m384C.c": ("fd_55B3_610A", "g_610A"),
        "src/root/m00DF.c": ("fd_55B3_610A", "g_610A"),
    }
    for rel, (alias, owner) in consumer_bindings.items():
        output = adapter.adapt((ROOT / rel).read_text(encoding="utf-8"), rel)[0]
        if f"extern int {owner};" not in output or alias in output:
            raise SystemExit(f"consumer did not bind uniquely to native owner: {rel}")

    # Exactly one C definition per lifted name prevents a duplicate zero owner.
    definitions = {}
    all_source = list((ROOT / "src").rglob("*.c"))
    for owner in plan["owners"]:
        name = owner["owner"]
        pattern = re.compile(rf"(?m)^\s*(?:static\s+)?int\s+{re.escape(name)}\s*=")
        hits = [p.relative_to(ROOT).as_posix() for p in all_source
                if pattern.search(p.read_text(encoding="utf-8"))]
        if hits != [owner["source"]]:
            raise SystemExit(f"expected exactly one original C owner for {name}, got {hits}")
        definitions[name] = hits

    # Negative source/plan and lexical controls.
    try:
        adapter.adapt((ROOT / "src/S20/m39F1.c").read_text(encoding="utf-8") + "\n/* drift */\n",
                      "src/S20/m39F1.c")
    except ValueError as exc:
        if "source changed" not in str(exc):
            raise
    else:
        raise SystemExit("mutated source was accepted")
    lexical_input = 'fd_55B3_610A; /* fd_55B3_610A */ "fd_55B3_610A" \'x\';\n'
    lexical_output, counts = adapter._lexical_replace(lexical_input,
                                                       {"fd_55B3_610A": "g_610A"})
    if lexical_output != 'g_610A; /* fd_55B3_610A */ "fd_55B3_610A" \'x\';\n' or counts != {"fd_55B3_610A": 1}:
        raise SystemExit("lexical replacement changed a comment or literal")
    tampered = json.loads(adapter.PLAN_PATH.read_text(encoding="utf-8"))
    tampered["owners"][0]["placement_offset"] += 2
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json",
                                     dir=ROOT / "build/workers", delete=False) as f:
        json.dump(tampered, f)
        bad_plan = Path(f.name)
    original_plan_path = adapter.PLAN_PATH
    try:
        adapter.PLAN_PATH = bad_plan
        try:
            adapter._load_plan()
        except ValueError as exc:
            if "offset" not in str(exc):
                raise
        else:
            raise SystemExit("altered private placement was accepted")
    finally:
        adapter.PLAN_PATH = original_plan_path
        bad_plan.unlink()

    after = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in pin_paths}
    if before != after:
        raise SystemExit("pinned source/layout/oracle helper changed during probe")
    out.mkdir(parents=True)
    report = {
        "schema": "private-data-lift-probe-v1", "status": "PASS",
        "claim": "source ownership conversion diagnostic only; no historical or behavior-equivalence claim",
        "plan_sha256": sha(adapter.PLAN_PATH.read_bytes()),
        "adapter_sha256": sha(ADAPTER_PATH.read_bytes()),
        "test_sha256": sha(Path(__file__).read_bytes()),
        "pinned_inputs": before, "inputs_stable": True,
        "oracle_sha256": original.sha256,
        "owner_initial_bytes": owner_bytes,
        "owners": plan["owners"], "source_outputs": transformed,
        "owner_definitions": definitions,
        "positive_controls": ["each address lies in exact owner module _DATA placement",
                              "private static owners lifted without changing initializer",
                              "existing public C owners reused; no duplicate storage emitted",
                              "consumer extern/reference views renamed to owner identifiers",
                              "DOS initialized word bytes match all four source initializers"],
        "negative_controls": ["source drift rejected", "placement-offset drift rejected",
                              "comments and literals preserved"],
    }
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
