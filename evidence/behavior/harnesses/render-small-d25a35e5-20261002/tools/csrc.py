"""csrc.py - an MSC-6.00-dialect-aware C tokenizer and function-body parser for source rewriting.

Not a compiler front end: it parses enough of one function body (statements, declarations and
expressions with C precedence) to enumerate *targeted* rewrites.  Every node keeps the character
span of the source it came from, so a rewrite replaces one span and everything else stays byte
for byte (comments, line layout, macros).  Dialect features that are kept opaque:

  * preprocessor lines (``#...`` with continuations) are single trivia tokens;
  * ``_asm { ... }`` blocks and ``_asm ...`` single lines are one raw token (asm comments use
    ``;`` and quotes that a C tokenizer must not see);
  * ``far near huge _far _near _huge _based(...) pascal cdecl _pascal _cdecl _fastcall
    _loadds _export _interrupt _saveregs`` are type qualifiers in declarations and casts;
  * macro invocations look like calls, which is what they are for rewriting purposes.

API:
    src = Source(text)                  # tokenizes the whole file
    fn = src.function("Name")           # Function: header span, body Block, params
    body = fn.body                      # Block(items=[Decl | stmt ...])
    for node in walk(body): ...         # every Stmt/Expr/Decl node, pre-order
    node.s, node.e                      # char span in ``text``
    src.text[node.s:node.e]             # original source of a node
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

KEYWORDS = {
    "auto", "break", "case", "char", "const", "continue", "default", "do", "double", "else", "enum",
    "extern", "float", "for", "goto", "if", "int", "long", "register", "return", "short", "signed",
    "sizeof", "static", "struct", "switch", "typedef", "union", "unsigned", "void", "volatile", "while",
}
QUALIFIERS = {"far", "near", "huge", "_far", "_near", "_huge", "__far", "__near", "__huge", "pascal", "cdecl",
              "_pascal", "_cdecl", "__pascal", "__cdecl", "_fastcall", "__fastcall", "_loadds", "_export",
              "_interrupt", "interrupt", "_saveregs", "_based", "__based", "_segment", "const", "volatile"}
TYPE_WORDS = {"int", "char", "short", "long", "unsigned", "signed", "void", "float", "double", "struct",
              "union", "enum"} | QUALIFIERS
STORAGE = {"static", "register", "auto", "extern", "typedef"}
ASM_WORDS = {"_asm", "__asm"}

OPS = sorted(""">>= <<= ... -> ++ -- << >> <= >= == != && || += -= *= /= %= &= ^= |=
    + - * / % & | ^ ! ~ < > = ? : ; , . ( ) [ ] { }""".split(), key=len, reverse=True)
_OP_RE = "|".join(re.escape(o) for o in OPS)
TOKEN_RE = re.compile(r"""
    (?P<nl>\n)
  | (?P<ws>[ \t\r\f\v]+)
  | (?P<cmt>/\*.*?\*/|//[^\n]*)
  | (?P<id>[A-Za-z_$][A-Za-z0-9_$]*)
  | (?P<num>(?:0[xX][0-9A-Fa-f]+|\d+\.\d*(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?|\d+(?:[eE][+-]?\d+)?)[uUlLfF]*)
  | (?P<str>"(?:[^"\\\n]|\\.)*")
  | (?P<chr>'(?:[^'\\\n]|\\.)*')
  | (?P<op>""" + _OP_RE + r""")
  | (?P<bad>.)
