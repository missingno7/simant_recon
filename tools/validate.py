"""Independent validation of everything accepted, plus the authoritative progress report.

    python tools/validate.py            # full: oracle, toolchain, fresh rebuild of every module, tests, report
    python tools/validate.py --no-tests
    python tools/validate.py --no-farbss-probe   # FAR_BSS declarations parsed instead of compiler-measured

Nothing cached is trusted: every module file is recompiled from src/ and every
claim is re-bound and compared.  Writes docs/progress.json and docs/progress.md.

Data accounting: modules with zero claims (data-only translation units ``data:FRAME`` and
code modules promoted with placements only) are listed as ``modules_data_only`` and never
counted as recovered code; their placements count in ``data_bytes_accepted``.  Placements
of different modules (and accepted runtime data) may not overlap; the fill between adjacent
placements that the next segment's SEGDEF alignment explains (paragraph fill between far
segments, the single 00 after an odd-length DGROUP segment before a word-aligned one) must be
zero and is counted as link fill (``data_link_fill_bytes``, of it ``data_link_fill_dgroup_bytes``);
``link_after`` positions are
checked; FAR_BSS (frame 50F6) is accounted by tools/farbss.py as linker zero fill; accepted
runtime DGROUP data segments are re-verified (tools/runtime.py verify_data).

Proof levels are reported separately (audit F-9): C bytes in complete TUs vs partial
modules, steered and layout-inferred claims, claims whose within-group relocation order is
pending, ASM bytes transcribed by a generator (source_origin), unmarked opaque data
initialisers (source_lint), runtime words derived from oracle operands, and the manifest
hash the report was computed from.  Every placement (file data, _BSS, runtime data) has one
owner and respects its SEGDEF alignment; ASM modules record source_origin; paths named in
asm_evidence exist; released claims that no module re-owned are listed.
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

# Tests that exercise the working DOS build or the SDL3 port.  They depend on builds on
# disk or on port contracts, so they are not part of the reconstruction gate.
UPPER_LAYER_TESTS = {
    "test_closure_graph", "test_dos_acceptance", "test_dos_diagnostic", "test_dos_linker",
    "test_instruction_word_sites", "test_native_acceptance", "test_native_register_returns",
    "test_native_word_expressions", "test_semantic_spans",
}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-tests", action="store_true")
    ap.add_argument("--upper-tests", action="store_true",
                    help="also run the tests of the working DOS build and the port (reported, not gating)")
    ap.add_argument("--no-farbss-probe", action="store_true",
                    help="skip the compile-only FAR_BSS declaration probes (tools/farbss.py probe_declarations)")
    a = ap.parse_args()
    failures = []
    import repository
    architecture = repository.audit(ROOT / 'layout/repository.json')
    print('repository architecture:', 'PASS' if architecture['passed'] else 'FAIL')
    failures.extend('architecture: ' + str(issue) for issue in architecture['issues'])

    r = subprocess.run([sys.executable, str(ROOT / "tools" / "oracle.py")], capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode:
        failures.append("oracle lock")

    # consistent snapshot: promotions write the source and then the manifest under the canonical
    # lock, so read both under it (quickly) and verify from memory afterwards
    from lockfile import CanonicalLock
    with CanonicalLock():
        man_bytes = modmod.MANIFEST.read_bytes()
        man = json.loads(man_bytes)
        snapshot = {k: (ROOT / m["source"]).read_bytes() for k, m in man["modules"].items()}
    import canonical
    program = canonical.load() if canonical.PROGRAM.exists() else None
    current_context_claims = []
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
    far_data_bytes = 0
    data_only_modules = []
    placed = []                  # (linear, size, owner, segment, far, alignment) of every exact file placement
    comdefs = defaultdict(list)  # C name -> [(bytes, module)] far communals of accepted objects
    link_after_seen = {}
    bss_placed = []              # (linear, size, owner, segment, False) of every _BSS placement
    acct = defaultdict(int)      # proof-level accounting (audit F-9)
    layout_modules, origin_unevidenced = [], []
    per_unit = defaultdict(int)
    listed = {str((ROOT / m["source"]).resolve()).lower() for m in man["modules"].values()}
    if program:
        listed |= {str((ROOT / m['source']).resolve()).lower() for m in program['modules']}
        listed.add(str(canonical.PROGRAM.resolve()).lower())
        canonical_payloads = {}
        for item in program['modules']:
            raw = (ROOT / item['source']).read_bytes()
            canonical_payloads[item['key']] = raw
            if sha(raw) != item['source_sha256']:
                failures.append(item['key'] + ': canonical inventory source pin differs')
            if item['key'] in man['modules'] and item['source_sha256'] != man['modules'][item['key']]['source_sha256']:
                failures.append(item['key'] + ': source authorities disagree')
        try:
            canonical.check_semantic_publication(program, canonical_payloads, program,
                                                 sha(canonical.PROGRAM.read_bytes()))
        except ValueError as error:
            failures.append('canonical semantic completeness: ' + str(error))
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
        item = next((item for item in program['modules'] if item['key'] == key), {}) if program else {}
        res = modmod.verify_module(text, m, m["claims"], man=man,
                                  code_references=item.get('owned_code_references'),
                                  data_frame_references=item.get('data_frame_references'))
        bad = [n for n, c in res["claims"].items() if not c["exact"]]
        dbad = [n for n, d in res.get("data", {}).items() if not d["exact"]]
        mreasons = list(res.get("module_reasons", [])) + modmod.link_after_reasons(
            man, key, m, {n: d.get("align") for n, d in res.get("data", {}).items()})
        # Extent failures can occur while every individual claim is exact. Preserve their
        # diagnostics so a rejected TU does not appear as the unhelpful "FAIL [] []".
        mreasons += (res.get("extent") or {}).get("reasons", [])
        # provenance (audit F-4): ASM modules record how their source was produced, and the probe
        # files their asm_evidence names exist
        mreasons += modmod.source_origin_reasons(m.get("source_origin"), m.get("lang", "c"))
        mreasons += modmod.evidence_path_reasons(m.get("asm_evidence"))
        if m.get("origin") and not m.get("origin_evidence"):
            origin_unevidenced.append(key)
        if "link_after" in m:
            # far and DGROUP link orders are separate sequences (FIRST exists in each)
            lk = (m["seg"] == modmod.match.DGROUP_SEG and modmod.is_data_module(m), m["link_after"])
            if lk in link_after_seen:
                mreasons.append(f"link_after {m['link_after'] or 'FIRST'} also claimed by {link_after_seen[lk]}")
            link_after_seen[lk] = key
        ok_mod = res["exact"] and not mreasons
        context_ok = False
        if m.get('canonical_admission'):
            context_errors = canonical.audit_context(key, res, m['canonical_admission'])
            failures += [key + ': ' + error for error in context_errors]
            context_ok = not context_errors and not mreasons
            current_context_claims += [c['name'] for c in m['claims']
                                       if not res['claims'][c['name']]['exact']]
        status = ('REVIEWED CANONICAL CONTEXT (historical differences retained)' if context_ok
                  else ("OK" + (" (data only)" if not m["claims"] else "")) if ok_mod
                  else f"FAIL {bad + dbad} {mreasons[:3]}")
        print(f"  {key:<10} {len(m['claims']):3d} claims  {status}")
        if not ok_mod and not context_ok:
            failures.append(f"{key}: {bad + dbad} {mreasons[:3]} {res.get('log', '')}")
        if not m["claims"]:
            data_only_modules.append(key)
        for c in res.get("communals", []):
            if c.get("kind") == "far":
                comdefs[c["name"][1:] if c["name"][:1] == "_" else c["name"]].append((c["length"], key))
        pending_order += sum(1 for c in res["claims"].values() if c.get("reloc_order") == "WITHIN_GROUP_PENDING")
        inplace_drafts += len(res.get("inplace_drafts", []))
        steered += sum(1 for c in m["claims"] if c.get("provenance") == "EXACT_STEERED")
        if res.get("extent"):
            (tu_order_proven if res["extent"].get("reloc_order") in ("EXACT", "GROUPED")
             else tu_order_pending).append(key)
        complete = bool(m.get("extent")) and res["exact"]
        transcribed = str(m.get("source_origin", "")).startswith(("asm-transcribed:", "generated:"))
        if m.get("layout_inferred"):
            layout_modules.append(key)
        acct["data_bytes_opaque_unmarked"] += res.get("opaque_unmarked_bytes", 0)
        for c in m["claims"]:
            claimed.append((c["unit"], c["seg"] * 16 + c["off"], c["size"], c["name"]))
            if not res['claims'][c['name']]['exact']:
                # Historical exact source authority is preserved through Git;
                # the rebuilt contribution is never counted as byte exact.
                continue
            if transcribed and c.get("kind") in ("ASM", modmod.DATA_KIND):
                acct["asm_transcribed_bytes"] += c["size"]
            if c.get("layout_inferred"):
                acct["claims_layout_inferred"] += 1
            if c.get("kind", "C") == "C":
                acct["exact_c_bytes_in_complete_tus" if complete else "exact_c_bytes_in_partial_modules"] += c["size"]
                if c.get("provenance") == "EXACT_STEERED":
                    acct["exact_c_bytes_steered"] += c["size"]
                if c.get("layout_inferred") or m.get("layout_inferred"):
                    acct["exact_c_bytes_layout_inferred"] += c["size"]
                if res["claims"].get(c["name"], {}).get("reloc_order") == "WITHIN_GROUP_PENDING":
                    acct["exact_c_bytes_within_group_pending"] += c["size"]
                exact_c += 1
                exact_c_bytes += c["size"]
            elif c["kind"] == "ASM":
                exact_asm += 1
                exact_asm_bytes += c["size"]
                # user policy: original assembly reproduced exactly is finished; ASM standing in
                # for code that was originally C is a matching workaround and reported apart
                acct["exact_asm_bytes_workaround" if c.get("asm_workaround") else "exact_asm_bytes_genuine"] += c["size"]
            elif c["kind"] == modmod.DATA_KIND:
                code_data_bytes += c["size"]
            per_unit[c["unit"]] += c["size"]
        for n, d in res.get("data", {}).items():
            if d.get("kind") == "BSS":
                bss_bytes += d["size"]
                if d.get("start") is not None:
                    bss_placed.append((d["start"], d["size"], key, n, False))
            elif d["exact"]:
                data_bytes += d["size"]
                if d.get("far"):
                    far_data_bytes += d["size"]
                if d.get("start") is not None:
                    placed.append((d["start"], d["size"], key, n, bool(d.get("far")), d.get("align")))
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
    # released claims (promote.py --release) must be re-owned by their true module (audit F-2)
    # (by address: a released function may have been renamed or re-framed since, e.g. f_277E_097A)
    owned_at = {(u, lin) for u, lin, _, _ in claimed}
    import symbols as symmod
    code_syms = symmod.load()["code"]
    released_unowned = []
    journal = ROOT / "evidence" / "promotions.jsonl"
    if journal.exists():
        for line in journal.read_text().splitlines():
            rec = json.loads(line) if line.strip() else {}
            for r in rec.get("released", []):
                s = code_syms.get(r["name"])
                at = (s["unit"], s["seg"] * 16 + s["off"]) if s else None
                if at not in owned_at and r["name"] not in released_unowned:
                    released_unowned.append(r["name"])
    if released_unowned:
        print(f"released and not re-owned: {released_unowned}")

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
        # The reconstruction gate runs only tests that depend on the current source and the
        # pinned tools.  Tests of the working DOS build and of the port read builds that
        # happen to be on disk and belong to the upper layers; they run on request and are
        # reported separately, never as part of the exactness verdicts.
        names = sorted(p.stem for p in (ROOT / "tests").glob("test_*.py"))
        groups = [("reconstruction tests", [n for n in names if n not in UPPER_LAYER_TESTS], True)]
        if a.upper_tests:
            groups.append(("upper-layer tests", [n for n in names if n in UPPER_LAYER_TESTS], False))
        for label, selected, gating in groups:
            t = subprocess.run([sys.executable, "-m", "unittest", "-q", *selected],
                               capture_output=True, text=True, cwd=ROOT / "tests")
            print(label + ": " + (t.stderr.strip().splitlines()[-1] if t.stderr.strip() else t.stdout.strip()))
            if t.returncode:
                print(t.stderr[-2000:])
                if gating:
                    failures.append(label)
                else:
                    print(label + " FAILED (reported only; the upper layers may be stale)")

    # ---- historical runtime: fresh re-binding of every accepted member -------------------
    runtime_bytes = 0
    runtime_members = 0
    acc = man.get("runtime", {}).get("members", [])
    located_spans, accepted_spans = set(), set()   # (linear, size) of located / accepted code segments
    import runtime as rtmod
    results, _derived = [], {}
    if acc or (ROOT / "evidence" / "toolchain" / "runtime-location.json").exists():
        results, _derived, conflicts, _ = rtmod.verify_all()
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
                                f"(re-prove runtime binding; reviewed publication belongs in tools/promote.py)")
            else:
                failures.append(f"runtime member {mrow['member']} no longer binds")
        for lib, info in man["runtime"]["libraries"].items():
            if hashlib.sha256(Path(info["path"]).read_bytes()).hexdigest() != info["sha256"]:
                failures.append(f"runtime library {lib} hash changed")
    print(f"historical runtime: {runtime_members} members, {runtime_bytes} bytes re-bound")
    # ---- runtime DGROUP data: re-verify every accepted data segment -------------------------
    runtime_data_bytes = 0
    acc_data = rtmod.accepted_data_segments(man) if acc else []
    if acc_data:
        rows = {(d["member"], d["segment"], d.get("linear")): d for d in rtmod.verify_data(results, _derived)}
        spans = set()               # common segments (PAD, EPAD) of several members are one area
        for d in acc_data:
            r = rows.get((d["member"], d["segment"], d["linear"]))
            if r is not None and r["exact"] and r["size"] == d["size"]:
                if (d["linear"], d["size"], d["segment"]) in spans:
                    continue
                spans.add((d["linear"], d["size"], d["segment"]))
                runtime_data_bytes += d["size"]
                placed.append((d["linear"], d["size"], f"runtime:{d['member']}", d["segment"], False, r.get("align")))
            else:
                failures.append(f"runtime data {d['member']} {d['segment']} no longer verifies "
                                f"({'; '.join((r or {}).get('reasons', ['not placed'])[:2])})")
    print(f"historical runtime data: {len(acc_data)} DGROUP segments, {runtime_data_bytes} bytes re-verified")

    # ---- data placements: single ownership, alignment link fill between placements --------
    # _BSS placements share DGROUP with file data and runtime data: one owner per byte (audit F-5)
    everything = sorted([p[:5] for p in placed] + bss_placed)
    bss_keys = {(a0, k0, s0) for a0, _, k0, s0, _ in bss_placed}
    for (a0, n0, k0, s0, _), (a1, n1, k1, s1, _) in zip(everything, everything[1:]):
        if a0 + n0 > a1 and ((a0, k0, s0) in bss_keys or (a1, k1, s1) in bss_keys):
            failures.append(f"overlapping placements {k0} {s0} {a0:05X}+{n0} and {k1} {s1} {a1:05X}+{n1}")
    link_fill, link_fill_dgroup, fill_failures = modmod.placement_link_fill(placed)
    failures += fill_failures
    import farbss
    c_sources = {k: snapshot[k].decode("latin1") for k, m in man["modules"].items() if m.get("lang", "c") == "c"}
    probed = None if a.no_farbss_probe else farbss.probe_declarations(man, c_sources)
    fb = farbss.account(c_sources, dict(comdefs), [(a, n) for a, n, *_ in placed], probed=probed)
    failures += [f"FAR_BSS: {f}" for f in fb["failures"]]
    far_bss_bytes = fb["size"] if fb["accounted"] else 0
    print(f"FAR_BSS {fb['size']} bytes zero fill, {fb['variables']} communals: sizes verified {fb['bytes_verified']}, "
          f"pinned {fb['bytes_pinned']}, consistent {fb['bytes_consistent']}, unverified {fb['bytes_unverified']}"
          + ("" if probed is None else f" (declarations of {probed['modules']} modules measured by the compiler"
             + (f"; {len(probed['failures'])} probe notes" if probed["failures"] else "") + ")")
          + (f"; {len(fb['warnings'])} size conflicts to review (tools/farbss.py)" if fb["warnings"] else ""))

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
    # frame 2CFB (0x2CFB0-0x2CFF0) is not the RTLink manager: crt0dat EMULATOR_TEXT (runtime),
    # the game's memory-hook jump table root:2CFB (0x2CFB2-0x2CFE4, 50 bytes) and paragraph fill;
    # The original RTLink manager starts at 2CFF0 (docs/exe-format.md).
    root_game_span += 0x2CFE4 - 0x2CFB2
    MANAGER_START = 0x2CFF0
    overlay_code = sum(len(s.data) for s in x.sections[:27])
    code_total = root_game_span + overlay_code
    s27 = len(x.sections[27].data)
    acc_members = {m["member"] for m in acc}
    derived_words = sum(1 for vals in _derived.values() for users in vals.values() for mem, _ in users
                        if mem in acc_members)
    progress = {
        "schema": "simant-progress-v1",
        "generated": dt.date.today().isoformat(),
        "oracle_sha256": x.sha256,
        "known_functions": len(table),
        "known_game_functions": len(game),
        "exact_c_functions": exact_c,
        "historical_exact_source_rebuilt_functions": sorted(current_context_claims),
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
        "rtlink_manager_bytes_unaccepted": len(x.image) - MANAGER_START
                                           - sum(1 for a in accepted_bytes_at if a >= MANAGER_START),
        "data_bytes_accepted": data_bytes,
        "far_data_bytes_accepted": far_data_bytes,
        "modules_data_only": sorted(data_only_modules),
        "historical_runtime_data_bytes_accepted": runtime_data_bytes,
        "data_link_fill_bytes": link_fill,
        "data_link_fill_dgroup_bytes": link_fill_dgroup,
        "far_bss_zero_fill_bytes": far_bss_bytes,
        "far_bss_sizes_verified_bytes": fb["bytes_verified"],
        "far_bss_sizes_pinned_bytes": fb["bytes_pinned"],
        "far_bss_sizes_consistent_bytes": fb["bytes_consistent"],
        "far_bss_sizes_unverified_bytes": fb["bytes_unverified"],
        "bss_bytes_placed": bss_bytes,
        "game_code_span_bytes": code_total,
        "unresolved_code_bytes": code_total - exact_c_bytes - exact_asm_bytes - code_data_bytes,
        # section 27 file bytes not yet owned: game data placements, runtime data, link fill and
        # the FAR_BSS zero fill (linker output) are owned
        "unresolved_data_bytes": s27 - data_bytes - runtime_data_bytes - link_fill - far_bss_bytes,
        "overlay_coverage": {s.name: {"bytes": len(s.data), "claimed": per_unit.get(s.name, 0)}
                             for s in x.sections[:27]},
        "root_claimed_bytes": per_unit.get("root", 0),
        "scaffold_functions": scaffolds,
        "exact_translation_units": exact_tus,
        "claims_within_group_order_pending": pending_order,
        "inplace_draft_functions": inplace_drafts,
        "claims_exact_steered": steered,
        # proof levels kept apart (audit F-9)
        "exact_c_bytes_in_complete_tus": acct["exact_c_bytes_in_complete_tus"],
        "exact_c_bytes_in_partial_modules": acct["exact_c_bytes_in_partial_modules"],
        "exact_c_bytes_steered": acct["exact_c_bytes_steered"],
        "exact_c_bytes_layout_inferred": acct["exact_c_bytes_layout_inferred"],
        "exact_c_bytes_within_group_pending": acct["exact_c_bytes_within_group_pending"],
        "claims_layout_inferred": acct["claims_layout_inferred"],
        "modules_layout_inferred": sorted(layout_modules),
        "asm_transcribed_bytes": acct["asm_transcribed_bytes"],
        "exact_asm_bytes_genuine": acct["exact_asm_bytes_genuine"],
        "exact_asm_bytes_workaround": acct["exact_asm_bytes_workaround"],
        "data_bytes_opaque_unmarked": acct["data_bytes_opaque_unmarked"],
        "runtime_oracle_derived_words": derived_words,
        "released_claims_unowned": released_unowned,
        "modules_origin_unevidenced": sorted(origin_unevidenced),
        "manifest_sha256": sha(man_bytes),
        "complete_tus_relocation_order_proven": len(tu_order_proven),
        "complete_tus_cross_function_order_pending": sorted(tu_order_pending),
        "codegen_rules_reproduced": rules_ok,
        "behavior_exact_confirmed_functions": len(program['semantics']) if program else 0,
        "historical_exact_source_rebuilt_function_count": len(current_context_claims),
        "canonical_translation_units": len(program['modules']) if program else 0,
        "canonical_storage_units": sum('storage_contract' in m for m in program['modules']) if program else 0,
        "canonical_program_sha256": sha(canonical.PROGRAM.read_bytes()) if program else None,
        "whole_executable": "FUNCTIONAL_SOURCE_BUILD (dos/build.py links the canonical source; the original image layout is not reproduced; see docs/dos-closure.md)",
        "validation": "PASS" if not failures else "FAIL",
        "failures": failures,
    }
    open_functions = len(program['semantics']) if program else 0
    own_units = sum('storage_contract' in m for m in program['modules']) if program else 0
    progress["verdicts"] = {
        "code": {
            "verdict": "EQUAL" if not open_functions and not failures else "NOT EQUAL",
            "detail": f"{exact_c + progress['exact_asm_functions']} of {progress['known_game_functions']} game "
                      f"functions exact; {open_functions} not exact",
            "proves": "each exact function's bytes, fixups and relocations, compiled from the current source "
                      "by the pinned tools in its whole module",
            "excludes": "where the linker places the module; functions listed as not exact"},
        "data": {
            "verdict": "NOT EQUAL" if own_units or progress["unresolved_data_bytes"]
                       or progress["far_bss_sizes_unverified_bytes"] else "EQUAL",
            "detail": f"{data_bytes} initialised bytes exact; {own_units} storage units of our own; "
                      f"uninitialised far data sizes unverified for {progress['far_bss_sizes_unverified_bytes']} of "
                      f"{far_bss_bytes} bytes; {progress['unresolved_data_bytes']} bytes unresolved",
            "proves": "the bytes and relocations of every accepted initialised data placement",
            "excludes": "owning file, type and size of data without an accepted placement; meaning of opaque bytes"},
        "layout": {
            "verdict": "NOT REPRODUCED",
            "detail": "the working DOS build orders data its own way; no link from this source reproduces "
                      "the original placement",
            "proves": "nothing yet beyond the per-module placements checked under code and data",
            "excludes": "segment order, communal placement, overlay structure, relocation table order"},
        "whole_executable": {
            "verdict": "NOT BUILT",
            "detail": f"the 1991 RTLink/Plus release is missing; its {progress['rtlink_manager_bytes_unaccepted']}-byte "
                      "overlay manager is not reproduced",
            "proves": "nothing",
            "excludes": "everything about the image as a file"},
        "not_rebuilt_from_source": [
            f"{runtime_members} members of the pinned Microsoft C 6.00 runtime libraries "
            f"({runtime_bytes} code bytes, {runtime_data_bytes} data bytes), linked from those libraries as the original was",
            "the linker's overlay manager and vector table"],
    }
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "progress.json").write_text(json.dumps(progress, indent=1) + "\n")
    md = ["# Progress (generated by tools/validate.py)", "",
          f"Validation: **{progress['validation']}** ({progress['generated']})", "",
          "| Measure | Value |", "|---|---:|"]
    for k in ("known_functions", "known_game_functions", "exact_c_functions", "exact_c_bytes",
              "historical_exact_source_rebuilt_function_count", "behavior_exact_confirmed_functions",
              "canonical_translation_units", "canonical_storage_units",
              "exact_asm_bytes", "exact_code_segment_data_bytes",
              "historical_runtime_bytes_accepted", "historical_runtime_members_accepted",
              "runtime_functions_known", "runtime_functions_owned", "owned_functions",
              "historical_runtime_bytes_located_unaccepted", "rtlink_manager_bytes_unaccepted",
              "data_bytes_accepted", "far_data_bytes_accepted", "historical_runtime_data_bytes_accepted",
              "data_link_fill_bytes", "data_link_fill_dgroup_bytes", "far_bss_zero_fill_bytes", "far_bss_sizes_verified_bytes",
              "far_bss_sizes_pinned_bytes",
              "far_bss_sizes_consistent_bytes", "far_bss_sizes_unverified_bytes",
              "game_code_span_bytes", "unresolved_code_bytes", "unresolved_data_bytes",
              "scaffold_functions", "exact_translation_units", "complete_tus_relocation_order_proven",
              "claims_within_group_order_pending", "inplace_draft_functions", "claims_exact_steered",
              "exact_c_bytes_in_complete_tus", "exact_c_bytes_in_partial_modules", "exact_c_bytes_steered",
              "exact_c_bytes_layout_inferred", "exact_c_bytes_within_group_pending", "claims_layout_inferred",
              "asm_transcribed_bytes", "exact_asm_bytes_genuine", "exact_asm_bytes_workaround",
              "data_bytes_opaque_unmarked", "runtime_oracle_derived_words"):
        md.append(f"| {k} | {progress[k]:,} |")
    md += ["", f"Manifest: `{progress['manifest_sha256']}`"]
    md += ["", "Complete TUs with cross-function relocation order pending (record breaks between "
           "functions differ; see docs/codegen-rules.md ZI-1): "
           + (", ".join(progress["complete_tus_cross_function_order_pending"]) or "none")]
    md += ["", "Modules with data placements only (never counted as recovered code): "
           + (", ".join(progress["modules_data_only"]) or "none")]
    md += ["", f"Whole executable: {progress['whole_executable']}", "",
           "Overlay coverage (claimed/bytes): " + ", ".join(
               f"{k} {v['claimed']}/{v['bytes']}" for k, v in progress["overlay_coverage"].items()), ""]
    (ROOT / "docs" / "progress.md").write_text("\n".join(md))
    print(f"exact C: {exact_c} functions, {exact_c_bytes} bytes; unresolved code {progress['unresolved_code_bytes']}"
          + (f"; code-segment data {code_data_bytes} bytes" if code_data_bytes else ""))
    print(f"data: {data_bytes} bytes accepted ({far_data_bytes} far), runtime data {runtime_data_bytes}, link fill "
          f"{link_fill} ({link_fill_dgroup} DGROUP), FAR_BSS {far_bss_bytes}; unresolved data {progress['unresolved_data_bytes']}; "
          f"data-only modules {len(data_only_modules)}")
    print("proof levels: C bytes in complete TUs {exact_c_bytes_in_complete_tus}, in partial modules "
          "{exact_c_bytes_in_partial_modules}; steered {exact_c_bytes_steered}, layout-inferred "
          "{exact_c_bytes_layout_inferred}, within-group pending {exact_c_bytes_within_group_pending}; "
          "ASM transcribed {asm_transcribed_bytes}; opaque data unmarked {data_bytes_opaque_unmarked}; "
          "runtime oracle-derived words {runtime_oracle_derived_words}".format(**progress))
    print(f"manifest sha256 {progress['manifest_sha256']}")
    print(f"verdicts against the original SIMANT.EXE (sha256 {progress['oracle_sha256']}):")
    for key in ("code", "data", "layout", "whole_executable"):
        v = progress["verdicts"][key]
        print(f"  {key.upper().replace('_', ' '):<17}{v['verdict']:<16}{v['detail']}")
        print(f"  {'':<17}proves: {v['proves']}")
        print(f"  {'':<17}excludes: {v['excludes']}")
    for item in progress["verdicts"]["not_rebuilt_from_source"]:
        print(f"  not rebuilt from source: {item}")
    if failures:
        print("VALIDATION FAILED:")
        for f in failures:
            print("  -", f)
        return 1
    print("VALIDATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
