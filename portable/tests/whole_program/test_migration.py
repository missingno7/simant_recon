"""Regression controls for whole-source membership and lexical conversion.

Includes the real failure shape where a scaffold comment contains the function
signature. A textual signature regex can silently delete its comment terminator.
"""
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "portable/tools"))
import whole_program as migration
from portable.whole_program.conversions import startup
from portable.whole_program.conversions import history


class MigrationControls(unittest.TestCase):
    def test_scaffold_signature_is_not_code(self):
        source = """/* SCAFFOLD BEGIN: f(int x) { this is a comment } */
int far f(int x) { if (x) { return 3; } return 4; }
/* SCAFFOLD END */
char *literal = "int g(void) { }";
int g(void) { return 1; }
"""
        rows = migration.function_heads(source)
        self.assertEqual([row["name"] for row in rows], ["f", "g"])
        self.assertTrue(source[rows[0]["start"]:rows[0]["end"]].startswith("int far f"))
        self.assertEqual(source[rows[1]["start"]:rows[1]["end"]], "int g(void) { return 1; }")

    def test_preprocessor_braces_and_initializer_are_not_functions(self):
        source = """#define FN(name) int name(void) { \\
return 1; }
struct S { int a; } table[] = { { 1 }, { 2 } };
int f(void) { return table[0].a; }
"""
        self.assertEqual([row["name"] for row in migration.function_heads(source)], ["f"])

    def test_literals_comments_and_widths(self):
        source = 'unsigned n; unsigned long x; signed char c; char *s="unsigned far int"; /* int far */'
        translated, _ = migration.convert_words(source)
        self.assertEqual(translated,
            'uint16_t n; uint32_t x; int8_t c; char *s="unsigned far int"; /* int far */')

    def test_aliases_preserve_noncode_and_call_order(self):
        source = 'int far f(void) { old(); second(); return 0; } /* old */ char *s="old";'
        result, _ = migration.convert_words(source, {"old": "real"})
        self.assertIn('real(); second();', result)
        self.assertIn('/* old */ char *s="old";', result)

    def test_io_namespace_and_only_declarations_removed(self):
        source = '''typedef struct _iobuf FILE;
extern int far read(int fd, char far *buf, unsigned n);
extern FILE far * far fopen(char far *path, char far *mode);
int f(void) { extern int far close(int fd); return close(read(3, "read", 2)); }
'''
        translated, _ = migration.convert_words(source)
        translated, removed = migration.centralize_io(translated)
        self.assertEqual(removed, 3)  # local extern is not a whole source line
        self.assertIn('return dos_close(dos_read(3, "read", 2));', translated)
        self.assertNotIn('_iobuf', translated)

    def test_real_io_calls_retain_argument_order(self):
        source = (ROOT / 'src/root/m1A28.c').read_text()
        converted, _ = migration.convert_words(source)
        converted, _ = migration.centralize_io(converted)
        self.assertEqual([r['name'] for r in migration.function_heads(source)],
                         [r['name'] for r in migration.function_heads(converted)])
        self.assertNotRegex(converted, r'extern[^;]*\bdos_read\s*\(')
        self.assertIn('dos_read(', converted)

    def test_real_frozen_multiline_scaffold(self):
        source = (ROOT / "src/root/m1C62.c").read_text()
        rows = [r for r in migration.function_heads(source) if r["name"] == "f_1C62_0415"]
        self.assertEqual(len(rows), 1)
        self.assertTrue(source[rows[0]["start"]:rows[0]["end"]].startswith("int far f_1C62_0415"))

    def test_real_knr_parameters_are_part_of_function(self):
        source = (ROOT / "src/root/m10F7.c").read_text()
        rows = [r for r in migration.function_heads(source) if r["name"] == "IsThisEgg"]
        self.assertEqual(len(rows), 1)
        self.assertIn("unsigned char value;", source[rows[0]["start"]:rows[0]["end"]])

    def test_startup_boundary_retains_full_module_and_drive_loop(self):
        source = (ROOT / "src/S15/m384C.c").read_text()
        converted, ledger = startup.adapt(source)
        self.assertEqual([r["name"] for r in migration.function_heads(source)],
                         [r["name"] for r in migration.function_heads(converted)])
        self.assertIn("for (drive = 0; drive < 12; drive++)", converted)
        self.assertIn("drive | 0x80", converted)
        self.assertNotIn("_asm", migration.masked(converted))
        self.assertTrue(ledger["leaf_status"].startswith("UNPROVIDED"))
        with self.assertRaises(ValueError):
            startup.adapt(source.replace("int 13h", "int 21h", 1))

    def test_history_lowering_requires_immediate_sentinel(self):
        source = (ROOT / 'src/S24/m39C7.c').read_text()
        converted, ledger = history.adapt(source)
        self.assertIn('(3 - i) * 2', converted)
        self.assertIn('shownGraphs[3] = (int)0x8000;', converted)
        self.assertEqual([r['name'] for r in migration.function_heads(source)],
                         [r['name'] for r in migration.function_heads(converted)])
        self.assertIn('Next10', ledger['claim'])
        with self.assertRaises(ValueError):
            history.adapt(source.replace('shownGraphs[3] = (int)0x8000;', 'shownGraphs[2] = 0;'))


if __name__ == "__main__":
    unittest.main()
