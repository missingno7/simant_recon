"""Strict pre-word adapter for the fixed V7 simulation-array owner plan."""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
from typing import Any
from .simulation_state_50f6_preword import replace_identifier_tokens

ROOT=Path(__file__).resolve().parents[3]
PLAN_PATH=ROOT/'portable/research/whole_program_simulation_state_50f6_v7.json'
PLAN_SHA256='83e3f4f80381b7b450c21127763ba8ca19ff27c5696af5c20633a4c7fa3a09ce'
FROZEN_INPUTS={
 'layout/manifest.json':'025a0a9255d910cae4b122ab5a3f3fb40888bb456d7fe42158db7c9e622fcf50',
 'layout/symbols.json':'0f5dd5b0a211945a97782cfccdb9bb31b0dfd07fcde5df4d4f9486b487eb0125',
}
def _sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def _fixed(path:Path,digest:str,kind:str)->None:
 if not digest or not path.is_file() or _sha(path)!=digest:raise ValueError(f'V7 pinned {kind} changed: {path.relative_to(ROOT).as_posix()}')
def _plan_eq(plan:dict[str,Any])->None:
 _fixed(PLAN_PATH,PLAN_SHA256,'plan')
 if plan!=json.loads(PLAN_PATH.read_text(encoding='utf-8')):raise ValueError('caller V7 plan differs from fixed plan')
def load_plan()->dict[str,Any]:
 _fixed(PLAN_PATH,PLAN_SHA256,'plan')
 p=json.loads(PLAN_PATH.read_text(encoding='utf-8'))
 if p.get('schema')!='simant-whole-program-simulation-state-plan-v7' or len(p.get('targets',[]))!=13:raise ValueError('unexpected V7 plan shape')
 for rel,digest in FROZEN_INPUTS.items():_fixed(ROOT/rel,digest,'layout')
 for rel,digest in p['source_hashes'].items():_fixed(ROOT/rel,digest,'source view')
 for pin in p.get('input_hashes',{}).values():
  rel,digest=pin.get('path'),pin.get('sha256')
  if rel and digest and not rel.startswith('build/workers/whole_program/generated/'):_fixed(ROOT/rel,digest,'old owner/source plan')
 return p
def render_owners(plan:dict[str,Any])->tuple[str,str]:
 _plan_eq(plan)
 h=['/* Fixed source-bounded simulation-array owners V7. */','#ifndef SIMANT_SOURCE_BOUNDED_SIMULATION_STATE_V7_H','#define SIMANT_SOURCE_BOUNDED_SIMULATION_STATE_V7_H','#include <stdint.h>','typedef struct NativeV7TriLevel { uint16_t frac, mid, weight; } NativeV7TriLevel;',
    '#if !defined(SIMANT_NATIVE_LITTLE_ENDIAN) || SIMANT_NATIVE_LITTLE_ENDIAN != 1','#error "V7 raw SaveRec byte overlays require an explicitly little-endian native target"','#endif',
    '#if defined(__BYTE_ORDER__) && defined(__ORDER_LITTLE_ENDIAN__) && (__BYTE_ORDER__ != __ORDER_LITTLE_ENDIAN__)','#error "V7 raw SaveRec byte overlays cannot be used on a big-endian target"','#endif','']
 c=['/* One native owner per source-bounded V7 SaveRec state object. */','#include "simulation_state_50f6_v7.h"','']
 seen=set()
 for t in plan['targets']:
  name=t['symbol'];n=t['count'];kind=t['kind'];typ='NativeV7_'+name
  if name in seen:raise ValueError('duplicate V7 owner '+name)
  seen.add(name)
  if kind=='byte-table-signed-view':decl=f'union {{ int8_t signed_values[{n}]; uint8_t unsigned_values[{n}]; uint8_t raw_bytes[{t["extent_bytes"]}]; }}'
  elif kind=='byte-table':decl=f'union {{ uint8_t unsigned_values[{n}]; uint8_t raw_bytes[{t["extent_bytes"]}]; }}'
  elif kind=='tri-level-struct':decl='union { NativeV7TriLevel tri; int16_t signed_values[3]; uint16_t unsigned_values[3]; uint8_t raw_bytes[6]; }'
  elif kind in ('word-array','word-array-prefix-scalar'):
   extra=' NativeV7TriLevel tri;' if name=='modeLevels' else ''
   decl=f'union {{{extra} int16_t signed_values[{n}]; uint16_t unsigned_values[{n}]; uint8_t raw_bytes[{t["extent_bytes"]}]; }}'
  else:raise ValueError(f'unsupported V7 owner type {kind}')
  h.extend([f'typedef {decl} {typ};',f'extern {typ} native_sim_state_{name};'])
  c.append(f'{typ} native_sim_state_{name};')
 h.extend(['','#endif',''])
 return '\n'.join(h),'\n'.join(c)
