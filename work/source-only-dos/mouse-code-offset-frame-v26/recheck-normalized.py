"""Normalize/recheck the v29 test-owned callback frame runtime evidence; stdlib only."""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
def find_root(path: Path) -> Path:
    for candidate in path.resolve().parents:
        if (candidate / "layout/toolchain.json").is_file(): return candidate
    raise RuntimeError("repository root not found from helper path")
DEFAULT_ROOT = find_root(Path(__file__))
MAIN_REL = Path("build/workers/dos_mouse_callback_frames_v29/callback-frame-whole-module-v29.json")
RUNTIME_REL = Path("build/workers/dos_mouse_callback_frames_v29/callback-fixtures/callback-frame-runtime-fixture-v29.json")
OUT_REL = Path("build/workers/dos_mouse_callback_frames_v30/callback-runtime-contract-v30.json")
EXPECTED_MAIN_SHA = "f500d8930076f9074b2a30da53aefa054fa5a4026267c9d7be1fda96b1695c97"
EXPECTED_MAIN_SIZE = 39703
EXPECTED_RUNTIME_SHA = "b7ef8370417553e27e83dea4c9342752d157d4d1d50d7d49229cddb34c70e682"
EXPECTED_RUNTIME_SIZE = 40771

def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def pinfo(path: Path, root: Path) -> dict:
    raw=path.read_bytes()
    try: name=path.relative_to(root).as_posix()
    except ValueError: name=path.as_posix()
    return {"path":name,"size":len(raw),"sha256":sha(raw)}

def checked_pin(root: Path, item: dict, role: str, checks: list, problems: list) -> dict:
    path=Path(item["path"])
    if not path.is_absolute(): path=root/path
    if not path.is_file():
        problems.append(f"missing {role}: {item['path']}")
        return {"role":role,"pin":item,"verified":False}
    raw=path.read_bytes(); ok=(len(raw)==item.get("size") and sha(raw)==item.get("sha256"))
    checks.append({"role":role,"path":item["path"],"size":len(raw),"sha256":sha(raw),"passed":ok})
    if not ok: problems.append(f"pin mismatch {role}: {item['path']}")
    return {"role":role,"pin":item,"verified":ok}

