#!/usr/bin/env python3
"""Exercise the production original-source audio shared-state adapter."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "build/workers/behavior_tutorial_menu/audio-shared-state-preword"
GCC = Path(os.environ.get("CC", "C:/msys64/mingw64/bin/gcc.exe"))
sys.path.insert(0, str(ROOT))
from portable.tools.whole_program import convert_words
from portable.tools.whole_program import reviewed_overlays
from portable.tools.whole_program import adapt_state, adapt_bounded_state, adapt_additive_state, adapt_simulation_state
from portable.whole_program.conversions import source_bounded_state
from portable.whole_program.conversions import source_bounded_additive
from portable.whole_program.conversions import source_bounded_simulation_state_v6
from portable.whole_program.conversions.unprovided_state_v2 import DEFAULT_REPORT as V2_PLAN
from portable.whole_program.conversions import audio
from portable.whole_program.conversions import audio_shared_state_preword as shared_state

TARGETS = list(shared_state.SOURCE_SHA256)
MODULES = TARGETS


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(args: list[str]) -> None:
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit(result.returncode)


def extract_function(source: str, name: str) -> str:
    marker = name + "("
    start_name = source.find(marker)
    while start_name >= 0:
        paren = source.find("(", start_name)
        depth = 0
        end_paren = -1
        for pos in range(paren, len(source)):
            if source[pos] == "(":
                depth += 1
            elif source[pos] == ")":
                depth -= 1
                if depth == 0:
                    end_paren = pos
                    break
        if end_paren >= 0:
            body = source.find("{", end_paren)
            semi = source.find(";", end_paren)
            if body >= 0 and (semi < 0 or body < semi):
                depth = 0
                for pos in range(body, len(source)):
                    if source[pos] == "{":
                        depth += 1
                    elif source[pos] == "}":
                        depth -= 1
                        if depth == 0:
                            return source[source.rfind("\n", 0, start_name) + 1:pos + 1]
        start_name = source.find(marker, start_name + len(marker))
    raise ValueError(f"missing source function body {name}")


def lexical_control() -> None:
    sample = ('const char *literal = "struct Sample fd_50F6_0000[x].sample";\n'
              '/* struct Sample fd_50F6_0000[x].sample */\n'
              'struct Sample *real;\n')
    transformed, count = shared_state._code_sub(
        sample, r"struct\s+Sample", lambda _m: "PortableWholeAudioSample",
        label="lexical negative control", expected=1)
    if count != 1 or '"struct Sample fd_50F6_0000[x].sample"' not in transformed or \
            "/* struct Sample fd_50F6_0000[x].sample */" not in transformed or \
            "PortableWholeAudioSample *real" not in transformed:
        raise AssertionError("comment/string lexical protection control failed")
    original = (ROOT / "src/root/m0000.c").read_bytes()
    try:
        shared_state.adapt("src/root/m0000.c", original.decode("utf-8"), original + b" ")
    except ValueError:
        pass
    else:
        raise AssertionError("modified original input was accepted")


def scalar_deferral_controls() -> dict[str, object]:
    checked = {}
    for rel in ("src/root/m277E.c", "src/root/m284A.c", "src/root/m293A.c", "src/root/m29D6.c"):
        original = (ROOT / rel).read_bytes()
        source = original.decode("utf-8")
        if rel in audio.SOURCE_HASHES:
            source, _ = audio.adapt(rel, source)
        source, _ = reviewed_overlays(ROOT / rel, source, overlays_for_controls())
        adapted, ledger = shared_state.adapt_production(rel, source, original)
        expected, _pins = shared_state.resolve_later_scalar_owners(rel)
        retained = ledger["deferred_scalar_externs_retained"]
        if set(retained) != expected:
            raise AssertionError(f"{rel}: production deferred set differs from pinned owner maps")
        masked, _ = shared_state._lexical_mask(adapted)
        for name in expected:
            count = len(re.findall(rf"(?m)^[ \t]*extern\b[^;\r\n]*\b{re.escape(name)}\b[^;\r\n]*;", masked))
            if count != retained[name]:
                raise AssertionError(f"{rel}: deferred declaration {name} was lost after adapter")
        ordinary, _ = shared_state.adapt(rel, source, original)
        ordinary_masked, _ = shared_state._lexical_mask(ordinary)
        for name in expected:
            if re.search(rf"(?m)^[ \t]*extern\b[^;\r\n]*\b{re.escape(name)}\b[^;\r\n]*;", ordinary_masked):
                raise AssertionError(f"{rel}: diagnostic default unexpectedly retained {name}")
        try:
            shared_state.adapt(rel, source, original, deferred_scalar_externs={"fd_not_a_shared_scalar"})
        except ValueError:
            pass
        else:
            raise AssertionError("unknown deferred declaration was accepted")
        checked[rel] = {"deferred_scalar_externs": sorted(expected), "count": len(expected)}
    return checked


def overlays_for_controls() -> list[dict[str, object]]:
    overlay_path = ROOT / "portable/research/whole_program_behavior_sources.json"
    return json.loads(overlay_path.read_text(encoding="utf-8"))["entries"]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    lexical_control()
    scalar_controls = scalar_deferral_controls()
    report: dict[str, object] = {
        "schema": "whole-audio-shared-state-original-preword-v2",
        "compiler": str(GCC),
        "stage_order": ["adapt_audio where registered", "reviewed_overlays", "audio_shared_state_preword.adapt_production", "V2 source aliases", "V3 bounded owners", "V5 additive owners", "V6 simulation owners", "convert_words"],
        "inputs": {},
        "modules": [],
    }
    state_plan = json.loads(V2_PLAN.read_text(encoding="utf-8"))
    bounded_plan = source_bounded_state.load_plan()
    additive_plan = source_bounded_additive.load_plan()
    simulation_plan = source_bounded_simulation_state_v6.load_plan()
    overlay_path = ROOT / "portable/research/whole_program_behavior_sources.json"
    overlays = json.loads(overlay_path.read_text(encoding="utf-8"))["entries"]
    converted_sources: dict[str, str] = {}
    preword_sources: dict[str, str] = {}
    linked_objects: dict[str, Path] = {}
    for rel in TARGETS:
        original_bytes = (ROOT / rel).read_bytes()
        original_text = original_bytes.decode("utf-8")
        transformed_input = original_text
        audio_ledger: dict[str, object] | None = None
        if rel in audio.SOURCE_HASHES:
            transformed_input, audio_ledger = audio.adapt(rel, transformed_input)
        transformed_input, overlay_ledger = reviewed_overlays(
            ROOT / rel, transformed_input, overlays)
        adapted, ledger = shared_state.adapt_production(rel, transformed_input, original_bytes)
        after_v2 = adapt_state(adapted, state_plan, rel)
        after_v3, v3_ledger = adapt_bounded_state(after_v2, rel, bounded_plan)
        after_v5, v5_ledger = adapt_additive_state(after_v3, rel, additive_plan)
        after_v6, v6_ledger = adapt_simulation_state(after_v5, rel, simulation_plan)
        words, word_ledger = convert_words(after_v6)
        name = Path(rel).name
        generated = OUT / name
        generated.write_text(words, encoding="utf-8")
        obj = OUT / (name + ".o")
        run([
            str(GCC), "-std=c11", "-Wall", "-Wextra", "-Werror",
            "-Wno-unused-parameter", "-Wno-incompatible-pointer-types",
            "-Wno-type-limits", "-Wno-unused-variable", "-Wno-pointer-sign",
            "-Wno-char-subscripts", "-I", str(ROOT), "-I", str(ROOT / "portable/whole_program/platform"),
            "-c", str(generated), "-o", str(obj),
        ])
        converted_sources[rel] = words
        preword_sources[rel] = adapted
        linked_objects[rel] = obj
        report["inputs"][rel] = {
            "original_sha256": sha(original_bytes),
            "audio_stage_sha256": sha(transformed_input.encode("utf-8")),
            "preword_source_sha256": ledger["output_sha256"],
            "after_v2_sha256": sha(after_v2.encode("utf-8")),
            "after_v3_sha256": sha(after_v3.encode("utf-8")),
            "after_v5_sha256": sha(after_v5.encode("utf-8")),
            "after_v6_sha256": sha(after_v6.encode("utf-8")),
            "word_source_sha256": sha(words.encode("utf-8")),
        }
        report["modules"].append({
            "path": rel,
            "audio_adapter": audio_ledger,
            "reviewed_overlays": overlay_ledger,
            "shared_state_adapter": ledger,
            "later_source_owner_adapters": {
                "v2_changed": after_v2 != adapted,
                "v3": v3_ledger,
                "v5": v5_ledger,
                "v6": v6_ledger,
            },
            "word_conversion": word_ledger,
            "strict_compile": "PASS",
        })

    # Link an actual source-body initializer slice with the canonical native
    # tables, real DATA table initializers, and generated V3 scalar owner.
    preword_m277e = preword_sources["src/root/m277E.c"]
    converted_m277e, _ = convert_words(preword_m277e)
    init_helpers = extract_function(converted_m277e, "f_277E_010A") + "\n\n" + \
        extract_function(converted_m277e, "f_277E_017D")
    m290d = converted_sources["src/root/m290D.c"]
    volume_start = m290d.find("int16_t fd_55B3_74C0 = 0;")
    if volume_start < 0:
        raise ValueError("source m290D volume owner missing after conversion")
    volume_end = volume_start + len("int16_t fd_55B3_74C0 = 0;")
    harness_text = (ROOT / "portable/tests/whole_program/platform/audio_state_preword_test.c").read_text(encoding="utf-8")
    helpers_path = OUT / "mode1_initializer_slice.c"
    helpers_path.write_text(
        '#include "portable/whole_program/platform/audio_state.h"\n#include <stdint.h>\n'
        'extern int16_t fd_50F6_4A48, fd_50F6_4A4C;\n'
        'extern int16_t fd_55B3_6B9C, fd_55B3_74AD;\n'
        'extern int16_t fd_50F6_01F0[7];\n'
        'extern PortableWholeAudioInstrumentEntry fd_55B3_0C42[56];\n'
        + m290d[volume_start:volume_end] + "\n\n" + init_helpers + "\n",
        encoding="utf-8")
    helpers_obj = OUT / "mode1_initializer_slice.o"
    run([str(GCC), "-std=c11", "-Wall", "-Wextra", "-Werror", "-I", str(ROOT),
         "-c", str(helpers_path), "-o", str(helpers_obj)])
    state_obj = OUT / "audio_state.o"
    owners_obj = OUT / "source_state_owners.o"
    run([str(GCC), "-std=c11", "-Wall", "-Wextra", "-Werror", "-I", str(ROOT / "portable/whole_program/platform"),
         "-c", str(ROOT / "portable/whole_program/platform/audio_state.c"), "-o", str(state_obj)])
    run([str(GCC), "-std=c11", "-Wall", "-Wextra", "-Werror", "-I", str(ROOT / "build/workers/whole_program/generated"),
         "-c", str(ROOT / "build/workers/whole_program/generated/source_state_owners.c"), "-o", str(owners_obj)])
    harness_obj = OUT / "audio_state_preword_test.o"
    run([str(GCC), "-std=c11", "-Wall", "-Wextra", "-Werror", "-I", str(ROOT), "-c",
         str(ROOT / "portable/tests/whole_program/platform/audio_state_preword_test.c"), "-o", str(harness_obj)])
    exe = OUT / "audio_state_preword_test.exe"
    run([str(GCC), "-o", str(exe), str(harness_obj), str(helpers_obj), str(state_obj), str(owners_obj),
         str(linked_objects["src/data/d55B3_00B8.c"])])
    executed = subprocess.run([str(exe)], cwd=ROOT, text=True, capture_output=True)
    if executed.returncode:
        sys.stderr.write(executed.stdout)
        sys.stderr.write(executed.stderr)
        raise SystemExit(executed.returncode)
    report["linked_source_flow"] = {
        "source": "src/root/m277E.c:f_277E_017D -> f_277E_010A",
        "table": "src/data/d55B3_00B8.c:fd_55B3_0C42[56]",
        "owners": ["generated/source_state_owners.c", "portable/whole_program/platform/audio_state.c"],
        "executed": executed.stdout.strip(),
        "scope": "Mode-1 initializer source slice, not device detection or other hardware profiles.",
        "source_slice_sha256": sha(helpers_path.read_bytes()),
    }
    report["controls"] = {"lexical_comment_and_string_preservation": "PASS", "mutated_original_hash_rejected": "PASS"}
    report["controls"]["mapped_scalar_declarations_retained_for_later_owners"] = scalar_controls
    report["controls"]["unmapped_scalar_declarations_removed_by_default"] = "PASS"
    report["controls"]["unknown_deferred_scalar_rejected"] = "PASS"
    report["adapter_sha256"] = sha((ROOT / "portable/whole_program/conversions/audio_shared_state_preword.py").read_bytes())
    report["later_owner_plan_sha256"] = shared_state.resolve_later_scalar_owners("src/root/m277E.c")[1]
    report["behavior_overlay_catalog_sha256"] = sha(overlay_path.read_bytes())
    report["owner_header_sha256"] = sha((ROOT / "portable/whole_program/platform/audio_state.h").read_bytes())
    report["owner_implementation_sha256"] = sha((ROOT / "portable/whole_program/platform/audio_state.c").read_bytes())
    report_path = OUT / "audio_shared_state_preword_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {len(MODULES)} immutable-source audio TUs converted and compiled; mode-1 source initializer linked and executed")
    print(f"REPORT: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
