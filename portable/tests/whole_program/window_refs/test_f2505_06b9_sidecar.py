"""Focused integration check for the converted f_2505_06B9 source body.

The test recompiles the function body from the current generated root:m2505 TU
after running the production windows converter. It proves the first-object
margin and draw requests use the registered host sidecar, not the poisoned
four-byte DOS pointer-table cell. This is not a DOS differential proof.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[4]
GENERATED = ROOT / "build/workers/whole_program/generated/root_m2505.c"
WINDOW_REFS_C = ROOT / "portable/whole_program/window_refs.c"
CONVERTER = ROOT / "portable/whole_program/conversions/windows.py"


HARNESS = r'''#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "portable/whole_program/window_refs.h"

struct Pt { int16_t x, y; };
struct Rect { int16_t left, top, right, bottom; };
SimWindowRefRegistry sim_window_ref_registry;

typedef struct Call {
    char kind;
    int16_t x, y, id, mode, flag;
} Call;
static Call calls[16];
static size_t call_count;

static void record_call(Call c)
{
    if (call_count >= sizeof(calls) / sizeof(calls[0])) abort();
    calls[call_count++] = c;
}

void f_1FD2_0883(int16_t x, int16_t y, int16_t id, int16_t mode,
                 int16_t flag)
{
    record_call((Call){'D', x, y, id, mode, flag});
}

void f_208F_0419(struct Pt *size, int16_t id)
{
    record_call((Call){'M', 0, 0, id, 0, 0});
    switch (id) {
    case 0x64: size->x = 7;  size->y = 5; break;
    case 0x70: size->x = 9;  size->y = 6; break;
    case 0x66: size->x = 11; size->y = 3; break;
    case 0x67: size->x = 13; size->y = 4; break;
    case 0x69: size->x = 5;  size->y = 2; break;
    default: abort();
    }
}

void f_2505_06B9(int16_t flag, char *w);

static void put_i16(uint8_t *p, int16_t v)
{
    p[0] = (uint8_t)v;
    p[1] = (uint8_t)((uint16_t)v >> 8);
}

static int positive_case(void)
{
    uint8_t wire[0x68] = {0};
    const uint8_t poison[4] = {0xD3, 0x7A, 0xE1, 0x5C};
    char *payload = (char *)wire;
    char **handle = &payload;
    const Call expected[] = {
        {'D', 104, 54, 0x64, (int16_t)0xf083, 1},
        {'M', 0, 0, 0x64, 0, 0},
        {'M', 0, 0, 0x70, 0, 0},
        {'D', 287, 240, 0x70, (int16_t)0xf084, 1},
        {'M', 0, 0, 0x66, 0, 0},
        {'D', 285, 54, 0x66, (int16_t)0xf085, 1},
        {'D', 111, 54, 0x65, (int16_t)0xf088, 1},
        {'M', 0, 0, 0x69, 0, 0},
        {'D', 280, 54, 0x69, (int16_t)0xf082, 1},
    };
    size_t i;

    put_i16(wire + 0, 100);
    put_i16(wire + 2, 50);
    put_i16(wire + 4, 300);
    put_i16(wire + 6, 250);
    put_i16(wire + 0x0c, 1);
    put_i16(wire + 0x1c, 0x059c);
    memcpy(wire + 0x2c, poison, sizeof(poison));
    put_i16(wire + 0x30 + 0x22, 0x38);
    wire[0x30 + 0x21] = 1;
    wire[0x30 + 0x28] = 4;

    sim_window_ref_registry_init(&sim_window_ref_registry);
    if (sim_window_ref_registry_attach(&sim_window_ref_registry, 0, handle,
                                       sizeof(wire)) != SIM_WINDOW_REFS_OK)
        return 10;
    if (sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry,
                                                    payload) == NULL ||
        sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry,
                                                    payload)[0] !=
            (char *)wire + 0x30)
        return 11;

    f_2505_06B9(1, payload);
    if (call_count != sizeof(expected) / sizeof(expected[0])) return 12;
    for (i = 0; i < call_count; ++i) {
        if (calls[i].kind != expected[i].kind ||
            calls[i].x != expected[i].x || calls[i].y != expected[i].y ||
            calls[i].id != expected[i].id ||
            calls[i].mode != expected[i].mode ||
            calls[i].flag != expected[i].flag) {
            fprintf(stderr, "call %zu mismatch: got %c %d %d id=%04x mode=%04x flag=%d\n",
                    i, calls[i].kind, calls[i].x, calls[i].y,
                    (uint16_t)calls[i].id, (uint16_t)calls[i].mode,
                    calls[i].flag);
            return 13;
        }
    }
    if (memcmp(wire + 0x2c, poison, sizeof(poison)) != 0) return 14;
    sim_window_ref_registry_detach(&sim_window_ref_registry, 0);
    return 0;
}

int main(int argc, char **argv)
{
    if (argc == 2 && strcmp(argv[1], "missing") == 0) {
        char wire[0x68] = {0};
        /* Negative control: an unregistered buffer has no projected table. */
        return sim_window_ref_registry_objects_for_buffer(
                   &sim_window_ref_registry, wire) == NULL && call_count == 0
            ? 0 : 80;
    }
    return positive_case();
}
'''


def _function_body(source: str) -> str:
    match = re.search(
        r"void\s+f_2505_06B9\s*\(int16_t\s+flag,\s*char\s*\*w\)\s*\{",
        source,
    )
    if not match:
        raise AssertionError("converted function definition not found")
    start = match.start()
    brace = source.find("{", match.start())
    depth = 0
    for end in range(brace, len(source)):
        if source[end] == "{":
            depth += 1
        elif source[end] == "}":
            depth -= 1
            if depth == 0:
                return source[start : end + 1]
    raise AssertionError("unterminated converted function body")


class F2505SidecarTest(unittest.TestCase):
    def test_converted_draw_reads_registered_sidecar(self) -> None:
        gcc = shutil.which("gcc")
        if not gcc:
            self.skipTest("gcc is required for this focused C integration test")
        spec = importlib.util.spec_from_file_location("windows_converter", CONVERTER)
        if spec is None or spec.loader is None:
            self.fail("could not load windows converter")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        source = GENERATED.read_text(encoding="utf-8")
        converted = module.convert_window_source(source)
        body = _function_body(converted.text)
        self.assertIn(
            "sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry, (char *)w)[0][0x28]",
            body,
        )
        self.assertNotRegex(body, r"\(\*\s*\(\(char\s+\*\s+\*\s+\*\)")

        with tempfile.TemporaryDirectory(prefix="f2505-sidecar-") as td:
            td_path = Path(td)
            test_c = td_path / "f2505_sidecar_test.c"
            exe = td_path / "f2505_sidecar_test.exe"
            test_c.write_text(HARNESS + "\n" + body + "\n", encoding="utf-8")
            compile_result = subprocess.run(
                [gcc, "-std=c11", "-O0", "-Wall", "-Wextra", "-Werror",
                 "-I", str(ROOT), str(test_c), str(WINDOW_REFS_C), "-o", str(exe)],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(compile_result.returncode, 0,
                             compile_result.stdout + compile_result.stderr)
            positive = subprocess.run([str(exe)], text=True, capture_output=True,
                                      check=False)
            self.assertEqual(positive.returncode, 0,
                             positive.stdout + positive.stderr)

            # Negative control for the real registry: an unbound payload has
            # no host pointer table and does not reach any draw service.
            missing = subprocess.run([str(exe), "missing"], text=True,
                                     capture_output=True, check=False)
            self.assertEqual(missing.returncode, 0,
                             missing.stdout + missing.stderr)


if __name__ == "__main__":
    unittest.main()
