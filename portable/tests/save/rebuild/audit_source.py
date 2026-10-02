#!/usr/bin/env python3
"""Check source/binding anchors for the post-load reset/rebuild inventory.

This is a structural source audit only; it does not execute DOS or native code.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def body(path: Path, name: str) -> tuple[str, int, int]:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(r"\b" + re.escape(name) + r"\s*\([^;{}]*\)\s*\{", re.S)
    match = pattern.search(text)
    if not match:
        raise AssertionError(f"missing definition: {path}:{name}")
    start = match.end() - 1
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1], text.count("\n", 0, match.start()) + 1, text.count("\n", 0, i + 1)
    raise AssertionError(f"unclosed body: {path}:{name}")


def require_order(text: str, *needles: str) -> None:
    pos = -1
    for needle in needles:
        at = text.find(needle, pos + 1)
        if at < 0:
            raise AssertionError(f"missing/out-of-order anchor: {needle}")
        pos = at


def main() -> None:
    s09 = ROOT / "src/S09/m35F5.c"
    s08 = ROOT / "src/S08/m35F5.c"
    root0250 = ROOT / "src/root/m0250.c"
    root0be8 = ROOT / "src/root/m0BE8.c"
    root0e2e = ROOT / "src/root/m0E2E.c"
    s15 = ROOT / "src/S15/m384C.c"
    s14 = ROOT / "src/S14/m384C.c"
    sources = [s09, s08, root0250, root0be8, root0e2e, s15, s14]
    funcs = {
        "LoadGame": (s09, "LoadGame"),
        "o09_35F5_0D7A": (s09, "o09_35F5_0D7A"),
        "o09_35F5_0DBB": (s09, "o09_35F5_0DBB"),
        "RandYard": (s08, "RandYard"),
        "OverlayTileSet": (root0250, "OverlayTileSet"),
        "CenterEdit": (root0250, "CenterEdit"),
        "f_0250_0F2C": (root0250, "f_0250_0F2C"),
        "FullCount": (root0be8, "FullCount"),
        "CountAnts": (root0be8, "CountAnts"),
        "Feedback": (root0e2e, "Feedback"),
        "SetDefaultWindows": (s15, "SetDefaultWindows"),
        "SetDefaultWindPrompt": (s14, "SetDefaultWindPrompt"),
    }
    captured = {}
    for label, (path, name) in funcs.items():
        source = path.read_text(encoding="utf-8")
        b, first, last = body(path, name)
        captured[label] = {
            "path": path.relative_to(ROOT).as_posix(),
            "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
            "line_start": first,
            "line_end": last,
            "body_sha256": hashlib.sha256(b.encode()).hexdigest(),
        }

    reset = body(s09, "o09_35F5_0D7A")[0]
    require_order(reset, "fd_50F6_0354 = 1", "fd_50F6_0214 = 0L", "fd_50F6_0204 = 300L", "fd_50F6_0472 = 0L", "RandYard();")
    rebuild = body(s09, "o09_35F5_0DBB")[0]
    require_order(rebuild, "CurGndTileID = 1000", "OverlayTileSet(0, CurGndTileID)", "LifeA[x][y] = 0", "LifeB[x][y] = 0", "LifeR[x][y] = 0", "i = ListIndexA; i >= 0", "i = ListIndexB; i >= 0", "i = ListIndexR; i >= 0", "SetMyLife(", "FullCount();", "o15_384C_037F();", "f_0250_0FC4(MeLocX, MeLocY);", "SetDefaultWindPrompt(1);")
    before = body(s09, "o09_35F5_0D7A")[0]
    load = body(s09, "LoadGame")[0]
    assert load.find("o09_35F5_0D7A();") < load.find("read(")
    assert load.find("o09_35F5_0DBB();") > load.find("read(")
    yard = body(s08, "RandYard")[0]
    assert "RRand(0x7fff)" in yard and "RandWorld(" in yard
    assert "CountUpdate();" in body(root0be8, "FullCount")[0]
    assert "f_0E2E_000A();" in body(root0be8, "CountUpdate")[0]
    assert "RunTutor();" in body(root0e2e, "Feedback")[0]
    default_windows = body(s15, "SetDefaultWindows")[0]
    require_order(default_windows, "OpenCasteWindow();", "OpenModeWindow();", "YardToMap();", "OpenEditWindow();")

    binding_path = ROOT / "portable/tests/save/evidence/legacy-save-codec-v3/binding-map.json"
    binding = json.loads(binding_path.read_text(encoding="utf-8"))
    rows = binding.get("rows") or binding.get("records")
    if not isinstance(rows, list):
        raise AssertionError("unrecognized V3 binding-map row shape")
    row_index = {}
    for i, row in enumerate(rows):
        name = row.get("source_symbol") or row.get("symbol") or row.get("source_expression")
        if name:
            row_index[name.lstrip("&")] = int(row.get("row", row.get("index", i)))
    expected = {"Barrier": 104, "fd_50F6_0354": 297, "ListIndexA": 180,
                "ListIndexB": 181, "ListIndexR": 182}
    for name, expected_row in expected.items():
        if row_index.get(name) != expected_row:
            raise AssertionError(f"{name} row is {row_index.get(name)}, expected {expected_row}")
    for derived in ("LifeA", "LifeB", "LifeR", "CurGndTileID"):
        if derived in row_index:
            raise AssertionError(f"derived field unexpectedly present as SaveRec row: {derived}")
    reset_controls = ("fd_50F6_0214", "fd_50F6_0204", "fd_50F6_0472")
    if any(name in row_index for name in reset_controls):
        raise AssertionError("pre-load reset control unexpectedly serialized")
    if "fd_50F6_0204 = 0;" not in yard:
        raise AssertionError("RandYard no longer overwrites the reset deadline")

    print(json.dumps({
        "schema": "save-rebuild-source-audit-v1",
        "status": "STRUCTURAL_SOURCE_AUDIT_ONLY",
        "source_files": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        "binding_map": {
            "path": binding_path.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(binding_path.read_bytes()).hexdigest(),
            "row_count": len(rows),
        },
        "functions": captured,
        "save_rows": expected,
        "checks": {
            "reset_before_first_read": True,
            "rebuild_after_record_reads": True,
            "life_planes_are_rebuilt_not_serialized": True,
            "inclusive_reverse_replay_preserved": True,
            "fullcount_reaches_feedback": True,
            "reset_controls_not_in_saved_rows": True,
            "native_dos_differential": False,
        },
    }, indent=2))


if __name__ == "__main__":
    main()



