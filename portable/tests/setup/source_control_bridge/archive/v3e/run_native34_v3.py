#!/usr/bin/env python3
"""Pinned v3 bridge replay with ownership, reentrancy, cap and abort controls."""
from __future__ import annotations
import argparse,ctypes as ct,hashlib,json,subprocess,sys
import shlex
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
DOS=ROOT/"portable/tests/setup/control_events/evidence/dos-control-events.json"
PAIR=ROOT/"portable/tests/setup/control_events/evidence/paired-control-events.json"
GEN=HERE/"source_control_events_extracted.c"
EXTRACTOR=HERE/"extract_control_events.py"
HEADER=HERE/"source_control_integration.h"
FIXTURE=HERE/"native_fixture_v3.c"
BRIDGE=HERE/"source_control_integration_v3.c"
NEXT=ROOT/"build/workers/recovered_source_next10/generated"
SOURCES=[GEN,BRIDGE,FIXTURE,NEXT/"recovered_state.c",NEXT/"root_m0798_controls.c",ROOT/"portable/game/simulation/setup.c"]
GCC=Path("C:/msys64/mingw64/bin/gcc.exe")
DLL=HERE/"source_control_native_v3.dll"
RUNNER=HERE/"run_native34_v3.py"
BASE=ROOT/"src/root/m0798.c"
WORD=ROOT/"portable/tools/word_spelling.py"
TRANSFORM=ROOT/"portable/tools/recover_source.py"
PROVENANCE=NEXT/"provenance.json"
REPORT_DIR=HERE/"evidence"

class Result(ct.Structure):
    _fields_=[("status",ct.c_int32),("automatic",ct.c_int16),("selector",ct.c_int16),("percent",ct.c_int16),
      ("current",ct.c_uint16*3),("presets",ct.c_uint16*12),("ideal_caste",ct.c_int16*4),("point",ct.c_int16*2),
      ("unrelated_auto",ct.c_int16),("unrelated_selector",ct.c_int16),("unrelated_percent",ct.c_int16),
      ("unrelated_current",ct.c_uint16*3),("unrelated_presets",ct.c_uint16*12),("unrelated_point",ct.c_int16*2),
      ("reentrant_attempted",ct.c_int),("reentrant_status",ct.c_int),
      ("event_count",ct.c_int),("events",(ct.c_int32*9)*64)]

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def tools()->dict[str,Path]:
    result={"gcc":GCC,"python":Path(sys.executable)}
    for n in ("cc1","collect2","as","ld"):
        s=subprocess.run([str(GCC),f"-print-prog-name={n}"],capture_output=True,text=True,check=True).stdout.strip()
        p=Path(s)
        if not p.is_absolute():p=(GCC.parent/p).resolve()
        result[n]=p
    return result
def pins(paths):return {str(p.relative_to(ROOT)).replace("\\","/"):sha(p) for p in paths}
def compiler_pins():return {k:{"path":str(v.resolve()),"sha256":sha(v)} for k,v in tools().items()}
def native_events(rows):
    out=[]
    for row in rows:
        op,a,b,c,d,e,f,g,h=row
        if op==1:x={"provider":"clip_set","args":[a]}
        elif op==2:x={"provider":"clip_off","args":[]}
        elif op==3:x={"provider":"help","args":[a]}
        elif op in (4,5):x={"provider":"group_invisible" if op==4 else "group_visible","args":[a,b],"visible":bool(c)}
        elif op==6:x={"provider":"select","args":[a]}
        elif op==7:x={"provider":"get_rect","object":a,"rect":[b,c,d,e]}
        elif op==8:x={"provider":"draw","args":[b],"kind":"caste" if a else "mode","flags":b,"percent":c,"current":[d,e,f],"selector":g,"auto":h}
        elif op==9:x={"provider":"pointer_poll","point":[a,b]}
        elif op==10:x={"provider":"still_down","down":a}
        else:raise RuntimeError(f"unknown provider record {op}")
        out.append(x)
    return out
def expected_events(row):
    x=list(row["callback_order"])
    base=0x1200 if row["kind"]=="mode" else 0x1300
    if row["code"]==base+13:x.insert(1,{"provider":"get_rect","object":base+13,"rect":row["snapshot"]["actual_triangle_rect"]})
    return x
