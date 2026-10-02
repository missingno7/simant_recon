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

# Reviewed finite reports added after the original 54-row inventory. Their
# schemas are deliberately kept separate from the historical registry above.
# These are input-identity records only; DIAGNOSTIC_ONLY and host-only reports
# remain labelled as such in `scope` and `recorded_report_status`.
REPORTS.extend([
    {
        "id": "native_unit_gate_43_20261002",
        "report": "portable/tests/evidence/native-unit-gate-43-20261002.json",
        "path_hash_maps": ["inputs"], "native_tu_maps": ["inputs"],
        "hash_resolvers": [{"field": "frozen_oracle_inputs.receipt_sha256",
                             "roots": ["portable/tests/evidence"]}],
        "scope_only": True,
        "metrics": [{"name": "native_suites_passed", "field": "tests", "operation": "len"}],
        "scope": "43 native host suites and integration checks; no direct-DOS acceptance claim.",
    },
    {
        "id": "next2_final_256_tick_replay_20261002",
        "report": "portable/research/core-proof/original-256-tick-summary-next2-lazy-clock-final-20261002.json",
        "path_hash_maps": ["final_replay_receipt_20261002.source_hashes_pre",
                           "final_replay_receipt_20261002.source_hashes_post",
                           "source_and_header_closure.files",
                           "fixture_and_profile_hashes_before",
                           "fixture_and_profile_hashes_after"],
        "native_tu_maps": ["source_and_header_closure.files"],
        "hash_fields": [("oracle_sha256", "assets/SIMANT.EXE"),
                        ("profile_hashes.recovered_state_header_sha256", "build/workers/recovered_source_next2/generated/recovered_state.h"),
                        ("profile_hashes.recovered_state_source_sha256", "build/workers/recovered_source_next2/generated/recovered_state.c"),
                        ("profile_hashes.recovered_native_adapters_sha256", "build/workers/recovered_source_next2/generated/recovered_native_adapters.c"),
                        ("profile_hashes.provenance_sha256", "build/workers/recovered_source_next2/generated/provenance.json"),
                        ("tool_hashes.native_tick_runner_sha256", "portable/tests/core/run_native_tick_fixture.py"),
                        ("current_engine_32tick_integration.integration_test_source_sha256", "portable/tests/core/engine_integration.c"),
                        ("current_engine_32tick_integration.integration_runner_sha256", "portable/tests/core/run_engine_integration.py")],
        "equal_hash_maps": [("final_replay_receipt_20261002.source_hashes_pre",
                             "final_replay_receipt_20261002.source_hashes_post"),
                            ("fixture_and_profile_hashes_before", "fixture_and_profile_hashes_after")],
        "assert_fields": [("final_replay_receipt_20261002.source_inputs_stable", True),
                           ("final_replay_receipt_20261002.changed_source_inputs", {}),
                           ("final_replay_receipt_20261002.unbaselined_inputs", []),
                           ("fixture_profile_stable", True)],
        "scope_only": True,
        "metrics": [{"name": "native_replay_cases", "field": "cases", "operation": "len"},
                     {"name": "native_tick_boundaries_compared", "field": "source_state.total_native_tick_comparisons", "operation": "value"}],
        "scope": "Final next2 replay reuses three preserved original DOS captures; 768 native ticks compare 370 captured globals and ordered normalized host traces, not new direct DOS executions.",
    },
    {
        "id": "next3_common370_replay_20261002",
        "report": "portable/research/core-proof/original-256-tick-summary-next3-common370-20261002.json",
        "path_hash_maps": ["source_stability.source_hashes_pre", "source_stability.source_hashes_post"],
        "native_tu_maps": ["source_stability.source_hashes_pre"],
        "runner": [("runner_sha256_stable", "portable/tests/core/next3_subset_replay.py")],
        "equal_hash_maps": [("source_stability.source_hashes_pre", "source_stability.source_hashes_post")],
        "assert_fields": [("source_stability.source_inputs_stable", True),
                           ("source_stability.changed_source_inputs", {}),
                           ("source_stability.unbaselined_inputs", [])],
        "scope_only": True,
        "metrics": [{"name": "native_replay_sequences", "field": "cases", "operation": "len"}],
        "scope": "Three 256-tick native replays against archived common-370 projections; uncaptured cue fields remain outside the comparison.",
    },
    {
        "id": "session_startup_setup_reset_146_20261002",
        "report": "portable/tests/core/evidence/randyard-session-startup-setup-reset-20261002.json",
        "path_hash_maps": ["pinned_input_sha256"],
        "native_tu_maps": ["pinned_input_sha256"],
        "hash_fields": [("native_sha256", "build/workers/session_startup_diff/setup-reset-next2/native.bin"),
                        ("native_executable_sha256", "build/workers/session_startup_diff/setup-reset-next2/session-startup-snapshot.exe")],
        "scope_only": True,
        "metrics": [{"name": "compared_state_ranges", "field": "compared_ranges", "operation": "value"}],
        "scope": "Diagnostic 146-range startup/setup-reset comparison; source says setup reset is tested, not full-session closure.",
    },
    {
        "id": "setup_data_init_controls_20261002",
        "report": "portable/tests/setup/evidence/setup_data_init_differential_report.json",
        "path_hash_maps": ["source_pins_before", "source_pins_after"],
        "native_tu_maps": ["source_pins_before"],
        "hash_fields": [("native_library_sha256", "portable/tests/setup/evidence/setup_native_adapter.dll"),
                        ("native_adapter_sha256", "portable/tests/setup/evidence/setup_native_adapter.c"),
                        ("machine_harness_sha256", "tools/behavior.py"),
                        ("original_oracle_sha256", "assets/SIMANT.EXE"),
                        ("database_ndx_sha256", "assets/HCEGANT.NDX"),
                        ("database_dat_sha256", "assets/HCEGANT.DAT")],
        "equal_hash_maps": [("source_pins_before", "source_pins_after")],
        "assert_fields": [("source_pins_stable", True), ("mismatch_count", 0)],
        "dos_count": "setup_calls",
        "metrics": [{"name": "original_initControls_calls", "field": "original_initControls_address", "operation": "one"}],
        "scope": "One original initControls execution with source-derived bitmap sizing and loaded-window fixture; not a full setup workflow.",
    },
    {
        "id": "setup_initcontrols_reuse_20261002",
        "report": "portable/tests/setup/evidence/setup_reuse_differential_report.json",
        "path_hash_maps": ["source_pins_before", "source_pins_after"],
        "native_tu_maps": ["source_pins_before"],
        "hash_fields": [("native_library_sha256", "portable/tests/setup/evidence/setup_native_adapter.dll"),
                        ("native_adapter_sha256", "portable/tests/setup/evidence/setup_native_adapter.c"),
                        ("behavior_harness_sha256", "tools/behavior.py"),
                        ("original_exe_sha256", "assets/SIMANT.EXE"),
                        ("ndx_sha256", "assets/HCEGANT.NDX"),
                        ("dat_sha256", "assets/HCEGANT.DAT"),
                        ("reuse_producer_sha256", "portable/tests/setup/evidence/setup_reuse_differential.py"),
                        ("default_producer_sha256", "portable/tests/setup/evidence/setup_differential.py")],
        "equal_hash_maps": [("source_pins_before", "source_pins_after")],
        "assert_fields": [("source_pins_stable", True), ("mismatch_count", 0)],
        "dos_count": "setup_calls",
        "metrics": [{"name": "fixture_windows", "field": "fixture_windows", "operation": "len"}],
        "scope": "Repeated initControls for windows 18/19 with mutated original selector tables; separate from a full RandYard/NewGame restart.",
    },
    {
        "id": "next4_controls_selected_source_20261002",
        "report": "portable/tests/recovered/evidence/controls-next4/report.json",
        "hash_fields": [("source.sha256", "src/root/m0798.c"),
                        ("oracle.executable_sha256", "assets/SIMANT.EXE"),
                        ("candidate.generator_sha256", "portable/tools/recover_source_next4.py"),
                        ("candidate.header_sha256", "build/workers/recovered_source_next4/generated/recovered_state.h"),
                        ("candidate.state_source_sha256", "build/workers/recovered_source_next4/generated/recovered_state.c"),
                        ("candidate.selected_tu_sha256", "build/workers/recovered_source_next4/generated/root_m0798_controls.c"),
                        ("candidate.native_probe_sha256", "build/workers/behavior_controls_next4/native_probe.c"),
                        ("candidate.native_probe_dll_sha256", "build/workers/behavior_controls_next4/native_probe.dll"),
                        ("inputs.ndx_sha256", "assets/HCEGANT.NDX"),
                        ("inputs.dat_sha256", "assets/HCEGANT.DAT"),
                        ("inputs.behavior_harness_sha256", "tools/behavior.py"),
                        ("inputs.setup_reuse_runner_sha256", "portable/tests/setup/evidence/setup_reuse_differential.py")],
        "native_tus": ["build/workers/recovered_source_next4/generated/root_m0798_controls.c"],
        "related_documents": [{
            "path": "portable/tests/recovered/evidence/controls-next4/profile-pins.json",
            "hash_links": [("report_sha256", "portable/tests/recovered/evidence/controls-next4/report.json")],
            "assertions": [("profile.all_24_module_compiles_passed", True),
                           ("profile.support_compile_passed", True),
                           ("profile.native_adapter_compile_passed", True)],
        }],
        "oracle_field": "oracle.executable_sha256", "dos_count": "domain.case_count",
        "metrics": [{"name": "directed_cases", "field": "domain.case_count", "operation": "value"}],
        "scope": "Diagnostic selected-source InitControls comparison, one case, with host services controlled; not behavioral acceptance or profile integration.",
    },
    {
        "id": "balloon_adapter_cues_164_20261002",
        "report": "portable/tests/recovered/evidence/balloon-adapter-dos/report.json",
        "hash_fields": [("source.sha256", "src/root/m0250.c"),
                        ("suite.sha256", "portable/tests/recovered/balloon_adapter_differential.py"),
                        ("model.sha256", "portable/ui_model/balloons/balloons.c"),
                        ("native_adapter.sha256", "portable/game/recovered/balloon_adapter.c"),
                        ("probe.sha256", "portable/tests/recovered/balloon_adapter_probe.c"),
                        ("native_probe_binary.sha256", "build/workers/behavior_text_card/balloon_adapter_diff/balloon_adapter_probe.dll"),
                        ("candidate_identity.oracle_sha256", "assets/SIMANT.EXE"),
                        ("candidate_identity.harness_sha256", "tools/behavior.py"),
                        ("candidate_identity.manifest_sha256", "layout/manifest.json")],
        "related_documents": [{
            "path": "portable/tests/recovered/evidence/balloon-adapter-dos/pins.json",
            "hash_links": [("artifacts.report.sha256", "portable/tests/recovered/evidence/balloon-adapter-dos/report.json"),
                           ("artifacts.case_ledger.sha256", "portable/tests/recovered/evidence/balloon-adapter-dos/balloon-adapter-cases.jsonl"),
                           ("artifacts.producer_snapshot.sha256", "portable/tests/recovered/evidence/balloon-adapter-dos/inputs/balloon_adapter_differential.py"),
                           ("artifacts.source_module_snapshot.sha256", "portable/tests/recovered/evidence/balloon-adapter-dos/inputs/m0250.c"),
                           ("artifacts.native_adapter_snapshot.sha256", "portable/tests/recovered/evidence/balloon-adapter-dos/inputs/balloon_adapter.c"),
                           ("artifacts.native_model_snapshot.sha256", "portable/tests/recovered/evidence/balloon-adapter-dos/inputs/balloons.c"),
                           ("artifacts.probe_source_snapshot.sha256", "portable/tests/recovered/evidence/balloon-adapter-dos/inputs/balloon_adapter_probe.c"),
                           ("artifacts.focused_native_test_snapshot.sha256", "portable/tests/recovered/evidence/balloon-adapter-dos/inputs/balloon_adapter_test.c"),
                           ("artifacts.oracle_lock_snapshot.sha256", "portable/tests/recovered/evidence/balloon-adapter-dos/inputs/oracle.lock.json"),
                           ("artifacts.manifest_snapshot.sha256", "portable/tests/recovered/evidence/balloon-adapter-dos/inputs/manifest.json"),
                           ("artifacts.behavior_harness_snapshot.sha256", "portable/tests/recovered/evidence/balloon-adapter-dos/inputs/behavior.py"),
                           ("artifacts.native_probe_binary.sha256", "portable/tests/recovered/evidence/balloon-adapter-dos/run/balloon_adapter_probe.dll"),
                           ("artifacts.prepared_candidate_object.sha256", "portable/tests/recovered/evidence/balloon-adapter-dos/run/candidate.obj"),
                           ("artifacts.candidate_identity.sha256", "portable/tests/recovered/evidence/balloon-adapter-dos/run/candidate-identity.json")],
            "assertions": [("run.executed_cases", 164), ("run.equal_dos_candidate", 164),
                           ("run.equal_native_dos", 164), ("run.execution_errors", 0)],
        }],
        "oracle_field": "candidate_identity.oracle_sha256", "dos_count": "case_count",
        "metrics": [{"name": "executed_cases", "field": "case_count", "operation": "value"}],
        "scope": "164 bounded egg/fight/queen/rest cue calls; not DrawCurBalloons or AddMsgBalloon proof.",
    },
    {
        "id": "end_game_flow_dos_native_5_20261002",
        "report": "portable/tests/dialogs/evidence/end-game-dos-native-flow-20261002.json",
        "path_hash_maps": ["source_pins", "source_pins_after"],
        "native_tu_maps": ["source_pins"],
        "equal_hash_maps": [("source_pins", "source_pins_after")],
        "assert_fields": [("status", "PASS")],
        "dos_count": "cases_count",
        "metrics": [{"name": "bounded_cases", "field": "cases", "operation": "len"}],
        "scope": "Five bounded EndGameDialog outcomes against original DOS with controlled window, event, wait, song, and audio services; no NewGame continuation.",
    },
    {
        "id": "scenario_flow_274_20261002",
        "report": "portable/tests/dialogs/evidence/scenario-flow-differential.json",
        "path_hash_maps": ["suite_inputs_sha256"],
        "native_tu_maps": ["suite_inputs_sha256"],
        "hash_fields": [("source.sha256", "src/S14/m384C.c"),
                        ("native_api.source_sha256", "portable/ui_model/dialogs/scenario_flow.c"),
                        ("native_api.header_sha256", "portable/ui_model/dialogs/scenario_flow.h"),
                        ("original_pair_identity.oracle_sha256", "assets/SIMANT.EXE"),
                        ("original_pair_identity.harness_sha256", "tools/behavior.py"),
                        ("original_pair_identity.manifest_sha256", "layout/manifest.json")],
        "dos_count": "cases.executed_original",
        "assert_fields": [("cases.executed_original", 274), ("cases.executed_native", 274),
                           ("cases.mismatches", 0)],
        "metrics": [{"name": "directed_event_cases", "field": "cases.directed", "operation": "value"}],
        "scope": "274 directed event-code cases for the scenario-flow model; no SDL rendering or full scenario startup claim.",
    },
    {
        "id": "scenario_modal_sdl_host_20261002",
        "report": "portable/tests/dialogs/evidence/scenario-modal-host.json",
        "path_hash_maps": ["assets_sha256", "build_receipt.inputs"],
        "native_tu_maps": ["build_receipt.inputs"],
        "hash_fields": [("harness_sha256", "portable/tests/dialogs/test_scenario_modal_host.c"),
                        ("runner_sha256", "portable/tests/dialogs/run_scenario_modal_host.py"),
                        ("module_sha256", "portable/platform/sdl3/scenario_modal.c"),
                        ("module_header_sha256", "portable/platform/sdl3/scenario_modal.h"),
                        ("flow_source_sha256", "portable/ui_model/dialogs/scenario_flow.c"),
                        ("flow_header_sha256", "portable/ui_model/dialogs/scenario_flow.h"),
                        ("build_receipt.compiler_sha256", "C:/msys64/mingw64/bin/gcc.exe")],
        "hash_resolvers": [{"field": "build_receipt_sha256", "roots": ["build/portable"]}],
        "scope_only": True,
        "metrics": [{"name": "host_cases", "field": "cases", "operation": "len"}],
        "scope": "Real SDL3 scenario modal host/input/restoration cases; explicitly not a DOS UI differential.",
    },
    {
        "id": "balloon_queue_addmsg_107_20261002",
        "report": "portable/tests/windows/evidence/balloon-queue-v1/run/addmsg/report.json",
        "hash_fields": [("source.sha256", "portable/tests/windows/evidence/balloon-queue-v1/source/module.c"),
                        ("native_model.sha256", "portable/ui_model/windows/balloon_queue.c"),
                        ("native_model.header_sha256", "portable/ui_model/windows/balloon_queue.h"),
                        ("native_model_binary.sha256", "portable/tests/windows/evidence/balloon-queue-v1/run/common/balloon_queue_model.dll"),
                        ("candidate_identity.oracle_sha256", "assets/SIMANT.EXE"),
                        ("candidate_identity.harness_sha256", "portable/tests/windows/evidence/balloon-queue-v1/inputs/behavior.py"),
                        ("candidate_identity.manifest_sha256", "portable/tests/windows/evidence/balloon-queue-v1/inputs/manifest.json"),
                        ("case_ledger.sha256", "portable/tests/windows/evidence/balloon-queue-v1/run/addmsg/cases.jsonl.gz")],
        "related_documents": [{
            "path": "portable/tests/windows/evidence/balloon-queue-v1/pins.json",
            "hash_links": [("runs.AddMsgBalloon.report.sha256", "portable/tests/windows/evidence/balloon-queue-v1/run/addmsg/report.json"),
                           ("runs.AddMsgBalloon.ledger.sha256", "portable/tests/windows/evidence/balloon-queue-v1/run/addmsg/cases.jsonl.gz"),
                           ("runs.AddMsgBalloon.candidate_identity.sha256", "portable/tests/windows/evidence/balloon-queue-v1/run/addmsg/candidate-identity.json"),
                           ("common.source_snapshot.sha256", "portable/tests/windows/evidence/balloon-queue-v1/source/module.c"),
                           ("common.drawballoons_logical_render_evidence.sha256", "portable/tests/windows/evidence/balloon-queue-v1/source/drawballoons-logical-render-evidence.json"),
                           ("native_model.compiled_probe.sha256", "portable/tests/windows/evidence/balloon-queue-v1/run/common/balloon_queue_model.dll"),
                           ("producers.AddMsgBalloon_runner.sha256", "portable/tests/windows/evidence/balloon-queue-v1/inputs/balloon_queue_differential.py"),
                           ("producers.behavior_harness_snapshot.sha256", "portable/tests/windows/evidence/balloon-queue-v1/inputs/behavior.py"),
                           ("producers.case_ledger_producer.sha256", "portable/tests/windows/evidence/balloon-queue-v1/inputs/behavior_ledger.py"),
                           ("producers.oracle_lock_snapshot.sha256", "portable/tests/windows/evidence/balloon-queue-v1/inputs/oracle.lock.json"),
                           ("producers.manifest_snapshot.sha256", "portable/tests/windows/evidence/balloon-queue-v1/inputs/manifest.json"),
                           ("native_model.header_sha256", "portable/tests/windows/evidence/balloon-queue-v1/inputs/balloon_queue.h"),
                           ("native_model.balloons_dependency_sha256", "portable/tests/windows/evidence/balloon-queue-v1/inputs/balloons.c"),
                           ("native_model.balloons_header_sha256", "portable/tests/windows/evidence/balloon-queue-v1/inputs/balloons.h")],
            "file_pins": [("native_model.header_sha256", "portable/ui_model/windows/balloon_queue.h"),
                          ("native_model.balloons_dependency_sha256", "portable/ui_model/balloons/balloons.c"),
                          ("native_model.balloons_header_sha256", "portable/ui_model/balloons/balloons.h")],
            "assertions": [("runs.AddMsgBalloon.ledger.rows", 107),
                           ("runs.AddMsgBalloon.totals.dos_candidate_equal", 107),
                           ("runs.AddMsgBalloon.totals.native_dos_equal", 107)],
        }],
        "oracle_field": "candidate_identity.oracle_sha256", "dos_count": "case_count",
        "metrics": [{"name": "bounded_cases", "field": "case_count", "operation": "value"}],
        "scope": "107 bounded AddMsgBalloon logical queue cases; not a full renderer or physical UI result.",
    },
    {
        "id": "balloon_drawcur_55_20261002",
        "report": "portable/tests/windows/evidence/balloon-queue-v1/run/drawcur/report.json",
        "hash_fields": [("source.sha256", "portable/tests/windows/evidence/balloon-queue-v1/source/module.c"),
                        ("model.sha256", "portable/ui_model/windows/balloon_queue.c"),
                        ("candidate_identity.oracle_sha256", "assets/SIMANT.EXE"),
                        ("candidate_identity.harness_sha256", "portable/tests/windows/evidence/balloon-queue-v1/inputs/behavior.py"),
                        ("candidate_identity.manifest_sha256", "portable/tests/windows/evidence/balloon-queue-v1/inputs/manifest.json"),
                        ("case_ledger.sha256", "portable/tests/windows/evidence/balloon-queue-v1/run/drawcur/cases.jsonl.gz")],
        "related_documents": [{
            "path": "portable/tests/windows/evidence/balloon-queue-v1/pins.json",
            "hash_links": [("runs.DrawCurBalloons.report.sha256", "portable/tests/windows/evidence/balloon-queue-v1/run/drawcur/report.json"),
                           ("runs.DrawCurBalloons.ledger.sha256", "portable/tests/windows/evidence/balloon-queue-v1/run/drawcur/cases.jsonl.gz"),
                           ("runs.DrawCurBalloons.candidate_identity.sha256", "portable/tests/windows/evidence/balloon-queue-v1/run/drawcur/candidate-identity.json"),
                           ("producers.DrawCurBalloons_runner.sha256", "portable/tests/windows/evidence/balloon-queue-v1/inputs/balloon_draw_current_differential.py"),
                           ("native_model.header_sha256", "portable/tests/windows/evidence/balloon-queue-v1/inputs/balloon_queue.h"),
                           ("native_model.balloons_dependency_sha256", "portable/tests/windows/evidence/balloon-queue-v1/inputs/balloons.c"),
                           ("native_model.balloons_header_sha256", "portable/tests/windows/evidence/balloon-queue-v1/inputs/balloons.h")],
            "file_pins": [("native_model.header_sha256", "portable/ui_model/windows/balloon_queue.h"),
                          ("native_model.balloons_dependency_sha256", "portable/ui_model/balloons/balloons.c"),
                          ("native_model.balloons_header_sha256", "portable/ui_model/balloons/balloons.h")],
            "assertions": [("runs.DrawCurBalloons.ledger.rows", 55),
                           ("runs.DrawCurBalloons.totals.dos_candidate_equal", 55),
                           ("runs.DrawCurBalloons.totals.native_dos_equal", 55)],
        }],
        "oracle_field": "candidate_identity.oracle_sha256", "dos_count": "case_count",
        "metrics": [{"name": "bounded_cases", "field": "case_count", "operation": "value"}],
        "scope": "55 bounded DrawCurBalloons logical queue cases; not pixels or physical backend effects.",
    },
    {
        "id": "end_game_modal_smoke_next4_sdl_20261002",
        "report": "portable/tests/live_game/evidence/end-game-modal-smoke-next4.json",
        "path_hash_maps": ["input_pins.source_and_transitive_header_sha256",
                           "input_pins.recovered_core_object_sha256",
                           "production_build_receipt.inputs"],
        "native_tu_maps": ["input_pins.source_and_transitive_header_sha256",
                            "production_build_receipt.inputs"],
        "hash_fields": [("production_executable_sha256", "build/portable/simant-sdl3.exe"),
                        ("smoke_executable_sha256", "build/portable/tests/simant-live-endgame-smoke.exe"),
                        ("test_event_driver.sha256", "portable/tests/live_game/end_game_key_injector.c"),
                        ("modal_frame.sha256", "portable/tests/live_game/evidence/end-game-modal-smoke-next4-modal.bmp"),
                        ("closed_frame.sha256", "portable/tests/live_game/evidence/end-game-modal-smoke-next4-closed.bmp"),
                        ("production_build_receipt.compiler_sha256", "C:/msys64/mingw64/bin/gcc.exe")],
        "hash_resolvers": [{"field": "build_receipt_sha256", "roots": ["build/portable"]}],
        "assert_fields": [("input_pins.production_receipt_inputs_match", True),
                           ("input_pins.source_and_transitive_header_pins_stable", True),
                           ("details.opened", True), ("details.closed", True),
                           ("details.logical_key", 27), ("details.rendered_modal_frames", 1),
                           ("returncode", 0)],
        "related_documents": [{
            "path": "portable/tests/live_game/evidence/end-game-modal-smoke-next4.endgame.json",
            "assertions": [("opened", True), ("closed", True),
                           ("restart_boundary_reached", True), ("logical_key", 27),
                           ("rendered_modal_frames", 1), ("audio_driver_ready", 0)],
        }],
        "scope_only": True,
        "metrics": [{"name": "rendered_modal_frames", "field": "details.rendered_modal_frames", "operation": "value"}],
        "scope": "Live next4 SDL EndGame host smoke through Escape/close to explicit unsupported NewGame(option=0); not DOS pixel equivalence or restart closure.",
    },
    {
        "id": "newgame_controlled_flow_next5_130_20261002",
        "report": "portable/tests/recovered/evidence/newgame-flow-next5/run/report.json",
        "hash_fields": [("oracle_sha256", "assets/SIMANT.EXE"),
                        ("harness_sha256", "tools/behavior.py"),
                        ("source.sha256", "src/S15/m384C.c"),
                        ("next5.wrapper_sha256", "portable/tools/recover_source_next5.py"),
                        ("next5.profile_provenance_sha256", "build/workers/recovered_source_next5/generated/provenance.json"),
                        ("next5.selected_source_sha256", "build/workers/recovered_source_next5/generated/root_m384C_newgame.c"),
                        ("next5.state_header_sha256", "build/workers/recovered_source_next5/generated/recovered_state.h"),
                        ("next5.state_source_sha256", "build/workers/recovered_source_next5/generated/recovered_state.c"),
                        ("next5.native_probe_sha256", "portable/tests/recovered/newgame_flow_probe.c"),
                        ("next5.native_library_sha256", "build/workers/behavior_newgame_next5/native.dll"),
                        ("ledger.sha256", "build/workers/behavior_newgame_next5/flow/cases.jsonl.gz")],
        "native_tus": ["build/workers/recovered_source_next5/generated/root_m384C_newgame.c"],
        "related_documents": [{
            "path": "portable/tests/recovered/evidence/newgame-flow-next5/pins.json",
            "hash_rows": {"root": "portable/tests/recovered/evidence/newgame-flow-next5",
                          "current_paths": {
                              "inputs/newgame_flow_differential.py": "portable/tests/recovered/newgame_flow_differential.py",
                              "inputs/newgame_flow_probe.c": "portable/tests/recovered/newgame_flow_probe.c",
                              "inputs/m384C.c": "src/S15/m384C.c",
                              "inputs/recover_source_next5.py": "portable/tools/recover_source_next5.py",
                          }},
        }],
        "assert_fields": [("all_equal", True),
                          ("status", "DIAGNOSTIC_ONLY_NOT_BEHAVIOR_ACCEPTANCE"),
                          ("domain.newgame_cases", 128),
                          ("domain.direct_setdefault_cases", 2),
                          ("ledger.row_count", 130),
                          ("domain.implicit_ax.native_service_input_records_replay_actual_original_entry_AX", True),
                          ("domain.randyard_boundary.whole_randyard_claim", False)],
        "dos_count": {"sum": ["domain.newgame_cases", "domain.direct_setdefault_cases"]},
        "metrics": [{"name": "newgame_cases", "field": "domain.newgame_cases", "operation": "value"},
                    {"name": "setdefault_cases", "field": "domain.direct_setdefault_cases", "operation": "value"},
                    {"name": "equal_case_rows", "field": "ledger.row_count", "operation": "value"}],
        "scope": "130 controlled original-DOS flow cases (128 NewGame, 2 SetDefaultWindows); native replays actual DOS AX values at two volatile helper-service boundaries. Typed services control modal/window/resource/LoadGame/RandYard effects; not independently generated native AX, RandYard/worldgen, or BEHAVIOR_EXACT acceptance.",
    },
    {
        "id": "session_bridge_next4_stored_dos_reference_20261002",
        "report": "portable/tests/recovered/evidence/session-bridge-next4-report.json",
        "path_hash_maps": ["input_hashes_before", "input_hashes_after"],
        "native_tu_maps": ["input_hashes_before"],
        "hash_fields": [("original_dos_controls_reference.sha256", "portable/tests/setup/evidence/setup_differential_report.json"),
                        ("original_dos_controls_reference.oracle_executable_sha256", "assets/SIMANT.EXE"),
                        ("profile.header_sha256", "build/workers/recovered_source_next4/generated/recovered_state.h"),
                        ("profile.state_source_sha256", "build/workers/recovered_source_next4/generated/recovered_state.c"),
                        ("profile.provenance_sha256", "build/workers/recovered_source_next4/generated/provenance.json"),
                        ("test.sha256", "portable/tests/recovered/session_bridge_next4_test.c"),
                        ("bridge.sha256", "portable/game/recovered/session_bridge.c")],
        "equal_hash_maps": [("input_hashes_before", "input_hashes_after")],
        "assert_fields": [("status", "PASS"), ("claim_boundary", "Resource-backed native Session NewGame values are compared to the original DOS initControls snapshot from setup_differential_report.json, then tested through next4 RecoveredState projection and typed Session export. This integration test does not rerun the DOS oracle."),
                          ("original_dos_controls_reference.mismatch_count", 0),
                          ("input_stability", True), ("compile.exit_code", 0), ("run.exit_code", 0)],
        "scope_only": True,
        "metrics": [{"name": "stored_original_dos_reference_mismatches", "field": "original_dos_controls_reference.mismatch_count", "operation": "value"}],
        "scope": "Native Session/RecoveredState/export integration reads a previously stored initControls DOS report as its reference; it does not execute the DOS oracle or establish restart behavior. CURRENT only means the stored-reference and build-input identities still match.",
    },
    {
        "id": "next7_captured370_replay_20261002",
        "report": "portable/research/core-proof/original-256-tick-summary-next7-captured370-20261002.json",
        "path_hash_maps": ["source_stability.source_hashes_pre"],
        "native_tu_maps": ["source_stability.source_hashes_pre"],
        "native_tu_map_prefixes": ["build/workers/recovered_source_next7/generated/"],
        "equal_hash_maps": [("source_stability.source_hashes_pre", "source_stability.source_hashes_post")],
        "assert_fields": [("source_stability.source_inputs_stable", True),
                          ("source_stability.preserved_captures_stable", True),
                          ("source_stability.runner_sha256_pre_post", "17daea4df042e064a7e7f0efcf05952cf58d9ba196a86e95d36214c6341e0d5b"),
                          ("source_stability.producer_sha256_pre_post", "caa522691cb595e61709e5ba911fbbe87da1f77ce0c9aa21a7e9493c513549c3"),
                          ("scope", "370 captured DOS fields only; 41 other NEXT7 state fields are explicitly excluded from DOS assertion"),
                          ("capture_reuse", "Three preserved DOS captures reused; zero fresh original DOS executions.")],
        "replay_capture_files": {"case_field": "cases", "root": "build/workers/core_proof_next7",
                                 "snapshot_root": "."},
        "host_list_assertions": [{"field": "cases", "length": 3, "item_field": "exit_code", "equals": 0},
                                 {"field": "cases", "item_field": "status",
                                  "equals": "PASS 256/256 captured-370 subset"}],
        "scope_only": True,
        "metrics": [{"name": "native_replay_ticks", "field": "cases", "operation": "len_times", "factor": 256},
                    {"name": "replay_fixtures", "field": "cases", "operation": "len"},
                    {"name": "excluded_fields", "field": "next7_uncaptured_fields", "operation": "len"}],
        "scope": "Three 256-tick native replays compare a 370-field subset against preserved DOS captures. They represent 768 native replay boundaries, not new DOS executions; 41 NEXT7 fields remain outside the captured DOS assertion. Current means the recorded source/profile/build-input identities and preserved capture files still match.",
        "audit_class": "captured_dos_replay_zero_new_dos_calls",
    },
    {
        "id": "menu_interaction_13_dos_native_20261002",
        "report": "portable/tests/menus/evidence/menu-interaction-differential.json",
        "hash_fields": [("target.source_sha256", "work/takeover/hardtail/seeds/S10_35F5_4b9dda15dbea.c"),
                        ("native.source_sha256", "portable/ui_model/menus/interaction.c"),
                        ("native.fixture_sha256", "portable/tests/menus/menu_interaction_fixture.c"),
                        ("native.resource_harness_sha256", "portable/tests/menus/test_menu_interaction.c")],
        "harness": [("target.harness_sha256", "tools/behavior.py")],
        "manifest_field": "target.manifest_sha256",
        "oracle_field": "target.oracle_sha256",
        "native_tus": ["portable/ui_model/menus/interaction.c", "portable/tests/menus/menu_interaction_fixture.c",
                       "portable/tests/menus/test_menu_interaction.c"],
        "hash_resolvers": [{"field": "native.shared_library_sha256", "roots": ["build/portable/menu-interaction-differential"]}],
        "assert_fields": [("status", "PASS"), ("cases.executed_original", 13),
                          ("cases.executed_native", 13), ("cases.mismatches", 0)],
        "dos_count": "cases.executed_original",
        "requires_missing": ["runner source/hash absent from report; actual source/fixture/test and transitive quoted includes are audited, but runner identity cannot be asserted"],
        "scope": "13 direct DOS and 13 native menu-interaction cases. The finite title-menu path is covered; popup/context geometry, event collection, and raster drawing remain outside this comparison.",
        "audit_class": "direct_dos_native_comparison_with_missing_runner_pin",
    },
    {
        "id": "menu_quit_18_dos_native_20261002",
        "report": "portable/tests/dialogs/evidence/menu-quit-dos-native-20261002.json",
        "path_hash_maps": ["inputs_sha256"],
        "native_tus": ["portable/ui_model/dialogs/menu_quit.c", "portable/game/resources/database.c",
                       "portable/tests/dialogs/menu_quit_probe.c", "portable/tests/dialogs/test_menu_quit.c"],
        "hash_fields": [("oracle.harness_sha256", "tools/behavior.py")],
        "oracle_field": "oracle.exe_sha256",
        "related_documents": [{
            "path": "portable/tests/dialogs/evidence/menu-quit-dos-native-v1/pins.json",
            "hash_rows": {"root": "portable/tests/dialogs/evidence/menu-quit-dos-native-v1",
                          "external_paths": {"assets/SHARED.DAT": "assets/SHARED.DAT",
                                             "assets/SHARED.NDX": "assets/SHARED.NDX"},
                          "current_paths": {
                              "inputs/menu_quit.c": "portable/ui_model/dialogs/menu_quit.c",
                              "inputs/menu_quit.h": "portable/ui_model/dialogs/menu_quit.h",
                              "inputs/database.c": "portable/game/resources/database.c",
                              "inputs/database.h": "portable/game/resources/database.h",
                              "inputs/menu_quit_probe.c": "portable/tests/dialogs/menu_quit_probe.c",
                              "inputs/menu_quit_probe.h": "portable/tests/dialogs/menu_quit_probe.h",
                              "inputs/test_menu_quit.c": "portable/tests/dialogs/test_menu_quit.c",
                              "inputs/run_menu_quit_differential.py": "portable/tests/dialogs/run_menu_quit_differential.py",
                              "inputs/original_S15_m384C.c": "src/S15/m384C.c",
                              "inputs/behavior.py": "tools/behavior.py",
                              "assets/SHARED.DAT": "assets/SHARED.DAT",
                              "assets/SHARED.NDX": "assets/SHARED.NDX",
                              "run/cases.jsonl.gz": "portable/tests/dialogs/evidence/menu-quit-dos-native-20261002.jsonl.gz"}}}],
        "assert_fields": [("status", "PASS"), ("counts.cases", 18), ("counts.executed_dos", 18),
                          ("counts.executed_native", 18), ("counts.mismatches", 0)],
        "dos_count": "counts.executed_dos",
        "scope": "18 direct DOS/native MenuQuit flow cases, including save dirty-state clearing and prompt retry semantics. Disk I/O, real windows/input, and process termination are controlled host boundaries.",
        "audit_class": "direct_dos_native_flow_with_archived_21_pin_snapshot",
    },
    {
        "id": "windows_zoom_toggle_13_diagnostic_20261002",
        "report": "portable/tests/windows_zoom/evidence/toggle-v1.json",
        "hash_fields": [("source_sha256", "src/S26/m39C7.c"),
                        ("model_source_sha256", "portable/ui_model/windows/zoom.c"),
                        ("model_header_sha256", "portable/ui_model/windows/zoom.h"),
                        ("native_test_source_sha256", "portable/tests/windows_zoom/test_zoom.c")],
        "runner": [("runner_sha256", "portable/tests/windows_zoom/dos_toggle_diff.py")],
        "harness": [("harness_sha256", "tools/behavior.py")],
        "oracle_field": "oracle_sha256",
        "native_tus": ["portable/ui_model/windows/zoom.c", "portable/tests/windows_zoom/test_zoom.c"],
        "hash_resolvers": [{"field": "native_model_library_sha256", "roots": ["build/portable/windows-zoom"]}],
        "assert_fields": [("status", "DIAGNOSTIC_ONLY"), ("case_count", 13), ("mismatches", 0)],
        "dos_count": "case_count",
        "scope": "13 direct DOS/native zoom-toggle observations. Controlled window/frame/draw services and captured DOS stack residue are replayed; this remains diagnostic evidence, not full UI equivalence.",
        "audit_class": "diagnostic_direct_dos_native_comparison",
    },
    {
        "id": "windows_zoom_constrain_8_diagnostic_20261002",
        "report": "portable/tests/windows_zoom/evidence/constrain-v1.json",
        "hash_fields": [("source_sha256", "src/S26/m39C7.c"),
                        ("model_source_sha256", "portable/ui_model/windows/zoom.c"),
                        ("model_header_sha256", "portable/ui_model/windows/zoom.h"),
                        ("native_test_source_sha256", "portable/tests/windows_zoom/test_zoom.c")],
        "runner": [("runner_sha256", "portable/tests/windows_zoom/dos_constrain_diff.py")],
        "harness": [("harness_sha256", "tools/behavior.py")],
        "oracle_field": "oracle_sha256",
        "native_tus": ["portable/ui_model/windows/zoom.c", "portable/tests/windows_zoom/test_zoom.c"],
        "hash_resolvers": [{"field": "native_model_library_sha256", "roots": ["build/portable/windows-zoom"]}],
        "assert_fields": [("status", "DIAGNOSTIC_ONLY"), ("case_count", 8), ("mismatches", 0)],
        "dos_count": "case_count",
        "scope": "Eight direct DOS/native window-rectangle constrain observations. Controlled window-service calls and geometry are compared; this remains a bounded diagnostic, not general window-manager equivalence.",
        "audit_class": "diagnostic_direct_dos_native_comparison",
    },
    {
        "id": "newgame_zoom_abi_16_original_dos_observations_20261002",
        "report": "portable/tests/recovered/evidence/newgame-zoom-abi/report.json",
        "path_hash_maps": ["pinned_inputs"],
        "oracle_field": "oracle.sha256",
        "assert_fields": [("status", "BOUNDED_ORIGINAL_DOS_ABI_OBSERVATION"), ("scope.cases", 16),
                          ("mismatches", [])],
        "dos_count": "scope.cases",
        "scope": "16 original-DOS call-entry observations for the NewGame zoom-query ABI (four planes by two NewGame flags, with paired window states). This is an original DOS observation only, not a native comparison or full NewGame claim.",
        "audit_class": "original_dos_abi_observations_no_native_lane",
    },
    {
        "id": "live_forced_next7_gameover_smoke_20261002",
        "report": "portable/tests/live_game/evidence/newgame-202-live-smoke-forced-next7.json",
        "path_hash_maps": ["source_and_transitive_header_sha256_before"],
        "equal_hash_maps": [("production_executable_sha256_before", "production_executable_sha256_after"),
                            ("production_build_receipt_sha256_before", "production_build_receipt_sha256_after")],
        "assert_fields": [("status", "PASS"), ("source_pins_stable", True), ("timed_out", False),
                          ("returncode", 0), ("source_newgame_report.diagnostic_action_called", True),
                          ("source_newgame_report.scenario_result_code", 514)],
        "hash_resolvers": [{"field": "smoke_executable_sha256", "roots": ["build/portable/tests"]}],
        "scope_only": True,
        "metrics": [{"name": "host_smoke_returncode", "field": "returncode", "operation": "value"},
                    {"name": "native_ticks", "field": "native_state_report.completed_ticks", "operation": "value"}],
        "scope": "One forced diagnostic game-over action reached a real SDL modal and accepted a physical click. This is a host smoke only: no direct DOS call, no naturally reached game-over state, and no full game-play claim.",
        "audit_class": "host_only_forced_scenario_no_dos_comparison",
    },
    {
        "id": "native_gate_46_and_sdl_host_20261002",
        "report": "portable/tests/evidence/current/20261002/native-gate-46-host-20261002.json",
        "path_hash_maps": ["inputs", "sdl3_host.receipt.build_receipt.inputs"],
        "opaque_artifact_maps": [{"field": "common_objects", "expected_entries": 57,
                                   "retention": "object outputs not retained; digest identity cannot be rechecked",
                                   "meaning": "Compiled object SHA-256 values keyed by their source paths. These are not source-file identity pins."}],
        "assert_fields": [("status", "PASS"), ("scope", "native unit/integration checks; not DOS differential acceptance"),
                          ("sdl3_host.status", "PASS"),
                          ("sdl3_host.receipt.scope", "SDL3 host boundary; not game startup or DOS raster proof"),
                          ("sdl3_host.receipt.framebuffer_pixels_compared", 224000)],
        "host_list_assertions": [{"field": "tests", "length": 46, "item_field": "exit_code", "equals": 0}],
        "scope_only": True,
        "metrics": [{"name": "native_checks", "field": "tests", "operation": "len"},
                    {"name": "host_pixels_compared", "field": "sdl3_host.receipt.framebuffer_pixels_compared", "operation": "value"}],
        "scope": "46 native unit/integration checks plus a separate SDL host receipt comparing 224,000 framebuffer pixels. These are native/host checks with zero original-DOS invocations.",
        "audit_class": "native_and_sdl_host_checks_zero_dos_calls",
    },
    {
        "id": "live_natural_gameover_fast_next7_smoke_20261002",
        "report": "portable/tests/live_game/evidence/natural-gameover-fast-202-live-smoke.json",
        "path_hash_maps": ["source_and_transitive_header_sha256_before"],
        "equal_hash_maps": [("production_executable_sha256_before", "production_executable_sha256_after"),
                            ("production_build_receipt_sha256_before", "production_build_receipt_sha256_after")],
        "assert_fields": [("status", "PASS"), ("natural_endgame_callback_observed", True),
                          ("scenario_click_observed", True), ("source_speed_at_exit", 3),
                          ("source_speed3_action_calls", 1), ("completed_ticks_at_exit", 3798),
                          ("source_pins_stable", True), ("timed_out", False), ("returncode", 0)],
        "hash_resolvers": [{"field": "smoke_executable_sha256", "roots": ["build/portable/tests"]}],
        "scope_only": True,
        "metrics": [{"name": "host_simulation_ticks", "field": "completed_ticks_at_exit", "operation": "value"},
                    {"name": "speed_actions", "field": "source_speed3_action_calls", "operation": "value"}],
        "scope": "One real SDL host run reached natural EndGame after physical Shift+4 selected speed 3, accepted the scenario click, and continued for 3,798 native ticks. Host smoke only; no DOS invocation or DOS/native equivalence claim.",
        "audit_class": "host_only_natural_gameover_no_dos_comparison",
    },
    {
        "id": "procmenu_next7_dos_native_84_20261002",
        "report": "portable/tests/menus/evidence/procmenu-next7-dos-differential-20261002.json",
        "path_hash_maps": ["input_stability.hashed_inputs"],
        "native_tu_maps": ["input_stability.hashed_inputs"],
        "native_tu_map_prefixes": ["build/workers/recovered_source_next7/generated/"],
        "hash_fields": [("native.state_header_sha256", "build/workers/recovered_source_next7/generated/recovered_state.h")],
        "hash_resolvers": [{"field": "native.dll_sha256", "roots": ["build/workers/procmenu_differential"]}],
        "oracle_field": "oracle.exe_sha256",
        "harness": [("oracle.harness_sha256", "tools/behavior.py")],
        "assert_fields": [("status", "PASS"), ("case_count", 84), ("mismatch_count", 0),
                          ("input_stability.stable_before_after", True)],
        "host_list_assertions": [{"field": "cases", "length": 84, "item_field": "equal", "equals": True},
                                 {"field": "cases", "item_field": "touched_globals_equal", "equals": True},
                                 {"field": "cases", "item_field": "ordered_host_effects_equal", "equals": True}],
        "dos_count": "case_count",
        "scope": "84 direct original-DOS ProcMenu and native NEXT7 cases over actual SHARED resource-0 menu IDs, signed FD-prefixed event words, pause/tool, speed, and yard-mode branches. SetPause/SetMenuEntries and ProcMenu source bodies execute; typed host leaves remain boundaries. Generated NEXT7 profile files live under ignored build/workers, so CURRENT is local identity only.",
        "audit_class": "direct_dos_native_procmenu_next7_source_profile",
    },
    {
        "id": "control_window_render_command_trace_2_dos_native_20261002",
        "report": "portable/tests/setup/render_controls/evidence/control-window-render-trace.json",
        "oracle_field": "oracle_sha256",
        "harness": [("behavior_harness_sha256", "tools/behavior.py")],
        "hash_resolvers": [
            {"field": "source_sha256", "roots": ["src"]},
            {"field": "primitive_source_sha256", "roots": ["src"]},
            {"field": "color_translation_source_sha256", "roots": ["src"]},
            {"field": "setup_fixture_source_sha256", "roots": ["portable/tests/setup"]},
            {"field": "window_resource_helper_sha256", "roots": ["portable/tests/windows"]},
            {"field": "model_source_sha256", "roots": ["portable/ui_model/windows/control_render"]},
            {"field": "model_header_sha256", "roots": ["portable/ui_model/windows/control_render"]},
            {"field": "test_source_sha256", "roots": ["portable/tests/setup/render_controls"]},
            {"field": "runner_sha256", "roots": ["portable/tests/setup/render_controls"]},
            {"field": "model_test_binary_sha256", "roots": ["build/workers/controls-render"]},
        ],
        "hash_fields": [("function_map_sha256", "layout/functions.json"),
                        ("symbol_map_sha256", "layout/symbols.json"),
                        ("ndx_sha256", "assets/HCEGANT.NDX"),
                        ("dat_sha256", "assets/HCEGANT.DAT")],
        "native_tus": ["portable/ui_model/windows/control_render/control_render.c",
                       "portable/tests/setup/render_controls/test_control_render.c"],
        "assert_fields": [("status", "PASS_BOUNDED_COMMAND_TRACE_NOT_PIXELS"),
                          ("runs.0.direct_original_calls", 1), ("runs.1.direct_original_calls", 1),
                          ("runs.0.comparison", "exact ordered normalized DOS command trace"),
                          ("runs.1.comparison", "exact ordered normalized DOS command trace")],
        "dos_count": {"sum": ["runs.0.direct_original_calls", "runs.1.direct_original_calls"]},
        "scope": "Two direct original-DOS control-window draw calls (Mode and Caste) compared as exact normalized ordered command traces. This packet proves commands and operands, not DOS pixels or full window composition.",
        "audit_class": "direct_dos_native_command_trace_not_pixels",
    },
    {
        "id": "control_window_raster_resource_backed_host_20261002",
        "report": "portable/tests/setup/render_controls/evidence/control-window-raster.json",
        "path_hash_maps": ["source_sha256", "assets_sha256"],
        "native_tu_maps": ["source_sha256"],
        "hash_fields": [("command_trace_report_sha256", "portable/tests/setup/render_controls/evidence/control-window-render-trace.json")],
        "hash_resolvers": [{"field": "binary_sha256", "roots": ["build/workers/controls-render"]}],
        "related_documents": [{"path": "portable/tests/setup/render_controls/evidence/control-window-render-trace.json",
                               "hash_field": "command_trace_report_sha256",
                               "hash_links": [("oracle_sha256", "assets/SIMANT.EXE")],
                               "assertions": [("status", "PASS_BOUNDED_COMMAND_TRACE_NOT_PIXELS"),
                                              ("runs.0.direct_original_calls", 1),
                                              ("runs.1.direct_original_calls", 1)]}],
        "assert_fields": [("status", "PASS_RESOURCE_BACKED_PLAN_RASTER_NO_DOS_PIXEL_CLAIM")],
        "scope_only": True,
        "metrics": [{"name": "raster_outputs", "field": "runs", "operation": "len"}],
        "scope": "Resource-backed native raster output for control windows 18 and 19; zero direct DOS calls in this raster run. It is linked to the separate two-call DOS command-trace report and makes no DOS framebuffer/pixel claim.",
        "audit_class": "native_raster_host_output_zero_dos_pixel_claim",
    },
    {
        "id": "windows_zoom_resource_adapter_host_repaint_v3_20261002",
        "report": "portable/tests/windows_zoom/evidence/adapter-host-repaint-v3.json",
        "hash_fields": [("pins.zoom_source_sha256", "portable/ui_model/windows/zoom.c"),
                        ("pins.zoom_header_sha256", "portable/ui_model/windows/zoom.h"),
                        ("pins.native_test_source_sha256", "portable/tests/windows_zoom/test_zoom.c"),
                        ("pins.resource_helper_sha256", "portable/tests/windows/evidence/differential_window.py"),
                        ("pins.hcegant_ndx_sha256", "assets/HCEGANT.NDX"),
                        ("pins.hcegant_dat_sha256", "assets/HCEGANT.DAT")],
        "library": ("pins.native_library_sha256", "build/workers/behavior_sim_contracts/zoom-resource-adapter-v3.dll"),
        "assert_fields": [("status", "PASS"), ("adapter.observed.status", 0),
                          ("adapter.invalid_resource_status", 1),
                          ("adapter.invalid_resource_preserved_state", True),
                          ("adapter.observed.zoom_rect_initialized", False)],
        "scope_only": True,
        "requires_missing": ["adapter/host repaint producer runner hash and before/after input stability receipt are absent; this is retained as an incomplete host-contract report, not current proof"],
        "scope": "One native resource-adapter observation and one invalid-resource preservation control, plus a stated full-z-order host repaint policy. No direct DOS call or redraw/clip equivalence is claimed.",
        "audit_class": "incomplete_native_adapter_host_contract",
    },
    {
        "id": "windows_zoom_independent_residue_sweep_v4_20261002",
        "report": "portable/tests/windows_zoom/evidence/independent-residue-sweep-v4.json",
        "hash_fields": [("pins.zoom_source_sha256", "src/S26/m39C7.c"),
                        ("pins.toggle_runner_sha256", "portable/tests/windows_zoom/dos_toggle_diff.py"),
                        ("pins.runner_sha256", "portable/tests/windows_zoom/independent_residue_sweep.py"),
                        ("pins.harness_sha256", "tools/behavior.py")],
        "oracle_field": "pins.oracle_sha256",
        "assert_fields": [("status", "PASS"), ("scope.case_count", 64), ("scope.compared", 64),
                          ("scope.budget_exceeded", 0), ("scope.distinct_final_geometries", 1)],
        "host_list_assertions": [{"field": "cases", "length": 64, "item_field": "status", "equals": "COMPARED"}],
        "dos_count": "scope.case_count",
        "requires_missing": ["the sweep reuses dos_toggle_diff.setup_case but the report does not pin its layout/executable helpers or HCEGANT resource files; completeness remains INCOMPLETE despite the recorded 64 original-DOS cases"],
        "scope": "64 original-DOS first-call residue cases; each drives the zoom entry once and records final geometry and the residue-dependent saved rectangle. Original-only sweep; no native lane and no redraw/clip equivalence claim.",
        "audit_class": "incomplete_original_dos_residue_sweep",
    },
    {
        "id": "legacy_save_codec_v1_mechanical_20261002",
        "report": "portable/tests/save/evidence/legacy-save-codec-v1/validation.json",
        "related_documents": [{"path": "portable/tests/save/evidence/legacy-save-codec-v1/pins.json",
                               "hash_rows": {"root": "."}},
                              {"path_field": "next7_binding_audit.path",
                               "assertions": [("schema", "simant-save-next7-binding-audit-v1"),
                                              ("status", "DIAGNOSTIC_ONLY_NOT_PRODUCTION_BINDING"),
                                              ("record_count", 307), ("unresolved_count", 7)]}],
        "hash_fields": [("next7_binding_audit.sha256", "portable/tests/save/evidence/legacy-save-codec-v1/next7-binding-audit.json")],
        "native_tus": ["portable/game/save/legacy_codec.c", "portable/tests/save/test_legacy_codec.c"],
        "assert_fields": [("status", "PASS_MECHANICAL_CODEC_ONLY"), ("records", 307),
                          ("payload_bytes", 48386), ("next7_binding_audit.unresolved_rows", 7)],
        "scope_only": True,
        "requires_missing": ["compiler identity, test executable hash, and run stability receipt are absent; do not treat the synthetic round-trip as DOS SaveGame evidence or production RecoveredState binding"],
        "scope": "307 synthetic ordered records round-trip mechanically. Zero DOS calls. Seven save-table rows remain unresolved in the diagnostic NEXT7 state binding; filesystem and SaveGame semantics are untested.",
        "audit_class": "incomplete_synthetic_save_codec_only",
    },
    {
        "id": "audio_voice_admission_279_dos_native_20261002",
        "report": "build/portable/audio-voice-admission-differential.json",
        "path_hash_maps": ["source_pins"],
        "hash_fields": [("native_sha256", "portable/research/audio_voice_admission.c")],
        "oracle_field": "oracle_sha256",
        "assert_fields": [("status", "PASS"), ("channel_count", 2), ("calls_compared", 9),
                          ("age_wrap_calls", 270)],
        "native_tus": ["portable/research/audio_voice_admission.c"],
        "dos_count": {"sum": ["calls_compared", "age_wrap_calls"]},
        "metrics": [{"name": "allocator_direct_calls", "field": "calls_compared", "operation": "value"},
                    {"name": "age_wrap_direct_calls", "field": "age_wrap_calls", "operation": "value"}],
        "scope_only": False,
        "requires_missing": ["report is an ignored build output and does not pin the differential runner, its Unicorn/tool helper inputs, or the temporary compiled native library; recorded 279 calls remain diagnostic and identity-incomplete"],
        "scope": "Nine directed DOS/native voice-admission cases plus 270 direct DOS/native age-wrap calls. The loaded source release helper executes; downstream mixer output is outside scope. Build-output report and temporary candidate binary are not preserved evidence.",
        "audit_class": "incomplete_direct_dos_native_audio_admission",
    },
    {
        "id": "next8_event_width_source_recipe_20261002",
        "report": "portable/tests/recovered/evidence/next8-event-width-v1/evidence.json",
        "hash_fields": [
            ("source.sha256", "src/S24/m39C7.c"),
            ("module.sha256", "build/workers/recovered_source_next8/generated/S24_m39C7.c"),
            ("state.recovered_state.h", "build/workers/recovered_source_next8/generated/recovered_state.h"),
            ("state.recovered_state.c", "build/workers/recovered_source_next8/generated/recovered_state.c"),
            ("module.compile.lowered_object_sha256", "build/workers/recovered_source_next8/generated/S24_m39C7.o"),
            ("extension.parent_wrapper_sha256", "portable/tools/recover_source_next7.py"),
            ("extension.wrapper_sha256", "portable/tools/recover_source_next8.py"),
            ("harness.behavior_py_sha256", "tools/behavior.py"),
            ("harness.context_py_sha256", "tools/context.py"),
            ("compiler.sha256", "C:/msys64/mingw64/bin/gcc.exe"),
        ],
        "rooted_path_hash_maps": [{"field": "preserved_files",
                                   "root": "portable/tests/recovered/evidence/next8-event-width-v1"}],
        "native_tus": ["portable/tests/recovered/evidence/next8-event-width-v1/generated/S24_m39C7.next8.c"],
        "assert_fields": [
            ("status", "DIAGNOSTIC_ONLY_NOT_BEHAVIOR_EXACT"),
            ("extension.status", "DIAGNOSTIC_ONLY_NOT_PRODUCTION"),
            ("extension.selected_functions", ["ProcHistoryEvent"]),
            ("extension.host_width_controls.positive.compile_passed", True),
            ("extension.host_width_controls.negative_parent_width.compile_passed", True),
            ("extension.parent_profile.state_hashes_unchanged", True),
            ("suite.directed_count", 64), ("suite.mismatches", 0),
            ("suite.errors", 0), ("suite.native_vs_original_trace_mismatches", 0),
        ],
        "host_list_assertions": [
            {"field": "suite.cases", "length": 64, "item_field": "exact_candidate_match", "equals": True},
            {"field": "suite.cases", "length": 64, "item_field": "native_matches_oracle_trace", "equals": True},
        ],
        "dos_count": {"sum": ["suite.directed_count"]},
        "scope": "64 directed original-DOS/native ProcHistoryEvent cases plus preserved positive/negative host-width controls. Source recipe and profile extension are diagnostic only; this is not production-profile or full-engine acceptance.",
        "audit_class": "diagnostic_next8_source_recipe_not_behavior_exact",
    },
    {
        "id": "native_gate_49_next9_state_only_20261002",
        "report": "portable/tests/evidence/current/20261002/native-gate-49-next9-state-only-20261002.json",
        "path_hash_maps": ["inputs", "sdl3_host.receipt.build_receipt.inputs"],
        "opaque_artifact_maps": [{"field": "common_objects", "expected_entries": 61,
                                   "retention": "compiled object outputs are build artifacts; source identities are independently pinned in inputs",
                                   "meaning": "Compiled object SHA-256 values keyed by translation-unit source paths; never source-file hashes."}],
        "assert_fields": [("status", "PASS"),
                          ("scope", "native unit/integration checks; not DOS differential acceptance"),
                          ("sdl3_host.status", "PASS"), ("sdl3_host.receipt.status", "PASS")],
        "host_list_assertions": [{"field": "tests", "length": 49, "item_field": "exit_code", "equals": 0}],
        "native_tu_maps": ["inputs"],
        "scope_only": True,
        "metrics": [{"name": "native_checks", "field": "tests", "operation": "len"},
                    {"name": "host_pixels_compared", "field": "sdl3_host.receipt.framebuffer_pixels_compared", "operation": "value"}],
        "scope": "49 native unit/integration checks plus separate SDL host checks after Next9 state-only guards. No original-DOS calls or pixel-equivalence claim.",
        "audit_class": "native_and_sdl_host_checks_zero_dos_calls",
    },
    {
        "id": "native_gate_49_menu_controls_final_superseded_archived_20261002",
        "report": "portable/tests/evidence/current/20261002/native-gate-49-menu-controls-final-20261002.json",
        "archived": True,
    },
    {
        "id": "procmenu_next7_dos_native_84_complete_closure_20261002",
        "report": "portable/tests/menus/evidence/procmenu-next7-dos-differential-adapter-complete-closure-20261002.json",
        "path_hash_maps": ["input_stability.hashed_inputs"],
        "native_tu_maps": ["input_stability.hashed_inputs"],
        "native_tu_map_prefixes": ["build/workers/recovered_source_next7/generated/"],
        "hash_fields": [
            ("native.S11_sha256", "build/workers/recovered_source_next7/generated/S11_m35F5.c"),
            ("native.state_header_sha256", "build/workers/recovered_source_next7/generated/recovered_state.h"),
            ("native.state_source_sha256", "build/workers/recovered_source_next7/generated/recovered_state.c"),
            ("native.probe_sha256", "portable/tests/menus/procmenu_native_probe.c"),
            ("native.menu_adapter_sha256", "portable/game/recovered/menu_adapter.c"),
            ("oracle.harness_sha256", "tools/behavior.py"),
        ],
        "hash_resolvers": [{"field": "native.dll_sha256", "roots": ["build/workers/procmenu_differential"]}],
        "oracle_field": "oracle.exe_sha256",
        "assert_fields": [
            ("status", "PASS"), ("claim", "Original DOS S11 ProcMenu compared with generated NEXT7 S11 ProcMenu for all command IDs present in SHARED resource 0, FD-prefixed signed event words proving low-byte dispatch, plus conditional yard-mode/pause/speed variants."),
            ("case_count", 84), ("mismatch_count", 0), ("input_stability.stable_before_after", True),
        ],
        "host_list_assertions": [
            {"field": "cases", "length": 84, "item_field": "equal", "equals": True},
            {"field": "cases", "length": 84, "item_field": "touched_globals_equal", "equals": True},
            {"field": "cases", "length": 84, "item_field": "ordered_host_effects_equal", "equals": True},
        ],
        "dos_count": "case_count",
        "scope": "84 direct DOS/native ProcMenu cases against generated NEXT7 source, with explicit typed host-effect boundaries. Candidate profile is an ignored build artifact; CURRENT is local identity only.",
        "audit_class": "direct_dos_native_procmenu_next7_complete_closure",
    },
    {
        "id": "engine_procmenu_next7_21_selected_closure_20261002",
        "report": "portable/tests/menus/evidence/engine-procmenu-next7-selected-closure-20261002.json",
        "path_hash_maps": ["inputs"],
        "native_tu_maps": ["inputs"],
        "native_tu_map_prefixes": ["build/workers/recovered_source_next7/generated/"],
        "hash_fields": [("generated_profile_provenance_sha256", "build/workers/recovered_source_next7/generated/provenance.json")],
        "hash_resolvers": [{"field": "executable.sha256", "roots": ["build/workers/procmenu_engine_next7"]}],
        "harness": [("harness_sha256", "tools/behavior.py")],
        "assert_fields": [
            ("status", "PASS"), ("profile", "NEXT7 generated recovered source"),
            ("inputs_stable_before_after", True),
            ("linked_profile_scope.whole_generated_profile_object_count", 27),
            ("linked_profile_scope.linked_generated_object_count", 25),
        ],
        "host_list_assertions": [
            {"field": "cases", "length": 21, "item_field": "status_code", "equals": 0},
        ],
        "scope_only": True,
        "requires_missing": ["one option-32 path intentionally fails closed at StopSong; the command matrix is a bounded native engine integration, not full menu or DOS equivalence"],
        "metrics": [{"name": "selected_menu_cases", "field": "cases", "operation": "len"}],
        "scope": "One resource-backed NewGame and DoAntSim tick followed by 21 engine ProcMenu actions. Native integration only, with typed host effects and one explicit unsupported StopSong gap.",
        "audit_class": "native_engine_procmenu_selected_closure_no_dos_claim",
    },
    {
        "id": "engine_procmenu_next7_complete_closure_superseded_archived_20261002",
        "report": "portable/tests/menus/evidence/engine-procmenu-next7-complete-closure-20261002.json",
        "archived": True,
    },
    {
        "id": "engine_procmenu_next7_stale_sourcepins_archived_20261002",
        "report": "portable/tests/menus/evidence/engine-procmenu-next7-stale-sourcepins-archived-20261002.json",
        "archived": True,
    },
    {
        "id": "native_gate_49_interim_archived_20261002",
        "report": "portable/tests/evidence/current/20261002/native-gate-49-menu-controls-20261002.json",
        "archived": True,
    },
    {
        "id": "physical_menu_next8_slow_final_20261002",
        "report": "portable/tests/live_menu/evidence/physical-menu-slow-final-next8-20261002.json",
        "path_hash_maps": ["source_closure.build_receipt.inputs_before",
                            "source_closure.build_receipt.inputs_after",
                            "source_closure.test_inputs_before",
                            "source_closure.test_inputs_after"],
        "equal_hash_maps": [("source_closure.build_receipt.inputs_before",
                             "source_closure.build_receipt.inputs_after"),
                            ("source_closure.test_inputs_before",
                             "source_closure.test_inputs_after"),
                            ("source_closure.build_receipt.sha256_before",
                             "source_closure.build_receipt.sha256_after")],
        "path_hash_fields": [
            ("source_closure.build_receipt.path", "source_closure.build_receipt.sha256_before"),
            ("source_closure.production_executable.path", "source_closure.production_executable.sha256"),
            ("source_closure.production_sdl3_dll.path", "source_closure.production_sdl3_dll.sha256"),
            ("source_closure.test_executable.path", "source_closure.test_executable.sha256"),
            ("source_closure.test_sdl3_dll.path", "source_closure.test_sdl3_dll.sha256"),
            ("final_artifacts.event_report.path", "final_artifacts.event_report.sha256"),
            ("final_artifacts.geometry_report.path", "final_artifacts.geometry_report.sha256"),
            ("final_artifacts.state_files.recovered.path", "final_artifacts.state_files.recovered.sha256"),
            ("final_artifacts.state_files.normalized.path", "final_artifacts.state_files.normalized.sha256"),
            ("final_artifacts.state_files.rng.path", "final_artifacts.state_files.rng.sha256"),
            ("final_artifacts.state_files.statistics.path", "final_artifacts.state_files.statistics.sha256"),
            ("final_artifacts.screenshot.path", "final_artifacts.screenshot.sha256"),
        ],
        "assert_fields": [("status", "PASS"), ("passed", True),
                          ("proof_boundary", "Finite live SDL host integration only; does not claim DOS state equivalence or framebuffer equivalence."),
                          ("execution.return_code", 0), ("execution.timed_out", False),
                          ("injected_events.interaction_count", 3),
                          ("injected_events.pushed_event_count", 9),
                          ("final_diagnostics.completed_ticks", 32),
                          ("final_diagnostics.menu_loaded", True)],
        "scope_only": True,
        "metrics": [{"name": "native_ticks", "field": "final_diagnostics.completed_ticks", "operation": "value"},
                    {"name": "physical_menu_events", "field": "injected_events.pushed_event_count", "operation": "value"}],
        "scope": "Corrected physical SDL Next8 host run selected Speed→Slow and toggled Pause twice in a resource-backed native NewGame session. Source/build stability and output artifacts are pinned; no DOS-state or framebuffer equivalence is claimed.",
        "audit_class": "physical_sdl_host_integration_no_dos_or_pixel_equivalence",
    },
    {
        "id": "physical_menu_fast_description_prior_archived_20261002",
        "report": "portable/tests/live_menu/evidence/physical-menu-fast-description-archived-20261002.json",
        "archived": True,
    },
    {
        "id": "next9_v2_savegame_stream_differential_20261002",
        "report": "portable/tests/save/evidence/legacy-save-codec-v2/validation.json",
        "hash_fields": [
            ("next9_profile.sha256", "build/workers/recovered_source_next9/generated/provenance.json"),
        ],
        "related_documents": [
            {"path": "portable/tests/save/evidence/legacy-save-codec-v2/input-pins.json",
             "path_hash_lists": [{"field": "inputs", "path_field": "path", "hash_field": "sha256"}],
             "assertions": [("schema", "simant-legacy-save-next9-input-pins-v1"),
                            ("captured_DOS_payload_sha256", "cb8c3f31b59eb869c230277876919193b4f887cbe8a3c41033a307d21abed480"),
                            ("captured_DOS_payload_bytes", 48386)]},
            {"path": "portable/tests/save/evidence/legacy-save-codec-v2/source-binding-proof.json",
             "assertions": [("schema", "simant-legacy-save-next9-state-binding-audit-v1"),
                            ("status", "SOURCE_GROUNDED_NEXT9_BINDING_IMPLEMENTED"),
                            ("claims.candidate_is_complete_binding", False),
                            ("claims.new_profile_or_engine_changes_made", False)],
             "file_pins": [("next9.header_sha256", "build/workers/recovered_source_next9/generated/recovered_state.h"),
                           ("next9.source_sha256", "build/workers/recovered_source_next9/generated/recovered_state.c"),
                           ("inputs.save_table.sha256", "src/S09/m35F5.c"),
                           ("inputs.swarm_owner.sha256", "src/S13/m384C.c"),
                           ("inputs.data_initializer.sha256", "src/data/d3D57.c")]},
        ],
        "assert_fields": [
            ("status", "PASS_DIAGNOSTIC_ONLY_NOT_PRODUCTION"),
            ("actual_original_DOS_SaveGame.function", "o09_35F5_0188"),
            ("actual_original_DOS_SaveGame.write_calls", 307),
            ("actual_original_DOS_SaveGame.payload_bytes", 48386),
            ("actual_original_DOS_SaveGame.payload_sha256", "cb8c3f31b59eb869c230277876919193b4f887cbe8a3c41033a307d21abed480"),
            ("native_replay.both_reproduced_actual_DOS_stream_byte_exactly", True),
        ],
        "dos_count": {"single_function_invocation": {"field": "actual_original_DOS_SaveGame",
                                                         "function": "o09_35F5_0188",
                                                         "positive_field": "write_calls"}},
        "scope_only": False,
        "requires_missing": ["validation packet does not pin the native test executable/compiler output or provide a source-stability receipt; keep as diagnostic stream evidence, not production SaveGame acceptance"],
        "metrics": [{"name": "original_dos_write_callbacks", "field": "actual_original_DOS_SaveGame.write_calls", "operation": "value"},
                    {"name": "payload_bytes", "field": "actual_original_DOS_SaveGame.payload_bytes", "operation": "value"}],
        "scope": "One actual original-DOS SaveGame stream capture (307 write callbacks, 48,386 payload bytes) and native replay reported byte-exact against its captured hash. Diagnostic Next9 binding only; native executable identity and live filesystem behavior are not pinned.",
        "audit_class": "incomplete_diagnostic_next9_savegame_stream",
    },
    {
        "id": "next9_v1_proposal_archived_20261002",
        "report": "portable/tests/save/evidence/legacy-save-next9-binding-v1/next9-binding-audit.json",
        "archived": True,
    },
    {
        "id": "next9_profile_state_smoke_host_20261002",
        "report": "portable/tests/recovered/evidence/next9-state-smoke-20261002.json",
        "path_hash_maps": ["inputs", "inputs_after"],
        "equal_hash_maps": [("inputs", "inputs_after")],
        "hash_fields": [("executable_sha256", "build/portable/simant-sdl3.exe")],
        "assert_fields": [("status", "PASS"), ("inputs_stable_before_after", True)],
        "scope_only": True,
        "metrics": [{"name": "completed_native_ticks", "field": "completed_ticks", "operation": "value"}],
        "scope": "Finite Next9 native NewGame/simulation smoke with an SDL dummy driver. No DOS state/pixel comparison or save/load lifecycle claim.",
        "audit_class": "host_only_next9_native_profile_smoke_no_dos_claim",
    },
    {
        "id": "paired_control_events_34_dos_native_20261002",
        "report": "portable/tests/setup/control_events/evidence/paired-control-events.json",
        "path_hash_maps": ["transitive_source_pins_before", "transitive_source_pins_after"],
        "equal_hash_maps": [("transitive_source_pins_before", "transitive_source_pins_after")],
        "hash_fields": [
            ("dos_report_sha256", "portable/tests/setup/control_events/evidence/dos-control-events.json"),
            ("native_adapter_sha256", "portable/tests/setup/control_events/native_adapter.c"),
            ("original_source_sha256", "src/root/m0798.c"),
            ("original_fixture_runner_sha256", "portable/tests/setup/evidence/setup_differential.py"),
            ("native_model_sha256", "portable/ui_model/windows/control_events.c"),
            ("native_header_sha256", "portable/ui_model/windows/control_events.h"),
            ("native_test_sha256", "portable/tests/setup/control_events/test_control_events.c"),
            ("native_differential_runner_sha256", "portable/tests/setup/control_events/run_paired_differential.py"),
            ("oracle_sha256", "assets/SIMANT.EXE"),
        ],
        "oracle_field": "oracle_sha256",
        "assert_fields": [("status", "PASS"), ("case_count", 34), ("mismatch_count", 0),
                          ("transitive_source_pins_stable", True)],
        "native_tus": ["portable/tests/setup/control_events/native_adapter.c",
                       "portable/ui_model/windows/control_events.c",
                       "portable/game/simulation/setup.c"],
        "dos_count": "case_count",
        "metrics": [{"name": "paired_cases", "field": "case_count", "operation": "value"}],
        "scope": "34 paired original-DOS/native controls for the source-backed setup-window control-event model; ordered host provider boundary is captured. The compiled adapter DLL digest is retained as an opaque artifact and is not treated as a source hash.",
        "audit_class": "paired_control_event_differential",
    },
    {
        "id": "group_visible_5380_dos_native_20261002",
        "report": "portable/tests/windows/group_visible/evidence/group-visible-dos-native-final-20261002.json",
        "path_hash_maps": ["input_stability.input_sha256_before", "input_stability.input_sha256_after"],
        "equal_hash_maps": [("input_stability.input_sha256_before", "input_stability.input_sha256_after")],
        "hash_fields": [
            ("original_execution.oracle_sha256", "assets/SIMANT.EXE"),
            ("original_execution.behavior_harness_sha256", "tools/behavior.py"),
        ],
        "oracle_field": "original_execution.oracle_sha256",
        "assert_fields": [("status", "PASS"), ("case_count", 5380), ("mismatch_count", 0),
                          ("inversion_event_count", 486), ("input_stability.unchanged", True)],
        "dos_count": "case_count",
        "metrics": [{"name": "direct_comparisons", "field": "case_count", "operation": "value"},
                    {"name": "normalized_inversion_events", "field": "inversion_event_count", "operation": "value"}],
        "scope": "5,380 finite original-DOS/native group-visibility comparisons, including 4 mixed-order cases. Captured inversion callback order is compared as normalized object IDs; renderer pixels and physical DOS rendering are outside scope.",
        "audit_class": "finite_group_visibility_differential_host_boundary",
    },
    {
        "id": "next9_v3_save_source_sentinels_1dos_20261002",
        "report": "portable/tests/save/evidence/legacy-save-codec-v3/original-dos-sentinel-report.json",
        "hash_fields": [
            ("oracle_sha256", "assets/SIMANT.EXE"),
            ("source_sha256", "src/S09/m35F5.c"),
            ("harness_sha256", "tools/behavior.py"),
            ("layout_symbols_sha256", "layout/symbols.json"),
            ("inventory_sha256", "portable/tests/dialogs/evidence/savegame-format-source-inventory-v1/save-records.json"),
        ],
        "oracle_field": "oracle_sha256",
        "assert_fields": [("status", "PASS_ORIGINAL_DOS_SOURCE_ADDRESS_TRACE"),
                          ("function", "o09_35F5_0188"), ("write_calls", 307),
                          ("payload_bytes", 48386), ("payload_matches_address_stream", True)],
        "related_documents": [
            {"path": "portable/tests/save/evidence/legacy-save-codec-v3/source-pins.json",
             "assertions": [("status", "DIAGNOSTIC_NOT_PRODUCTION")],
             "file_pins": [("next9_profile_provenance_sha256", "build/workers/recovered_source_next9/generated/provenance.json"),
                           ("original_executable_sha256", "assets/SIMANT.EXE"),
                           ("original_harness_sha256", "tools/behavior.py")],
             "path_hash_lists": [{"field": "pins", "path_field": "path", "hash_field": "sha256"}]},
            {"path": "portable/tests/save/evidence/legacy-save-codec-v3/native-sentinel-validation.json",
             "assertions": [("status", "PASS"), ("original_payload_sha256", "7895bc872a8a58504ef85b0f8bcaa81bcabc35cd2576ca0ea4e14241679cedbc")]},
            {"path": "portable/tests/save/evidence/legacy-save-codec-v3/binding-map.json",
             "assertions": [("status", "GENERATED_SOURCE_MAP_NOT_ACCEPTANCE")]},
        ],
        "dos_count": {"single_function_invocation": {"function_field": "function",
                                                       "function": "o09_35F5_0188",
                                                       "positive_field": "write_calls"}},
        "metrics": [{"name": "actual_savegame_invocations", "field": "function", "operation": "one"},
                    {"name": "nested_write_callbacks", "field": "write_calls", "operation": "value"},
                    {"name": "payload_bytes", "field": "payload_bytes", "operation": "value"}],
        "requires_missing": ["V3 evidence is a source-address sentinel diagnostic, not a linked production codec or full SaveGame equivalence proof."],
        "scope": "One actual original-DOS SaveGame invocation emitted 307 nested write callbacks and 48,386 payload bytes; a separate native source-sentinel test records positive endian runs and negative row/width mutants. This is not a full codec comparison or production save acceptance. The recorded Python harness digest is bound to tools/behavior.py; compiled native executable digests remain report metadata, not source identities.",
        "audit_class": "incomplete_diagnostic_next9_v3_save_sentinels",
    },
    {
        "id": "engine_procmenu_next7_control_model_21_20261002",
        "report": "portable/tests/menus/evidence/engine-procmenu-next7-control-model-closure-20261002.json",
        "partitioned_path_hash_maps": [{"field": "inputs", "artifact_suffixes": [".o"]}],
        "path_hash_fields": [("executable.path", "executable.sha256")],
        "hash_fields": [
            ("generated_profile_provenance_sha256", "build/workers/recovered_source_next7/generated/provenance.json"),
            ("runner_sha256", "portable/tests/menus/run_engine_procmenu.py"),
        ],
        "assert_fields": [("status", "PASS"), ("profile", "NEXT7 generated recovered source"),
                          ("inputs_stable_before_after", True),
                          ("compiler_dependency_method", "GCC -MM non-system transitive dependencies for each directly compiled native/recovered/harness TU and each linked generated profile TU; exact generated source/object pair and provenance, original source anchors, and HCEGANT/SHARED asset files are hash-pinned."),
                          ("summary.0", "SUMMARY|PASS|completed_ticks=1|queries_flags=22"),
                          ("expected_source_gap", "FD32 reaches the actual source StopSong call before its option-state toggle. The engine correctly fails closed with UNSUPPORTED_CALL and failed_service StopSong; the toggle is therefore not committed.")],
        "host_list_assertions": [{"field": "cases", "length": 21,
                                  "item_field": "recovered_binding_clean_after_return", "equals": True}],
        "skip_dependency_closure": True,
        "scope_only": True,
        "metrics": [{"name": "engine_menu_cases", "field": "cases", "operation": "len"},
                    {"name": "completed_simulation_ticks", "field": "baseline_tick", "operation": "one"}],
        "scope": "Resource-backed native engine integration: one actual DoAntSim tick then 21 source-mapped ProcMenu actions. The evidence includes the newer control-model closure and its StopSong fail-closed boundary. Native-only; the report's harness_sha256 is not rebound to tools/behavior.py because it denotes a distinct compiled/source harness identity.",
        "audit_class": "native_engine_procmenu_control_model_next7",
    },
    {
        "id": "native_gate_50_control_events_20261002",
        "report": "portable/tests/evidence/current/20261002/native-gate-50-control-events-20261002.json",
        "path_hash_maps": ["inputs", "sdl3_host.receipt.build_receipt.inputs"],
        "opaque_artifact_maps": [{"field": "common_objects", "expected_entries": 63,
                                   "retention": "compiled object outputs are build artifacts; source identities are independently pinned in inputs",
                                   "meaning": "Compiled object SHA-256 values keyed by translation-unit source paths; never source-file hashes."}],
        "assert_fields": [("status", "PASS"), ("scope", "native unit/integration checks; not DOS differential acceptance"),
                          ("frozen_oracle_inputs.status", "PASS"),
                          ("sdl3_host.status", "PASS"), ("sdl3_host.receipt.status", "PASS")],
        "host_list_assertions": [{"field": "tests", "length": 50, "item_field": "exit_code", "equals": 0}],
        "native_tu_maps": ["inputs"],
        "scope_only": True,
        "metrics": [{"name": "native_checks", "field": "tests", "operation": "len"},
                    {"name": "host_pixels_compared", "field": "sdl3_host.receipt.framebuffer_pixels_compared", "operation": "value"}],
        "scope": "50 native unit/integration checks and a separate SDL host receipt with a passing frozen-oracle input receipt. Host/native only; no original-DOS invocations or framebuffer-equivalence claim.",
        "audit_class": "native_and_sdl_host_checks_zero_dos_calls",
    },
    {
        "id": "control_preselect_type1_all_flags_20261002",
        "report": "portable/tests/windows/control_preselect/evidence/control-preselect-dos-native-final-20261002.json",
        "path_hash_maps": ["input_stability.input_sha256_before", "input_stability.input_sha256_after",
                           "toolchain.native_dependency_closure"],
        "equal_hash_maps": [("input_stability.input_sha256_before", "input_stability.input_sha256_after")],
        "hash_fields": [
            ("original_execution.oracle_sha256", "assets/SIMANT.EXE"),
            ("original_execution.behavior_harness_sha256", "tools/behavior.py"),
        ],
        "oracle_field": "original_execution.oracle_sha256",
        "assert_fields": [("status", "PASS"), ("case_count", 65536), ("mismatch_count", 0),
                          ("input_stability.unchanged", True)],
        "skip_dependency_closure": True,
        "dos_count": "case_count",
        "metrics": [{"name": "type1_all_flag_comparisons", "field": "case_count", "operation": "value"},
                    {"name": "native_unsupported_type_controls", "field": "unsupported_type_checks", "operation": "len"},
                    {"name": "native_provider_fault_controls", "field": "provider_fault_checks", "operation": "len"}],
        "scope": "65,536 direct original-DOS/native type-1 flag comparisons. The 11 unsupported-type and 11 provider-fault checks are separate native-only controls and are not added to the DOS comparison count.",
        "audit_class": "finite_control_preselect_differential_with_native_only_guards",
    },
    {
        "id": "historical_integrity_controls_frozen_20261002",
        "report": "portable/tests/evidence/current/20261002/historical-integrity-controls-20261002.json",
        "path_hash_fields": [("historical_validation.log_path", "historical_validation.log_sha256"),
                             ("hybrid.log_path", "hybrid.log_sha256")],
        "hash_fields": [
            ("manifest_sha256", "layout/manifest.json"),
            ("oracle_lock_sha256", "layout/oracle.lock.json"),
            ("asset_inventory_correction.sha256", "build/portable/asset-contamination-preserved/SDL3.dll"),
        ],
        "assert_fields": [("historical_validation.status", "PASS"),
                          ("historical_validation.codegen_rules", 48),
                          ("hybrid.status", "PASS"), ("hybrid.byte_identical", True),
                          ("hybrid.sha256", "aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11"),
                          ("frozen_input_receipt.status", "PASS"),
                          ("frozen_input_receipt.receipt_sha256", "072e2b2db963c13f5a37d6bd2328e08cf1cd6455ed1d5005e228337fe1755d01"),
                          ("asset_inventory_correction.locked_original_assets_changed", False),
                          ("asset_inventory_correction.oracle_lock_changed", False)],
        "scope_only": True,
        "metrics": [{"name": "historical_codegen_rules", "field": "historical_validation.codegen_rules", "operation": "value"}],
        "scope": "Frozen historical validation, hybrid byte-identity check, and input-integrity receipt. This is not native behavior, DOS/native equivalence, or an expanded EXACT/BEHAVIOR_EXACT claim.",
        "audit_class": "historical_integrity_identity_only",
    },
    {
        "id": "control_engine_next9_10_event_integration_20261002",
        "report": "portable/tests/setup/control_engine/evidence/control-engine-next9-20261002T175047Z.json",
        "path_hash_maps": ["compile.input_sha256_before", "compile.input_sha256_after"],
        "equal_hash_maps": [("compile.input_sha256_before", "compile.input_sha256_after")],
        "path_list_hash_map_membership": [{"list_field": "compile.local_transitive_dependencies",
                                           "map_field": "compile.input_sha256_before"}],
        "hash_fields": [
            ("profile_state.header_sha256", "build/workers/recovered_source_next9/generated/recovered_state.h"),
            ("profile_state.source_sha256", "build/workers/recovered_source_next9/generated/recovered_state.c"),
        ],
        "assert_fields": [("status", "PASS"), ("compile.local_transitive_dependency_count", 115),
                          ("counts.successful_engine_control_events", 10),
                          ("counts.actual_do_antsim_ticks", 1),
                          ("counts.actual_randyard_lifetime_call", 1),
                          ("checks.all_non_control_recovered_state_bytes_unchanged_per_event", True),
                          ("checks.session_selectors_and_caller_percent_words_survive_RandYard", True),
                          ("checks.provider_failure_unbinds_and_fresh_engine_succeeds", True)],
        "skip_dependency_closure": True,
        "scope_only": True,
        "metrics": [{"name": "native_engine_control_events", "field": "counts.successful_engine_control_events", "operation": "value"},
                    {"name": "native_simulation_ticks", "field": "counts.actual_do_antsim_ticks", "operation": "value"}],
        "scope": "One resource-backed actual DoAntSim tick and ten successful source-backed engine control events, plus native-only invalid/reentrant/provider-failure controls. The report pins its exact compiler transitive dependency list and stable before/after source map. No DOS calls are counted by this engine-boundary probe.",
        "audit_class": "native_control_engine_boundary_no_dos_claim",
    },
])


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


