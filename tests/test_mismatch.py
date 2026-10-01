"""Synthetic byte localization and strict comparison behavior."""
import copy
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from mismatch import compare_streams,compact,format_summary

PREFIX='558bec83ec10'
SUFFIX='8b46020346048946065b5dc3'


def compare(a,b,**kwargs):return compare_streams(bytes.fromhex(a),bytes.fromhex(b),**kwargs)
def classes(r):return {c['class'] for i in r['islands'] for c in i['classifications']}


class AlignmentTests(unittest.TestCase):
    def test_identical_and_deterministic(self):
        r=compare(PREFIX+SUFFIX,PREFIX+SUFFIX)
        self.assertEqual(r,compare(PREFIX+SUFFIX,PREFIX+SUFFIX))
        self.assertEqual(r['counts']['mismatch_islands'],0)
        self.assertEqual(r['counts']['exact_instructions'],r['counts']['target_instructions'])

    def test_register_substitution(self):
        r=compare(PREFIX+'8bd8'+SUFFIX,PREFIX+'8bf0'+SUFFIX)
        self.assertIn('REGISTER_ALLOCATION',classes(r))
        self.assertTrue(r['islands'][0]['resumes_exact'])

    def test_stack_slots(self):
        r=compare(PREFIX+'8946f48956f6'+SUFFIX,PREFIX+'8946f88956fa'+SUFFIX)
        self.assertEqual(r['islands'][0]['classifications'][0]['class'],'STACK_SLOT_ALLOCATION')
        self.assertEqual(r['islands'][0]['classifications'][0]['confidence'],'high')

    def test_insert_then_realign(self):
        r=compare(PREFIX+SUFFIX,PREFIX+'40'+SUFFIX)
        self.assertIn('EXTRA_INSTRUCTIONS',classes(r))
        self.assertTrue(r['islands'][0]['resumes_exact'])
        self.assertNotEqual(r['exact_suffix']['target']['bytes'],r['exact_suffix']['candidate']['bytes'])

    def test_delete_then_realign(self):
        r=compare(PREFIX+'40'+SUFFIX,PREFIX+SUFFIX)
        self.assertIn('MISSING_INSTRUCTIONS',classes(r))
        self.assertTrue(r['islands'][0]['resumes_exact'])

    def test_branch_encoding_and_position_independent_decode(self):
        r=compare(PREFIX+'eb00'+SUFFIX,PREFIX+'e90000'+SUFFIX)
        self.assertIn('BRANCH_ENCODING',classes(r))
        self.assertEqual(r['counts']['decoded_exact_pairs'],1)
        self.assertTrue(r['islands'][0]['resumes_exact'])

    def test_branch_layout(self):
        r=compare(PREFIX+'7400'+SUFFIX,PREFIX+'740140'+SUFFIX)
        self.assertIn('BRANCH_TARGET_OR_LAYOUT',classes(r))
        self.assertTrue(r['exact_suffix'])

    def test_repeated_epilogue_is_not_anchor(self):
        r=compare('b801005dc3b802005dc3','b803005dc3')
        self.assertIsNone(r['exact_suffix'])
        self.assertEqual(r['counts']['anchors'],0)
        self.assertTrue(any('Repeated terminal' in n for n in r['notes']))

    def test_unbound_fixups_refused_and_undecoded_tail_retained(self):
        for kwargs in ({'bound':False},{'fixups':[{'offset':1,'width':4}]}):
            with self.assertRaises(ValueError):
                compare('9a00000000c3','9a00000000c3',**kwargs)
        r=compare('550f','550f')
        self.assertFalse(r['decode_complete'])
        self.assertEqual(r['islands'][-1]['target']['bytes'],[1,2])

    def test_immediate_width_control_and_unclassified(self):
        self.assertIn('IMMEDIATE_VALUE',classes(compare(PREFIX+'b80100'+SUFFIX,PREFIX+'b80200'+SUFFIX)))
        self.assertIn('WIDTH_OR_EXTENSION',classes(compare(PREFIX+'b001'+SUFFIX,PREFIX+'b80100'+SUFFIX)))
        self.assertIn('CONTROL_FLOW_SHAPE',classes(compare('74005dc3','75005dc3')))
        self.assertIn('LOCAL_CODEGEN_UNCLASSIFIED',classes(compare('01d8','29d8')))

    def test_compact_bounded_and_formatter(self):
        r=compare(PREFIX+'40'+SUFFIX,PREFIX+SUFFIX)
        r['islands']=r['islands']*100;r['anchors']=r['anchors']*100
        summary=compact(r)
        self.assertEqual(len(summary['islands']),12)
        self.assertGreater(summary['omitted_islands'],0)
        self.assertNotIn('target_instructions',summary)
        self.assertNotIn('alignment',summary)
        self.assertIn('Exact stream resumes',format_summary(summary))
