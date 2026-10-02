"""Add a source-faithful S24 history snapshot and bounded removal lowering over Next9.

Next9, its producer, and the frozen historical source remain unchanged. Next10
changes only the generated S24 translation unit and is diagnostic-only.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
NEXT9 = ROOT / "portable/tools/recover_source_next9.py"
NEXT9_SHA = "c9429350a6c8bc9453e0a34c5e0f13f5c5d10d34ac643e8271e7db00c4beb3ae"
NEXT9_DIR = ROOT / "build/workers/recovered_source_next9/generated"
NEXT9_PROVENANCE_SHA = "9821efeca4abdaf177f748c5179d9c7138618751641780b589baf7ac2efdf4ff"
NEXT9_PRIOR_PROVENANCE_SHA = "e3547a24caab7a9037f4b1aa6727078a8f8759a6feba65bcca7dbbcd6ff10156"
NEXT9_REVIEW = ROOT / "portable/tests/recovered/evidence/next9-profile-regeneration-review-20261002/review.json"
NEXT9_REVIEW_SHA = "38a3e50f42bcf18f7e14ae3ba20120a77880467b728095c94593fc7184333eed"
NEXT9_REGENERATED_PROVENANCE = ROOT / "portable/tests/recovered/evidence/next9-profile-regeneration-review-20261002/regenerated-provenance.json"
NEXT9_HEADER_SHA = "7e01016c0c3a2326176f0a5ce487cc3f47e6d808518687edf95f6e70a9dcc835"
NEXT9_STATE_SHA = "7d514c15c50d89798c1b7f809904ab65d5e0e446b0731ea0e71afd45234cafca"
NEXT9_S24_SHA = "585dabce10299983019777ec5b193e91f952b9e2cd848960472ccf49304a2059"
SOURCE = ROOT / "src/S24/m39C7.c"
SOURCE_SHA = "3de9615a57dbe35eacd073726b451478dc5b12396360501631d7553b6139e240"
OUT_DIR = "build/workers/recovered_source_next10/generated"
MODULE = "S24_m39C7"
TARGET = "ToggleHistButton"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"expected one {label} anchor, found {text.count(old)}")
    return text.replace(old, new, 1)


def main() -> int:
    for path, expected, label in (
        (NEXT9, NEXT9_SHA, "Next9 wrapper"),
        (NEXT9_DIR / "provenance.json", NEXT9_PROVENANCE_SHA, "Next9 provenance"),
        (NEXT9_REGENERATED_PROVENANCE, NEXT9_PROVENANCE_SHA,
         "reviewed Next9 regenerated provenance"),
        (NEXT9_REVIEW, NEXT9_REVIEW_SHA, "Next9 profile regeneration review"),
        (NEXT9_DIR / "recovered_state.h", NEXT9_HEADER_SHA, "Next9 state header"),
        (NEXT9_DIR / "recovered_state.c", NEXT9_STATE_SHA, "Next9 state source"),
        (NEXT9_DIR / f"{MODULE}.c", NEXT9_S24_SHA, "Next9 generated S24"),
        (SOURCE, SOURCE_SHA, "frozen historical S24 source")):
        if sha(path.read_bytes()) != expected:
            raise RuntimeError(f"pinned {label} changed: {path}")

    review = json.loads(NEXT9_REVIEW.read_text(encoding="utf-8"))
    if review.get("status") != "PASS" or \
       review.get("prior_profile_sha256") != NEXT9_PRIOR_PROVENANCE_SHA or \
       review.get("current_profile_sha256") != NEXT9_PROVENANCE_SHA:
        raise RuntimeError("reviewed Next9 parent lineage changed")
    if not review.get("all_other_production_inputs_unchanged") or \
       not review.get("all_other_engine_source_object_inputs_unchanged"):
        raise RuntimeError("Next9 regeneration review no longer validates unchanged parent inputs")

    parent_prov = json.loads((NEXT9_DIR / "provenance.json").read_text(encoding="utf-8"))
    parent_modules = {row["name"]: row["generated_sha256"] for row in parent_prov["modules"]}
    parent_objects = {}
    for row in parent_prov["modules"]:
        compile_record = row.get("compile", {})
        object_hash = compile_record.get("next9_object_sha256")
        if not object_hash:
            raise RuntimeError(f"Next9 current object hash missing for {row['name']}")
        object_path = NEXT9_DIR / f"{row['name']}.o"
        if sha(object_path.read_bytes()) != object_hash:
            raise RuntimeError(f"Next9 object differs from reviewed current parent: {row['name']}")
        parent_objects[row["name"]] = object_hash
    if len(parent_modules) != 25 or parent_modules.get(MODULE) != NEXT9_S24_SHA:
        raise RuntimeError("pinned Next9 profile is not the expected 25-TU profile")
    extension9 = parent_prov.get("versioned_profile_extension_next9", {})
    if extension9.get("inherited_module_generated_hashes") != parent_modules:
        raise RuntimeError("Next9 inherited module hash map does not match its current profile")

    argv = sys.argv[1:]
    if "--out" in argv:
        out_arg = argv[argv.index("--out") + 1]
    else:
        out_arg = OUT_DIR
    out = (ROOT / out_arg).resolve() if not Path(out_arg).is_absolute() else Path(out_arg).resolve()
    if out == NEXT9_DIR.resolve() or NEXT9_DIR.resolve() in out.parents:
        raise RuntimeError("Next10 output may not target or nest inside the immutable Next9 profile")
    out.mkdir(parents=True, exist_ok=True)
    # Consume the reviewed current artifact snapshot directly. Never invoke the
    # Next9 producer here: its output is shared and is an immutable parent input.
    shutil.copytree(NEXT9_DIR, out, dirs_exist_ok=True)
    prov_path = out / "provenance.json"
    provenance = json.loads(prov_path.read_text(encoding="utf-8"))
    current = {row["name"]: row["generated_sha256"] for row in provenance["modules"]}
    if current != parent_modules:
        raise RuntimeError("fresh Next9 layer does not reproduce every pinned Next9 TU")
    for name, expected in (("recovered_state.h", NEXT9_HEADER_SHA),
                           ("recovered_state.c", NEXT9_STATE_SHA)):
        if sha((out / name).read_bytes()) != expected:
            raise RuntimeError(f"fresh Next9 layer changed pinned {name}")

    module = next(row for row in provenance["modules"] if row["name"] == MODULE)
    module_path = out / f"{MODULE}.c"
    before = module_path.read_text(encoding="utf-8")
    if sha(before.encode("utf-8")) != NEXT9_S24_SHA:
        raise RuntimeError("fresh Next9 S24 does not match pinned source")
    buggy = "_fmemmove(&shownGraphs[i], &shownGraphs[i + 1], (4 - i) * 2);"
    lowered = ("/* Native lowering: omit the one-past source read; destination slot 3 is "
               "immediately replaced by the sentinel. */\n"
               "                _fmemmove(&shownGraphs[i], &shownGraphs[i + 1], (3 - i) * 2);")
    after, move_replacements = before.replace(buggy, lowered), before.count(buggy)
    if move_replacements != 1:
        raise RuntimeError(f"expected exactly one source overread expression, found {move_replacements}")
    accessor = r'''

/* Snapshot only; S24 remains the sole owner of these private UI arrays.
 * histColor has 20 source elements, while valid history graph IDs are 0..9. */
void S24_GetHistoryUiSnapshot(int16_t graph_colors[4],
                              int16_t history_colors[10],
                              int16_t shown_graphs[4],
                              int16_t *shown_graph_count)
{
    int16_t i;
    int16_t count = 0;
    for (i = 0; i < 4; ++i) {
        graph_colors[i] = graphColors[i];
        shown_graphs[i] = shownGraphs[i];
        if (shownGraphs[i] != (int16_t)0x8000)
            ++count;
    }
    for (i = 0; i < 10; ++i)
        history_colors[i] = histColor[i];
    *shown_graph_count = count;
}
'''
    after += accessor
    module_path.write_text(after, encoding="utf-8", newline="")

    changed_modules = []
    next9_relative = str(NEXT9_DIR.relative_to(ROOT)).replace("\\", "/")
    next10_relative = str(out.relative_to(ROOT)).replace("\\", "/")
    for row in provenance["modules"]:
        name = row["name"]
        parent_generated_path = row["generated"]
        new_hash = sha((out / f"{name}.c").read_bytes())
        if new_hash != parent_modules[name]:
            changed_modules.append(name)
        if name != MODULE and new_hash != parent_modules[name]:
            raise RuntimeError(f"Next10 changed non-S24 translation unit {name}")
        parent_compile = dict(row["compile"])
        parent_command = list(parent_compile["command"])
        command = [arg.replace(next9_relative, next10_relative).replace(
            next9_relative.replace("/", "\\"), next10_relative.replace("/", "\\"))
            for arg in parent_command]
        compiled = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if compiled.returncode:
            raise RuntimeError(f"Next10 TU {name} failed strict compile:\n" +
                               compiled.stdout + compiled.stderr)
        current_object_hash = sha(Path(command[-1]).read_bytes())
        row["parent_profile_generated_path"] = parent_generated_path
        row["generated"] = str((out / f"{name}.c").relative_to(ROOT)).replace("\\", "/")
        row["generated_sha256"] = new_hash
        row["compile"]["parent_profile_command"] = parent_command
        row["compile"]["parent_profile_object_sha256"] = parent_objects[name]
        old_lowered = parent_compile.get("lowered_object_sha256")
        if old_lowered and old_lowered != parent_objects[name]:
            row["compile"]["parent_profile_lowered_object_sha256"] = old_lowered
        row["compile"]["command"] = command
        row["compile"]["passed"] = True
        row["compile"]["diagnostics"] = compiled.stdout + compiled.stderr
        row["compile"]["lowered_object_sha256"] = current_object_hash
        row["compile"]["next10_recompiled"] = True
        row["compile"]["next10_command"] = command
        row["compile"]["next10_object_sha256"] = current_object_hash
    if changed_modules != [MODULE]:
        raise RuntimeError(f"Next10 must change exactly S24, changed={changed_modules}")
    if sum(bool(row["compile"].get("next10_recompiled")) for row in provenance["modules"]) != 25:
        raise RuntimeError("Next10 did not recompile all 25 translation units")
    module["generated_sha256"] = sha(module_path.read_bytes())
    module["compile"]["passed"] = True

    source_text = SOURCE.read_text(encoding="latin1")
    source_lines = source_text.splitlines()
    source_overread_lines = [(n, line.strip()) for n, line in enumerate(source_lines, 1)
                             if "_fmemmove(&shownGraphs[i]" in line]
    if len(source_overread_lines) != 1:
        raise RuntimeError("frozen ToggleHistButton overread source anchor changed")
    provenance["versioned_profile_extension_next10"] = {
        "schema": "simant-recovered-source-profile-extension-v1",
        "id": "s24-history-ui-snapshot-and-bounded-removal-next10-v1",
        "status": "DIAGNOSTIC_ONLY_NOT_PRODUCTION",
        "parent_profile": "Next9",
        "parent_wrapper_path": str(NEXT9.relative_to(ROOT)).replace("\\", "/"),
        "parent_wrapper_sha256": NEXT9_SHA,
        "parent_profile_provenance_sha256": NEXT9_PROVENANCE_SHA,
        "parent_profile_prior_provenance_sha256": NEXT9_PRIOR_PROVENANCE_SHA,
        "parent_regeneration_review": {
            "path": str(NEXT9_REVIEW.relative_to(ROOT)).replace("\\", "/"),
            "sha256": NEXT9_REVIEW_SHA,
            "status": review["status"],
            "cause": review["cause"],
            "same_reviewed_source_state_objects": True},
        "parent_profile_regenerated_provenance_path":
            str(NEXT9_REGENERATED_PROVENANCE.relative_to(ROOT)).replace("\\", "/"),
        "parent_profile_regenerated_provenance_sha256": NEXT9_PROVENANCE_SHA,
        "parent_generated_state_sha256": {"recovered_state.h": NEXT9_HEADER_SHA,
                                           "recovered_state.c": NEXT9_STATE_SHA},
        "parent_module_generated_hashes": parent_modules,
        "parent_module_object_hashes": parent_objects,
        "selected_module": MODULE,
        "selected_function": TARGET,
        "source_anchor": {"path": "src/S24/m39C7.c", "sha256": SOURCE_SHA,
                          "line": source_overread_lines[0][0],
                          "text": source_overread_lines[0][1]},
        "native_lowering": {
            "generated_path": str(module_path.relative_to(ROOT)).replace("\\", "/"),
            "before_sha256": NEXT9_S24_SHA,
            "after_sha256": sha(module_path.read_bytes()),
            "overread_expression_replacements": move_replacements,
            "old_expression": "(4 - i) * 2",
            "new_expression": "(3 - i) * 2",
            "semantic_reason": "The DOS count copies one word beyond shownGraphs[3] for every removal position; the destination's fourth word is immediately overwritten with 0x8000. Copy only the remaining in-array words, avoiding host out-of-bounds access while preserving the post-call four-word list.",
            "original_dos_count_retained_in_oracle": True},
        "snapshot_api": {"name": "S24_GetHistoryUiSnapshot",
                         "signature": "void S24_GetHistoryUiSnapshot(int16_t graph_colors[4], int16_t history_colors[10], int16_t shown_graphs[4], int16_t *shown_graph_count)",
                         "source_storage": {"graphColors": 4, "histColor": 20,
                                            "valid_graph_ids": 10, "shownGraphs": 4,
                                            "histShown": 10, "freeColors": 1},
                         "exported_history_color_elements": 10,
                         "shown_graph_count": "number of non-sentinel elements among shownGraphs[0..3]"},
        "profile_recompilation": {"module_count": len(provenance["modules"]),
                                  "recompiled_module_count": 25,
                                  "changed_generated_modules": changed_modules,
                                  "parent_next9_objects_preserved_as_metadata": True,
                                  "primary_compile_lowered_object_sha256_is_current_next10_object": True,
                                  "state_files_byte_identical_to_next9": True},
        "limits": ["Diagnostic-only profile; no production build/admission selection.",
                   "The accessor copies current S24 UI state and does not add a second owner.",
                   "Removal lowering equivalence is accepted only with the paired event packet."]}
    prov_path.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8", newline="")
    print(json.dumps({"status": "DIAGNOSTIC_ONLY_NOT_PRODUCTION",
                      "out": str(out), "changed_modules": changed_modules,
                      "TUs_recompiled": 25, "snapshot_api": "S24_GetHistoryUiSnapshot",
                      "source_histColor_elements": 20, "valid_graph_ids": 10,
                      "generated_S24_sha256": sha(module_path.read_bytes())}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