def make_closure():
    cmd=[str(GCC),"-MM","-MT","source_control_dependency_scan","-std=c11","-I",".","-I","portable","-I","build/workers/recovered_source_next10/generated",
         *(str(p.relative_to(ROOT)).replace("\\","/") for p in SOURCES)]
    raw=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,check=True).stdout.replace("\\\n"," ")
    deps=[]
    for line in raw.splitlines():
        if ":" not in line:continue
        rhs=line.split(":",1)[1]
        for token in shlex.split(rhs):
            p=(ROOT/token).resolve()
            if p.is_file() and p not in deps:deps.append(p)
    return sorted(deps,key=lambda p:str(p).lower()),raw
def compile_native():
    flags=["-std=c11","-Wall","-Wextra","-Werror","-Wno-implicit-fallthrough","-Wno-sign-compare",
      "-O2","-ffunction-sections","-fdata-sections","-shared","-Wl,--gc-sections","-I",".","-I","portable",
      "-I","build/workers/recovered_source_next10/generated"]
    subprocess.run([str(GCC),*flags,"-o",str(DLL),*(str(p) for p in SOURCES)],cwd=ROOT,check=True)
    lib=ct.CDLL(str(DLL));fn=lib.source_control_native_run
    i16p=ct.POINTER(ct.c_int16);u16p=ct.POINTER(ct.c_uint16)
    fn.argtypes=[ct.c_int,ct.c_uint16,ct.c_int16,ct.c_int16,ct.c_int16,i16p,u16p,i16p,i16p,i16p,
      ct.c_int,ct.c_int,ct.c_int,ct.c_uint16,ct.c_int,ct.c_int,ct.POINTER(Result)]
    fn.restype=ct.c_int
    return fn,flags
