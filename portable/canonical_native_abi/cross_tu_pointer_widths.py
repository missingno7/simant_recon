"""Normalize DOS-width-equivalent pointer/integer views in the native projection."""
from __future__ import annotations

from collections import defaultdict
import re

_HANDLE_TYPEDEF = re.compile(r'\btypedef\s+(?P<type>[^;]*\*)\s*Handle\s*;')
_EXTERN_FUNCTION = re.compile(
    r'^\s*extern\s+(?P<ret>[^;{}]*?)\s+(?P<name>[A-Za-z_]\w*)\s*'
    r'\((?P<params>[^;{}]*)\)\s*;\s*$')
_FUNCTION_HEADER = re.compile(
    r'^\s*(?P<ret>[^;{}=]*?)\s+(?P<name>[A-Za-z_]\w*)\s*'
    r'\((?P<params>[^;{}]*)\)\s*(?P<body>\{)?\s*$')
_GLOBAL_OBJECT = re.compile(
    r'^(?P<indent>\s*)(?P<storage>(?:extern|static)\s+)?(?P<type>[^;]+?)\s+'
    r'(?P<name>[A-Za-z_]\w*)(?P<tail>\s*(?:=\s*[^;]*)?;)\s*$')
_GLOBAL_LONG_INIT = re.compile(
    r'^(?P<indent>\s*)(?P<type>(?:unsigned\s+)?long(?:\s+far)?)\s+'
    r'(?P<name>[A-Za-z_]\w*)(?P<tail>\s*=\s*[^;]*;)\s*$')


def _split_params(params: str) -> list[str]:
    if not params.strip() or params.strip() == 'void':
        return []
    result, start, depth = [], 0, 0
    for i, ch in enumerate(params):
        if ch in '([':
            depth += 1
        elif ch in ')]':
            depth -= 1
        elif ch == ',' and depth == 0:
            result.append(params[start:i].strip())
            start = i + 1
    result.append(params[start:].strip())
    return result


def _param_type_name(param: str) -> tuple[str, str]:
    value = param.strip()
    match = re.search(r'([A-Za-z_]\w*)\s*$', value)
    if not match or match.group(1) in {'far', 'near', 'const', 'volatile'}:
        return value, ''
    prefix = value[:match.start()].rstrip()
    if not prefix or not re.search(r'[A-Za-z_*\]]$', prefix):
        return value, ''
    return prefix, match.group(1)


def _pointer_aliases(sources: dict[str, str]) -> dict[str, str]:
    aliases = {}
    for source in sources.values():
        for match in _HANDLE_TYPEDEF.finditer(source):
            aliases['Handle'] = match.group('type').strip()
    return aliases


def _expand_alias(type_text: str, aliases: dict[str, str]) -> str:
    value = type_text.strip()
    words = value.split()
    if len(words) == 1 and words[0] in aliases:
        return aliases[words[0]]
    if len(words) == 2 and words[0] in aliases and words[1] in {'far', 'near'}:
        return aliases[words[0]] + ' ' + words[1]
    return value


def _width_class(type_text: str, aliases: dict[str, str]) -> str | None:
    value = type_text.strip()
    expanded = _expand_alias(value, aliases)
    if '*' in expanded and not re.search(r'\bnear\b', expanded):
        return 'dos4-pointer'
    if re.search(r'\b(?:unsigned\s+)?long\b', value):
        return 'dos4-integer'
    if re.search(r'\bint32_t\b|\buint32_t\b', value):
        return 'dos4-integer'
    return None


def _pointer_spelling(type_text: str, aliases: dict[str, str]) -> str:
    return _expand_alias(type_text, aliases).strip()


def _pointer_return_spelling(type_text: str, aliases: dict[str, str]) -> tuple[str, str]:
    value = type_text.strip()
    suffix = ''
    match = re.search(r'\s+(far|near)\s*$', value)
    if match:
        suffix = match.group(1)
        value = value[:match.start()].strip()
    return _expand_alias(value, aliases).strip(), suffix


def _is_top_level_header(lines: list[str], index: int, match: re.Match) -> bool:
    if match.group('body'):
        return True
    for next_line in lines[index + 1:index + 3]:
        if not next_line.strip():
            continue
        return next_line.lstrip().startswith('{')
    return False


