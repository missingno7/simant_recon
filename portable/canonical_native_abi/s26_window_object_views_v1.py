from __future__ import annotations
import hashlib
import re
HEADER = '#include "portable/whole_program/window_refs.h"\n'
REGISTRY_DECL = 'extern SimWindowRefRegistry sim_window_ref_registry;\n'
HELPER = 'static struct Obj *simant_s26_window_object(struct Win *w, int index)\n{\n    char **objects;\n\n    if (w == NULL || index < 0 || index >= w->count)\n        return NULL;\n    objects = sim_window_ref_registry_objects_for_buffer(\n        &sim_window_ref_registry, (const char *)w);\n    if (objects == NULL)\n        return NULL;\n    return (struct Obj *)objects[index];\n}\n'

def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def _text(value: str | bytes) -> tuple[str, bytes]:
    raw = value.encode('utf-8') if isinstance(value, str) else value
    return (raw.decode('utf-8'), raw)

def _replace_code_refs(text: str) -> tuple[str, dict[str, int]]:
    """Replace the four active S26 references, leaving comments/literals alone."""
    matches: list[tuple[int, int, str]] = []
    i = 0
    state = 'code'
    while i < len(text):
        if state == 'code':
            if text.startswith('/*', i):
                state = 'block'
                i += 2
                continue
            if text.startswith('//', i):
                state = 'line'
                i += 2
                continue
            if text[i] == '"':
                state = 'string'
                i += 1
                continue
            if text[i] == "'":
                state = 'char'
                i += 1
                continue
            m = re.match('\\bw\\s*->\\s*objs\\s*\\[\\s*([01])\\s*\\]', text[i:])
            if m:
                idx = m.group(1)
                matches.append((i, i + m.end(), idx))
                i += m.end()
                continue
            i += 1
        elif state == 'block':
            if text.startswith('*/', i):
                state = 'code'
                i += 2
            else:
                i += 1
        elif state == 'line':
            if text[i] == '\n':
                state = 'code'
            i += 1
        else:
            endchar = '"' if state == 'string' else "'"
            if text[i] == '\\':
                i += 2
            elif text[i] == endchar:
                state = 'code'
                i += 1
            else:
                i += 1
    counts = {'index_0': 0, 'index_1': 0}
    for (_, _, idx) in matches:
        counts[f'index_{idx}'] += 1
    if counts != {'index_0': 3, 'index_1': 1}:
        raise ValueError(f'S26 object lookup inventory drift: {counts}')
    for (start, end, idx) in reversed(matches):
        text = text[:start] + f'simant_s26_window_object(w, {idx})' + text[end:]
    return (text, counts)

def _adapt_text(text: str, rel: str) -> tuple[str, dict]:
    (output, lookup_counts) = _replace_code_refs(text)
    if re.search('\\bw\\s*->\\s*objs\\b', _code_only(output)):
        raise ValueError('native S26 Win object-table member remains')
    if 'simant_s26_window_object(struct Win *w, int index)' in output:
        raise ValueError('S26 adapter appears to have already been applied')
    if HEADER not in output:
        output = HEADER + output
    if REGISTRY_DECL in output:
        raise ValueError('S26 registry declaration already exists')
    anchor = '};\n\nstruct Pt {'
    if output.count(anchor) != 1:
        raise ValueError('S26 Obj/Point declaration anchor drift')
    output = output.replace(anchor, '};\n\n' + REGISTRY_DECL + HELPER + '\nstruct Pt {', 1)
    return (output, {'kind': 'S26_WINDOW_OBJECT_SIDECAR_LOOKUPS', 'source': rel, 'active_lookups': lookup_counts, 'helper_count': 1, 'native_pointer_table_bypasses_remaining': 0})

def adapt(source: str | bytes, rel: str) -> tuple[str, dict]:
    """Apply at raw S26 preword stage, guarded by canonical source identity."""
    (text, raw) = _text(source)
    (output, report) = _adapt_text(text, rel)
    report.update({'input_sha256': _sha(raw), 'output_sha256': _sha(output.encode('utf-8'))})
    return (output, report)

def _code_only(source: str) -> str:
    """Return source with comments and literals blanked for safety checks."""
    out = list(source)
    i = 0
    state = 'code'
    while i < len(source):
        if state == 'code':
            if source.startswith('/*', i):
                state = 'block'
                out[i] = out[i + 1] = ' '
                i += 2
            elif source.startswith('//', i):
                state = 'line'
                out[i] = out[i + 1] = ' '
                i += 2
            elif source[i] == '"':
                state = 'string'
                out[i] = ' '
                i += 1
            elif source[i] == "'":
                state = 'char'
                out[i] = ' '
                i += 1
            else:
                i += 1
        elif state == 'block':
            if source.startswith('*/', i):
                out[i] = out[i + 1] = ' '
                state = 'code'
                i += 2
            else:
                if source[i] != '\n':
                    out[i] = ' '
                i += 1
        elif state == 'line':
            if source[i] == '\n':
                state = 'code'
            else:
                out[i] = ' '
            i += 1
        else:
            endchar = '"' if state == 'string' else "'"
            if source[i] == '\\':
                if i + 1 < len(source):
                    out[i] = out[i + 1] = ' '
                i += 2
            elif source[i] == endchar:
                out[i] = ' '
                state = 'code'
                i += 1
            else:
                if source[i] != '\n':
                    out[i] = ' '
                i += 1
    return ''.join(out)