def invoke(fn,row,fail_op=0,fail_nth=0,drag_cap=0,reentrant=0,outer_interrupt_op=0):
    rect=(ct.c_int16*4)(*row["snapshot"]["actual_triangle_rect"])
    metrics=(ct.c_uint16*3)(*row["snapshot"]["shared_triangle_metrics"])
    initial=(ct.c_int16*2)(*row["initial_point"]);point=(ct.c_int16*2)(*row["initial_control_point"])
    vals=[v for p in row["cursor_samples"] for v in p];samples=(ct.c_int16*max(1,len(vals)))(*(vals or [0]))
    r=Result();kind=int(row["kind"]=="caste")
    rc=fn(kind,row["code"],-1 if row["start_auto"] is None else row["start_auto"],row["start_selector"],row["start_percent"],
      rect,metrics,initial,point,samples,len(row["cursor_samples"]),fail_op,fail_nth,drag_cap,reentrant,outer_interrupt_op,ct.byref(r))
    if rc:raise RuntimeError(f"native fixture setup failed {rc}")
    return {"status":r.status,"auto":r.automatic,"selector":r.selector,"percent":r.percent,"current":list(r.current),
      "presets":list(r.presets),"ideal_caste":list(r.ideal_caste),"point":list(r.point),"provider_events":native_events(r.events[:r.event_count]),
      "unrelated":{"auto":r.unrelated_auto,"selector":r.unrelated_selector,"percent":r.unrelated_percent,
       "current":list(r.unrelated_current),"presets":list(r.unrelated_presets),"point":list(r.unrelated_point)},
      "reentrant_attempted":r.reentrant_attempted,"reentrant_status":r.reentrant_status}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--report",type=Path,required=True);args=ap.parse_args()
    out=args.report if args.report.is_absolute() else ROOT/args.report
    if out.exists():raise FileExistsError(f"write-once output exists: {out}")
    if DLL.exists():raise FileExistsError(f"write-once build output exists: {DLL}")
    out.parent.mkdir(parents=True,exist_ok=True)
    extraction=json.loads(subprocess.run([sys.executable,str(EXTRACTOR)],cwd=ROOT,capture_output=True,text=True,check=True).stdout)
    inputpaths=[BASE,WORD,TRANSFORM,EXTRACTOR,GEN,BRIDGE,HEADER,FIXTURE,DOS,PAIR,PROVENANCE,
                NEXT/"recovered_state.h",RUNNER,*SOURCES]
    closure_before,make_before=make_closure()
    inputpaths.extend(closure_before)
    before={"files":pins(inputpaths),"compiler_tools":compiler_pins()}
    fn,flags=compile_native()
    dos=json.loads(DOS.read_text(encoding="utf-8"));pair=json.loads(PAIR.read_text(encoding="utf-8"))
    if dos.get("status")!="DIRECT_ORIGINAL_HANDLER_EXECUTION" or pair.get("case_count")!=34:
        raise RuntimeError("pinned direct DOS and paired-34 corpora unavailable")
    cases=[];diffs=[]
    unrelated_failures=[]
    for row in dos["cases"]:
        n=invoke(fn,row);s=row["snapshot"]
        expected={"status":0,"auto":s["auto"],"selector":s["selector"],"percent":s["percent"],"current":s["current"],
          "presets":s["presets"],"ideal_caste":s["ideal_caste"],
          "point":row["source_draw_point_projection"] if row["source_draw_point_projection"] is not None else s["level_point"],
          "provider_events":expected_events(row)}
        bad=[{"field":k,"expected":v,"actual":n[k]} for k,v in expected.items() if n[k]!=v]
        cases.append({"kind":row["kind"],"code":row["code"],"native":n,"expected_dos":expected,"mismatches":bad})
        if bad:diffs.append({"kind":row["kind"],"code":row["code"],"diff":bad})
        u=n["unrelated"]
        expected_u=(dict(auto=77,selector=3,percent=77,current=[0x1357,0x2468,0x369a],presets=list(range(0xa100,0xa10c)),point=[-123,321])
                    if row["kind"]=="mode" else
                    dict(auto=66,selector=2,percent=66,current=[0x1020,0x3040,0x5060],presets=list(range(0xb200,0xb20c)),point=[-234,432]))
        if u!=expected_u:unrelated_failures.append({"kind":row["kind"],"code":row["code"],"expected":expected_u,"actual":u})
    # Force the source fallthrough after a preset switch to fail at the host
    # visibility provider. The updated selector/level/Auto fields must remain,
    # callbacks after the failed boundary must not run, and a later call works.
    frow=next(x for x in dos["cases"] if x["kind"]=="mode" and x["code"]==0x1208)
    failed=invoke(fn,frow,5,1)
    failed_check={"status":5,"auto":0,"selector":2,"current":[0,0xffff,0],
        "last_provider":"group_visible","no_clip_off":not any(e["provider"]=="clip_off" for e in failed["provider_events"])}
    group_failure_pass=(failed["status"]==5 and failed["auto"]==0 and failed["selector"]==2 and
       failed["current"]==failed_check["current"] and failed["provider_events"][-1]["provider"]=="group_visible" and failed_check["no_clip_off"])
    draw_failed=invoke(fn,frow,8,1)
    draw_failure_pass=(draw_failed["status"]==5 and draw_failed["auto"]==1 and
       draw_failed["selector"]==2 and draw_failed["current"]==[0,0xffff,0] and
       draw_failed["provider_events"][-1]["provider"]=="draw" and
       not any(e["provider"]=="group_visible" for e in draw_failed["provider_events"]) and
       not any(e["provider"]=="clip_off" for e in draw_failed["provider_events"]))
    recovery=invoke(fn,next(x for x in dos["cases"] if x["kind"]=="mode" and x["code"]==0x1203))
    recovery_pass=recovery["status"]==0 and recovery["provider_events"][-1]["provider"]=="clip_off"
    failure_pass=group_failure_pass and draw_failure_pass and recovery_pass
    reentry=invoke(fn,next(x for x in dos["cases"] if x["kind"]=="mode" and x["code"]==0x1203),reentrant=1)
    reentry_pass=(reentry["status"]==0 and reentry["reentrant_attempted"]==1 and reentry["reentrant_status"]==1)
    drag_row=next(x for x in dos["cases"] if x["kind"]=="mode" and x["code"]==0x120d and len(x["cursor_samples"])==2)
    capped=invoke(fn,drag_row,drag_cap=1)
    cap_pass=(capped["status"]==6 and sum(e["provider"]=="pointer_poll" for e in capped["provider_events"])==1)
    outer=invoke(fn,next(x for x in dos["cases"] if x["kind"]=="mode" and x["code"]==0x1203),outer_interrupt_op=1)
    post_outer=invoke(fn,next(x for x in dos["cases"] if x["kind"]=="mode" and x["code"]==0x1203))
    outer_pass=(outer["status"]==100 and len(outer["provider_events"])==1 and post_outer["status"]==0 and
                post_outer["provider_events"][-1]["provider"]=="clip_off")
    closure_after,make_after=make_closure()
    after={"files":pins(inputpaths),"compiler_tools":compiler_pins()}
    if [str(p) for p in closure_before]!=[str(p) for p in closure_after] or pins(closure_before)!=pins(closure_after):
        raise RuntimeError("GCC -MM local dependency closure changed during run")
    if before!=after:raise RuntimeError("integration compile/run inputs changed")
    report={"schema":"source-control-integration-native34-v3","status":"PASS" if not diffs and failure_pass and not unrelated_failures and reentry_pass and cap_pass and outer_pass else "MISMATCH",
      "case_count":len(cases),"mismatch_count":len(diffs),"cases":cases,"mismatches":diffs,
      "unrelated_kind_sentinel_failures":unrelated_failures,
      "failure_controls":[{"case":"mode 0x1208; fail first group_visible callback","result":failed,"asserted":failed_check,"passed":group_failure_pass},
        {"case":"mode 0x1208; fail first draw callback","result":draw_failed,"passed":draw_failure_pass}],
      "post_failure_recovery":{"status":recovery["status"],"final_provider":recovery["provider_events"][-1]["provider"],"passed":recovery_pass},
      "reentrancy_control":{"result":reentry,"passed":reentry_pass},
      "explicit_finite_drag_cap":{"result":capped,"expected_status":6,"passed":cap_pass},
      "outer_abort_cleanup_control":{"interrupted_result":outer,"fresh_followup":post_outer,"passed":outer_pass,
       "mechanism":"fixture performs external longjmp from clip provider; catcher invokes sim_recovered_source_control_abort_cleanup then recovered_bind_end, followed by fresh source event"},
      "mechanical_extraction":extraction,"input_pins_before":before,"input_pins_after":after,
      "native_dll_sha256":sha(DLL),"compile_flags":flags,
      "gcc_mm_local_header_closure":{"before":{"files":pins(closure_before),"raw":make_before},"after":{"files":pins(closure_after),"raw":make_after}},
      "actual_next10_binding":{"state_header_sha256":sha(NEXT/"recovered_state.h"),"state_source_sha256":sha(NEXT/"recovered_state.c"),
        "root_m0798_controls_sha256":sha(NEXT/"root_m0798_controls.c"),"provenance_sha256":sha(PROVENANCE),
        "bind_calls":"native_fixture calls recovered_bind_begin/recovered_bind_end around every adapter invocation"},
      "state_ownership":"selectors are pointers directly into SimSetupControls; percentage words are pointers directly into caller SimControlEventPrivateState; other source mutable fields are the active RecoveredState TLS. Callback publication copies only selected-window fields; IdealCaste is published only for caste.",
      "limits":["Uses retained DOS 34-case data, not a fresh DOS execution.","DrawMode/Caste implementations remain explicit host draw leaves; SetTriLatPoint and cvtLevels2IdealCaste are actual Next10 root:m0798 compiled dependencies.","The optional max_drag_samples provider value bounds polling when nonzero; zero retains source's unbounded loop as specified by provider API.","Outer interruption cleanup is exercised in fixture but engine integration remains a separate change.","Unselected Next10 m0798 leaves are stubbed in the fixture and are not called by this corpus/control set."]}
    with out.open("x",encoding="utf-8",newline="") as f:f.write(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"status":report["status"],"cases":len(cases),"mismatches":len(diffs),"provider_failure":failure_pass,"report":str(out.relative_to(ROOT))},indent=2))
    if report["status"]!="PASS":raise SystemExit(1)
if __name__=="__main__":main()
