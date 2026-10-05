"""Source-span helpers; no source selection or generator dependency."""
import re
from . import tokenizer as csrc


def rename(text, mapping):
    edits = [(t.s, t.e, mapping[t.text]) for t in csrc.tokenize(text)
             if t.kind == 'id' and t.text in mapping]
    for lo, hi, new in reversed(edits):
        text = text[:lo] + new + text[hi:]
    return text


def _identifier_rewrite(text, mapping):
    return rename(text, mapping)


def replace_identifier_tokens(text, mapping):
    counts = {n: sum(t.kind == 'id' and t.text == n for t in csrc.tokenize(text))
              for n in mapping}
    return rename(text, mapping), counts


def masked(source):
    output = list(source)
    for t in csrc.tokenize(source):
        if t.kind in {'cmt', 'str', 'chr', 'pp', 'asm'}:
            output[t.s:t.e] = ['\n' if x == '\n' else ' ' for x in t.text]
    return ''.join(output)


def function_heads(source):
    """Top-level definitions with exact spans and K&R declaration support.

    Initializer braces and function-pointer prototypes are excluded. This is a
    lexical structural check, not a body picker; it reads only the given text.
    """
    code = masked(source)
    result = []
    current_function = None
    knr_function = None
    depth = 0
    start = 0
    for i, ch in enumerate(code):
        if ch == '{' and depth == 0:
            head = code[start:i].strip()
            found = re.search(r'\b([A-Za-z_]\w*)\s*\([^;{}]*\)\s*$', head, re.S)
            if knr_function is not None:
                found = knr_function
            if found and not re.search(r'\btypedef\b|=', head):
                leading = start + len(code[start:i]) - len(code[start:i].lstrip())
                current_function = {'name': found.group(1),
                                    'signature': source[leading:i].strip(),
                                    'line': source.count('\n', 0, leading) + 1,
                                    'start': leading}
                result.append(current_function)
                knr_function = None
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth < 0:
                raise ValueError('unbalanced top-level braces')
            if depth == 0:
                if current_function is not None:
                    current_function['end'] = i + 1
                    current_function = None
                start = i + 1
        elif ch == ';' and depth == 0:
            head = code[start:i].strip()
            candidate = re.search(r'\b([A-Za-z_]\w*)\s*\(([A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*)\)\s*\n\s*([^{}]+)$', head)
            if candidate and candidate.group(2) != 'void' and '=' not in head and not re.search(r'\btypedef\b', head):
                knr_function = candidate
            elif knr_function is None:
                start = i + 1
    if depth:
        raise ValueError('unbalanced source braces')
    return result
