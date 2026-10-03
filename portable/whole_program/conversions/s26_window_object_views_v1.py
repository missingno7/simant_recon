"""Route S26 Win object lookups through the native window sidecar table.

The source Win record carries a 32-bit DOS offset table at +0x2c. In the SDL
host, object addresses live in the registry sidecar; the generated native
``struct Win::objs`` member is only an accidental pointer-width overlay and
must never be read.
"""
from __future__ import annotations

import hashlib
import re


SOURCE_PATH = "src/S26/m39C7.c"
SOURCE_SHA256 = "fb4938daa334a8e9f929b44a542392f47fc7c1a654ca87f303ee80528b34c4c4"
GENERATED_PATH = "build/workers/whole_program/generated/S26_m39C7.c"
GENERATED_SHA256 = "7dca4ba983881c6309863f34d03d7093d95a079a5cb23cf0f26b767a84c69bbb"
HEADER = '#include "portable/whole_program/window_refs.h"\n'
REGISTRY_DECL = "extern SimWindowRefRegistry sim_window_ref_registry;\n"
HELPER = r'''static struct Obj *simant_s26_window_object(struct Win *w, int index)
{
    char **objects;

    if (w == NULL || index < 0 || index >= w->count)
        return NULL;
    objects = sim_window_ref_registry_objects_for_buffer(
        &sim_window_ref_registry, (const char *)w);
    if (objects == NULL)
        return NULL;
    return (struct Obj *)objects[index];
}
'''


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _text(value: str | bytes) -> tuple[str, bytes]:
    raw = value.encode("utf-8") if isinstance(value, str) else value
    return raw.decode("utf-8"), raw


def _replace_code_refs(text: str) -> tuple[str, dict[str, int]]:
    """Replace the four active S26 references, leaving comments/literals alone."""
    matches: list[tuple[int, int, str]] = []
    i = 0
    state = "code"
    while i < len(text):
        if state == "code":
            if text.startswith("/*", i):
                state = "block"
                i += 2
                continue
            if text.startswith("//", i):
                state = "line"
                i += 2
                continue
            if text[i] == '"':
                state = "string"
                i += 1
                continue
            if text[i] == "'":
                state = "char"
                i += 1
                continue
            m = re.match(r"\bw\s*->\s*objs\s*\[\s*([01])\s*\]", text[i:])
            if m:
                idx = m.group(1)
                matches.append((i, i + m.end(), idx))
                i += m.end()
                continue
            i += 1
        elif state == "block":
            if text.startswith("*/", i):
                state = "code"
                i += 2
            else:
                i += 1
        elif state == "line":
            if text[i] == "\n":
                state = "code"
            i += 1
        else:
            endchar = '"' if state == "string" else "'"
            if text[i] == "\\":
                i += 2
            elif text[i] == endchar:
                state = "code"
                i += 1
            else:
                i += 1

    counts = {"index_0": 0, "index_1": 0}
    for _, _, idx in matches:
        counts[f"index_{idx}"] += 1
    if counts != {"index_0": 3, "index_1": 1}:
        raise ValueError(f"S26 object lookup inventory drift: {counts}")
    for start, end, idx in reversed(matches):
        text = text[:start] + f"simant_s26_window_object(w, {idx})" + text[end:]
    return text, counts


def _adapt_text(text: str, rel: str) -> tuple[str, dict]:
    output, lookup_counts = _replace_code_refs(text)
    if re.search(r"\bw\s*->\s*objs\b", _code_only(output)):
        raise ValueError("native S26 Win object-table member remains")
    if "simant_s26_window_object(struct Win *w, int index)" in output:
        raise ValueError("S26 adapter appears to have already been applied")
    if HEADER not in output:
        output = HEADER + output
    if REGISTRY_DECL in output:
        raise ValueError("S26 registry declaration already exists")
    # Place the owner declaration and helper after the complete Obj type. This
    # keeps the source function order and all source operations unchanged.
    anchor = "};\n\nstruct Pt {"
    if output.count(anchor) != 1:
        raise ValueError("S26 Obj/Point declaration anchor drift")
    output = output.replace(anchor, "};\n\n" + REGISTRY_DECL + HELPER + "\nstruct Pt {", 1)
    return output, {
        "kind": "S26_WINDOW_OBJECT_SIDECAR_LOOKUPS",
        "source": rel,
        "active_lookups": lookup_counts,
        "helper_count": 1,
        "native_pointer_table_bypasses_remaining": 0,
    }


def adapt(source: str | bytes, rel: str) -> tuple[str, dict]:
    """Apply at raw S26 preword stage, guarded by canonical source identity."""
    text, raw = _text(source)
    if rel != SOURCE_PATH or _sha(raw) != SOURCE_SHA256:
        raise ValueError("frozen S26 source identity drift")
    output, report = _adapt_text(text, rel)
    report.update({
        "canonical_source_sha256": SOURCE_SHA256,
        "input_sha256": _sha(raw),
        "output_sha256": _sha(output.encode("utf-8")),
    })
    return output, report


def adapt_generated(source: str | bytes, rel: str) -> tuple[str, dict]:
    """Standalone compile-control path pinned to the captured v15 TU."""
    text, raw = _text(source)
    if rel != GENERATED_PATH or _sha(raw) != GENERATED_SHA256:
        raise ValueError("captured generated S26 identity drift")
    output, report = _adapt_text(text, rel)
    report.update({
        "canonical_source_sha256": SOURCE_SHA256,
        "captured_generated_sha256": GENERATED_SHA256,
        "input_sha256": _sha(raw),
        "output_sha256": _sha(output.encode("utf-8")),
    })
    return output, report


def _code_only(source: str) -> str:
    """Return source with comments and literals blanked for safety checks."""
    out = list(source)
    i = 0
    state = "code"
    while i < len(source):
        if state == "code":
            if source.startswith("/*", i):
                state = "block"
                out[i] = out[i + 1] = " "
                i += 2
            elif source.startswith("//", i):
                state = "line"
                out[i] = out[i + 1] = " "
                i += 2
            elif source[i] == '"':
                state = "string"
                out[i] = " "
                i += 1
            elif source[i] == "'":
                state = "char"
                out[i] = " "
                i += 1
            else:
                i += 1
        elif state == "block":
            if source.startswith("*/", i):
                out[i] = out[i + 1] = " "
                state = "code"
                i += 2
            else:
                if source[i] != "\n":
                    out[i] = " "
                i += 1
        elif state == "line":
            if source[i] == "\n":
                state = "code"
            else:
                out[i] = " "
            i += 1
        else:
            endchar = '"' if state == "string" else "'"
            if source[i] == "\\":
                if i + 1 < len(source):
                    out[i] = out[i + 1] = " "
                i += 2
            elif source[i] == endchar:
                out[i] = " "
                state = "code"
                i += 1
            else:
                if source[i] != "\n":
                    out[i] = " "
                i += 1
    return "".join(out)
