#!/usr/bin/env python3
"""Build the versioned next3 profile: next2 plus balloon state globals only.

The historical translator remains pinned and unmodified. This wrapper adds
twelve typed, source/layout-grounded state views before delegating generation.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE_PATH = ROOT / "portable/tools/recover_source.py"
BASE_SHA256 = "c1fd7616c392d39ebe4574e6ccde85b4e7f79205d21afcfbcb7ead249d5ffc50"
LAYOUT_PATH = ROOT / "layout/symbols.json"
SOURCE_PATH = ROOT / "src/root/m0250.c"
EXTENSION_ID = "balloon-source-state-next3-v1"

BALLOON_DECLARATIONS = {
    # Four displayed (last committed) point/plane pairs.
    "fd_50F6_08DE": ("RecoveredXY", [], "EggBalloons displayed point"),
    "fd_50F6_0AD8": ("int16_t", [], "EggBalloons displayed plane"),
    "fd_50F6_09F2": ("RecoveredXY", [], "FightBalloons displayed point"),
    "fd_50F6_0B06": ("int16_t", [], "FightBalloons displayed plane"),
    "fd_50F6_0A8A": ("RecoveredXY", [], "QueenBalloons displayed point"),
    "fd_50F6_0C3A": ("int16_t", [], "QueenBalloons displayed plane"),
    "fd_50F6_0AB2": ("RecoveredXY", [], "RestBalloons displayed point"),
    "fd_50F6_0D9A": ("int16_t", [], "RestBalloons displayed plane"),
    # Four pending plane words; pending point and active globals already exist
    # in the base profile because DoAntSim directly resets/reads them.
    "fd_50F6_0ACA": ("int16_t", [], "EggBalloons pending plane"),
    "fd_50F6_0AEA": ("int16_t", [], "FightBalloons pending plane"),
    "fd_50F6_0B08": ("int16_t", [], "QueenBalloons pending plane"),
    "fd_50F6_0D68": ("int16_t", [], "RestBalloons pending plane"),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_base():
    actual = sha(BASE_PATH.read_bytes())
    if actual != BASE_SHA256:
        raise RuntimeError(f"base generator pin changed: expected {BASE_SHA256}, got {actual}")
    spec = importlib.util.spec_from_file_location("simant_recover_source_next3_base", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import the pinned base source generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def balloon_state_extension(base) -> dict[str, object]:
    """Validate source declarations and layout addresses, then return field evidence."""
    source_bytes = SOURCE_PATH.read_bytes()
    source = source_bytes.decode("utf-8")
    symbols_doc = json.loads(LAYOUT_PATH.read_text(encoding="utf-8"))
    symbols = symbols_doc["data"]
    evidence: dict[str, dict[str, object]] = {}
    extra = {}
    for name, (state_type, dims, role) in BALLOON_DECLARATIONS.items():
        if name in base.SOURCE_EXTRA_STATE_DECLARATIONS:
            raise RuntimeError(f"balloon field already exists in base generator: {name}")
        symbol = symbols.get(name)
        if symbol is None or int(symbol.get("seg", -1)) != 0x50F6:
            raise RuntimeError(f"missing or wrong-segment layout row for {name}")
        if state_type == "RecoveredXY" and (int(symbol.get("off", -1)) & 1):
            raise RuntimeError(f"unaligned source point storage: {name}")

        if state_type == "RecoveredXY":
            declaration_pattern = rf"(?m)^\s*extern\s+Pnt\s+far\s+{re.escape(name)}\s*;"
            expected_declaration = f"extern Pnt far {name};"
        else:
            declaration_pattern = rf"(?m)^\s*extern\s+int\s+far\s+{re.escape(name)}\s*;"
            expected_declaration = f"extern int far {name};"
        match = re.search(declaration_pattern, source)
        if match is None:
            raise RuntimeError(f"source declaration anchor missing for {name}")
        line = source.count("\n", 0, match.start()) + 1
        record = {
            "role": role,
            "source_path": SOURCE_PATH.relative_to(ROOT).as_posix(),
            "source_sha256": sha(source_bytes),
            "source_line": line,
            "source_declaration": expected_declaration,
            "layout_path": LAYOUT_PATH.relative_to(ROOT).as_posix(),
            "layout_sha256": sha(LAYOUT_PATH.read_bytes()),
            "layout_segment": int(symbol["seg"]),
            "layout_offset": int(symbol["off"]),
            "layout_grounding": symbol.get("grounding"),
            "state_type": state_type,
            "state_dims": dims,
            "storage_bytes": 4 if state_type == "RecoveredXY" else 2,
            "resolution": "source declaration plus exact layout symbol; BSS bytes retain zero initialization",
        }
        evidence[name] = record
        extra[name] = {
            "type": state_type,
            "dims": dims,
            "source_declaration": expected_declaration,
            "layout_grounding": f"layout/symbols.json {int(symbol['seg']):04X}:{int(symbol['off']):04X}",
            "initialization": "zero-initialized BSS source global",
            "next3_balloon_evidence": record,
        }
    base.SOURCE_EXTRA_STATE_DECLARATIONS.update(extra)
    return {
        "schema": "simant-recovered-source-profile-extension-v1",
        "id": EXTENSION_ID,
        "status": "DIAGNOSTIC_ONLY_NOT_PRODUCTION",
        "base_generator_path": BASE_PATH.relative_to(ROOT).as_posix(),
        "base_generator_sha256": BASE_SHA256,
        "wrapper_path": Path(__file__).resolve().relative_to(ROOT).as_posix(),
        "wrapper_sha256": sha(Path(__file__).read_bytes()),
        "added_fields": evidence,
        "limits": [
            "Adds only twelve BSS source-state views: four displayed point/plane pairs and four pending planes.",
            "Existing active and pending-point state fields are not replaced or duplicated.",
            "Does not integrate the recovered engine, claim behavioral equivalence, or add persistent shadow state.",
        ],
    }


def main() -> int:
    base = _load_base()
    extension = balloon_state_extension(base)
    cli_args = sys.argv[1:]
    out_arg = None
    for index, arg in enumerate(cli_args):
        if arg == "--out" and index + 1 < len(cli_args):
            out_arg = cli_args[index + 1]
            break
    if out_arg is None:
        out_arg = "build/workers/recovered_source_next3/generated"
        cli_args.extend(["--out", out_arg])
        sys.argv = [sys.argv[0], *cli_args]
    result = base.main()
    if result != 0:
        return result
    out = Path(out_arg)
    if not out.is_absolute():
        out = ROOT / out
    provenance_path = out.resolve() / "provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    provenance["versioned_profile_extension"] = extension
    provenance_path.write_text(json.dumps(provenance, indent=2) + "\n",
                               encoding="utf-8", newline="")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
