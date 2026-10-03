"""Single native owners for source handle cells and overlapping viewport views.

All extents come from complete source declarations, not address gaps. Rectangles
retain their eight-byte scalar representation; handle cells use host pointers.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from .simulation_state_50f6_preword import replace_identifier_tokens

ROOT = Path(__file__).resolve().parents[3]
PLAN = ROOT / 'portable/research/game_view_state_v1.json'
PLAN_SHA256 = '7539f9318bebaE2cea0c1f96be09681e56a248dcb5590e66db55311d8a2a5dc6'.lower()
HEADER = 'portable/whole_program/state/game_views.h'


def load_plan():
    if hashlib.sha256(PLAN.read_bytes()).hexdigest() != PLAN_SHA256:
        raise ValueError('fixed game-view plan changed')
    plan = json.loads(PLAN.read_text())
    if len(plan['owners']) != 9:
        raise ValueError('expected six handle cells and three rectangles')
    for rel, expected in plan['sources'].items():
        if hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() != expected:
            raise ValueError(f'game view source changed: {rel}')
    return plan


def adapt(source, rel, plan):
    replacements, counts = {}, {}
    for owner in plan['owners']:
        rows = [r for r in owner['declarations'] if r['source'] == rel]
        if not rows:
            continue
        name = owner['name']
        views = set()
        for row in rows:
            declaration = row['text']
            pattern = r'(?m)^[ \t]*' + re.escape(declaration) + r'[ \t]*(?:\r?\n|$)'
            source, n = re.subn(pattern, '', source)
            if n != 1:
                raise ValueError(f'game view declaration changed: {rel}:{name}:{n}')
            views.add(row['native_view'])
        if len(views) != 1:
            raise ValueError(f'conflicting native view: {rel}:{name}')
        replacements[name] = views.pop()
    if not replacements:
        return source, None
    source, counts = replace_identifier_tokens(source, replacements)
    return f'#include "{HEADER}"\n' + source, {
        'kind': 'SOURCE_BOUNDED_GAME_HANDLE_AND_RECTANGLE_VIEWS',
        'plan_sha256': hashlib.sha256(PLAN.read_bytes()).hexdigest(),
        'source_sha256': plan['sources'][rel], 'views': replacements,
        'identifier_replacements': counts,
        'claim': 'Native ownership/layout conversion; original algorithms unchanged',
    }