def check_path_map(checks, missing, report, field, path_prefix=None):
    try:
        values = get_field(report, field)
    except (KeyError, IndexError, TypeError):
        missing.append(f"{field}: required path/hash map is absent")
        return
    if not isinstance(values, dict) or not values:
        missing.append(f"{field}: required path/hash map is empty or malformed")
        return
    for path, expected in values.items():
        check_path = f"{path_prefix}/{path}" if path_prefix else path
        check_hash(checks, missing, label=f"{field}:{path}", expected=expected, path=check_path)


def check_path_hash_rows(checks, missing, document, document_path, list_spec):
    """Verify a JSON array of explicit {path, sha256} input rows."""
    field = list_spec["field"]
    try:
        rows = get_field(document, field)
    except (KeyError, IndexError, TypeError):
        missing.append(f"{document_path}:{field}: path/hash list absent")
        return
    if not isinstance(rows, list) or not rows:
        missing.append(f"{document_path}:{field}: path/hash list empty or malformed")
        return
    for row in rows:
        if not isinstance(row, dict):
            missing.append(f"{document_path}:{field}: malformed path/hash row")
            continue
        try:
            row_path = row[list_spec["path_field"]]
            row_hash = row[list_spec["hash_field"]]
        except KeyError:
            missing.append(f"{document_path}:{field}: path/hash row missing keys")
            continue
        check_hash(checks, missing, label=f"related-row:{document_path}:{row_path}",
                   expected=row_hash, path=row_path)


