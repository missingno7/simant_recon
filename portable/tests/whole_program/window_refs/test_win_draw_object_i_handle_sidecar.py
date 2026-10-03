"""Exercise converted win_DrawObjectI's type-16 Handle sidecar branches.

This compiles the actual converted body extracted from the current generated
root:m21FA TU. It checks the source inline-text and mapped-Handle paths against
the real window-reference registry. It is a focused native integration test,
not a DOS behavioral-equivalence claim.
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
GENERATED = ROOT / "build/workers/whole_program/generated/root_m21FA.c"
WINDOW_REFS_C = ROOT / "portable/whole_program/window_refs.c"
CONVERTER = ROOT / "portable/whole_program/conversions/windows.py"


HARNESS = r'''#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "portable/whole_program/window_refs.h"

struct Rect { int16_t left, top, right, bottom; };
struct Pt { int16_t x, y; };
struct Sides { uint8_t left, top, right, bottom; };
struct WinObj {
    struct Rect rect;
    int16_t origin[4], ref[4], mode[4];
    char unk20, type;
    int16_t size, flags, data[3];
};
SimWindowRefRegistry sim_window_ref_registry;
int16_t g_6300 = 1;
static char colors[4] = {0, 0, 0, 0};
static char *colorEntry = colors;
void (*g_9134)(int16_t, int16_t, int16_t, int16_t, int16_t);

typedef struct Event { char kind; int16_t a, b; const char *text; } Event;
static Event events[32];
static size_t event_count;
static char **expected_native_handle;
static char *expected_native_text;

static void event(char kind, int16_t a, int16_t b, const char *text)
{
    if (event_count == sizeof(events) / sizeof(events[0])) abort();
    events[event_count++] = (Event){kind, a, b, text};
}

void win_SetColorFromObj(char *obj)
{ (void)obj; event('C', 0, 0, NULL); }
void clip_Push(void) { abort(); }
void clip_SubInclude(char *obj) { (void)obj; abort(); }
void clip_Pop(void) { abort(); }
void win_RectFillOutline(int16_t width, struct Rect *rect)
{ (void)width; (void)rect; abort(); }
void win_RectFill(struct Rect *rect) { (void)rect; abort(); }
void f_23E6_0392(char *obj) { (void)obj; abort(); }
void f_23E6_066C(char *obj) { (void)obj; abort(); }
void f_1CE2_046D(struct Rect *rect, int16_t color)
{ (void)rect; (void)color; abort(); }
void win_DrawButtonBorder(char *obj) { (void)obj; abort(); }
void win_DrawBitMapAtObj(int16_t id, struct Rect *rect)
{ (void)id; (void)rect; abort(); }
void f_1CE2_0430(struct Rect *rect) { (void)rect; abort(); }
void win_RectOutline(struct Rect *rect, int16_t width)
{ (void)rect; (void)width; abort(); }
void win_RectHOutline(struct Rect *rect, int16_t width)
{ (void)rect; (void)width; abort(); }
void win_RectVOutline(struct Rect *rect, int16_t width)
{ (void)rect; (void)width; abort(); }
void f_24AB_02AD(int16_t font) { event('F', font, 0, NULL); }
char *_fstrchr(char *s, int c) { return strchr(s, c); }
void gr_JustifyStrInRect(int16_t mode, struct Rect *rect, char *text)
{
    event('J', mode, rect->left, text);
}
char *f_171C_1B84(char **handle)
{
    if (handle != expected_native_handle) abort();
    event('L', 0, 0, NULL);
    return expected_native_text;
}
void f_171C_1BBA(char **handle)
{
    if (handle != expected_native_handle) abort();
    event('U', 0, 0, NULL);
}

void win_DrawObjectI(struct WinObj *obj);

static void put_i16(uint8_t *p, int16_t value)
{
    p[0] = (uint8_t)value;
    p[1] = (uint8_t)((uint16_t)value >> 8);
}

static int expect_event(size_t i, char kind, int16_t a, int16_t b,
                        const char *text)
{
    return i < event_count && events[i].kind == kind && events[i].a == a &&
           events[i].b == b && events[i].text == text;
}

static int run_case(int with_handle)
{
    uint8_t wire[0x70] = {0};
    uint8_t initial_wire[sizeof(wire)];
    const uint8_t expected_wire_handle[4] = {0, 0, 0, 0};
    const uint8_t poisoned_object_table[4] = {0xD3, 0x7A, 0xE1, 0x5C};
    char *payload = (char *)wire;
    char **handle_cell = &payload;
    char *object = payload + 0x30;
    char native_payload[] = "native payload from mapped Handle";
    char *native_handle_payload = native_payload;
    char **native_handle = &native_handle_payload;
    char *inline_text = object + 0x2e;
    char *chosen_text = with_handle ? native_payload : inline_text;
    char **objects;
    char ***sidecar_slot;
    memset(wire, 0xA7, sizeof(wire));
    put_i16(wire + 0x0c, 1);
    memcpy(wire + 0x2c, poisoned_object_table,
           sizeof(poisoned_object_table));
    /* The serialized DOS pointer is null; bytes after it are inline text and
       poison for any accidental native-width load from +0x2a. */
    memset(object + 0x2a, 0, 4);
    memcpy(inline_text, "INLINE TEXT: pretend pointer", 28);
    inline_text[28] = '\0';
    put_i16((uint8_t *)object + 0x22, 0x40);
    object[0x21] = 16;
    put_i16((uint8_t *)object + 0x24, 0x100); /* centered alignment */
    put_i16((uint8_t *)object + 0x26 + 2, 5); /* selected font */
    put_i16((uint8_t *)object + 0, 10);
    put_i16((uint8_t *)object + 2, 20);
    put_i16((uint8_t *)object + 4, 100);
    put_i16((uint8_t *)object + 6, 40);
    sim_window_ref_registry_init(&sim_window_ref_registry);
    if (sim_window_ref_registry_attach(&sim_window_ref_registry, 0, handle_cell,
                                       sizeof(wire)) != SIM_WINDOW_REFS_OK)
        return 10;
    objects = sim_window_ref_registry_objects_for_buffer(&sim_window_ref_registry,
                                                           payload);
    if (objects == NULL || objects[0] != (char *)wire + 0x30) return 11;
    sidecar_slot = sim_window_ref_registry_handle_slot_for_object(
        &sim_window_ref_registry, objects[0], 0x2a);
    if (sidecar_slot == NULL) return 12;
    if (with_handle) *sidecar_slot = native_handle;
    expected_native_handle = native_handle;
    expected_native_text = native_payload;
    event_count = 0;
    memcpy(initial_wire, wire, sizeof(wire));

    win_DrawObjectI((struct WinObj *)objects[0]);

    /* Both cases select the source font, justify the source rectangle in mode
       two, then reset the font. Only the native Handle branch locks/unlocks. */
    if (with_handle) {
        if (event_count != 6 || !expect_event(0, 'C', 0, 0, NULL) ||
            !expect_event(1, 'F', 5, 0, NULL) ||
            !expect_event(2, 'L', 0, 0, NULL) ||
            !expect_event(3, 'J', 2, 10, chosen_text) ||
            !expect_event(4, 'U', 0, 0, NULL) ||
            !expect_event(5, 'F', 0, 0, NULL)) return 13;
    } else {
        if (event_count != 5 || !expect_event(0, 'C', 0, 0, NULL) ||
            !expect_event(1, 'F', 5, 0, NULL) ||
            !expect_event(2, 'F', 5, 0, NULL) ||
            !expect_event(3, 'J', 2, 10, chosen_text) ||
            !expect_event(4, 'F', 0, 0, NULL)) return 14;
    }
    if (memcmp(object + 0x2a, expected_wire_handle, 4) != 0 ||
        memcmp(wire + 0x2c, poisoned_object_table,
               sizeof(poisoned_object_table)) != 0 ||
        memcmp(wire, initial_wire, sizeof(wire)) != 0) return 15;
    /* The callback must see the source inline text or the real mapped record. */
    if (events[3].text != chosen_text) return 16;
    sim_window_ref_registry_detach(&sim_window_ref_registry, 0);
    return 0;
}

int main(void)
{
    int status = run_case(0);
    if (status != 0) return status;
    return run_case(1);
}
'''


def extract_definition(source: str) -> str:
    match = re.search(
        r"void\s+win_DrawObjectI\s*\(struct\s+WinObj\s*\*\s*obj\)\s*\{",
        source,
    )
    if not match:
        raise AssertionError("converted win_DrawObjectI definition not found")
    open_brace = source.find("{", match.start())
    depth = 0
    for end in range(open_brace, len(source)):
        if source[end] == "{":
            depth += 1
        elif source[end] == "}":
            depth -= 1
            if depth == 0:
                return source[match.start() : end + 1]
    raise AssertionError("unterminated win_DrawObjectI")


class DrawObjectHandleSidecarTest(unittest.TestCase):
    def test_inline_null_and_mapped_native_handle(self) -> None:
        gcc = shutil.which("gcc")
        if gcc is None:
            self.skipTest("gcc is required for this focused C integration test")
        spec = importlib.util.spec_from_file_location("windows_converter", CONVERTER)
        if spec is None or spec.loader is None:
            self.fail("could not load window converter")
        converter = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = converter
        spec.loader.exec_module(converter)
        source = GENERATED.read_text(encoding="utf-8")
        converted = converter.convert_window_source(source)
        body = extract_definition(converted.text)
        handle_lookup = (
            "sim_window_ref_registry_handle_slot_for_object(&sim_window_ref_registry, "
            "(char *)obj, 0x2a)"
        )
        self.assertEqual(body.count(handle_lookup), 2,
                         "both source Handle accesses must use the registry sidecar")
        self.assertNotRegex(body, r"\*\s*\(char\s*\*\s*\*\s*\*\s*\)\s*\(&?obj->data")

        with tempfile.TemporaryDirectory(prefix="win-draw-object-sidecar-") as td:
            td_path = Path(td)
            test_c = td_path / "win_draw_object_test.c"
            exe = td_path / "win_draw_object_test.exe"
            test_c.write_text(HARNESS + "\n" + body + "\n", encoding="utf-8")
            compile_result = subprocess.run(
                [gcc, "-std=c11", "-O0", "-Wall", "-Wextra", "-Werror",
                 "-Wno-implicit-fallthrough",
                 "-I", str(ROOT), str(test_c), str(WINDOW_REFS_C), "-o", str(exe)],
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(compile_result.returncode, 0,
                             compile_result.stdout + compile_result.stderr)
            result = subprocess.run([str(exe)], text=True, capture_output=True,
                                   check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
