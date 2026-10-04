"""Fresh minimal-view proposal controls, confined to this worker directory.

Whole generated U088 is compiled; its actual selector body/fixups are independently
bound. Runtime phase forbids assets and links exact extracted consumer/table with
natural data-only providers, stock CRT and both pinned RTLinks. No game stubs.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, "C:/tools/capstone-5.0.3")
import compiler
import match
import source_only_dos as dos
from omf import OmfReader

compiler.WORK = OUT / "compiler"
FLAGS = ["/AL", "/Os", "/Gs"]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pin(path, expected=None):
    raw=Path(path).read_bytes()
    digest=sha(raw)
    if expected is not None and expected != digest:
        raise RuntimeError(f"stale pin: {path}")
    try:
        label=Path(path).relative_to(ROOT).as_posix()
    except ValueError:
        label=Path(path).as_posix()
    return {"path":label,"sha256":digest,"size":len(raw)}


def save(name,text):
    p=OUT/name
    p.write_text(text,encoding="ascii")
    return p


def compile_unit(path,basename,flags):
    res=compiler.compile_c(path.read_text(encoding="ascii"),"msc600ax",flags,basename=basename,keep=True)
    if not res.ok:
        raise RuntimeError(f"compile {basename}: {res.log}")
    dest=OUT/"objects"
    dest.mkdir(exist_ok=True)
    p=dest/(basename+".OBJ")
    p.write_bytes(res.obj)
    (dest/(basename+".log")).write_text(res.log,encoding="latin1")
    obj=OmfReader(communals=True).read(res.obj,basename)
    return res.obj,{"source":pin(path),"object":pin(p),"flags":flags,
        "module_name":obj.name,"segments":obj.segment_defs,"groups":obj.groups,
        "publics":obj.publics,"externals":obj.externals,"communals":obj.communals,
        "linker_fixups":obj.linker_fixups,
        "segment_payload_hashes":{n:{"size":len(b),"sha256":sha(bytes(b))} for n,b in obj.segments.items()},
        "compiler_log":pin(dest/(basename+".log")),"compiler_workdir":res.workdir.relative_to(ROOT).as_posix()}


MAIN=r'''
extern int far printf(char far *format, ...);
SHIFT_DECL
int main(void)
{
    int i;
    int signed_probe;

    if (sizeof(g_8CCB) != 1) {
        printf("SELECTOR FAIL width=%u\n", sizeof(g_8CCB));
        return 1;
    }
    if (g_8CCB != 0) {
        printf("SELECTOR FAIL init=%d\n", (int)g_8CCB);
        return 1;
    }
    SHIFT_CHECK
    if (f_1C62_06A6(0) != sys_errlist[0] || f_1C62_06A6(sys_nerr) != sys_errlist[sys_nerr]) {
        printf("SELECTOR FAIL crt_range\n");
        return 1;
    }
    for (i = 0; i < 14; i++) {
        g_8CCB = i;
        if (f_1C62_06A6(-1) != g_567A[i] || f_1C62_06A6(sys_nerr + 1) != g_567A[i]) {
            printf("SELECTOR FAIL index=%d\n", i);
            return 1;
        }
    }
    *((unsigned char near *)&g_8CCB) = 0x80;
    signed_probe = g_8CCB;
    if (signed_probe != -128) {
        printf("SELECTOR FAIL signed=%d\n", signed_probe);
        return 1;
    }
    g_8CCB = 0;
    printf("SELECTOR PASS width=1 signed=%d entries=14 init=0\n", signed_probe);
    return 0;
}
'''


def map_publics(text):
    rows=[]
    seen=set()
    for seg,off,name,attrs,member in re.findall(r"(?m)^\s*([0-9A-Fa-f]{4}):([0-9A-Fa-f]{1,4})\s+(\S+)(?:[ \t]+((?:[A-Z][ \t]+){1,3})(\S+))?[ \t]*$",text):
        row=(name,int(seg,16),int(off,16))
        if row not in seen:
            rows.append({"name":name,"segment":row[1],"offset":row[2],"attributes":attrs.split(),"member":member or None})
            seen.add(row)
    return rows


def main():
    tc=compiler.toolchain()
    manifest=json.loads((ROOT/"layout/manifest.json").read_text())
    intake=json.loads((OUT/"intake/build-report.json").read_text())
    row=next(r for r in intake["translation_units"] if r["module"]=="root:1C62")
    actual=ROOT/row["generated_source"]["path"]
    pin(actual,row["generated_source"]["sha256"])
    whole,whole_meta=compile_unit(actual,"U088",row["flags"])
    obj=OmfReader(communals=True).read(whole)
    pb=next(p for p in obj.publics if p["name"]=="_f_1C62_06A6")
    result=match.match_object(whole,match.Target("root",0x1C62,0x06A6,54),pb["segment"],pb["name"],
        manifest["modules"]["root:1C62"]["placements"])
    whole_gate={"actual_full_generated_TU":whole_meta,"selector_binding":{
        "exact":result.exact,"reasons":result.reasons,"candidate_extent":result.candidate_extent_size,
        "fixups":result.fixups,"unbound":result.unbound,"reloc_order":result.reloc_order,
        "relocations_expected":result.relocs_expected,"relocations_candidate":result.relocs_candidate,
        "candidate_sha256":sha(result.candidate),"original_sha256":sha(result.original)},
        "scope":"Full selected TU compiled, selector extent and symbolic fixups matched; no complete historical TU claim for the behavior-substituted module."}
    (OUT/"whole-tu-v36.json").write_text(json.dumps(whole_gate,indent=2)+"\n",encoding="utf-8")
    if not result.exact:
        raise RuntimeError("actual full-TU selector failed: "+result.summary())

    # From this point only the source fixture/compiler/libraries are accessible.
    denied=dos.install_input_guard()
    text=actual.read_text(encoding="ascii")
    marker="extern char far * near sys_errlist[];"
    # The strict whole-TU insertion repeats prototypes before the dialog body.
    # Extract the declaration/table/function block immediately before selector.
    selector_start=text.index("char far * far f_1C62_06A6(int err)")
    start=text.rindex(marker,0,selector_start)
    end=text.index("\nint far WaitedEnough(",start)
    extracted=text[start:end].rstrip()
    assert extracted.count("return g_567A[g_8CCB];")==1
    base_main=MAIN.replace("SHIFT_DECL","").replace("SHIFT_CHECK","")
    shift_main=MAIN.replace("SHIFT_DECL","extern unsigned char near independent_context[257];").replace("SHIFT_CHECK",'''if (independent_context[0] != 0x51 || independent_context[256] != 0) {
        printf("SELECTOR FAIL context_storage\\n");
        return 1;
    }''')
    paths={
        "SELVIEW":save("selector-view.c","/* Proposed minimal mutable source view; alias gate remains open. */\nchar near g_8CCB;\n"),
        "SELINIT":save("selector-initialized-contrast.c","char near g_8CCB = 1;\n"),
        "SELWORD":save("selector-width-contrast.c","int near g_8CCB;\n"),
        "SELUNSG":save("selector-unsigned-diagnostic.c","unsigned char near g_8CCB;\n"),
        "SELTEST":save("selector-consumer.c",extracted+"\n"+base_main),
        "SELWTEST":save("selector-width-consumer.c",extracted.replace("extern char near g_8CCB;","extern int near g_8CCB;")+"\n"+base_main),
        "SELSHIFT":save("selector-shift-consumer.c",extracted+"\n"+shift_main),
        "CONTEXT":save("context-storage.c","unsigned char near independent_context[257] = { 0x51 };\n")}
    objects,controls={},{}
    for name,path in paths.items():
        objects[name],controls[name]=compile_unit(path,name,FLAGS)
    for name in ("SELVIEW","SELUNSG"):
        _,controls[name+"_CV"]=compile_unit(paths[name],name+"D",FLAGS+["/Zi"])
    owner=controls["SELVIEW"]
    wide=controls["SELWORD"]
    unsigned=controls["SELUNSG"]
    assert owner["communals"]==unsigned["communals"]
    for candidate,length in ((owner,1),(wide,2)):
        communals=[c for c in candidate["communals"] if c["name"]=="_g_8CCB"]
        assert len(communals)==1 and communals[0]["kind"]=="near" and communals[0]["length"]==length
    assert not controls["SELINIT"]["communals"]
    assert all(s["length"]==0 for s in owner["segments"])

    inputs=[pin(__file__),pin(actual),pin(ROOT/"tools/compiler.py"),pin(ROOT/"tools/omf.py"),
        pin(ROOT/"tools/source_only_dos.py"),pin(ROOT/"layout/toolchain.json"),pin(ROOT/"layout/manifest.json")]
    prof=compiler.verify_profile("msc600ax")
    inputs += [pin(Path(prof["directory"])/n,d) for n,d in prof["files"].items()]
    libs=list(manifest["runtime"]["libraries"].values())
    inputs += [pin(v["path"],v["sha256"]) for v in libs]
    runner=tc["runners"]["dosbox-x"]
    inputs += [pin(runner["path"],runner["sha256"])]
    cases=[]
    for link_name in ("rtlink400","rtlink610"):
        tool=tc["linkers"][link_name]
        inputs += [pin(Path(tool["directory"])/n,d) for n,d in tool["files"].items()]
        tool_dir=compiler.pinned_tree(tool)
        for case,names,expected in (
            ("byte_view",["SELTEST","SELVIEW"],"SELECTOR PASS width=1 signed=-128 entries=14 init=0"),
            ("initialized_one",["SELTEST","SELINIT"],"SELECTOR FAIL init=1"),
            ("word_width",["SELWTEST","SELWORD"],"SELECTOR FAIL width=2"),
            ("shifted_dgroup",["CONTEXT","SELSHIFT","SELVIEW"],"SELECTOR PASS width=1 signed=-128 entries=14 init=0")):
            directory=OUT/"runtime"/link_name/case
            directory.mkdir(parents=True,exist_ok=True)
            for n in names:
                (directory/(n+".OBJ")).write_bytes(objects[n])
            for lib in libs:
                shutil.copyfile(lib["path"],directory/Path(lib["path"]).name.upper())
            (directory/"PROBE.LNK").write_text("OUTPUT PROBE\nMAP = PROBE S,N,A,L,V,X\nNODEFLIB\nLIBRARY LLIBCR, LIBH\nFILE "+", ".join(names)+"\n",encoding="ascii")
            (directory/"RTLINK.CFG").write_text("SYNTAX = FREEFORMAT\n",encoding="ascii")
            (directory/"RUN.BAT").write_bytes(("@echo off\r\nD:\\"+tool["executable"]+" @PROBE.LNK < NUL > LINK.LOG\r\nPROBE.EXE > RUN.LOG\r\n").encode("ascii"))
            conf=[]
            for section,settings in runner["conf"].items():
                conf.append("["+section+"]")
                conf += [str(k)+"="+str(v) for k,v in settings.items()]
            conf += ["[autoexec]",f'mount c "{directory}"',f'mount d "{tool_dir}" -ro',"c:","call RUN.BAT","exit"]
            cp=directory/"dosbox.conf"
            cp.write_text("\n".join(conf)+"\n",encoding="ascii")
            env=os.environ.copy();env.update(SDL_VIDEODRIVER="dummy",SDL_AUDIODRIVER="dummy")
            proc=subprocess.run([runner["path"],"-conf",str(cp),"-fastlaunch","-exit","-nomenu"],cwd=directory,
                env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=60,
                creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
            link_log=(directory/"LINK.LOG").read_text(encoding="latin1") if (directory/"LINK.LOG").exists() else ""
            run_log=(directory/"RUN.LOG").read_text(encoding="latin1") if (directory/"RUN.LOG").exists() else ""
            map_text=(directory/"PROBE.MAP").read_text(encoding="latin1") if (directory/"PROBE.MAP").exists() else ""
            public_table=map_publics(map_text)
            wanted={"_g_8CCB","_errno","_sys_errlist","_sys_nerr","__astart"}
            found={p["name"] for p in public_table}
            diagnostics=dos.independent_link_diagnostics(link_log)
            clean=bool(link_log) and not diagnostics and (directory/"PROBE.EXE").is_file()
            passed=clean and proc.returncode==0 and run_log.strip()==expected and wanted<=found
            rows={p["name"]:p for p in public_table}
            cases.append({"linker":link_name,"case":case,"expected":expected,"stdout":run_log,
                "emulator_exit":proc.returncode,"clean_link":clean,"diagnostics":diagnostics,
                "public_table":public_table,"owner_map_public":rows.get("_g_8CCB"),
                "all_required_publics_present":wanted<=found,"passed":passed,
                "files":[pin(p) for p in sorted(directory.iterdir()) if p.is_file()]})
            print(link_name,case,run_log.strip(),"PASS" if passed else "FAILED",flush=True)
    shifts=[]
    for link_name in ("rtlink400","rtlink610"):
        a=next(r for r in cases if r["linker"]==link_name and r["case"]=="byte_view")["owner_map_public"]
        b=next(r for r in cases if r["linker"]==link_name and r["case"]=="shifted_dgroup")["owner_map_public"]
        shifts.append({"linker":link_name,"base":a,"shifted":b,
            "owner_offset_changed":a is not None and b is not None and a["offset"]!=b["offset"]})
    report={"schema":"simant-dos-critical-selector-storage-proposal-controls-v36",
        "status":"PROPOSAL_ONLY; COMPUTED_ALIAS_GATE_UNRESOLVED", "inputs":inputs,
        "whole_TU_gate":pin(OUT/"whole-tu-v36.json"),"compiler_controls":controls,
        "extraction":{"full_generated_source":pin(actual),"start_marker":marker,
            "end_exclusive":"int far WaitedEnough(","extracted_sha256":sha(extracted.encode("ascii")),
            "positive_has_exact_selected_consumer_and_table":True},
        "unsigned_provider_diagnostic":"Same near one-byte COMDEF as signed char; cannot be a runtime signedness negative with unchanged signed-char consumer. Original CBW/whole-TU matching fixes consumer signed promotion. Supplemental /Zi objects retain type metadata for source review.",
        "runtime_cases":cases,"shifted_DGROUP_controls":shifts,"denied_oracle_reads":denied,
        "all_required_checks_pass":all(c["passed"] for c in cases) and all(s["owner_offset_changed"] for s in shifts) and not denied,
        "gate":"Storage view/type/startup only. Does not establish full-game execution, historical owner TU/placement, invariant selector zero, dead sole read, or preservation of original computed aliases."}
    (OUT/"fixture-receipt-v36.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    if not report["all_required_checks_pass"]:
        raise RuntimeError("selector proposal controls failed")


def recheck_maps():
    path=OUT/"fixture-receipt-v36.json"
    report=json.loads(path.read_text())
    # Map parsing failed after all eight clean links/runtime runs. Preserve and
    # hash-verify those actual outputs rather than rerunning unchanged binaries.
    for case in report["runtime_cases"]:
        for p in case["files"]:
            pin(ROOT/p["path"],p["sha256"])
        directory=OUT/"runtime"/case["linker"]/case["case"]
        table=map_publics((directory/"PROBE.MAP").read_text(encoding="latin1"))
        wanted={"_g_8CCB","_errno","_sys_errlist","_sys_nerr","__astart"}
        rows={p["name"]:p for p in table}
        case["public_table"]=table
        case["owner_map_public"]=rows.get("_g_8CCB")
        case["all_required_publics_present"]=wanted<=rows.keys()
        case["passed"]=case["clean_link"] and case["emulator_exit"]==0 and case["stdout"].strip()==case["expected"] and case["all_required_publics_present"]
    report["shifted_DGROUP_controls"]=[]
    for linker in ("rtlink400","rtlink610"):
        a=next(r for r in report["runtime_cases"] if r["linker"]==linker and r["case"]=="byte_view")["owner_map_public"]
        b=next(r for r in report["runtime_cases"] if r["linker"]==linker and r["case"]=="shifted_dgroup")["owner_map_public"]
        report["shifted_DGROUP_controls"].append({"linker":linker,"base":a,"shifted":b,
            "owner_offset_changed":a is not None and b is not None and a["offset"]!=b["offset"]})
    report["inputs"]=[pin(__file__) if p["path"].endswith("/fixture_v36.py") else p for p in report["inputs"]]
    report["map_recheck"]="Reparsed all hash-verified full RTLink maps including used/member columns; no compiler, link or runtime rerun after parser repair."
    report["all_required_checks_pass"]=all(c["passed"] for c in report["runtime_cases"]) and all(s["owner_offset_changed"] for s in report["shifted_DGROUP_controls"]) and not report["denied_oracle_reads"]
    path.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"all_required_checks_pass":report["all_required_checks_pass"],"shifted_DGROUP_controls":report["shifted_DGROUP_controls"],
        "cases":[{"linker":c["linker"],"case":c["case"],"passed":c["passed"],"public_count":len(c["public_table"])} for c in report["runtime_cases"]]},indent=2))
    if not report["all_required_checks_pass"]:
        raise RuntimeError("rechecked map cases failed")


if __name__=="__main__":
    recheck_maps() if "--recheck-maps" in sys.argv else main()