def _declarations(sources: dict[str, str]):
    definitions = {}
    prototypes = defaultdict(list)
    for source_name, text in sources.items():
        lines = text.splitlines()
        for i, line in enumerate(lines):
            prototype = _EXTERN_FUNCTION.match(line)
            if prototype:
                prototypes[prototype.group('name')].append(
                    (source_name, i, prototype.group('ret').strip(),
                     _split_params(prototype.group('params'))))
                continue
            header = _FUNCTION_HEADER.match(line)
            if not header or not _is_top_level_header(lines, i, header):
                continue
            ret = header.group('ret').strip()
            if not ret or re.search(r'\b(?:if|while|for|switch|return)\b', ret):
                continue
            definitions.setdefault(header.group('name'),
                                   (ret, _split_params(header.group('params'))))
    return definitions, prototypes


def _fix_function_width_views(sources: dict[str, str], aliases: dict[str, str]):
    definitions, prototypes = _declarations(sources)
    result = dict(sources)
    changed = []
    pointer_returns = {}
    for name, (ret, params) in definitions.items():
        if _width_class(ret, aliases) == 'dos4-pointer':
            pointer_returns[name] = _pointer_return_spelling(ret, aliases)[0]
        for source_name, line_index, proto_ret, proto_params in prototypes.get(name, []):
            if len(params) != len(proto_params):
                continue
            edits = []
            proto_ret_class, def_ret_class = _width_class(proto_ret, aliases), _width_class(ret, aliases)
            if {proto_ret_class, def_ret_class} == {'dos4-integer', 'dos4-pointer'}:
                # The pointer view is the native representation of this DOS 4-byte value.
                pointer_type, _ = _pointer_return_spelling(ret if def_ret_class == 'dos4-pointer' else proto_ret, aliases)
                if proto_ret_class == 'dos4-integer':
                    edits.append(('return', pointer_type))
            for position, (definition_param, prototype_param) in enumerate(zip(params, proto_params)):
                def_type, _ = _param_type_name(definition_param)
                proto_type, proto_name = _param_type_name(prototype_param)
                if {_width_class(def_type, aliases), _width_class(proto_type, aliases)} != {
                        'dos4-integer', 'dos4-pointer'}:
                    continue
                pointer_type = _pointer_spelling(
                    def_type if _width_class(def_type, aliases) == 'dos4-pointer' else proto_type,
                    aliases)
                if _width_class(proto_type, aliases) == 'dos4-integer':
                    edits.append((position, (pointer_type + (' ' + proto_name if proto_name else '')).strip()))
            if not edits:
                continue
            old_line = result[source_name].splitlines()[line_index]
            match = _EXTERN_FUNCTION.match(old_line)
            ret_text = match.group('ret').strip()
            param_texts = _split_params(match.group('params'))
            for position, replacement in edits:
                if position == 'return':
                    # Preserve a trailing far/near function-model qualifier.
                    qualifiers = re.findall(r'\b(?:far|near)\b', ret_text)
                    new_base = replacement
                    new_ret = new_base + ((' ' + qualifiers[-1]) if qualifiers else '')
                    ret_text = new_ret
                else:
                    param_texts[position] = replacement
            new_line = re.sub(r'\bextern\s+' + re.escape(match.group('ret').strip()) +
                              r'\s+' + re.escape(name) + r'\s*\(.*\)\s*;',
                              'extern ' + ret_text + ' ' + name + '(' + ', '.join(param_texts) + ');',
                              old_line, count=1)
            if new_line == old_line:
                raise ValueError(f'could not rewrite pointer-width prototype {source_name}:{line_index+1}: {name}')
            lines = result[source_name].splitlines()
            lines[line_index] = new_line
            result[source_name] = '\n'.join(lines) + ('\n' if result[source_name].endswith('\n') else '')
            changed.append({'source': source_name, 'line': line_index + 1,
                            'function': name, 'before': old_line.strip(), 'after': new_line.strip()})
    return result, pointer_returns, changed


