"""Recompute and check the supported clip-generation boundary package."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
import re

sys.dont_write_bytecode = True
ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src/program.json").is_file())
PACKAGE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
import anim_boundary
import bound as bound_module
import census as census_module

ORACLE_SHA256 = "aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11"
MAX_RECORDS = 256
RECORD_BYTES = 8
SENTINEL_TOP_OFFSET = 2
PRODUCER_ORDER = {
    "clip_SubInclude": "f_1D8E_003F ( g_5AAC , r , p , 0L )",
    "f_1E57_08F5": "f_1D8E_003F ( c , r , p , 0L )",
    "clip_SubExclude": "f_1D8E_003F ( g_5AAC , r , 0L , p )",
    "f_1E57_0C2D": "f_1D8E_003F ( r , g_5AAC , 0L , p )",
}
PRODUCER_DIAGNOSTICS = {
    "clip_SubInclude": "CL074:Temp clip overflow in SubInclude",
    "f_1E57_08F5": "CL074:Temp clip overflow in SubInclude",
    "clip_SubExclude": "CL074:Temp clip overflow in SubExclude",
    "f_1E57_0C2D": "CL174:Temp clip overflow in SubExclude",
}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _json_sha(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha(raw)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _source(path: str, overrides: dict[str, str | bytes] | None) -> str:
    if overrides and path in overrides:
        value = overrides[path]
        return value.decode("latin1") if isinstance(value, bytes) else value
    return (ROOT / path).read_text(encoding="latin1")


def _source_and_allocator_facts(owner_module, source_overrides: dict[str, str] | None,
                                owner_facts: dict) -> dict:
    function_text = owner_module.function_text
    normalize = owner_module.normalized
    clip = _source("src/root/m1E57.c", source_overrides)
    helper = _source("src/root/m1D8E.c", source_overrides)

    window_body = function_text(clip, "f_1E57_038E")
    for diagnostic, effect in (
        ('C097: Clip overflow %d" , count )', '_fmemcpy ( list , tmp'),
        ('C098: Clip overflow %d" , count )', 'fd_50F6_3B60 [ next >> 8 ] = f_171C_1A9E'),
        ('C099: Clip overflow %d" , n )', 'g_574A = f_171C_1B2C'),
    ):
        if window_body.index(diagnostic) >= window_body.index(effect):
            raise AssertionError("window clip overflow check moved past emission/allocation")

    records = owner_facts["owner"]["maximum_live_records"]
    if records != 255:
        raise AssertionError("clip-owner induction no longer gives M <= 255")
    formulas = {
        "clip_SubInclude": ("M", records),
        "f_1E57_08F5": ("2M", 2 * records),
        "clip_SubExclude": ("4M", 4 * records),
        "f_1E57_0C2D": ("5M", 5 * records),
    }
    for name, generation in PRODUCER_ORDER.items():
        body = function_text(clip, name)
        check = body.find(">= 256 ) Punt")
        generated = body.find(generation)
        if generated < 0 or check < 0 or generated >= check:
            raise AssertionError(f"{name}: capacity check must follow generation")
        if body.find(PRODUCER_DIAGNOSTICS[name]) < check:
            raise AssertionError(f"{name}: overflow branch diagnostic token moved")
        copy_at = body.find("_fmemcpy ( g_5AAC")
        if copy_at >= 0 and check >= copy_at:
            raise AssertionError(f"{name}: destination copy no longer follows its check")

    checked_source = function_text(clip, "f_1E57_08F5")
    if "if ( ! g_5AAC )" not in checked_source:
        raise AssertionError("08F5's unchecked null-current-list branch changed")
    if checked_source.count("for (") != 3:
        raise AssertionError("08F5 nested caller/current-list traversal changed")

    helper_body = function_text(helper, "f_1D8E_003F")
    # One increment is the wholly-outside pass-through; the four remaining
    # increments are the ordered top/bottom/left/right slabs.
    if helper_body.count("out ++") != 5 or "out --" in helper_body or "out -= " in helper_body:
        raise AssertionError("rectangle helper is no longer a non-retreating 0..4 output walk")
    if "out -> top = RECT_END" not in helper_body:
        raise AssertionError("rectangle helper sentinel write changed")
    for name, body_token in PRODUCER_ORDER.items():
        body = function_text(clip, name)
        if "p --" in body or "p -= " in body or "p = p -" in body:
            raise AssertionError(f"{name}: output pointer can retreat")
        if body_token not in body:
            raise AssertionError(f"{name}: output pointer/helper relation changed")

    maximum_records = formulas["f_1E57_0C2D"][1]
    sentinel_start = maximum_records * RECORD_BYTES + SENTINEL_TOP_OFFSET
    last_written_byte = sentinel_start + 1
    end_exclusive = last_written_byte + 1
    if not (maximum_records == 1275 and end_exclusive == 10204 and end_exclusive < 0x10000):
        raise AssertionError("finite nonwrapping 5M envelope changed")

    mem = _source("src/root/m171C.c", source_overrides)
    alloc = function_text(mem, "f_171C_07BE")
    payload = function_text(mem, "f_171C_125C")
    indexed = function_text(mem, "f_171C_1A9E")
    lock = function_text(mem, "f_171C_1B84")
    resolve = function_text(mem, "f_171C_1FC2")
    ems = function_text(mem, "f_171C_0034")
    normalized_mem = normalize(mem)
    required = [
        "_dos_allocmem ( 0xFF00 , & g_91A0 )",
        "_dos_allocmem ( g_91A0 , & g_91A2 )",
        "s_8C72 = ( s_2F4A * 4 + 15 ) / 16",
        "s_2F46 = ( Handle ) ( ( ( unsigned long ) s_8C72 + g_91A2 - 0x1000 ) << 16 )",
        "g_91A0 -= s_8C72 + 1",
        "g_91A2 += s_8C72 + 1",
        "g_91AC = g_91A4 = BLK ( g_91A2 )",
    ]
    for token in required:
        if token not in normalized_mem:
            raise AssertionError("allocator provenance token missing: " + token)
    if "#defineBLK(s)((Blockfar*)((unsignedlong)(s)<<16))" not in "".join(mem.split()):
        raise AssertionError("allocator block pointers are no longer normalized at offset zero")
    if not (alloc.index("s_2F46 =") < alloc.index("g_91A2 += s_8C72 + 1")
            < alloc.index("g_91AC = g_91A4 = BLK ( g_91A2 )")):
        raise AssertionError("handle table no longer precedes block arena")
    if "* h = ( char far * ) ( ( long ) b + 0x20000L )" not in payload:
        raise AssertionError("allocation payload no longer begins at normalized header+2")
    if "return ( Handle ) ( ( long ) ( s_2F46 - h ) + 0xF0EFFFFL )" not in indexed:
        raise AssertionError("indexed-handle mapping changed")
    if "p = f_171C_1FC2 ( h )" not in lock or "return * p" not in lock:
        raise AssertionError("handle lock no longer resolves the payload")
    if "CHECKH ( h )" not in resolve:
        raise AssertionError("handle index resolution guard changed")
    if "fd_50F6_394C = FP_SEG ( fd_55B3_360E ) + 1" not in ems:
        raise AssertionError("EMS frame endpoint token changed")
    if "fd_50F6_394E = 0xBF8" not in ems:
        raise AssertionError("EMS managed paragraph count changed")
    for token in ("s_2F3E = fd_50F6_394E + fd_50F6_394C - g_91A2",
                  "fd_50F6_3950 = SEG ( BLK ( g_91A2 ) ) + g_91A0 - 2"):
        if token not in alloc:
            raise AssertionError("EMS arena endpoint/range token changed: " + token)

    ems_frame_max = 0xF000
    ems_endpoint_paragraph = ems_frame_max + 1 + 0xBF8
    ems_endpoint_byte = ems_endpoint_paragraph << 4
    ems_envelope_end = ems_endpoint_byte + end_exclusive
    if ems_envelope_end >= 0x100000:
        raise AssertionError("EMS forward envelope can cross the 1 MiB endpoint")

    # The original MZ image plus min_alloc is the loaded process memory range.
    # Pin the original addresses for the static list, code, Punt guard and stack
    # anchor that the forward envelope must be kept away from.
    import behavior
    import exe
    oracle = exe.load()
    original_addresses = {
        "clip_destination": behavior.symbol_address("fd_50F6_3C14"),
        "screen_rectangle": behavior.symbol_address("g_5A9C"),
        "clip_generator": behavior.symbol_address("f_1E57_038E"),
        "outside_producer": behavior.symbol_address("clip_SubExclude"),
        "outside_helper": behavior.symbol_address("f_1D8E_003F"),
        "unchecked_caller": behavior.symbol_address("f_0250_5058"),
        "Punt": behavior.symbol_address("Punt"),
        "Punt_guard": 0x55B30 + 0x54F8,
    }
    mz_stack_base = oracle.mz.ss * 16
    mz_stack_top = mz_stack_base + oracle.mz.sp
    loaded_process_end = len(oracle.image) + oracle.mz.min_alloc * 16
    if any(address < 0 or address >= loaded_process_end for address in original_addresses.values()):
        raise AssertionError("protected original read/control address escaped the MZ process block")
    if mz_stack_top > loaded_process_end:
        raise AssertionError("MZ initial stack anchor escaped the loaded process block")

    return {
        "clip_owner_M": records,
        "clip_owner_induction": {
            "records": owner_facts["owner"]["records"],
            "record_bytes": owner_facts["owner"]["record_bytes"],
            "extent_bytes": owner_facts["owner"]["extent_bytes"],
            "maximum_live_records": owner_facts["owner"]["maximum_live_records"],
            "sentinel_records": owner_facts["owner"]["sentinel_records"],
            "initialization": owner_facts["owner"]["initialization"],
            "destination_census_sha256": owner_facts["destination_census"]["sha256"],
            "destination_writers": owner_facts["destination_writers"],
        },
        "producer_precheck_bounds": [
            {"producer": name, "formula": formula, "max_records": maximum,
             "diagnostic": PRODUCER_DIAGNOSTICS[name]}
            for name, (formula, maximum) in formulas.items()
        ],
        "unchecked_08f5": {
            "branch": "g_5AAC == NULL",
            "caller": "f_0250_5058",
            "caller_records_including_sentinel": 3,
            "rectangles": 2,
            "arbitrary_larger_direct_entry": "EXCLUDED",
        },
        "traversal_and_offsets": {
            "current_list_max_records": records,
            "maximum_output_records": maximum_records,
            "sentinel_top_word_start_offset": sentinel_start,
            "last_written_byte_offset": last_written_byte,
            "write_end_exclusive": end_exclusive,
            "largest_record_pointer_difference": maximum_records,
            "record_payload_byte_span": maximum_records * RECORD_BYTES,
            "signed_int_record_difference_wrap": False,
            "far_offset_wrap": False,
            "pointer_retreat": False,
            "premise": "current-list sentinel controls finite iteration independently of rectangle values; f_1D8E_003F writes at most four outside records and never retreats p",
        },
        "allocator": {
            "conventional_arena": "_dos_allocmem in f_171C_07BE",
            "payload": "offset zero at paragraph-normalized block segment + 2 (32-byte header)",
            "handle_table": "placed before first block arena via s_8C72 / g_91A2 split",
            "ems_frame_max_assumption": "F000",
            "ems_managed_endpoint_paragraph": ems_endpoint_paragraph,
            "ems_managed_endpoint_byte": ems_endpoint_byte,
            "ems_envelope_end_byte": ems_envelope_end,
            "below_1MiB": True,
        },
        "range_separation": {
            "protected_generation_reads": [
                "current list: fd_50F6_3C14 or screen rectangle g_5A9C",
                "08F5 caller stack rectangles and local stack/control state",
                "executing clip/helper/caller code and return addresses",
                "Punt guard in DGROUP",
            ],
            "conventional_premise": "ordinary _dos_allocmem payload follows loaded DOS image; a forward write of at most 10204 bytes cannot reach lower image, DGROUP, stack or code",
            "alternate_placement": "if the arena can be below/within the loaded image, independently prove the same protected-range separation; historical read ranges are not assumed away",
            "heap_neighbors": "NOT PROTECTED; physical corruption is excluded from the claim",
            "original_loaded_process_range": [0, loaded_process_end],
            "original_protected_read_addresses": original_addresses,
            "original_initial_stack_segment_base": mz_stack_base,
            "original_initial_stack_top": mz_stack_top,
            "protected_addresses_within_loaded_process": True,
        },
        "allocator_source_token_sha256": {
            "src/root/m171C.c": _sha(mem.encode("latin1"))
        },
    }


def _program_for_overrides(source_overrides: dict[str, str] | None):
    if not source_overrides:
        return None
    program = json.loads((ROOT / "src/program.json").read_text(encoding="utf-8"))
    for module in program["modules"]:
        text = source_overrides.get(module["source"])
        if text is not None:
            raw = text if isinstance(text, bytes) else text.encode("latin1")
            module["source_sha256"] = _sha(raw)
    return program


def _lifetime_facts(lifetime: dict, bound: dict) -> dict:
    if lifetime["function_count"] != 1264 or len(lifetime["open_census"]) != 48:
        raise AssertionError("reviewed opener census count changed")
    if len(lifetime["indirect_calls"]) != 106:
        raise AssertionError("reviewed indirect-call census count changed")
    ids = {"persistent": bound["persistent_ids"],
           "transient": bound["transient_ids"],
           "transient_pairs": bound["transient_pairs"]}
    if ids != {
        "persistent": [0, 1, 5, 18, 19, 21, 25],
        "transient": [2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17,
                      20, 22, 23, 24, 26, 29, 30, 31, 32, 33],
        "transient_pairs": [[9, 12], [9, 13], [9, 14], [9, 15], [9, 16], [9, 17], [26, 30]],
    }:
        raise AssertionError("reviewed persistent/transient co-open catalog changed")
    max_stack = max(row["window_count"] for row in bound["states"])
    if max_stack != 9 or bound["maximum_stack_ceiling"] != max_stack:
        raise AssertionError("co-open census no longer supports N <= 9")
    return {
        "function_count": lifetime["function_count"],
        "open_call_count": len(lifetime["open_census"]),
        "open_census_sha256": _json_sha(lifetime["open_census"]),
        "opener_descendant_paths_sha256": _json_sha(lifetime["opener_descendant_paths"]),
        "hook_open_paths_sha256": _json_sha(lifetime["hook_open_paths"]),
        "indirect_call_count": len(lifetime["indirect_calls"]),
        "indirect_calls_sha256": _json_sha(lifetime["indirect_calls"]),
        "window_catalog": ids,
        "max_simultaneous_windows": max_stack,
        "bound_premises": bound["premises"],
        "inherited_bound_scope": [
            "existing window-domain supported source/event/ordinary-save domain",
            "pinned HCEGANT/SHARED resources and successful relevant services",
            "locked VGA profile 8",
            "ordinary first-fatal Punt behavior",
            "exclude arbitrary helper entry, fabricated events, corrupt/replacement resources or saves, and returning-Punt continuation",
        ],
        "decoded_nonempty_resource_guards_passed": bound["nonempty_resource_guards_passed"],
        "root_extent_residues_mod16": bound["root_extent_residues_mod16"],
    }


def _window_bound_facts(bound: dict, lifetime_facts: dict) -> dict:
    if lifetime_facts["max_simultaneous_windows"] != 9:
        raise AssertionError("window count premise changed")
    expected = {"C097_bound": 137, "C098_bound": 137, "C099_bound": 172,
                "sentinel_inclusive_maximum": 173}
    if any(bound.get(key) != value for key, value in expected.items()):
        raise AssertionError("decoded-resource window bound changed")
    if bound["maximum_stack_ceiling"] > 9 or bound["C099_bound"] > 172:
        raise AssertionError("window-stack/C099 bound exceeds reviewed ceiling")
    sys.path.insert(0, str(ROOT / "evidence/canonical/audio-track-owner"))
    import shipped_domain
    window_ids = sorted(row["id"] for row in shipped_domain.parse_records("HCEGANT")[1]
                        if row["kind"] == 0 and 0 <= row["id"] < 34)
    if window_ids != list(range(34)):
        raise AssertionError("decoded shipped window-resource ID set changed")
    return {
        "maximum_window_stack": bound["maximum_stack_ceiling"],
        "C097_records_before_sentinel": bound["C097_bound"],
        "C098_records_before_sentinel": bound["C098_bound"],
        "C099_records_before_sentinel": bound["C099_bound"],
        "maximum_records_plus_sentinel": bound["sentinel_inclusive_maximum"],
        "window_resource_count": len(window_ids),
        "supported_window_geometry_count": len(bound["window_object0_geometry"]),
        "decoded_asset_sha256": bound["assets"],
        "decoded_font_sha256": {row["name"]: row["sha256"] for row in bound["fonts"]},
        "recomputed_bound_sha256": _json_sha(bound),
        "source_pins": bound["source_pins"],
    }


def _original_controls(owner_module, owner_fresh: dict, run_controls: bool) -> dict:
    if not run_controls:
        return {"status": "not-run"}
    domain_module = _load("clip_domain_replay_for_package",
                          ROOT / "evidence/canonical/clip-domain/replay.py")
    domain_cases = domain_module.controls()
    domain_summary = []
    for row in domain_cases:
        domain_summary.append({key: row[key] for key in (
            "bars_per_axis", "windows", "completed", "visible_rectangles",
            "pairwise_nonoverlap", "scratch_allocations", "boundary_events", "tmp_tail")})

    owner_summary = owner_fresh["original_boundary_controls"]

    fixture = json.loads((PACKAGE / "animation-fixture.json").read_text(encoding="utf-8"))
    pre_state = fixture["incoming_current_list"]
    animation_result = anim_boundary.execute(fixture)
    punt_events = [row for row in animation_result["events"]
                   if row.get("event") == "Punt-entry"]
    if len(punt_events) != 1 or punt_events[0].get("message") != "CL074:Temp clip overflow in SubExclude":
        raise AssertionError("same-anchor original animation replay lost its CL074 boundary")
    if punt_events[0].get("loop") != 2 or punt_events[0].get("role") != "swarm-old-1-1":
        raise AssertionError("animation overflow no longer occurs at the reviewed same-anchor loop-2 witness")
    if punt_events[0].get("generated_count_including_overflow_record") != 256:
        raise AssertionError("animation original replay no longer witnesses the 256-record boundary")

    return {
        "original_sha256": ORACLE_SHA256,
        "clip_domain_29_31_window_controls": domain_summary,
        "animation_same_anchor_control": {
            "fixture": "clip-subexclude-255-list-one-cutter",
            "original_boundary_case": animation_result["label"],
            "pre_state_records": len(pre_state),
            "pre_state_sha256": _json_sha(pre_state),
            "loop": punt_events[0]["loop"],
            "role": punt_events[0]["role"],
            "rect": punt_events[0].get("rect"),
            "generated_count_including_overflow_record": punt_events[0]["generated_count_including_overflow_record"],
            "Punt_message": punt_events[0]["message"],
            "original_bodies": animation_result["original_bodies"],
            "modeled_services": animation_result["modeled_services"],
            "scope": animation_result["scope"],
        },
        "clip_owner_255_256_controls": owner_summary,
        "replay_results_recomputed": True,
    }


def collect(*, run_controls: bool = True,
            source_overrides: dict[str, str | bytes] | None = None) -> dict:
    """Recompute resource, source/census, and original-instruction facts."""
    bound = bound_module.compute()
    lifetime = census_module.collect()
    owner_module = _load("clip_package_clip_owner", ROOT / "evidence/canonical/clip-owner/replay.py")
    owner_overrides = {
        path: value if isinstance(value, bytes) else value.encode("latin1")
        for path, value in (source_overrides or {}).items()
    } or None
    program_override = _program_for_overrides(owner_overrides)
    owner_fresh = owner_module.collect(program_override=program_override,
                                       source_overrides=owner_overrides,
                                       run_original=run_controls)
    # The source/range proof uses the fresh owner census; no saved owner facts are read.
    source_facts = _source_and_allocator_facts(owner_module, owner_overrides, owner_fresh)
    life_facts = _lifetime_facts(lifetime, bound)

    input_paths = [
        "evidence/canonical/clip-domain/replay.py",
        "evidence/canonical/clip-domain/review.md",
        "evidence/canonical/clip-owner/replay.py",
        "evidence/canonical/clip-owner/review.md",
        "evidence/canonical/audio-track-owner/shipped_domain.py",
        "tools/resource_domains.py",
    ]
    local_inputs = ["probe.py", "bound.py", "census.py", "anim_boundary.py", "animation-fixture.json",
                    "bound-proof.md", "review.md"]
    input_hashes = {
        f"evidence/canonical/clip-generation/{name}": _sha((PACKAGE / name).read_bytes())
        for name in local_inputs
    }
    input_hashes.update({path: _sha((ROOT / path).read_bytes()) for path in input_paths})
    return {
        "schema": "simant-clip-generation-package-v1",
        "verdict": "SUPPORTED_DOMAIN_OVERFLOW_CALL_SELECTION_ONLY",
        "contract": "same overflow diagnostic call selected; counts, generated rectangles and heap state after capacity exhaustion are not claimed equivalent",
        "window_bound": _window_bound_facts(bound, life_facts),
        "lifetime_and_coopen_census": life_facts,
        "producer_and_allocator_proof": source_facts,
        "overflow_call_sites": [
            {"producer": name, "diagnostic": diagnostic,
             "count_argument": False}
            for name, diagnostic in PRODUCER_DIAGNOSTICS.items()
        ],
        "original_instruction_controls": _original_controls(owner_module, owner_fresh, run_controls),
        "input_sha256": input_hashes,
    }


def check(*, run_controls: bool = True,
          source_overrides: dict[str, str] | None = None,
          facts_path: Path | None = None) -> dict:
    actual = collect(run_controls=run_controls, source_overrides=source_overrides)
    if source_overrides:
        # Mutation callers assert that recomputation rejects their virtual source.
        return actual
    if not run_controls:
        raise ValueError("a package check must recompute the original-instruction controls")
    expected_path = facts_path or (PACKAGE / "facts.json")
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    if actual != expected:
        raise ValueError("clip-generation recomputation differs from pinned facts.json")
    return actual


def check_source_overrides(source_overrides: dict[str, str]) -> dict:
    """Run the fast source/ownership checks for virtual-source mutation tests."""
    owner_module = _load("clip_package_mutation_clip_owner",
                         ROOT / "evidence/canonical/clip-owner/replay.py")
    owner_overrides = {path: value.encode("latin1") for path, value in source_overrides.items()}
    m0250 = _source("src/root/m0250.c", owner_overrides)
    tokens = [token.text for token in owner_module.csrc.tokenize(m0250)
              if token.kind == "id" and token.text == "f_1E57_08F5"]
    caller = re.search(r"void\s+far\s+f_0250_5058\s*\(\s*void\s*\)\s*\{([^{}]*)\}",
                       m0250, re.S)
    if len(tokens) != 2 or caller is None:
        raise AssertionError("f_1E57_08F5 no longer has exactly one definition-site caller")
    caller_tokens = owner_module.normalized(caller.group(1))
    for token in ("struct Rect rects [ 3 ] ;", "rects [ 2 ] . top = 0x8000 ;",
                  "f_1E57_08F5 ( rects ) ;"):
        if token not in caller_tokens:
            raise AssertionError("08F5's two-record-plus-sentinel caller changed")
    stub_owner = {
        "owner": {"records": 256, "record_bytes": 8, "extent_bytes": 2048,
                  "maximum_live_records": 255, "sentinel_records": 1,
                  "initialization": "source-only mutation check; full induction is checked by collect()"},
        "destination_census": {"sha256": "source-mutation-only"},
        "destination_writers": sorted(owner_module.DESTINATION_WRITERS),
    }
    return _source_and_allocator_facts(owner_module, owner_overrides, stub_owner)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-facts", action="store_true",
                        help="write the freshly recomputed facts.json in this package")
    args = parser.parse_args()
    if args.write_facts:
        facts = collect(run_controls=True)
        (PACKAGE / "facts.json").write_text(json.dumps(facts, indent=2) + "\n", encoding="utf-8")
        print("wrote " + str(PACKAGE / "facts.json"))
    else:
        check()
        print("PASS: clip-generation facts, resource bound, source census, and controls")


if __name__ == "__main__":
    main()
