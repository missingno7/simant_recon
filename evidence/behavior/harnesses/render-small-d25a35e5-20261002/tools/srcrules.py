"""srcrules.py - catalogue of semantically equivalent C rewrites, each named after its evidence.

Every rule enumerates *moves* for one function of a module source: a move is a list of text
edits (char spans of the whole file) plus a stable site key.  Rules never touch other
functions' bodies; file-level rules (prototypes, extern order) edit top-level declarations
that the target function references, and the whole-module check of the driver catches any
effect on other claims.

Categories:
  code    equivalent C that can change code generation (register/slot choice, block layout,
          operand order, CSE) -- promotable as ordinary hand-written C;
  decl    declaration order / identifier count / prototype spelling (natural forms of the
          symbol-table effects, SYM-1, PROTO-1/2) -- promotable, reported with
          --layout-inferred when nothing else changed;
  steer   constructs with no plausible original purpose (dummy autos, identifier padding):
          analysis only, never promoted automatically.

Evidence references (docs/codegen-rules.md, evidence/codegen/*.json) are given per rule.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import csrc as C  # noqa: E402

REL_FLIP = {"<": ">", ">": "<", "<=": ">=", ">=": "<=", "==": "==", "!=": "!="}
REL_NEG = {"<": ">=", ">=": "<", ">": "<=", "<=": ">", "==": "!=", "!=": "=="}
COMMUTATIVE = {"+", "*", "&", "|", "^"}
COMPOUNDABLE = {"+", "-", "*", "/", "%", "&", "|", "^", "<<", ">>"}


@dataclass
class Move:
    rule: str
    site: str                      # short human-readable site description
    edits: list                    # [(s, e, text)] on the whole file
    key: str = ""                  # rule + normalised site text (stable across other edits)

    def __post_init__(self):
        if not self.key:
            self.key = self.rule + "|" + re.sub(r"\s+", " ", self.site)[:120]


@dataclass
class Rule:
    id: str
    evidence: str
    category: str
    doc: str
    fn: object = None


RULES: dict[str, Rule] = {}


def rule(id_, evidence, category, doc):
    def deco(f):
        RULES[id_] = Rule(id_, evidence, category, doc, f)
        return f
    return deco


def apply_edits(text: str, edits) -> str:
    """Apply non-overlapping edits (s, e, new) to text."""
    es = sorted(edits, key=lambda x: (x[0], x[1]))
    for a, b in zip(es, es[1:]):
        if b[0] < a[1]:
            raise ValueError("overlapping edits")
    for s, e, new in reversed(es):
        text = text[:s] + new + text[e:]
    return text


# ------------------------------------------------------------------ context


class Ctx:
    """Parsed view of one function in a file."""

    def __init__(self, text: str, fname: str):
        self.text = text
        self.src = C.Source(text)
        self.fn = self.src.function(fname)
        self.parent = {}
        for n, p in C.walk_parents(self.fn.body):
            self.parent[id(n)] = p
        self.nodes = list(C.walk(self.fn.body))
        self.locals = {}           # name -> (Decl, Declarator)
        for n in self.nodes:
            if isinstance(n, C.Decl) and n.storage not in ("extern", "typedef"):
                for d in n.decls:
                    if d.name and not d.is_func:
                        self.locals.setdefault(d.name, (n, d))
        self.params = [p for _, p in self.fn.params if p]
        self.has_goto = any(isinstance(n, (C.Label,)) or (isinstance(n, C.Jump) and n.kind == "goto")
                            for n in self.nodes)
        self.has_asm = any(isinstance(n, C.Asm) for n in self.nodes)
        self.addr_taken = C.address_taken(self.fn.body)

    def T(self, n) -> str:
        return self.text[n.s:n.e]

    def par(self, n):
        return self.parent.get(id(n))

    def wrap(self, n, minprec: int) -> str:
        t = self.T(n)
        return t if C.prec_of(n) >= minprec else f"({t})"

    def slot_prec(self, n) -> int:
        """Minimum precedence an expression needs in the slot where n sits."""
        p = self.par(n)
        if isinstance(p, C.Decl):
            return C.P_ASSIGN
        if p is None or isinstance(p, C.Stmt):
            return C.P_COMMA
        if isinstance(p, C.Paren):
            return C.P_COMMA
        if isinstance(p, C.Bin):
            return C.PREC[p.op] if n is p.l else C.PREC[p.op] + 1
        if isinstance(p, C.Assign):
            return C.P_UNARY if n is p.l else C.P_ASSIGN
        if isinstance(p, C.Cond):
            if n is p.c:
                return 4
            return C.P_COMMA if n is p.a else C.P_COND
        if isinstance(p, (C.Unary, C.Cast)):
            return C.P_UNARY
        if isinstance(p, (C.Post, C.Member)):
            return C.P_POSTFIX
        if isinstance(p, C.Call):
            return C.P_POSTFIX if n is p.f else C.P_ASSIGN
        if isinstance(p, C.Index):
            return C.P_POSTFIX if n is p.a else C.P_COMMA
        if isinstance(p, C.Comma):
            return C.P_ASSIGN
        if isinstance(p, C.Decl):
            return C.P_ASSIGN
        return C.P_COMMA

    def replace_expr(self, n, new: str, new_prec: int):
        if new_prec < self.slot_prec(n):
            new = f"({new})"
        return (n.s, n.e, new)

    def indent(self, pos: int) -> str:
        return C.line_indent(self.text, pos)

    def lists(self):
        """(Block, index, stmt) for every statement that sits directly in a block."""
        for b in C.stmt_lists(self.fn.body):
            for i, st in enumerate(b.items):
                yield b, i, st

    def neg(self, c) -> tuple[str, int]:
        """Text and precedence of the logical negation of condition c."""
        c0 = C.strip_paren(c)
        if isinstance(c0, C.Bin) and c0.op in REL_NEG:
            return f"{self.wrap(c0.l, C.PREC[c0.op])} {REL_NEG[c0.op]} {self.wrap(c0.r, C.PREC[c0.op] + 1)}", C.PREC[c0.op]
        if isinstance(c0, C.Unary) and c0.op == "!":
            return self.T(c0.x), C.prec_of(c0.x)
        return f"!{self.wrap(c, C.P_UNARY)}", C.P_UNARY

    def neg_dm(self, c) -> tuple[str, int] | None:
        """De Morgan negation of an && / || condition (None if c is neither)."""
        c0 = C.strip_paren(c)
        if isinstance(c0, C.Bin) and c0.op in ("&&", "||"):
            op = "||" if c0.op == "&&" else "&&"
            p = C.PREC[op]
            parts = []
            for side, need in ((c0.l, p), (c0.r, p + 1)):
                t, tp = self.neg_dm(side) or self.neg(side)
                parts.append(t if tp >= need else f"({t})")
            return f"{parts[0]} {op} {parts[1]}", p
        return None

    def cond_rparen(self, st) -> int:
        """End offset of the ')' closing an if/while condition."""
        j = self.text.index(")", st.c.e)
        return j + 1

    def line_span(self, st) -> tuple[int, int]:
        """Span of statement st extended to whole lines when it is alone on its line(s)."""
        b = self.text.rfind("\n", 0, st.s) + 1
        e = self.text.find("\n", st.e)
        e = len(self.text) if e < 0 else e
        if self.text[b:st.s].strip() == "" and self.text[st.e:e].strip() == "":
            return b, e + 1
        return st.s, st.e

    def local_type(self, name: str) -> str | None:
        if name in self.locals:
            d, _ = self.locals[name]
            return self.text[d.spec_s:d.spec_e]
        return None


def reindent(text: str, delta: int) -> str:
    """Shift every line after the first by delta spaces (negative: remove up to -delta)."""
    lines = text.split("\n")
    out = [lines[0]]
    for ln in lines[1:]:
        if delta >= 0:
            out.append((" " * delta + ln) if ln.strip() else ln)
        else:
            k = 0
            while k < -delta and k < len(ln) and ln[k] == " ":
                k += 1
            out.append(ln[k:])
    return "\n".join(out)


def pure(x) -> bool:
    return x is not None and not C.has_side_effects(x)


def norm(s: str) -> str:
    return re.sub(r"\s+", "", s)


def occurrences(node, name):
    return [n for n in C.walk(node) if isinstance(n, C.Id) and n.name == name]


def body_items_text(cx: Ctx, st, ind: str) -> str:
    """Statements of st (a Block's items, or st itself) as lines at indentation ind."""
    if isinstance(st, C.Block):
        if not st.items:
            return ""
        first = st.items[0]
        old = cx.indent(first.s)
        seg = cx.text[first.s:st.items[-1].e]
        return ind + reindent(seg, len(ind) - len(old))
    old = cx.indent(st.s)
    return ind + reindent(cx.T(st), len(ind) - len(old)) if old != ind else ind + cx.T(st)


def as_block_body(cx: Ctx, st, ind: str) -> str:
    """Text for st as the sub-statement of a statement whose line has indentation ind: a block
    follows on the same line, anything else on the next line at ind + 4.  The statement's own
    first-line indentation is the reference for reindenting its continuation lines."""
    old = stmt_indent(cx, st)
    if isinstance(st, C.Block):
        return " " + reindent(cx.T(st), len(ind) - len(old))
    return "\n" + ind + "    " + reindent(cx.T(st), len(ind) + 4 - len(old))


def stmt_indent(cx: Ctx, st) -> str:
    """Indentation that st's continuation lines are relative to: its line's indentation if st
    starts its line, else (a block after 'if (..) {' or 'else') that of the owning line."""
    return cx.indent(st.s)


def sub_end(st, ind: str) -> str:
    """Separator after a sub-statement before 'else': ' ' after a block, newline + ind otherwise."""
    return " " if isinstance(st, C.Block) else "\n" + ind


# ------------------------------------------------------------------ expression rules


@rule("REL-SWAP", "TERN-1 (relational operand order decides arm order); commutative/relational operand order "
      "observations", "code", "a < b -> b > a, a == b -> b == a")
def r_rel_swap(cx: Ctx):
    for n in cx.nodes:
        if isinstance(n, C.Bin) and n.op in REL_FLIP:
            p = C.PREC[n.op]
            new = f"{cx.wrap(n.r, p)} {REL_FLIP[n.op]} {cx.wrap(n.l, p + 1)}"
            yield Move("REL-SWAP", cx.T(n), [(n.s, n.e, new)])


@rule("COMM-SWAP", "commutative operand order observation (symbol-table state), SYM-1", "code",
      "a + b -> b + a for + * & | ^")
def r_comm_swap(cx: Ctx):
    for n in cx.nodes:
        if isinstance(n, C.Bin) and n.op in COMMUTATIVE:
            if isinstance(n.l, C.Num) and isinstance(n.r, C.Num):
                continue
            if n.op in ("*", "&") and isinstance(cx.par(n), C.Unary):
                pass
            p = C.PREC[n.op]
            new = f"{cx.wrap(n.r, p)} {n.op} {cx.wrap(n.l, p + 1)}"
            yield Move("COMM-SWAP", cx.T(n), [(n.s, n.e, new)])


@rule("TERN-SWAP", "TERN-1", "code", "c ? a : b -> !c ? b : a (relational conditions negated)")
def r_tern_swap(cx: Ctx):
    for n in cx.nodes:
        if isinstance(n, C.Cond):
            nc, _ = cx.neg(n.c)
            if C.prec_of(C.strip_paren(n.c)) < 4:
                nc = f"!({cx.T(n.c)})"
            new = f"{nc} ? {cx.T(n.b)} : {cx.wrap(n.a, C.P_COND)}"
            yield Move("TERN-SWAP", cx.T(n), [(n.s, n.e, new)])


@rule("NOT-CMP", "materialised boolean observation (if ((a==K) == 0))", "code",
      "!x <-> x == 0; x != 0 <-> x in conditions")
def r_not_cmp(cx: Ctx):
    for n in cx.nodes:
        if isinstance(n, C.Unary) and n.op == "!":
            yield Move("NOT-CMP", cx.T(n), [cx.replace_expr(n, f"{cx.wrap(n.x, 10)} == 0", 9)])
        elif isinstance(n, C.Bin) and n.op in ("==", "!=") and isinstance(n.r, C.Num) and n.r.value == 0:
            if n.op == "==":
                yield Move("NOT-CMP", cx.T(n), [cx.replace_expr(n, f"!{cx.wrap(n.l, C.P_UNARY)}", C.P_UNARY)])
            elif is_cond_context(cx, n):
                yield Move("NOT-CMP", cx.T(n), [cx.replace_expr(n, cx.T(n.l), C.prec_of(n.l))])
    for st in cx.nodes:
        c = getattr(st, "c", None)
        if isinstance(st, (C.If, C.While, C.DoWhile, C.For)) and c is not None:
            c0 = C.strip_paren(c)
            if not (isinstance(c0, C.Bin) and c0.op in REL_FLIP or isinstance(c0, C.Unary) and c0.op == "!"
                    or isinstance(c0, C.Bin) and c0.op in ("&&", "||")):
                yield Move("NOT-CMP", "cond " + cx.T(c), [(c.s, c.e, f"{cx.wrap(c, 10)} != 0")])


def is_cond_context(cx: Ctx, n) -> bool:
    p = cx.par(n)
    while isinstance(p, C.Paren):
        n, p = p, cx.par(p)
    if isinstance(p, (C.If, C.While, C.DoWhile)) and n is p.c:
        return True
    if isinstance(p, C.For) and n is p.c:
        return True
    if isinstance(p, C.Bin) and p.op in ("&&", "||"):
        return True
    if isinstance(p, C.Cond) and n is p.c:
        return True
    return False


@rule("CONST-U", "unsigned vs int constants (PROTO-1/2: constant type decides register reuse)", "code",
      "integer literal K -> Ku")
def r_const_u(cx: Ctx):
    for n in cx.nodes:
        if isinstance(n, C.Num) and not n.text.startswith("'") and re.fullmatch(r"(0[xX][0-9A-Fa-f]+|\d+)[lL]?", n.text):
            p = cx.par(n)
            if isinstance(p, C.Case):
                continue
            ctx_txt = cx.T(p) if isinstance(p, C.Expr) else n.text
            yield Move("CONST-U", f"{n.text} in {ctx_txt}", [(n.e, n.e, "u")])


@rule("COMPOUND", "statement-form observations (x = x op y vs x op= y, x++ vs x += 1)", "code",
      "x = x op y <-> x op= y; x += 1 <-> x++ <-> ++x (statements)")
def r_compound(cx: Ctx):
    for n in cx.nodes:
        if isinstance(n, C.Assign):
            if n.op == "=" and isinstance(n.r, C.Bin) and n.r.op in COMPOUNDABLE and pure(n.l) \
                    and norm(cx.T(n.r.l)) == norm(cx.T(n.l)):
                yield Move("COMPOUND", cx.T(n), [(n.s, n.e, f"{cx.T(n.l)} {n.r.op}= {cx.T(n.r.r)}")])
            elif n.op != "=" and n.op[:-1] in COMPOUNDABLE and pure(n.l):
                op = n.op[:-1]
                new = f"{cx.T(n.l)} = {cx.wrap(n.l, C.PREC[op])} {op} {cx.wrap(n.r, C.PREC[op] + 1)}"
                yield Move("COMPOUND", cx.T(n), [cx.replace_expr(n, new, C.P_ASSIGN)])
                if n.op in ("+=", "-=") and isinstance(n.r, C.Num) and n.r.value == 1 and \
                        isinstance(cx.par(n), (C.ExprStmt, C.For)):
                    yield Move("COMPOUND", cx.T(n) + " ++", [(n.s, n.e, f"{cx.T(n.l)}{n.op[0] * 2}")])
        elif isinstance(n, (C.Post, C.Unary)) and n.op in ("++", "--") and isinstance(cx.par(n), (C.ExprStmt, C.For)):
            other = f"{n.op}{cx.T(n.x)}" if isinstance(n, C.Post) else f"{cx.T(n.x)}{n.op}"
            yield Move("COMPOUND", cx.T(n), [(n.s, n.e, other)])
            yield Move("COMPOUND", cx.T(n) + " +=", [(n.s, n.e, f"{cx.T(n.x)} {n.op[0]}= 1")])


# ------------------------------------------------------------------ assignment rules


@rule("CHAIN-ORDER", "chained-assignment order (218D:0656), DEAD-2 (rightmost stored first)", "code",
      "a = b = E -> b = a = E")
def r_chain_order(cx: Ctx):
    for n in cx.nodes:
        if isinstance(n, C.Assign) and n.op == "=" and isinstance(n.r, C.Assign) and n.r.op == "=":
            a, b, e = n.l, n.r.l, n.r.r
            if not (pure(a) and pure(b)):
                continue
            ta, tb = type_of(cx, a), type_of(cx, b)
            if ta and tb and norm(ta) != norm(tb):
                continue
            yield Move("CHAIN-ORDER", cx.T(n), [(n.s, n.e, f"{cx.T(b)} = {cx.T(a)} = {cx.T(e)}")])


def type_of(cx: Ctx, x) -> str | None:
    x = C.strip_paren(x)
    if isinstance(x, C.Id):
        t = cx.local_type(x.name)
        if t is None:
            for pt, pn in cx.fn.params:
                if pn == x.name:
                    return pt
        return t
    return None


@rule("CHAIN-SPLIT", "chained-assignment order; DEAD-2", "code",
      "a = b = E; <-> b = E; a = b;")
def r_chain_split(cx: Ctx):
    for blk, i, st in cx.lists():
        if isinstance(st, C.ExprStmt) and isinstance(st.x, C.Assign) and st.x.op == "=" \
                and isinstance(st.x.r, C.Assign) and st.x.r.op == "=":
            a, b, e = st.x.l, st.x.r.l, st.x.r.r
            if pure(a) and pure(b):
                ind = cx.indent(st.s)
                new = f"{cx.T(b)} = {cx.T(e)};\n{ind}{cx.T(a)} = {cx.T(b)};"
                yield Move("CHAIN-SPLIT", cx.T(st), [(st.s, st.e, new)])
        # join: b = E; a = b;
        if i + 1 < len(blk.items):
            nx = blk.items[i + 1]
            if (isinstance(st, C.ExprStmt) and isinstance(st.x, C.Assign) and st.x.op == "="
                    and isinstance(nx, C.ExprStmt) and isinstance(nx.x, C.Assign) and nx.x.op == "="
                    and isinstance(C.strip_paren(st.x.l), C.Id) and isinstance(C.strip_paren(nx.x.r), C.Id)
                    and C.strip_paren(nx.x.r).name == C.strip_paren(st.x.l).name and pure(nx.x.l)
                    and not isinstance(st.x.r, C.Assign)):
                a = nx.x.l
                if norm(cx.T(a)) in [norm(v) for v in (cx.T(st.x.l),)]:
                    continue
                if any(isinstance(z, C.Id) and z.name in C.idents(a) for z in C.walk(st.x.r)):
                    continue
                ta, tb = type_of(cx, a), type_of(cx, st.x.l)
                if ta and tb and norm(ta) != norm(tb):
                    continue
                s, _ = cx.line_span(st)
                new = f"{cx.T(a)} = {cx.T(st.x.l)} = {cx.T(st.x.r)};"
                yield Move("CHAIN-SPLIT", cx.T(st) + " " + cx.T(nx), [(st.s, nx.e, new)])


def conditional_position(cx: Ctx, n, root) -> bool:
    """True if evaluating root does not always evaluate n first-class (n under the right operand of
    && / ||, or an arm of ?:)."""
    child = n
    p = cx.par(n)
    while p is not None and child is not root:
        if isinstance(p, C.Bin) and p.op in ("&&", "||") and child is p.r:
            return True
        if isinstance(p, C.Cond) and child is not p.c:
            return True
        if isinstance(p, C.Stmt):
            break
        child, p = p, cx.par(p)
    return False


def stmt_expr_roots(st):
    """Expressions evaluated unconditionally first when statement st runs."""
    if isinstance(st, C.ExprStmt):
        return [st.x]
    if isinstance(st, (C.If, C.While, C.Switch)):
        return [st.c]
    if isinstance(st, C.Return) and st.x is not None:
        return [st.x]
    if isinstance(st, C.For) and st.init is not None:
        return [st.init]
    return []


@rule("EMBED", "embedded assignments in arguments/conditions (ExitHole, DoSow, AddAntLion, GetNestDir; "
      "resI if ((d = f()) < 0))", "code", "v = E; S(v) <-> S(v = E)")
def r_embed(cx: Ctx):
    for blk, i, st in cx.lists():
        # embed: v = E; followed by a statement that reads v once, unconditionally
        if i + 1 < len(blk.items) and isinstance(st, C.ExprStmt) and isinstance(st.x, C.Assign) \
                and st.x.op == "=" and isinstance(C.strip_paren(st.x.l), C.Id):
            v = C.strip_paren(st.x.l).name
            nx = blk.items[i + 1]
            roots = stmt_expr_roots(nx)
            if roots and not isinstance(nx, C.Label):
                root = roots[0]
                occ = occurrences(nx, v)
                occ_root = occurrences(root, v)
                if len(occ_root) == 1 and not conditional_position(cx, occ_root[0], root):
                    o = occ_root[0]
                    p = cx.par(o)
                    if not (isinstance(p, C.Assign) and o is p.l) and not (isinstance(p, (C.Post, C.Unary)) and p.op in ("++", "--", "&")):
                        rest_se = any(C.has_side_effects(k) for k in root.children()) if o is not root else False
                        if not (C.has_side_effects(st.x.r) and rest_se) and len(occ) >= 1:
                            new = f"{v} = {cx.T(st.x.r)}"
                            e1 = cx.replace_expr(o, new, C.P_ASSIGN)
                            s0, e0 = cx.line_span(st)
                            yield Move("EMBED", cx.T(st) + " -> " + cx.T(root), [(s0, e0, ""), e1])
        # unembed: an assignment inside a statement's first-evaluated expression
        for root in stmt_expr_roots(st):
            if isinstance(st, C.ExprStmt) and isinstance(root, C.Assign):
                cands = [n for n in C.walk(root.r) if isinstance(n, C.Assign)]
            else:
                cands = [n for n in C.walk(root) if isinstance(n, C.Assign)]
            for a in cands:
                if a.op != "=" or not isinstance(C.strip_paren(a.l), C.Id) or conditional_position(cx, a, root):
                    continue
                if isinstance(st, C.For):
                    continue
                v = C.strip_paren(a.l).name
                ind = cx.indent(st.s)
                p = cx.par(a)
                repl = (p.s, p.e, v) if isinstance(p, C.Paren) and cx.par(p) is not None and not isinstance(cx.par(p), C.Stmt) else (a.s, a.e, v)
                if isinstance(st, C.Label):
                    continue
                yield Move("EMBED", "un " + cx.T(a), [(st.s, st.s, f"{cx.T(a)};\n{ind}"), repl])


# ------------------------------------------------------------------ control-flow rules


@rule("OR-DUP", "REG-3 (duplicated else-if tails count as references), || vs if/else-if", "code",
      "if (a || b) S <-> if (a) S else if (b) S")
def r_or_dup(cx: Ctx):
    for n in cx.nodes:
        if not isinstance(n, C.If):
            continue
        c = C.strip_paren(n.c)
        if isinstance(c, C.Bin) and c.op == "||":
            if any(isinstance(z, (C.Label, C.Case)) for z in C.walk(n.then)):
                continue
            ind = cx.indent(n.s)
            th = as_block_body(cx, n.then, ind)
            new = f"if ({cx.T(c.l)}){th}{sub_end(n.then, ind)}else if ({cx.T(c.r)}){th}"
            if n.els is not None:
                new += sub_end(n.then, ind) + cx.text[n.else_s:n.e]
            yield Move("OR-DUP", cx.T(n.c), [(n.s, n.e, new)])
        if isinstance(n.els, C.If) and n.els.els is None and norm(cx.T(n.then)) == norm(cx.T(n.els.then)):
            new_c = f"{cx.wrap(n.c, 4)} || {cx.wrap(n.els.c, 5)}"
            yield Move("OR-DUP", "join " + cx.T(n.c), [(n.c.s, n.c.e, new_c), (n.then.e, n.els.e, "")])


@rule("AND-NEST", "block layout observations (if (c) goto L), REG-6 region allocation", "code",
      "if (a && b) S <-> if (a) { if (b) S }")
def r_and_nest(cx: Ctx):
    for n in cx.nodes:
        if not isinstance(n, C.If):
            continue
        c = C.strip_paren(n.c)
        ind = cx.indent(n.s)
        if n.els is not None:
            # if (a && b) S else E  ->  if (a) { if (b) S else E } else E
            if isinstance(c, C.Bin) and c.op == "&&" and not isinstance(n.els, C.If) \
                    and not any(isinstance(z, (C.Label, C.Case)) for z in C.walk(n.els)):
                i4 = ind + "    "
                new = (f"if ({cx.T(c.l)}) {{\n{i4}if ({cx.T(c.r)}){as_block_body(cx, n.then, i4)}"
                       f"{sub_end(n.then, i4)}else{as_block_body(cx, n.els, i4)}\n{ind}}} else"
                       f"{as_block_body(cx, n.els, ind)}")
                yield Move("AND-NEST", "else " + cx.T(n.c), [(n.s, n.e, new)])
            continue
        if isinstance(c, C.Bin) and c.op == "&&":
            body = as_block_body(cx, n.then, ind + "    ")
            new = f"if ({cx.T(c.l)}) {{\n{ind}    if ({cx.T(c.r)}){body}\n{ind}}}"
            yield Move("AND-NEST", cx.T(n.c), [(n.s, n.e, new)])
        inner = n.then
        if isinstance(inner, C.Block) and len(inner.items) == 1:
            inner = inner.items[0]
        if isinstance(inner, C.If) and inner.els is None:
            new_c = f"{cx.wrap(n.c, 6)} && {cx.wrap(inner.c, 6)}"
            body = as_block_body(cx, inner.then, ind)
            yield Move("AND-NEST", "join " + cx.T(n.c), [(n.s, n.e, f"if ({new_c}){body}")])


@rule("IF-NEG", "REG-6 (if/else vs negated early exit), early returns observation", "code",
      "if (c) A else B -> if (!c) B else A")
def r_if_neg(cx: Ctx):
    for n in cx.nodes:
        if isinstance(n, C.If) and n.els is not None:
            ind = cx.indent(n.s)
            if isinstance(n.els, C.If):
                # an else-if chain becomes the then-branch: braces keep the else bound
                els = " {" + as_block_body(cx, n.els, ind) + "\n" + ind + "}"
                end = " "
            else:
                els = as_block_body(cx, n.els, ind)
                end = sub_end(n.els, ind)
            negs = [cx.neg(n.c)[0]] + ([cx.neg_dm(n.c)[0]] if cx.neg_dm(n.c) else [])
            for k, nc in enumerate(dict.fromkeys(negs)):
                new = f"if ({nc}){els}{end}else{as_block_body(cx, n.then, ind)}"
                yield Move("IF-NEG", ("demorgan " if k else "") + cx.T(n.c), [(n.s, n.e, new)])


@rule("ELSE-WRAP", "early return vs if/else (REG-6, early returns observation)", "code",
      "if (c) {..jump} else {B} <-> if (c) {..jump} B")
def r_else_wrap(cx: Ctx):
    for blk, i, st in cx.lists():
        if not isinstance(st, C.If):
            continue
        ind = cx.indent(st.s)
        if st.els is not None and C.ends_in_jump(st.then) and not isinstance(st.els, C.If):
            body = body_items_text(cx, st.els, ind)
            if body:
                yield Move("ELSE-WRAP", "unwrap " + cx.T(st.c), [(st.then.e, st.e, "\n" + body)])
        if st.els is None and C.ends_in_jump(st.then) and i + 1 < len(blk.items):
            rest = blk.items[i + 1:]
            if any(isinstance(r, C.Decl) for r in rest):
                continue
            seg = cx.text[rest[0].s:rest[-1].e]
            old = cx.indent(rest[0].s)
            inner = ind + "    " + reindent(seg, len(ind) + 4 - len(old))
            sep = " " if isinstance(st.then, C.Block) else "\n" + ind
            yield Move("ELSE-WRAP", "wrap " + cx.T(st.c), [(st.then.e, rest[-1].e, f"{sep}else {{\n{inner}\n{ind}}}")])


@rule("RET-MERGE", "early returns observation (separate returns place the return block first, || last)",
      "code", "if (a) J; if (b) J; <-> if (a || b) J;  (J = identical return/goto/break/continue)")
def r_ret_merge(cx: Ctx):
    for blk, i, st in cx.lists():
        if not (isinstance(st, C.If) and st.els is None):
            continue
        j1 = single_jump(st.then)
        if j1 is None:
            continue
        if i + 1 < len(blk.items):
            nx = blk.items[i + 1]
            if isinstance(nx, C.If) and nx.els is None and single_jump(nx.then) is not None \
                    and norm(cx.T(single_jump(nx.then))) == norm(cx.T(j1)):
                new_c = f"{cx.wrap(st.c, 4)} || {cx.wrap(nx.c, 5)}"
                yield Move("RET-MERGE", "merge " + cx.T(st.c), [(st.c.s, st.c.e, new_c), (st.e, nx.e, "")])
        c = C.strip_paren(st.c)
        if isinstance(c, C.Bin) and c.op == "||":
            ind = cx.indent(st.s)
            gap = cx.text[cx.cond_rparen(st):st.then.s]
            th = cx.T(st.then)
            new = f"if ({cx.T(c.l)}){gap}{th}\n{ind}if ({cx.T(c.r)}){gap}{th}"
            yield Move("RET-MERGE", "split " + cx.T(st.c), [(st.s, st.e, new)])


def single_jump(st):
    if isinstance(st, C.Block) and len(st.items) == 1:
        st = st.items[0]
    if isinstance(st, (C.Return, C.Jump)):
        return st
    return None


@rule("TERN-IF", "ZI-3 (f(c ? a : b) vs if/else calls: same bytes, more line entries), TERN-1", "code",
      "x = c ? a : b; <-> if (c) x = a; else x = b;  (also returns and call arguments)")
def r_tern_if(cx: Ctx):
    for blk, i, st in cx.lists():
        ind = cx.indent(st.s)
        if isinstance(st, C.ExprStmt):
            x = st.x
            if isinstance(x, C.Assign) and isinstance(C.strip_paren(x.r), C.Cond) and pure(x.l):
                cnd = C.strip_paren(x.r)
                lhs = f"{cx.T(x.l)} {x.op}"
                new = (f"if ({cx.T(cnd.c)})\n{ind}    {lhs} {cx.T(cnd.a)};\n{ind}else\n{ind}    {lhs} {cx.T(cnd.b)};")
                yield Move("TERN-IF", cx.T(st), [(st.s, st.e, new)])
            if isinstance(x, C.Call):
                conds = [k for k, a in enumerate(x.args) if isinstance(C.strip_paren(a), C.Cond)]
                if len(conds) == 1 and all(pure(a) for k, a in enumerate(x.args) if k != conds[0]):
                    k = conds[0]
                    cnd = C.strip_paren(x.args[k])
                    arg = x.args[k]

                    def call_with(t):
                        return cx.text[x.s:arg.s] + t + cx.text[arg.e:x.e]
                    new = (f"if ({cx.T(cnd.c)})\n{ind}    {call_with(cx.T(cnd.a))};\n{ind}else\n{ind}    "
                           f"{call_with(cx.T(cnd.b))};")
                    yield Move("TERN-IF", cx.T(st), [(st.s, st.e, new)])
        if isinstance(st, C.Return) and st.x is not None and isinstance(C.strip_paren(st.x), C.Cond):
            cnd = C.strip_paren(st.x)
            new = f"if ({cx.T(cnd.c)})\n{ind}    return {cx.T(cnd.a)};\n{ind}return {cx.T(cnd.b)};"
            yield Move("TERN-IF", cx.T(st), [(st.s, st.e, new)])
        # reverse forms
        if isinstance(st, C.If) and st.els is not None:
            a, b = one_stmt(st.then), one_stmt(st.els)
            if isinstance(a, C.ExprStmt) and isinstance(b, C.ExprStmt):
                xa, xb = a.x, b.x
                if isinstance(xa, C.Assign) and isinstance(xb, C.Assign) and xa.op == xb.op \
                        and norm(cx.T(xa.l)) == norm(cx.T(xb.l)):
                    new = f"{cx.T(xa.l)} {xa.op} {cx.wrap(st.c, 4)} ? {cx.T(xa.r)} : {cx.wrap(xb.r, C.P_COND)};"
                    yield Move("TERN-IF", "join " + cx.T(st.c), [(st.s, st.e, new)])
                if isinstance(xa, C.Call) and isinstance(xb, C.Call) and len(xa.args) == len(xb.args) \
                        and norm(cx.T(xa.f)) == norm(cx.T(xb.f)):
                    diff = [k for k in range(len(xa.args)) if norm(cx.T(xa.args[k])) != norm(cx.T(xb.args[k]))]
                    if len(diff) == 1:
                        k = diff[0]
                        t = f"{cx.wrap(st.c, 4)} ? {cx.T(xa.args[k])} : {cx.wrap(xb.args[k], C.P_COND)}"
                        new = cx.text[xa.s:xa.args[k].s] + t + cx.text[xa.args[k].e:xa.e] + ";"
                        yield Move("TERN-IF", "join " + cx.T(st.c), [(st.s, st.e, new)])
            if isinstance(a, C.Return) and isinstance(b, C.Return) and a.x is not None and b.x is not None:
                new = f"return {cx.wrap(st.c, 4)} ? {cx.T(a.x)} : {cx.wrap(b.x, C.P_COND)};"
                yield Move("TERN-IF", "join " + cx.T(st.c), [(st.s, st.e, new)])
        if isinstance(st, C.If) and st.els is None and i + 1 < len(blk.items):
            a, nx = one_stmt(st.then), blk.items[i + 1]
            if isinstance(a, C.Return) and isinstance(nx, C.Return) and a.x is not None and nx.x is not None:
                new = f"return {cx.wrap(st.c, 4)} ? {cx.T(a.x)} : {cx.wrap(nx.x, C.P_COND)};"
                yield Move("TERN-IF", "join ret " + cx.T(st.c), [(st.s, nx.e, new)])


def one_stmt(st):
    if isinstance(st, C.Block) and len(st.items) == 1:
        return st.items[0]
    return st


@rule("FOR-WHILE", "LOOP-1 (loop entry test), /Zi line entries of for headers", "code",
      "for (i; c; s) S <-> i; while (c) { S s; }")
def r_for_while(cx: Ctx):
    for blk, i, st in cx.lists():
        ind = cx.indent(st.s)
        if isinstance(st, C.For) and st.init is not None and st.c is not None and st.step is not None \
                and not C.contains_jump_kind(st.body, ("continue",)):
            inner = body_items_text(cx, st.body, ind + "    ")
            new = (f"{cx.T(st.init)};\n{ind}while ({cx.T(st.c)}) {{\n" + (inner + "\n" if inner else "")
                   + f"{ind}    {cx.T(st.step)};\n{ind}}}")
            yield Move("FOR-WHILE", cx.T(st)[:60], [(st.s, st.e, new)])
        if isinstance(st, C.While) and i > 0 and isinstance(st.body, C.Block) and len(st.body.items) >= 2:
            prev = blk.items[i - 1]
            last = st.body.items[-1]
            if isinstance(prev, C.ExprStmt) and isinstance(last, C.ExprStmt) and pure(st.c) \
                    and not C.contains_jump_kind(st.body, ("continue",)) and not isinstance(prev, C.Label):
                rest = st.body.items[:-1]
                seg = cx.text[rest[0].s:rest[-1].e]
                body = "{\n" + cx.indent(rest[0].s) + seg + "\n" + ind + "}"
                if len(rest) == 1:
                    body = "\n" + cx.indent(rest[0].s) + seg
                    new = f"for ({cx.T(prev.x)}; {cx.T(st.c)}; {cx.T(last.x)}){body}"
                else:
                    new = f"for ({cx.T(prev.x)}; {cx.T(st.c)}; {cx.T(last.x)}) {body}"
                yield Move("FOR-WHILE", "for " + cx.T(st.c), [(prev.s, st.e, new)])


# ------------------------------------------------------------------ locals


def top_index_of(cx: Ctx, node) -> int | None:
    """Index of the top-level body statement containing node."""
    for k, st in enumerate(cx.fn.body.items):
        if st.s <= node.s and node.e <= st.e:
            return k
    return None


def uses(cx: Ctx, name):
    return [n for n in cx.nodes if isinstance(n, C.Id) and n.name == name]


def remove_declarator(cx: Ctx, name: str):
    """Edits that delete local `name`'s declarator (whole line if it is the only one)."""
    d, dd = cx.locals[name]
    if len(d.decls) == 1:
        s, e = cx.line_span(d)
        return [(s, e, "")]
    k = d.decls.index(dd)
    if k + 1 < len(d.decls):
        return [(dd.s, d.decls[k + 1].s, "")]
    return [(d.decls[k - 1].e, dd.e, "")]


def rename_edits(cx: Ctx, old: str, new: str, lo: int = 0, hi: int | None = None):
    hi = len(cx.text) if hi is None else hi
    return [(n.s, n.e, new) for n in uses(cx, old) if lo <= n.s and n.e <= hi]


def fresh_name(cx: Ctx, base: str) -> str:
    used = set(re.findall(r"[A-Za-z_]\w*", cx.text))
    for k in range(2, 100):
        n = f"{base}{k}"
        if n not in used:
            return n
    raise ValueError("no fresh name")


def decl_insert_point(cx: Ctx) -> tuple[int, str]:
    """(offset, indent) after the last top-level declaration of the body (or at the body start)."""
    items = cx.fn.body.items
    decls = [st for st in items if isinstance(st, C.Decl)]
    if decls:
        last = decls[-1]
        return cx.line_span(last)[1], cx.indent(last.s)
    b = cx.fn.body.s + 1
    first = items[0] if items else None
    ind = cx.indent(first.s) if first is not None else "    "
    nl = cx.text.find("\n", b)
    return nl + 1, ind


def first_stmt_point(cx: Ctx) -> tuple[int, str]:
    items = [st for st in cx.fn.body.items if not isinstance(st, C.Decl)]
    if not items:
        return decl_insert_point(cx)
    st = items[0]
    s, _ = cx.line_span(st)
    return s, cx.indent(st.s)


@rule("CSE-INLINE", "BP-slot values while SI/DI are free are /Og CSE temporaries (218D:02D5/000C); "
      "repeated far char expression gets a byte CSE temp (simB)", "code",
      "t = E; ...t...t  ->  ...E...E  (single-assignment local, pure E)")
def r_cse_inline(cx: Ctx):
    for name, (d, dd) in cx.locals.items():
        if name in cx.addr_taken or dd.is_array or dd.init is not None or d.storage == "static":
            continue
        occ = uses(cx, name)
        writes = [o for o in occ if is_write(cx, o)]
        if len(writes) != 1:
            continue
        w = writes[0]
        a = cx.par(w)
        st = cx.par(a)
        if not (isinstance(a, C.Assign) and a.op == "=" and isinstance(st, C.ExprStmt)):
            continue
        e = a.r
        if not pure(e) or name in C.idents(e):
            continue
        # every read after the statement, within the same block
        blk = cx.par(st)
        if not isinstance(blk, C.Block):
            continue
        k = blk.items.index(st)
        reads = [o for o in occ if o is not w]
        if not reads or any(o.s < st.e or o.e > blk.items[-1].e for o in reads):
            continue
        last = max(o.e for o in reads)
        between = [x for x in blk.items[k + 1:] if x.s < last]
        vars_e = set(C.idents(e))
        nonlocal_read = any(v not in cx.locals and v not in cx.params for v in vars_e)
        bad = False
        for x in between:
            if C.writes(x) & vars_e:
                bad = True
            if nonlocal_read and any(isinstance(z, (C.Call, C.Assign)) for z in C.walk(x)):
                # a call or store may change the global E reads (stores only when E reads memory)
                if any(isinstance(z, C.Call) for z in C.walk(x)) or any(
                        isinstance(z, C.Assign) and not isinstance(C.strip_paren(z.l), C.Id) for z in C.walk(x)):
                    bad = True
            if any(isinstance(z, (C.Label,)) for z in C.walk(x)):
                bad = True
        if bad:
            continue
        ed = [cx.replace_expr(o, cx.T(e), C.prec_of(e)) for o in reads]
        ed.append(cx.line_span(st) + ("",))
        ed += remove_declarator(cx, name)
        try:
            ed = dedupe(ed)
        except ValueError:
            continue
        yield Move("CSE-INLINE", f"{name} = {cx.T(e)}", ed)


def dedupe(ed):
    out = sorted(set(ed), key=lambda x: (x[0], x[1]))
    for a, b in zip(out, out[1:]):
        if b[0] < a[1]:
            raise ValueError("overlap")
    return out


def is_write(cx: Ctx, o) -> bool:
    p = cx.par(o)
    while isinstance(p, C.Paren):
        o, p = p, cx.par(p)
    if isinstance(p, C.Assign) and o is p.l:
        return True
    if isinstance(p, (C.Post,)) or (isinstance(p, C.Unary) and p.op in ("++", "--")):
        return True
    return False


@rule("CSE-REUSE", "CSE temporary observations (repeat expression vs cached local), STORE-1", "code",
      "v = E; ... E ...  ->  v = E; ... v ...")
def r_cse_reuse(cx: Ctx):
    for blk, i, st in cx.lists():
        if not (isinstance(st, C.ExprStmt) and isinstance(st.x, C.Assign) and st.x.op == "="
                and isinstance(C.strip_paren(st.x.l), C.Id)):
            continue
        v = C.strip_paren(st.x.l).name
        e = st.x.r
        if not pure(e) or isinstance(C.strip_paren(e), (C.Id, C.Num)) or v in C.idents(e):
            continue
        ne = norm(cx.T(e))
        vars_e = set(C.idents(e)) | {v}
        nonlocal_read = any(x not in cx.locals and x not in cx.params for x in vars_e)
        ed = []
        for x in blk.items[i + 1:]:
            hits = [n for n in C.walk(x) if isinstance(n, C.Expr) and norm(cx.T(n)) == ne
                    and not (isinstance(cx.par(n), C.Assign) and cx.par(n).l is n)]
            # keep only outermost hits
            hits = [h for h in hits if not any(o is not h and o.s <= h.s and h.e <= o.e for o in hits)]
            ed += [cx.replace_expr(h, v, C.P_PRIMARY) for h in hits]
            if C.writes(x) & vars_e or (nonlocal_read and any(isinstance(z, C.Call) for z in C.walk(x))) \
                    or any(isinstance(z, C.Label) for z in C.walk(x)):
                if hits:
                    ed = ed[:len(ed) - len(hits)]
                break
        if ed:
            yield Move("CSE-REUSE", f"{v} = {cx.T(e)}", ed)


@rule("LOCAL-MERGE", "reuse vs separate locals (REG-5; /Og overlays disjoint locals)", "code",
      "two same-type locals with disjoint top-level live ranges -> one local")
def r_local_merge(cx: Ctx):
    if cx.has_goto:
        return
    names = [n for n, (d, dd) in cx.locals.items()
             if n not in cx.addr_taken and not dd.is_array and dd.init is None and d.storage != "static"
             and cx.par(d) is cx.fn.body]
    ranges = {}
    for n in names:
        occ = uses(cx, n)
        if not occ:
            continue
        idx = [top_index_of(cx, o) for o in occ]
        if None in idx:
            continue
        ranges[n] = (min(idx), max(idx), occ)
    for a in names:
        for b in names:
            if a == b or a not in ranges or b not in ranges:
                continue
            if norm(cx.local_type(a)) != norm(cx.local_type(b)):
                continue
            da, db = cx.locals[a][1], cx.locals[b][1]
            if da.is_pointer != db.is_pointer:
                continue
            ea, eb = ranges[a], ranges[b]
            if not ea[1] < eb[0]:
                continue
            first = min(eb[2], key=lambda o: o.s)
            st = cx.fn.body.items[eb[0]]
            if not (isinstance(st, C.ExprStmt) and isinstance(st.x, C.Assign) and st.x.op == "="
                    and C.strip_paren(st.x.l) is first and b not in C.idents(st.x.r)):
                continue
            ed = rename_edits(cx, b, a) + remove_declarator(cx, b)
            yield Move("LOCAL-MERGE", f"{b} -> {a}", ed)


@rule("LOCAL-SPLIT", "REG-5 (new locals for recomputed positions), reuse vs separate locals", "code",
      "a local re-assigned at top level gets a new local for its second live range")
def r_local_split(cx: Ctx):
    if cx.has_goto:
        return
    items = cx.fn.body.items
    for name in list(cx.locals) + list(cx.params):
        if name in cx.addr_taken:
            continue
        if name in cx.locals:
            d, dd = cx.locals[name]
            if dd.is_array or d.storage == "static" or cx.par(d) is not cx.fn.body:
                continue
            typ = cx.text[d.spec_s:d.spec_e] + (" *" * 0)
            if dd.is_pointer:
                typ = cx.text[d.spec_s:dd.name_s].strip() if len(d.decls) == 1 else None
        else:
            typ = next(t for t, p in cx.fn.params if p == name)
        if not typ:
            continue
        occ = uses(cx, name)
        for k, st in enumerate(items):
            if not (isinstance(st, C.ExprStmt) and isinstance(st.x, C.Assign)
                    and isinstance(C.strip_paren(st.x.l), C.Id) and C.strip_paren(st.x.l).name == name):
                continue
            before = [o for o in occ if o.e <= st.s]
            after = [o for o in occ if o.s >= st.e]
            if not before or not after:
                continue
            nn = fresh_name(cx, name)
            at, ind = decl_insert_point(cx)
            ed = [(at, at, f"{ind}{typ} {nn};\n")]
            if st.x.op == "=":
                if name in C.idents(st.x.r):
                    continue
                ed.append((st.x.l.s, st.x.l.e, nn))
            else:
                op = st.x.op[:-1]
                ed.append((st.x.s, st.x.e, f"{nn} = {name} {op} {cx.wrap(st.x.r, C.PREC[op] + 1)}"))
            ed += [(o.s, o.e, nn) for o in after]
            yield Move("LOCAL-SPLIT", f"{name} @ {cx.T(st)}", ed)


@rule("PARAM-COPY", "SPLIT-1 (local copy of a far pointer parameter), local copies of parameters", "code",
      "param p -> local q = p; uses of p become q")
def r_param_copy(cx: Ctx):
    for typ, p in cx.fn.params:
        if not p or p in cx.addr_taken:
            continue
        occ = uses(cx, p)
        if not occ:
            continue
        nn = fresh_name(cx, p)
        at, ind = decl_insert_point(cx)
        fs, find = first_stmt_point(cx)
        ed = [(at, at, f"{ind}{typ} {nn};\n")]
        if fs == at:
            ed = [(at, at, f"{ind}{typ} {nn};\n\n{find}{nn} = {p};\n")]
        else:
            ed.append((fs, fs, f"{find}{nn} = {p};\n"))
        ed += [(o.s, o.e, nn) for o in occ]
        try:
            ed = dedupe(ed)
        except ValueError:
            continue
        yield Move("PARAM-COPY", p, ed)


@rule("RESULT-LOCAL", "REG-2 (a local that only carries the return value still takes SI)", "code",
      "return E; -> r = E; return r;  (new local of the return type)")
def r_result_local(cx: Ctx):
    rt = return_type(cx)
    if not rt or rt == "void":
        return
    rets = [n for n in cx.nodes if isinstance(n, C.Return) and n.x is not None
            and not isinstance(C.strip_paren(n.x), (C.Id, C.Num))]
    if not rets:
        return
    nn = fresh_name(cx, "result")
    at, ind = decl_insert_point(cx)
    for r in rets:
        blk = cx.par(r)
        if not isinstance(blk, C.Block):
            continue
        i2 = cx.indent(r.s)
        ed = [(at, at, f"{ind}{rt} {nn};\n"), (r.s, r.e, f"{nn} = {cx.T(r.x)};\n{i2}return {nn};")]
        yield Move("RESULT-LOCAL", cx.T(r), ed)


def return_type(cx: Ctx) -> str | None:
    head = cx.text[cx.fn.head_s:cx.fn.params_s]
    head = head[:head.rfind(cx.fn.name)]
    head = re.split(r"[;}]|\*/", head)[-1]
    toks = head.split()
    while toks and toks[-1] in ("far", "near", "pascal", "cdecl", "_fastcall", "_loadds", "_pascal", "_cdecl",
                                "_far", "_near", "_export", "_saveregs", "_interrupt", "interrupt"):
        toks.pop()
    toks = [t for t in toks if t not in ("static", "extern")]
    return " ".join(toks) or None


@rule("DECL-SWAP", "declaration order (identifier windows, slot order of address-taken locals)", "decl",
      "swap two adjacent local declarations")
def r_decl_swap(cx: Ctx):
    for blk, i, st in cx.lists():
        if isinstance(st, C.Decl) and st.storage != "typedef":
            if i + 1 < len(blk.items) and isinstance(blk.items[i + 1], C.Decl):
                nx = blk.items[i + 1]
                if any(d.init is not None and not isinstance(d.init, C.Num) for d in st.decls + nx.decls):
                    continue
                yield Move("DECL-SWAP", f"{cx.T(st)} / {cx.T(nx)}",
                           [(st.s, st.e, cx.T(nx)), (nx.s, nx.e, cx.T(st))])
            if len(st.decls) >= 2 and all(d.init is None for d in st.decls):
                for k in range(len(st.decls) - 1):
                    a, b = st.decls[k], st.decls[k + 1]
                    yield Move("DECL-SWAP", f"{cx.T(a)} , {cx.T(b)}", [(a.s, a.e, cx.T(b)), (b.s, b.e, cx.T(a))])


@rule("DECL-INIT", "declaration form (int x = E vs int x; x = E)", "code",
      "int x = E;  <->  int x; ... x = E;")
def r_decl_init(cx: Ctx):
    items = cx.fn.body.items
    decls = [st for st in items if isinstance(st, C.Decl)]
    for st in decls:
        if st.storage == "static" or len(st.decls) != 1:
            continue
        dd = st.decls[0]
        if dd.init is None or isinstance(dd.init, C.InitList) or dd.is_array:
            continue
        later = decls[decls.index(st) + 1:]
        if any(d.init is not None and not pure(d.init) for x in later for d in x.decls):
            continue
        at, ind = first_stmt_point(cx)
        yield Move("DECL-INIT", cx.T(st), [(dd.name_s + len(dd.name), dd.e, ""), (at, at, f"{ind}{dd.name} = {cx.T(dd.init)};\n")])
    # join: first statement 'x = E;' for x declared without initialiser
    stmts = [st for st in items if not isinstance(st, C.Decl)]
    if stmts and isinstance(stmts[0], C.ExprStmt) and isinstance(stmts[0].x, C.Assign) and stmts[0].x.op == "=":
        v = C.strip_paren(stmts[0].x.l)
        if isinstance(v, C.Id) and v.name in cx.locals:
            d, dd = cx.locals[v.name]
            e = stmts[0].x.r
            if cx.par(d) is cx.fn.body and dd.init is None and not dd.is_array and \
                    not any(x in cx.locals for x in C.idents(e)):
                s0, e0 = cx.line_span(stmts[0])
                yield Move("DECL-INIT", "join " + cx.T(stmts[0]), [(dd.e, dd.e, f" = {cx.T(e)}"), (s0, e0, "")])


@rule("DEAD-AUTO", "one plain auto removes dead far-address spills (JamScent*, AlarmHere2), DEAD-1/2", "steer",
      "add an unused int local (steering: analysis only)")
def r_dead_auto(cx: Ctx):
    nn = fresh_name(cx, "unused")
    at, ind = decl_insert_point(cx)
    yield Move("DEAD-AUTO", "int unused", [(at, at, f"{ind}int {nn};\n")])


# ------------------------------------------------------------------ file level


def top_decls(cx: Ctx):
    """Top-level declarations before the function: [(s, e, text, names)] (statement spans)."""
    src = cx.src
    out = []
    depth = 0
    start = None
    names = []
    fbody = False
    prev = None
    for t in src.sig:
        if t.s >= cx.fn.head_s:
            break
        if start is None:
            start = t.s
            names = []
        if t.text == "{":
            if depth == 0 and prev is not None and prev.text == ")":
                fbody = True
            depth += 1
        elif t.text == "}":
            depth -= 1
            if depth == 0 and fbody:
                fbody = False
                start = None
                prev = t
                continue
        elif t.kind == "id" and depth == 0:
            names.append(t.text)
        if t.text == ";" and depth == 0:
            out.append((start, t.e, src.text[start:t.e], names))
            start = None
        prev = t
    # drop function definitions (they contain '{' ... '}' followed by no ';' handled by span start)
    return [d for d in out if "{" not in d[2] or d[2].lstrip().startswith(("struct", "typedef", "union", "enum"))]


def callees(cx: Ctx) -> set:
    return {C.strip_paren(n.f).name for n in cx.nodes if isinstance(n, C.Call) and isinstance(C.strip_paren(n.f), C.Id)}


def prototypes(cx: Ctx):
    """[(decl_s, lp, rp, name, params)] for top-level prototypes of functions the target calls."""
    want = callees(cx)
    out = []
    for s, e, text, names in top_decls(cx):
        m = None
        for mm in re.finditer(r"\b([A-Za-z_]\w*)\s*\(", text):
            if mm.group(1) in want:
                m = mm
                break
        if m is None or "{" in text:
            continue
        lp = s + m.end() - 1
        depth, j = 0, lp
        while j < e:
            if cx.text[j] == "(":
                depth += 1
            elif cx.text[j] == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        params = [p.strip() for p in split_params(cx.text[lp + 1:j])]
        out.append((s, lp, j, m.group(1), params))
    return out


def split_params(t: str) -> list[str]:
    out, cur, d = [], "", 0
    for ch in t:
        if ch == "(":
            d += 1
        elif ch == ")":
            d -= 1
        if ch == "," and d == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    return out


def param_name(p: str) -> str | None:
    toks = re.findall(r"[A-Za-z_]\w*", p)
    toks = [t for t in toks if t not in C.TYPE_WORDS and t not in C.STORAGE]
    if not toks or p.strip().endswith("*") or p.strip() in ("void", "..."):
        return None
    # a lone typedef name is a type, not a parameter name
    words = re.findall(r"[A-Za-z_]\w*", p)
    if len(words) == 1:
        return None
    return toks[-1] if re.search(r"\b" + re.escape(toks[-1]) + r"\s*(\[[^\]]*\])?\s*$", p) else None


@rule("PROTO-NAMES", "symbol-table count (named prototype parameters are identifiers), SYM-1", "decl",
      "named <-> unnamed parameters in the prototype of a callee")
def r_proto_names(cx: Ctx):
    for s, lp, rp, name, params in prototypes(cx):
        if not params or params == ["void"]:
            continue
        named = [param_name(p) for p in params]
        if any(named):
            new = []
            for p, n in zip(params, named):
                new.append(re.sub(r"\s*\b" + re.escape(n) + r"\s*(\[[^\]]*\])?\s*$", r"\1", p) if n else p)
            yield Move("PROTO-NAMES", f"{name} unnamed", [(lp + 1, rp, ", ".join(new))])
        else:
            new = [p if p == "..." else f"{p}{'' if p.endswith('*') else ' '}{'p%d' % k}" for k, p in enumerate(params)]
            yield Move("PROTO-NAMES", f"{name} named", [(lp + 1, rp, ", ".join(new))])


@rule("PROTO-TYPE", "PROTO-1/PROTO-2 (declared parameter type of constant arguments), REG-4 (variadic)", "decl",
      "callee prototype: int <-> unsigned parameter, (x, ...) variadic, () unprototyped")
def r_proto_type(cx: Ctx):
    for s, lp, rp, name, params in prototypes(cx):
        if not params or params == ["void"]:
            continue
        for k, p in enumerate(params):
            if re.match(r"^(int|long)\b", p):
                q = "unsigned " + p
            elif re.match(r"^unsigned\s+(int|long)\b", p):
                q = re.sub(r"^unsigned\s+", "", p)
            elif re.match(r"^unsigned\b", p):
                q = re.sub(r"^unsigned\b", "int", p)
            else:
                continue
            new = params[:k] + [q] + params[k + 1:]
            yield Move("PROTO-TYPE", f"{name} arg{k} {q}", [(lp + 1, rp, ", ".join(new))])
        if "..." not in params and len(params) >= 2:
            yield Move("PROTO-TYPE", f"{name} variadic", [(lp + 1, rp, params[0] + ", ...")])
        yield Move("PROTO-TYPE", f"{name} unprototyped", [(lp + 1, rp, "")])


@rule("EXTERN-SWAP", "declaration order of externs (symbol-table state, SYM-1, first-use order)", "decl",
      "swap two adjacent top-level declarations, one of them referenced by the function")
def r_extern_swap(cx: Ctx):
    refs = set(C.idents(cx.fn.body))
    ds = top_decls(cx)
    for a, b in zip(ds, ds[1:]):
        if "{" in a[2] or "{" in b[2] or a[2].lstrip().startswith("typedef") or b[2].lstrip().startswith("typedef"):
            continue
        if not (set(a[3]) & refs or set(b[3]) & refs):
            continue
        between = cx.text[a[1]:b[0]]
        if "#" in between or "/*" in between:
            continue
        yield Move("EXTERN-SWAP", f"{a[2].strip()[:50]} <> {b[2].strip()[:50]}",
                   [(a[0], a[1], b[2]), (b[0], b[1], a[2])])


# ------------------------------------------------------------------ enumeration

DEFAULT_RULES = [r for r in RULES if RULES[r].category != "steer"]


def enumerate_moves(text: str, fname: str, rules=None) -> list[Move]:
    cx = Ctx(text, fname)
    out = []
    for rid in (rules or DEFAULT_RULES):
        r = RULES[rid]
        seen = {}
        try:
            for mv in r.fn(cx):
                k = mv.key
                seen[k] = seen.get(k, 0) + 1
                if seen[k] > 1:
                    mv.key = f"{k}#{seen[k]}"
                out.append(mv)
        except (C.ParseError, ValueError, KeyError, IndexError, StopIteration):
            continue
    return out


def apply_move(text: str, mv: Move) -> str:
    return apply_edits(text, mv.edits)


def valid_variant(text: str, fname: str) -> bool:
    """A variant must still parse and still define the function."""
    try:
        C.Source(text).function(fname)
        return True
    except (C.ParseError, KeyError, IndexError):
        return False


# ------------------------------------------------------------------ later additions


@rule("TEMP-INTRO", "CSE temporaries vs named locals (reverse of CSE-INLINE), STORE-1, REG-5", "code",
      "S(... e ...)  ->  t = e; S(... t ...)  (new int local for an operand subexpression)")
def r_temp_intro(cx: Ctx):
    at, ind0 = decl_insert_point(cx)
    for blk, i, st in cx.lists():
        if isinstance(st, (C.Label, C.Case, C.Decl)):
            continue
        for root in stmt_expr_roots(st):
            for e in C.walk(root):
                if e is root or not isinstance(e, (C.Call, C.Index, C.Member, C.Bin)):
                    continue
                p = cx.par(e)
                if not ((isinstance(p, C.Bin) and p.op not in ("&&", "||"))
                        or (isinstance(p, C.Call) and e is not p.f)
                        or (isinstance(p, C.Index) and e is p.i)):
                    continue
                if isinstance(e, C.Bin) and e.op in ("&&", "||"):
                    continue
                if any(isinstance(z, C.Assign) or isinstance(z, C.Post) for z in C.walk(e)):
                    continue
                if conditional_position(cx, e, root):
                    continue
                if isinstance(st, C.ExprStmt) and isinstance(root, C.Assign) and (e is root.l or
                                                                                   (root.l.s <= e.s and e.e <= root.l.e)):
                    continue
                nn = fresh_name(cx, "tmp")
                ind = cx.indent(st.s)
                ed = [(at, at, f"{ind0}int {nn};\n"), (st.s, st.s, f"{nn} = {cx.T(e)};\n{ind}"), (e.s, e.e, nn)]
                try:
                    ed = dedupe(ed)
                except ValueError:
                    continue
                yield Move("TEMP-INTRO", cx.T(e), ed)


def case_groups(sw):
    """[(start, end, [items])] of a switch body: each group runs from a case label to the next."""
    if not isinstance(sw.body, C.Block):
        return []
    groups = []
    for it in sw.body.items:
        if isinstance(it, C.Case):
            groups.append([it])
        elif groups:
            groups[-1].append(it)
    return groups


def case_tail_jump(cx, g) -> bool:
    last = g[-1]
    while isinstance(last, (C.Case, C.Label)) and last.stmt is not None:
        last = last.stmt
    return isinstance(last, (C.Return, C.Jump)) or C.ends_in_jump(last)


@rule("CASE-SWAP", "switch observations (case blocks laid out by value; merged identical cases, LessonDone)",
      "code", "swap two adjacent case groups that both end in a jump")
def r_case_swap(cx: Ctx):
    for sw in cx.nodes:
        if not isinstance(sw, C.Switch):
            continue
        gs = case_groups(sw)
        for a, b in zip(gs, gs[1:]):
            if not (case_tail_jump(cx, a) and case_tail_jump(cx, b)):
                continue
            sa, ea = a[0].s, a[-1].e
            sb, eb = b[0].s, b[-1].e
            ta, tb = cx.text[sa:ea], cx.text[sb:eb]
            yield Move("CASE-SWAP", f"{ta[:30]} <> {tb[:30]}", [(sa, ea, tb), (sb, eb, ta)])


DEFAULT_RULES = [r for r in RULES if RULES[r].category != "steer"]


def reads_writes(cx: Ctx, st):
    """(read texts, written texts, has_call) of a statement; lvalues compared by normalised text."""
    w, r = set(), set()
    call = False
    for n in C.walk(st):
        if isinstance(n, C.Call):
            call = True
        if isinstance(n, C.Assign):
            w.add(norm(cx.T(n.l)))
            if isinstance(C.strip_paren(n.l), C.Id):
                w.add(C.strip_paren(n.l).name)
        elif isinstance(n, (C.Post, C.Unary)) and n.op in ("++", "--"):
            w.add(norm(cx.T(n.x)))
        if isinstance(n, (C.Id, C.Member, C.Index)):
            p = cx.par(n)
            if isinstance(p, C.Member) or (isinstance(p, C.Index) and n is p.a):
                continue           # only whole access paths
            r.add(norm(cx.T(n)) if not isinstance(n, C.Id) else n.name)
    return r, w, call


@rule("STMT-SWAP", "statement order vs /Og store sinking (STORE-1), block layout observations", "code",
      "swap two adjacent independent expression statements")
def r_stmt_swap(cx: Ctx):
    for blk, i, st in cx.lists():
        if i + 1 >= len(blk.items):
            continue
        nx = blk.items[i + 1]
        if not (isinstance(st, C.ExprStmt) and isinstance(nx, C.ExprStmt)):
            continue
        ra, wa, ca = reads_writes(cx, st)
        rb, wb, cb = reads_writes(cx, nx)
        if ca and cb:
            continue
        if (ca and wb) or (cb and wa):
            continue

        def overlap(x, y):
            if x == y:
                return True
            a, b = (x, y) if len(x) < len(y) else (y, x)
            if b.startswith(a) and b[len(a)] in ".[-":
                return True
            # element accesses of one array may alias whatever their indices
            return ("[" in a or "[" in b) and a.split("[")[0] == b.split("[")[0]

        def clash(ws, rs):
            return any(overlap(x, y) for x in ws for y in rs)
        if clash(wa, rb | wb) or clash(wb, ra):
            continue
        yield Move("STMT-SWAP", f"{cx.T(st)} <> {cx.T(nx)}", [(st.s, st.e, cx.T(nx)), (nx.s, nx.e, cx.T(st))])


@rule("STORE-LOCAL", "STORE-1 (compute a stored member value into a local first), REG-5", "code",
      "M = E; ... M ...  ->  t = E; M = t; ... t ...  (M a member/element, t a new int local)")
def r_store_local(cx: Ctx):
    at, ind0 = decl_insert_point(cx)
    for blk, i, st in cx.lists():
        if not (isinstance(st, C.ExprStmt) and isinstance(st.x, C.Assign) and st.x.op == "="
                and isinstance(C.strip_paren(st.x.l), (C.Member, C.Index, C.Unary))):
            continue
        m = norm(cx.T(st.x.l))
        nn = fresh_name(cx, "val")
        ind = cx.indent(st.s)
        ed = [(at, at, f"{ind0}int {nn};\n"), (st.s, st.e, f"{nn} = {cx.T(st.x.r)};\n{ind}{cx.T(st.x.l)} = {nn};")]
        for x in blk.items[i + 1:]:
            hits = [n for n in C.walk(x) if isinstance(n, C.Expr) and norm(cx.T(n)) == m and not is_write(cx, n)]
            ed += [(h.s, h.e, nn) for h in hits]
            _, w, call = reads_writes(cx, x)
            if m in w or call or any(isinstance(z, C.Label) for z in C.walk(x)):
                break
        try:
            ed = dedupe(ed)
        except ValueError:
            continue
        yield Move("STORE-LOCAL", cx.T(st), ed)


DEFAULT_RULES = [r for r in RULES if RULES[r].category != "steer"]


def all_prototypes(cx: Ctx):
    """[(decl_s, lp, rp, name, params)] for every top-level function prototype before the function."""
    out = []
    for s, e, text, names in top_decls(cx):
        if "{" in text or text.lstrip().startswith("typedef"):
            continue
        m = re.search(r"\b([A-Za-z_]\w*)\s*\(", text)
        if m is None or m.group(1) in C.TYPE_WORDS:
            continue
        lp = s + m.end() - 1
        depth, j = 0, lp
        while j < e:
            if cx.text[j] == "(":
                depth += 1
            elif cx.text[j] == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        params = [p.strip() for p in split_params(cx.text[lp + 1:j])]
        out.append((s, lp, j, m.group(1), params))
    return out


@rule("SYM-NAMES", "SYM-1 / symbol-table count: named prototype parameters of *any* earlier prototype are "
      "identifiers (S14 CalcScore needed +6 named parameters)", "decl",
      "named <-> unnamed parameters in any prototype before the function")
def r_sym_names(cx: Ctx):
    want = callees(cx)
    for s, lp, rp, name, params in all_prototypes(cx):
        if name in want or not params or params == ["void"] or params == [""]:
            continue
        named = [param_name(p) for p in params]
        if any(named):
            new = [re.sub(r"\s*\b" + re.escape(n) + r"\s*(\[[^\]]*\])?\s*$", r"\1", p) if n else p
                   for p, n in zip(params, named)]
            yield Move("SYM-NAMES", f"{name} unnamed (-{sum(1 for n in named if n)})", [(lp + 1, rp, ", ".join(new))])
        else:
            new = [p if p == "..." else f"{p}{'' if p.endswith('*') else ' '}{'p%d' % k}" for k, p in enumerate(params)]
            yield Move("SYM-NAMES", f"{name} named (+{len(params)})", [(lp + 1, rp, ", ".join(new))])


DEFAULT_RULES = [r for r in RULES if RULES[r].category != "steer"]
