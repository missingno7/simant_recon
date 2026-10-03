"""Strict production adapter for the fixed, source-bounded 50F6 V6 owner plan.

This module is a separate integration adapter. It does not edit the plan,
consult an unresolved-symbol list, infer extents, or modify the central
whole-program generator.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .simulation_state_50f6_preword import replace_identifier_tokens

ROOT = Path(__file__).resolve().parents[3]
PLAN_PATH = ROOT / 'portable/research/whole_program_simulation_state_50f6_v6.json'
PLAN_SHA256 = '47a5940df5784fccd41b3bc4328d5a4c374d6c5693f6a1e34f65514049f045e5'
OWNER_HEADER_SHA256 = '5c87fe9e12f755eee3e1beeaab9b2478bb5ec95782b031b805ecb828c8c6de1f'
OWNER_SOURCE_SHA256 = 'c2489524a8975665e0c49b3cfd19fb2b5e8161c3ac7b5ec4dca4eb9cda51c79a'
FROZEN_INPUTS = {
    'layout/manifest.json': '025a0a9255d910cae4b122ab5a3f3fb40888bb456d7fe42158db7c9e622fcf50',
    'layout/symbols.json': '0f5dd5b0a211945a97782cfccdb9bb31b0dfd07fcde5df4d4f9486b487eb0125',
}

def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def _check_fixed(path: Path, expected: str, label: str) -> None:
    if not path.is_file() or _sha(path) != expected:
        raise ValueError(f'V6 fixed {label} changed: {path.relative_to(ROOT).as_posix()}')

def _check_plan_argument(plan: dict[str, Any]) -> None:
    _check_fixed(PLAN_PATH, PLAN_SHA256, 'plan')
    canonical = json.loads(PLAN_PATH.read_text(encoding='utf-8'))
    if plan != canonical:
        raise ValueError('caller-supplied V6 plan differs from the fixed reviewed plan')

def load_plan() -> dict[str, Any]:
    """Load only the immutable reviewed plan and its source/layout pins."""
    _check_fixed(PLAN_PATH, PLAN_SHA256, 'plan')
    plan = json.loads(PLAN_PATH.read_text(encoding='utf-8'))
    if plan.get('schema') != 'simant-whole-program-simulation-state-plan-v6':
        raise ValueError('unexpected V6 plan schema')
    for rel, expected in FROZEN_INPUTS.items():
        _check_fixed(ROOT / rel, expected, 'layout input')
    for rel, expected in plan.get('source_hashes', {}).items():
        _check_fixed(ROOT / rel, expected, 'source view')
    for item in plan.get('input_hashes', {}).values():
        rel, expected = item.get('path'), item.get('sha256')
        if not rel or not expected or rel.startswith('build/workers/whole_program/generated/'):
            continue
        _check_fixed(ROOT / rel, expected, 'pinned plan input')
    # Ensure this adapter never accepts an edited or substituted subset plan.
    if len(plan.get('targets', [])) != 24:
        raise ValueError('V6 plan must contain exactly 24 typed owners')
    return plan

def _declarations(plan: dict[str, Any], rel: str) -> dict[str, list[tuple[dict[str, Any], dict[str, Any]]]]:
    by_name: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = {}
    for owner in plan['targets']:
        for decl in owner['declarations']:
            if decl['source'] == rel:
                by_name.setdefault(owner['symbol'], []).append((owner, decl))
    return by_name

def _view_expression(owner: dict[str, Any], declaration: str) -> str:
    name = owner['symbol']
    if re.search(r'\bunsigned\s+char\s+(?:far\s+)?' + re.escape(name) + r'\s*\[\s*\]', declaration):
        return f'native_sim_state_{name}.raw_bytes'
    if owner['kind'] == 'history-64-signed-words':
        if not re.search(r'\bint\s+(?:far\s+)?' + re.escape(name) + r'\s*\[\s*64\s*\]', declaration):
            raise ValueError(f'V6 unexpected history declaration: {declaration}')
        return f'native_sim_state_{name}.signed_values'
    if re.search(r'\bint\s+(?:far\s+)?' + re.escape(name) + r'\s*\[\s*2\s*\]', declaration):
        return f'native_sim_state_{name}.words'
    m = re.search(r'\bextern\s+((?:struct\s+\w+|Point|Pnt))\s+far\s+' + re.escape(name) + r'\s*;', declaration)
    if m:
        ctype = m.group(1)
        return f'(*(({ctype} *)native_sim_state_{name}.raw_bytes))'
    raise ValueError(f'V6 no exact source-view adapter for {name}: {declaration}')

def render_owners(plan: dict[str, Any]) -> tuple[str, str]:
    """Render one strict single-owner declaration/definition per plan symbol."""
    _check_plan_argument(plan)
    header = [
        '/* Fixed source-bounded shared simulation owners, V6. */',
        '#ifndef SIMANT_SOURCE_BOUNDED_SIMULATION_STATE_V6_H',
        '#define SIMANT_SOURCE_BOUNDED_SIMULATION_STATE_V6_H',
        '#include <stdint.h>',
        '#if !defined(SIMANT_NATIVE_LITTLE_ENDIAN) || SIMANT_NATIVE_LITTLE_ENDIAN != 1',
        '#error "V6 serialized-byte overlays require an explicitly little-endian native target"',
        '#endif',
        '#if defined(__BYTE_ORDER__) && defined(__ORDER_LITTLE_ENDIAN__) && (__BYTE_ORDER__ != __ORDER_LITTLE_ENDIAN__)',
        '#error "V6 serialized-byte overlays cannot be used on a big-endian native target"',
        '#endif',
        'typedef union { struct { int16_t x, y; } xy; struct { int16_t v, h; } vh; int16_t words[2]; uint8_t raw_bytes[4]; } NativeSimStatePointV6;',
        'typedef union { int16_t signed_values[64]; uint8_t raw_bytes[128]; } NativeSimStateHistoryV6;',
        '',
    ]
    source = ['/* Fixed V6 owner storage. */', '#include "simulation_state_50f6.h"', '']
    for owner in plan['targets']:
        name = owner['symbol']
        ctype = 'NativeSimStatePointV6' if owner['kind'] == 'point-two-word-overlay' else 'NativeSimStateHistoryV6'
        if owner['extent_bytes'] != (4 if ctype.endswith('PointV6') else 128):
            raise ValueError(f'V6 extent/type mismatch: {name}')
        header.append(f'extern {ctype} native_sim_state_{name};')
        source.append(f'{ctype} native_sim_state_{name};')
    header.extend(['', '#endif', ''])
    header_text, source_text = '\n'.join(header), '\n'.join(source)
    if hashlib.sha256(header_text.encode('utf-8')).hexdigest() != OWNER_HEADER_SHA256:
        raise ValueError('V6 rendered owner header differs from its pinned proposal')
    if hashlib.sha256(source_text.encode('utf-8')).hexdigest() != OWNER_SOURCE_SHA256:
        raise ValueError('V6 rendered owner source differs from its pinned proposal')
    return header_text, source_text

def adapt(source: str, rel: str, plan: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
    """Apply exact per-TU extern removal and lexical owner-view rewrites."""
    _check_plan_argument(plan)
    rel = Path(rel).as_posix()
    if rel not in plan.get('source_hashes', {}):
        if any(d['source'] == rel for owner in plan['targets'] for d in owner['declarations']):
            raise ValueError(f'V6 source lacks a frozen source hash: {rel}')
        return source, None
    _check_fixed(ROOT / rel, plan['source_hashes'][rel], 'consumer source')
    mappings = _declarations(plan, rel)
    if not mappings:
        return source, None
    original_lines = (ROOT / rel).read_text(encoding='latin1').splitlines()
    replacements: dict[str, str] = {}
    removed: dict[str, int] = {}
    for name, rows in sorted(mappings.items()):
        expected_rows = []
        for owner, decl in rows:
            line_no = int(decl['line'])
            if line_no < 1 or line_no > len(original_lines) or original_lines[line_no - 1].strip() != decl['text']:
                raise ValueError(f'V6 declaration pin mismatch: {rel}:{line_no}:{name}')
            expected_rows.append(decl['text'])
        exprs = {_view_expression(owner, decl['text']) for owner, decl in rows}
        if len(exprs) != 1:
            raise ValueError(f'V6 source has conflicting typed views: {rel}:{name}:{sorted(exprs)}')
        replacements[name] = next(iter(exprs))
        # Generated whole TUs normalize storage qualifiers/type spellings. Match
        # exactly one declaration-shaped extern per pinned original occurrence.
        pattern = r'(?m)^[ \t]*extern\s+[^;\r\n]*\b' + re.escape(name) + r'\b[^;\r\n]*;[ \t]*(?:\r?\n|$)'
        source, count = re.subn(pattern, '', source)
        if count != len(expected_rows):
            raise ValueError(f'V6 generated declaration count mismatch: {rel}:{name}: {count}/{len(expected_rows)}')
        removed[name] = count
    converted, counts = replace_identifier_tokens(source, replacements)
    if any(counts[name] < 1 for name in replacements):
        raise ValueError(f'V6 target has no generated consumer token: {rel}:{counts}')
    return '#include "simulation_state_50f6.h"\n' + converted, {
        'kind': 'SOURCE_BOUNDED_SIMULATION_STATE_V6',
        'plan': PLAN_PATH.relative_to(ROOT).as_posix(),
        'plan_sha256': PLAN_SHA256,
        'source': rel,
        'source_sha256': plan['source_hashes'][rel],
        'source_views': replacements,
        'removed_extern_declarations': removed,
        'rewritten_identifier_tokens': counts,
        'claim': 'Strict source-bounded single-owner adaptation from complete declarations and exact SaveRec rows; not communal-gap extent evidence.',
    }
