from __future__ import annotations
import re

def _body_span(source: str, name: str) -> tuple[int, int]:
    match = re.search('(?m)^int\\s+far\\s+' + re.escape(name) + '\\s*\\(', source)
    if match is None:
        raise ValueError(f'canonical source body missing: {name}')
    start = source.find('{', match.start())
    depth = 0
    state = 'code'
    i = start
    while i < len(source):
        if state == 'code':
            if source.startswith('//', i):
                state = 'line'
                i += 2
                continue
            if source.startswith('/*', i):
                state = 'comment'
                i += 2
                continue
            if source[i] in '"\'':
                state = 'string' if source[i] == '"' else 'char'
                i += 1
                continue
            if source[i] == '{':
                depth += 1
            elif source[i] == '}':
                depth -= 1
                if depth == 0:
                    return (match.start(), i + 1)
        elif state == 'line':
            if source[i] == '\n':
                state = 'code'
        elif state == 'comment':
            if source.startswith('*/', i):
                state = 'code'
                i += 2
                continue
        else:
            if source[i] == '\\':
                i += 2
                continue
            if state == 'string' and source[i] == '"' or (state == 'char' and source[i] == "'"):
                state = 'code'
        i += 1
    raise ValueError(f'unbalanced source body: {name}')

def _adapt_s17_body(body: str) -> str:
    local_decl = re.compile('\\s*long\\s+far\\s+\\*\\s+far\\s+\\*h;\\s*long\\s+far\\s+\\*p;\\s*long\\s+far\\s+\\*q;\\s*long\\s+far\\s+\\*r;\\s*int\\s+i;\\s*int\\s+draw;\\s*', re.MULTILINE)
    (body, count) = local_decl.subn('\n    SimHandle h;\n    char **r;\n    int i;\n    int draw;\n', body, count=1)
    if count != 1:
        raise ValueError('S17 local pointer declarations changed')
    (body, count) = re.subn('\\s*fd_55B3_6054\\s*=\\s*\\*h;', '\n    if (portable_menu_source_record_view_bind_handle(\n            &g_menu_view, h, f_171C_1C1C(h)) !=\n        PORTABLE_MENU_SOURCE_RECORD_OK) {\n        db_UnhookObject(id, 6);\n        return 0;\n    }\n    fd_55B3_6054 = portable_menu_source_record_tables(&g_menu_view);', body, count=1)
    if count != 1:
        raise ValueError('S17 base-pointer assignment changed')
    relocation = re.compile('\\s*for\\s*\\(p\\s*=\\s*fd_55B3_6054;\\s*\\*p;\\s*p\\+\\+\\)\\s*\\{.*?\\n\\s*\\}', re.DOTALL)
    (body, count) = relocation.subn('\n    /* Native sidecar replaces the DOS offset relocation traversal. */', body, count=1)
    if count != 1:
        raise ValueError('S17 DOS pointer-relocation loop changed')
    (body, count) = re.subn('r\\s*=\\s*\\(long\\s+far\\s+\\*\\s*\\)\\s*\\*fd_55B3_6054', 'r = fd_55B3_6054[0]', body, count=1)
    if count != 1:
        raise ValueError('S17 title-table traversal changed')
    ordered = ('db_LoadObject(id, 6)', 'source_record_view_bind_handle', 'db_UnhookObject(id, 6)', 'f_1FD2_0663(draw)', 'o17_384C_0184')
    if list(map(body.index, ordered)) != sorted(map(body.index, ordered)):
        raise ValueError('S17 source operation order changed')
    return body

def _geometry_pointer_views(source: str) -> str:
    for name in ('fd_50F6_46A8', 'fd_50F6_46BC'):
        (source, count) = re.subn('(?m)^extern\\s+int\\s+far\\s+' + name + '\\[\\];$', 'extern int far *' + name + ';', source)
        if count != 1:
            raise ValueError(f'menu geometry source declaration changed: {name}')
    return source

def adapt_s17_source(source: str) -> str:
    """Adapt canonical S17 TU while preserving all unrelated source text."""
    (source, count) = re.subn('(?m)^extern\\s+long\\s+far\\s+\\*\\s+far\\s+\\*\\s+far\\s+db_LoadObject\\(int\\s+object,\\s*int\\s+kind\\);$', 'extern SimHandle db_LoadObject(int object, int kind);', source, count=1)
    if count != 1:
        raise ValueError('S17 db_LoadObject source declaration changed')
    (source, count) = re.subn('(?m)^extern\\s+long\\s+far\\s+\\*\\s+far\\s+fd_55B3_6054;$', 'extern char ***fd_55B3_6054;', source, count=1)
    if count != 1:
        raise ValueError('S17 fd_55B3_6054 declaration changed')
    (start, end) = _body_span(source, 'o17_384C_0039')
    source = source[:start] + _adapt_s17_body(source[start:end]) + source[end:]
    headers = '#include "portable/whole_program/platform/handles.h"\n#include "portable/whole_program/platform/resource_menu_view.h"\nextern int32_t f_171C_1C1C(SimHandle handle);\n'
    return headers + _geometry_pointer_views(source)

def adapt_s10_source(source: str) -> str:
    """Map S10's over-wide source view to the same native char*** owner."""
    (source, count) = re.subn('(?m)^extern\\s+char\\s+far\\s+\\*\\s+far\\s+\\*\\s+far\\s+\\*\\s+far\\s+fd_55B3_6054;$', 'extern char ***fd_55B3_6054;', source, count=1)
    if count != 1:
        raise ValueError('S10 fd_55B3_6054 source declaration changed')
    return _geometry_pointer_views(source)
