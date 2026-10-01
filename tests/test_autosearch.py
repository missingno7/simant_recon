"""Tests for the autosearch prototype (no compiler needed).

    python -m unittest tests.test_autosearch -v

The compile-level check is test_live.py (opt-in: AUTOSEARCH_LIVE=1), which runs the driver on
one small open function with a tiny budget.
"""
import glob
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))

import csrc as C  # noqa: E402
import srcrules as R  # noqa: E402

SAMPLE = (HERE / "autosearch_sample.c").read_text()


def moves(text, rule, fname="target"):
    return R.enumerate_moves(text, fname, [rule])


def variant(text, rule, site_prefix, fname="target"):
    ms = moves(text, rule, fname)
    for mv in [m for m in ms if m.site == site_prefix] + [m for m in ms if m.site.startswith(site_prefix)]:
        return R.apply_move(text, mv)
    raise AssertionError(f"no {rule} move at {site_prefix!r}: {[m.site for m in moves(text, rule, fname)]}")


def body(text, fname="target"):
    src = C.Source(text)
    fn = src.function(fname)
    return text[fn.body.s:fn.body.e]


class Tokenizer(unittest.TestCase):
    def test_asm_block_is_one_token(self):
        t = "void f(void)\n{\n    _asm {\n        mov ax, 1 ; it's a comment\n    }\n}\n"
        toks = [x for x in C.tokenize(t) if x.kind == "asm"]
        self.assertEqual(len(toks), 1)
        self.assertIn("it's", toks[0].text)
        fn = C.Source(t).function("f")
        self.assertIsInstance(fn.body.items[0], C.Asm)

    def test_asm_line(self):
        t = "void f(void)\n{\n    _asm mov ax,'x'\n    g();\n}\n"
        fn = C.Source(t).function("f")
        self.assertIsInstance(fn.body.items[0], C.Asm)
        self.assertIsInstance(fn.body.items[1], C.ExprStmt)

    def test_preprocessor_line_and_continuation(self):
        t = "#define X(a) \\\n    ((a) + 1)\nint f(int a)\n{\n    return X(a);\n}\n"
        pp = [x for x in C.tokenize(t) if x.kind == "pp"]
        self.assertEqual(len(pp), 1)
        self.assertIn("((a) + 1)", pp[0].text)

    def test_msc_qualifiers_in_casts_and_decls(self):
        t = ("typedef struct { int a; } S;\nint far f(S far *p)\n{\n    char far * far q;\n"
             "    q = (char far *)p;\n    return ((S far *)q)->a;\n}\n")
        fn = C.Source(t).function("f")
        self.assertIsInstance(fn.body.items[0], C.Decl)
        casts = [n for n in C.walk(fn.body) if isinstance(n, C.Cast)]
        self.assertEqual(len(casts), 2)

    def test_typedef_name_variable_not_a_cast(self):
        t = "typedef int T;\nint f(int a)\n{\n    return (a) - 1;\n}\n"
        fn = C.Source(t).function("f")
        r = fn.body.items[0].x
        self.assertIsInstance(r, C.Bin)


class ParseCanonical(unittest.TestCase):
    def test_every_canonical_function_parses(self):
        n = 0
        for f in sorted(glob.glob(str(ROOT / "src" / "*" / "*.c"))):
            t = Path(f).read_text(encoding="latin1")
            fs = C.Source(t).functions()
            for fn in fs:
                self.assertEqual(t[fn.body.s], "{")
                self.assertEqual(t[fn.body.e - 1], "}")
            n += len(fs)
        self.assertGreater(n, 1000)


