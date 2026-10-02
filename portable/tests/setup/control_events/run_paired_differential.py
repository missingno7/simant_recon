#!/usr/bin/env python3
"""Pair native control-event adapter results with the direct DOS probe."""
from __future__ import annotations

import ctypes as ct
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
DOS_REPORT = HERE / "evidence/dos-control-events.json"
OUT = HERE / "evidence/paired-control-events.json"
GCC = Path("C:/msys64/mingw64/bin/gcc.exe")
DLL = ROOT / "build/workers/control_events_native_adapter.dll"
SOURCE = ROOT / "portable/tests/setup/control_events/native_adapter.c"

OP_NAMES = {1:"clip_set",2:"clip_off",3:"help",4:"group_invisible",
            5:"group_visible",6:"select",7:"get_rect",8:"draw",
            9:"pointer_poll",10:"still_down"}
PINNED_PATHS = [
    "portable/ui_model/windows/control_events.c",
    "portable/ui_model/windows/control_events.h",
    "portable/game/simulation/setup.c",
    "portable/game/simulation/setup.h",
    "portable/tests/setup/control_events/native_adapter.c",
    "portable/tests/setup/control_events/test_control_events.c",
    "portable/tests/setup/control_events/run_dos_probe.py",
    "portable/tests/setup/control_events/run_paired_differential.py",
    "portable/tests/setup/evidence/setup_differential.py",
    "portable/tests/windows/evidence/differential_window.py",
    "portable/tests/setup/evidence/setup_native_adapter.c",
    "tools/behavior.py","tools/exe.py","tools/functions.py","tools/match.py",
    "tools/modctx.py","tools/modules.py","tools/compiler.py","tools/autosearch.py",
    "tools/symbols.py","layout/manifest.json","layout/functions.json",
    "layout/symbols.json","assets/SIMANT.EXE","assets/HCEGANT.NDX",
    "assets/HCEGANT.DAT","src/root/m0798.c",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def pins() -> dict[str,str]:
    return {name:sha(ROOT/name) for name in PINNED_PATHS}


def compile_adapter() -> str:
    subprocess.run([str(GCC), "-std=c11", "-Wall", "-Wextra", "-Werror",
                    "-shared", "-I", str(ROOT / "portable"), str(SOURCE),
                    str(ROOT / "portable/ui_model/windows/control_events.c"),
                    str(ROOT / "portable/game/simulation/setup.c"), "-o", str(DLL)],
                   cwd=ROOT, check=True)
    return sha(DLL)


def setup_library():
    lib = ct.CDLL(str(DLL))
    fn = lib.control_event_native_run
    i16p = ct.POINTER(ct.c_int16)
    u16p=ct.POINTER(ct.c_uint16)
    fn.argtypes = [ct.c_int,ct.c_int,ct.c_int,ct.c_int,ct.c_int,
                   i16p,u16p,i16p,i16p,i16p,ct.c_int,
                   ct.POINTER(ct.c_int32)]
    fn.restype = ct.c_int
    return fn


def invoke(fn, row: dict, shared_metrics: list[int]) -> dict:
    is_mode = row["kind"] == "mode"
    rect = (ct.c_int16 * 4)(*row["snapshot"]["actual_triangle_rect"])
    metrics = (ct.c_uint16 * 3)(*shared_metrics)
    point = (ct.c_int16 * 2)(*row["initial_point"])
    control_point = (ct.c_int16 * 2)(*initial_point(row["kind"],row["snapshot"]["actual_triangle_rect"],
                                                    shared_metrics))
    samples_flat = [v for sample in row["cursor_samples"] for v in sample]
    samples = (ct.c_int16 * max(1,len(samples_flat)))(*(samples_flat or [0]))
    result = (ct.c_int32 * 640)()
    count = fn(int(not is_mode),row["code"],
               -1 if row["start_auto"] is None else row["start_auto"],
               row["start_selector"],row["start_percent"],
               rect,metrics,point,control_point,samples,
               len(row["cursor_samples"]),result)
    if count < 26:
        raise RuntimeError(f"native adapter returned short result ({count})")
    auto, selector, percent = result[1:4]
    current = list(result[4:7])
    presets = list(result[7:19])
    ideal = list(result[19:23])
    control_point = list(result[23:25])
    op_count = result[25]
    native_ops=[]
    at=26
    for _ in range(op_count):
        op,a,b,c,d,e,f,g,h=result[at:at+9];at+=9
        name=OP_NAMES[op]
        if name=="clip_set": event={"provider":name,"args":[a]}
        elif name=="clip_off": event={"provider":name,"args":[]}
        elif name=="help": event={"provider":name,"args":[a]}
        elif name in ("group_visible","group_invisible"):
            event={"provider":name,"args":[a,b],"visible":bool(c)}
        elif name=="select": event={"provider":name,"args":[a]}
        elif name=="get_rect": event={"provider":name,"object":a,"rect":[b,c,d,e]}
        elif name=="draw": event={"provider":name,"args":[b],"kind":"mode" if a==0 else "caste",
            "flags":b,"percent":c,"current":[d,e,f],"selector":g,"auto":h}
        elif name=="pointer_poll": event={"provider":name,"point":[a,b]}
        elif name=="still_down": event={"provider":name,"down":a}
        else: raise RuntimeError(f"unhandled native provider {name}")
        native_ops.append(event)
    return {"auto":auto,"selector":selector,"percent":percent,
            "current":current,"presets":presets,"ideal_caste":ideal,
            "point":control_point,"provider_events":native_ops}


def initial_point(kind: str, rect: list[int], metrics: list[int]) -> list[int]:
    frac, mid, weight = ((0x9999,0x3333,0x3333) if kind=="mode"
                         else (0,0x9999,0x6666))
    width=rect[2]-rect[0]; height=rect[3]-rect[1]
    half=width//2
    # InitTriVars computes each window's initial dot before the other
    # window replaces the TU-shared triangle metrics.
    used_width=width; used_half=half; used_height=height
    w=used_half*frac//0xffff
    row=used_width-2*w
    y=(used_height-2)*(0xffff-frac)//0xffff+rect[1]
    if frac==0xffff or row<3:
        x=rect[0]+half+2
    else:
        x=(row-3)*weight//(0xffff-frac)+rect[0]+w+2
    return [x,y]


def dos_events(row: dict) -> list[dict]:
    order = [dict(call) for call in row["callback_order"]]
    base=0x1200 if row["kind"]=="mode" else 0x1300
    if row["code"]==base+13:
        order.insert(1,{"provider":"get_rect","object":base+13,
                        "rect":row["snapshot"]["actual_triangle_rect"]})
    return order


def compare(row: dict, native: dict) -> list[dict]:
    source=row["snapshot"]
    expected_point=(row["source_draw_point_projection"]
                    if row["source_draw_point_projection"] is not None
                    else source["level_point"])
    pairs={"auto":source["auto"],"selector":source["selector"],
           "percent":source["percent"],"current":source["current"],
           "presets":source["presets"],"ideal_caste":source["ideal_caste"],
           "point":expected_point,"provider_events":dos_events(row)}
    return [{"field":field,"dos":expected,"native":native[field]}
            for field,expected in pairs.items() if expected!=native[field]]


def main() -> None:
    before=pins()
    dos=json.loads(DOS_REPORT.read_text(encoding="utf-8"))
    if dos.get("status")!="DIRECT_ORIGINAL_HANDLER_EXECUTION":
        raise RuntimeError("direct original DOS report is not an execution receipt")
    dll_hash=compile_adapter()
    native_fn=setup_library()
    caste_rect=dos["control_geometry"]["caste_object_13"]
    shared_metrics=[caste_rect[2]-caste_rect[0],caste_rect[3]-caste_rect[1],
                    (caste_rect[2]-caste_rect[0])//2]
    cases=[]; mismatches=[]
    for row in dos["cases"]:
        if row["snapshot"]["shared_triangle_metrics"]!=shared_metrics:
            raise RuntimeError("DOS shared InitTriVars metrics disagree with independent startup geometry derivation")
        native=invoke(native_fn,row,shared_metrics)
        diff=compare(row,native)
        cases.append({"kind":row["kind"],"code":row["code"],
                      "native":native,"dos_provider_events":dos_events(row),
                      "dos_snapshot":row["snapshot"],"mismatches":diff})
        if diff:mismatches.append({"kind":row["kind"],"code":row["code"],"diff":diff})
    after=pins()
    if before!=after:
        raise RuntimeError("transitive source/harness pins changed during paired run")
    compiler=subprocess.run([str(GCC),"--version"],check=True,text=True,
                            capture_output=True).stdout.splitlines()[0]
    report={"schema":"portable-setup-control-events-paired-differential-v1",
        "status":"PASS" if not mismatches else "MISMATCH",
        "dos_report_sha256":sha(DOS_REPORT),"native_adapter_sha256":sha(SOURCE),
        "oracle_sha256":dos["original_oracle_sha256"],
        "original_source_sha256":dos["source_sha256"],
        "original_fixture_runner_sha256":dos["fixture_runner_sha256"],
        "native_adapter_dll_sha256":dll_hash,
        "native_model_sha256":sha(ROOT/"portable/ui_model/windows/control_events.c"),
        "native_header_sha256":sha(ROOT/"portable/ui_model/windows/control_events.h"),
        "native_test_sha256":sha(ROOT/"portable/tests/setup/control_events/test_control_events.c"),
        "native_differential_runner_sha256":sha(Path(__file__)),
        "case_count":len(cases),"mismatch_count":len(mismatches),
        "compiler":{"version":compiler,"flags":["-std=c11","-Wall","-Wextra","-Werror","-shared"]},
        "transitive_source_pins_before":before,"transitive_source_pins_after":after,
        "transitive_source_pins_stable":before==after,
        "compared_fields":["auto","selector","percent","current levels",
            "all four preset rows","IdealCaste","source SetTriLatPoint result",
            "ordered host provider boundary calls"],
        "provider_boundary":dos["provider_boundary"],
        "common_geometry_input": {"mode_object_13":dos["control_geometry"]["mode_object_13"],
            "caste_object_13":caste_rect,"shared_metrics_derived_from_startup_caste_object":shared_metrics,
            "derivation":"initControls invokes ModeControlChanged then CasteControlChanged; InitTriVars leaves its shared metrics from the last (caste) object; independently derived here from the same loaded window records"},
        "limitations":["DOS DrawModeWindow/DrawCasteWindow are represented by provider sinks; after those sinks the direct original SetTriLatPoint body is run to capture the exact source point projection",
            "screen pixels and host window side effects are outside this event-state contract",
            "admitted drag domain is the loaded HCEGANT profile-0 triangle geometry; arbitrary corrupt rectangles are not covered"],
        "cases":cases,"mismatches":mismatches}
    OUT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"report":str(OUT.relative_to(ROOT)),"status":report["status"],
                      "cases":len(cases),"mismatches":len(mismatches)},indent=2))
    if mismatches: raise SystemExit(1)


if __name__=="__main__":main()
