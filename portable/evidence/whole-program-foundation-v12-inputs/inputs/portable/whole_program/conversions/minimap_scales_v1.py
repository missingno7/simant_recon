"""Strict source-pinned owner binding for OpenMiniMapWin's paired scales."""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
from typing import Any
from portable.whole_program.conversions.simulation_state_50f6_preword import replace_identifier_tokens
ROOT=Path(__file__).resolve().parents[3]
PLAN_PATH=ROOT/"portable/research/minimap_scales_v1.json"
PLAN_SHA256="b2e3d6a372f44e2ce4161e5078c4f6a78a03ff76e3bd0a3c3808e4532d5dd0c3"
SOURCE_PATH="src/S04/m35F5.c"
SOURCE_SHA256="65db48855f97c32600ff7527999a463019ba2884117f0c921b35e46d5d37d406"
DECLS={"g_8BD2":"extern int near g_8BD2;","g_8BD4":"extern int near g_8BD4;"}
OWNERS={"g_8BD2":"native_minimap_scale_x_v1","g_8BD4":"native_minimap_scale_y_v1"}
EXPECTED_USES={"g_8BD2":7,"g_8BD4":7}
BRANCH=("if (g_5A97 & 1)\n        g_8BD2 = g_8BD4 = 2;\n    else\n        g_8BD2 = g_8BD4 = 1;")
def _sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def load_plan()->dict[str,Any]:
 raw=PLAN_PATH.read_bytes()
 if _sha(raw)!=PLAN_SHA256:raise ValueError("fixed minimap scales plan identity mismatch")
 p=json.loads(raw.decode("utf-8-sig"))
 if p.get("schema")!="simant-source-assigned-minimap-scales-v1" or p.get("source",{}).get("path")!=SOURCE_PATH or p.get("source",{}).get("sha256")!=SOURCE_SHA256:
  raise ValueError("fixed minimap scale plan fields changed")
 if {x["symbol"]:x["declaration"] for x in p.get("targets",[])}!=DECLS or p.get("owner_names")!=OWNERS or p.get("branch_source")!=BRANCH:
  raise ValueError("fixed minimap scale target/producer changed")
 if p.get("expected_uses")!=EXPECTED_USES:raise ValueError("fixed minimap scale reference counts changed")
 return p
def render_owners(plan:dict[str,Any]|None=None)->tuple[str,str]:
 plan=load_plan() if plan is None else plan
 if plan!=load_plan():raise ValueError("caller-supplied minimap plan differs from fixed plan")
 h=["/* Runtime-assigned native map scale values from S04 OpenMiniMapWin. */","#ifndef SIMANT_MINIMAP_SCALES_V1_H","#define SIMANT_MINIMAP_SCALES_V1_H","#include <stdint.h>"]
 c=['/* One native owner per source near-int scale. */','#include "minimap_scales_v1.h"']
 for n in DECLS:
  h.append(f"extern int16_t {OWNERS[n]};"); c.append(f"int16_t {OWNERS[n]};")
 h.extend(["#endif",""]);c.append("")
 return "\n".join(h),"\n".join(c)
def adapt(source:str|bytes,rel:str,plan:dict[str,Any]|None=None)->tuple[str|bytes,dict[str,Any]|None]:
 if Path(rel).as_posix()!=SOURCE_PATH:raise ValueError(f"unexpected minimap scale source route: {rel}")
 plan=load_plan() if plan is None else plan
 if plan!=load_plan():raise ValueError("caller-supplied minimap plan differs from fixed plan")
 if _sha((ROOT/SOURCE_PATH).read_bytes())!=SOURCE_SHA256:raise ValueError("frozen S04 source identity mismatch")
 raw=source.encode("latin1") if isinstance(source,str) else source
 if _sha(raw)!=SOURCE_SHA256:raise ValueError("input S04 source does not match frozen minimap source")
 text=raw.decode("latin1")
 if text.count(BRANCH)!=1:raise ValueError("expected exact paired OpenMiniMapWin scale producer block")
 removed={}
 for name,decl in DECLS.items():
  pat=re.compile(r"(?m)^"+re.escape(decl)+r"\r?\n")
  text,n=pat.subn("",text)
  if n!=1:raise ValueError(f"expected exactly one exact scale extern for {name}: {n}")
  removed[name]=n
 out,counts=replace_identifier_tokens(text,OWNERS)
 if counts!=EXPECTED_USES:raise ValueError(f"minimap scale references changed: {counts}")
 out='#include "minimap_scales_v1.h"\n'+out
 b=out.encode("latin1")
 ledger={"kind":"SOURCE_ASSIGNED_MINIMAP_SCALES_V1","plan":PLAN_PATH.relative_to(ROOT).as_posix(),"plan_sha256":PLAN_SHA256,
  "source":SOURCE_PATH,"source_sha256":SOURCE_SHA256,"removed_extern_declarations":removed,"owner_views":OWNERS,
  "rewritten_identifier_tokens":counts,"producer_block_sha256":_sha(BRANCH.encode()),"output_sha256":_sha(b),
  "claim":"OpenMiniMapWin source-controlled paired scales use one native int16_t owner each; no historical zero/extent is claimed."}
 return (out if isinstance(source,str) else b),ledger
