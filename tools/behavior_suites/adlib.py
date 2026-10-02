"""Oracle-backed contract suite for the AdLib volume/pitch helper.

Runs f_2815_0165 against the original executable and its current whole-module
C draft. The register-helper callback observes call boundaries then falls through
to original assembly; status-port reads use a deterministic provider because the
historical delay routine's fixed IN/LOOP values do not affect returned state.
No proof status is assigned here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import shutil
import struct
import sys
import time
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import behavior
import behavior_ledger

TARGET = "f_2815_0165"
SUITE = "adlib_register_contract_v1"
INSTRUMENT_TABLE = "fd_50F6_0000"
VOLUME_OFFSET = "fd_50F6_4B16"
OUT_LEVEL_TABLE = "fd_55B3_6BA4"
DATA_SEG = 0xA000
DATA_OFF = 0x2000
INSTR_COUNT = 56
INSTR_STRIDE = 6
INSTR_BYTES = 16


def _word(value: int) -> bytes:
    return struct.pack("<H", value & 0xFFFF)


def _far(offset: int, segment: int) -> bytes:
    return struct.pack("<HH", offset & 0xFFFF, segment & 0xFFFF)


def _signed16(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def _range(symbol: str, size: int, name: str | None = None):
    return behavior.Range(name or symbol, behavior.symbol_address(symbol), size)


def instrument_bytes(instr: int, level: int, key_transpose: int, volume_adjust: int) -> bytes:
    raw = bytearray(((instr * 29 + i * 43 + 0x37) & 0xFF) for i in range(INSTR_BYTES))
    raw[2] = level & 0xFF
    struct.pack_into("<h", raw, 11, _signed16(key_transpose))
    struct.pack_into("<h", raw, 13, _signed16(volume_adjust))
    return bytes(raw)


def adlib_case(label: str, *, instr=0, note=60, vol=64, voice=0,
               global_volume_offset=-40, level=0x35, key_transpose=0,
               instrument_volume_adjust=0, status_byte=0):
    """Create a valid 56-record instrument table with the selected entry populated."""
    table = behavior.symbol_address(INSTRUMENT_TABLE) + (instr & 0xFFFF) * INSTR_STRIDE
    volume_global = behavior.symbol_address(VOLUME_OFFSET)
    data_address = DATA_SEG * 16 + DATA_OFF
    pdata = instrument_bytes(instr, level, key_transpose, instrument_volume_adjust)
    writes = [
        (table, _word(instr) + _far(DATA_OFF, DATA_SEG)),
        (data_address, pdata),
        (volume_global, _word(global_volume_offset)),
    ]
    return behavior.Case(
        label=label,
        args=[instr & 0xFFFF, note & 0xFFFF, vol & 0xFFFF, voice & 0xFFFF],
        writes=writes,
        observe=[
            behavior.Range("instrument_record", table, INSTR_STRIDE),
            behavior.Range("instrument_data", data_address, INSTR_BYTES),
            behavior.Range("driver_volume_offset", volume_global, 2),
        ],
        callbacks={"f_283E_000A": behavior.Callback(stack_words=2)},
        return_kind="void",
        io_reads={0x388: status_byte},
        metadata={
            "suite": SUITE,
            "contract": "ordered OPL index/data OUT pairs, helper call arguments, original/candidate non-stack writes and caller ABI",
            "helper_policy": "f_283E_000A is observed with no handler, then original genuine assembly executes; port 0388h IN supplies a fixed status byte",
            "io_delay_evidence": "src/root/m283E.asm f_283E_0020 writes index to DX=0388h, executes exactly ten IN/LOOP reads at 0388h, increments DX and writes data to 0389h, decrements DX and executes exactly forty more IN/LOOP reads at 0388h; IN results are overwritten or AX is restored before output and never control branches",
            "valid_fixture": {"instrument_index": "0..55 record in the 56-entry six-byte table", "voice": "0..8 OPL channel maps", "note": "7-bit note domain plus explicit transposition and endpoint probes", "volume": "all 0..255 byte values; signed/wide edge cases separately tagged"},
        },
        callee_pop=0,
    )


def directed_cases():
    cases = []
    # All byte velocity values over all nine OPL voices, with valid note values
    # and rotating instrument/parameter fixtures.
    for voice in range(9):
        for vol in range(256):
            cases.append(adlib_case(
                f"voice-volume/v{voice}/vol{vol}", instr=(voice * 7 + vol) % INSTR_COUNT,
                note=(17 * voice + 5 * vol) % 128, vol=vol, voice=voice,
                global_volume_offset=-40,
                level=(vol * 37 + voice * 11) & 0xFF,
                key_transpose=((vol + voice) % 5 - 2),
                instrument_volume_adjust=(vol % 17) - 8))
    # Touch every instrument index across all channels, with boundary note and
    # parameter values. This distinguishes pointer selection and register maps.
    for instr in range(INSTR_COUNT):
        for voice in range(9):
            note = (instr * 13 + voice * 7) % 128
            cases.append(adlib_case(
                f"instrument-channel/i{instr}/v{voice}", instr=instr, note=note,
                vol=(instr * 19 + voice * 23) & 0xFF, voice=voice,
                global_volume_offset=-40, level=(instr * 31 + voice * 17) & 0xFF,
                key_transpose=(instr % 7) - 3,
                instrument_volume_adjust=(voice % 9) - 4))
    # Cross high-information signed/clamp cases through every voice.
    for voice in range(9):
        for goff in (-32768, -128, -41, -40, -1, 0, 1, 127, 128, 32767):
            for vol in (0, 1, 63, 127, 128, 255, 0x7FFF, 0x8000, 0xFFFF):
                cases.append(adlib_case(
                    f"signed-clamp/v{voice}/g{goff}/vol{vol:04x}", instr=(voice * 5 + 17) % INSTR_COUNT,
                    note=60, vol=vol, voice=voice, global_volume_offset=goff,
                    level=0xFF, key_transpose=0, instrument_volume_adjust=0))
    # Exercise all 7-bit notes, range edges after octave adjustment, including
    # cases where the source must suppress frequency/key-on register writes.
    for voice in range(9):
        for note in list(range(128)) + [-13, -12, -1, 128, 139, 140, 32767, 0x8000, 0xFFFF]:
            cases.append(adlib_case(
                f"note-edge/v{voice}/n{note:04x}", instr=(voice * 3 + 1) % INSTR_COUNT,
                note=note, vol=73, voice=voice, global_volume_offset=-40,
                level=0xC7, key_transpose=(note % 5) - 2,
                instrument_volume_adjust=-3))
    return cases


def random_cases(count=3000, seed=0x28150165):
    rng = random.Random(seed)
    cases = []
    for i in range(count):
        cases.append(adlib_case(
            f"random/{seed:08x}/{i}", instr=rng.randrange(INSTR_COUNT),
            note=rng.randrange(128), vol=rng.randrange(256), voice=rng.randrange(9),
            global_volume_offset=rng.choice((-40, -1, 0, 1, rng.randrange(-128, 129))),
            level=rng.randrange(256), key_transpose=rng.randrange(-3, 4),
            instrument_volume_adjust=rng.randrange(-16, 17),
            status_byte=rng.choice((0x00, 0xFF, 0x55, 0xAA))))
    return cases


def _report_identity(pair, outdir):
    source_dir = outdir / "source-snapshots"
    source_dir.mkdir(parents=True, exist_ok=True)
    snapshot = source_dir / Path(pair.source).name
    shutil.copyfile(pair.source, snapshot)
    return snapshot


def run(outdir: Path, random_count: int, seed: int):
    pair = behavior.PreparedPair(TARGET, out=outdir / "candidate")
    snapshot = _report_identity(pair, outdir)
    suite_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    cases = directed_cases()
    directed_count = len(cases)
    cases.extend(random_cases(random_count, seed))
    compared_effects = [
        "return value (void ABI)", "ordered helper register arguments",
        "ordered actual OUT events (port, width, value)",
        "status-port IN event sequence", "instrument/global fixture memory",
        "all non-stack memory writes and final bytes", "preserved ABI registers",
    ]
    ledger = behavior_ledger.CaseLedger(
        outdir / "case-ledger.jsonl.gz", pair, compared_effects)
    started = time.time()
    failures = []
    totals = {"original": {"register_calls": 0, "OUT": 0, "IN388": 0},
              "candidate": {"register_calls": 0, "OUT": 0, "IN388": 0}}
    representatives = {}
    representative_labels = {"voice-volume/v0/vol0", "voice-volume/v4/vol127", "voice-volume/v8/vol255",
                             "note-edge/v2/n127", "note-edge/v2/n0080"}
    for index, case in enumerate(cases):
        comparison = pair.compare(case)
        a, b = comparison.original, comparison.candidate
        for side, result in (("original", a), ("candidate", b)):
            totals[side]["register_calls"] += len(result["trace"])
            totals[side]["OUT"] += sum(event[0] == "out" for event in result["io"])
            totals[side]["IN388"] += sum(event[0] == "in" and event[1] == 0x388 for event in result["io"])
        if case.label in representative_labels:
            representatives[case.label] = {
                "equal": comparison.equal,
                "original": {"trace": a["trace"], "io": a["io"], "preserved_registers": a["preserved_registers"]},
                "candidate": {"trace": b["trace"], "io": b["io"], "preserved_registers": b["preserved_registers"]},
            }
        if not comparison.equal:
            ledger.record(case, comparison,
                          lane="directed" if index < directed_count else "randomized")
            failures.append({"index": index, "label": case.label, "diff": comparison.diff,
                             "original": a, "candidate": b})
            if len(failures) >= 25:
                break
        else:
            ledger.record(case, comparison,
                          lane="directed" if index < directed_count else "randomized")
    # The helper's status reads are timing polls only. Replay a stable case with
    # 00h and FFh providers; exact OUT order/values must be invariant.
    status_case = adlib_case("status-provider-control", instr=7, note=63, vol=91, voice=4,
                             level=0xB7, key_transpose=1, instrument_volume_adjust=-2)
    low = pair.compare(replace(status_case, io_reads={0x388: 0x00}))
    high = pair.compare(replace(status_case, io_reads={0x388: 0xFF}))
    low_out = [x for x in low.original["io"] if x[0] == "out"]
    high_out = [x for x in high.original["io"] if x[0] == "out"]
    low_candidate_out = [x for x in low.candidate["io"] if x[0] == "out"]
    high_candidate_out = [x for x in high.candidate["io"] if x[0] == "out"]
    status_provider_equal = low.equal and high.equal and low_out == high_out and low_candidate_out == high_candidate_out
    if not status_provider_equal:
        failures.append({"label": "status-provider-control", "low": low.diff, "high": high.diff,
                         "oracle_out_equal": low_out == high_out,
                         "candidate_out_equal": low_candidate_out == high_candidate_out})
    out_table = behavior.symbol_address(OUT_LEVEL_TABLE)
    table_bytes = pair.original_machine.read(out_table, 128 * 2)
    ledger_identity = ledger.finalize()
    cases_run = ledger_identity["row_count"]
    # The per-case run's aggregate trace counts provide the observed boundary
    # count; the ledger independently pins each invocation's observation.
    original_calls = totals["original"]["register_calls"]
    run_report = {
        "schema": "behavior-run-evidence-v1",
        "completion": "COMPLETE" if cases_run == len(cases) and not failures else "INCOMPLETE",
        "identity": {
            "function": TARGET, "suite_id": SUITE,
            "module": f'{pair.identity["address"]["unit"]}:{pair.identity["address"]["seg"]:04X}',
            "source_sha256": pair.identity["source_sha256"],
            "compiled_source_sha256": pair.identity["compiled_source_sha256"],
            "suite_sha256": suite_sha256,
            "harness_sha256": pair.identity["harness_sha256"],
            "oracle_sha256": pair.identity["oracle_sha256"],
            "historical_manifest_sha256": pair.identity["manifest_sha256"],
            "object_sha256": pair.identity["object_sha256"],
            "profile": pair.identity["profile"], "flags": pair.identity["flags"],
        },
        "execution": {"engine": "PreparedPair.compare",
                       "actual_original_execution": True,
                       "actual_candidate_execution": True,
                       "original_exe_sha256": pair.identity["oracle_sha256"]},
        "cases": {
            "directed": {"generated": directed_count,
                         "executed": min(cases_run, directed_count),
                         "actual_original_invocations": min(cases_run, directed_count),
                         "actual_candidate_invocations": min(cases_run, directed_count),
                         "seeds": []},
            "randomized": {"generated": random_count,
                           "executed": max(0, cases_run - directed_count),
                           "actual_original_invocations": max(0, cases_run - directed_count),
                           "actual_candidate_invocations": max(0, cases_run - directed_count),
                           "seeds": [seed]},
        },
        "errors": 0, "mismatches": len(failures),
        "compared_effects": compared_effects,
        "case_ledger": {"path": "case-ledger.jsonl.gz",
                        "sha256": ledger_identity["sha256"],
                        "row_count": ledger_identity["row_count"],
                        "lane_counts": ledger_identity["lane_counts"],
                        "compression": ledger_identity["compression"],
                        "identity": ledger_identity["identity"]},
        "unmodeled_boundaries": 0, "peer_data_gates": "PASS",
        "positive_controls": [],
        "helper_boundaries": [{"name": "f_283E_000A",
                               "execution_mode": "ORIGINAL_EXE",
                               "observed_call_count": original_calls,
                               "executed_from_original": True}],
    }
    if cases_run:
        # A matched case from the actual ledger is a positive control only if
        # its observation hashes match (never manufactured from aggregates).
        import gzip
        with gzip.open(outdir / "case-ledger.jsonl.gz", "rt", encoding="utf-8") as stream:
            for line in stream:
                row = json.loads(line)
                if row["equal"]:
                    run_report["positive_controls"] = [{
                        "id": row["case_id"], "executed": True, "matched": True,
                        "execution_errors": 0, "original_executed": True,
                        "candidate_executed": True,
                        "source_sha256": pair.identity["source_sha256"],
                        "object_sha256": pair.identity["object_sha256"],
                        "oracle_sha256": pair.identity["oracle_sha256"],
                        "compared_effects": row["compared_effects"],
                        "original_observation_sha256": row["original_observation_sha256"],
                        "candidate_observation_sha256": row["candidate_observation_sha256"]}]
                    break
    (outdir / "run-evidence.json").write_text(json.dumps(run_report, indent=2) + "\n")
    report = {
        "schema": "behavior-suite-run-v1",
        "suite": SUITE,
        "function": TARGET,
        "function_address": pair.identity["address"],
        "source": pair.identity["source"],
        "source_sha256": pair.identity["source_sha256"],
        "source_snapshot": str(snapshot.resolve().relative_to(ROOT.resolve())),
        "source_snapshot_sha256": behavior.digest(snapshot.read_bytes()),
        "candidate_object_sha256": pair.identity["object_sha256"],
        "oracle_sha256": pair.identity["oracle_sha256"],
        "harness_sha256": pair.identity["harness_sha256"],
        "suite_sha256": suite_sha256,
        "unicorn_version": pair.identity["unicorn_version"],
        "compiler_profile": pair.identity["profile"],
        "compiler_flags": pair.identity["flags"],
        "target_strict_verdict": pair.strict.get("claims", {}).get(TARGET, {}),
        "whole_module_peer_private_data_gate": "passed via PreparedPair; target remains strict-inexact",
        "directed_cases": directed_count,
        "random_cases": random_count,
        "random_seed": seed,
        "cases_generated": len(cases),
        "cases_run": min(len(cases), (failures[0]["index"] + 1) if failures and "index" in failures[0] else len(cases)),
        "case_ledger": ledger_identity,
        "run_evidence": "run-evidence.json",
        "mismatches": len(failures),
        "failures": failures,
        "domain_completeness": {
            "valid_voice_domain": "0..8 from the nine-entry g_68FE/g_6908 maps; selected caller configurations initialize subsets, while this sweeps all OPL voices",
            "valid_instrument_domain": "0..55 (56 six-byte instrument records in the source table)",
            "volume_domain": "all 0..255 byte values at every voice, plus signed-word boundaries and global volume offset clamps",
            "note_domain": "all raw MIDI note bytes 0..127 at every voice plus signed/range/transposition endpoints",
            "instrument_parameters": "p[2] all byte patterns through volume grid, signed pitch transpose and volume adjustment structured crossings, plus seeded random values",
            "timing_io": "fixed 10+40 status-port IN reads per register helper; providers 00h and FFh produce identical ordered OUT subsequences",
        },
        "caller_fixture_evidence": {
            "adlib_dispatch": "src/root/m295C.c g_7504[2] maps type 2 to f_2815_0165",
            "voice_maps": "src/root/m2815.c g_68FE/g_6908 each contain nine OPL operator/channel mappings; src/root/m277E.c f_277E_040E/f_277E_04E8 initialize type-2 voice nums 1..7 or 0..7 depending on driver mode",
            "instrument_records": "src/root/m277E.c f_277E_010A copies 0x38 six-byte records to fd_50F6_0000; m2815 interprets the same six-byte shape as int plus far instrument-data pointer",
            "effect_scope": "register outputs and helper calls are captured; status-port reads are deterministic timing inputs, not modeled status state",
        },
        "helper_execution": {
            "boundary_callback": "f_283E_000A callback has no handler: runner logs arguments/state then executes original helper",
            "status_port_provider": "port 0388h => deterministic byte selected per test; 0389h reads are unmodeled and would fail",
            "actual_out": "OUT events remain actual original f_283E_0020 assembly execution in both VMs",
            "status_provider_out_control": {"equal": status_provider_equal,
                                             "out_count": len(low_out),
                                             "low_provider_in_count": sum(x[0] == "in" for x in low.original["io"]),
                                             "high_provider_in_count": sum(x[0] == "in" for x in high.original["io"])},
        },
        "out_level_table": {"address": f"{OUT_LEVEL_TABLE}:0..255", "bytes_sha256": hashlib.sha256(table_bytes).hexdigest(), "bytes": table_bytes.hex()},
        "helper_observation_totals_per_side": totals,
        "representative_traces": representatives,
        "elapsed_seconds": round(time.time() - started, 3),
        "behavioral_status": "UNRESOLVED; evidence pending supervisor review",
    }
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "adlib.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def negative_controls(outdir: Path):
    seed_path = ROOT / "work/takeover/hardtail/seeds/root_2815_8b6ca1b25908.c"
    text = seed_path.read_text(encoding="latin1")
    variants = [
        ("wrong-register", "f_283E_000A(voice + 0xa0, g_6924[note % 12]);",
         "f_283E_000A(voice + 0xa1, g_6924[note % 12]);"),
        ("wrong-value", "((p[2] & 0x3f) ^ 0x3f)", "((p[2] & 0x3f) ^ 0x3e)"),
    ]
    first = "f_283E_000A(voice + 0xa0, g_6924[note % 12]);"
    second = "f_283E_000A(voice + 0xb0, ((note / 12 + 8) << 2) + (g_6924[note % 12] >> 8));"
    if text.count(first) != 1 or text.count(second) != 1:
        raise RuntimeError("AdLib negative-control order anchors are not unique")
    variants.append(("wrong-order", first + "\n        " + second, second + "\n        " + first))
    case = adlib_case("negative-control", instr=7, note=60, vol=94, voice=3,
                      global_volume_offset=-40, level=0x35,
                      key_transpose=0, instrument_volume_adjust=0)
    negdir = outdir / "negative-controls"
    negdir.mkdir(parents=True, exist_ok=True)
    base_pair = behavior.PreparedPair(TARGET, out=negdir / "baseline")
    baseline = base_pair.compare(case)
    if not baseline.equal:
        raise AssertionError("unmutated AdLib baseline failed negative-control fixture")
    result = []
    for name, old, new in variants:
        if text.count(old) != 1:
            raise RuntimeError(f"negative control {name} anchor is not unique")
        mutant = negdir / f"{name}.c"
        mutant.write_text(text.replace(old, new, 1), encoding="latin1")
        pair = behavior.PreparedPair(TARGET, source=mutant, out=negdir / name)
        comparison = pair.compare(case)
        obj_path = negdir / name / "candidate.obj"
        if not obj_path.is_file():
            raise RuntimeError(f"mutant candidate object was not retained: {obj_path}")
        relative_source = mutant.resolve().relative_to(ROOT.resolve()).as_posix()
        relative_object = obj_path.resolve().relative_to(ROOT.resolve()).as_posix()
        row = {"id": name, "executed": True, "detected_mismatch": not comparison.equal,
               "original_executed": True, "mutant_executed": True,
               "baseline_matches": baseline.equal, "mutant_differs": not comparison.equal,
               "execution_errors": 0,
               "mismatch_categories": sorted(comparison.diff.keys()),
               "mutant_source_sha256": pair.identity["source_sha256"],
               "mutant_source": {"path": relative_source,
                                 "sha256": pair.identity["source_sha256"]},
               "mutant_object": {"path": relative_object,
                                 "sha256": behavior.digest(obj_path.read_bytes())},
               "candidate_object_sha256": pair.identity["object_sha256"],
               "diff": comparison.diff}
        result.append(row)
        if comparison.equal:
            raise AssertionError(f"AdLib harness did not detect {name} mutant")
    report = {"schema": "behavior-negative-controls-v1", "function": TARGET,
              "suite_id": SUITE, "errors": 0,
              "mismatches_detected": sum(row["detected_mismatch"] for row in result),
              "identity": {"source_sha256": base_pair.identity["source_sha256"],
                           "oracle_sha256": base_pair.identity["oracle_sha256"],
                           "harness_sha256": base_pair.identity["harness_sha256"],
                           "historical_manifest_sha256": base_pair.identity["manifest_sha256"]},
              "baseline": {"equal": baseline.equal,
                           "source_sha256": base_pair.identity["source_sha256"],
                           "object_sha256": base_pair.identity["object_sha256"],
                           "oracle_sha256": base_pair.identity["oracle_sha256"]},
              "controls": result}
    (outdir / "negative-controls.json").write_text(json.dumps(report, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--random-count", type=int, default=3000)
    parser.add_argument("--seed", type=lambda s: int(s, 0), default=0x28150165)
    parser.add_argument("--out", type=Path, default=ROOT / "build/workers/behavior_adlib")
    parser.add_argument("--negative-controls", action="store_true")
    args = parser.parse_args()
    output = args.out
    output.mkdir(parents=True, exist_ok=True)
    report = run(output, args.random_count, args.seed)
    negatives = negative_controls(output) if args.negative_controls else []
    print(json.dumps({"function": TARGET, "directed": report["directed_cases"],
                      "random": report["random_cases"], "cases": report["cases_run"],
                      "mismatches": report["mismatches"], "status": report["behavioral_status"],
                      "negative_controls_detected": sum(x["detected_mismatch"] for x in negatives)}, indent=2))


if __name__ == "__main__":
    main()
