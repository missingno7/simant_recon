#!/usr/bin/env python3
"""One-time extraction of the pinned source bodies for source-conversion V1."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
TARGET_SOURCE = ROOT / "src/S25/m3BA4.c"
HELPER_SOURCE = ROOT / "src/root/m0BE8.c"
RECOVER_SOURCE = ROOT / "portable/tools/recover_source.py"
OUTPUT_TARGET = HERE / "get_my_rand_dirs_extracted.c"
OUTPUT_HELPERS = HERE / "get_dir_dis_extracted.c"
OUTPUT_IDENTITY = HERE / "source_identity_v1.json"
TARGET_NAME = "o25_3BA4_1686"
HELPER_NAMES = ("GetDir", "GetDis")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_recover_source():
    spec = importlib.util.spec_from_file_location("source_conversion_recover_source", RECOVER_SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load the pinned recover_source module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def once_write(path: Path, content: bytes) -> None:
    if path.exists():
        raise SystemExit(f"refusing to overwrite source-conversion V1 artifact: {path}")
    path.write_bytes(content)


def main() -> int:
    recover_source = load_recover_source()
    target_bytes = TARGET_SOURCE.read_bytes()
    helper_bytes = HELPER_SOURCE.read_bytes()
    target_text = target_bytes.decode("utf-8")
    # The source function is inside an explicit SCAFFOLD fence. Strip only the
    # two fence comments so the shared converter treats the body as source text.
    import re
    begin_matches = list(re.finditer(r"/\*\s*SCAFFOLD BEGIN:\s*o25_3BA4_1686\b.*?\*/", target_text))
    if len(begin_matches) != 1:
        raise RuntimeError("expected exactly one GetMyRandDirs scaffold fence")
    begin = begin_matches[0]
    end = re.search(r"/\*\s*SCAFFOLD END\s*\*/", target_text[begin.end():])
    if not end:
        raise RuntimeError("GetMyRandDirs scaffold fence is unclosed")
    end_after = begin.end() + end.end()
    target_text = target_text[:begin.start()] + target_text[begin.end():begin.end() + end.start()] + target_text[end_after:]
    helper_text = helper_bytes.decode("utf-8")

    target_body, target_start, target_end = recover_source.extract_named_function(target_text, TARGET_NAME)
    target_c, excluded, ax_tail = recover_source.transform(target_body)
    if excluded or ax_tail:
        raise RuntimeError(f"unexpected scaffold or tail transformation: excluded={excluded}, ax_tail={ax_tail}")

    helper_outputs = []
    helper_rows = []
    for name in HELPER_NAMES:
        body, line_start, line_end = recover_source.extract_named_function(helper_text, name)
        converted, excluded, ax_tail = recover_source.transform(body)
        if excluded or ax_tail:
            raise RuntimeError(f"unexpected helper transformation for {name}")
        helper_outputs.append(converted)
        helper_rows.append({"name": name, "source_line_start": line_start,
                            "source_line_end": line_end,
                            "body_sha256": sha(body.encode("utf-8"))})

    module_path = ROOT / "evidence/behavior/functions/o25_3BA4_1686/module.c"
    evidence_path = ROOT / "evidence/behavior/functions/o25_3BA4_1686/evidence.json"
    behavior_manifest_path = ROOT / "evidence/behavior/manifest.json"
    historical_manifest_path = ROOT / "layout/manifest.json"
    historical = json.loads(historical_manifest_path.read_text(encoding="utf-8"))
    historical_module = historical["modules"]["S25:3BA4"]
    function_claims = [row for row in historical_module.get("claims", [])
                       if row["name"] == TARGET_NAME]
    if function_claims or TARGET_NAME not in historical_module.get("scaffold", []):
        raise RuntimeError("historical manifest no longer marks this function as an unclaimed scaffold")

    identity = {
        "schema": "get-my-rand-dirs-source-conversion-identity-v1",
        "classification": {
            "behavioral_registry_status": json.loads(behavior_manifest_path.read_text(encoding="utf-8"))
                                         ["entries"][TARGET_NAME]["status"],
            "behavioral_evidence_path": "evidence/behavior/functions/o25_3BA4_1686/evidence.json",
            "behavioral_evidence_sha256": sha(evidence_path.read_bytes()),
            "reviewed_behavior_source_path": "evidence/behavior/functions/o25_3BA4_1686/module.c",
            "reviewed_behavior_source_sha256": sha(module_path.read_bytes()),
            "this_conversion_source_is_current_historical_scaffold": True,
            "scaffold_behavior_source_is_not_the_reviewed_BEHAVIOR_EXACT_module": True,
            "historical_exact_provenance": "SCAFFOLD; no per-function EXACT entry",
            "historical_exact_target_sha256": None,
            "historical_module_object_sha256": historical_module["object_sha256"],
            "historical_manifest_sha256": sha(historical_manifest_path.read_bytes()),
            "no_historical_claim_or_registry_change": True,
        },
        "conversion": {
            "generator_path": "portable/tools/recover_source.py",
            "generator_sha256": sha(RECOVER_SOURCE.read_bytes()),
            "target_source_path": "src/S25/m3BA4.c",
            "target_source_sha256": sha(target_bytes),
            "target_name": TARGET_NAME,
            "target_source_lines": [target_start, target_end],
            "target_body_sha256": sha(target_body.encode("utf-8")),
            "target_converted_sha256": sha(target_c.encode("utf-8")),
            "scalar_width_and_far_transform_only": True,
            "scaffold_fence_comments_removed_for_extraction": True,
            "target_excluded_scaffolds": excluded,
            "helper_source_path": "src/root/m0BE8.c",
            "helper_source_sha256": sha(helper_bytes),
            "translated_helpers": helper_rows,
            "helper_symbol_mapping": {
                "f_0BE8_0B21": "GetDir source body in src/root/m0BE8.c",
                "f_0BE8_0B83": "GetDis source body in src/root/m0BE8.c",
                "TileCanBeMovedOn": "portable sim_tile_can_be_moved_on, separately DOS-differential-tested; original helper executes in oracle lane",
            },
        },
        "outputs": {
            "target_path": "portable/tests/movement/source_conversion/get_my_rand_dirs_extracted.c",
            "helper_path": "portable/tests/movement/source_conversion/get_dir_dis_extracted.c",
            "identity_path": "portable/tests/movement/source_conversion/source_identity_v1.json",
        },
        "limits": [
            "The extracted GetMyRandDirs body is a historical source scaffold, not the separately reviewed BEHAVIOR_EXACT candidate module.",
            "Passing this finite conversion differential does not upgrade or revise historical exact or behavioral claims.",
            "TileCanBeMovedOn in the native lane uses the separately tested portable helper implementation; original DOS execution uses its original helper body.",
        ],
    }
    once_write(OUTPUT_TARGET, target_c.encode("utf-8"))
    once_write(OUTPUT_HELPERS, ("\n".join(helper_outputs)).encode("utf-8"))
    once_write(OUTPUT_IDENTITY, (json.dumps(identity, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({"status": "EXTRACTED", "target": str(OUTPUT_TARGET.relative_to(ROOT)),
                      "helpers": str(OUTPUT_HELPERS.relative_to(ROOT)),
                      "identity": str(OUTPUT_IDENTITY.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
