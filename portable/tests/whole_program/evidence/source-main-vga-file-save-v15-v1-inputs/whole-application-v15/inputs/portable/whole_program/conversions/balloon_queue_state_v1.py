"""Source-bounded native six-slot owner for root:m0250 balloon queues."""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
from typing import Any
from portable.whole_program.conversions.simulation_state_50f6_preword import replace_identifier_tokens
ROOT=Path(__file__).resolve().parents[3]
PLAN_PATH=ROOT/"portable/research/balloon_queue_state_v1.json"
PLAN_SHA256="68ca74acf270ea733cd93e70e8e36948b73f9cfa7366acf0b3aa651f487929ae"
SOURCE_PATH="src/root/m0250.c"
SOURCE_SHA256="bb8a325c543151e09cb173d2194844877805a9e1058d3b24362ff5a7cbd9f61b"
COUNT_PLAN_PATH=ROOT/"portable/research/whole_program_unprovided_owners_v2.json"
COUNT_PLAN_SHA256="ff91c70e7d1458816e9a10d69945e2d87d0510fd5ebeb4bf8c391028f29229ae"
CAPACITY=6
TYPE_BLOCK="typedef struct {\n    int x;\n    int y;\n} Pnt;\n"
GUARD="if (fd_50F6_1092 >= 6)\n        return;"
PRODUCER_ROWS=(
 "fd_50F6_04C8[fd_50F6_1092].x = style == 10 ? x : g_19BE * x + 8;",
 "fd_50F6_04C8[fd_50F6_1092].y = style == 10 ? y : g_19C0 * y + 8;",
 "fd_50F6_04F6[fd_50F6_1092] = plane;",
 "fd_50F6_04E6[fd_50F6_1092] = style;",
 "fd_50F6_04A6[fd_50F6_1092] = msg;",
)
DECLS={
 "fd_50F6_04A6":"extern char far * far fd_50F6_04A6[];",
 "fd_50F6_04C8":"extern Pnt far fd_50F6_04C8[];",
 "fd_50F6_04E6":"extern int far fd_50F6_04E6[];",
 "fd_50F6_04F6":"extern int far fd_50F6_04F6[];",
}
OWNERS={
 "fd_50F6_04A6":"native_balloon_message_slots_v1",
 "fd_50F6_04C8":"native_balloon_position_slots_v1",
 "fd_50F6_04E6":"native_balloon_style_slots_v1",
 "fd_50F6_04F6":"native_balloon_plane_slots_v1",
}
EXPECTED_USES={"fd_50F6_04A6":4,"fd_50F6_04C8":3,"fd_50F6_04E6":1,"fd_50F6_04F6":2}
def _sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def load_plan()->dict[str,Any]:
 raw=PLAN_PATH.read_bytes()
 if _sha(raw)!=PLAN_SHA256:raise ValueError("fixed balloon queue plan identity mismatch")
 p=json.loads(raw.decode("utf-8-sig"))
 if (p.get("schema")!="simant-source-bounded-balloon-queue-v1" or p.get("source",{}).get("path")!=SOURCE_PATH or
     p.get("source",{}).get("sha256")!=SOURCE_SHA256 or p.get("capacity")!=CAPACITY or
     p.get("producer_guard")!=GUARD or tuple(p.get("producer_rows",()))!=PRODUCER_ROWS or
     {t["symbol"]:t["declaration"] for t in p.get("targets",[])}!=DECLS or p.get("owner_names")!=OWNERS):
  raise ValueError("fixed balloon queue plan fields changed")
 dep=p.get("count_owner_dependency",{})
 if dep.get("path")!=COUNT_PLAN_PATH.relative_to(ROOT).as_posix() or dep.get("sha256")!=COUNT_PLAN_SHA256 or dep.get("symbol")!="fd_50F6_1092":
  raise ValueError("fixed balloon count-owner dependency changed")
 if _sha(COUNT_PLAN_PATH.read_bytes())!=COUNT_PLAN_SHA256:raise ValueError("balloon count-owner plan identity mismatch")
 count_plan=json.loads(COUNT_PLAN_PATH.read_text(encoding="utf-8"))
 if not any(x.get("owner")=="fd_50F6_1092" and x.get("extent_bytes")==2 for x in count_plan.get("bss_owner_candidates",[])):
  raise ValueError("bounded balloon queue count no longer has the reviewed int16 owner")
 if p.get("expected_uses")!=EXPECTED_USES:raise ValueError("fixed balloon queue reference counts changed")
 return p
