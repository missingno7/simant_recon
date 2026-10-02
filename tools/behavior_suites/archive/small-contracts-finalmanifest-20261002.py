"""Original-DOS differential contracts for FindIndex and small sound helpers.

This suite executes the hash-pinned DOS EXE and a separately compiled whole-module
candidate in the shared Unicorn runner. It records observable pointers/globals and
actual OUT instructions. It does not assign a proof category.
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
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import behavior
import behavior_ledger
import exe
import functions
import mismatch

SUITE = "small_contracts_v1"
FIND_DB = "fd_50F6_3958"
FIND_LOW = "fd_50F6_3956"
FIND_PTR = "fd_50F6_3952"
DB_RECORD_BYTES = 124
DB_COUNT_OFF = 0x54
DB_INDEX_OFF = 0x50
ARRAY_SEG = 0xA000
ARRAY_OFF = 0x1000


def _range(name, size):
    return behavior.Range(name, behavior.symbol_address(name), size)


def _word(v):
    return struct.pack("<H", v & 0xFFFF)


def _far(off, seg):
    return struct.pack("<HH", off & 0xFFFF, seg & 0xFFFF)


def _s16(value):
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def _findindex_machine_ordering_evidence():
    f = functions.get("FindIndex")
    code = exe.load().read(f["unit"], f["seg"] * 16 + f["off"], f["size"])
    rows = mismatch._decode(code, 0)
    offsets = (0x70, 0x74, 0x76, 0x79, 0x8A, 0x93, 0x97)
    return [{"offset": row["load_offset"], "bytes": row["bytes"], "instruction": row["instruction"]}
            for row in rows if row["load_offset"] in offsets]


def _record(entry):
    # IndexEntry: far data pointer, int id, byte kind, byte spare.
    data_ptr, ident, kind = entry
    return _far(data_ptr, 0xA000) + struct.pack("<HBB", ident & 0xFFFF, kind & 255, 0)


def find_case(label, entries, query_id, query_kind, db=0):
    """Entries follow unsigned byte kind, then signed 16-bit id ordering."""
    if list(entries) != sorted(entries, key=lambda e: (e[2] & 255, _s16(e[1]))):
        raise ValueError("FindIndex fixture must be sorted by unsigned kind and signed id")
    b = behavior
    rec = b.symbol_address(FIND_DB) + db * DB_RECORD_BYTES
    low, ptr = b.symbol_address(FIND_LOW), b.symbol_address(FIND_PTR)
    arr = ARRAY_SEG * 16 + ARRAY_OFF
    slots = list(entries) + [(0, 0x1357, 0xD6)]
    data = b"".join(_record(e) for e in slots)
    writes = [
        (rec + DB_INDEX_OFF, _far(ARRAY_OFF, ARRAY_SEG)),
        (rec + DB_COUNT_OFF, _word(len(entries))),
        (arr, data),
        (low, _word(0xBEEF)),
        (ptr, _far(0x4321, 0x9876)),
    ]
    return b.Case(
        label=label,
        args=[db, query_id, query_kind],
        writes=writes,
        observe=[_range(FIND_LOW, 2), _range(FIND_PTR, 4),
                 b.Range(f"db{db}_index_and_count", rec + DB_INDEX_OFF, 8)],
        return_kind="farptr",
        metadata={"suite": SUITE, "contract": "FindIndex lower-bound result, pointer, low cursor; array data-pointer fields are deliberately irrelevant", "oracle_helpers": "none", "ordering": "original +0x79 JG compares zero-extended unsigned-byte entry.kind to signed int argument; +0x97 JL compares signed int entry.id to signed int argument"},
    )


def _lower_bound(entries, ident, kind):
    wanted = (kind & 0xFFFF, ident & 0xFFFF)
    lo, hi = 0, len(entries)
    while lo < hi:
        mid = (lo + hi) // 2
        e = entries[mid]
        if (e[2], e[1]) < wanted:
            lo = mid + 1
        else:
            hi = mid
    return lo


def find_cases(random_count=30000, seed=0xF1D1):
    """Exhaustive small tables, cardinality/duplicate/signed boundaries, then random cases."""
    # Exhaust every exact-key, gap, boundary and empty-table query for all
    # subsets of a compact ordered key space.
    keyspace = [(ident, kind) for kind in range(2) for ident in range(4)]
    cases = []
    cases.append(find_case("empty/negative", [], 0, 0))
    for mask in range(1 << len(keyspace)):
        # Enumerate every subset of this eight-key domain and query every key,
        # all adjacent gaps, and values beyond both ends.
        entries = [(0x1000 + i, ident, kind)
                   for i, (ident, kind) in enumerate(keyspace) if mask & (1 << i)]
        # Each possible key in the compact domain, plus just-outside and values
        # on both sides of each sorted key.
        queries = {(ident, kind) for ident, kind in keyspace}
        queries.update({(-1, 0), (4, 1), (0, -1), (0, 2), (0xFFFF, 0xFFFF)})
        for ident, kind in sorted(queries):
            cases.append(find_case(f"exhaustive/m{mask:04x}/id{ident}/k{kind}", entries, ident, kind))
    # Search topology depends on table cardinality. Cover every insertion rank
    # and exact hit at each listed size, including both sides of 64 and
    # progressively larger binary-search trees through 256 records.
    cardinalities = (1, 2, 3, 7, 8, 15, 16, 31, 32, 63, 64, 65, 127, 128, 255, 256)
    for count in cardinalities:
        entries = [(0x2000 + i, i * 2, 3) for i in range(count)]
        probes = {(ident, 3) for ident in range(-1, count * 2 + 1)}
        probes.update({(-1, 3), (count * 2 + 1, 3), (0, 2), (0, 4)})
        for ident, kind in sorted(probes):
            cases.append(find_case(f"cardinality/{count}/id{ident}/k{kind}", entries, ident, kind))
    # Duplicate keys are legal in a sorted index. Verify the lower-bound result
    # selects the first duplicate and that both signed id and unsigned kind
    # promotion boundaries match the original comparisons.
    duplicate_rows = [(0x3100 + i, ident, 0x80) for i, ident in enumerate((0x8000, 0xFFFF, 0, 0x7FFF))]
    duplicate_rows += [(0x3200 + i, 0xFFFF, 0x80) for i in range(1, 4)]
    duplicate_rows.sort(key=lambda e: (e[2], _s16(e[1])))
    for ident in (0x8000, 0x8001, 0xFFFF, 0, 1, 0x7FFF):
        cases.append(find_case(f"signed-id/duplicate/id{ident:04x}", duplicate_rows, ident, 0x80))
    signed_kind_rows = [(0x4000 + i, ident, kind)
                        for i, (kind, ident) in enumerate(
                            (kind, ident) for kind in (0, 127, 128, 255)
                            for ident in (0x8000, 0xFFFF, 0, 0x7FFF))]
    signed_kind_rows.sort(key=lambda e: (e[2], _s16(e[1])))
    for kind in (0xFFFF, 0, 1, 127, 128, 255, 256, 0x7FFF, 0x8000):
        for ident in (0x8000, 0xFFFF, 0, 0x7FFF):
            cases.append(find_case(f"signed-kind/k{kind:04x}/id{ident:04x}", signed_kind_rows, ident, kind))
    rng = random.Random(seed)
    for i in range(random_count):
        count = rng.randrange(0, 65)
        keys = sorted(rng.sample(range(1 << 16), count))
        # Encode a mixed distribution with ties in kind and id domains while
        # keeping pairs sorted and unique, as a database index is expected to be.
        entries = []
        for key in keys:
            kind, ident = (key >> 11) & 255, key & 0x7FF
            entries.append((rng.randrange(1 << 16), ident, kind))
        # Independent random queries include hits, adjacent misses, and extremes.
        if entries and rng.randrange(2):
            ident, kind = rng.choice(entries)[1:]
            if rng.randrange(3) == 0:
                ident = (ident + rng.choice([-1, 1])) & 0xFFFF
        else:
            ident, kind = rng.randrange(1 << 16), rng.randrange(8)
        cases.append(find_case(f"random/{seed:08x}/{i}", entries, ident, kind, db=i % 4))
    return cases


def midi_case(label, off, byte0, byte1):
    b = behavior
    seg_global = b.symbol_address("g_8DFC")
    # _based(g_8DFC) uses this word as a segment base.
    base = 0xA000 * 16
    return b.Case(
        label=label, args=[off & 0xFFFF],
        writes=[(seg_global, _word(0xA000)),
                (base + (off & 0xFFFF), bytes([byte0 & 255])),
                (base + (((off + 1) & 0xFFFF)), bytes([byte1 & 255]))],
        observe=[], return_kind="s16",
        metadata={"suite": SUITE, "contract": "return the big-endian MIDI word at the song segment offset", "oracle_helpers": "none", "offset_representation": "16-bit based pointer offset"},
    )


def midi_cases(random_count=10000, seed=0x0138):
    cases = []
    # Exercise every byte value in both high and low return lanes, plus byte
    # order edge patterns at segment-wrap offsets. Random runs cover combinations.
    for value in range(256):
        off = (value * 251 + 0xFF00) & 0xFFFF
        cases.append(midi_case(f"high-lane/{value:02x}", off, value, 0xA5))
        cases.append(midi_case(f"low-lane/{value:02x}", off, 0x5A, value))
    for off in (0, 1, 0xFFFD, 0xFFFE, 0xFFFF):
        for a, z in ((0, 0), (0xFF, 0xFF), (0x12, 0x34), (0x80, 0x01), (0x01, 0x80)):
            cases.append(midi_case(f"boundary/{off:04x}/{a:02x}{z:02x}", off, a, z))
    # At offset FFFF, distinguish 16-bit based-pointer wrap to A000:0000 from
    # linear carry to B000:0000 by placing a different decoy byte there.
    wrap = midi_case("wrap-proof/ffff", 0xFFFF, 0x12, 0x34)
    wrap.writes.append((0xB0000, b"\x56"))
    wrap.metadata["wrap_probe"] = "A000:FFFF + 1 must read A000:0000; B000:0000 contains decoy 0x56"
    cases.append(wrap)
    rng = random.Random(seed)
    for i in range(random_count):
        off = rng.choice([0, 1, 0xFFFD, 0xFFFE, 0xFFFF, rng.randrange(65536)])
        cases.append(midi_case(f"random/{seed:08x}/{i}", off, rng.randrange(256), rng.randrange(256)))
    return cases


def tandy_case(label, ignored, note, vol, chan):
    b = behavior
    return behavior.Case(
        label=label, args=[ignored & 0xFFFF, note & 0xFFFF, vol & 0xFFFF, chan & 0xFFFF],
        observe=[], callbacks={"f_29F0_002A": b.Callback(stack_words=2)},
        return_kind="void", io_reads={},
        metadata={"suite": SUITE, "contract": "ordered actual OUT port/width/value sequence from original f_29F0_002A helper plus each helper-call argument/state snapshot", "helper_policy": "callback observes entry and falls through to execute original helper and actual OUT; no modeled writes", "expected_writes": 3, "caller_domain": {"note": "0..127 MIDI data byte", "velocity_argument": "0..255 tested; normal MIDI note-on velocity is 0..127", "channel": "0..2 from f_277E_034F type-3 channel initialization"}},
    )


def tandy_cases(random_count=20000, seed=0x29D6):
    cases = []
    # Caller audit: m295C routes the 7-bit MIDI note and velocity to the
    # selected voice; m277E_034F creates precisely three type-3 voices with
    # channel nums 0,1,2. Sweep all byte-sized velocity values for every note
    # and real Tandy channel (128*256*3 = 98,304 finite-domain cases).
    volumes = range(256)
    channels = range(3)
    for note in range(128):
        for vol in volumes:
            for chan in channels:
                ignored = (note * 257 + vol * 17 + chan) & 0xFFFF
                cases.append(tandy_case(f"grid/n{note}/v{vol}/c{chan}", ignored, note, vol, chan))
    # The song player adds a signed 16-bit header transpose to the 7-bit note
    # before dispatch. Probe octave-edge offsets around that normal MIDI range.
    for note in (-12, -1, 128, 139):
        for vol in (0, 1, 127, 128, 255):
            for chan in channels:
                cases.append(tandy_case(f"transpose-edge/n{note}/v{vol}/c{chan}", 0, note, vol, chan))
    rng = random.Random(seed)
    for i in range(random_count):
        # Include signed/overflow-sensitive but memory-safe notes only in the
        # documented note domain; wider vol/channel inputs probe C promotions.
        cases.append(tandy_case(f"random/{seed:08x}/{i}", rng.randrange(65536),
                                rng.randrange(128), rng.randrange(65536), rng.randrange(16)))
    return cases


def _run_one(pair, case):
    cmp = pair.compare(case)
    return cmp.equal, cmp.diff, cmp.original, cmp.candidate


def run_suite(name, count, seed, outdir):
    target = {"findindex": "FindIndex", "midi": "f_284A_0138", "tandy": "f_29D6_000A"}[name]
    pair = behavior.PreparedPair(target, out=outdir / name)
    source_snapshot_dir = outdir / "source-snapshots"
    source_snapshot_dir.mkdir(parents=True, exist_ok=True)
    source_snapshot = source_snapshot_dir / Path(pair.source).name
    shutil.copyfile(pair.source, source_snapshot)
    cases = {"findindex": find_cases, "midi": midi_cases, "tandy": tandy_cases}[name](count, seed)
    directed_count = len(cases) - count
    compared_effects = {
        "findindex": ["return pointer/result", "search cursor globals", "observed database table state",
                      "all non-stack writes and final bytes", "preserved caller registers and stack"],
        "midi": ["return word", "based-segment byte reads including offset wrap",
                 "all non-stack writes and final bytes", "preserved caller registers and stack"],
        "tandy": ["ordered actual OUT port/width/value sequence", "ordered helper arguments and call count",
                   "all non-stack writes and final bytes", "preserved caller registers and stack"],
    }[name]
    ledger = behavior_ledger.CaseLedger(outdir / f"{name}-case-ledger.jsonl.gz", pair, compared_effects)
    suite_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    started = time.time()
    failures = []
    callback_events = {"original": 0, "candidate": 0}
    modified_state_events = {"original": 0, "candidate": 0}
    io_events = {"original": 0, "candidate": 0}
    wrap_result = None
    selected_tandy_traces = {}
    selected_labels = {"grid/n0/v0/c0", "grid/n60/v255/c2", "grid/n127/v127/c1"}
    for i, case in enumerate(cases):
        comparison = pair.compare(case)
        equal, diff, original, candidate = comparison.equal, comparison.diff, comparison.original, comparison.candidate
        callback_events["original"] += len(original["trace"])
        callback_events["candidate"] += len(candidate["trace"])
        modified_state_events["original"] += sum(bool(t["modified_state_at_entry"]) for t in original["trace"])
        modified_state_events["candidate"] += sum(bool(t["modified_state_at_entry"]) for t in candidate["trace"])
        io_events["original"] += len(original["io"])
        io_events["candidate"] += len(candidate["io"])
        if case.label == "wrap-proof/ffff":
            wrap_result = {"original_return": original["return"], "candidate_return": candidate["return"],
                           "decoy_linear_byte": "0x56 at B000:0000", "expected_return": 0x1234,
                           "equal": equal}
        if name == "tandy" and case.label in selected_labels:
            selected_tandy_traces[case.label] = {
                "equal": equal,
                "original": {"trace": original["trace"], "io": original["io"],
                             "preserved_registers": original["preserved_registers"]},
                "candidate": {"trace": candidate["trace"], "io": candidate["io"],
                              "preserved_registers": candidate["preserved_registers"]},
            }
        if not equal:
            ledger.record(case, comparison, lane="directed" if i < directed_count else "randomized")
            failures.append({"index": i, "label": case.label, "diff": diff,
                             "original": original, "candidate": candidate})
            if len(failures) >= 25:
                break
        else:
            ledger.record(case, comparison, lane="directed" if i < directed_count else "randomized")
    ledger_pin = ledger.finalize()
    elapsed = time.time() - started
    cases_run = ledger_pin["row_count"]
    module = f'{pair.identity["address"]["unit"]}:{pair.identity["address"]["seg"]:04X}'
    run_evidence = {
        "schema": "behavior-run-evidence-v1",
        "completion": "COMPLETE" if cases_run == len(cases) and not failures else "INCOMPLETE",
        "identity": {"function": target, "suite_id": SUITE, "module": module,
                     "source_sha256": pair.identity["source_sha256"],
                     "compiled_source_sha256": pair.identity["compiled_source_sha256"],
                     "suite_sha256": suite_hash,
                     "harness_sha256": pair.identity["harness_sha256"],
                     "oracle_sha256": pair.identity["oracle_sha256"],
                     "historical_manifest_sha256": pair.identity["manifest_sha256"],
                     "object_sha256": pair.identity["object_sha256"],
                     "profile": pair.identity["profile"], "flags": pair.identity["flags"]},
        "execution": {"engine": "PreparedPair.compare", "actual_original_execution": True,
                      "actual_candidate_execution": True,
                      "original_exe_sha256": pair.identity["oracle_sha256"]},
        "cases": {
            "directed": {"generated": directed_count, "executed": min(cases_run, directed_count),
                         "actual_original_invocations": min(cases_run, directed_count),
                         "actual_candidate_invocations": min(cases_run, directed_count), "seeds": []},
            "randomized": {"generated": count, "executed": max(0, cases_run - directed_count),
                           "actual_original_invocations": max(0, cases_run - directed_count),
                           "actual_candidate_invocations": max(0, cases_run - directed_count),
                           "seeds": [seed]},
        },
        "errors": 0, "mismatches": len(failures), "compared_effects": compared_effects,
        "case_ledger": {"path": f"{name}-case-ledger.jsonl.gz", "sha256": ledger_pin["sha256"],
                        "row_count": ledger_pin["row_count"], "lane_counts": ledger_pin["lane_counts"],
                        "compression": ledger_pin["compression"], "identity": ledger_pin["identity"]},
        "unmodeled_boundaries": 0, "peer_data_gates": "PASS", "positive_controls": [],
        "helper_boundaries": ([{"name": "f_29F0_002A", "execution_mode": "ORIGINAL_EXE",
                                 "observed_call_count": callback_events["original"],
                                 "executed_from_original": True}] if name == "tandy" else []),
    }
    if cases_run:
        import gzip
        with gzip.open(outdir / f"{name}-case-ledger.jsonl.gz", "rt", encoding="utf-8") as stream:
            for line in stream:
                row = json.loads(line)
                if row["equal"]:
                    run_evidence["positive_controls"] = [{
                        "id": row["case_id"], "executed": True, "matched": True,
                        "execution_errors": 0, "original_executed": True, "candidate_executed": True,
                        "source_sha256": pair.identity["source_sha256"],
                        "object_sha256": pair.identity["object_sha256"],
                        "oracle_sha256": pair.identity["oracle_sha256"],
                        "compared_effects": row["compared_effects"],
                        "original_observation_sha256": row["original_observation_sha256"],
                        "candidate_observation_sha256": row["candidate_observation_sha256"]}]
                    break
    (outdir / f"{name}-run-evidence.json").write_text(json.dumps(run_evidence, indent=2) + "\n")
    result = {
        "schema": "behavior-suite-run-v1", "suite": SUITE, "contract": name,
        "function": target, "function_address": pair.identity["address"],
        "source": pair.identity["source"], "source_sha256": pair.identity["source_sha256"],
        "source_snapshot": str(source_snapshot.resolve().relative_to(ROOT.resolve())),
        "source_snapshot_sha256": behavior.digest(source_snapshot.read_bytes()),
        "suite_sha256": suite_hash,
        "compiled_source_sha256": pair.identity["compiled_source_sha256"],
        "object_sha256": pair.identity["object_sha256"], "oracle_sha256": pair.identity["oracle_sha256"],
        "harness_sha256": pair.identity["harness_sha256"], "unicorn_version": pair.identity["unicorn_version"],
        "profile": pair.identity["profile"], "flags": pair.identity["flags"],
        "candidate_strict": pair.strict.get("claims", {}).get(target, {}),
        "module_peers_and_data": "passed PreparedPair strict whole-module peer/private-data gates",
        "cases_generated": len(cases), "cases_run": cases_run,
        "case_ledger": ledger_pin,
        "run_evidence": f"{name}-run-evidence.json",
        "directed_cases": directed_count,
        "random_cases": count,
        "domain_completeness": {
            "findindex": {"finite_exhaustion": "all 256 subsets of 8 small keys queried at every domain key and endpoints; duplicate keys; signed id values 0x8000/0xFFFF/0/0x7FFF; kind values 0/127/128/255 queried at signed-int boundaries", "cardinality_exhaustion": "every exact key and every inter-key insertion rank at each table size 1,2,3,7,8,15,16,31,32,63,64,65,127,128,255,256", "random": "seeded 0..64-entry tables and queries"},
            "midi": {"finite_exhaustion": "all 256 byte values in each return lane; five offset boundaries; explicit A000:FFFF wrap distinguished from B000:0000 decoy", "random": "seeded random offsets and byte pairs"},
            "tandy": {"finite_exhaustion": "all 128 note values x all 256 byte velocity values x actual channels 0,1,2 (98,304 cases), plus transposed-note edges -12,-1,128,139 at volume boundaries", "random": "seeded wide-volume/channel ABI controls with note in 0..127"},
        }[name],
        "abi_checks": "shared Machine enforces preserved SI/DI/BP/SS/DS and far-callee stack cleanup independently for original and candidate; Tandy records each helper boundary and modified non-stack state",
        "boundary_observations": {"helper_calls": callback_events, "calls_with_modified_nonstack_state": modified_state_events, "actual_io_instructions": io_events, "expected_tandy_calls_per_machine": 3 * len(cases) if name == "tandy" else None},
        "midi_segment_wrap_probe": wrap_result if name == "midi" else None,
        "findindex_original_key_comparison": _findindex_machine_ordering_evidence() if name == "findindex" else None,
        "tandy_representative_call_traces": selected_tandy_traces if name == "tandy" else None,
        "tandy_caller_domain_evidence": ({
            "dispatch": "src/root/m295C.c: g_7504[3] selects f_29D6_000A; f_295C_01EC dispatches (dev,note,vel,num) through that table",
            "note": "src/root/m284A.c: f_284A_0537 reads the MIDI note byte and f_284A_04C9 adds 16-bit g_7576; suite exhausts raw 0..127 notes and probes transposed edges -12,-1,128,139",
            "velocity": "src/root/m284A.c: velocity is an unsigned MIDI data byte and is scaled by g_7570; src/root/m295C.c: f_295C_01EC scales unsigned velocity again by g_7502 before dispatch; suite exhausts all callee byte values 0..255 and samples wider values",
            "channel": "src/root/m277E.c: f_277E_034F loops i=0;i<3, assigning type=3 and num=i; suite exhausts 0,1,2",
        } if name == "tandy" else None),
        "mismatches": len(failures), "failures": failures,
        "seed": seed, "elapsed_seconds": round(elapsed, 3),
        "behavioral_status": "UNRESOLVED; evidence pending supervisor contract review",
    }
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f"{name}.json"
    path.write_text(json.dumps(result, indent=2) + "\n")
    return result


def negative_controls(outdir):
    """Scratch whole-module mutants demonstrate return/write-order sensitivity."""
    seed_dir = ROOT / "work/takeover/hardtail/seeds"
    specs = [
        ("FindIndex", "root_1986_1af5252fe844.c", "findindex", "return fd_50F6_3952;", "return 0L;", 
         find_case("negative/findindex-hit", [(0x1234, 7, 2)], 7, 2)),
        ("f_284A_0138", "root_284A_5d328bf943dd.c", "midi", "return SONG(off) << 8 | SONG(off + 1);", "return SONG(off + 1) << 8 | SONG(off);",
         midi_case("negative/midi-byte-order", 0x1234, 0x12, 0x34)),
        ("f_29D6_000A", "root_29D6_55476efe4ad6.c", "tandy", "f_29F0_002A(0x205, (f & 0xf) + ((char)chan + 0x80));\n    f_29F0_002A(0x205, f >> 4);", "f_29F0_002A(0x205, f >> 4);\n    f_29F0_002A(0x205, (f & 0xf) + ((char)chan + 0x80));",
         tandy_case("negative/tandy-write-order", 0, 60, 100, 3)),
    ]
    report = []
    for target, filename, label, old, new, case in specs:
        source = (seed_dir / filename).read_text(encoding="latin1")
        if source.count(old) != 1:
            raise RuntimeError(f"negative control source anchor not unique: {target}")
        mutant = outdir / "negative" / f"{label}.c"
        mutant.parent.mkdir(parents=True, exist_ok=True)
        mutant.write_text(source.replace(old, new, 1), encoding="latin1")
        baseline_pair = behavior.PreparedPair(target, out=outdir / "negative" / f"{label}-baseline")
        baseline_cmp = baseline_pair.compare(case)
        if not baseline_cmp.equal:
            raise AssertionError(f"negative-control baseline did not match: {target}")
        pair = behavior.PreparedPair(target, source=mutant, out=outdir / "negative" / label)
        comparison = pair.compare(case)
        equal, diff = comparison.equal, comparison.diff
        obj_path = outdir / "negative" / label / "candidate.obj"
        if not obj_path.is_file():
            raise RuntimeError(f"negative candidate object not retained for {target}")
        source_rel = mutant.resolve().relative_to(ROOT.resolve()).as_posix()
        object_rel = obj_path.resolve().relative_to(ROOT.resolve()).as_posix()
        row = {"id": label, "target": target,
               "executed": True, "detected_mismatch": not equal,
               "original_executed": True, "mutant_executed": True,
               "baseline_matches": baseline_cmp.equal, "mutant_differs": not equal,
               "execution_errors": 0,
               "mismatch_categories": sorted(diff.keys()),
               "mutant_source_sha256": pair.identity["source_sha256"],
               "mutant_source": {"path": source_rel, "sha256": pair.identity["source_sha256"]},
               "mutant_object": {"path": object_rel, "sha256": behavior.digest(obj_path.read_bytes())},
               "diff": diff}
        if equal:
            raise AssertionError(f"behavior harness failed to catch negative control: {target}")
        neg_report = {"schema": "behavior-negative-controls-v1", "function": target,
                      "suite_id": SUITE, "errors": 0, "mismatches_detected": 1,
                      "identity": {"source_sha256": baseline_pair.identity["source_sha256"],
                                   "oracle_sha256": baseline_pair.identity["oracle_sha256"],
                                   "harness_sha256": baseline_pair.identity["harness_sha256"],
                                   "historical_manifest_sha256": baseline_pair.identity["manifest_sha256"]},
                      "controls": [row]}
        (outdir / f"negative-controls-{label}.json").write_text(json.dumps(neg_report, indent=2) + "\n")
        report.append(row)
    path = outdir / "negative-controls.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("suite", choices=("findindex", "midi", "tandy", "all"))
    parser.add_argument("--count", type=int, default=None, help="random tests after deterministic/exhaustive cases")
    parser.add_argument("--seed", type=lambda s: int(s, 0), default=0xB3A71)
    parser.add_argument("--out", type=Path, default=ROOT / "build/workers/behavior_small_contracts_hardened")
    parser.add_argument("--negative-controls", action="store_true")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    # Preserve the first bounded suite and its mutation controls byte-for-byte
    # as separate baseline evidence before emitting the hardened run.
    old = ROOT / "build/workers/behavior_small_contracts"
    prior = args.out / "prior-evidence"
    if old.exists() and not prior.exists():
        prior.mkdir(parents=True)
        for filename in ("findindex.json", "midi.json", "tandy.json", "negative-controls.json"):
            src = old / filename
            if src.exists(): shutil.copyfile(src, prior / filename)
    if args.suite == "all":
        names = ("findindex", "midi", "tandy")
    else:
        names = (args.suite,)
    results = []
    for name in names:
        defaults = {"findindex": 10000, "midi": 20000, "tandy": 20000}
        result = run_suite(name, defaults[name] if args.count is None else args.count,
                           args.seed, args.out)
        results.append(result)
    negatives = negative_controls(args.out) if args.negative_controls else []
    print(json.dumps({"suite": SUITE, "results": [{k:r[k] for k in ("contract","cases_generated","cases_run","mismatches","elapsed_seconds","behavioral_status")} for r in results],
                      "negative_controls_detected": sum(n["detected_mismatch"] for n in negatives)}, indent=2))


if __name__ == "__main__":
    main()
