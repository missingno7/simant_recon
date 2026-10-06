"""Supported corpus proofs must reject malformed topology, not enforce observed maxima."""
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import resource_domains


def synthetic_menu(titles):
    outer_size = 4 * (titles + 2)
    text_start = outer_size + 4 * (titles + 1) + 4 * titles
    outer = [outer_size] + [outer_size + 4 * (titles + 1) + 4 * i for i in range(titles)] + [0]
    pointers = [text_start + 2 * i for i in range(titles)] + [0]
    return struct.pack("<" + "I" * len(outer), *outer) + struct.pack("<" + "I" * len(pointers), *pointers) + b"\0" * (4 * titles) + b"T\0" * titles


class ResourceDomain(unittest.TestCase):
    def test_menu_parser_does_not_clamp_to_shipped_bound(self):
        for count in (1, 5, 11, 21):
            self.assertEqual(resource_domains.menu_domain(synthetic_menu(count))["title_count"], count)

    def test_invalid_target_and_missing_sentinel(self):
        raw = synthetic_menu(5)
        with self.assertRaisesRegex(ValueError, "outside"):
            resource_domains.menu_domain(struct.pack("<I", len(raw)) + raw[4:])
        with self.assertRaises(ValueError):
            resource_domains.menu_domain(raw[:-1])
        with self.assertRaisesRegex(ValueError, "sentinel"):
            resource_domains.offset_list(struct.pack("<I", 1), 0)

    def test_alias_to_pointer_table_rejected(self):
        raw = bytearray(synthetic_menu(5))
        struct.pack_into("<I", raw, 28, 4)
        with self.assertRaisesRegex(ValueError, "overlap|gap"):
            resource_domains.menu_domain(bytes(raw))

    def test_pinned_corpus_and_reviewed_consumers(self):
        report = resource_domains.collect()
        reviewed = json.loads((ROOT / "evidence/canonical/shipped-resource-domain/facts.json").read_text())
        self.assertEqual(report["corpus"], reviewed["corpus"])
        self.assertEqual([(x["database"], x["id"], x["title_count"], x["item_counts"]) for x in report["menus"]],
                         [("SHARED", 0, 5, [8, 7, 8, 6, 6])])
        self.assertEqual(report["window_control"], reviewed["window_control"])
        self.assertEqual([(x["window"], x["index"], x["selected_color"], x["flags"]) for x in report["exceptional_palette_fields"]], [(18, 3, 63, 0xa003)])
        self.assertEqual(sum(bool(x["raw_high_bytes"]) for x in report["text_records"]), 9)
        self.assertTrue(report["highlighted_style_intervals"])
        self.assertFalse(any(x["high_bytes"] for x in report["highlighted_style_intervals"]))
        self.assertEqual(report["palette_direct_calls"], reviewed["palette_direct_calls"])
        # Source changes require review of the corresponding static proof, rather
        # than automatically retaining a domain certificate after a count writer
        # or escaped pointer is added.
        for name, digest in reviewed["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), digest, name)
        for symbol, expected in reviewed["complete_symbolic_consumer_files"].items():
            found = set()
            for path in (ROOT / "src").rglob("*"):
                if path.suffix.lower() not in (".c", ".asm"):
                    continue
                # Data-only functional providers are independently compiled and
                # shape-checked by dos/build.py; this census tracks consumers.
                if (ROOT / "src/state") in path.parents:
                    continue
                source = path.read_text()
                source = re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)
                if re.search(r"(?<!\w)_?" + re.escape(symbol) + r"(?!\w)", source):
                    found.add(path.relative_to(ROOT).as_posix())
            self.assertEqual(sorted(found), expected, symbol)

    def test_original_palette_selection_gate_negative_contrast(self):
        import importlib.util
        import types
        file = ROOT / "evidence/canonical/shipped-resource-domain/palette_probe.py"
        spec = importlib.util.spec_from_file_location("palette_probe", file)
        probe = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(probe)
        raw = next(x["payload"] for x in resource_domains.decoder().parse_records("HCEGANT")[1]
                   if (x["id"], x["kind"]) == (18, 0))
        record = resource_domains.window_domain(raw)["objects"][3]
        obj = raw[record["offset"]:record["offset"] + record["size"]]
        image = probe.exe.load()
        pair = types.SimpleNamespace(function=probe.functions.get("f_218D_000C"),
            vectors={probe.exe.MANAGER_SEG * 16 + v.offset: v for v in image.vectors},
            identity={"oracle_sha256": image.sha256})
        actual = probe.run_case(pair, obj, record["flags"])
        contrast = probe.run_case(pair, obj, record["flags"] | 0x800)
        self.assertTrue(actual["object_unchanged"])
        self.assertEqual(actual["selection_calls"], [])
        self.assertEqual(contrast["selection_calls"], [[0x1203, 1], [0x1203, 0]])

    def test_menu_owner_complete_producer_and_consumer_census(self):
        facts = json.loads((ROOT / "evidence/canonical/menu-title-owner/facts.json").read_text())
        self.assertEqual(resource_domains.menu_calls(), facts["complete_direct_calls"])
        for path, digest in facts["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), digest, path)
        found = {symbol: [] for symbol in facts["complete_symbolic_consumer_files"]}
        for path in sorted((ROOT / "src").rglob("*")):
            if path.suffix.lower() not in (".c", ".asm") or ROOT / "src/state" in path.parents:
                continue
            text = re.sub(r"/\*.*?\*/|//[^\n]*", "", path.read_text(), flags=re.S)
            if path.suffix == ".asm":
                text = re.sub(r";[^\n]*", "", text)
            for symbol in found:
                if re.search(r"(?<!\w)_?" + re.escape(symbol) + r"(?!\w)", text):
                    found[symbol].append(path.relative_to(ROOT).as_posix())
        self.assertEqual(found, facts["complete_symbolic_consumer_files"])
        # No input clamp is inferred: the complete producer table, not a
        # user-supplied command value, establishes this finite FE domain.
        source = (ROOT / "src/S19/m384C.c").read_text()
        pairs = re.findall(r"\{\s*(0x[0-9a-f]+|0)\s*,\s*(0x[0-9a-f]+|0)\s*\}",
            source[source.index("struct KeyCmd g_2CBE[]"):source.index("int g_2D3A")])
        pairs = [[int(key, 0), int(value, 0)] for key, value in pairs]
        self.assertEqual(pairs, facts["key_command_pairs"])
        self.assertEqual({value & 255 for key, value in pairs if value & 0xff00 == 0xfe00}, set(range(5)))

    def test_original_menu_geometry_and_indirect_event_route(self):
        import importlib.util
        path = ROOT / "evidence/canonical/shipped-resource-domain/menu_probe.py"
        spec = importlib.util.spec_from_file_location("menu_probe", path)
        probe = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(probe)
        report = probe.controls()
        self.assertEqual(report["actual"]["count"], [5])
        self.assertEqual(report["actual"]["x"][5], 0x7a7a)
        self.assertEqual(report["actual"]["width"][5], 0x7a7a)
        self.assertEqual(report["sixth_title_contrast"]["count"], [6])
        self.assertNotEqual(report["sixth_title_contrast"]["x"][5], 0x7a7a)
        self.assertNotEqual(report["sixth_title_contrast"]["width"][5], 0x7a7a)
        self.assertEqual([x["delivered_code"] for x in report["mouse"]], list(range(0xfe00, 0xfe05)))
        self.assertEqual(report["outside_all_titles"]["count"], 0)


if __name__ == "__main__":
    unittest.main()
