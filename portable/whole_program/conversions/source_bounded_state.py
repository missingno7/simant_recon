"""Integrate the reviewed V3 native allocations without historical extent claims."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from .unprovided_state_v2 import _identifier_rewrite

ROOT = Path(__file__).resolve().parents[3]
PLAN = ROOT / 'portable/research/whole_program_source_bounded_owners_v3.json'


def load_plan():
    plan = json.loads(PLAN.read_text(encoding='utf-8'))
    for entry in plan['inputs'].values():
        if isinstance(entry, dict) and 'path' in entry:
            path = ROOT / entry['path']
            if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
                raise ValueError(f"source-bounded state input changed: {entry['path']}")
    for path, entry in plan['inputs']['source_files'].items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError(f'source-bounded consumer changed: {path}')
    return plan


def render_owners(plan):
    # Reproduce the immutable proposal exactly, rather than selecting from the
    # live unresolved-symbol list or recalculating sizes from historical gaps.
    header = ['/* Additive native owner declarations; diagnostic V3. */',
              '#ifndef SIMANT_SOURCE_BOUNDED_OWNERS_V3_H',
              '#define SIMANT_SOURCE_BOUNDED_OWNERS_V3_H', '#include <stdint.h>', '']
    source = ['/* Additive native state definitions; diagnostic V3 only. */',
              '#include "native_owners.h"', '']
    for owner in plan['owners']:
        name = owner['owner_c_name']
        if owner['kind'] == 'scalar-with-serialized-byte-overlay':
            typ = 'NativeState_' + owner['owner']
            header.append(f'typedef union {typ} {{')
            for member in owner['members']:
                if member['name'] == 'raw_bytes':
                    header.append(f"    uint8_t raw_bytes[{member['count']}];")
                else:
                    header.append(f"    {member['type']} {member['name']};")
            header.extend([f'}} {typ};', f'extern {typ} {name};'])
            source.append(f'{typ} {name};')
        elif owner['kind'] == 'source-bounded-array':
            decl = f"{owner['native_type']} {name}[{owner['count']}];"
            header.append('extern ' + decl)
            source.append(decl)
        else:
            raise ValueError(f'unsupported native owner: {owner["kind"]}')
        header.append('')
        source.append('')
    header.append('#endif')
    header_text = '\n'.join(header) + '\n'
    source_text = '\n'.join(source)
    for text, key in [(header_text, 'owner_header_sha256'),
                      (source_text, 'owner_source_sha256')]:
        if hashlib.sha256(text.encode()).hexdigest() != plan[key]:
            raise ValueError('native owner emission differs from the reviewed V3 proposal')
    return header_text, source_text


def adapt(source, source_path, plan):
    mappings = [row for owner in plan['owners'] for row in owner['source_mappings']
                if row['source'] == source_path]
    if not mappings:
        return source, None
    replacements = {}
    for row in mappings:
        name, expression = row['name'], row['expression']
        if name in replacements:
            if replacements[name] != expression:
                raise ValueError(f'conflicting state views in {source_path}: {name}')
            continue
        declaration = row['remove_extern']['text']
        pattern = r'(?m)^[ \t]*' + re.escape(declaration) + r'[ \t]*(?:\r?\n|$)'
        # A few original TUs repeat an identical extern near later functions.
        # Remove every pinned instance, including repeated local declarations.
        original = (ROOT / source_path).read_text(encoding='utf-8')
        expected = len(re.findall(pattern, original))
        source, count = re.subn(pattern, '', source)
        if expected < 1 or count != expected:
            raise ValueError(f'source state declaration count changed: {source_path}:{name}: {count}/{expected}')
        replacements[name] = expression
    source = _identifier_rewrite(source, replacements)
    source = '#include "native_owners.h"\n' + source
    return source, {
        'kind': 'SOURCE_BOUNDED_NATIVE_STATE',
        'plan': PLAN.relative_to(ROOT).as_posix(),
        'plan_sha256': hashlib.sha256(PLAN.read_bytes()).hexdigest(),
        'source_views': replacements,
        'claim': 'Native single-owner allocation and SaveRec byte overlays; historical gaps are not allocation bounds',
    }
