"""Supported-domain viewport closure: facts replay and rejection mutations."""
from pathlib import Path
import json
import re
import subprocess
import sys
import unittest

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src/program.json").is_file())
PACKAGE = ROOT / "evidence/canonical/viewport-layout"
sys.path.insert(0, str(PACKAGE))
import domain_probe

ROOT = domain_probe.ROOT


def test_facts_replay():
    result = subprocess.run(
        [sys.executable, str(PACKAGE / "domain_probe.py"), "--check"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert '"rows": 29' in result.stdout
    assert '"columns": 36' in result.stdout
    assert '"mickey_negative_rows": 2046' in result.stdout
    facts = json.loads((PACKAGE / "domain-facts.json").read_text(encoding="utf-8"))
    resize = facts["resize_loop"]
    assert resize["sample_invariant"] == {
        "x": "sampleX in {startX} union [0,639]",
        "y": "sampleY in {startY} union [0,479]",
        "proof_shape": "raw start warp seeds the exceptional axis; updates replace an axis with an in-screen value or replay the prior value",
    }
    assert resize["moved_root_horizontal_control"]["start"] == [408, 817]
    assert resize["moved_root_horizontal_control"]["horizontal_edge_sample"] == [6, 817]
    assert resize["moved_root_horizontal_control"]["delta_y"] == 0
    assert resize["timer_replacement_control"]["one_up_repeat_after_clamp"] == [408, 479]
    assert resize["mouse_replacement_control"]["absolute_callback"] == [636, 476]


def test_removing_keyboard_y_clamp_fails():
    rel = "src/root/m1B73.asm"
    source = (ROOT / rel).read_text(encoding="latin1")
    mutated, count = re.subn(
        r"(add ax, word ptr _g_9124\r?\n)\s*cmp ax, 0\r?\n\s*jge L062A\r?\n\s*xor ax, ax\r?\nL062A:",
        r"\1L062A:", source, count=1, flags=re.I,
    )
    assert count == 1
    try:
        domain_probe.collect({rel: mutated}, run_negative=False)
    except AssertionError:
        return
    raise AssertionError("probe accepted a missing keyboard lower clamp")


def test_removing_timer_x_upper_clamp_fails():
    rel = "src/root/m1B73.asm"
    source = (ROOT / rel).read_text(encoding="latin1")
    mutated, count = re.subn(
        r"(mov cx, word ptr _g_3DB2\r?\n)\s*cmp ax, cx\r?\n\s*jl L0619\r?\n\s*mov ax, cx\r?\n\s*dec ax\r?\nL0619:",
        r"\1L0619:", source, count=1, flags=re.I,
    )
    assert count == 1
    try:
        domain_probe.collect({rel: mutated}, run_negative=False)
    except AssertionError:
        return
    raise AssertionError("probe accepted a missing timer X upper clamp")


def test_removing_timer_y_upper_clamp_fails():
    rel = "src/root/m1B73.asm"
    source = (ROOT / rel).read_text(encoding="latin1")
    mutated, count = re.subn(
        r"(mov cx, word ptr _g_3DB4\r?\n)\s*cmp ax, cx\r?\n\s*jl L0635\r?\n\s*mov ax, cx\r?\n\s*dec ax\r?\nL0635:",
        r"\1L0635:", source, count=1, flags=re.I,
    )
    assert count == 1
    try:
        domain_probe.collect({rel: mutated}, run_negative=False)
    except AssertionError:
        return
    raise AssertionError("probe accepted a missing timer Y upper clamp")


def test_adding_g9124_writer_fails():
    rel = "src/root/m00F8.c"
    source = (ROOT / rel).read_text(encoding="latin1")
    mutated = source + "\nvoid viewport_domain_mutation(void) { g_9124 = -1; }\n"
    try:
        domain_probe.collect({rel: mutated}, run_negative=False)
    except AssertionError:
        return
    raise AssertionError("probe accepted an additional g_9124 writer")


def test_adding_g9122_writer_fails():
    rel = "src/root/m00F8.c"
    source = (ROOT / rel).read_text(encoding="latin1")
    mutated = source + "\nvoid viewport_domain_mutation_x(void) { g_9122 = -1; }\n"
    try:
        domain_probe.collect({rel: mutated}, run_negative=False)
    except AssertionError:
        return
    raise AssertionError("probe accepted an additional g_9122 writer")


def test_cursor_callback_to_raw_warp_fails():
    rel = "src/root/m1FD2.c"
    source = (ROOT / rel).read_text(encoding="latin1")
    old = "f_1FD2_032F(f_1CE2_000C(), f_1B73_0D4B, 100);"
    new = "f_1FD2_032F(f_1CE2_000C(), f_1B73_09FF, 100);"
    assert source.count(old) == 1
    mutated = source.replace(old, new)
    try:
        domain_probe.collect({rel: mutated}, run_negative=False)
    except AssertionError:
        return
    raise AssertionError("probe accepted a generic cursor callback rebound to the raw warp")


def test_stale_resize_control_without_rebuild_fails():
    rel = "src/S26/m39C7.c"
    source = (ROOT / rel).read_text(encoding="latin1")
    resize = domain_probe.c_function(source, "o26_39C7_0671")
    old = "f_2505_0831(win);"
    assert resize.count(old) == 1
    mutated_resize = resize.replace(old, "/* omitted active-control rebuild */", 1)
    mutated = source.replace(resize, mutated_resize, 1)
    try:
        domain_probe.collect({rel: mutated}, run_negative=False)
    except AssertionError:
        return
    raise AssertionError("probe accepted a resize path that leaves a stale F084")


def test_negative_menu_bottom_fails():
    rel = "src/root/m1FD2.c"
    source = (ROOT / rel).read_text(encoding="latin1")
    old = "fd_50F6_393C.bottom = g_3DDC + fd_50F6_393C.top + 3;"
    new = "fd_50F6_393C.bottom = fd_50F6_393C.top - 1;"
    assert source.count(old) == 1
    mutated = source.replace(old, new)
    try:
        domain_probe.collect({rel: mutated}, run_negative=False)
    except AssertionError:
        return
    raise AssertionError("probe accepted a negative menu-bottom derivation")


class ViewportDomainTests(unittest.TestCase):
    def test_facts_replay(self):
        test_facts_replay()

    def test_removing_keyboard_y_clamp_fails(self):
        test_removing_keyboard_y_clamp_fails()

    def test_removing_timer_x_upper_clamp_fails(self):
        test_removing_timer_x_upper_clamp_fails()

    def test_removing_timer_y_upper_clamp_fails(self):
        test_removing_timer_y_upper_clamp_fails()

    def test_adding_g9124_writer_fails(self):
        test_adding_g9124_writer_fails()

    def test_adding_g9122_writer_fails(self):
        test_adding_g9122_writer_fails()

    def test_cursor_callback_to_raw_warp_fails(self):
        test_cursor_callback_to_raw_warp_fails()

    def test_stale_resize_control_without_rebuild_fails(self):
        test_stale_resize_control_without_rebuild_fails()

    def test_negative_menu_bottom_fails(self):
        test_negative_menu_bottom_fails()


if __name__ == "__main__":
    unittest.main()