class Rules(unittest.TestCase):
    def test_every_move_parses(self):
        for mv in R.enumerate_moves(SAMPLE, "target", list(R.RULES)):
            v = R.apply_move(SAMPLE, mv)
            self.assertTrue(R.valid_variant(v, "target"), f"{mv.rule} {mv.site}")
            self.assertNotEqual(v, SAMPLE, f"{mv.rule} {mv.site} is a no-op")

    def test_rel_swap(self):
        self.assertIn("if (3 > a || b == 0)", variant(SAMPLE, "REL-SWAP", "a < 3"))

    def test_rel_swap_parenthesises(self):
        t = "int target(int a, int b, int c)\n{\n    return a < b < c;\n}\n"
        v = variant(t, "REL-SWAP", "a < b < c")
        self.assertIn("c > (a < b)", v)

    def test_tern_swap_negates_relational(self):
        t = "int target(int a)\n{\n    return a < 3 ? 1 : 2;\n}\n"
        self.assertIn("a >= 3 ? 2 : 1", variant(t, "TERN-SWAP", "a < 3"))

    def test_chain_order(self):
        self.assertIn("t = u = f(a, b);", variant(SAMPLE, "CHAIN-ORDER", "u = t"))

    def test_chain_split_and_embed(self):
        v = variant(SAMPLE, "CHAIN-SPLIT", "u = t = f(a, b);")
        self.assertIn("t = f(a, b);\n    u = t;", v)
        self.assertIn("h(u = t = f(a, b));", variant(SAMPLE, "EMBED", "u = t = f(a, b); -> h(u)"))

    def test_unembed_condition(self):
        t = "int target(int a)\n{\n    int d;\n\n    if ((d = f(a)) < 0)\n        return d;\n    return 0;\n}\n"
        v = variant(t, "EMBED", "un d = f(a)")
        self.assertIn("d = f(a);\n    if (d < 0)", v)

    def test_or_dup_roundtrip(self):
        v = variant(SAMPLE, "OR-DUP", "a < 3 || b == 0")
        self.assertIn("if (a < 3)\n        return 0;\n    else if (b == 0)\n        return 0;", v)
        back = variant(v, "OR-DUP", "join a < 3")
        self.assertEqual(C.Source(back).function("target").body.items[4].c.op, "||")

    def test_or_dup_keeps_else(self):
        t = "void target(int a, int b)\n{\n    if (a || b)\n        f(1);\n    else\n        f(2);\n}\n"
        v = variant(t, "OR-DUP", "a || b")
        self.assertIn("if (a)\n        f(1);\n    else if (b)\n        f(1);\n    else\n        f(2);", v)

    def test_and_nest(self):
        t = "void target(int a, int b)\n{\n    if (a && b)\n        f(1);\n}\n"
        v = variant(t, "AND-NEST", "a && b")
        self.assertIn("if (a) {\n        if (b)\n            f(1);\n    }", v)

    def test_if_neg_braces_else_if(self):
        t = ("void target(int a, int b)\n{\n    if (a < 1)\n        f(1);\n    else if (b)\n        f(2);\n"
             "    else\n        f(3);\n}\n")
        v = variant(t, "IF-NEG", "a < 1")
        self.assertIn("if (a >= 1) {", v)
        fn = C.Source(v).function("target")
        st = fn.body.items[0]
        self.assertIsInstance(st.then, C.Block)
        self.assertIsInstance(st.then.items[0], C.If)
        self.assertIsNotNone(st.then.items[0].els)

    def test_if_neg_demorgan(self):
        v = variant(SAMPLE, "IF-NEG", "demorgan")
        self.assertIn("if (a <= 5 || b == 2)", v)

    def test_else_wrap_unwrap(self):
        t = "int target(int a)\n{\n    if (a)\n        return 1;\n    f(a);\n    return 0;\n}\n"
        v = variant(t, "ELSE-WRAP", "wrap a")
        self.assertIn("else {\n        f(a);\n        return 0;\n    }", v)
        back = variant(v, "ELSE-WRAP", "unwrap a")
        self.assertEqual(body(back).split(), body(t).split())

    def test_tern_if_roundtrip(self):
        v = variant(SAMPLE, "TERN-IF", "i = a ? 1 : 2;")
        self.assertIn("if (a)\n        i = 1;\n    else\n        i = 2;", v)
        back = variant(v, "TERN-IF", "join a")
        self.assertIn("i = a ? 1 : 2;", back)

    def test_for_while(self):
        v = variant(SAMPLE, "FOR-WHILE", "for (i = 0")
        self.assertIn("i = 0;\n    while (i < b) {\n        h(i);\n        i++;\n    }", v)

    def test_cse_inline(self):
        t = "int target(int a)\n{\n    int t;\n\n    t = a * 6;\n    f(t);\n    return t + 1;\n}\n"
        v = variant(t, "CSE-INLINE", "t = a * 6")
        self.assertNotIn("int t;", v)
        self.assertIn("f(a * 6);", v)
        self.assertIn("return a * 6 + 1;", v)

    def test_cse_inline_refuses_across_call_for_globals(self):
        t = "extern int g;\nint target(int a)\n{\n    int t;\n\n    t = g;\n    f(a);\n    return t;\n}\n"
        self.assertFalse([m for m in moves(t, "CSE-INLINE")])

    def test_local_merge_and_split(self):
        t = ("int target(int a)\n{\n    int i;\n    int j;\n\n    i = a;\n    f(i);\n    j = a + 1;\n"
             "    f(j);\n    return 0;\n}\n")
        v = variant(t, "LOCAL-MERGE", "j -> i")
        self.assertNotIn("int j;", v)
        self.assertIn("i = a + 1;\n    f(i);", v)
        s = variant(v, "LOCAL-SPLIT", "i @ i = a + 1;")
        self.assertIn("i2 = a + 1;\n    f(i2);", s)

    def test_param_copy(self):
        v = variant(SAMPLE, "PARAM-COPY", "b")
        self.assertIn("int b2;", v)
        self.assertIn("b2 = b;", v)
        self.assertIn("for (i = 0; i < b2; i++)", v)

    def test_proto_rules(self):
        self.assertIn("extern int far f(int, int);", variant(SAMPLE, "PROTO-NAMES", "f unnamed"))
        self.assertIn("extern int far f(int a, ...);", variant(SAMPLE, "PROTO-TYPE", "f variadic"))
        self.assertIn("extern int far f(unsigned int a, int b);", variant(SAMPLE, "PROTO-TYPE", "f arg0"))

    def test_decl_init(self):
        v = variant(SAMPLE, "DECL-INIT", "join t = a + b;")
        self.assertIn("int t = a + b;", v)
        back = variant(v, "DECL-INIT", "int t = a + b;")
        self.assertEqual(back.split(), SAMPLE.split())

    def test_case_swap(self):
        t = ("int target(int a)\n{\n    switch (a) {\n    case 1:\n        return 3;\n    case 2:\n"
             "        f(a);\n        break;\n    }\n    return 0;\n}\n")
        v = variant(t, "CASE-SWAP", "case 1")
        self.assertLess(v.index("case 2:"), v.index("case 1:"))

    def test_edits_overlap_refused(self):
        with self.assertRaises(ValueError):
            R.apply_edits("abcdef", [(0, 3, "x"), (2, 4, "y")])

    def test_rule_catalogue_documents_evidence(self):
        for r in R.RULES.values():
            self.assertTrue(r.evidence and r.doc)
            self.assertIn(r.category, ("code", "decl", "steer"))
        self.assertNotIn("DEAD-AUTO", R.DEFAULT_RULES)