""", re.S | re.X)


@dataclass
class Tok:
    kind: str       # id num str chr op pp cmt ws nl asm
    text: str
    s: int
    e: int

    def __repr__(self):
        return f"{self.kind}:{self.text!r}"


class ParseError(Exception):
    pass


def tokenize(text: str) -> list[Tok]:
    """All tokens including trivia.  Preprocessor lines and _asm blocks/lines are single tokens."""
    out: list[Tok] = []
    i, n = 0, len(text)
    line_start = True
    while i < n:
        if line_start:
            m = re.compile(r"[ \t]*#").match(text, i)
            if m:
                j = i
                while True:
                    k = text.find("\n", j)
                    if k < 0:
                        k = n
                        break
                    if text[k - 1] == "\\" or (text[k - 1] == "\r" and text[k - 2] == "\\"):
                        j = k + 1
                        continue
                    break
                out.append(Tok("pp", text[i:k], i, k))
                i = k
                line_start = False
                continue
        m = TOKEN_RE.match(text, i)
        kind = m.lastgroup
        t = m.group()
        if kind == "id" and t in ASM_WORDS:
            # _asm { ... } or _asm <rest of line>
            j = i + len(t)
            while j < n and text[j] in " \t":
                j += 1
            if j < n and text[j] == "{":
                depth, k = 0, j
                while k < n:
                    if text[k] == "{":
                        depth += 1
                    elif text[k] == "}":
                        depth -= 1
                        if depth == 0:
                            break
                    k += 1
                if k >= n:
                    raise ParseError("unterminated _asm block")
                out.append(Tok("asm", text[i:k + 1], i, k + 1))
                i = k + 1
            else:
                k = text.find("\n", j)
                k = n if k < 0 else k
                # a following _asm on the same line starts a new asm token
                m2 = re.compile(r"\b_?_asm\b").search(text, j, k)
                if m2:
                    k = m2.start()
                out.append(Tok("asm", text[i:k].rstrip(), i, i + len(text[i:k].rstrip())))
                i = i + len(text[i:k].rstrip())
            line_start = False
            continue
        if kind == "bad":
            raise ParseError(f"unexpected character {t!r} at {i}")
        out.append(Tok(kind, t, i, i + len(t)))
        i += len(t)
        if kind == "nl":
            line_start = True
        elif kind not in ("ws", "cmt"):
            line_start = False
        elif kind == "cmt" and "\n" in t:
            line_start = False
    return out


# ---------------------------------------------------------------- AST


@dataclass(eq=False)
class Node:
    s: int = 0
    e: int = 0

    def children(self):
        return []


@dataclass(eq=False)
class Expr(Node):
    pass


@dataclass(eq=False)
class Id(Expr):
    name: str = ""


@dataclass(eq=False)
class Num(Expr):
    text: str = ""

    @property
    def value(self) -> int | None:
        t = self.text.rstrip("uUlL")
        try:
            if t.lower().startswith("0x"):
                return int(t, 16)
            if len(t) > 1 and t.startswith("0") and t.isdigit():
                return int(t, 8)
            return int(t)
        except ValueError:
            return None


@dataclass(eq=False)
class Str(Expr):
    text: str = ""


@dataclass(eq=False)
class Paren(Expr):
    x: Expr = None

    def children(self):
        return [self.x]


@dataclass(eq=False)
class Unary(Expr):          # prefix: - + ! ~ * & ++ --  sizeof
    op: str = ""
    x: Expr = None

    def children(self):
        return [self.x]


@dataclass(eq=False)
class Post(Expr):           # postfix ++ --
    op: str = ""
    x: Expr = None

    def children(self):
        return [self.x]


@dataclass(eq=False)
class Cast(Expr):
    type_s: int = 0
    type_e: int = 0
    x: Expr = None

    def children(self):
        return [self.x]


@dataclass(eq=False)
class SizeofType(Expr):
    pass


@dataclass(eq=False)
class Bin(Expr):
    op: str = ""
    l: Expr = None
    r: Expr = None
    op_s: int = 0

    def children(self):
        return [self.l, self.r]


@dataclass(eq=False)
class Assign(Expr):
    op: str = ""
    l: Expr = None
    r: Expr = None

    def children(self):
        return [self.l, self.r]


@dataclass(eq=False)
class Cond(Expr):
    c: Expr = None
    a: Expr = None
    b: Expr = None

    def children(self):
        return [self.c, self.a, self.b]


@dataclass(eq=False)
class Comma(Expr):
    items: list = field(default_factory=list)

    def children(self):
        return list(self.items)


@dataclass(eq=False)
class Call(Expr):
    f: Expr = None
    args: list = field(default_factory=list)

    def children(self):
        return [self.f] + list(self.args)


@dataclass(eq=False)
class Index(Expr):
    a: Expr = None
    i: Expr = None

    def children(self):
        return [self.a, self.i]


@dataclass(eq=False)
class Member(Expr):
    x: Expr = None
    op: str = "."
    name: str = ""

    def children(self):
        return [self.x]


@dataclass(eq=False)
class InitList(Expr):
    pass


# statements

@dataclass(eq=False)
class Stmt(Node):
    pass


@dataclass(eq=False)
class Declarator(Node):
    name: str = ""
    name_s: int = 0
    init: Expr | None = None
    is_array: bool = False
    is_func: bool = False
    is_pointer: bool = False


@dataclass(eq=False)
class Decl(Stmt):
    spec_s: int = 0
    spec_e: int = 0
    storage: str = ""
    decls: list = field(default_factory=list)

    def children(self):
        return [d.init for d in self.decls if d.init is not None]


@dataclass(eq=False)
class Block(Stmt):
    items: list = field(default_factory=list)

    def children(self):
        return list(self.items)


@dataclass(eq=False)
class ExprStmt(Stmt):
    x: Expr = None

    def children(self):
        return [self.x]


@dataclass(eq=False)
class Empty(Stmt):
    pass


@dataclass(eq=False)
class If(Stmt):
    c: Expr = None
    then: Stmt = None
    els: Stmt | None = None
    else_s: int = 0          # start of the 'else' keyword

    def children(self):
        return [self.c, self.then] + ([self.els] if self.els is not None else [])


@dataclass(eq=False)
class While(Stmt):
    c: Expr = None
    body: Stmt = None

    def children(self):
        return [self.c, self.body]


@dataclass(eq=False)
class DoWhile(Stmt):
    body: Stmt = None
    c: Expr = None

    def children(self):
        return [self.body, self.c]


@dataclass(eq=False)
class For(Stmt):
    init: Expr | None = None
    c: Expr | None = None
    step: Expr | None = None
    body: Stmt = None
    hdr_s: int = 0           # '(' of the header
    hdr_e: int = 0           # after ')'

    def children(self):
        return [x for x in (self.init, self.c, self.step) if x is not None] + [self.body]


@dataclass(eq=False)
class Switch(Stmt):
    c: Expr = None
    body: Stmt = None

    def children(self):
        return [self.c, self.body]


@dataclass(eq=False)
class Case(Stmt):
    x: Expr | None = None      # None = default
    stmt: Stmt | None = None

    def children(self):
        return ([self.x] if self.x is not None else []) + ([self.stmt] if self.stmt is not None else [])


@dataclass(eq=False)
class Label(Stmt):
    name: str = ""
    stmt: Stmt | None = None

    def children(self):
        return [self.stmt] if self.stmt is not None else []


@dataclass(eq=False)
class Return(Stmt):
    x: Expr | None = None

    def children(self):
        return [self.x] if self.x is not None else []


@dataclass(eq=False)
class Jump(Stmt):          # goto / break / continue
    kind: str = ""
    label: str = ""


@dataclass(eq=False)
class Asm(Stmt):
    pass


@dataclass(eq=False)
class Function(Node):
    name: str = ""
    head_s: int = 0            # start of the declaration (after the previous top-level item)
    params_s: int = 0          # '(' of the parameter list
    params_e: int = 0          # after ')'
    params: list = field(default_factory=list)   # [(type_text, name)]
    body: Block = None


def walk(node):
    """Pre-order walk over statements, declarations and expressions."""
    if node is None:
        return
    yield node
    for c in node.children():
        yield from walk(c)


def walk_parents(node, parent=None):
    """Pre-order (node, parent) pairs."""
    if node is None:
        return
    yield node, parent
    for c in node.children():
        yield from walk_parents(c, node)


# ---------------------------------------------------------------- parser

PREC = {"||": 4, "&&": 5, "|": 6, "^": 7, "&": 8, "==": 9, "!=": 9, "<": 10, ">": 10, "<=": 10, ">=": 10,
        "<<": 11, ">>": 11, "+": 12, "-": 12, "*": 13, "/": 13, "%": 13}
ASSIGN_OPS = {"=", "+=", "-=", "*=", "/=", "%=", "&=", "^=", "|=", "<<=", ">>="}
# precedence levels of whole nodes (for parenthesisation of moved text)
P_COMMA, P_ASSIGN, P_COND, P_UNARY, P_POSTFIX, P_PRIMARY = 1, 2, 3, 14, 15, 16


def prec_of(x: Expr) -> int:
    if isinstance(x, Comma):
        return P_COMMA
    if isinstance(x, Assign):
        return P_ASSIGN
    if isinstance(x, Cond):
        return P_COND
    if isinstance(x, Bin):
        return PREC[x.op]
    if isinstance(x, (Unary, Cast, SizeofType)):
        return P_UNARY
    if isinstance(x, (Post, Call, Index, Member)):
        return P_POSTFIX
    return P_PRIMARY


class Parser:
    def __init__(self, src: "Source", toks: list[Tok]):
        self.src = src
        self.t = toks          # significant tokens only
        self.i = 0

    # token helpers
    def peek(self, k=0) -> Tok | None:
        j = self.i + k
        return self.t[j] if j < len(self.t) else None

    def at(self, text: str, k=0) -> bool:
        t = self.peek(k)
        return t is not None and t.text == text and t.kind in ("op", "id")

    def next(self) -> Tok:
        t = self.peek()
        if t is None:
            raise ParseError("unexpected end of input")
        self.i += 1
        return t

    def expect(self, text: str) -> Tok:
        t = self.next()
        if t.text != text:
            raise ParseError(f"expected {text!r}, got {t.text!r} at {t.s}")
        return t

    @property
    def last_e(self) -> int:
        return self.t[self.i - 1].e

    # types
    def is_type_start(self, k=0) -> bool:
        t = self.peek(k)
        if t is None or t.kind != "id":
            return False
        if t.text in TYPE_WORDS or t.text in STORAGE:
            return True
        if t.text in self.src.typedefs:
            n = self.peek(k + 1)
            # a typedef name followed by an operator that cannot follow a type is a variable
            return n is not None and (n.kind == "id" or n.text in ("*", ")", "("))
        return False

    def skip_balanced(self, open_: str, close: str) -> None:
        depth = 0
        while True:
            t = self.next()
            if t.text == open_ and t.kind == "op":
                depth += 1
            elif t.text == close and t.kind == "op":
                depth -= 1
                if depth == 0:
                    return

    def type_name_end(self, k=0) -> int | None:
        """If a type name (as in a cast or sizeof) starts at peek(k) and ends at a ')' return the
        index offset of that ')' else None."""
        j = k
        if not self.is_type_start(j):
            return None
        depth = 0
        while True:
            t = self.peek(j)
            if t is None:
                return None
            if t.text == "(":
                depth += 1
            elif t.text == ")":
                if depth == 0:
                    return j
                depth -= 1
            elif t.text in (";", "{", "}", "=", ",") and depth == 0:
                return None
            elif t.kind in ("num", "str", "chr"):
                if depth == 0:
                    return None
            j += 1

    # expressions
    def expr(self) -> Expr:
        x = self.assign()
        if self.at(","):
            items = [x]
            while self.at(","):
                self.next()
                items.append(self.assign())
            return Comma(s=items[0].s, e=items[-1].e, items=items)
        return x

    def assign(self) -> Expr:
        x = self.cond()
        t = self.peek()
        if t is not None and t.kind == "op" and t.text in ASSIGN_OPS:
            self.next()
            r = self.assign()
            return Assign(s=x.s, e=r.e, op=t.text, l=x, r=r)
        return x

    def cond(self) -> Expr:
        c = self.binary(4)
        if self.at("?"):
            self.next()
            a = self.expr()
            self.expect(":")
            b = self.cond()
            return Cond(s=c.s, e=b.e, c=c, a=a, b=b)
        return c

    def binary(self, minp: int) -> Expr:
        x = self.unary()
        while True:
            t = self.peek()
            if t is None or t.kind != "op" or t.text not in PREC or PREC[t.text] < minp:
                return x
            self.next()
            r = self.binary(PREC[t.text] + 1)
            x = Bin(s=x.s, e=r.e, op=t.text, l=x, r=r, op_s=t.s)

    def unary(self) -> Expr:
        t = self.peek()
        if t is None:
            raise ParseError("unexpected end in expression")
        if t.kind == "op" and t.text in ("-", "+", "!", "~", "*", "&", "++", "--"):
            self.next()
            x = self.unary()
            return Unary(s=t.s, e=x.e, op=t.text, x=x)
        if t.kind == "id" and t.text == "sizeof":
            self.next()
            if self.at("(") and self.type_name_end(1) is not None:
                j = self.type_name_end(1)
                self.i += j + 1
                return SizeofType(s=t.s, e=self.last_e)
            x = self.unary()
            return Unary(s=t.s, e=x.e, op="sizeof", x=x)
        if t.text == "(" and t.kind == "op":
            j = self.type_name_end(1)
            if j is not None:
                ts, te = self.peek(1).s, self.peek(j - 1).e
                self.i += j + 1
                x = self.unary()
                return Cast(s=t.s, e=x.e, type_s=ts, type_e=te, x=x)
        return self.postfix(self.primary())

    def primary(self) -> Expr:
        t = self.next()
        if t.kind == "id":
            if t.text in KEYWORDS and t.text not in ("sizeof",):
                raise ParseError(f"keyword {t.text!r} in expression at {t.s}")
            return Id(s=t.s, e=t.e, name=t.text)
        if t.kind == "num" or t.kind == "chr":
            return Num(s=t.s, e=t.e, text=t.text)
        if t.kind == "str":
            e = t.e
            while self.peek() is not None and self.peek().kind == "str":
                e = self.next().e
            return Str(s=t.s, e=e, text=self.src.text[t.s:e])
        if t.text == "(":
            x = self.expr()
            self.expect(")")
            return Paren(s=t.s, e=self.last_e, x=x)
        raise ParseError(f"unexpected {t.text!r} at {t.s}")

    def postfix(self, x: Expr) -> Expr:
        while True:
            t = self.peek()
            if t is None or t.kind != "op":
                return x
            if t.text == "(":
                self.next()
                args = []
                if not self.at(")"):
                    args.append(self.assign())
                    while self.at(","):
                        self.next()
                        args.append(self.assign())
                self.expect(")")
                x = Call(s=x.s, e=self.last_e, f=x, args=args)
            elif t.text == "[":
                self.next()
                i = self.expr()
                self.expect("]")
                x = Index(s=x.s, e=self.last_e, a=x, i=i)
            elif t.text in (".", "->"):
                self.next()
                n = self.next()
                x = Member(s=x.s, e=n.e, x=x, op=t.text, name=n.text)
            elif t.text in ("++", "--"):
                self.next()
                x = Post(s=x.s, e=t.e, op=t.text, x=x)
            else:
                return x

    # declarations
    def declaration(self) -> Decl:
        start = self.peek().s
        storage = ""
        spec_e = start
        # specifiers: type words, qualifiers, storage, struct/union/enum tags (+ bodies), typedef names
        seen_type = False
        while True:
            t = self.peek()
            if t is None:
                raise ParseError("eof in declaration")
            if t.kind == "id" and t.text in STORAGE:
                storage = t.text
                self.next()
            elif t.kind == "id" and t.text in ("struct", "union", "enum"):
                self.next()
                if self.peek().kind == "id":
                    self.next()
                if self.at("{"):
                    self.skip_balanced("{", "}")
                seen_type = True
            elif t.kind == "id" and t.text in ("_based", "__based"):
                self.next()
                self.skip_balanced("(", ")")
            elif t.kind == "id" and (t.text in TYPE_WORDS) and t.text not in QUALIFIERS - {"const", "volatile"}:
                self.next()
                seen_type = True
            elif t.kind == "id" and t.text in ("const", "volatile"):
                self.next()
            elif t.kind == "id" and t.text in self.src.typedefs and not seen_type:
                self.next()
                seen_type = True
            else:
                break
            spec_e = self.last_e
        d = Decl(s=start, spec_s=start, spec_e=spec_e, storage=storage)
        if self.at(";"):
            self.next()
            d.e = self.last_e
            return d
        while True:
            d.decls.append(self.declarator())
            if self.at(","):
                self.next()
                continue
            self.expect(";")
            break
        d.e = self.last_e
        return d

    def declarator(self) -> Declarator:
        s = self.peek().s
        dd = Declarator(s=s)
        depth = 0
        while True:
            t = self.peek()
            if t is None:
                raise ParseError("eof in declarator")
            if t.kind == "id" and t.text in QUALIFIERS:
                self.next()
                if t.text in ("_based", "__based"):
                    self.skip_balanced("(", ")")
            elif t.text == "*":
                dd.is_pointer = True
                self.next()
            elif t.text == "(":
                depth += 1
                self.next()
            elif t.kind == "id" and not dd.name:
                dd.name, dd.name_s = t.text, t.s
                self.next()
            elif t.text == "[":
                dd.is_array = True
                self.skip_balanced("[", "]")
            elif t.text == ")" and depth > 0:
                depth -= 1
                self.next()
                if self.at("("):
                    dd.is_func = True
                    self.skip_balanced("(", ")")
            elif t.text == "(" and dd.name:
                dd.is_func = True
                self.skip_balanced("(", ")")
            else:
                break
            if dd.name and self.at("(") and depth == 0:
                dd.is_func = True
                self.skip_balanced("(", ")")
        dd.e = self.last_e
        if self.at("="):
            self.next()
            if self.at("{"):
                b = self.peek().s
                self.skip_balanced("{", "}")
                dd.init = InitList(s=b, e=self.last_e)
            else:
                dd.init = self.assign()
            dd.e = self.last_e
        return dd

    # statements
    def block(self) -> Block:
        b = self.expect("{")
        items = []
        while not self.at("}"):
            items.append(self.statement())
        self.next()
        return Block(s=b.s, e=self.last_e, items=items)

    def statement(self) -> Stmt:
        t = self.peek()
        if t is None:
            raise ParseError("eof in statement")
        if t.kind == "asm":
            self.next()
            return Asm(s=t.s, e=t.e)
        if t.text == "{" and t.kind == "op":
            return self.block()
        if t.text == ";" and t.kind == "op":
            self.next()
            return Empty(s=t.s, e=t.e)
        if t.kind == "id":
            w = t.text
            if w == "if":
                self.next()
                self.expect("(")
                c = self.expr()
                self.expect(")")
                th = self.statement()
                st = If(s=t.s, c=c, then=th)
                if self.at("else"):
                    st.else_s = self.next().s
                    st.els = self.statement()
                st.e = self.last_e
                return st
            if w == "while":
                self.next()
                self.expect("(")
                c = self.expr()
                self.expect(")")
                body = self.statement()
                return While(s=t.s, e=self.last_e, c=c, body=body)
            if w == "do":
                self.next()
                body = self.statement()
                self.expect("while")
                self.expect("(")
                c = self.expr()
                self.expect(")")
                self.expect(";")
                return DoWhile(s=t.s, e=self.last_e, body=body, c=c)
            if w == "for":
                self.next()
                h = self.expect("(")
                init = None if self.at(";") else self.expr()
                self.expect(";")
                c = None if self.at(";") else self.expr()
                self.expect(";")
                step = None if self.at(")") else self.expr()
                self.expect(")")
                he = self.last_e
                body = self.statement()
                return For(s=t.s, e=self.last_e, init=init, c=c, step=step, body=body, hdr_s=h.s, hdr_e=he)
            if w == "switch":
                self.next()
                self.expect("(")
                c = self.expr()
                self.expect(")")
                body = self.statement()
                return Switch(s=t.s, e=self.last_e, c=c, body=body)
            if w in ("case", "default"):
                self.next()
                x = None
                if w == "case":
                    x = self.cond()
                self.expect(":")
                st = None if self.at("}") else self.statement()
                return Case(s=t.s, e=self.last_e, x=x, stmt=st)
            if w == "return":
                self.next()
                x = None if self.at(";") else self.expr()
                self.expect(";")
                return Return(s=t.s, e=self.last_e, x=x)
            if w in ("break", "continue"):
                self.next()
                self.expect(";")
                return Jump(s=t.s, e=self.last_e, kind=w)
            if w == "goto":
                self.next()
                lab = self.next().text
                self.expect(";")
                return Jump(s=t.s, e=self.last_e, kind="goto", label=lab)
            if w not in KEYWORDS and self.at(":", 1) and not self.at("::", 1):
                self.next()
                self.next()
                st = None if self.at("}") else self.statement()
                return Label(s=t.s, e=self.last_e, name=w, stmt=st)
            if self.is_type_start():
                return self.declaration()
        x = self.expr()
        self.expect(";")
        return ExprStmt(s=x.s, e=self.last_e, x=x)


class Source:
    """A whole C file: tokens, typedef names, top-level function definitions."""

    def __init__(self, text: str):
        self.text = text
        self.toks = tokenize(text)
        self.sig = [t for t in self.toks if t.kind not in ("ws", "nl", "cmt", "pp")]
        self.typedefs = self._typedefs()
        self._funcs = None

    def _typedefs(self) -> set:
        names = set()
        sig = self.sig
        i = 0
        while i < len(sig):
            if sig[i].kind == "id" and sig[i].text == "typedef":
                depth_b = depth_p = 0
                j = i + 1
                after_paren_group = False
                while j < len(sig) and not (sig[j].text == ";" and depth_b == 0 and depth_p == 0):
                    t = sig[j]
                    if t.text == "{":
                        depth_b += 1
                    elif t.text == "}":
                        depth_b -= 1
                    elif t.text == "(":
                        if depth_p == 0 and after_paren_group:
                            # parameter list of a function (pointer) typedef: skip
                            d = 0
                            while j < len(sig):
                                if sig[j].text == "(":
                                    d += 1
                                elif sig[j].text == ")":
                                    d -= 1
                                    if d == 0:
                                        break
                                j += 1
                            j += 1
                            continue
                        depth_p += 1
                    elif t.text == ")":
                        depth_p -= 1
                        if depth_p == 0:
                            after_paren_group = True
                    elif (t.kind == "id" and depth_b == 0 and t.text not in KEYWORDS and t.text not in QUALIFIERS
                          and j + 1 < len(sig) and sig[j + 1].text in (";", ",", "[", ")")):
                        names.add(t.text)
                        if sig[j + 1].text == "(" or depth_p == 0:
                            after_paren_group = True
                    j += 1
                i = j
            i += 1
        return names

    def functions(self, only: str | None = None) -> list[Function]:
        """Top-level function definitions (name, spans, parsed body).  With ``only``, just that
        function's body is parsed (the others are skipped by brace matching)."""
        if self._funcs is not None and only is None:
            return self._funcs
        sig = self.sig
        out = []
        depth = 0
        prev_end = 0         # end of the previous top-level item (char offset)
        i = 0
        while i < len(sig):
            t = sig[i]
            if t.text == "{" and t.kind == "op" and depth == 0:
                # function definition iff the previous token is ')' of a parameter list
                fn_body = i > 0 and sig[i - 1].text == ")"
                if i > 0 and sig[i - 1].text == ")":
                    j, d = i - 1, 0
                    while j >= 0:
                        if sig[j].text == ")":
                            d += 1
                        elif sig[j].text == "(":
                            d -= 1
                            if d == 0:
                                break
                        j -= 1
                    name_tok = sig[j - 1] if j > 0 else None
                    # old-style '(far *f(...))' not supported; name must be an identifier
                    if name_tok is not None and name_tok.kind == "id" and only in (None, name_tok.text):
                        p = Parser(self, sig)
                        p.i = i
                        body = p.block()
                        fn = Function(s=self._head_start(prev_end, name_tok.s), e=body.e, name=name_tok.text,
                                      head_s=self._head_start(prev_end, name_tok.s), params_s=sig[j].s,
                                      params_e=sig[i - 1].e, params=self._params(j, i - 1), body=body)
                        out.append(fn)
                        i = p.i
                        prev_end = body.e
                        continue
                # struct/initialiser body at top level
                d = 0
                while i < len(sig):
                    if sig[i].text == "{":
                        d += 1
                    elif sig[i].text == "}":
                        d -= 1
                        if d == 0:
                            break
                    i += 1
                if fn_body and i < len(sig):
                    prev_end = sig[i].e
            elif t.text == ";" and t.kind == "op":
                prev_end = t.e
            i += 1
        if only is None:
            self._funcs = out
        return out

    def _head_start(self, prev_end: int, name_s: int) -> int:
        """Start of the definition's first token after prev_end (skipping trivia and pp lines)."""
        for t in self.toks:
            if t.s >= prev_end and t.kind not in ("ws", "nl", "cmt", "pp") and t.s <= name_s:
                return t.s
        return name_s

    def _params(self, lp: int, rp: int) -> list:
        """[(type_text, name)] of a prototype-style parameter list sig[lp]..sig[rp]."""
        sig = self.sig
        out, cur = [], []
        d = 0
        for t in sig[lp + 1:rp]:
            if t.text == "(":
                d += 1
            elif t.text == ")":
                d -= 1
            if t.text == "," and d == 0:
                out.append(cur)
                cur = []
            else:
                cur.append(t)
        if cur:
            out.append(cur)
        res = []
        for toks in out:
            if len(toks) == 1 and toks[0].text in ("void", "..."):
                continue
            ids = [t for t in toks if t.kind == "id" and t.text not in TYPE_WORDS and t.text not in STORAGE]
            name = ids[-1].text if ids and not (len(ids) == 1 and ids[0].text in self.typedefs) else ""
            ttext = self.text[toks[0].s:toks[-1].e]
            if name:
                k = ttext.rfind(name)
                ttext = (ttext[:k] + ttext[k + len(name):]).strip()
            res.append((ttext, name))
        return res

    def function(self, name: str) -> Function:
        for f in (self._funcs if self._funcs is not None else self.functions(only=name)):
            if f.name == name:
                return f
        raise KeyError(f"no definition of {name}")

    def span(self, node: Node) -> str:
        return self.text[node.s:node.e]


