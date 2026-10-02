#!/usr/bin/env python3
"""Compile the isolated fixed-width m0798 extraction and pair it to the DOS corpus."""
from __future__ import annotations
import ctypes as ct
import argparse, hashlib, json, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
DOS=ROOT/"portable/tests/setup/control_events/evidence/dos-control-events.json"
PAIRED=ROOT/"portable/tests/setup/control_events/evidence/paired-control-events.json"
GCC=Path("C:/msys64/mingw64/bin/gcc.exe")
DLL=ROOT/"build/workers/source_control_events_extracted_v2.dll"
SRC=HERE/"source_control_events.c"
HDR=HERE/"source_control_events.h"
EXTRACT=HERE/"extract_m0798_v2.py"
EXTRACTED=HERE/"m0798_extracted_v2.c"
SRC_ORIG=ROOT/"src/root/m0798.c"
RECOVER=ROOT/"portable/tools/recover_source.py"
COMPILER_NAMES=("cc1","collect2","as","ld")

class Result(ct.Structure):
    _fields_=[("automatic",ct.c_int16),("selector",ct.c_int16),("percent",ct.c_int16),
        ("current",ct.c_uint16*3),("presets",ct.c_uint16*12),
        ("ideal_caste",ct.c_int16*4),("point",ct.c_int16*2),
        ("event_count",ct.c_int),("events",(ct.c_int32*9)*64)]

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def tool_paths()->dict[str,Path]:
    found={"gcc":GCC,"python":Path(sys.executable)}
    for name in COMPILER_NAMES:
        text=subprocess.run([str(GCC),f"-print-prog-name={name}"],cwd=ROOT,check=True,capture_output=True,text=True).stdout.strip()
        path=Path(text)
        if not path.is_absolute():path=(GCC.parent/path).resolve()
        if not path.is_file():raise RuntimeError(f"compiler subtool {name} missing: {path}")
        found[name]=path
    return found
def pathpins(paths:dict[str,Path])->dict[str,dict[str,str]]:
    return {name:{"path":str(path.resolve()),"sha256":sha(path)} for name,path in paths.items()}
