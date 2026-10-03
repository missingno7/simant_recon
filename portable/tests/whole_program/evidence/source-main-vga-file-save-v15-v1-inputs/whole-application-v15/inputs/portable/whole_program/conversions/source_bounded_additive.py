"""Production selection of the immutable additive V5 native-state proposal.

The diagnostic emitter remains unchanged so its original receipts stay useful.
This adapter protects C comments/literals and requires an explicit LE target.
"""
from __future__ import annotations

import re

from . import source_bounded_additive_v5 as proposal
from .unprovided_state_v2 import _identifier_rewrite

load_plan = proposal.load_plan


def render_owners(plan):
    header, source = proposal.render_owners(plan)
    header = header.replace('#if !defined(SIMANT_NATIVE_LITTLE_ENDIAN)',
        '#if !defined(SIMANT_NATIVE_LITTLE_ENDIAN) || SIMANT_NATIVE_LITTLE_ENDIAN != 1')
    return header, source


def adapt(source, source_path, plan):
    rows = [row for owner in plan['owners'] for row in owner['source_mappings']
            if row['source'] == source_path]
    if not rows:
        return source, None
    replacements = {}
    original = (proposal.ROOT / source_path).read_text(encoding='utf-8')
    for row in rows:
        name, expression = row['name'], row['expression']
        if name in replacements:
            if replacements[name] != expression:
                raise ValueError(f'conflicting V5 state views: {source_path}:{name}')
            continue
        declaration = row['remove_extern']['text']
        pattern = r'(?m)^[ \t]*' + re.escape(declaration) + r'[ \t]*(?:\r?\n|$)'
        expected = len(re.findall(pattern, original))
        source, count = re.subn(pattern, '', source)
        if expected < 1 or count != expected:
            raise ValueError(f'V5 source declaration changed: {source_path}:{name}: {count}/{expected}')
        replacements[name] = expression
    source = _identifier_rewrite(source, replacements)
    return '#include "source_bounded_additive.h"\n' + source, {
        'kind': 'SOURCE_BOUNDED_NATIVE_STATE_V5',
        'plan': proposal.PLAN.relative_to(proposal.ROOT).as_posix(),
        'plan_sha256': proposal._sha(proposal.PLAN),
        'source_views': replacements,
        'claim': 'Source-derived single native owners and serialized byte views; not historical extent evidence',
    }
