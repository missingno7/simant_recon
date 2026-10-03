"""Diagnostic V5 owner emitter/rewriter, isolated from the V3 adapter."""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
PLAN=ROOT/'portable/research/whole_program_source_bounded_owners_v5.json'

def _sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def load_plan():
    plan=json.loads(PLAN.read_text(encoding='utf-8'))
    for item in plan['inputs'].values():
        if isinstance(item,dict) and 'path' in item:
            path=ROOT/item['path']
            if _sha(path)!=item['sha256']:
                raise ValueError(f'V5 source-bounded input changed: {item["path"]}')
    for rel,item in plan['inputs']['source_files'].items():
        if _sha(ROOT/rel)!=item['sha256']:
            raise ValueError(f'V5 source view changed: {rel}')
    return plan

def render_owners(plan):
    header=['/* Additive source-bounded owners V5; diagnostic until reviewed. */',
            '#ifndef SIMANT_SOURCE_BOUNDED_ADDITIVE_V5_H',
            '#define SIMANT_SOURCE_BOUNDED_ADDITIVE_V5_H', '#include <stdint.h>', '']
    if any(owner['name']=='Cycle' for owner in plan['owners']):
        header.extend(['/* Cycle has an original unsigned-byte alias to the low byte of a DOS word. */',
                       '#if !defined(SIMANT_NATIVE_LITTLE_ENDIAN)',
                       '#error "V5 Cycle byte alias requires an explicitly little-endian native target"',
                       '#endif',
                       '#if defined(__BYTE_ORDER__) && defined(__ORDER_LITTLE_ENDIAN__) && (__BYTE_ORDER__ != __ORDER_LITTLE_ENDIAN__)',
                       '#error "V5 Cycle byte alias cannot be used on a big-endian native target"',
                       '#endif', ''])
    source=['/* Additive source-bounded storage V5; diagnostic. */',
            '#include "source_bounded_additive.h"', '']
    for owner in plan['owners']:
        name=owner['name']; c_name='native_state_'+name; kind=owner['kind']
        if kind=='byte-array':
            decl=f'struct {{ uint8_t values[{owner["width_bytes"]}]; }}'
        elif kind=='word-union':
            decl='union { int16_t signed_value; uint8_t raw_bytes[2]; }'
        elif kind=='word-array-union':
            count=owner['count']
            decl=f'union {{ int16_t signed_values[{count}]; uint8_t raw_bytes[{count*2}]; }}'
        else: raise ValueError(f'unsupported V5 owner kind: {kind}')
        header.append(f'typedef {decl} NativeAdditive_{name};')
        header.append(f'extern NativeAdditive_{name} {c_name};')
        source.append(f'NativeAdditive_{name} {c_name};')
        header.append('');source.append('')
    header.append('#endif')
    return '\n'.join(header)+'\n','\n'.join(source)

def adapt(source, source_path, plan):
    rows=[m for o in plan['owners'] for m in o['source_mappings'] if m['source']==source_path]
    if not rows:return source,None
    replacements={}; original=(ROOT/source_path).read_text(encoding='utf-8')
    for row in rows:
        name,expr=row['name'],row['expression']
        if name in replacements and replacements[name]!=expr:
            raise ValueError(f'conflicting V5 state views: {source_path}:{name}')
        replacements[name]=expr
        decl=row['remove_extern']['text']
        source_pattern=r'(?m)^[ \t]*'+re.escape(decl)+r'[ \t]*(?:\r?\n|$)'
        expected=len(re.findall(source_pattern,original))
        # Whole-program generated TUs normalize `far` and primitive spellings
        # (for example unsigned char -> uint8_t). The pinned source determines
        # the expected count; remove the corresponding generated extern lines.
        pattern=r'(?m)^[ \t]*extern\s+[^;\r\n]*\b'+re.escape(name)+r'\b[^;\r\n]*;[ \t]*(?:\r?\n|$)'
        source,count=re.subn(pattern,'',source)
        if expected<1 or count!=expected:
            raise ValueError(f'V5 declaration changed: {source_path}:{name}: {count}/{expected}')
    # Identifier-only replacement preserves each call/index expression while
    # redirecting the lvalue to its typed view of the one additive owner.
    for name in sorted(replacements,key=len,reverse=True):
        source=re.sub(r'\b'+re.escape(name)+r'\b',lambda _m:replacements[name],source)
    return '#include "source_bounded_additive.h"\n'+source,{
        'kind':'SOURCE_BOUNDED_NATIVE_STATE_V5_DIAGNOSTIC',
        'plan':PLAN.relative_to(ROOT).as_posix(),
        'plan_sha256':_sha(PLAN),
        'source_views':replacements,
        'claim':'Source-derived additive native owner proposal; not historical extent evidence and not production selection.'}