class Driver(unittest.TestCase):
    def test_broken_base_cannot_drop_manifest_claim_or_data_from_filter(self):
        import autosearch as A
        from types import SimpleNamespace
        ev=A.Evaluator.__new__(A.Evaluator)
        ev.ctx=SimpleNamespace(key='fixture',claims=[{'name':'accepted_peer'}])
        ev.fname='target'
        base={'compile_ok':True,'claims':{'target':False,'accepted_peer':False},'data':{'CONST':False}}
        ev.set_base(base)
        self.assertEqual(set(ev.regressions(base)), {'accepted_peer','data CONST'})
        self.assertEqual(ev.regressions({'compile_ok':True,'claims':{'accepted_peer':True},'data':{'CONST':True}}), [])
        ev.one=lambda text:base
        result=A.search(ev,'source',[],1,1,1,1,log=lambda _:None)
        self.assertIn('base fails accepted ownership',result['error'])
        self.assertEqual(set(result['base_losses']), {'accepted_peer','data CONST'})

    def test_neutral_contexts_survive_until_combined_edit(self):
        import autosearch as A
        from types import SimpleNamespace
        from unittest.mock import patch
        class FakeEvaluator:
            fname='target'
            ctx=SimpleNamespace(key='fixture')
            compiles=0
            key=staticmethod(lambda text:text)
            set_base=staticmethod(lambda result:None)
            save=staticmethod(lambda:None)
            regressions=staticmethod(lambda result:[])
            def one(self,text):
                self.compiles+=1
                exact=text=='context2+edit'
                return {'compile_ok':True,'score':[0,0,0,0] if exact else [1,2,2,0],
                        'fhash':'exact' if exact else 'same bytes'}
            def many(self,texts):
                return [self.one(t) for t in texts]
        def moves(text,*args):
            if text=='base':
                return [SimpleNamespace(rule='PROTO-NAMES',site=str(i),key=str(i)) for i in range(3)]
            if text.startswith('context'):
                return [SimpleNamespace(rule='DECL-SWAP',site='combine',key='edit')]
            return []
        def apply(text,move):
            return 'context'+move.site if text=='base' else text+'+edit'
        class PeerLossEvaluator(FakeEvaluator):
            regressions=staticmethod(lambda result:['accepted_peer'] if result['score'][0]==0 else [])
        with patch.object(A.R,'enumerate_moves',side_effect=moves), \
             patch.object(A.R,'apply_move',side_effect=apply), \
             patch.object(A.R,'valid_variant',return_value=True):
            narrow=A.search(FakeEvaluator(),'base',[],1,2,20,20,log=lambda _:None,neutral_beam=1)
            wider=A.search(FakeEvaluator(),'base',[],1,2,20,20,log=lambda _:None,neutral_beam=3)
            peer_loss=A.search(PeerLossEvaluator(),'base',[],1,2,20,20,log=lambda _:None,neutral_beam=3)
        self.assertEqual(narrow['best_score'][0],1)
        self.assertEqual(wider['best_score'][0],0)
        self.assertEqual(wider['code_identities'],2)
        self.assertEqual(peer_loss['best_score'][0],1)
        self.assertEqual(peer_loss['rule_stats']['DECL-SWAP']['regress'],1)

    def test_neutral_selection_spreads_rules_and_fills_budget(self):
        import autosearch as A
        states=[A.State(str(i),[(r,str(i),str(i))],{})
                for r in ('DECL-SWAP','PROTO-NAMES','REL-SWAP') for i in range(3)]
        chosen=A.pick_neutral(states,6)
        self.assertEqual(len(chosen),6)
        self.assertEqual({s.path[-1][0] for s in chosen}, {'DECL-SWAP','PROTO-NAMES','REL-SWAP'})
        self.assertEqual(A.pick_neutral(states,0),[])

    def test_cache_invalidates_placement_extent_claim_and_evidence_changes(self):
        import autosearch as A
        import modctx
        ev = A.Evaluator.__new__(A.Evaluator)
        ev.ctx = modctx.Ctx('root:295C', 'root', 0x295C, None, 'msc600ax', ['/AL'],
                            {'CONST': {'seg': 0x55B3, 'off': 0x8A9E, 'size': 8}})
        ev.claims = [{'name': 'f', 'size': 75}]
        ev.cache_fingerprint = 'original registries'
        initial = ev.key('void f(void) {}')
        ev.ctx.placements['CONST']['off'] += 2
        self.assertNotEqual(initial, ev.key('void f(void) {}'))
        ev.ctx.placements['CONST']['off'] -= 2
        ev.ctx.extent = {'start': 0x295CA, 'end': 0x29B80}
        self.assertNotEqual(initial, ev.key('void f(void) {}'))
        ev.ctx.extent = None
        ev.claims[0]['size'] = 74
        self.assertNotEqual(initial, ev.key('void f(void) {}'))
        ev.claims[0]['size'] = 75
        ev.cache_fingerprint = 'reframed registries'
        self.assertNotEqual(initial, ev.key('void f(void) {}'))

    def test_continuation_finds_preserved_draft_and_handles_missing_file(self):
        import autosearch as A
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            saved = root / 'work/autosearch/runs/old-run/best.c'
            saved.parent.mkdir(parents=True)
            saved.write_text('void f(void) {}')
            entry = {'out': str(root / 'build/deleted/old-run'), 'base': [1, 9], 'best': [1, 3]}
            self.assertEqual(A.continuation_base(entry, root / 'work/autosearch/results.json'), saved)
            # A previous baseline can be a better whole-module draft than the canonical stub
            # even when that search did not improve it (DoAntMoveY).
            entry['best'] = entry['base']
            self.assertEqual(A.continuation_base(entry, root / 'work/autosearch/results.json'), saved)
            saved.unlink()
            self.assertIsNone(A.continuation_base(entry, root / 'work/autosearch/results.json'))

    def test_all_targets_includes_inplace_drafts_and_honors_explicit_skip(self):
        import autosearch as A
        import tempfile
        import json
        from pathlib import Path
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'layout').mkdir()
            (root / 'm.c').write_text('void claimed(void) {}\nvoid scaffold(void) {}\nvoid inplace(void) {}')
            (root / 'layout/manifest.json').write_text(json.dumps({'modules': {'root:295C': {
                'unit': 'root', 'seg': 0x295C, 'source': 'm.c', 'claims': [{'name': 'claimed'}],
                'scaffold': ['scaffold']}}}))
            rows = [{'name': n, 'off': i, 'unit': 'root', 'seg': 0x295C}
                    for i, n in enumerate(('claimed', 'scaffold', 'inplace', 'absent'))]
            lookup = {r['name']: r for r in rows}
            with patch.object(A, 'ROOT', root), patch.object(A.modctx, 'module_rows', return_value=rows), \
                 patch.object(A.modctx.fnmod, 'get', side_effect=lambda n: lookup[n]):
                self.assertEqual(A.targets([], []), [('root:295C', 'scaffold'), ('root:295C', 'inplace')])
                self.assertEqual(A.targets(['root:295C'], []), [])
                self.assertEqual(A.targets([], ['inplace']), [('root:295C', 'inplace')])

    def test_unscaffold_only_the_target_block(self):
        import autosearch as A
        t = ("int a(void)\n{\n    return 1;\n}\n/* SCAFFOLD BEGIN: note */\nint b(void)\n{\n    return 2;\n}\n"
             "/* SCAFFOLD END */\n/* SCAFFOLD BEGIN: x */\nint c(void)\n{\n    return 3;\n}\n/* SCAFFOLD END */\n")
        u = A.unscaffold(t, "b")
        self.assertNotIn("SCAFFOLD BEGIN: note", u)
        self.assertIn("SCAFFOLD BEGIN: x", u)
        self.assertIn("int b(void)", u)

    def test_unscaffold_splits_shared_block(self):
        import autosearch as A
        import modules
        t = ("/* SCAFFOLD BEGIN: note */\nint b(void)\n{\n    return 2;\n}\n\nint c(void)\n{\n    return 3;\n}\n"
             "/* SCAFFOLD END */\n")
        self.assertEqual(modules.scaffold_names(A.unscaffold(t, "b")), {"c"})
        self.assertEqual(modules.scaffold_names(A.unscaffold(t, "c")), {"b"})

    def test_insn_distance(self):
        import autosearch as A
        a = bytes.fromhex("558bec8b460650e80000")   # push bp; mov bp,sp; mov ax,[bp+6]; push ax; call
        b = bytes.fromhex("558bec8b460850e80000")
        self.assertEqual(A.insn_distance(a, a), 0)
        self.assertEqual(A.insn_distance(a, b), 1)

    def test_annotate(self):
        import autosearch as A
        t = "int x;\nint far target(int a)\n{\n    return a;\n}\n"
        v = A.annotate(t, "target", [("REL-SWAP", "a < b", "k")])
        self.assertIn("/* autosearch: exact after rules REL-SWAP */\nint far target", v)


if __name__ == "__main__":
    unittest.main()
