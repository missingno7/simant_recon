from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location(
    "word_spelling", ROOT / "portable/tools/word_spelling.py")
assert SPEC is not None and SPEC.loader is not None
word_spelling = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(word_spelling)


class WordSpellingTests(unittest.TestCase):
    def test_implicit_word_declarations_prototypes_and_casts(self):
        source = "unsigned f(unsigned seed) { unsigned x = (unsigned)seed; return x; }"
        converted, count = word_spelling.explicit_unsigned_word(source)
        self.assertEqual(count, 4)
        self.assertEqual(converted,
                         "uint16_t f(uint16_t seed) { uint16_t x = (uint16_t)seed; return x; }")

    def test_explicit_types_identifiers_comments_and_literals_are_preserved(self):
        source = '''unsigned char a; unsigned short b; unsigned int c; unsigned long d;
unsigned_result = 1; /* unsigned x; */ // unsigned y;
char *s = "unsigned int and unsigned"; char c = 'u';
'''
        self.assertEqual(word_spelling.explicit_unsigned_word(source), (source, 0))

    def test_comment_separated_type_is_rejected(self):
        for source in ("unsigned /* size */ int x;",
                       "unsigned /* one */ /* two */ long x;",
                       "unsigned // note\n char x;"):
            with self.subTest(source=source), self.assertRaises(ValueError):
                word_spelling.explicit_unsigned_word(source)

    def test_comment_between_type_and_identifier_is_preserved(self):
        self.assertEqual(word_spelling.explicit_unsigned_word("unsigned /* word */ x;"),
                         ("uint16_t /* word */ x;", 1))

    def test_actual_frozen_randworld_signature_and_body(self):
        import sys
        sys.path.insert(0, str(ROOT / "portable/tools"))
        import recover_source
        frozen = (ROOT / "src/S08/m35F5.c").read_text(encoding="utf-8")
        body, _, _ = recover_source.extract_named_function(frozen, "RandWorld")
        explicit, count = word_spelling.explicit_unsigned_word(body)
        self.assertEqual(count, 1)
        converted, excluded, adapted = recover_source.transform(explicit)
        self.assertIn("RandWorld(uint16_t seed", converted)
        self.assertFalse(excluded)
        self.assertFalse(adapted)
        # Aside from the one implicit-word spelling, retain every source byte.
        self.assertEqual(explicit.replace("uint16_t seed", "unsigned seed", 1), body)


if __name__ == "__main__":
    unittest.main()
