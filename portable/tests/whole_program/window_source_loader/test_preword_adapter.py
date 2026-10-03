#!/usr/bin/env python3
"""Focused controls for the source-side window-global adapter."""
from pathlib import Path
import re

from portable.whole_program.conversions.windows import convert_window_source
from portable.whole_program.conversions.window_loader import (
    _code_mask,
    adapt,
    convert_window_global_declarations,
)


ROOT = Path(__file__).resolve().parents[4]


def require(test: bool, message: str) -> None:
    if not test:
        raise SystemExit("FAIL: " + message)


def main() -> None:
    expected = {"m20E8.c", "m21FA.c", "m22BF.c", "m23AE.c", "m2505.c"}
    for name in sorted(expected):
        path = ROOT / "src/root" / name
        source = path.read_text(encoding="utf-8")
        sidecar = convert_window_source(source)
        require(not sidecar.unresolved, name + " sidecar conversion control")
        converted = adapt(sidecar.text, name)
        require(not converted.unresolved, name + " global adapter control")
        require('#include "portable/whole_program/window_source_globals.h"' in converted.text,
                name + " includes the common source-global owner")
    loader = adapt(convert_window_source(
        (ROOT / "src/root/m20E8.c").read_text(encoding="utf-8")).text, "m20E8.c")
    require(loader.replacements.get("typed_hook_declaration") == 1 and
            loader.replacements.get("typed_offsets_declaration") == 1 and
            loader.replacements.get("dynamic_color_declaration") == 1 and
            loader.replacements.get("color_reservation") == 1 and
            loader.replacements.get("dos_color_copy_width") == 1,
            "loader owner declarations and dynamic allocation boundary each match once")
    reserve = loader.text.index("sim_window_source_reserve_colors(win_numOfColors)")
    load81 = loader.text.index("db_LoadObject(0x81, 0)")
    require(reserve < load81, "checked color allocation precedes source 0x81 load")

    # Three historical consumers declared the same byte as unsigned. Their
    # original read semantics are retained without an incompatible extern.
    for rel in ("m1629.c", "m208F.c"):
        source = (ROOT / "src/root" / rel).read_text(encoding="utf-8")
        result = adapt(convert_window_source(source).text, rel)
        require(not result.unresolved, rel + " unsigned profile source adaptation")
        require("extern unsigned char near g_5A97" not in result.text and
                "((uint8_t)g_5A97)" in result.text,
                rel + " uses a casted unsigned view of canonical char storage")
    s23 = (ROOT / "src/S23/m39C7.c").read_text(encoding="utf-8")
    s23_result = adapt(convert_window_source(s23).text, "S23/m39C7.c")
    require(not s23_result.unresolved and "((uint8_t)g_5A97)" in s23_result.text,
            "S23 unsigned profile view preserves source promotion")

    profile_consumers = []
    for path in sorted((ROOT / "src").rglob("*.c")):
        source = path.read_text(encoding="utf-8")
        if not re.search(r"\bg_5A97\b", _code_mask(source)):
            continue
        sidecar = convert_window_source(source)
        require(not sidecar.unresolved, path.relative_to(ROOT).as_posix() +
                " window-sidecar precondition")
        result = adapt(sidecar.text, path.name)
        require(not result.unresolved, path.relative_to(ROOT).as_posix() +
                " shared profile-byte owner")
        require("extern char near g_5A97" not in result.text and
                "extern unsigned char near g_5A97" not in result.text and
                '#include "portable/whole_program/window_source_globals.h"' in result.text,
                path.relative_to(ROOT).as_posix() + " uses one profile storage owner")
        profile_consumers.append(path.relative_to(ROOT).as_posix())
    require(len(profile_consumers) >= 20,
            "all source C consumers of the shared profile byte are audited")

    literal_control = (
        'extern unsigned char near g_5A97;\n'
        'static const char *a = "g_5A97"; /* g_5A97 */\n'
        'int f(void) { return g_5A97 == 2; }\n')
    literal_result = convert_window_global_declarations(literal_control)
    require(not literal_result.unresolved and '"g_5A97"' in literal_result.text and
            "/* g_5A97 */" in literal_result.text and
            "return ((uint8_t)g_5A97) == 2" in literal_result.text,
            "profile lexical adapter rewrites code identifiers only")

    malformed_color = (
        "extern char far win_colors[][5];\n"
        "void f(void) { (void)win_colors[0][0]; }\n")
    require(convert_window_global_declarations(malformed_color).unresolved,
            "unexpected color row extent fails closed")
    unsigned_writer = (
        "extern unsigned char near g_5A97;\n"
        "void f(void) { g_5A97 = 2; }\n")
    require(convert_window_global_declarations(unsigned_writer).unresolved,
            "unsigned profile write fails closed")
    print("PASS pre-word source window adapter: five window TUs, " +
          str(len(profile_consumers)) + " profile C consumers, and negative controls")


if __name__ == "__main__":
    main()