def render_owners(plan:dict[str,Any]|None=None)->tuple[str,str]:
 plan=load_plan() if plan is None else plan
 if plan!=load_plan():raise ValueError("caller-supplied balloon queue plan differs from fixed plan")
 h=["/* Six source-bounded parallel balloon slots; native pointers keep process lifetime. */",
    "#ifndef SIMANT_BALLOON_QUEUE_STATE_V1_H","#define SIMANT_BALLOON_QUEUE_STATE_V1_H","#include <stdint.h>",
    "typedef struct NativeBalloonPointV1 { int16_t x; int16_t y; } NativeBalloonPointV1;",
    "_Static_assert(sizeof(NativeBalloonPointV1) == 4, \"source Pnt has two Win16 int fields\");",
    "#define Pnt NativeBalloonPointV1"]
 c=["/* Native static storage; capacity is source-guarded, not gap-derived. */",'#include "balloon_queue_state_v1.h"']
 types={"fd_50F6_04A6":"char *","fd_50F6_04C8":"NativeBalloonPointV1","fd_50F6_04E6":"int16_t","fd_50F6_04F6":"int16_t"}
 for symbol in DECLS:
  owner=OWNERS[symbol];typ=types[symbol]
  h.append(f"extern {typ} {owner}[6];");c.append(f"{typ} {owner}[6];")
 h.extend(["#endif",""]);c.append("")
 return "\n".join(h),"\n".join(c)
def adapt(source:str|bytes,rel:str,plan:dict[str,Any]|None=None,original_source:bytes|None=None)->tuple[str|bytes,dict[str,Any]|None]:
 if Path(rel).as_posix()!=SOURCE_PATH:raise ValueError(f"unexpected balloon queue source route: {rel}")
 plan=load_plan() if plan is None else plan
 if plan!=load_plan():raise ValueError("caller-supplied balloon queue plan differs from fixed plan")
 canonical=(ROOT/SOURCE_PATH).read_bytes()
 if _sha(canonical)!=SOURCE_SHA256:raise ValueError("frozen m0250 balloon source identity mismatch")
 raw=source.encode("latin1") if isinstance(source,str) else source
 pinned=raw if original_source is None else original_source
 if _sha(pinned)!=SOURCE_SHA256:raise ValueError("input m0250 source does not match frozen balloon source")
 text=raw.decode("latin1")
 if text.count(TYPE_BLOCK)!=1:raise ValueError("expected exact complete Pnt type definition")
 if text.count(GUARD)!=1:raise ValueError("expected exact six-entry AddMsgBalloon capacity guard")
 for row in PRODUCER_ROWS:
  if text.count(row)!=1:raise ValueError(f"expected one source producer row: {row}")
 consumer=("for (i = 0, shown = 0; i < fd_50F6_1092; i++) {",
           "if (shown >= 1 || fd_50F6_04A6[i] == 0)",
           "pos = fd_50F6_04C8[i];",
           "if (!BalloonIsVisible(fd_50F6_04F6[i], pos.x / g_19BE, pos.y / g_19C0))")
 for snippet in consumer:
  if text.count(snippet)!=1:raise ValueError(f"expected one source balloon consumer expression: {snippet}")
 text=text.replace(TYPE_BLOCK,"",1)
 removed={}
 for n,d in DECLS.items():
  pat=re.compile(r"(?m)^"+re.escape(d)+r"\r?\n")
  text,count=pat.subn("",text)
  if count!=1:raise ValueError(f"expected exactly one exact balloon array extern for {n}: {count}")
  removed[n]=count
 out,counts=replace_identifier_tokens(text,OWNERS)
 if counts!=EXPECTED_USES:raise ValueError(f"balloon queue token counts changed: {counts} expected {EXPECTED_USES}")
 out='#include "balloon_queue_state_v1.h"\n'+out
 b=out.encode("latin1")
 ledger={"kind":"SOURCE_BOUNDED_BALLOON_QUEUE_V1","plan":PLAN_PATH.relative_to(ROOT).as_posix(),"plan_sha256":PLAN_SHA256,
  "source":SOURCE_PATH,"source_sha256":SOURCE_SHA256,"capacity":CAPACITY,"capacity_basis":"AddMsgBalloon >=6 early return plus same-index writes; existing count owner increments after writes",
  "count_owner_dependency_sha256":COUNT_PLAN_SHA256,"removed_extern_declarations":removed,"owner_views":OWNERS,
  "rewritten_identifier_tokens":counts,"native_pointer_extent_claim":"source-bounded six entries; native pointers use host pointer width",
  "output_sha256":_sha(b),"claim":"All four source parallel arrays share six source-guarded rows for one process lifetime; no historical gap/OMF owner is inferred."}
 return (out if isinstance(source,str) else b),ledger
