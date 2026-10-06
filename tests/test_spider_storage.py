import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class SpiderStorageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            "spider_storage_probe", ROOT / "evidence/canonical/spider-storage/probe.py")
        cls.probe = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.probe)

    def test_startup_zero_width_vga_leaf_reads_no_image_bytes(self):
        rows = self.probe.startup_raw_controls()
        self.assertTrue(rows[0]["completed"])
        self.assertEqual(rows[0]["reads"]["unique_bytes"], 0)
        self.assertFalse(rows[1]["completed"])
        self.assertGreaterEqual(rows[1]["reads"]["maximum"], 4)

    def test_supported_hcegant_resources_fit_natural_image(self):
        rows = self.probe.resource_controls()
        self.assertEqual(len(rows), 12)
        self.assertLessEqual(max(row["writes"]["maximum"] for row in rows), 6275)


if __name__ == "__main__":
    unittest.main()
