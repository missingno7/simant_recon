"""Bounded source-span lowering of closed DOS unsigned-word expression islands.

This is not a C frontend. Types come only from explicit scalar casts, literal
types in the MSC16 model, parentheses, and supported operators. Unknown nodes
remain unknown. No identifier spelling, module, function, or source byte pin
selects an edit. Call/field/index expressions are opaque below an explicit cast.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import re

from . import tokenizer

TRIVIA = {"ws", "nl", "cmt"}
CAST_WORDS = {"unsigned", "signed", "char", "short", "int", "long",
              "uint16_t", "int16_t", "uint32_t", "int32_t"}
PRECEDENCE = {",": 1, "=": 2, "+=": 2, "-=": 2, "*=": 2, "/=": 2,
              "%=": 2, "<<=": 2, ">>=": 2, "&=": 2, "|=": 2, "^=": 2,
              "?": 3, "||": 4, "&&": 5, "|": 6, "^": 7, "&": 8,
              "==": 9, "!=": 9, "<": 10, "<=": 10, ">": 10, ">=": 10,
              "<<": 11, ">>": 11, "+": 12, "-": 12,
              "*": 13, "/": 13, "%": 13}
COMPARISONS = {"==", "!=", "<", "<=", ">", ">="}


class Unsupported(ValueError):
    pass


@dataclass
class Node:
    start: int
    end: int
    type: str | None = None
    children: list["Node"] = field(default_factory=list)
    operator: str | None = None
    action: str | None = None
    constant: int | None = None


def cast_type(words):
    if words in (["uint16_t"], ["unsigned"], ["unsigned", "int"],
                 ["unsigned", "short"], ["unsigned", "short", "int"]):
        return "u16"
    if words in (["int16_t"], ["int"], ["signed"], ["signed", "int"],
                 ["short"], ["short", "int"], ["signed", "short"],
                 ["signed", "short", "int"]):
        return "s16"
    # These casts are parsed so a 32-bit peer prevents an unsigned-word edit.
    if words in (["uint32_t"], ["unsigned", "long"], ["unsigned", "long", "int"]):
        return "u32"
    if words in (["int32_t"], ["long"], ["long", "int"],
                 ["signed", "long"], ["signed", "long", "int"]):
        return "s32"
    return None


def literal_type(text):
    m = re.fullmatch(r"(0[xX][0-9a-fA-F]+|[0-9]+)([uUlL]*)", text)
    if not m:
        return None, None
    number, suffix = m.groups()
    suffix = suffix.lower()
    if suffix not in {"", "u", "l", "ul", "lu"}:
        return None, None
    try:
        base = 16 if number.lower().startswith("0x") else 8 if len(number) > 1 and number[0] == "0" else 10
        value = int(number, base)
    except ValueError:
        return None, None
    if value > 0xffffffff:
        return None, None
    if "l" in suffix:
        return ("u32" if "u" in suffix or value > 0x7fffffff else "s32"), value
    if "u" in suffix:
        return ("u16" if value <= 0xffff else "u32"), value
    if value <= 0x7fff:
        return "s16", value
    if base != 10 and value <= 0xffff:
        return "u16", value
    return ("s32" if value <= 0x7fffffff else "u32"), value


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens

    def token(self, index):
        if index >= len(self.tokens):
            raise Unsupported("incomplete expression")
        return self.tokens[index]

    def prefix(self, index):
        t = self.token(index)
        if t.text == "(":
            j = index + 1
            words = []
            while j < len(self.tokens) and self.tokens[j].text in CAST_WORDS:
                words.append(self.tokens[j].text)
                j += 1
            if words and self.token(j).text == ")":
                child, end = self.prefix(j + 1)
                node = Node(t.s, child.end, cast_type(words), [child])
                return node, end
            child, j = self.expression(index + 1)
            close = self.token(j)
            if close.text != ")":
                raise Unsupported("unclosed parentheses")
            node = Node(t.s, close.e, child.type, [child], constant=child.constant)
            return self.postfix(node, j + 1)
        if t.text in {"+", "-", "~", "!", "*", "&", "++", "--", "sizeof"}:
            child, j = self.prefix(index + 1)
            # Unary +/- on known small constants are safe; other unary nodes
            # are deliberately unknown, even if their child has a known type.
            typ, value = None, None
            if t.text in {"+", "-"} and child.constant is not None and child.type == "s16":
                value = child.constant if t.text == "+" else -child.constant
                if -32768 <= value <= 32767:
                    typ = "s16"
            return Node(t.s, child.end, typ, [child], constant=value), j
        if t.kind == "num":
            typ, value = literal_type(t.text)
            return self.postfix(Node(t.s, t.e, typ, constant=value), index + 1)
        if t.kind in {"id", "str", "chr"}:
            return self.postfix(Node(t.s, t.e), index + 1)
        raise Unsupported("unsupported expression prefix")

    def postfix(self, node, index):
        while index < len(self.tokens):
            t = self.tokens[index]
            if t.text in {".", "->"}:
                member = self.token(index + 1)
                if member.kind != "id":
                    raise Unsupported("unsupported member")
                node = Node(node.start, member.e, children=[node])
                index += 2
            elif t.text in {"++", "--"}:
                node = Node(node.start, t.e, children=[node])
                index += 1
            elif t.text in {"(", "["}:
                close = ")" if t.text == "(" else "]"
                j = index + 1
                children = [node]
                if self.token(j).text != close:
                    child, j = self.expression(j)
                    children.append(child)
                if self.token(j).text != close:
                    raise Unsupported("unclosed postfix expression")
                node = Node(node.start, self.tokens[j].e, children=children)
                index = j + 1
            else:
                break
        return node, index

    def expression(self, index, minimum=1):
        left, index = self.prefix(index)
        while index < len(self.tokens):
            op = self.tokens[index].text
            prec = PRECEDENCE.get(op, 0)
            if prec < minimum:
                break
            if op == "?":
                yes, middle = self.expression(index + 1)
                if self.token(middle).text != ":":
                    raise Unsupported("incomplete conditional")
                no, index = self.expression(middle + 1, prec)
                left = Node(left.start, no.end, children=[left, yes, no], operator=op)
                continue
            right, index = self.expression(index + 1, prec if prec == 2 else prec + 1)
            typ, action = None, None
            if left.type in {"s16", "u16"} and right.type in {"s16", "u16"}:
                if op in {"+", "-"} and "u16" in {left.type, right.type}:
                    typ, action = "u16", "word-additive-result"
                elif op in COMPARISONS:
                    typ = "s16"
                    if {left.type, right.type} == {"s16", "u16"}:
                        signed = left if left.type == "s16" else right
                        # Native and DOS comparisons already agree against a
                        # known nonnegative small literal; avoid redundant
                        # edits to original folded range/lifetime controls.
                        if signed.constant is None or signed.constant < 0:
                            action = "word-comparison-operands"
            left = Node(left.start, right.end, typ, [left, right], op, action)
        return left, index


def convert(source):
    """Return edited whole source and per-operator spans/types; never body-pick.

    Preprocessor and ASM tokens separate runs. Successful parses may contain
    unknown nodes; only individually proven supported operator nodes are edited.
    An unsupported parse contributes no edits. A containing unknown node never
    acquires a type merely because its children are typed.
    """
    tokens = [t for t in tokenizer.tokenize(source) if t.kind not in TRIVIA]
    actions = {}
    # Only structural expression boundaries may start a parse. Starting at every
    # literal would misread the RHS in "(unsigned)x + 2 <= (unsigned)y" as
    # the independent comparison "2 <= (unsigned)y". The complete root owns
    # its children, including nested islands under unsupported operators.
    for start, token in enumerate(tokens):
        previous = tokens[start - 1].text if start else None
        if previous not in {None, "{", "}", ";", "(", "[", ",", "=",
                            "+=", "-=", "*=", "/=", "%=", "<<=", ">>=",
                            "&=", "|=", "^=", "?", ":", "&&", "||", "return", "case"}:
            continue
        if token.kind not in {"id", "num", "str", "chr"} and token.text not in {"(", "+", "-", "~", "!", "*", "&", "++", "--"}:
            continue
        parser = Parser(tokens)
        try:
            root, _ = parser.expression(start)
        except Unsupported:
            continue
        pending = [root]
        while pending:
            node = pending.pop()
            pending.extend(node.children)
            if node.action:
                key = (node.start, node.end)
                old = actions.get(key)
                if old is not None and (old.action, old.type, old.operator) != (node.action, node.type, node.operator):
                    raise Unsupported("ambiguous typed span")
                actions[key] = node
    # Every interval is a proper expression subtree; crossing intervals signal
    # a parser ambiguity and cause the complete conversion to fail closed.
    spans = sorted(actions)
    for i, (lo, hi) in enumerate(spans):
        for next_lo, next_hi in spans[i + 1:]:
            if next_lo >= hi:
                break
            if next_lo > lo and next_hi > hi:
                raise Unsupported(f"crossing expression intervals: {source[lo:hi]!r} / {source[next_lo:next_hi]!r}")

    def render(node):
        text = source[node.start:node.end]
        for child in reversed(node.children):
            replacement = render(child)
            text = text[:child.start - node.start] + replacement + text[child.end - node.start:]
        action = actions.get((node.start, node.end))
        if action and action.action == "word-additive-result":
            return "((uint16_t)(" + text + "))"
        if action and action.action == "word-comparison-operands":
            left, right = node.children
            middle = source[left.end:right.start]
            return "((uint16_t)(" + render(left) + ")" + middle + "(uint16_t)(" + render(right) + "))"
        return text

    roots = [node for span, node in actions.items()
             if not any(other[0] <= span[0] and span[1] <= other[1] and span != other for other in actions)]
    output = source
    for node in sorted(roots, key=lambda n: n.start, reverse=True):
        output = output[:node.start] + render(node) + output[node.end:]
    receipt = {"schema": "dos-word-expression-islands-v1",
               "input_sha256": hashlib.sha256(source.encode("latin1")).hexdigest(),
               "output_sha256": hashlib.sha256(output.encode("latin1")).hexdigest(),
               "operators": [{"start": node.start, "end": node.end,
                              "line": source.count("\n", 0, node.start) + 1,
                              "source": source[node.start:node.end],
                              "operator": node.operator,
                              "operand_types": [c.type for c in node.children],
                              "result_type": node.type, "action": node.action}
                             for node in sorted(actions.values(), key=lambda n: (n.start, n.end))]}
    return output, receipt