def _fix_pointer_globals(sources: dict[str, str], aliases: dict[str, str], object_aliases: dict[str, str]):
    declarations = defaultdict(list)
    for source_name, text in sources.items():
        for i, line in enumerate(text.splitlines()):
            if line[:1].isspace():
                continue
            match = _GLOBAL_OBJECT.match(line)
            if not match:
                continue
            type_text = match.group('type').strip()
            category = _width_class(type_text, aliases)
            if category not in {'dos4-integer', 'dos4-pointer'}:
                continue
            name = match.group('name')
            canonical = object_aliases.get(name, name)
            declarations[canonical].append((category, source_name, i, name, type_text, line))
    result = dict(sources)
    changed = []
    pointer_owners = {}
    for canonical, facts in declarations.items():
        longs = [fact for fact in facts if fact[0] == 'dos4-integer']
        pointers = [fact for fact in facts if fact[0] == 'dos4-pointer']
        if not longs or not pointers:
            continue
        pointer_owners[canonical] = {'integer_views': len(longs), 'pointer_views': len(pointers)}
        for _, source_name, line_index, raw_name, _, old_line in facts:
            match = _GLOBAL_OBJECT.match(old_line)
            new_line = old_line[:match.start('type')] + 'void far * far' + old_line[match.end('type'):]
            if new_line == old_line:
                raise ValueError(f'could not unify native pointer owner {source_name}:{line_index+1}: {raw_name}')
            lines = result[source_name].splitlines()
            lines[line_index] = new_line
            result[source_name] = '\n'.join(lines) + ('\n' if result[source_name].endswith('\n') else '')
            changed.append({'source': source_name, 'line': line_index + 1,
                            'object': raw_name, 'owner': canonical,
                            'before': old_line.strip(), 'after': new_line.strip()})
    return result, pointer_owners, changed


def _promote_pointer_result_globals(sources: dict[str, str], aliases: dict[str, str], pointer_returns: dict[str, str]):
    result = dict(sources)
    long_globals = {}
    for source_name, text in sources.items():
        for i, line in enumerate(text.splitlines()):
            match = _GLOBAL_LONG_INIT.match(line)
            if match and not match.group('indent'):
                long_globals[match.group('name')] = (source_name, i, match.group('type'), line)
    assignments = defaultdict(set)
    for source_name, text in sources.items():
        for name, function_type in pointer_returns.items():
            pattern = re.compile(r'\b([A-Za-z_]\w*)\s*=\s*' + re.escape(name) + r'\s*\(')
            for match in pattern.finditer(text):
                if match.group(1) in long_globals:
                    assignments[match.group(1)].add(function_type)
    promoted = {}
    for name, types in assignments.items():
        if len(types) != 1:
            raise ValueError(f'conflicting pointer result views for {name}: {sorted(types)}')
        promoted[name] = _pointer_spelling(next(iter(types)), aliases)
    changed = []
    for source_name, text in list(result.items()):
        lines = text.splitlines()
        dirty = False
        for line_index, old_line in enumerate(lines):
            match = _GLOBAL_OBJECT.match(old_line)
            if not match or match.group('indent'):
                continue
            if _width_class(match.group('type').strip(), aliases) != 'dos4-integer':
                continue
            name = match.group('name')
            if name not in promoted:
                continue
            pointer_type = promoted[name]
            new_line = old_line[:match.start('type')] + pointer_type + old_line[match.end('type'):]
            if new_line == old_line:
                raise ValueError(f'could not widen pointer-result owner {source_name}:{line_index+1}: {name}')
            lines[line_index] = new_line
            dirty = True
            changed.append({'source': source_name, 'line': line_index + 1,
                            'object': name, 'native_type': pointer_type,
                            'before': old_line.strip(), 'after': new_line.strip()})
        if dirty:
            result[source_name] = '\n'.join(lines) + ('\n' if text.endswith('\n') else '')
    return result, changed


def adapt(sources: dict[str, str], object_aliases: dict[str, str] | None = None):
    """Return projected sources plus the mechanically discovered pointer-width edits."""
    aliases = _pointer_aliases(sources)
    object_aliases = object_aliases or {}
    projected, pointer_returns, function_changes = _fix_function_width_views(sources, aliases)
    projected, pointer_owners, global_changes = _fix_pointer_globals(projected, aliases, object_aliases)
    projected, result_changes = _promote_pointer_result_globals(projected, aliases, pointer_returns)
    receipt = {
        'schema': 'cross-tu-pointer-width-projection-v1',
        'rule': 'When a DOS 4-byte long view conflicts with a far-pointer view, preserve the pointer in native storage and function declarations; promote long globals assigned pointer-return results.',
        'pointer_function_prototypes': function_changes,
        'pointer_owners': global_changes,
        'pointer_result_owners': result_changes,
        'count': len(function_changes) + len(global_changes) + len(result_changes),
    }
    return projected, receipt