def validate_opaque_artifact_map(report: dict[str, Any], field: str,
                                 expected_entries: int | None = None) -> tuple[dict[str, Any], list[str]]:
    """Validate output-artifact digests without treating their keys as source paths."""
    issues: list[str] = []
    try:
        values = get_field(report, field)
    except (KeyError, IndexError, TypeError):
        return {"field": field, "entries": 0}, [f"{field}: artifact hash map absent"]
    if not isinstance(values, dict) or not values:
        return {"field": field, "entries": 0}, [f"{field}: artifact hash map empty or malformed"]
    if expected_entries is not None and len(values) != expected_entries:
        issues.append(f"{field}: expected {expected_entries} artifact digests, got {len(values)}")
    for name, value in values.items():
        if not isinstance(name, str) or not isinstance(value, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", value):
            issues.append(f"{field}: malformed artifact hash row {name!r}")
    return {"field": field, "entries": len(values)}, issues


def self_test_artifact_hash_maps() -> None:
    """Positive source pin and negative object-vs-source classification controls."""
    import tempfile

    with tempfile.TemporaryDirectory(prefix="proof-pin-map-selftest-") as directory:
        source_path = Path(directory) / "unit.c"
        source_path.write_bytes(b"int source_identity(void) { return 7; }\n")
        source_digest = sha256(source_path)
        checks: list[dict[str, Any]] = []
        missing: list[str] = []
        check_path_map(checks, missing, {"source_map": {str(source_path): source_digest}}, "source_map")
        if missing or len(checks) != 1 or checks[0].get("result") != "MATCH":
            raise AssertionError("positive source-map control failed")

        object_digest = hashlib.sha256(b"compiled object bytes, not C source").hexdigest()
        opaque, issues = validate_opaque_artifact_map(
            {"objects": {str(source_path): object_digest}}, "objects", expected_entries=1)
        if issues or opaque.get("entries") != 1:
            raise AssertionError("opaque object-artifact control failed")

        negative_checks: list[dict[str, Any]] = []
        negative_missing: list[str] = []
        check_path_map(negative_checks, negative_missing,
                       {"wrong_source_map": {str(source_path): object_digest}}, "wrong_source_map")
        if not any(row.get("result") == "MISMATCH" for row in negative_checks):
            raise AssertionError("negative object-as-source control did not reproduce the mismatch")


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
    """Require project-local quoted includes of native TUs to be pinned.

    This lexical fallback deliberately over-approximates inactive preprocessor
    branches. A producer that records GCC -MM active dependencies must validate
    that exact source map instead and set skip_dependency_closure; do not add
    inactive #ifdef includes to that compiler-produced closure.
    """
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
    if isinstance(field, dict) and "single_function_invocation" in field:
        descriptor = field["single_function_invocation"]
        try:
            if "function_field" in descriptor:
                function = get_field(report, descriptor["function_field"])
                positive = int(get_field(report, descriptor["positive_field"]))
            else:
                invocation = get_field(report, descriptor["field"])
                function = invocation.get("function")
                positive = int(invocation.get(descriptor["positive_field"], 0))
            expected_function = descriptor["function"]
            if function != expected_function or positive <= 0:
                return None, "Single original-function invocation is not established by the recorded function/callback fields."
            return 1, f"One invocation of {expected_function}; {positive} nested callbacks are reported separately, not counted as DOS calls."
        except (KeyError, TypeError, ValueError, AttributeError):
            return None, "Report lacks fields needed to establish one original-function invocation."
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
    for field, path in spec.get("hash_fields", []):
        try:
            expected = get_field(report, field)
        except (KeyError, IndexError, TypeError):
            missing.append(f"{field}: required file hash was not recorded")
            continue
        check_hash(checks, missing, label=f"file:{field}", expected=expected, path=path)
    for path_field, hash_field in spec.get("path_hash_fields", []):
        try:
            path = get_field(report, path_field)
            expected = get_field(report, hash_field)
        except (KeyError, IndexError, TypeError):
            missing.append(f"{path_field}/{hash_field}: path/hash pair is absent")
            continue
        if not isinstance(path, str):
            missing.append(f"{path_field}: recorded path is not a string")
            continue
        check_hash(checks, missing, label=f"path-pin:{path_field}/{hash_field}",
                   expected=expected, path=path)
    for field in spec.get("path_hash_maps", []):
        check_path_map(checks, missing, report, field)
    for membership in spec.get("path_list_hash_map_membership", []):
        try:
            paths = get_field(report, membership["list_field"])
            pinned = get_field(report, membership["map_field"])
        except (KeyError, IndexError, TypeError):
            missing.append(f"{membership}: dependency paths or hash map are absent")
            continue
        if not isinstance(paths, list) or not isinstance(pinned, dict):
            missing.append(f"{membership}: dependency path/hash map has malformed type")
            continue
        normalized_pins = {norm_rel(path).casefold() for path in pinned if isinstance(path, str)}
        for path in paths:
            if not isinstance(path, str) or norm_rel(path).casefold() not in normalized_pins:
                missing.append(f"{membership['list_field']}: unpinned transitive dependency {path!r}")
    partition_metadata = []
    for partition in spec.get("partitioned_path_hash_maps", []):
        try:
            values = get_field(report, partition["field"])
        except (KeyError, IndexError, TypeError):
            missing.append(f"{partition['field']}: required partitioned path/hash map is absent")
            continue
        if not isinstance(values, dict) or not values:
            missing.append(f"{partition['field']}: required partitioned path/hash map is empty or malformed")
            continue
        artifact_suffixes = tuple(s.lower() for s in partition.get("artifact_suffixes", []))
        artifact_paths = []
        non_artifact_count = 0
        for raw_path, expected in values.items():
            if not isinstance(raw_path, str):
                missing.append(f"{partition['field']}: non-string path in partitioned map")
                continue
            is_artifact = norm_rel(raw_path).lower().endswith(artifact_suffixes) if artifact_suffixes else False
            label_kind = "artifact-input" if is_artifact else "input"
            check_hash(checks, missing, label=f"{label_kind}:{partition['field']}:{raw_path}",
                       expected=expected, path=raw_path)
            if is_artifact:
                artifact_paths.append(norm_rel(raw_path))
            else:
                non_artifact_count += 1
        partition_metadata.append({"field": partition["field"], "non_artifact_input_entries": non_artifact_count,
                                   "artifact_input_entries": len(artifact_paths),
                                   "artifact_suffixes": list(artifact_suffixes),
                                   "artifact_paths": artifact_paths,
                                   "meaning": "mixed input map partitioned by extension; artifact digests are not source identities"})
    if partition_metadata:
        base["partitioned_input_hash_maps"] = partition_metadata
    for map_spec in spec.get("rooted_path_hash_maps", []):
        check_path_map(checks, missing, report, map_spec["field"],
                       path_prefix=map_spec["root"])
    opaque_metadata = []
    for artifact_spec in spec.get("opaque_artifact_maps", []):
        metadata, issues = validate_opaque_artifact_map(
            report, artifact_spec["field"], artifact_spec.get("expected_entries"))
        metadata["meaning"] = artifact_spec.get("meaning", "opaque build artifact hashes; not source identity")
        metadata["retention"] = artifact_spec.get("retention", "unspecified")
        opaque_metadata.append(metadata)
        missing.extend(issues)
    if opaque_metadata:
        base["opaque_artifact_hash_maps"] = opaque_metadata
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

    for resolver in spec.get("hash_resolvers", []):
        field = resolver["field"]
        try:
            expected = get_field(report, field)
        except (KeyError, IndexError, TypeError):
            missing.append(f"{field}: hash for resolver was not recorded")
            continue
        found, candidates = find_hash_path(expected, resolver["roots"])
        if found:
            check_hash(checks, missing, label=f"resolved:{field}", expected=expected, path=found)
            base.setdefault("resolved_producer_paths", []).append({"sha256": expected, "matches": candidates})
        else:
            missing.append(f"{field}: no unique file with recorded hash in {resolver['roots']}; candidates={candidates}")

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
        if document_spec.get("hash_rows"):
            rows_spec = document_spec["hash_rows"]
            if not isinstance(document, list):
                missing.append(f"{document_path}: expected an immutable hash-row list")
            else:
                rows_by_path = {row.get("path"): row for row in document
                                if isinstance(row, dict) and isinstance(row.get("path"), str)}
                archive_root = rows_spec["root"]
                for row_path, row in rows_by_path.items():
                    if not isinstance(row.get("sha256"), str):
                        missing.append(f"{document_path}:{row_path}: snapshot SHA-256 absent")
                        continue
                    archived_path = rows_spec.get("archive_paths", {}).get(row_path, row_path)
                    archived_target = rows_spec.get("external_paths", {}).get(
                        row_path, f"{archive_root}/{archived_path}")
                    check_hash(checks, missing,
                               label=f"snapshot-row:{document_path}:{row_path}",
                               expected=row["sha256"],
                               path=archived_target)
                for row_path, current_path in rows_spec.get("current_paths", {}).items():
                    row = rows_by_path.get(row_path)
                    if row is None:
                        missing.append(f"{document_path}:{row_path}: current source has no archived hash row")
                    else:
                        check_hash(checks, missing,
                                   label=f"snapshot-current:{document_path}:{row_path}",
                                   expected=row.get("sha256"), path=current_path)
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
        for list_spec in document_spec.get("path_hash_lists", []):
            check_path_hash_rows(checks, missing, document, document_path, list_spec)
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

    for left_field, right_field in spec.get("equal_hash_maps", []):
        try:
            left = get_field(report, left_field)
            right = get_field(report, right_field)
        except (KeyError, IndexError, TypeError):
            missing.append(f"{left_field}/{right_field}: required paired maps are absent")
            continue
        if left != right:
            missing.append(f"{left_field}/{right_field}: recorded before/after maps differ")
    if spec.get("replay_capture_files"):
        replay = spec["replay_capture_files"]
        try:
            capture_cases = get_field(report, replay["case_field"])
        except (KeyError, IndexError, TypeError):
            capture_cases = None
            missing.append(f"{replay['case_field']}: replay capture case list absent")
        if isinstance(capture_cases, list):
            for case in capture_cases:
                fixture = case.get("fixture") if isinstance(case, dict) else None
                if not fixture:
                    missing.append("replay capture case has no descriptor fixture name")
                    continue
                descriptor_path = f"{replay['root']}/{fixture}"
                try:
                    descriptor = json.loads(path_for(descriptor_path).read_text(encoding="utf-8"))
                except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                    missing.append(f"replay capture descriptor {descriptor_path} unreadable: {exc}")
                    continue
                check_hash(checks, missing, label=f"replay-descriptor:{fixture}",
                           expected=case.get("descriptor_sha256"), path=descriptor_path)
                snapshot = descriptor.get("snapshot_file")
                if not snapshot:
                    missing.append(f"replay capture descriptor {descriptor_path} has no snapshot_file")
                    continue
                check_hash(checks, missing, label=f"replay-snapshot:{fixture}",
                           expected=case.get("snapshot_sha256"), path=snapshot)
                if descriptor.get("snapshot_sha256") != case.get("snapshot_sha256"):
                    missing.append(f"replay capture descriptor {descriptor_path} disagrees with recorded snapshot hash")
    for field, expected in spec.get("assert_fields", []):
        try:
            actual = get_field(report, field)
        except (KeyError, IndexError, TypeError):
            missing.append(f"{field}: required evidence assertion is absent")
            continue
        if actual != expected:
            missing.append(f"{field}: expected {expected!r}, got {actual!r}")
    for assertion in spec.get("host_list_assertions", []):
        try:
            rows = get_field(report, assertion["field"])
        except (KeyError, IndexError, TypeError):
            missing.append(f"{assertion['field']}: host check list absent")
            continue
        if (not isinstance(rows, list)
                or ("length" in assertion and len(rows) != assertion["length"])
                or any(not isinstance(row, dict)
                       or row.get(assertion["item_field"]) != assertion["equals"]
                       for row in rows)):
            missing.append(f"{assertion['field']}: one or more host checks did not equal {assertion['equals']!r}")

    metrics = {}
    for metric in spec.get("metrics", []):
        name, field, operation = metric["name"], metric["field"], metric.get("operation", "value")
        try:
            value = get_field(report, field)
            if operation == "len":
                value = len(value)
            elif operation == "one":
                value = 1
            elif operation == "len_times":
                value = len(value) * int(metric["factor"])
            elif operation != "value":
                raise ValueError(f"unsupported metric operation {operation}")
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            missing.append(f"metric {name}: cannot read {field}: {exc}")
            continue
        metrics[name] = value
    if metrics:
        base["recorded_metrics"] = metrics

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
            prefixes = [norm_rel(p).lower() for p in spec.get("native_tu_map_prefixes", [])]
            tus.extend(path for path in values
                       if norm_rel(path).lower().endswith(".c")
                       and (norm_rel(path).lower().startswith("portable/")
                            or any(norm_rel(path).lower().startswith(prefix) for prefix in prefixes)))
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
    parser.add_argument("--self-test-artifact-maps", action="store_true",
                        help="run positive source-pin and negative object/source classification controls")
    args = parser.parse_args()
    if args.self_test_artifact_maps:
        self_test_artifact_hash_maps()
        print("PASS source-map positive control; PASS opaque-object negative control")
        return 0
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
