import tempfile
import unittest
from pathlib import Path

from portable.tools.whole_program_call_arity_audit import (
    ROOT, arguments, audit, call_mask, parameter_shape,
)


class DirectArityAuditTests(unittest.TestCase):
    def test_nested_and_literal_arguments(self):
        code = call_mask('foo("text", nested(1,2), (int[]){3,4})')
        args, end = arguments(code, code.index('('))
        self.assertEqual(len(args), 3)
        self.assertEqual(end, len(code))

    def test_parameter_shapes(self):
        self.assertEqual(parameter_shape('void f(void)', 'f'), (0, False))
        self.assertEqual(parameter_shape('void f(int x, ...)', 'f'), (1, True))
        self.assertIsNone(parameter_shape('void f()', 'f'))

    def test_calls_not_prototypes_or_member_callbacks(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'build/workers') as directory:
            path = Path(directory) / 'input.c'
            path.write_text('''void leaf(int x) { (void)x; }
void text(const char *s) { (void)s; }
void caller(void) {
    struct Hooks *hooks;
    hooks->leaf();
    text("one argument");
    leaf(7);
    leaf();
}
''')
            result = audit([path])
            self.assertTrue(result['inputs_stable'])
            self.assertEqual(result['checked_calls'], 3)
            self.assertEqual(len(result['findings']), 1)
            self.assertEqual(result['findings'][0]['callee'], 'leaf')
            self.assertEqual(result['findings'][0]['difference'], 'MISSING_ARGUMENT')


if __name__ == '__main__':
    unittest.main()