def eventify(rows, row):
    out=[]
    for e in rows:
        op,a,b,c,d,ee,f,g,h=e
        if op==1:v={"provider":"clip_set","args":[a]}
        elif op==2:v={"provider":"clip_off","args":[]}
        elif op==3:v={"provider":"help","args":[a]}
        elif op in (4,5):v={"provider":"group_invisible" if op==4 else "group_visible","args":[a,b],"visible":bool(c)}
        elif op==6:v={"provider":"select","args":[a]}
        elif op==7:v={"provider":"get_rect","object":a,"rect":[b,c,d,ee]}
        elif op==8:v={"provider":"draw","args":[b],"kind":"caste" if a else "mode","flags":b,
            "percent":c,"current":[d,ee,f],"selector":g,"auto":h}
        elif op==9:v={"provider":"pointer_poll","point":[a,b]}
        elif op==10:v={"provider":"still_down","down":a}
        else:raise ValueError(f"unknown event op {op}")
        out.append(v)
    return out

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--report",required=True,type=Path,help="new report path; existing paths are never overwritten")
    args=parser.parse_args()
    out=args.report if args.report.is_absolute() else ROOT/args.report
    if out.exists():raise FileExistsError(f"write-once report already exists: {out}")
    out.parent.mkdir(parents=True,exist_ok=True)
    tools=tool_paths()
    extraction=json.loads(subprocess.run([sys.executable,str(EXTRACT)],cwd=ROOT,check=True,capture_output=True,text=True).stdout)
    before={"source":sha(SRC),"header":sha(HDR),"extractor":sha(EXTRACT),"extractor_library":sha(RECOVER),"runner":sha(Path(__file__)),"extracted":sha(EXTRACTED),"original":sha(SRC_ORIG),"dos":sha(DOS),"paired":sha(PAIRED),"toolchain":pathpins(tools)}
    flags=["-std=c11","-Wall","-Wextra","-Werror","-Wno-implicit-fallthrough","-Wno-sign-compare","-shared"]
    subprocess.run([str(GCC),*flags,"-o",str(DLL),str(SRC),str(EXTRACTED)],cwd=ROOT,check=True)
    lib=ct.CDLL(str(DLL)); fn=lib.source_control_event_run
    i16p=ct.POINTER(ct.c_int16);u16p=ct.POINTER(ct.c_uint16)
    fn.argtypes=[ct.c_int,ct.c_uint16,ct.c_int16,ct.c_int16,ct.c_int16,i16p,u16p,i16p,i16p,i16p,ct.c_int,ct.POINTER(Result)]
    fn.restype=ct.c_int
    dos=json.loads(DOS.read_text(encoding="utf-8")); old=json.loads(PAIRED.read_text(encoding="utf-8"))
    if dos.get("status")!="DIRECT_ORIGINAL_HANDLER_EXECUTION" or old.get("case_count")!=34:
        raise RuntimeError("required immutable direct-DOS/paired-34 corpus missing")
    cases=[];mismatches=[]
    for row in dos["cases"]:
        rect=(ct.c_int16*4)(*row["snapshot"]["actual_triangle_rect"])
        metrics=(ct.c_uint16*3)(*row["snapshot"]["shared_triangle_metrics"])
        ip=(ct.c_int16*2)(*row["initial_point"]);cp=(ct.c_int16*2)(*row["initial_control_point"])
        flat=[v for pt in row["cursor_samples"] for v in pt]
        samples=(ct.c_int16*max(1,len(flat)))(*(flat or [0])); got=Result()
        kind=int(row["kind"]=="caste")
        status=fn(kind,row["code"],-1 if row["start_auto"] is None else row["start_auto"],row["start_selector"],row["start_percent"],rect,metrics,ip,cp,samples,len(row["cursor_samples"]),ct.byref(got))
        if status:raise RuntimeError(f"source fixture failed {row['kind']} {row['code']:04x}: {status}")
        native={"auto":got.automatic,"selector":got.selector,"percent":got.percent,
            "current":list(got.current),"presets":list(got.presets),"ideal_caste":list(got.ideal_caste),
            "point":list(got.point),"provider_events":eventify(got.events[:got.event_count],row)}
        snap=row["snapshot"]
        expected={"auto":snap["auto"],"selector":snap["selector"],"percent":snap["percent"],
            "current":snap["current"],"presets":snap["presets"],"ideal_caste":snap["ideal_caste"],
            "point":row["source_draw_point_projection"] if row["source_draw_point_projection"] is not None else snap["level_point"],
            "provider_events":list(row["callback_order"])}
        # GetObjRect is a real source call intercepted by the direct-DOS lane,
        # so it is projected beside that lane's callback trace.
        if row["code"]==(0x1200 if row["kind"]=="mode" else 0x1300)+13:
            expected["provider_events"].insert(1,{"provider":"get_rect","object":
                (0x1200 if row["kind"]=="mode" else 0x1300)+13,
                "rect":row["snapshot"]["actual_triangle_rect"]})
        diff=[{"field":k,"dos":v,"native":native[k]} for k,v in expected.items() if native[k]!=v]
        cases.append({"kind":row["kind"],"code":row["code"],"native":native,"dos_expected":expected,"mismatches":diff})
        if diff:mismatches.append({"kind":row["kind"],"code":row["code"],"diff":diff})
    after={"source":sha(SRC),"header":sha(HDR),"extractor":sha(EXTRACT),"extractor_library":sha(RECOVER),"runner":sha(Path(__file__)),"extracted":sha(EXTRACTED),"original":sha(SRC_ORIG),"dos":sha(DOS),"paired":sha(PAIRED),"toolchain":pathpins(tools)}
    if before!=after:raise RuntimeError("input pins changed during extraction comparison")
    compiler=subprocess.run([str(GCC),"--version"],capture_output=True,text=True,check=True).stdout.splitlines()[0]
    report={"schema":"source-extracted-control-events-paired-34-v2","status":"PASS" if not mismatches else "MISMATCH",
      "case_count":len(cases),"mismatch_count":len(mismatches),"cases":cases,"mismatches":mismatches,
      "input_pins_before":before,"input_pins_after":after,"native_dll_sha256":sha(DLL),
      "compiler":{"version":compiler,"python_version":sys.version,"flags":flags,"tools":before["toolchain"]},
      "mechanical_extraction":extraction,
      "body_origins":{"ProcCasteEvent":"src/root/m0798.c:130-196","ProcModeEvent":"src/root/m0798.c:198-259",
        "IsPointInIsoTri":"src/root/m0798.c:261-285","BoundPointToTri":"src/root/m0798.c:287-322",
        "GetTriLatDist":"src/root/m0798.c:468-493","SetTriLatPoint":"src/root/m0798.c:495-510"},
      "conversion":"The seven named C function bodies are mechanically extracted from frozen root:m0798.c and passed through recover_source.transform. A target-specific lexical pass maps the DOS default-int spelling unsigned to uint16_t outside comments/literals. Window, clip, help, pointer, group, object-select, and draw leaves are explicit fixture providers.",
      "state_ownership":"One isolated fixture owns g_1B4E/g_1B50 selectors and g_1B62/g_1B64 percentages for one call. Production ownership remains session selectors plus live-game percentages; no second persistent owner is proposed. Source mode/caste globals, level arrays, IdealCaste and shared triangle metrics are fixture projections.",
      "limits":["This paired check reuses the retained 34 direct-DOS inputs and their expected callback/state records; it is not a fresh DOS execution.","Pixel rendering and window-system effects remain provider leaves.","Only loaded profile-0 geometry and staged pointer domain represented by the 34 cases are compared; arbitrary corrupt rectangles and unbounded interactive drags are not exercised."],
      "cases_source":"portable/tests/setup/control_events/evidence/dos-control-events.json","prior_pair_source":"portable/tests/setup/control_events/evidence/paired-control-events.json"}
    if before!=after:raise RuntimeError("input pins changed during extraction comparison")
    payload=json.dumps(report,indent=2)+"\n"
    with out.open("x",encoding="utf-8",newline="") as stream:stream.write(payload)
    print(json.dumps({"status":report["status"],"cases":len(cases),"mismatches":len(mismatches),"report":str(out.relative_to(ROOT))},indent=2))
    if mismatches:raise SystemExit(1)
if __name__=="__main__":main()
