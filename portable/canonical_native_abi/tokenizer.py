from __future__ import annotations
import re
from dataclasses import dataclass, field
ASM_WORDS = {'_asm', '__asm'}
OPS = sorted('>>= <<= ... -> ++ -- << >> <= >= == != && || += -= *= /= %= &= ^= |=\n    + - * / % & | ^ ! ~ < > = ? : ; , . ( ) [ ] { }'.split(), key=len, reverse=True)
_OP_RE = '|'.join((re.escape(o) for o in OPS))
TOKEN_RE = re.compile('\n    (?P<nl>\\n)\n  | (?P<ws>[ \\t\\r\\f\\v]+)\n  | (?P<cmt>/\\*.*?\\*/|//[^\\n]*)\n  | (?P<id>[A-Za-z_$][A-Za-z0-9_$]*)\n  | (?P<num>(?:0[xX][0-9A-Fa-f]+|\\d+\\.\\d*(?:[eE][+-]?\\d+)?|\\.\\d+(?:[eE][+-]?\\d+)?|\\d+(?:[eE][+-]?\\d+)?)[uUlLfF]*)\n  | (?P<str>"(?:[^"\\\\\\n]|\\\\.)*")\n  | (?P<chr>\'(?:[^\'\\\\\\n]|\\\\.)*\')\n  | (?P<op>' + _OP_RE + ')\n  | (?P<bad>.)\n', re.S | re.X)

@dataclass
class Tok:
    kind: str
    text: str
    s: int
    e: int

    def __repr__(self):
        return f'{self.kind}:{self.text!r}'

class ParseError(Exception):
    pass

def tokenize(text: str) -> list[Tok]:
    """All tokens including trivia.  Preprocessor lines and _asm blocks/lines are single tokens."""
    out: list[Tok] = []
    (i, n) = (0, len(text))
    line_start = True
    while i < n:
        if line_start:
            m = re.compile('[ \\t]*#').match(text, i)
            if m:
                j = i
                while True:
                    k = text.find('\n', j)
                    if k < 0:
                        k = n
                        break
                    if text[k - 1] == '\\' or (text[k - 1] == '\r' and text[k - 2] == '\\'):
                        j = k + 1
                        continue
                    break
                out.append(Tok('pp', text[i:k], i, k))
                i = k
                line_start = False
                continue
        m = TOKEN_RE.match(text, i)
        kind = m.lastgroup
        t = m.group()
        if kind == 'id' and t in ASM_WORDS:
            j = i + len(t)
            while j < n and text[j] in ' \t':
                j += 1
            if j < n and text[j] == '{':
                (depth, k) = (0, j)
                while k < n:
                    if text[k] == '{':
                        depth += 1
                    elif text[k] == '}':
                        depth -= 1
                        if depth == 0:
                            break
                    k += 1
                if k >= n:
                    raise ParseError('unterminated _asm block')
                out.append(Tok('asm', text[i:k + 1], i, k + 1))
                i = k + 1
            else:
                k = text.find('\n', j)
                k = n if k < 0 else k
                m2 = re.compile('\\b_?_asm\\b').search(text, j, k)
                if m2:
                    k = m2.start()
                out.append(Tok('asm', text[i:k].rstrip(), i, i + len(text[i:k].rstrip())))
                i = i + len(text[i:k].rstrip())
            line_start = False
            continue
        if kind == 'bad':
            raise ParseError(f'unexpected character {t!r} at {i}')
        out.append(Tok(kind, t, i, i + len(t)))
        i += len(t)
        if kind == 'nl':
            line_start = True
        elif kind not in ('ws', 'cmt'):
            line_start = False
        elif kind == 'cmt' and '\n' in t:
            line_start = False
    return out
