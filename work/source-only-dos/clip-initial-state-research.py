#!/usr/bin/env python3
"""Separate original-image research: observe only typed g_5AAC null semantics.

This is intentionally not imported by clip-pointer-probe.py and is never a
source-only build input. It maps the locked original image, reads the typed far
pointer before any guest instruction executes, and emits no raw bytes/words.
It does not execute DOS, RTLink, or the MSC startup runtime.
"""
from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "tools"))

import behavior
import exe
import functions
import match


def file_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    lock = json.loads((ROOT / "layout/oracle.lock.json").read_text(encoding="utf-8"))
    image_identity = lock["inputs"]["SIMANT.EXE"]
    image_path = ROOT / "assets/SIMANT.EXE"
    if file_sha(image_path) != image_identity["sha256"]:
        raise SystemExit("original executable does not match layout/oracle.lock.json")
    tool_paths = [ROOT / "work/source-only-dos/clip-initial-state-research.py",
                  ROOT / "layout/oracle.lock.json", ROOT / "layout/functions.json",
                  ROOT / "layout/symbols.json", ROOT / "layout/manifest.json",
                  ROOT / "tools/behavior.py",
                  ROOT / "tools/exe.py", ROOT / "tools/functions.py", ROOT / "tools/match.py",
                  ROOT / "tools/modctx.py", ROOT / "tools/modules.py"]
    research_tools = [{"path": path.relative_to(ROOT).as_posix(), "sha256": file_sha(path)}
                      for path in tool_paths]

    machine = behavior.Machine(SimpleNamespace(function=functions.get("main")))
    address = match.DGROUP_SEG * 16 + 0x5AAC
    pointer_offset, pointer_segment = struct.unpack("<HH", machine.read(address, 4))
    observation = {
        "boundary": "original image loaded into research VM; before any guest instruction",
        "typed_value": "null far pointer" if pointer_offset == 0 and pointer_segment == 0
        else "non-null far pointer",
        "is_null": pointer_offset == 0 and pointer_segment == 0,
        "segment_is_DGROUP": pointer_segment == match.DGROUP_SEG,
        "targets_g_5A9C": pointer_segment == match.DGROUP_SEG and pointer_offset == 0x5A9C,
        "raw_pointer_words_emitted": False,
        "startup_limit": "no DOS, RTLink, or CRT startup executed",
    }
    result = {
        "schema": "simant-clip-initial-state-research-v1",
        "purpose": "original-oracle typed-null corroboration, separate from source-only build proof",
        "original_input": {"path": "assets/SIMANT.EXE", "sha256": image_identity["sha256"],
                           "size": image_identity["size"], "identity_source": "layout/oracle.lock.json"},
        "tool_inputs": research_tools,
        "field": {"symbol": "g_5AAC", "DGROUP_offset": "5AAC", "type_hypothesis": "struct Rect far * near",
                  "storage_extent": 4},
        "observation": observation,
        "interpretation_limit": "This only observes the loaded image before guest execution. It neither proves the historical producing TU nor stands in for a source initializer or DOS CRT startup execution.",
    }
    out = ROOT / "work/source-only-dos/clip-initial-state-research-v1.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
