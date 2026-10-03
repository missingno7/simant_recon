"""Strict pre-word adapter for a single source-complete S06 simulation grid."""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
from typing import Any
from .simulation_state_50f6_preword import replace_identifier_tokens

ROOT=Path(__file__).resolve().parents[3]
PLAN_PATH=ROOT/'portable/research/whole_program_simulation_grid_3e1d_v8.json'
PLAN_SHA256='35db8eb7e6e6a021bf65d17da85877c51da8b84d1a46b1e76842dd62ff1f19f1'
FROZEN_INPUTS={
 'layout/manifest.json':'025a0a9255d910cae4b122ab5a3f3fb40888bb456d7fe42158db7c9e622fcf50',
 'layout/symbols.json':'0f5dd5b0a211945a97782cfccdb9bb31b0dfd07fcde5df4d4f9486b487eb0125',
}
def _sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def _fixed(path:Path,digest:str,kind:str)->None:
 if not digest or not path.is_file() or _sha(path)!=digest:raise ValueError(f'V8 pinned {kind} changed: {path.relative_to(ROOT).as_posix()}')
def _plan_eq(plan:dict[str,Any])->None:
 _fixed(PLAN_PATH,PLAN_SHA256,'plan')
 if plan!=json.loads(PLAN_PATH.read_text(encoding='utf-8')):raise ValueError('caller V8 plan differs from fixed plan')
def load_plan()->dict[str,Any]:
 _fixed(PLAN_PATH,PLAN_SHA256,'plan')
 plan=json.loads(PLAN_PATH.read_text(encoding='utf-8'))
 if plan.get('schema')!='simant-source-complete-simulation-grid-plan-v8' or plan['target']['extent_bytes']!=8192:raise ValueError('unexpected V8 plan shape')
 for rel,digest in FROZEN_INPUTS.items():_fixed(ROOT/rel,digest,'layout')
 for rel,item in plan['inputs'].items():_fixed(ROOT/rel,item['sha256'],'proposal input')
 return plan
def render_owners(plan:dict[str,Any])->tuple[str,str]:
 _plan_eq(plan)
 t=plan['target']
 h='\n'.join(['/* Source-complete ant occupancy grid owner V8. */','#ifndef SIMANT_SOURCE_BOUNDED_SIMULATION_GRID_V8_H','#define SIMANT_SOURCE_BOUNDED_SIMULATION_GRID_V8_H','#include <stdint.h>','typedef struct NativeSimulationGridV8 { uint8_t cells[128][64]; } NativeSimulationGridV8;','extern NativeSimulationGridV8 native_sim_grid_fd_3E1D_6180;','#endif',''])
 c='\n'.join(['/* Exact fixed-size native S06 simulation grid owner V8. */','#include "simulation_grid_3e1d_v8.h"','NativeSimulationGridV8 native_sim_grid_fd_3E1D_6180;',''])
 if t['symbol']!='fd_3E1D_6180' or t['dimensions']!=[128,64]:raise ValueError('V8 owner definition differs from fixed plan')
 return h,c
def adapt(source:str,rel:str,plan:dict[str,Any])->tuple[str,dict[str,Any]|None]:
 _plan_eq(plan);rel=Path(rel).as_posix();t=plan['target']
 if rel not in {r['source'] for r in plan['source_references']}:return source,None
 source_hash=plan['inputs'][rel]['sha256'] if rel in plan['inputs'] else None
 if not source_hash:raise ValueError(f'V8 source lacks frozen hash: {rel}')
 _fixed(ROOT/rel,source_hash,'source')
 original=(ROOT/rel).read_text(encoding='latin1').splitlines()
 d=t['source_declaration'];line=int(d['line'])
 if line<1 or line>len(original) or original[line-1].strip()!=d['text']:raise ValueError(f'V8 declaration changed: {rel}:{line}')
 name=t['symbol'];pattern=r'(?m)^[ \t]*extern\s+[^;\r\n]*\b'+re.escape(name)+r'\b[^;\r\n]*;[ \t]*(?:\r?\n|$)'
 source,removed=re.subn(pattern,'',source)
 if removed!=1:raise ValueError(f'V8 generated declaration count mismatch: {rel}:{name}:{removed}/1')
 source,counts=replace_identifier_tokens(source,{name:'native_sim_grid_fd_3E1D_6180.cells'})
 if counts[name]!=4:raise ValueError(f'V8 generated access-token count changed: {rel}:{counts[name]}/4')
 return '#include "simulation_grid_3e1d_v8.h"\n'+source,{'kind':'SOURCE_COMPLETE_SIMULATION_GRID_V8','plan':PLAN_PATH.relative_to(ROOT).as_posix(),'plan_sha256':PLAN_SHA256,'source':rel,'source_sha256':source_hash,'symbol':name,'removed_extern_declarations':removed,'rewritten_identifier_tokens':counts[name],'dimensions':[128,64],'extent_bytes':8192,'basis':'complete unsigned char[128][64] declaration; no SaveRec or historical gap claim'}