def _view(t:dict[str,Any],decl:str)->str:
 n=t['symbol'];kind=t['kind']
 if kind.startswith('byte-table'):
  if re.search(r'\bsigned\s+char\b',decl):return f'native_sim_state_{n}.signed_values'
  if re.search(r'\bunsigned\s+char\b',decl):return f'native_sim_state_{n}.unsigned_values' if kind=='byte-table-signed-view' else f'native_sim_state_{n}.unsigned_values'
  raise ValueError(f'unexpected V7 byte alias: {decl}')
 if 'struct TriLevel' in decl:return f'(*((struct TriLevel *)native_sim_state_{n}.raw_bytes))'
 if kind=='tri-level-struct':
  if not re.search(r'\bunsigned\s+char\b',decl):raise ValueError(f'casteLevels requires TriLevel or serialization byte view: {decl}')
  return f'native_sim_state_{n}.raw_bytes'
 if re.search(r'\bunsigned\s+char\b',decl):return f'native_sim_state_{n}.raw_bytes'
 if re.search(r'\bunsigned\s+int\b',decl):return f'native_sim_state_{n}.unsigned_values'
 if re.search(r'\bint\b',decl):
  if kind=='word-array-prefix-scalar' and re.search(r'\b'+re.escape(n)+r'\s*;',decl):return f'native_sim_state_{n}.signed_values[0]'
  return f'native_sim_state_{n}.signed_values'
 raise ValueError(f'unexpected V7 word alias: {decl}')
def adapt(source:str,rel:str,plan:dict[str,Any])->tuple[str,dict[str,Any]|None]:
 _plan_eq(plan); rel=Path(rel).as_posix()
 mappings={}
 for t in plan['targets']:
  for d in t['source_declarations']:
   if d['source']==rel:mappings.setdefault(t['symbol'],[]).append((t,d))
 if not mappings:return source,None
 source_hash=plan['source_hashes'].get(rel)
 if not source_hash:raise ValueError(f'V7 source lacks frozen hash: {rel}')
 _fixed(ROOT/rel,source_hash,'source')
 original=(ROOT/rel).read_text(encoding='latin1').splitlines()
 replacements={};removed={}
 for name,rows in sorted(mappings.items()):
  exprs=set()
  for t,d in rows:
   ln=int(d['line'])
   if ln<1 or ln>len(original) or original[ln-1].strip()!=d['text']:raise ValueError(f'V7 declaration changed: {rel}:{ln}:{name}')
   exprs.add(_view(t,d['text']))
  if len(exprs)!=1:raise ValueError(f'V7 conflicting source views {rel}:{name}:{exprs}')
  replacements[name]=next(iter(exprs))
  pat=r'(?m)^[ \t]*extern\s+[^;\r\n]*\b'+re.escape(name)+r'\b[^;\r\n]*;[ \t]*(?:\r?\n|$)'
  source,count=re.subn(pat,'',source)
  if count!=len(rows):raise ValueError(f'V7 generated extern count mismatch {rel}:{name}:{count}/{len(rows)}')
  removed[name]=count
 converted,counts=replace_identifier_tokens(source,replacements)
 if any(counts[n]<1 for n in replacements):raise ValueError(f'V7 selected declaration has no source uses: {rel}:{counts}')
 return '#include "simulation_state_50f6_v7.h"\n'+converted,{'kind':'SOURCE_BOUNDED_SIMULATION_STATE_V7','plan':PLAN_PATH.relative_to(ROOT).as_posix(),'plan_sha256':PLAN_SHA256,'source':rel,'source_sha256':source_hash,'source_views':replacements,'removed_extern_declarations':removed,'rewritten_identifier_tokens':counts,'claim':'Single owner from complete source views and exact S09 SaveRec extents; no gap sizing.'}