def parse_function(text: str, name: str) -> tuple[Source, Function]:
    src = Source(text)
    return src, src.function(name)


# ---------------------------------------------------------------- analysis helpers


def idents(x) -> list[str]:
    return [n.name for n in walk(x) if isinstance(n, Id)]


def has_side_effects(x) -> bool:
    for n in walk(x):
        if isinstance(n, (Assign, Call, Post)) or (isinstance(n, Unary) and n.op in ("++", "--")):
            return True
    return False


def writes(x) -> set[str]:
    """Identifiers assigned (=, op=, ++, --) inside x (plain Id lvalues only)."""
    out = set()
    for n in walk(x):
        if isinstance(n, Assign) and isinstance(strip_paren(n.l), Id):
            out.add(strip_paren(n.l).name)
        elif isinstance(n, (Post,)) and isinstance(strip_paren(n.x), Id):
            out.add(strip_paren(n.x).name)
        elif isinstance(n, Unary) and n.op in ("++", "--") and isinstance(strip_paren(n.x), Id):
            out.add(strip_paren(n.x).name)
    return out


def address_taken(x) -> set[str]:
    return {strip_paren(n.x).name for n in walk(x)
            if isinstance(n, Unary) and n.op == "&" and isinstance(strip_paren(n.x), Id)}


