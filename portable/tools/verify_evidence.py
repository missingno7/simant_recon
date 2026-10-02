#!/usr/bin/env python3
"""Audit pinned inputs of selected native-vs-frozen-DOS evidence reports.

This is a read-only auditor. It never edits reports, historical reconstruction
metadata, or source files. CURRENT means the recorded evidence inputs still
match the checked-out files; it is not an acceptance or semantic-closure claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "build/native-proof-pin-audit.json"


# Schemas intentionally remain explicit. Field names in historic reports are
# inconsistent; adapters below bind each field to the actual input path.
REPORTS: list[dict[str, Any]] = [
    {
        "id": "movement",
        "report": "portable/tests/movement/evidence/movement-full-322720.json",
        "native": [("native_sources.header_sha256", "portable/game/simulation/movement.h"),
                   ("native_sources.source_sha256", "portable/game/simulation/movement.c")],
        "library": ("native_sources.library_sha256", "build/portable/movement.dll"),
        "command_fields": ["native_sources.build_command"],
        "suite_path_field": "archived_suite", "suite_hash_field": "suite_sha256",
        "runner": [("runner_sha256", "tools/behavior.py")],
        "manifest_field": "historical_manifest_sha256",
        "oracle_field": "oracle_sha256", "dos_count": "executed",
    },
    {
        "id": "nest",
        "report": "portable/tests/nest/evidence/nest-random-5000-dig-128.json",
        "native": [("native.source_sha256", "portable/game/simulation/nest.c"),
                   ("native.header_sha256", "portable/game/simulation/nest.h"),
                   ("native.adapter_sha256", "portable/tests/nest/native_adapter.c")],
        "library": ("native.library_sha256", "build/portable/nest.dll"),
        "command_fields": ["native.build_command"],
        "suite_path_field": "suite", "suite_hash_field": "suite_sha256",
        "runner": [("runner_sha256", "tools/behavior.py")],
        "manifest_field": "historical_manifest_sha256",
        "oracle_field": "oracle_sha256", "dos_count": "executed",
    },
    {
        "id": "spider_corrected",
        "report": "portable/tests/spider/evidence/native-dos-spiderscan-10146.json",
        "native": [("native_source_sha256", "portable/game/simulation/spider.c"),
                   ("native_header_sha256", "portable/game/simulation/spider.h"),
                   ("native_bridge_sha256", "portable/tests/spider/native_bridge.c")],
        "library": ("native_library_sha256", "build/portable/spider-test.dll"),
        "command_fields": ["compile_command"],
        "suite_path_field": "archived_suite", "suite_hash_field": "suite_sha256",
        "runner": [("runner_sha256", "tools/behavior.py")],
        "oracle_field": "oracle_sha256", "dos_count": "cases",
        "linked_report": {
            "path": "portable/tests/spider/evidence/manifest-corrected.json",
            "field": "report_sha256", "target": "portable/tests/spider/evidence/native-dos-spiderscan-10146.json",
        },
        "linked_report_inputs": "source_hashes",
    },
    {
        "id": "movespider_current_world",
        "report": "portable/tests/spider_sim/evidence/native-dos-movespider-10146-current-world.json",
        "path_hash_maps": ["source_hashes"],
        "library": ("native_library_sha256", "build/portable/spider-sim-test.dll"),
        "native_tus": ["portable/tests/spider_sim/native_bridge.c", "portable/game/simulation/spider_sim.c",
                       "portable/game/simulation/spider.c", "portable/game/simulation/movement.c",
                       "portable/game/simulation/rng.c"],
        "oracle_field": "oracle_sha256", "dos_count": "cases",
        "related_documents": [
            {"path": "portable/tests/spider_sim/evidence/run-plan-current-world.json",
             "hash_links": [("report_sha256", "portable/tests/spider_sim/evidence/native-dos-movespider-10146-current-world.json"),
                            ("receipt_sha256", "portable/tests/spider_sim/evidence/source-stability-receipt-current-world.json")],
             "file_pins": [("producer_sha256", "portable/tests/spider_sim/evidence/run-pinned-current-world.py"),
                           ("world_header_sha256", "portable/game/state/world.h")],
             "assertions": [("all_dependency_hashes_stable_during_run", True), ("passed", 10146), ("total_cases", 10146)]},
            {"path": "portable/tests/spider_sim/evidence/source-stability-receipt-current-world.json",
             "source_maps": ["source_hashes_before", "source_hashes_after"],
             "file_pins": [("producer_sha256", "portable/tests/spider_sim/evidence/run-pinned-current-world.py")],
             "hash_links": [("report_sha256", "build/portable/spider-tick-current-world-10146.json")],
             "compare_maps_to_primary": "source_hashes",
             "assertions": [("status", "source-stable"), ("runner_exit_code", 0)]},
        ],
    },
    {"id": "movespider_prior_stale_world_archived",
     "report": "portable/tests/spider_sim/evidence/native-dos-movespider-10146-stale-world-header.json",
     "archived": True},
    {"id": "movespider_prior_plan_archived",
     "report": "portable/tests/spider_sim/evidence/run-plan-stale-world-header.json",
     "archived": True},
    {"id": "movespider_prior_generic_archived",
     "report": "portable/tests/spider_sim/evidence/native-dos-movespider-10146.json",
     "archived": True},
    {"id": "movespider_prior_plan_archived_legacy",
     "report": "portable/tests/spider_sim/evidence/run-plan.json",
     "archived": True},
    {
        "id": "database",
        "report": "portable/tests/resources/evidence/database-dos-differential.json",
        "native": [("native_sources.database_h", "portable/game/resources/database.h"),
                   ("native_sources.database_c", "portable/game/resources/database.c"),
                   ("native_sources.test_c", "portable/tests/resources/database_test.c")],
        "native_tus": ["portable/game/resources/database.c", "portable/tests/resources/database_test.c"],
        "asset_fields": [
            ("assets.HCEGANT.ndx_sha256", "assets/HCEGANT.NDX"),
            ("assets.HCEGANT.dat_sha256", "assets/HCEGANT.DAT"),
            ("assets.SHARED.ndx_sha256", "assets/SHARED.NDX"),
            ("assets.SHARED.dat_sha256", "assets/SHARED.DAT"),
            ("assets.SOUND.ndx_sha256", "assets/SOUND.NDX"),
            ("assets.SOUND.dat_sha256", "assets/SOUND.DAT"),
        ],
        "suite_hash_field": "suite_sha256",
        "suite_hash_search_roots": ["portable/tests/resources", "tools/behavior_suites/archive"],
        "harness": [("harness_sha256", "tools/behavior.py")],
        "oracle_field": "oracle.sha256",
        "dos_count": {"sum": ["lzss_original_dos.records_compared", "findindex_original_dos.cases"]},
    },
    {
        "id": "render",
        "report": "portable/tests/render/evidence/dos-render-differential.json",
        "path_hash_maps": ["pins.sources"],
        "native_tu_maps": ["pins.sources"],
        "oracle_fields": ["original_runtime.dos_executable_sha256", "original_runtime.oracle_sha256"],
        "dos_count": "render_original_call_count",
    },
    {
        "id": "terrain953",
        "report": "portable/tests/terrain/evidence/terrain-dos-diff-953-20261002.json",
        "native_hash_map": ("native_source_sha256", {
            "terrain.c": "portable/game/simulation/terrain.c", "terrain.h": "portable/game/simulation/terrain.h",
            "rng.c": "portable/game/simulation/rng.c", "native_probe.c": "portable/tests/terrain/native_probe.c",
            "test_terrain.c": "portable/tests/terrain/test_terrain.c"}),
        "harness_hash_map": ("harness_sha256", {
            "behavior": "tools/behavior.py", "exe": "tools/exe.py", "functions": "tools/functions.py",
            "match": "tools/match.py"}),
        "runner": [("runner_sha256", "portable/tests/terrain/run_dos_diff.py")],
        "command_fields": ["native_command"],
        "oracle_fields": ["oracle_exe_sha256"], "dos_count": "compared_count",
    },
    {
        "id": "water50",
        "report": "portable/tests/water/evidence/water-dos-diff-20261002.json",
        "native_hash_map": ("native_source_sha256", {
            "water.c": "portable/game/simulation/water.c", "water.h": "portable/game/simulation/water.h",
            "rng.c": "portable/game/simulation/rng.c", "native_probe.c": "portable/tests/water/native_probe.c"}),
        "harness_hash_map": ("harness_sha256", {
            "behavior": "tools/behavior.py", "exe": "tools/exe.py", "functions": "tools/functions.py",
            "match": "tools/match.py"}),
        "runner": [("runner_sha256", "portable/tests/water/run_dos_diff.py")],
        "command_fields": ["native_command"],
        "oracle_fields": ["oracle_exe_sha256"], "dos_count": "executed_count",
    },
    {
        "id": "terrain950_current_20261002",
        "report": "portable/tests/terrain/evidence/current/20261002/terrain-950-rerun3.json",
        "path_hash_maps": ["native_source_hashes", "oracle_input_hashes"],
        "native_tu_maps": ["native_source_hashes"],
        "command_fields": ["native_command"],
        "runner": [("runner_sha256", "portable/tests/terrain/run_dos_diff.py")],
        "producer": [("compiler_sha256", "C:/msys64/mingw64/bin/gcc.exe")],
        "library_from_report": ("native_library_sha256", "native_library_path"),
        "oracle_field": "oracle_exe_sha256", "manifest_field": "oracle_input_hashes.layout/manifest.json",
        "dos_count": "compared_count",
        "related_documents": [{
            "path": "portable/tests/evidence/current/20261002/leaf-suite-source-stability-receipt-rerun3.json",
            "source_maps": ["runs.0.inputs_before", "runs.0.inputs_after"],
            "hash_links": [("runs.0.report_sha256", "portable/tests/terrain/evidence/current/20261002/terrain-950-rerun3.json"),
                           ("runs.0.library_sha256", "build/portable/current-20261002/terrain-probe-rerun3.dll")],
            "file_pins": [("producer_sha256", "portable/tests/evidence/run-current-leaf-suites-20261002.py")],
            "assertions": [("runs.0.id", "terrain"), ("runs.0.runner_exit_code", 0),
                           ("runs.0.source_stability", "stable")],
        }],
    },
    {
        "id": "water50_current_20261002",
        "report": "portable/tests/water/evidence/current/20261002/water-50-rerun3.json",
        "path_hash_maps": ["native_source_hashes", "oracle_input_hashes"],
        "native_tu_maps": ["native_source_hashes"],
        "command_fields": ["native_command"],
        "runner": [("runner_sha256", "portable/tests/water/run_dos_diff.py")],
        "producer": [("compiler_sha256", "C:/msys64/mingw64/bin/gcc.exe")],
        "library_from_report": ("native_library_sha256", "native_library_path"),
        "oracle_field": "oracle_exe_sha256", "manifest_field": "oracle_input_hashes.layout/manifest.json",
        "dos_count": "executed_count",
        "related_documents": [{
            "path": "portable/tests/evidence/current/20261002/leaf-suite-source-stability-receipt-rerun3.json",
            "source_maps": ["runs.1.inputs_before", "runs.1.inputs_after"],
            "hash_links": [("runs.1.report_sha256", "portable/tests/water/evidence/current/20261002/water-50-rerun3.json"),
                           ("runs.1.library_sha256", "build/portable/current-20261002/water-probe-rerun3.dll")],
            "file_pins": [("producer_sha256", "portable/tests/evidence/run-current-leaf-suites-20261002.py")],
            "assertions": [("runs.1.id", "water"), ("runs.1.runner_exit_code", 0),
                           ("runs.1.source_stability", "stable")],
        }],
    },
    {
        "id": "feeding126_current_20261002",
        "report": "portable/tests/feeding/evidence/current/20261002/feeding-126-rerun3.json",
        "path_hash_maps": ["native_source_hashes", "oracle_input_hashes"],
        "native_tu_maps": ["native_source_hashes"],
        "command_fields": ["native_command"],
        "runner": [("runner_sha256", "portable/tests/feeding/run_dos_diff.py")],
        "producer": [("compiler_sha256", "C:/msys64/mingw64/bin/gcc.exe")],
        "library_from_report": ("native_library_sha256", "native_library_path"),
        "oracle_field": "oracle_exe_sha256", "manifest_field": "oracle_input_hashes.layout/manifest.json",
        "dos_count": "executed_count",
        "related_documents": [{
            "path": "portable/tests/evidence/current/20261002/leaf-suite-source-stability-receipt-rerun3.json",
            "source_maps": ["runs.2.inputs_before", "runs.2.inputs_after"],
            "hash_links": [("runs.2.report_sha256", "portable/tests/feeding/evidence/current/20261002/feeding-126-rerun3.json"),
                           ("runs.2.library_sha256", "build/portable/current-20261002/feeding-probe-rerun3.dll")],
            "file_pins": [("producer_sha256", "portable/tests/evidence/run-current-leaf-suites-20261002.py")],
            "assertions": [("runs.2.id", "feeding"), ("runs.2.runner_exit_code", 0),
                           ("runs.2.source_stability", "stable")],
        }],
    },
    {
        "id": "scent360_current_20261002",
        "report": "portable/tests/scent/evidence/current/20261002/scent-360-rerun3.json",
        "path_hash_maps": ["native_source_hashes", "oracle_input_hashes"],
        "native_tu_maps": ["native_source_hashes"],
        "command_fields": ["native_command"],
        "runner": [("runner_sha256", "portable/tests/scent/run_dos_diff.py")],
        "producer": [("compiler_sha256", "C:/msys64/mingw64/bin/gcc.exe")],
        "library_from_report": ("native_library_sha256", "native_library_path"),
        "oracle_field": "oracle_exe_sha256", "manifest_field": "oracle_input_hashes.layout/manifest.json",
        "dos_count": "executed_count",
        "related_documents": [{
            "path": "portable/tests/evidence/current/20261002/leaf-suite-source-stability-receipt-rerun3.json",
            "source_maps": ["runs.3.inputs_before", "runs.3.inputs_after"],
            "hash_links": [("runs.3.report_sha256", "portable/tests/scent/evidence/current/20261002/scent-360-rerun3.json"),
                           ("runs.3.library_sha256", "build/portable/current-20261002/scent-probe-rerun3.dll")],
            "file_pins": [("producer_sha256", "portable/tests/evidence/run-current-leaf-suites-20261002.py")],
            "assertions": [("runs.3.id", "scent"), ("runs.3.runner_exit_code", 0),
                           ("runs.3.source_stability", "stable")],
        }],
    },
    {
        "id": "worldgen_union_final_sweep",
        "report": "portable/tests/worldgen/evidence/randworld-union-final-sweep-20261002.json",
        "path_hash_maps": ["native_source_hashes", "evidence_input_hashes"],
        "native": [("native_bridge_sha256", "portable/tests/worldgen/native_snapshot.c")],
        "native_tu_maps": ["native_source_hashes"],
        "command_fields": ["build_command"],
        "runner": [("runner_sha256", "portable/tests/worldgen/run_dos_diff.py")],
        "harness": [("harness_sha256", "tools/behavior.py")],
        "producer": [("compiler_sha256", "C:/msys64/mingw64/bin/gcc.exe")],
        "library_from_report": ("native_library_sha256", "native_library_path"),
        "oracle_fields": ["oracle_sha256", "oracle_identity.sha256"], "dos_count": "case_count",
    },
    {
        "id": "worldgen_union_final_edge_8000",
        "report": "portable/tests/worldgen/evidence/randworld-union-final-edge-8000-20261002.json",
        "path_hash_maps": ["native_source_hashes", "evidence_input_hashes"],
        "native": [("native_bridge_sha256", "portable/tests/worldgen/native_snapshot.c")],
        "native_tu_maps": ["native_source_hashes"],
        "command_fields": ["build_command"],
        "runner": [("runner_sha256", "portable/tests/worldgen/run_dos_diff.py")],
        "harness": [("harness_sha256", "tools/behavior.py")],
        "producer": [("compiler_sha256", "C:/msys64/mingw64/bin/gcc.exe")],
        "library_from_report": ("native_library_sha256", "native_library_path"),
        "oracle_fields": ["oracle_sha256", "oracle_identity.sha256"], "dos_count": "case_count",
    },
    {
        "id": "worldgen_union_final_edge_ffff",
        "report": "portable/tests/worldgen/evidence/randworld-union-final-edge-ffff-20261002.json",
        "path_hash_maps": ["native_source_hashes", "evidence_input_hashes"],
        "native": [("native_bridge_sha256", "portable/tests/worldgen/native_snapshot.c")],
        "native_tu_maps": ["native_source_hashes"],
        "command_fields": ["build_command"],
        "runner": [("runner_sha256", "portable/tests/worldgen/run_dos_diff.py")],
        "harness": [("harness_sha256", "tools/behavior.py")],
        "producer": [("compiler_sha256", "C:/msys64/mingw64/bin/gcc.exe")],
        "library_from_report": ("native_library_sha256", "native_library_path"),
        "oracle_fields": ["oracle_sha256", "oracle_identity.sha256"], "dos_count": "case_count",
    },
    {"id": "worldgen_session_sweep_prior_archived",
     "report": "portable/tests/worldgen/evidence/randworld-session-sweep-20261002.json", "archived": True},
    {"id": "worldgen_session_edge_8000_prior_archived",
     "report": "portable/tests/worldgen/evidence/randworld-session-edge-8000-20261002.json", "archived": True},
    {"id": "worldgen_session_edge_ffff_prior_archived",
     "report": "portable/tests/worldgen/evidence/randworld-session-edge-ffff-20261002.json", "archived": True},
    {"id": "worldgen_seed_sweep_prior_archived",
     "report": "portable/tests/worldgen/evidence/randworld-seed-sweep-20261002.json", "archived": True},
    {"id": "worldgen_edge_8000_prior_archived",
     "report": "portable/tests/worldgen/evidence/randworld-edge-8000-20261002.json", "archived": True},
    {"id": "worldgen_edge_ffff_prior_archived",
     "report": "portable/tests/worldgen/evidence/randworld-edge-ffff-20261002.json", "archived": True},
    {
        "id": "map272",
        "report": "portable/tests/map/evidence/map-compose-dos-diff.json",
        "path_hash_maps": ["pinned_sources"],
        "command_fields": ["native_build_command"],
        "manifest_field": "identity.manifest_sha256",
        "oracle_field": "identity.oracle_sha256", "dos_count": "case_count",
    },
    {"id": "map_pre_game_view_archived",
     "report": "portable/tests/map/evidence/map-compose-dos-diff-pre-game-view-20261002.json",
     "archived": True},
    {
        "id": "population",
        "report": "portable/tests/population/evidence/countants-dos-diff.json",
        "path_hash_maps": ["pinned_sources"],
        "command_fields": ["native_build_command"],
        "manifest_field": "identity.manifest_sha256",
        "oracle_fields": ["identity.oracle_sha256", "oracle_sha256"], "dos_count": "case_count",
    },
    {
        "id": "setup_pinned_current",
        "report": "portable/tests/setup/evidence/setup_differential_pinned_report.json",
        "path_hash_maps": ["input_sha256"],
        "native_tus": ["portable/tests/setup/evidence/setup_native_adapter.c",
                       "portable/game/simulation/setup.c", "portable/ui_model/windows/registry.c",
                       "portable/ui_model/windows/window.c", "portable/game/resources/database.c",
                       "portable/render/bitmap.c", "portable/render/primitives.c"],
        "native": [("native_adapter_sha256", "portable/tests/setup/evidence/setup_native_adapter.c")],
        "asset_fields": [("database_ndx_sha256", "assets/HCEGANT.NDX"),
                         ("database_dat_sha256", "assets/HCEGANT.DAT")],
        "harness": [("machine_harness_sha256", "tools/behavior.py")],
        "oracle_field": "original_oracle_sha256", "dos_count": "setup_calls",
        "producer_fields": [("producer.path", "producer.sha256"),
                            ("producer_runner.path", "producer_runner.sha256")],
        "library": ("build.native_library_sha256", "portable/tests/setup/evidence/setup_native_adapter.dll"),
    },
    {"id": "setup_unpinned_prior_archived",
     "report": "portable/tests/setup/evidence/setup_differential_report.json", "archived": True},
    {
        "id": "registry",
        "report": "portable/tests/windows/evidence/differential_registry_report.json",
        "path_hash_maps": ["source_inputs"],
        "native_tus": ["portable/tests/windows/evidence/registry_native_adapter.c",
                       "portable/ui_model/windows/registry.c", "portable/ui_model/windows/window.c",
                       "portable/game/resources/database.c"],
        "asset_fields": [("database_ndx_sha256", "assets/HCEGANT.NDX"),
                         ("database_dat_sha256", "assets/HCEGANT.DAT")],
        "harness": [("machine_harness_sha256", "tools/behavior.py")],
        "producer": [("native_adapter_sha256", "portable/tests/windows/evidence/registry_native_adapter.c"),
                     ("compiler.sha256", "C:/msys64/mingw64/bin/gcc.exe")],
        "oracle_field": "original_oracle_sha256", "dos_count": "cases_count",
    },
    {
        "id": "rng",
        "report": "portable/tests/rng/rng-dos-differential.json",
        "native": [("native_source_sha256", "portable/game/simulation/rng.c"),
                   ("native_header_sha256", "portable/game/simulation/rng.h")],
        "native_tus": ["portable/game/simulation/rng.c"],
        "suite_path": "portable/tests/rng/original_dos_differential.py",
        "suite_hash_field": "suite_sha256",
        "harness": [("harness_sha256", "tools/behavior.py")],
        "oracle_field": "oracle.sha256", "dos_count": "rng_original_call_count",
    },
    {"id": "yellow_doantmovey_exitnest_5000",
     "report": "portable/tests/yellow/evidence/doantmovey-with-exit-nest-differential-5000.json",
     "path_hash_maps": ["native.source_sha256"],
     "command_fields": ["native.build_command"],
     "library_from_command": ("native", "build_command"),
     "manifest_field": "historical_manifest_sha256", "oracle_field": "oracle_sha256",
     "dos_count": "executed"},
    {"id": "yellow_exit_nest_direct_128",
     "report": "portable/tests/yellow/evidence/exit-nest-differential-128.json",
     "path_hash_maps": ["native.source_sha256"],
     "command_fields": ["native.build_command"],
     "library_from_command": ("native", "build_command"),
     "manifest_field": "historical_manifest_sha256", "oracle_field": "oracle_sha256",
     "dos_count": "executed"},
    {"id": "yellow_legacy_5000_archived",
     "report": "portable/tests/yellow/evidence/dos-differential-5000.json", "archived": True},
    {
        "id": "audio_decoder_57",
        "report": "portable/tests/audio/evidence/dos-decoder-differential.json",
        "path_hash_maps": ["current_source_pins"],
        "native_tus": ["portable/game/resources/database.c", "portable/audio/intent.c"],
        "asset_fields": [("assets.SOUND.NDX.sha256", "assets/SOUND.NDX"),
                         ("assets.SOUND.DAT.sha256", "assets/SOUND.DAT")],
        "oracle_field": "oracle.sha256", "dos_count": "record_count",
    },
    {
        "id": "bios_font_provider_diagnostic",
        "report": "portable/tests/windows/render/evidence/bios_font_provider_dos_diff.json",
        "audit_class": "controlled-provider-diagnostic",
        "scope": "Four direct glyph-provider calls; generated provider bytes and modeled graphics callback. Not physical DOS pixels or a historical BIOS-ROM claim.",
        "path_hash_maps": ["input_sha256"],
        "producer_fields": [("producer.path", "producer.sha256")],
        "command_fields": ["build.command"],
        "oracle_fields": ["oracle.oracle_sha256"],
        "dos_count": "cases_array_length",
    },
    {
        "id": "window_titles_source_mapped_model",
        "report": "portable/tests/windows/titles/title-model-evidence.json",
        "audit_class": "source-mapped-native-model-identity-only",
        "scope": "Native model test and source/resource identity only; no direct original-DOS execution is claimed.",
        "native": [
            ("implementation.source_sha256", "portable/ui_model/windows/titles.c"),
            ("implementation.header_sha256", "portable/ui_model/windows/titles.h"),
            ("validation.test_source_sha256", "portable/tests/windows/titles/test_titles.c"),
            ("source_facts.0.sha256", "src/root/m075B.c"),
            ("source_facts.1.sha256", "src/root/m0250.c"),
            ("source_facts.2.sha256", "src/root/m00F8.c"),
            ("source_facts.3.sha256", "src/root/m015B.c"),
            ("source_facts.4.sha256", "src/root/m22BF.c"),
        ],
        "asset_fields": [("resource_evidence.index_sha256", "assets/SHARED.NDX"),
                         ("resource_evidence.data_sha256", "assets/SHARED.DAT")],
        "library": ("validation.executable_sha256", "build/portable/tests/titles-test-final.exe"),
        "scope_only": True,
        "skip_dependency_closure": True,
        "requires_missing": ["title-model report does not pin the database implementation/header inputs used by its compiled test"],
    },
    {
        "id": "recovered_enter_nest_adapter_937",
        "report": "portable/tests/recovered/evidence/nest-adapter-diff.json",
        "audit_class": "direct-dos-adapter-differential",
        "scope": "937 EnterNest adapter cases including 128 dirt/grass cases. Generated mechanical state reuse remains diagnostic, not a historical source claim.",
        "path_hash_maps": ["native.source_sha256"],
        "native": [("native.library_sha256", "build/portable/recovered-nest-adapter.dll"),
                   ("generated_state_sha256", "build/workers/recovered_source/generated/recovered_state.h")],
        "native_tu_maps": ["native.source_sha256"],
        "command_fields": ["native.build_command"],
        "oracle_field": "oracle_sha256",
        "manifest_field": "historical_manifest_sha256",
        "dos_count": "executed",
        "related_documents": [
            {"path": "build/workers/recovered_source/generated/provenance.json",
             "file_pins": [("generator_sha256", "portable/tools/recover_source.py")]},
        ],
    },
    {
        "id": "doantsim_integer_bounds_rationale",
        "report": "portable/research/core-proof/doantsim-integer-promotion-review-20261002.json",
        "audit_class": "pinned-source-rationale-only",
        "scope": "Source-hash-pinned arithmetic bounds and excluded out-of-domain counterexamples; not a DOS differential or semantic-closure claim.",
        "path_hash_maps": ["source_sha256"],
        "scope_only": True,
        "skip_dependency_closure": True,
    },
    {
        "id": "feeding126",
        "report": "portable/tests/feeding/evidence/feeding-dos-diff-20261002.json",
        "native_hash_map": ("native_source_sha256", {
            "feeding.c": "portable/game/simulation/feeding.c", "feeding.h": "portable/game/simulation/feeding.h",
            "rng.c": "portable/game/simulation/rng.c", "native_probe.c": "portable/tests/feeding/native_probe.c"}),
        "unit_test": ("unit_test_sha256", "portable/tests/feeding/test_feeding.c"),
        "command_fields": ["native_command"],
        "native_tus": ["portable/tests/feeding/test_feeding.c"],
        "runner": [("runner_sha256", "portable/tests/feeding/evidence/run_dos_diff-20261002.py")],
        "harness_hash_map": ("harness_sha256", {
            "behavior": "tools/behavior.py", "exe": "tools/exe.py", "functions": "tools/functions.py", "match": "tools/match.py"}),
        "library": ("native_library_sha256", "build/portable/feeding-probe.dll"),
        "oracle_field": "oracle_exe_sha256", "dos_count": "executed_count",
    },
    {
        "id": "scent360",
        "report": "portable/tests/scent/evidence/scent-dos-diff-20261002.json",
        "native_hash_map": ("native_source_sha256", {
            "scent.c": "portable/game/simulation/scent.c", "scent.h": "portable/game/simulation/scent.h",
            "native_probe.c": "portable/tests/scent/native_probe.c"}),
        "unit_test": ("unit_test_sha256", "portable/tests/scent/test_scent.c"),
        "command_fields": ["native_command"],
        "native_tus": ["portable/tests/scent/test_scent.c"],
        "runner": [("runner_sha256", "portable/tests/scent/evidence/run_dos_diff-20261002.py")],
        "harness_hash_map": ("harness_sha256", {
            "behavior": "tools/behavior.py", "exe": "tools/exe.py", "functions": "tools/functions.py", "match": "tools/match.py"}),
        "library": ("native_library_sha256", "build/portable/scent-probe.dll"),
        "oracle_field": "oracle_exe_sha256", "dos_count": "executed_count",
    },
    {"id": "audio_source_only_archived",
     "report": "portable/tests/audio/evidence/source-only-report.json", "archived": True},
    {
        "id": "spider_superseded_mapping_bug",
        "report": "portable/tests/spider/evidence/native-dos-10146-SUPERSEDED-MAPPING-BUG.json",
        "archived": True,
    },
    {
        "id": "enternest_current_5937_20261002",
        "report": "portable/tests/evidence/current/20261002/enternest-5937.json",
        "native": [
            ("native.source_sha256", "portable/game/simulation/nest.c"),
            ("native.header_sha256", "portable/game/simulation/nest.h"),
            ("native.adapter_sha256", "portable/tests/nest/native_adapter.c"),
            ("native.library_sha256", "build/portable/nest.dll"),
        ],
        "command_fields": ["native.build_command"],
        "suite_path_field": "suite", "suite_hash_field": "suite_sha256",
        "harness": [("runner_sha256", "tools/behavior.py")],
        "manifest_field": "historical_manifest_sha256",
        "oracle_field": "oracle_sha256", "dos_count": "executed",
        "related_documents": [{
            "path": "portable/tests/evidence/current/20261002/source-stability-receipt.json",
            "source_maps": ["runs.0.inputs_before", "runs.0.inputs_after"],
            "hash_links": [("runs.0.report_sha256", "portable/tests/evidence/current/20261002/enternest-5937.json")],
            "file_pins": [("wrapper_sha256", "portable/tests/evidence/run-current-core-diffs-20261002.py")],
            "assertions": [("runs.0.source_stability", "stable"), ("runs.0.runner_exit_code", 0)],
        }],
    },
    {
        "id": "enternest_current_5937_rerun4_20261002",
        "report": "portable/tests/evidence/current/20261002/enternest-5937-rerun4.json",
        "native": [("native.source_sha256", "portable/game/simulation/nest.c"),
                   ("native.header_sha256", "portable/game/simulation/nest.h"),
                   ("native.adapter_sha256", "portable/tests/nest/native_adapter.c")],
        "command_fields": ["native.build_command"],
        "library_from_command": ("native", "build_command"),
        "suite_path_field": "suite", "suite_hash_field": "suite_sha256",
        "harness": [("runner_sha256", "tools/behavior.py")],
        "manifest_field": "historical_manifest_sha256", "oracle_field": "oracle_sha256",
        "dos_count": "executed",
        "related_documents": [{
            "path": "portable/tests/evidence/current/20261002/enternest-source-stability-rerun4.json",
            "source_maps": ["inputs_before", "inputs_after"],
            "hash_links": [("report_sha256", "portable/tests/evidence/current/20261002/enternest-5937-rerun4.json"),
                           ("library_sha256", "build/portable/current-20261002/nest-rerun4.dll")],
            "file_pins": [("producer_sha256", "portable/tests/evidence/run-enternest-rerun4-20261002.py")],
            "assertions": [("runner_exit_code", 0), ("source_stability", "stable")],
        }],
    },
    {
        "id": "spiderscan_current_10146_20261002",
        "report": "portable/tests/evidence/current/20261002/spiderscan-10146-complete.json",
        "native": [
            ("native_source_sha256", "portable/game/simulation/spider.c"),
            ("native_header_sha256", "portable/game/simulation/spider.h"),
            ("native_bridge_sha256", "portable/tests/spider/native_bridge.c"),
            ("native_library_sha256", "build/portable/spider-test.dll"),
        ],
        "command_fields": ["compile_command"],
        "suite_path_field": "archived_suite", "suite_hash_field": "suite_sha256",
        "harness": [("runner_sha256", "tools/behavior.py")],
        "oracle_field": "oracle_sha256", "dos_count": "cases",
        "related_documents": [{
            "path": "portable/tests/evidence/current/20261002/spiderscan-source-stability.json",
            "source_maps": ["inputs_before", "inputs_after"],
            "hash_links": [("report_sha256", "portable/tests/evidence/current/20261002/spiderscan-10146-complete.json")],
            "file_pins": [("producer_sha256", "portable/tests/evidence/run-spiderscan-complete-20261002.py")],
            "assertions": [("source_stability", "stable"), ("runner_exit_code", 0)],
        }],
    },
    {
        "id": "movespider_current_10146_20261002",
        "report": "portable/tests/evidence/current/20261002/movespider-10146.json",
        "path_hash_maps": ["source_hashes"],
        "native_tu_maps": ["source_hashes"],
        "library": ("native_library_sha256", "build/portable/spider-sim-test.dll"),
        "command_fields": ["compile_command"],
        "oracle_field": "oracle_sha256", "dos_count": "cases",
        "related_documents": [{
            "path": "portable/tests/evidence/current/20261002/source-stability-receipt.json",
            "source_maps": ["runs.2.inputs_before", "runs.2.inputs_after"],
            "hash_links": [("runs.2.report_sha256", "portable/tests/evidence/current/20261002/movespider-10146.json")],
            "file_pins": [("wrapper_sha256", "portable/tests/evidence/run-current-core-diffs-20261002.py")],
            "assertions": [("runs.2.source_stability", "stable"), ("runs.2.runner_exit_code", 0)],
        }],
    },
    {
        "id": "worldgen_union_current_sweep_20261002",
        "report": "portable/tests/worldgen/evidence/current/20261002/randworld-union-current-sweep-20261002.json",
        "path_hash_maps": ["native_source_hashes", "evidence_input_hashes"],
        "native": [("native_bridge_sha256", "portable/tests/worldgen/native_snapshot.c")],
        "native_tu_maps": ["native_source_hashes"],
        "command_fields": ["build_command"],
        "runner": [("runner_sha256", "portable/tests/worldgen/run_dos_diff.py")],
        "harness": [("harness_sha256", "tools/behavior.py")],
        "producer": [("compiler_sha256", "C:/msys64/mingw64/bin/gcc.exe")],
        "library_from_report": ("native_library_sha256", "native_library_path"),
        "oracle_fields": ["oracle_sha256", "oracle_identity.sha256"], "dos_count": "case_count",
        "related_documents": [{
            "path": "portable/tests/worldgen/evidence/current/20261002/source-stability-receipt.json",
            "source_maps": ["runs.0.inputs_before", "runs.0.inputs_after"],
            "hash_links": [("runs.0.report_sha256", "portable/tests/worldgen/evidence/current/20261002/randworld-union-current-sweep-20261002.json")],
            "file_pins": [("producer_sha256", "portable/tests/evidence/run-worldgen-current-20261002.py")],
            "assertions": [("runs.0.source_stability", "stable"), ("runs.0.runner_exit_code", 0)],
        }],
    },
    {
        "id": "worldgen_union_current_edge_8000_20261002",
        "report": "portable/tests/worldgen/evidence/current/20261002/randworld-union-current-edge-8000-20261002.json",
        "path_hash_maps": ["native_source_hashes", "evidence_input_hashes"],
        "native": [("native_bridge_sha256", "portable/tests/worldgen/native_snapshot.c")],
        "native_tu_maps": ["native_source_hashes"],
        "command_fields": ["build_command"],
        "runner": [("runner_sha256", "portable/tests/worldgen/run_dos_diff.py")],
        "harness": [("harness_sha256", "tools/behavior.py")],
        "producer": [("compiler_sha256", "C:/msys64/mingw64/bin/gcc.exe")],
        "library_from_report": ("native_library_sha256", "native_library_path"),
        "oracle_fields": ["oracle_sha256", "oracle_identity.sha256"], "dos_count": "case_count",
        "related_documents": [{
            "path": "portable/tests/worldgen/evidence/current/20261002/source-stability-receipt.json",
            "source_maps": ["runs.1.inputs_before", "runs.1.inputs_after"],
            "hash_links": [("runs.1.report_sha256", "portable/tests/worldgen/evidence/current/20261002/randworld-union-current-edge-8000-20261002.json")],
            "file_pins": [("producer_sha256", "portable/tests/evidence/run-worldgen-current-20261002.py")],
            "assertions": [("runs.1.source_stability", "stable"), ("runs.1.runner_exit_code", 0)],
        }],
    },
    {
        "id": "worldgen_union_current_edge_ffff_20261002",
        "report": "portable/tests/worldgen/evidence/current/20261002/randworld-union-current-edge-ffff-20261002.json",
        "path_hash_maps": ["native_source_hashes", "evidence_input_hashes"],
        "native": [("native_bridge_sha256", "portable/tests/worldgen/native_snapshot.c")],
        "native_tu_maps": ["native_source_hashes"],
        "command_fields": ["build_command"],
        "runner": [("runner_sha256", "portable/tests/worldgen/run_dos_diff.py")],
        "harness": [("harness_sha256", "tools/behavior.py")],
        "producer": [("compiler_sha256", "C:/msys64/mingw64/bin/gcc.exe")],
        "library_from_report": ("native_library_sha256", "native_library_path"),
        "oracle_fields": ["oracle_sha256", "oracle_identity.sha256"], "dos_count": "case_count",
        "related_documents": [{
            "path": "portable/tests/worldgen/evidence/current/20261002/source-stability-receipt.json",
            "source_maps": ["runs.2.inputs_before", "runs.2.inputs_after"],
            "hash_links": [("runs.2.report_sha256", "portable/tests/worldgen/evidence/current/20261002/randworld-union-current-edge-ffff-20261002.json")],
            "file_pins": [("producer_sha256", "portable/tests/evidence/run-worldgen-current-20261002.py")],
            "assertions": [("runs.2.source_stability", "stable"), ("runs.2.runner_exit_code", 0)],
        }],
    },
    {
        "id": "worldgen_union_current_rerun4_sweep",
        "report": "portable/tests/worldgen/evidence/current/20261002/randworld-union-current-sweep-rerun4-20261002.json",
        "path_hash_maps": ["native_source_hashes", "evidence_input_hashes"],
        "native": [("native_bridge_sha256", "portable/tests/worldgen/native_snapshot.c")],
        "native_tu_maps": ["native_source_hashes"], "command_fields": ["build_command"],
        "runner": [("runner_sha256", "portable/tests/worldgen/run_dos_diff.py")],
        "harness": [("harness_sha256", "tools/behavior.py")],
        "producer": [("compiler_sha256", "C:/msys64/mingw64/bin/gcc.exe")],
        "library_from_report": ("native_library_sha256", "native_library_path"),
        "oracle_fields": ["oracle_sha256", "oracle_identity.sha256"], "dos_count": "case_count",
        "related_documents": [{
            "path": "portable/tests/worldgen/evidence/current/20261002/source-stability-receipt-rerun4.json",
            "source_maps": ["runs.0.inputs_before", "runs.0.inputs_after"],
            "hash_links": [("runs.0.report_sha256", "portable/tests/worldgen/evidence/current/20261002/randworld-union-current-sweep-rerun4-20261002.json"),
                           ("runs.0.library_sha256", "portable/tests/worldgen/evidence/current/20261002/randworld-union-current-sweep-rerun4-20261002.dll")],
            "file_pins": [("producer_sha256", "portable/tests/evidence/run-worldgen-current-rerun4-20261002.py")],
            "assertions": [("runs.0.id", "sweep"), ("runs.0.runner_exit_code", 0),
                           ("runs.0.source_stability", "stable"), ("runs.0.mismatch_count", 0)],
        }],
    },
    {
        "id": "worldgen_union_current_rerun4_edge_8000",
        "report": "portable/tests/worldgen/evidence/current/20261002/randworld-union-current-edge-8000-rerun4-20261002.json",
        "path_hash_maps": ["native_source_hashes", "evidence_input_hashes"],
        "native": [("native_bridge_sha256", "portable/tests/worldgen/native_snapshot.c")],
        "native_tu_maps": ["native_source_hashes"], "command_fields": ["build_command"],
        "runner": [("runner_sha256", "portable/tests/worldgen/run_dos_diff.py")],
        "harness": [("harness_sha256", "tools/behavior.py")],
        "producer": [("compiler_sha256", "C:/msys64/mingw64/bin/gcc.exe")],
        "library_from_report": ("native_library_sha256", "native_library_path"),
        "oracle_fields": ["oracle_sha256", "oracle_identity.sha256"], "dos_count": "case_count",
        "related_documents": [{
            "path": "portable/tests/worldgen/evidence/current/20261002/source-stability-receipt-rerun4.json",
            "source_maps": ["runs.1.inputs_before", "runs.1.inputs_after"],
            "hash_links": [("runs.1.report_sha256", "portable/tests/worldgen/evidence/current/20261002/randworld-union-current-edge-8000-rerun4-20261002.json"),
                           ("runs.1.library_sha256", "portable/tests/worldgen/evidence/current/20261002/randworld-union-current-edge-8000-rerun4-20261002.dll")],
            "file_pins": [("producer_sha256", "portable/tests/evidence/run-worldgen-current-rerun4-20261002.py")],
            "assertions": [("runs.1.id", "edge-8000"), ("runs.1.runner_exit_code", 0),
                           ("runs.1.source_stability", "stable"), ("runs.1.mismatch_count", 0)],
        }],
    },
    {
        "id": "worldgen_union_current_rerun4_edge_ffff",
        "report": "portable/tests/worldgen/evidence/current/20261002/randworld-union-current-edge-ffff-rerun4-20261002.json",
        "path_hash_maps": ["native_source_hashes", "evidence_input_hashes"],
        "native": [("native_bridge_sha256", "portable/tests/worldgen/native_snapshot.c")],
        "native_tu_maps": ["native_source_hashes"], "command_fields": ["build_command"],
        "runner": [("runner_sha256", "portable/tests/worldgen/run_dos_diff.py")],
        "harness": [("harness_sha256", "tools/behavior.py")],
        "producer": [("compiler_sha256", "C:/msys64/mingw64/bin/gcc.exe")],
        "library_from_report": ("native_library_sha256", "native_library_path"),
        "oracle_fields": ["oracle_sha256", "oracle_identity.sha256"], "dos_count": "case_count",
        "related_documents": [{
            "path": "portable/tests/worldgen/evidence/current/20261002/source-stability-receipt-rerun4.json",
            "source_maps": ["runs.2.inputs_before", "runs.2.inputs_after"],
            "hash_links": [("runs.2.report_sha256", "portable/tests/worldgen/evidence/current/20261002/randworld-union-current-edge-ffff-rerun4-20261002.json"),
                           ("runs.2.library_sha256", "portable/tests/worldgen/evidence/current/20261002/randworld-union-current-edge-ffff-rerun4-20261002.dll")],
            "file_pins": [("producer_sha256", "portable/tests/evidence/run-worldgen-current-rerun4-20261002.py")],
            "assertions": [("runs.2.id", "edge-ffff"), ("runs.2.runner_exit_code", 0),
                           ("runs.2.source_stability", "stable"), ("runs.2.mismatch_count", 0)],
        }],
    },
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def norm_rel(value: str) -> str:
    value = value.replace("\\", "/")
    # Build logs sometimes pin absolute paths from the original Windows host.
    match = re.match(r"^[A-Za-z]:/(.*)$", value)
    if match:
        value = match.group(1)
        if value.lower().startswith("prog/simant_recon/"):
            value = value[len("Prog/simant_recon/"):]
    return value.lstrip("./")


def path_for(value: str) -> Path:
    p = Path(value)
    if p.is_absolute():
        return p
    return ROOT / norm_rel(value)


def get_field(obj: Any, dotted: str) -> Any:
    parts = dotted.split(".")
    cur = obj
    i = 0
    while i < len(parts):
        if isinstance(cur, list):
            cur = cur[int(parts[i])]
            i += 1
            continue
        if not isinstance(cur, dict):
            raise KeyError(dotted)
        # Asset and file maps commonly use dotted names such as SOUND.NDX.
        for end in range(len(parts), i, -1):
            joined = ".".join(parts[i:end])
            if joined in cur:
                cur = cur[joined]
                i = end
                break
        else:
            raise KeyError(dotted)
    return cur


def check_hash(checks: list[dict[str, Any]], missing: list[str], *, label: str,
               expected: Any, path: str) -> None:
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected):
        missing.append(f"{label}: no valid recorded SHA-256 pin")
        return
    p = path_for(path)
    if not p.is_file():
        missing.append(f"{label}: pinned input missing at {norm_rel(path)}")
        checks.append({"label": label, "path": norm_rel(path), "expected": expected,
                       "actual": None, "result": "MISSING"})
        return
    actual = sha256(p)
    checks.append({"label": label, "path": norm_rel(path), "expected": expected,
                   "actual": actual, "result": "MATCH" if actual == expected else "MISMATCH"})


def check_path_map(checks, missing, report, field):
    try:
        values = get_field(report, field)
    except (KeyError, IndexError, TypeError):
        missing.append(f"{field}: required path/hash map is absent")
        return
    if not isinstance(values, dict) or not values:
        missing.append(f"{field}: required path/hash map is empty or malformed")
        return
    for path, expected in values.items():
        check_hash(checks, missing, label=f"{field}:{path}", expected=expected, path=path)


def find_hash_path(expected: str, roots: list[str]) -> tuple[str | None, list[str]]:
    found: list[str] = []
    for root_name in roots:
        root = path_for(root_name)
        if not root.exists():
            continue
        iterator = [root] if root.is_file() else root.rglob("*")
        for p in iterator:
            if not p.is_file():
                continue
            try:
                if sha256(p) == expected:
                    found.append(p.relative_to(ROOT).as_posix())
            except OSError:
                continue
    found = sorted(set(found))
    return (found[0] if len(found) == 1 else None), found


INCLUDE_RE = re.compile(r'^\s*#\s*include\s*"([^"]+)"', re.MULTILINE)


def include_target(source: Path, include: str) -> Path | None:
    candidates = [source.parent / include, ROOT / "portable" / include,
                  ROOT / include, ROOT / "include" / include]
    for candidate in candidates:
        candidate = candidate.resolve()
        try:
            candidate.relative_to(ROOT.resolve())
        except ValueError:
            continue
        if candidate.is_file():
            return candidate
    return None


def check_cpp_dependency_closure(checks: list[dict[str, Any]], missing: list[str],
                                 tus: list[str] | None = None) -> list[dict[str, str]]:
    """Require project-local quoted includes of actual native TUs to be pinned."""
    pinned = {norm_rel(item["path"]).lower() for item in checks if item.get("path")}
    queue: list[Path] = []
    if tus is None:
        tus = [rel for rel in sorted(pinned) if rel.startswith("portable/") and rel.endswith(".c")]
    for raw in tus:
        p = path_for(raw).resolve()
        try:
            rel = p.relative_to(ROOT.resolve()).as_posix()
        except ValueError:
            missing.append(f"native translation unit escapes checkout: {raw}")
            continue
        if not p.is_file():
            missing.append(f"native translation unit missing: {norm_rel(raw)}")
            continue
        if rel.lower() not in pinned:
            missing.append(f"native translation unit lacks a recorded source hash: {rel}")
        queue.append(p)
    seen: set[str] = set()
    rows: list[dict[str, str]] = []
    while queue:
        source = queue.pop()
        source_rel = source.relative_to(ROOT).as_posix()
        key = source_rel.lower()
        if key in seen:
            continue
        seen.add(key)
        try:
            text = source.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            missing.append(f"include closure: unable to read {source_rel}: {exc}")
            continue
        for include in INCLUDE_RE.findall(text):
            target = include_target(source, include)
            if target is None:
                # Some preprocessor includes are generated by the external
                # compiler environment. They are reported but do not pretend
                # to be repository source headers.
                rows.append({"source": source_rel, "include": include, "result": "NOT_IN_REPOSITORY"})
                continue
            rel = target.relative_to(ROOT).as_posix()
            if rel.lower() not in pinned:
                rows.append({"source": source_rel, "include": rel, "result": "UNPINNED"})
                missing.append(f"unrecorded C/C++ dependency header/source: {rel} included by {source_rel}")
            else:
                rows.append({"source": source_rel, "include": rel, "result": "PINNED"})
            if target.suffix.lower() in (".h", ".hpp", ".hh"):
                queue.append(target)
    return rows


def dos_comparison_count(spec, report):
    field = spec.get("dos_count")
    if field is None:
        if spec.get("scope_only"):
            return 0, "Identity-only report; no original-DOS invocations are claimed."
        return None, "No explicit original-DOS comparison count was recorded."
    if field == "cases_array_length":
        try:
            return len(get_field(report, "cases")), "Counted direct-oracle case records."
        except (KeyError, TypeError):
            return None, "Report has no cases array."
    if field == "cases_count":
        try:
            return len(get_field(report, "cases")), "Counted case records in a DOS differential report."
        except (KeyError, TypeError):
            return None, "Report has no cases array."
    if field == "rng_original_call_count":
        try:
            masks = report["mask_functions"]
            # Count only recorded calls that executed the DOS oracle. Native
            # recurrence-only exhaustive rows are deliberately excluded.
            count = (masks["original_oracle_seeds_per_mask"] * len(masks["functions"])
                     + report["SRand1"]["original_oracle_cases"]
                     + report["SG_helpers"]["cases"]
                     + report["SeedSRand"]["cases"]
                     + report["SeedRRand_and_RRand"]["tick_pairs"]
                     * (1 + report["SeedRRand_and_RRand"]["rrand_draws_per_pair"])
                     + report["MSC_rand_arbitrary_state"]["states"]
                     + report["SetSRandSeed_GetSRandSeed"]["seeds"] * 2)
            return count, "Direct original DOS entry invocations only; native-only exhaustive recurrences excluded."
        except (KeyError, TypeError):
            return None, "RNG report lacks required direct-oracle count fields."
    if field == "render_original_call_count":
        try:
            count = (1 + report["type3_resource_1200"]["shift_cases"]
                     + len(report["font_FONT2"]["chars"])
                     + report["font_FONT2"]["string_cases"])
            return count, "Original DOS decoder/raster/width invocations; compared bytes/pixels are not mislabeled as calls."
        except (KeyError, TypeError):
            return None, "Render report lacks direct-original invocation counts."
    if field == "setup_calls":
        if "original_initControls_address" in report and "original_snapshot" in report:
            return 1, "One original initControls invocation represented by paired original/native snapshots."
        return None, "Setup report does not pin the original entry and paired snapshot."
    try:
        if isinstance(field, dict) and "sum" in field:
            return sum(int(get_field(report, item)) for item in field["sum"]), "Sum of report fields explicitly compared against original DOS output."
        return int(get_field(report, field)), f"Report field `{field}`."
    except (KeyError, TypeError, ValueError):
        return None, f"No usable DOS comparison count at `{field}`."


def audit(spec: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    missing: list[str] = []
    mismatches: list[str] = []
    report_path = path_for(spec["report"])
    base = {"id": spec["id"], "report": norm_rel(spec["report"]), "status": "INCOMPLETE",
            "checks": checks, "missing_or_unpinned": missing, "mismatches": mismatches}
    if not report_path.is_file():
        missing.append("evidence report file missing")
        return base
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        missing.append(f"evidence report unreadable: {exc}")
        return base
    base["report_sha256"] = sha256(report_path)
    base["report_schema"] = report.get("schema")
    base["recorded_report_status"] = report.get("status", report.get("evidence_status"))
    if spec.get("archived"):
        base["status"] = "ARCHIVED"
        base["reason"] = "Report is explicitly marked superseded/archived; it is retained for history and excluded from current proof."
        return base

    for field, path in spec.get("native", []):
        try:
            expected = get_field(report, field)
        except (KeyError, IndexError, TypeError):
            missing.append(f"{field}: native input hash was not recorded")
            continue
        check_hash(checks, missing, label=f"native:{field}", expected=expected, path=path)
    for field in spec.get("path_hash_maps", []):
        check_path_map(checks, missing, report, field)
    if "native_hash_map" in spec:
        field, mapping = spec["native_hash_map"]
        for key, path in mapping.items():
            try:
                expected = get_field(report, field)[key]
            except (KeyError, IndexError, TypeError):
                missing.append(f"{field}.{key}: native input hash was not recorded")
                continue
            check_hash(checks, missing, label=f"native:{key}", expected=expected, path=path)
    if "harness_hash_map" in spec:
        field, mapping = spec["harness_hash_map"]
        for key, path in mapping.items():
            try:
                expected = get_field(report, field)[key]
            except (KeyError, IndexError, TypeError):
                missing.append(f"{field}.{key}: harness input hash was not recorded")
                continue
            check_hash(checks, missing, label=f"harness:{key}", expected=expected, path=path)
    if "native_hash_map" in spec:
        field, mapping = spec["native_hash_map"]
        for key, path in mapping.items():
            try:
                expected = get_field(report, field)[key]
            except (KeyError, IndexError, TypeError):
                missing.append(f"{field}.{key}: native input hash was not recorded")
                continue
            check_hash(checks, missing, label=f"native:{key}", expected=expected, path=path)
    if spec.get("unit_test"):
        field, path = spec["unit_test"]
        try:
            expected = get_field(report, field)
        except (KeyError, IndexError, TypeError):
            missing.append(f"{field}: test/producer source hash was not recorded")
        else:
            check_hash(checks, missing, label=f"test:{field}", expected=expected, path=path)
    for field, path in spec.get("asset_fields", []):
        try:
            expected = get_field(report, field)
        except (KeyError, IndexError, TypeError):
            missing.append(f"{field}: asset hash was not recorded")
            continue
        check_hash(checks, missing, label=f"asset:{field}", expected=expected, path=path)

    producer_specs = list(spec.get("runner", [])) + list(spec.get("harness", [])) + list(spec.get("producer", []))
    for field, path in producer_specs:
        try:
            expected = get_field(report, field)
        except (KeyError, IndexError, TypeError):
            missing.append(f"{field}: producer/harness hash was not recorded")
            continue
        check_hash(checks, missing, label=f"producer:{field}", expected=expected, path=path)
    for path_field, hash_field in spec.get("producer_fields", []):
        try:
            producer_path = get_field(report, path_field)
            expected = get_field(report, hash_field)
        except (KeyError, IndexError, TypeError):
            missing.append(f"{path_field}/{hash_field}: linked producer path/hash was not recorded")
            continue
        check_hash(checks, missing, label=f"producer:{path_field}", expected=expected, path=producer_path)

    suite_field = spec.get("suite_hash_field")
    if suite_field:
        try:
            expected = get_field(report, suite_field)
        except (KeyError, IndexError, TypeError):
            missing.append(f"{suite_field}: suite hash was not recorded")
        else:
            suite_path = spec.get("suite_path")
            if not suite_path and spec.get("suite_path_field"):
                try:
                    suite_path = get_field(report, spec["suite_path_field"])
                except (KeyError, IndexError, TypeError):
                    missing.append(f"{spec['suite_path_field']}: suite path was not recorded")
            if suite_path:
                check_hash(checks, missing, label=f"suite:{suite_field}", expected=expected, path=suite_path)
            elif spec.get("suite_hash_search_roots"):
                found, all_found = find_hash_path(expected, spec["suite_hash_search_roots"])
                if found:
                    check_hash(checks, missing, label=f"suite:{suite_field}", expected=expected, path=found)
                    base.setdefault("resolved_producer_paths", []).append({"sha256": expected, "matches": all_found})
                else:
                    missing.append(f"{suite_field}: no unique matching suite in declared search roots; candidates={all_found}")
            else:
                missing.append(f"{suite_field}: producer path is not recorded and no resolver was declared")

    for field in spec.get("oracle_fields", [spec["oracle_field"]] if spec.get("oracle_field") else []):
        try:
            expected = get_field(report, field)
        except (KeyError, IndexError, TypeError):
            missing.append(f"{field}: oracle hash was not recorded")
            continue
        check_hash(checks, missing, label=f"oracle:{field}", expected=expected, path="assets/SIMANT.EXE")

    if spec.get("library"):
        field, path = spec["library"]
        try:
            expected = get_field(report, field)
        except (KeyError, IndexError, TypeError):
            missing.append(f"{field}: compiled native library hash was not recorded")
        else:
            check_hash(checks, missing, label=f"native-library:{field}", expected=expected, path=path)
    if spec.get("library_from_report"):
        hash_field, path_field = spec["library_from_report"]
        try:
            expected = get_field(report, hash_field)
            path = get_field(report, path_field)
            if not isinstance(path, str):
                raise TypeError("library path is not a string")
        except (KeyError, IndexError, TypeError):
            missing.append(f"{hash_field}/{path_field}: native library hash/path was not recorded")
        else:
            check_hash(checks, missing, label=f"native-library:{hash_field}",
                       expected=expected, path=path)
    if spec.get("library_from_command"):
        owner_field, command_field = spec["library_from_command"]
        try:
            owner = get_field(report, owner_field)
            command = get_field(owner, command_field)
            expected = owner["library_sha256"]
            output_at = command.index("-o")
            path = command[output_at + 1]
        except (KeyError, IndexError, TypeError, ValueError):
            missing.append(f"{owner_field}.{command_field}: native library hash/output path was not recorded")
        else:
            check_hash(checks, missing, label=f"native-library:{owner_field}.{command_field}",
                       expected=expected, path=path)

    if spec.get("manifest_field"):
        field = spec["manifest_field"]
        try:
            expected = get_field(report, field)
        except (KeyError, IndexError, TypeError):
            missing.append(f"{field}: linked historical manifest hash was not recorded")
        else:
            check_hash(checks, missing, label=f"historical-manifest:{field}", expected=expected,
                       path="layout/manifest.json")

    if spec.get("linked_report"):
        link = spec["linked_report"]
        try:
            sidecar = json.loads(path_for(link["path"]).read_text(encoding="utf-8"))
            expected = get_field(sidecar, link["field"])
        except (OSError, json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            missing.append(f"linked report {link['path']} unreadable or missing {link['field']}: {exc}")
        else:
            check_hash(checks, missing, label=f"linked-report:{link['field']}", expected=expected,
                       path=link["target"])
            if spec.get("linked_report_inputs"):
                check_path_map(checks, missing, sidecar, spec["linked_report_inputs"])

    for document_spec in spec.get("related_documents", []):
        try:
            if document_spec.get("path"):
                document_path = document_spec["path"]
            else:
                document_path = get_field(report, document_spec["path_field"])
            document = json.loads(path_for(document_path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            missing.append(f"related document {document_spec.get('path', document_spec.get('path_field'))} unreadable: {exc}")
            continue
        if document_spec.get("hash_field") and document_spec.get("path"):
            check_hash(checks, missing, label=f"related:{document_spec['path']}",
                       expected=get_field(report, document_spec["hash_field"]), path=document_path)
        for hash_field, target in document_spec.get("hash_links", []):
            try:
                expected = get_field(document, hash_field)
            except (KeyError, IndexError, TypeError):
                missing.append(f"{document_path}:{hash_field}: linked hash omitted")
                continue
            check_hash(checks, missing, label=f"related-link:{document_path}:{hash_field}",
                       expected=expected, path=target)
        for hash_field, target in document_spec.get("file_pins", []):
            try:
                expected = get_field(document, hash_field)
            except (KeyError, IndexError, TypeError):
                missing.append(f"{document_path}:{hash_field}: producer/source hash omitted")
                continue
            check_hash(checks, missing, label=f"related-pin:{document_path}:{hash_field}",
                       expected=expected, path=target)
        for map_field in document_spec.get("source_maps", []):
            check_path_map(checks, missing, document, map_field)
        if len(document_spec.get("source_maps", [])) >= 2:
            try:
                before = get_field(document, document_spec["source_maps"][0])
                after = get_field(document, document_spec["source_maps"][1])
                if before != after:
                    missing.append(f"{document_path}: source hashes changed during execution")
            except (KeyError, IndexError, TypeError):
                pass
        if document_spec.get("compare_maps_to_primary"):
            try:
                primary_map = get_field(report, document_spec["compare_maps_to_primary"])
                source_maps = document_spec.get("source_maps", [])
                normalize_map = lambda value: {
                    str(key).replace("\\", "/").casefold(): item
                    for key, item in value.items()
                }
                if source_maps and any(
                    normalize_map(get_field(document, f)) != normalize_map(primary_map)
                    for f in source_maps
                ):
                    missing.append(f"{document_path}: dependency receipt differs from the primary report source map")
            except (KeyError, IndexError, TypeError):
                missing.append(f"{document_path}: source-stability receipt cannot be compared to primary pins")
        for field, expected in document_spec.get("assertions", []):
            try:
                actual = get_field(document, field)
            except (KeyError, IndexError, TypeError):
                missing.append(f"{document_path}:{field}: required run-plan/receipt field absent")
                continue
            if actual != expected:
                missing.append(f"{document_path}:{field}: expected {expected!r}, got {actual!r}")

    count, count_basis = dos_comparison_count(spec, report)
    base["direct_original_dos_comparisons"] = {"count": count, "basis": count_basis}
    tus: list[str] = list(spec.get("native_tus", []))
    for field in spec.get("native_tu_maps", []):
        try:
            values = get_field(report, field)
        except (KeyError, IndexError, TypeError):
            missing.append(f"{field}: native TU source map missing")
            continue
        if isinstance(values, dict):
            tus.extend(path for path in values if norm_rel(path).lower().startswith("portable/")
                       and norm_rel(path).lower().endswith(".c"))
    for field in spec.get("command_fields", []):
        try:
            command = get_field(report, field)
        except (KeyError, IndexError, TypeError):
            missing.append(f"{field}: native build command missing")
            continue
        if isinstance(command, list):
            tus.extend(value for value in command if isinstance(value, str)
                       and value.lower().endswith(".c"))
    if not tus and not spec.get("native_tu_maps") and not spec.get("command_fields"):
        tus = None
    else:
        tus = list(dict.fromkeys(tus))
    dependency_rows = [] if spec.get("skip_dependency_closure") else check_cpp_dependency_closure(checks, missing, tus)
    base["cpp_dependency_closure"] = dependency_rows
    for check in checks:
        if check["result"] == "MISMATCH":
            mismatches.append(f"{check['label']} at {check['path']}: expected {check['expected']}, got {check['actual']}")
    if spec.get("requires_missing"):
        missing.extend(f"Required proof pin absent: {item}" for item in spec["requires_missing"])
    # A green report status is necessary but insufficient for a current pin audit.
    report_status = str(report.get("status", report.get("evidence_status", ""))).upper()
    if report_status and any(word in report_status for word in ("SUPERSEDED", "ARCHIVED", "BUG")):
        base["status"] = "ARCHIVED"
    elif mismatches:
        base["status"] = "STALE"
    elif missing or count is None or (count == 0 and not spec.get("scope_only")):
        base["status"] = "INCOMPLETE"
    elif report.get("mismatches", report.get("mismatch_count", 0)) not in (0, [], {}, None):
        base["status"] = "INCOMPLETE"
        missing.append("Report itself records nonzero or malformed mismatch state")
    elif report.get("mismatch_count", 0) != 0:
        base["status"] = "INCOMPLETE"
        missing.append("Report mismatch_count is not zero")
    else:
        base["status"] = "CURRENT"
    if spec.get("audit_class"):
        base["audit_class"] = spec["audit_class"]
    if spec.get("scope"):
        base["scope"] = spec["scope"]
    return base


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="write machine-readable audit JSON (default: build/native-proof-pin-audit.json)")
    parser.add_argument("--stdout", action="store_true", help="print JSON instead of writing the default output")
    args = parser.parse_args()
    results = [audit(spec) for spec in REPORTS]
    counts = {key: sum(row["status"] == key for row in results)
              for key in ("CURRENT", "STALE", "INCOMPLETE", "ARCHIVED")}
    result = {"schema": "native-dos-proof-input-pin-audit-v1",
              "scope": "read-only input identity audit; CURRENT is not a behavioral acceptance claim",
              "audit_script_sha256": sha256(Path(__file__).resolve()),
              "report_count": len(results), "status_counts": counts, "reports": results}
    rendered = json.dumps(result, indent=2) + "\n"
    if args.stdout:
        print(rendered, end="")
    else:
        out = args.output if args.output.is_absolute() else ROOT / args.output
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")
        print(f"wrote {out}")
        print(json.dumps(counts, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
