"""Small C-identifier adapter used only by the 50F6 migration test lane.

This deliberately runs before target-word expression conversion. It rewrites
identifier tokens in temporary generated-consumer copies, never canonical or
historical files.
"""
from __future__ import annotations

import re


def replace_identifier_tokens(source: str, replacements: dict[str, str]) -> tuple[str, dict[str, int]]:
    counts = {name: 0 for name in replacements}
    out: list[str] = []
    i = 0
    state = "code"
    while i < len(source):
        ch = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""
        if state == "code":
            if ch == "/" and nxt == "/":
                out.extend((ch, nxt)); i += 2; state = "line_comment"; continue
            if ch == "/" and nxt == "*":
                out.extend((ch, nxt)); i += 2; state = "block_comment"; continue
            if ch in ('"', "'"):
                out.append(ch); i += 1; state = "string" if ch == '"' else "char"; continue
            if ch == "_" or ch.isalpha():
                j = i + 1
                while j < len(source) and (source[j] == "_" or source[j].isalnum()):
                    j += 1
                token = source[i:j]
                if token in replacements:
                    out.append(replacements[token]); counts[token] += 1
                else:
                    out.append(token)
                i = j
                continue
            out.append(ch); i += 1; continue
        if state == "line_comment":
            out.append(ch); i += 1
            if ch == "\n": state = "code"
            continue
        if state == "block_comment":
            if ch == "*" and nxt == "/":
                out.extend((ch, nxt)); i += 2; state = "code"; continue
            out.append(ch); i += 1; continue
        if state in ("string", "char"):
            quote = '"' if state == "string" else "'"
            if ch == "\\" and i + 1 < len(source):
                out.extend(source[i:i + 2]); i += 2; continue
            out.append(ch); i += 1
            if ch == quote: state = "code"
            continue
    if state in ("block_comment", "string", "char"):
        raise ValueError(f"unterminated C lexical state: {state}")
    return "".join(out), counts


def remove_target_externs(source: str, names: set[str]) -> tuple[str, dict[str, int]]:
    counts = {name: 0 for name in names}
    output: list[str] = []
    for line in source.splitlines(keepends=True):
        stripped = line.lstrip()
        if stripped.startswith("extern "):
            for name in names:
                if re.search(r"\b" + re.escape(name) + r"\b", line) and ";" in line:
                    counts[name] += 1
                    break
            else:
                output.append(line)
        else:
            output.append(line)
    return "".join(output), counts


def adapt_generated_consumer(source: str, replacements: dict[str, str]) -> tuple[str, dict[str, object]]:
    text, removed = remove_target_externs(source, set(replacements))
    text, rewritten = replace_identifier_tokens(text, replacements)
    return text, {"removed_extern_declarations": removed,
                  "rewritten_identifier_tokens": rewritten}


def self_test() -> None:
    sample = ('extern int far fd_50F6_0508;\n'
              '/* fd_50F6_0508 is a comment. */\n'
              'const char *s = "fd_50F6_0508";\n'
              'int16_t a = fd_50F6_0508.x; int16_t b = fd_50F6_05080;\n')
    stripped, removed = remove_target_externs(sample, {"fd_50F6_0508"})
    converted, rewritten = replace_identifier_tokens(
        stripped, {"fd_50F6_0508": "native_state_fd_50F6_0508.xy"})
    if removed["fd_50F6_0508"] != 1 or rewritten["fd_50F6_0508"] != 1:
        raise AssertionError("pre-word positive-control count mismatch")
    if ("/* fd_50F6_0508 is a comment. */" not in converted or
            '"fd_50F6_0508"' not in converted or "fd_50F6_05080" not in converted):
        raise AssertionError("pre-word negative lexical controls changed")


if __name__ == "__main__":
    self_test()
    print("pre-word C identifier rewrite positive/negative controls PASS")