def strip_paren(x):
    while isinstance(x, Paren):
        x = x.x
    return x


def stmt_lists(node):
    """Every statement list (Block.items) in a function body, outermost first."""
    for n in walk(node):
        if isinstance(n, Block):
            yield n


def ends_in_jump(st) -> bool:
    """True if control never falls through the end of statement st."""
    if isinstance(st, (Return, Jump)):
        return True
    if isinstance(st, Block):
        return bool(st.items) and ends_in_jump(st.items[-1])
    if isinstance(st, If):
        return st.els is not None and ends_in_jump(st.then) and ends_in_jump(st.els)
    return False


def contains_jump_kind(st, kinds=("break", "continue")) -> bool:
    """break/continue that would bind to an enclosing loop (not nested loops/switches)."""
    def rec(n, in_loop, in_switch):
        if isinstance(n, Jump) and n.kind in kinds:
            if n.kind == "continue" and not in_loop:
                return True
            if n.kind == "break" and not in_loop and not in_switch:
                return True
        for c in n.children():
            if isinstance(c, Stmt) or isinstance(c, Block):
                if rec(c, in_loop or isinstance(n, (While, DoWhile, For)),
                       in_switch or isinstance(n, Switch)):
                    return True
        return False
    return rec(st, False, False)


def line_indent(text: str, pos: int) -> str:
    """The leading whitespace of the line containing pos."""
    b = text.rfind("\n", 0, pos) + 1
    m = re.match(r"[ \t]*", text[b:])
    return m.group()
