import re
from . import tokenizer as csrc
TRIVIA = {'ws', 'nl', 'cmt'}
TYPE_WORDS = {'unsigned', 'signed', 'char', 'short', 'int', 'long'}
REMOVE = {'far', 'near', '_far', '_near', '_fastcall', 'pascal', 'register', '_loadds'}

def scalar_type(words):
    if words == ['char']:
        return 'char'
    unsigned = 'unsigned' in words
    if 'char' in words:
        return 'uint8_t' if unsigned else 'int8_t'
    width = 32 if 'long' in words else 16
    return ('uint' if unsigned else 'int') + str(width) + '_t'

def convert(text):
    lexical = re.sub('\\\\\\r?\\n', lambda m: ' ' * len(m[0]), text)
    ts = csrc.tokenize(lexical)
    edits = []
    i = 0
    while i < len(ts):
        t = ts[i]
        if t.kind == 'id' and t.text in TYPE_WORDS:
            j = i
            words = []
            end = t.e
            while j < len(ts):
                q = ts[j]
                if q.kind in TRIVIA:
                    j += 1
                    continue
                if q.kind == 'id' and q.text in TYPE_WORDS:
                    words.append(q.text)
                    end = q.e
                    j += 1
                    continue
                break
            edits.append((t.s, end, scalar_type(words)))
            i = j
            continue
        if t.kind == 'id' and t.text in REMOVE:
            edits.append((t.s, t.e, ''))
        if t.kind == 'id' and t.text == 'main':
            edits.append((t.s, t.e, 'dos_game_main'))
        if t.kind == 'pp' and re.match('\\s*#\\s*define\\b', t.text):
            match = re.match('(\\s*#\\s*define\\s+)(.*)', t.text, re.S)
            edits.append((t.s, t.e, match[1] + convert(match[2])))
        i += 1
    for (lo, hi, new) in reversed(edits):
        text = text[:lo] + new + text[hi:]
    text = re.sub('(?m)^(\\s*#pragma\\s+pack)\\s*\\(\\s*\\)', '\\1(2)', text)
    return text
