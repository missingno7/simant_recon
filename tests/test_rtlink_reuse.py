"""A successful old trial must not certify objects from another accepted state."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import rtlink
import link


class TrialReuse(unittest.TestCase):
    def test_previous_state_and_wrong_object_are_rejected(self):
        module = {"source_sha256": "accepted", "flags": ["/AL", "/Os"]}
        source = b"void f(void) {}\n"
        digest = rtlink.object_input_hash(module, source, b"gate object identity")
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "cache.dat"
            path.write_bytes(b"cached object identity")
            record = {"input_hash": digest, "object_sha": link.sha(path.read_bytes())}
            self.assertTrue(rtlink.reusable_object(path, record, digest))
            for m, s, g in [
                (module, b"void f(void) { return; }\n", b"gate object identity"),
                ({**module, "flags": ["/AL", "/Os", "/Zi"]}, source, b"gate object identity"),
                (module, source, b"another gate object identity"),
            ]:
                changed = rtlink.object_input_hash(m, s, g)
                self.assertFalse(rtlink.reusable_object(path, record, changed))
            self.assertFalse(rtlink.reusable_object(path, {**record, "object_sha": "wrong"}, digest))
            self.assertFalse(rtlink.reusable_object(path, {}, digest))
            self.assertFalse(rtlink.reusable_object(path.with_name("absent.dat"), record, digest))


if __name__ == "__main__":
    unittest.main()