def parse_map(raw: bytes) -> dict:
    text=raw.decode("latin1",errors="strict")
    segs={}; pubs={}; origin=None; mode=""
    for line in text.splitlines():
        s=line.strip(); a=s.split()
        if s.startswith("Start  Stop   Length Name"): mode="segments"; continue
        if s.startswith("Section# Fname"): mode=""
        if s=="Origin   Group": mode="origin"; continue
        if s=="Address         Publics by Name": mode="publics"; continue
        if s.startswith("Address         Publics by Value"): mode=""
        if mode=="segments" and len(a)>=5 and a[0].endswith("H") and a[1].endswith("H"):
            try:
                segs[a[3]]={"start":int(a[0][:-1],16),"stop":int(a[1][:-1],16),"length":int(a[2][:-1],16),"class":a[4],"group":a[5] if len(a)>5 else None}
            except ValueError: pass
        elif mode=="origin" and len(a)==2 and ":" in a[0]:
            x,y=a[0].split(":",1)
            try: origin={"segment":int(x,16),"offset":int(y,16),"group":a[1]}
            except ValueError: pass
        elif mode=="publics" and len(a)>=2 and ":" in a[0]: pubs[a[1]]=a[0]
    if origin is None: raise ValueError("MAP lacks DGROUP origin")
    base=origin["segment"]*16+origin["offset"]
    def addr(name):
        val=pubs.get(name)
        if not val: return None
        s,o=val.split(":",1); return {"segment":int(s,16),"offset":int(o,16)}
    ps,pe=addr("_prefix_start"),addr("_prefix_end")
    data=segs.get("_DATA",{}); prefix=segs.get("PREFIX",{}); code=segs.get("CALLBACK_TEXT",{})
    return {"origin":origin,"segments":{k:segs.get(k) for k in ("PREFIX","_DATA","CALLBACK_TEXT")},
        "prefix_start":ps,"prefix_end":pe,
        "prefix_offset_in_group":(ps["offset"] if ps and ps["segment"]==origin["segment"] else None),
        "prefix_span":(pe["offset"]-ps["offset"] if ps and pe and ps["segment"]==pe["segment"] else None),
        "data_offset_in_group":data.get("start",0)-base,
        "callback_code_is_separate":bool(code and code.get("class")=="CODE" and code.get("group") is None),
        "shifted_physical_layout":bool(origin["group"]=="DGROUP" and prefix.get("length")==16 and prefix.get("group")=="DGROUP" and data.get("group")=="DGROUP" and ps and pe and ps["segment"]==origin["segment"] and ps["offset"]>=16 and pe["offset"]-ps["offset"]==16 and data.get("start",0)-base==pe["offset"] and code and code.get("group") is None)}

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--root",type=Path,default=DEFAULT_ROOT); ap.add_argument("--out",type=Path,default=None); a=ap.parse_args()
    root=a.root.resolve(); out=(a.out or (root/OUT_REL)).resolve(); problems=[]; verified=[]; artifact_checks=[]
    main_path=root/MAIN_REL; rt_path=root/RUNTIME_REL
    main_raw=main_path.read_bytes(); main=json.loads(main_raw)
    rt_raw=rt_path.read_bytes(); rt=json.loads(rt_raw)
    main_pin=pinfo(main_path,root); rt_pin=pinfo(rt_path,root)
    if main.get("root_reviewed") is not False or rt.get("root_reviewed") is not False: problems.append("source receipts must remain root_reviewed=false")
    if main_pin["sha256"]!=EXPECTED_MAIN_SHA or main_pin["size"]!=EXPECTED_MAIN_SIZE: problems.append("v29 main receipt identity changed")
    if rt_pin["sha256"]!=EXPECTED_RUNTIME_SHA or rt_pin["size"]!=EXPECTED_RUNTIME_SIZE: problems.append("v29 runtime receipt identity changed")
    if not rt.get("all_cases_pass") or not rt.get("all_natural_frame_links_clean"): problems.append("v29 runtime receipt top-level checks are not all passing")
    if main.get("status")!="WHOLE_MODULE_FRAME_ONLY_VARIANTS_AND_SHIFTED_CALLBACK_FIXTURE_PASS": problems.append("v29 whole-module receipt status changed")
    if main.get("inputs",{}).get("callback_fixture_report")!={"path":RUNTIME_REL.as_posix(),"size":len(rt_raw),"sha256":sha(rt_raw)}: problems.append("main receipt does not pin the exact runtime subreceipt")
    verified.append({"role":"v29_whole_module_receipt","pin":main_pin,"verified":True})
    verified.append({"role":"v29_runtime_receipt","pin":rt_pin,"verified":True})
    mutable_build_report=None
    for k,v in main.get("inputs",{}).items():
        if k=="build_report":
            live_path=root/v["path"]
            live=json.loads(live_path.read_text(encoding="utf-8"))
            live_row=next((x for x in live.get("translation_units",[]) if x.get("module")=="root:1B73"),None)
            expected_rows={"source":main["inputs"]["canonical_source"],"generated_source":main["inputs"]["generated_source"],"object":main["inputs"]["admitted_object"]}
            row_matches=bool(live_row)
            for field,pin in expected_rows.items():
                current=live_row.get(field,{}) if live_row else {}
                row_matches=row_matches and current.get("size")==pin["size"] and current.get("sha256")==pin["sha256"]
            live_pin=pinfo(live_path,root)
            mutable_build_report={"historical_receipt_pin":v,"current_pin":live_pin,"whole_file_changed":live_pin["sha256"]!=v["sha256"],"root_1B73_source_generated_object_rows_match":row_matches}
            if not row_matches: problems.append("current mutable build report no longer agrees with pinned root:1B73 source/object inputs")
            continue
        if isinstance(v,dict) and all(x in v for x in ("path","size","sha256")):
            checked_pin(root,v,"main-input:"+k,artifact_checks,problems)
    for i,v in enumerate(main.get("inputs",{}).get("binding_chain",[])):
        checked_pin(root,v["packet"],f"binding-packet-{i}",artifact_checks,problems)
    for i,v in enumerate(rt.get("inputs",[])): checked_pin(root,v,f"runtime-tool-input-{i}",artifact_checks,problems)
    for role,v in rt.get("fixture_sources",{}).items(): checked_pin(root,v,"fixture-source:"+role,artifact_checks,problems)
    for role,items in rt.get("objects",{}).items():
        for kind,v in items.items():
            if v: checked_pin(root,v,f"fixture-{kind}:{role}",artifact_checks,problems)
    wrong_src=rt["fixture_sources"]["wrong_checker"]["path"]
    natural_src=rt["fixture_sources"]["natural_checker"]["path"]
    wrong_text=(root/wrong_src).read_text(encoding="latin1")
    natural_text=(root/natural_src).read_text(encoding="latin1")
    labels=("MouseCB","Vector15CB","Vector09CB","Vector08CB","LocalCB")
    wrong_operands=all(f"lea dx, ds:{n}" in wrong_text for n in labels)
    natural_operands=all(f"lea dx, {n}" in natural_text and f"lea dx, ds:{n}" not in natural_text for n in labels)
    wrong_listing_path=root/rt["objects"]["wrong_dgroup_frame"]["listing"]["path"]
    wrong_listing=(wrong_listing_path.read_text(encoding="latin1") if wrong_listing_path.exists() else "")
    def listing_offset(needle):
        m=re.search(r"^\s*([0-9A-F]{4})\s+[^\r\n]*\b"+re.escape(needle)+r"\s*$",wrong_listing,re.M)
        return int(m.group(1),16) if m else None
    early_branch=listing_offset("jne FixtureBad")
    callback_call=listing_offset("call word ptr _g5FFA")
    only_local_call=wrong_listing.count("call word ptr _g5FFA")==1
    early_exit_proved=bool(early_branch is not None and callback_call is not None and early_branch<callback_call and only_local_call and "FixtureBad:" in wrong_text)
    fx=rt.get("omf_target_fixups",{})
    wanted_sites=[6,30,49,68,88]
    bad_fx=fx.get("wrong_source_DGROUP_frames",[])
    good_fx=fx.get("natural_source_CODE_frames",[])
    wrong_fixups=bool([x["site"] for x in bad_fx]==wanted_sites and all(x["frame_kind"]=="group" and x["frame"]=="DGROUP" for x in bad_fx))
    good_at={x["site"]:x for x in good_fx}
    natural_fixups=bool(all(s in good_at and good_at[s]["frame_kind"]=="segment" and good_at[s]["frame"]=="CALLBACK_TEXT" for s in wanted_sites))
    expected={("rtlink400","wrong_dgroup_frame"):"FAIL",("rtlink400","natural_code_frame"):"PASS",("rtlink610","wrong_dgroup_frame"):"FAIL",("rtlink610","natural_code_frame"):"PASS"}
    seen=set(); normalized_cases=[]; maps=[]
    for c in rt.get("cases",[]):
        profile=c["linker"]; mode=c["variant"]; key=(profile,mode); seen.add(key); want=expected.get(key)
        casefiles={}
        for name in ("exe","map_file","link_log","run_log"):
            pin=c.get(name)
            casefiles[name]=checked_pin(root,pin,f"{profile}:{mode}:{name}",artifact_checks,problems) if pin else {"verified":False}
        exe_p=root/c["exe"]["path"]; map_p=root/c["map_file"]["path"]; link_p=root/c["link_log"]["path"]; run_p=root/c["run_log"]["path"]
        exe_raw=exe_p.read_bytes(); map_raw=map_p.read_bytes(); link_raw=link_p.read_bytes(); run_raw=run_p.read_bytes()
        link_text=link_raw.decode("latin1"); run_text=run_raw.decode("latin1"); actual=run_text.strip()
        warnings=[line.strip() for line in link_text.splitlines() if line.strip().lower().startswith("warning ")]
        errors=[line.strip() for line in link_text.splitlines() if line.strip().lower().startswith("error ")]
        identity=("RTLink/Plus 4.00" if profile=="rtlink400" and "Ver. 4.00" in link_text else "RTLink/Plus 6.10" if profile=="rtlink610" and "Version 6.10" in link_text else None)
        mapinfo=parse_map(map_raw); maps.append(mapinfo)
        warnings_ok=(not warnings and not errors) if mode=="natural_code_frame" or profile=="rtlink400" else (len(warnings)==5 and all("wrt0082" in w.lower() for w in warnings) and not errors and "requested address lies before the address it is relative to" in link_text)
        runtime_ok=(want is not None and actual==want and c.get("actual")==actual and c.get("expected")==want and c.get("emulator_exit")==0)
        case_ok=runtime_ok and warnings_ok and identity is not None and mapinfo["shifted_physical_layout"] and all(casefiles[k]["verified"] for k in casefiles)
        normalized_cases.append({"linker_profile":profile,"frame_form":mode,"expected_run":want,"actual_run":actual,"run_log_text":run_text,"linker_identity":identity,"link_log_text":link_text,"warning_lines":warnings,"error_lines":errors,"link_clean":not warnings and not errors,"warning_policy_passed":warnings_ok,"emulator_exit":c.get("emulator_exit"),"map_physical_frame":mapinfo,"artifacts":{k:v.get("pin") for k,v in casefiles.items()},"passed":case_ok})
        if not case_ok: problems.append(f"runtime case failed normalization: {profile}/{mode}")
    if seen!=set(expected): problems.append("runtime case matrix is not exactly four required cases")
    if not wrong_operands or not natural_operands or not early_exit_proved: problems.append("source/listing control ordering or LEA spelling proof failed")
    if not wrong_fixups or not natural_fixups: problems.append("fixture OMF fixup frame evidence failed")
    if not all(m["shifted_physical_layout"] for m in maps): problems.append("one or more raw MAP files fail physical layout checks")
    all_natural_clean=all(c["link_clean"] for c in normalized_cases if c["frame_form"]=="natural_code_frame")
    if not all_natural_clean: problems.append("natural-frame link is not clean")
    helper_pin=pinfo(Path(__file__),root)
    outdoc={"schema":"simant-callback-frame-runtime-contract-normalized-v30","root_reviewed":False,
        "scope":"stdlib-only integrity/normalization of pinned v29 fixture outputs and source receipts; no original executable is read and no compiler/linker is invoked",
        "v29_scope_wording_correction":"The v29 whole-module receipt says no warning-image execution; this is too broad. The test-only wrong-frame RTLink 6.10 negative was executed and returned FAIL before the sole callback call, after the first mismatch branch at offset 000D; it emitted five WRT0082 warnings. Natural-frame candidate images were clean and passed. No game or original executable was linked or run.",
        "source_receipts":{"whole_module":main_pin,"runtime":rt_pin},
        "source_fixup_controls":{"wrong_source_all_five_DGROUP":{"passed":wrong_operands and wrong_fixups},"natural_source_all_five_code_segment":{"passed":natural_operands and natural_fixups},"wrong_frame_exits_before_callback_call":{"passed":early_exit_proved,"first_failure_branch_offset":early_branch,"only_callback_call_offset":callback_call,"control_listing":rt["objects"]["wrong_dgroup_frame"]["listing"]}},
        "required_case_matrix":[{"profile":p,"frame_form":f,"expected":v} for (p,f),v in expected.items()],
        "cases":normalized_cases,"all_natural_links_clean":all_natural_clean,
        "mutable_build_report_observation":mutable_build_report,"integrity":{"helper":helper_pin,"verified_artifacts":artifact_checks,"problems":problems,"all_pins_match":not problems},
        "passed":not problems and len(normalized_cases)==4 and all(x["passed"] for x in normalized_cases)}
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(outdoc,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"report":out.as_posix(),"root_reviewed":False,"passed":outdoc["passed"],"all_natural_links_clean":all_natural_clean,"case_summary":[{k:c[k] for k in ("linker_profile","frame_form","expected_run","actual_run","link_clean","warning_policy_passed","passed")} for c in normalized_cases],"problem_count":len(problems)},indent=2))
    return 0 if outdoc["passed"] else 1

if __name__=="__main__": raise SystemExit(main())

