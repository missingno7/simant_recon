"""Independent validation of everything accepted, plus the authoritative progress report.

    python tools/validate.py            # full: oracle, toolchain, fresh rebuild of every module, tests, report
    python tools/validate.py --no-tests

Nothing cached is trusted: every module file is recompiled from src/ and every
claim is re-bound and compared.  Writes docs/progress.json and docs/progress.md.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compiler  # noqa: E402
import exe as exemod  # noqa: E402
import functions as fnmod  # noqa: E402
import modules as modmod  # noqa: E402

ROOT = exemod.ROOT


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-tests", action="store_true")
    a = ap.parse_args()
    failures = []

    r = subprocess.run([sys.executable, str(ROOT / "tools" / "oracle.py")], capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode:
        failures.append("oracle lock")

    # consistent snapshot: promotions write the source and then the manifest under the canonical
    # lock, so read both under it (quickly) and verify from memory afterwards
    from lockfile import CanonicalLock
    with CanonicalLock():
        man = modmod.load_manifest()
        snapshot = {k: (ROOT / m["source"]).read_bytes() for k, m in man["modules"].items()}
    for prof in sorted({m["profile"] for m in man["modules"].values()} | {"msc600", "msc600a", "masm510"}):
        try:
            compiler.verify_profile(prof)
        except Exception as e:  # noqa: BLE001
            failures.append(f"toolchain {prof}: {e}")
    print("toolchain hashes verified" if not any(f.startswith("toolchain") for f in failures) else "TOOLCHAIN FAIL")

    x = exemod.load()
    claimed = []
    exact_c = 0
    exact_c_bytes = 0
    data_bytes = 0
    scaffolds = 0
    exact_tus = 0
    pending_order = 0
    tu_order_proven, tu_order_pending = [], []
    inplace_drafts = 0
    steered = 0
    exact_asm = 0
    exact_asm_bytes = 0
    code_data_bytes = 0
    bss_bytes = 0
    per_unit = defaultdict(int)
    listed = {str((ROOT / m["source"]).resolve()).lower() for m in man["modules"].values()}
    for f in sorted((ROOT / "src").rglob("*")):
        if f.is_file() and str(f.resolve()).lower() not in listed:
            failures.append(f"{f.relative_to(ROOT)}: file in src/ not published by promote.py (drafts belong in build/workers/)")
    for key, m in man["modules"].items():
        path = ROOT / m["source"]
        text = snapshot[key].decode("latin1")
        # UNIT:SEG[@OFF] keys, origins and object ranges of multi-object frames (tools/modules.py)
        if modmod.module_key(m["unit"], m["seg"], m.get("origin")) != key:
            failures.append(f"{key}: key does not match unit/seg/origin of its record")
        lo, hi = modmod.object_range(man, m["unit"], m["seg"], m.get("origin"))
        if any(c["unit"] != m["unit"] or c["seg"] != m["seg"] or not lo <= c["off"] < hi
               or c["off"] + c["size"] > hi for c in m["claims"]):
            failures.append(f"{key}: claims outside the object's frame offsets {lo:04X}-{hi - 1:04X}")
        if sha(text.encode("latin1")) != m["source_sha256"]:
            failures.append(f"{key}: source hash differs from manifest (unpublished edit)")
        res = modmod.verify_module(text, m, m["claims"])
        bad = [n for n, c in res["claims"].items() if not c["exact"]]
        dbad = [n for n, d in res.get("data", {}).items() if not d["exact"]]
        status = "OK" if res["exact"] else f"FAIL {bad + dbad}"
        print(f"  {key:<10} {len(m['claims']):3d} claims  {status}")
        if not res["exact"]:
            failures.append(f"{key}: {bad + dbad} {res.get('log', '')}")
        pending_order += sum(1 for c in res["claims"].values() if c.get("reloc_order") == "WITHIN_GROUP_PENDING")
        inplace_drafts += len(res.get("inplace_drafts", []))
        steered += sum(1 for c in m["claims"] if c.get("provenance") == "EXACT_STEERED")
        if res.get("extent"):
            (tu_order_proven if res["extent"].get("reloc_order") in ("EXACT", "GROUPED")
             else tu_order_pending).append(key)
        for c in m["claims"]:
            claimed.append((c["unit"], c["seg"] * 16 + c["off"], c["size"], c["name"]))
            if c.get("kind", "C") == "C":
                exact_c += 1
                exact_c_bytes += c["size"]
            elif c["kind"] == "ASM":
                exact_asm += 1
                exact_asm_bytes += c["size"]
            elif c["kind"] == modmod.DATA_KIND:
                code_data_bytes += c["size"]
            per_unit[c["unit"]] += c["size"]
        for n, d in res.get("data", {}).items():
            if d.get("kind") == "BSS":
                bss_bytes += d["size"]
            elif d["exact"]:
                data_bytes += d["size"]
        scaffolds += len(res.get("scaffold", []))
        if m.get("extent") and res["exact"]:
            exact_tus += 1
    # accepted historical runtime segments are owned too: no game claim may overlap them
    for mrow in man.get("runtime", {}).get("members", []):
        for lin, size in [(mrow["linear"], mrow["size"])] + [(e["linear"], e["size"]) for e in mrow.get("extra_segments", [])]:
            claimed.append(("root", lin, size, f"runtime:{mrow['member']}@{lin:05X}"))
    claimed.sort()
    for (u1, a1, s1, n1), (u2, a2, s2, n2) in zip(claimed, claimed[1:]):
        if u1 == u2 and a1 + s1 > a2:
            failures.append(f"overlapping claims {n1} {n2}")

    import probe
    rules_ok = 0
    for spec in sorted((ROOT / "evidence" / "codegen").glob("*.json")):
        if spec.name.endswith(".result.json"):
            continue
        res = probe.run(json.loads(spec.read_text()))
        if res["all_checks_pass"]:
            rules_ok += 1
        else:
            failures.append(f"codegen rule {spec.stem} no longer reproduces")
    print(f"codegen rules reproduced: {rules_ok}")

    if not a.no_tests:
        t = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(ROOT / "tests"), "-q"],
                           capture_output=True, text=True, cwd=ROOT)
        print(t.stderr.strip().splitlines()[-1] if t.stderr.strip() else t.stdout.strip())
        if t.returncode:
            failures.append("unit tests")
            print(t.stderr[-2000:])

    # ---- historical runtime: fresh re-binding of every accepted member -------------------
    runtime_bytes = 0
    runtime_members = 0
    acc = man.get("runtime", {}).get("members", [])
    located_spans, accepted_spans = set(), set()   # (linear, size) of located / accepted code segments
    if acc or (ROOT / "evidence" / "toolchain" / "runtime-location.json").exists():
        import runtime as rtmod
        results, _, conflicts, _ = rtmod.verify_all()
        exact = {(r["member"], r["linear"]): r for r in results if r["exact"]}
        for r in results:
            located_spans |= {(r["linear"], r["size"])} | {(e["linear"], e["size"]) for e in r["extra_segments"]}
        for mrow in acc:
            r = exact.get((mrow["member"], mrow["linear"]))
            extra = mrow.get("extra_segments", [])
            if r is not None and r["size"] == mrow["size"] and r["extra_segments"] == extra:
                runtime_bytes += mrow["size"] + sum(e["size"] for e in extra)
                runtime_members += 1
                accepted_spans |= {(mrow["linear"], mrow["size"])} | {(e["linear"], e["size"]) for e in extra}
            elif r is not None:
                failures.append(f"runtime member {mrow['member']} binds with other segments than accepted "
                                f"(re-run tools/runtime.py accept)")
            else:
                failures.append(f"runtime member {mrow['member']} no longer binds")
        for lib, info in man["runtime"]["libraries"].items():
            if hashlib.sha256(Path(info["path"]).read_bytes()).hexdigest() != info["sha256"]:
                failures.append(f"runtime library {lib} hash changed")
    print(f"historical runtime: {runtime_members} members, {runtime_bytes} bytes re-bound")

    # ---- accounting -------------------------------------------------------------------
    table = fnmod.table()["functions"]
    game = [f for f in table if f["region"] == "game_or_library"]

    def span_bytes(spans):      # unique bytes covered (located members can share code)
        return len({a for lin, n in spans for a in range(lin, lin + n)})
    accepted_bytes_at = {a for lin, n in accepted_spans for a in range(lin, lin + n)}
    runtime_located_unaccepted = span_bytes(located_spans) - len(accepted_bytes_at)
    # function-table rows over the runtime text are owned when an accepted member contains them
    runtime_rows = [f for f in table if f["region"] == "msc_runtime_text"]
    runtime_rows_owned = sum(1 for f in runtime_rows if any(
        lin <= f["seg"] * 16 + f["off"] and f["seg"] * 16 + f["off"] + f["size"] <= lin + n for lin, n in accepted_spans))
    root_game_span = 0x29F4 * 16 + 0x1C - 0     # game code precedes the MSC runtime _TEXT
    overlay_code = sum(len(s.data) for s in x.sections[:27])
    code_total = root_game_span + overlay_code
    s27 = len(x.sections[27].data)
    progress = {
        "schema": "simant-progress-v1",
        "generated": dt.date.today().isoformat(),
        "oracle_sha256": x.sha256,
        "known_functions": len(table),
        "known_game_functions": len(game),
        "exact_c_functions": exact_c,
        "exact_c_bytes": exact_c_bytes,
        "exact_asm_functions": exact_asm,
        "exact_asm_bytes": exact_asm_bytes,
        "exact_code_segment_data_bytes": code_data_bytes,
        "historical_runtime_bytes_accepted": runtime_bytes,
        "historical_runtime_members_accepted": runtime_members,
        "historical_runtime_bytes_located_unaccepted": runtime_located_unaccepted,
        "runtime_functions_known": len(runtime_rows),
        "runtime_functions_owned": runtime_rows_owned,
        "owned_functions": exact_c + exact_asm + runtime_rows_owned,
        "rtlink_manager_bytes_unaccepted": len(x.image) - 0x2CFB * 16
                                           - sum(1 for a in accepted_bytes_at if a >= 0x2CFB * 16),
        "data_bytes_accepted": data_bytes,
        "bss_bytes_placed": bss_bytes,
        "game_code_span_bytes": code_total,
        "unresolved_code_bytes": code_total - exact_c_bytes - exact_asm_bytes - code_data_bytes,
        "unresolved_data_bytes": s27 - data_bytes,
        "overlay_coverage": {s.name: {"bytes": len(s.data), "claimed": per_unit.get(s.name, 0)}
                             for s in x.sections[:27]},
        "root_claimed_bytes": per_unit.get("root", 0),
        "scaffold_functions": scaffolds,
        "exact_translation_units": exact_tus,
        "claims_within_group_order_pending": pending_order,
        "inplace_draft_functions": inplace_drafts,
        "claims_exact_steered": steered,
        "complete_tus_relocation_order_proven": len(tu_order_proven),
        "complete_tus_cross_function_order_pending": sorted(tu_order_pending),
        "codegen_rules_reproduced": rules_ok,
        "whole_executable": "NOT_BUILT (no historical link yet; see docs/next-steps.md)",
        "validation": "PASS" if not failures else "FAIL",
        "failures": failures,
    }
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "progress.json").write_text(json.dumps(progress, indent=1) + "\n")
    md = ["# Progress (generated by tools/validate.py)", "",
          f"Validation: **{progress['validation']}** ({progress['generated']})", "",
          "| Measure | Value |", "|---|---:|"]
    for k in ("known_functions", "known_game_functions", "exact_c_functions", "exact_c_bytes",
              "exact_asm_bytes", "exact_code_segment_data_bytes",
              "historical_runtime_bytes_accepted", "historical_runtime_members_accepted",
              "runtime_functions_known", "runtime_functions_owned", "owned_functions",
              "historical_runtime_bytes_located_unaccepted", "rtlink_manager_bytes_unaccepted",
              "data_bytes_accepted", "game_code_span_bytes", "unresolved_code_bytes", "unresolved_data_bytes",
              "scaffold_functions", "exact_translation_units", "complete_tus_relocation_order_proven",
              "claims_within_group_order_pending", "inplace_draft_functions", "claims_exact_steered"):
        md.append(f"| {k} | {progress[k]:,} |")
    md += ["", "Complete TUs with cross-function relocation order pending (record breaks between "
           "functions differ; see docs/codegen-rules.md ZI-1): "
           + (", ".join(progress["complete_tus_cross_function_order_pending"]) or "none")]
    md += ["", f"Whole executable: {progress['whole_executable']}", "",
           "Overlay coverage (claimed/bytes): " + ", ".join(
               f"{k} {v['claimed']}/{v['bytes']}" for k, v in progress["overlay_coverage"].items()), ""]
    (ROOT / "docs" / "progress.md").write_text("\n".join(md))
    print(f"exact C: {exact_c} functions, {exact_c_bytes} bytes; unresolved code {progress['unresolved_code_bytes']}"
          + (f"; code-segment data {code_data_bytes} bytes" if code_data_bytes else ""))
    if failures:
        print("VALIDATION FAILED:")
        for f in failures:
            print("  -", f)
        return 1
    print("VALIDATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
