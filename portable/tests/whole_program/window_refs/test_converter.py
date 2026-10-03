#!/usr/bin/env python3
"""Source-shaped checks for the explicitly bounded window wire converter."""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "portable/whole_program/conversions"))
from windows import convert_window_source  # noqa: E402


def converted(name: str):
    return convert_window_source((ROOT / "src/root" / name).read_text(encoding="utf-8"))


def main() -> None:
    repoint = converted("m2505.c")
    assert not repoint.unresolved, repoint.unresolved
    assert "extern SimWindowRefRegistry sim_window_ref_registry;" in repoint.text
    assert repoint.replacements["repoint_owner_bind"] == 1
    start = repoint.text.index("void _fastcall RepointObjects")
    stop = repoint.text.index("int _fastcall f_2505_00AA", start)
    body = repoint.text[start:stop]
    ordered = [
        "sim_window_ref_registry_repoint_handle_signed",
        "n = sim_window_wire_read_i16(w, 0x0c)",
        "p = w + n * 4 + 0x2c",
        "for (i = 0; i < n; i++)",
        "sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry, (char *)w)[i] = p",
        "p += sim_window_wire_read_i16(p, 0x22)",
    ]
    positions = [body.index(piece) for piece in ordered]
    assert positions == sorted(positions), positions
    assert body.index("window_index >= 45") < body.index("w = f_2505_0006(win)")
    assert "((char far * far *)(w + 0x2c))" not in body

    mutated = (ROOT / "src/root/m2505.c").read_text(encoding="utf-8").replace(
        "p += *(int far *)(p + 0x22);",
        "p += *(int far *)(p + 0x24);", 1)
    negative = convert_window_source(mutated)
    assert any("object-size advance" in issue for issue in negative.unresolved), \
        negative.unresolved

    load = converted("m20E8.c")
    assert not load.unresolved, load.unresolved
    load_body = load.text[load.text.index("void far win_LoadWindow"):]
    assert load_body.index("RepointObjects(win)") < load_body.index(
        "window type-4 runtime clear failed") < load_body.index(
        "window text Handle clear failed")
    assert "window text Handle clear failed\"); return;" in load_body
    assert "sim_window_clear_draw_hooks(win_drawHooks, 45);" in load.text
    assert "_fmemset(win_drawHooks, 0, 0xb4)" not in load.text
    assert '_Static_assert(offsetof(struct Win, object_table_wire) == 0x2c' not in load.text

    unlock = converted("m23AE.c")
    assert not unlock.unresolved, unlock.unresolved
    assert unlock.replacements["object_handle_addresses"] == 2
    assert unlock.replacements["unresolved_handle_guard"] == 1
    assert unlock.replacements["unload_registry_detach"] == 1
    assert 'Punt("unresolved serialized window Handle"); return;' in unlock.text
    assert "((struct Obj *)sim_window_ref_registry_objects_for_buffer" in unlock.text
    assert unlock.text.index("win_offsets[n] =") < unlock.text.index(
        "sim_window_ref_registry_detach")
    assert '_Static_assert(sizeof(struct Obj) == 0x38' in unlock.text

    for name in ("m22BF.c", "m21FA.c", "m218D.c"):
        result = converted(name)
        assert not result.unresolved, (name, result.unresolved)
        assert result.replacements["wire_table_subscript"] > 0
    formats = converted("m22BF.c")
    assert formats.replacements["object_handle_dereferences"] == 6
    print("PASS: six frozen window TUs map their bounded wire-pointer forms")


if __name__ == "__main__":
    main()
