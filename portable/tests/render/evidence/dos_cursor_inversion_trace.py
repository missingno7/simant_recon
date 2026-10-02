"""Trace the original GRectInvOutline helper's g_913C command sequence.

The helper executes from the frozen DOS image.  Its g_913C indirect target is
replaced by the original empty far-return routine as a callback recorder; this
establishes the helper-to-driver rectangle ABI and order, not VGA memory output.
The EGA/VGA indexed XOR operation is independently grounded in S00 assembly.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
import behavior
import exe
import functions


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def trace(width: int) -> dict:
    function = functions.get("f_1CE2_032B")
    vectors = {exe.MANAGER_SEG * 16 + vector.offset: vector
               for vector in exe.load().vectors}
    pair = SimpleNamespace(function=function, sequence_targets=frozenset(),
                           sequence_function=lambda name: functions.get(name),
                           vectors=vectors)
    machine = behavior.Machine(pair)
    callback_symbol = behavior.symbol("f_1B4E_000C")
    callback = behavior.Callback(
        stack_words=4,
        handler=lambda current, args: current.state.setdefault("calls", []).append(args))
    far_pointer = callback_symbol["off"].to_bytes(2, "little") + \
        callback_symbol["seg"].to_bytes(2, "little")
    case = behavior.Case(
        label=f"grect-inv-outline-width-{width}",
        args=[10, 20, 30, 40, width],
        writes=[(behavior.symbol_address("g_913C"), far_pointer)],
        callbacks={"f_1B4E_000C": callback},
        return_kind="void")
    result = machine.run(case, function="f_1CE2_032B")
    return {"width": width, "calls": result["state"].get("calls", []),
            "raw_trace": result["raw_trace"], "blocks": result["blocks"]}


def main() -> None:
    positive = trace(2)
    negative = trace(0)
    expected = [[12, 22, 28, 20], [12, 38, 28, 40],
                [12, 20, 10, 40], [30, 20, 28, 40]]
    if positive["calls"] != expected:
        raise AssertionError(f"original positive callback trace changed: {positive}")
    if negative["calls"]:
        raise AssertionError(f"zero-width negative contrast called driver: {negative}")

    source_paths = (
        "src/root/m1CE2.c", "src/S00/m3126.asm", "src/S00/m31AD.asm",
        "src/root/m1B4E.asm", "src/root/m205F.c", "tools/behavior.py",
        "tools/functions.py", "portable/ui_model/windows/overview_view.c",
        "portable/ui_model/windows/overview_view.h",
        "portable/tests/render/test_overview_view.c",
        "portable/tests/render/evidence/dos_cursor_inversion_trace.py",
        "portable/render/primitives.c", "portable/render/primitives.h")
    report = {
        "schema": "portable-overview-cursor-inversion-trace-v1",
        "status": "PASS",
        "function": "f_1CE2_032B",
        "positive_control": positive,
        "negative_control": negative,
        "expected_positive_calls": expected,
        "execution_boundary": (
            "Original DOS f_1CE2_032B executes. Its g_913C pointer is redirected "
            "to f_1B4E_000C, intercepted as a four-stack-word callback recorder. "
            "No S00 driver body or VGA hardware memory is executed by this trace."),
        "source_contract": {
            "dispatch": "S00 DispatchS00 index 5 is _o00_31AD_037C, the g_913C slot; profiles 0 and 8 both select S00.",
            "raster_op": "_o00_31AD_0394 writes GC data-rotate 0x18 (XOR), set/reset 0x0f, enable-set/reset 0x0f, sequencer map mask 0x0f, and bit mask 0xff before per-byte RMW writes; inferred indexed effect is pixel XOR 0x0f.",
            "outline": "f_1CE2_032B issues four half-open strips in top, bottom, left, right order, with no corner overlap for ordinary dimensions.",
            "clipping": "The caller DrawMapCursor brackets this helper with clip_SetWin(0x0100); the portable renderer applies the caller-provided framebuffer clip."},
        "source_hashes": {path: sha256((ROOT / path).read_bytes())
                          for path in source_paths},
        "oracle_sha256": exe.load().sha256,
        "unicorn_version": behavior.uc.__version__,
    }
    out = ROOT / "portable/tests/render/evidence/dos-cursor-inversion-trace.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("DOS GRectInvOutline trace matched the four expected strips; width-zero contrast emitted none.")


if __name__ == "__main__":
    main()
