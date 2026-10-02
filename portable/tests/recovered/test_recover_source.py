from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location(
    "recover_source", ROOT / "portable/tools/recover_source.py")
assert SPEC and SPEC.loader
recover_source = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(recover_source)


class RecoveredSourceTests(unittest.TestCase):
    def test_width_translation_preserves_literals_and_source_function_body(self) -> None:
        original = 'int f(unsigned char x) { long n = 2L; return x + n; }\n/* int long far */\nchar *s = "int far long";\n'
        generated, _, _ = recover_source.transform(original)
        self.assertIn("int16_t f(uint8_t x)", generated)
        self.assertIn("int32_t n = 2L", generated)
        self.assertIn('"int far long"', generated)
        self.assertIn("/* int long far */", generated)
        self.assertIn("return x + n;", generated)

    def test_scaffolds_are_declarations_and_ax_tail_is_explicit_return(self) -> None:
        source = '''/* SCAFFOLD BEGIN: fn draft */
int far fn(int x) { return x + 1; }
/* SCAFFOLD END */
int far ret(void) { call(); }
'''
        transformed, excluded, _ = recover_source.transform(source)
        self.assertEqual(excluded, ["fn"])
        self.assertIn("int16_t  fn(int16_t x);", transformed)
        self.assertNotIn("return x + 1", transformed)
        self.assertNotIn("SCAFFOLD BEGIN", transformed)
        dos_tail = '''int far o25_3BA4_19AD(int *rot) {
    side_effect();
    o25_3BA4_1686(rot);
}'''
        adapted, changed = recover_source.adapt_ax_tail_return(dos_tail)
        self.assertTrue(changed)
        self.assertIn("return o25_3BA4_1686(rot);", adapted)

    def test_keyboard_bda_rewrite_is_narrow_and_fails_closed(self) -> None:
        source = "if (*(unsigned char far *)0x417L & 8) x++;"
        rewritten, rows = recover_source.adapt_keyboard_bda("fixture", source)
        self.assertIn("recovered_keyboard_modifiers() & 8", rewritten)
        self.assertEqual(rows[0]["count"], 1)
        with self.assertRaisesRegex(ValueError, "unsupported absolute pointer access"):
            recover_source.adapt_keyboard_bda("negative", "x = *(unsigned char far *)0x418L;")

    def test_generated_translation_units_pin_exact_inputs(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "build/workers") as tmp:
            out = Path(tmp)
            # Exercise generation without compiling; all paths derive from repository sources.
            import subprocess
            subprocess.run(["python", str(ROOT / "portable/tools/recover_source.py"),
                            "--out", str(out)], cwd=ROOT, check=True,
                            capture_output=True, text=True)
            report = json.loads((out / "provenance.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "DIAGNOSTIC_ONLY_NOT_PRODUCTION")
            self.assertEqual(len(report["modules"]), 23)
            map_to_yard = next(x for x in report["modules"] if x["name"] == "root_m00F8_MapToYard")
            self.assertTrue(map_to_yard["excluded_unrelated_module_bodies"])
            self.assertEqual(map_to_yard["explicit_host_edges"],
                             ["win_IsWinOpen", "SetMapPlane", "win_Swap", "win_Open"])
            selected = (out / Path(map_to_yard["generated"]).name).read_text(encoding="utf-8")
            self.assertIn("MapToYard(void)", selected)
            self.assertIn("MapToYard", selected)
            self.assertNotIn("win_YardClosed", selected)
            self.assertEqual(report["recovered_state"]["binding_status"], "COMPLETE")
            self.assertTrue({"fd_50F6_0472", "fd_50F6_0214"}.issubset(
                {x["symbol"] for x in report["recovered_state"]["same_width_signedness_views"]}))
            alias_rows = report["recovered_state"]["alias_declaration_audit"]
            byte_view = next(row for row in alias_rows if row["alias"] == "fd_50F6_0F08")
            self.assertEqual(byte_view["address"], "50F6:0F08")
            self.assertEqual(byte_view["view_bytes"], 1)
            self.assertEqual(report["excluded_modules"][0]["name"], "root_m0093")
            self.assertTrue(report["excluded_modules"][0]["source_sha256"])
            self.assertTrue(report["recovered_state"]["source_defined_initializers"])
            mismatch_names = {x["symbol"] for x in report["recovered_state"]["source_data_initializer_mismatches"]}
            self.assertNotIn("fd_3D57_02BC", mismatch_names)
            state_rows = {x["name"]: x for x in report["recovered_state"]["fields"]}
            self.assertEqual(state_rows["fd_3D57_02BC"]["dims"], ["2"])
            self.assertEqual(state_rows["fd_3D57_07A8"]["dims"], ["7"])
            adjacent = report["recovered_state"]["adjacent_source_data_views"][0]
            self.assertEqual(adjacent["bytes"], 14)
            self.assertEqual(adjacent["members"]["fd_3D57_07B2"], 10)
            self.assertEqual(len(adjacent["initializers"]), 5)
            delay_field = state_rows["fd_3D57_07CC"]
            self.assertEqual(delay_field["dims"], ["7"])
            delay_view = next(x for x in report["recovered_state"]["adjacent_source_data_views"]
                              if x["base"] == "fd_3D57_07CC")
            self.assertEqual(delay_view["bytes"], 14)
            self.assertEqual(delay_view["members"]["fd_3D57_07CE"], 2)
            self.assertEqual(delay_view["initializers"][0]["source_bytes"], 14)
            self.assertEqual(report["recovered_state"]["derived_source_pointer_tables"][0]["name"], "fd_3D57_082A")
            header = (out / "recovered_state.h").read_text(encoding="utf-8")
            self.assertIn("uint8_t HoleMapB[64]", header)
            self.assertIn("int8_t Dx8[8]", header)
            self.assertIn("#define fd_3D57_07B2 (fd_3D57_07A8[5])", header)
            self.assertIn("#define fd_3D57_07CE (fd_3D57_07CC + 1)", header)
            exp_module = next(x for x in report["modules"] if x["name"] == "S22_m3BBD")
            self.assertTrue(exp_module["source_type_view_adaptations"])
            self.assertIn("recovered_keyboard_set_modifiers", header)
            self.assertEqual(sum(row["count"] for module in report["modules"]
                                 for row in module["platform_boundary_adaptations"]), 22)
            for item in report["modules"]:
                source = (ROOT / item["source"]).read_bytes()
                generated = (out / Path(item["generated"]).name).read_bytes()
                self.assertEqual(hashlib.sha256(source).hexdigest(), item["source_sha256"])
                self.assertEqual(hashlib.sha256(generated).hexdigest(), item["generated_sha256"])
                self.assertIn("UNREVIEWED_HOST_PROMOTIONS", item["integer_promotion_status"])
                self.assertIn("external_objects", item)

    def test_adjacent_data_initializers_share_array_and_named_word_view(self) -> None:
        import subprocess
        with tempfile.TemporaryDirectory(dir=ROOT / "build/workers") as tmp:
            base = Path(tmp)
            out = base / "generated"
            subprocess.run(["python", str(ROOT / "portable/tools/recover_source.py"),
                            "--out", str(out)], cwd=ROOT, check=True,
                           capture_output=True, text=True)
            source = base / "data_view_test.c"
            source.write_text(r'''#include "recovered_state.h"
#include <assert.h>
int main(void) {
    RecoveredState s = {0};
    RecoveredBindingFrame frame;
    recovered_state_init(&s);
    assert(s.fd_3D57_02BC[0] == 0 && s.fd_3D57_02BC[1] == 0);
    assert(s.fd_3D57_07A8[0] == 0);
    assert(s.fd_3D57_07A8[1] == 1);
    assert(s.fd_3D57_07A8[2] == 1);
    assert(s.fd_3D57_07A8[3] == 1);
    assert(s.fd_3D57_07A8[4] == 1);
    assert(s.fd_3D57_07A8[5] == 0);
    assert(s.fd_3D57_07A8[6] == 0);
    recovered_bind_begin(&frame, &s);
    assert(fd_3D57_07B2 == fd_3D57_07A8[5]);
    assert(fd_3D57_082A[0] == fd_50F6_0516);
    assert(fd_3D57_082A[1] == fd_50F6_0626);
    fd_3D57_082A[0][3] = 19;
    assert(fd_50F6_0516[3] == 19);
    fd_3D57_07A8[5] = 0x1234;
    assert(fd_3D57_07B2 == 0x1234);
    recovered_bind_end(&frame, &s);
    assert(s.fd_3D57_07A8[5] == 0x1234);
    { int flags[] = {0, 3, 8, 11}; unsigned i;
      for (i = 0; i < 4; ++i) {
          recovered_keyboard_set_modifiers((uint8_t)flags[i]);
          assert(recovered_keyboard_modifiers() == (uint8_t)flags[i]);
      }
    }
    return 0;
}
''', encoding="utf-8")
            exe = base / "data_view_test.exe"
            proc = subprocess.run(["gcc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                                  "-I", str(out), str(source),
                                  str(out / "recovered_state.c"), "-o", str(exe)],
                                 cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            subprocess.run([str(exe)], check=True, capture_output=True, text=True)

    def test_context_bindings_preserve_typed_aliases_and_nested_restore(self) -> None:
        import subprocess
        with tempfile.TemporaryDirectory(dir=ROOT / "build/workers") as tmp:
            base = Path(tmp)
            out = base / "generated"
            subprocess.run(["python", str(ROOT / "portable/tools/recover_source.py"),
                            "--out", str(out)], cwd=ROOT, check=True,
                            capture_output=True, text=True)
            source = base / "binding_test.c"
            source.write_text(r'''#include "recovered_state.h"
#include <assert.h>
int main(void) {
    RecoveredState a = {0}, b = {0};
    RecoveredBindingFrame outer, inner;
    recovered_state_init(&a);
    assert((uint8_t)a.Dx8[5] == 0xff);
    assert(a.CasteModeTabB[0] == 8);
    assert(a.HoleMapB[63] == 0);
    a.Cycle = 0x1234; a.Dx8[0] = -1; a.HoleMapB[63] = 7;
    recovered_bind_begin(&outer, &a);
    assert(fd_50F6_0F08 == 0x34);
    assert(fd_3D57_0000[0] == -1);
    assert(fd_3D57_0224[63] == 7);
    b.Cycle = 0xABCD; b.Dx8[0] = 2;
    recovered_bind_begin(&inner, &b);
    fd_50F6_0F08 = 0x55;
    fd_3D57_0000[0] = 3;
    recovered_bind_end(&inner, &b);
    assert((uint16_t)b.Cycle == 0xAB55 && b.Dx8[0] == 3);
    assert(Cycle == 0x1234 && Dx8[0] == -1);
    recovered_bind_end(&outer, &a);
    assert(a.Cycle == 0x1234 && a.Dx8[0] == -1);
    return 0;
}
''', encoding="utf-8")
            exe = base / "binding_test.exe"
            proc = subprocess.run(["gcc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                            "-I", str(out), str(source), str(out / "recovered_state.c"),
                            "-o", str(exe)], cwd=ROOT, check=True,
                           capture_output=True, text=True)
            subprocess.run([str(exe)], cwd=ROOT, check=True,
                           capture_output=True, text=True)

    def test_host_integer_promotion_probe_is_a_negative_control(self) -> None:
        import subprocess
        with tempfile.TemporaryDirectory(dir=ROOT / "build/workers") as tmp:
            base = Path(tmp)
            source = base / "promotion_probe.c"
            source.write_text(r'''#include <assert.h>
#include <stdint.h>
int main(void) {
    int16_t s = -1;
    uint16_t u = 0x8000;
    int16_t x = 30000, y = 2;
    assert(s < u);                 /* host int32_t promotion: true */
    assert((int16_t)(x * y) / 100 == -55); /* explicit MSC 16-bit step */
    assert(x * y / 100 == 600);    /* uncast host expression differs */
    return 0;
}
''', encoding="utf-8")
            exe = base / "promotion_probe.exe"
            proc = subprocess.run(["gcc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                            str(source), "-o", str(exe)], check=True,
                           capture_output=True, text=True)
            subprocess.run([str(exe)], check=True, capture_output=True, text=True)

    def test_get_rand_dirs_scaffold_adapter_maps_shared_source_state(self) -> None:
        import subprocess
        with tempfile.TemporaryDirectory(dir=ROOT / "build/workers") as tmp:
            base = Path(tmp)
            out = base / "generated"
            subprocess.run(["python", str(ROOT / "portable/tools/recover_source.py"),
                            "--out", str(out)], cwd=ROOT, check=True,
                           capture_output=True, text=True)
            source = base / "adapter_test.c"
            source.write_text(r'''#include "recovered_state.h"
#include "portable/game/simulation/movement.h"
#include "portable/game/simulation/rng.h"
#include <assert.h>
#include <string.h>
void recovered_rng_bind(SimRng *rng);
int16_t SRand1(uint16_t range);
int16_t o25_3BA4_1686(int16_t *, int16_t *, int16_t, int16_t, int16_t,
                     int16_t, int16_t);
int main(void) {
    RecoveredState s = {0};
    RecoveredBindingFrame frame;
    SimRng rng_a = {0}, rng_b = {0};
    SimWorldTiles tiles = {0};
    SimMoveContext context;
    SimRandDirBias expected, actual;
    int plane, mode, x, y, rot, dir;
    recovered_state_init(&s);
    sim_rng_set_s_seed(&rng_a, 0x6a31);
    sim_rng_set_s_seed(&rng_b, 0x6a31);
    recovered_rng_bind(&rng_a);
    for (x = 1; x <= 257; x += 17) {
        uint16_t expected_value;
        assert(sim_rng_s1(&rng_b, (uint16_t)x, &expected_value) == 1);
        assert(SRand1((uint16_t)x) == (int16_t)expected_value);
    }
    assert(sim_rng_get_s_seed(&rng_a) == sim_rng_get_s_seed(&rng_b));
    recovered_rng_bind(0);
    memset(s.MapA, 0, sizeof(s.MapA));
    memset(s.MapB, 0, sizeof(s.MapB));
    memset(s.MapR, 0, sizeof(s.MapR));
    s.TERRAINset = 0;
    s.fd_50F6_0A8E = 0;
    s.fd_50F6_0AF8 = 2;
    s.fd_50F6_0AD6 = 10; s.fd_50F6_0AE8 = 10;
    s.fd_50F6_0AB6 = 8; s.fd_50F6_0AC6 = 8;
    recovered_bind_begin(&frame, &s);
    for (plane = 1; plane <= 3; ++plane) {
        for (mode = 0; mode <= 1; ++mode) {
            fd_50F6_0A8E = mode ? 2 : 0;
            context.mode = mode ? 2 : 0;
            context.from_plane = fd_50F6_0AF8;
            context.from.x = fd_50F6_0AD6; context.from.y = fd_50F6_0AE8;
            context.previous.x = fd_50F6_0AB6; context.previous.y = fd_50F6_0AC6;
            for (x = 0; x < 64; x += 7) {
                y = (x * 3) & 63;
                expected.rot = actual.rot = 0;
                expected.direction = actual.direction = 5;
                tiles.terrain_set = 0;
                memcpy(tiles.surface, MapA, sizeof(tiles.surface));
                memcpy(tiles.nest_b, MapB, sizeof(tiles.nest_b));
                memcpy(tiles.nest_r, MapR, sizeof(tiles.nest_r));
                {
                    int16_t want = sim_get_my_rand_dirs(&tiles, &context, plane,
                        (SimGridPos){(int16_t)x, (int16_t)y},
                        (SimGridPos){(int16_t)((x + 11) & 63), (int16_t)((y + 9) & 63)},
                        &expected, 0);
                    int16_t got = o25_3BA4_1686(&actual.rot, &actual.direction,
                        (int16_t)plane, (int16_t)x, (int16_t)y,
                        (int16_t)((x + 11) & 63), (int16_t)((y + 9) & 63));
                    assert(got == want);
                    assert(actual.rot == expected.rot);
                    assert(actual.direction == expected.direction);
                }
            }
        }
    }
    recovered_bind_end(&frame, &s);
    return 0;
}
''', encoding="utf-8")
            exe = base / "adapter_test.exe"
            proc = subprocess.run(["gcc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                            "-Wno-unused-parameter", "-Wno-unused-variable",
                            "-Wno-unused-but-set-variable", "-Wno-unused-but-set-parameter",
                            "-Wno-parentheses", "-Wno-type-limits", "-Wno-implicit-fallthrough",
                            "-ffunction-sections", "-fdata-sections", "-I", str(out), "-I", str(ROOT),
                            str(source), str(out / "recovered_native_adapters.c"),
                            str(out / "recovered_state.c"),
                            str(ROOT / "portable/game/simulation/movement.c"),
                            str(ROOT / "portable/game/simulation/rng.c"),
                            "-Wl,--gc-sections", "-o", str(exe)], cwd=ROOT,
                           capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            subprocess.run([str(exe)], check=True, capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
