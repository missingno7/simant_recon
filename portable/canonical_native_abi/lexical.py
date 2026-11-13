"""Source-span helpers; no source selection or generator dependency."""
import re
from pathlib import Path
from . import tokenizer as csrc


def rename(text, mapping):
    edits = [(t.s, t.e, mapping[t.text]) for t in csrc.tokenize(text)
             if t.kind == 'id' and t.text in mapping]
    for lo, hi, new in reversed(edits):
        text = text[:lo] + new + text[hi:]
    return text






def mask_literals(source: str) -> str:
    """Return same-length text with comments and C literals blanked."""
    pattern = re.compile('//[^\\r\\n]*|/\\*.*?\\*/|\\"(?:\\\\.|[^\\"\\\\])*\\"|\'(?:\\\\.|[^\'\\\\])*\'', re.S)
    return pattern.sub(lambda m: ''.join(('\n' if c == '\n' else ' ' for c in m.group())), source)


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


ROOT = Path(__file__).resolve().parents[2]


def expand_shared_headers(text, seen=None):
    """Expose canonical include/ records and constants before native ABI views.

    The existing record adapters need complete declarations to replace DOS
    pointer slots; included definitions therefore pass through scalar lowering
    with their consumers. GCC still expands remaining macros in the expression
    frontend. The builder pins every input header in its identity receipt.
    """
    seen = set() if seen is None else seen
    def include(match):
        name = match[1]
        header = ROOT / 'include' / name
        if not header.is_file():
            return match[0]
        if name in seen:
            return ''
        seen.add(name)
        body = header.read_text(encoding='latin1')
        # Comments between members did not exist in the old local declarations.
        body = re.sub(r'/\*.*?\*/', '', body, flags=re.S)
        return expand_shared_headers(body, seen)
    text = re.sub(r'^\s*#include\s+"([^"\n]+)"\s*$', include, text, flags=re.M)
    constants = dict(re.findall(r'^#define[ \t]+(\w+)[ \t]+([^\r\n]+)', text, re.M))
    # Named object constants now occur inside exact hardware/ABI anchors.
    # Token replacement protects comments/literals and leaves #define directives
    # for GCC. All current *_ids.h macros are object-like numeric constants.
    return rename(text, constants)
