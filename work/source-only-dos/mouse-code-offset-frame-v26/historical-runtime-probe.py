from __future__ import annotations
import hashlib, json, os, shutil, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "callback-fixtures"
sys.path.insert(0, str(ROOT / "tools"))
import compiler
from omf import OmfReader

def pin(p):
    b=p.read_bytes()
    try: n=p.relative_to(ROOT).as_posix()
    except ValueError: n=p.as_posix()
    return {"path":n,"size":len(b),"sha256":hashlib.sha256(b).hexdigest()}
def save(p,s):
    p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(s.replace("\r\n","\n").replace("\n","\r\n").encode("ascii"))
def owner():
    return """PREFIX segment word public 'DATA'
public _prefix_start,_prefix_end
_prefix_start label byte
db 16 dup (0A5h)
_prefix_end label byte
PREFIX ends
_DATA segment word public 'DATA'
public _g5FFA,_called
_g5FFA dw 0
_called dw 0
_DATA ends
DGROUP group PREFIX,_DATA
end
"""
def checker(natural):
    def lea(r,n): return f"lea {r}, {n}" if natural else f"lea {r}, ds:{n}"
    x=["_DATA segment word public 'DATA'","extrn _g5FFA:word,_called:word","_DATA ends","DGROUP group _DATA","CALLBACK_TEXT segment word public 'CODE'","assume cs:CALLBACK_TEXT,ds:DGROUP","public _FrameFixture","_FrameFixture proc far","push ds","push es","push cs","pop es",lea("dx","MouseCB"),"mov bx,offset CALLBACK_TEXT:MouseCB","cmp dx,bx","jne FixtureBad","mov ax,es","mov bx,cs","cmp ax,bx","jne FixtureBad","push ds","mov ax,cs","mov ds,ax"]
    for n in ("Vector15CB","Vector09CB","Vector08CB"):
        x += [lea("dx",n),f"mov bx,offset CALLBACK_TEXT:{n}","cmp dx,bx","jne FixtureBad","mov ax,ds","mov bx,cs","cmp ax,bx","jne FixtureBad"]
    x += ["pop ds",lea("dx","LocalCB"),"mov word ptr _g5FFA,dx","mov bx,offset CALLBACK_TEXT:LocalCB","cmp dx,bx","jne FixtureBad","call word ptr _g5FFA","cmp word ptr _called,1","jne FixtureBad","xor ax,ax","jmp short FixtureDone","FixtureBad:","mov ax,1","FixtureDone:","pop es","pop ds","retf","_FrameFixture endp","MouseCB:","ret","Vector15CB:","ret","Vector09CB:","ret","Vector08CB:","ret","LocalCB:","inc word ptr _called","ret","CALLBACK_TEXT ends","end"]
    return "\n".join(x)+"\n"
def map_summary(p):
    t=p.read_text(encoding="latin1",errors="replace"); seg={}; origin=None; pubs={}; mode=""
    for line in t.splitlines():
        s=line.strip()
        if s.startswith("Start  Stop   Length Name"): mode="seg"; continue
        if s.startswith("Section# Fname"): mode=""
        if s=="Origin   Group": mode="origin"; continue
        if s=="Address         Publics by Name": mode="pub"; continue
        if s.startswith("Address         Publics by Value"): mode=""
        a=s.split()
        if mode=="seg" and len(a)>=5 and a[0].endswith("H") and a[1].endswith("H"):
            try: seg[a[3]]={"start":int(a[0][:-1],16),"length":int(a[2][:-1],16),"class":a[4],"group":a[5] if len(a)>5 else None}
            except ValueError: pass
        elif mode=="origin" and len(a)==2 and ":" in a[0]:
            q,r=a[0].split(":"); origin={"segment":int(q,16),"offset":int(r,16),"group":a[1]}
        elif mode=="pub" and len(a)>=2 and ":" in a[0]: pubs[a[1]]=a[0]
    group=(origin["segment"]*16+origin["offset"]) if origin else None
    dd=seg.get("_DATA",{}).get("start",0)-group if group is not None else None
    start=pubs.get("_prefix_start","").split(":")
    end=pubs.get("_prefix_end","").split(":")
    prefix_span=(int(end[1],16)-int(start[1],16)) if len(start)==2 and len(end)==2 and start[0]==end[0] else None
    prefix_offset=int(start[1],16) if len(start)==2 and start[0]==f"{origin['segment']:04X}" else None if origin else None
    code_outside=bool(seg.get("CALLBACK_TEXT",{}).get("group")!="DGROUP" and "CALLBACK_TEXT" in seg)
    passed=bool(origin and origin["group"]=="DGROUP" and seg.get("PREFIX",{}).get("length")==16 and seg.get("PREFIX",{}).get("group")=="DGROUP" and seg.get("_DATA",{}).get("group")=="DGROUP" and dd is not None and dd>=16 and prefix_span==16 and prefix_offset is not None and prefix_offset>=16 and code_outside)
    return {"origin":origin,"segments":seg,"publics":{"_prefix_start":pubs.get("_prefix_start"),"_prefix_end":pubs.get("_prefix_end")},"data_delta_from_group":dd,"prefix_offset_in_group":prefix_offset,"prefix_marker_span":prefix_span,"callback_code_is_separate_segment":code_outside,"shifted_layout_proven":passed}
def main():
    OUT.mkdir(parents=True,exist_ok=True); compiler.WORK=OUT/"compiler-work"; compiler.WORK.mkdir(parents=True,exist_ok=True)
    sd=OUT/"sources"; od=OUT/"objects"; sd.mkdir(exist_ok=True); od.mkdir(exist_ok=True)
    tc=compiler.toolchain(); owner_text=owner(); ctext="extern int far FrameFixture(void);\nint main(void) { return FrameFixture(); }\n"
    owner_result=compiler.assemble(owner_text,"masm510",["/Mx","/L"],basename="OWNER",keep=True)
    crt_result=compiler.compile_c(ctext,"msc600ax",["/AL","/Os","/Zi"],basename="CRT",keep=True)
    if not owner_result.ok or not crt_result.ok: raise SystemExit("fixture base compile failed")
    save(sd/"OWNER.asm",owner_text); save(sd/"CRT.c",ctext); (od/"OWNER.OBJ").write_bytes(owner_result.obj); (od/"CRT.OBJ").write_bytes(crt_result.obj)
    cases=[]; object_pins={}
    runtimes=list(json.loads((ROOT/"layout/manifest.json").read_text(encoding="utf-8"))["runtime"]["libraries"].values())
    dosbox=tc["runners"]["dosbox-x"]
    for natural,label,expected in ((False,"wrong_dgroup_frame","FAIL"),(True,"natural_code_frame","PASS")):
        txt=checker(natural); save(sd/f"CHECK_{label}.asm",txt)
        r=compiler.assemble(txt,"masm510",["/Mx","/L"],basename="CHECK",keep=True)
        if not r.ok: raise SystemExit(label+" MASM failed: "+r.log)
        op=od/f"CHECK_{label}.OBJ"; op.write_bytes(r.obj); lp=r.workdir/"CHECK.LST"
        if lp.exists(): shutil.copyfile(lp,od/f"CHECK_{label}.LST")
        object_pins[label]={"object":pin(op),"listing":pin(od/f"CHECK_{label}.LST") if (od/f"CHECK_{label}.LST").exists() else None}
    bad=OmfReader().read((od/"CHECK_wrong_dgroup_frame.OBJ").read_bytes(),"bad")
    good=OmfReader().read((od/"CHECK_natural_code_frame.OBJ").read_bytes(),"good")
    targets=["MouseCB","Vector15CB","Vector09CB","Vector08CB","LocalCB"]
    def selected(m,frame):
        return [{"site":f["offset"],"displacement":f["displacement"],"frame_kind":f["frame_kind"],"frame":f["frame"]} for f in m.linker_fixups if f.get("target")=="CALLBACK_TEXT" and f.get("frame")==frame]
    fixups={"wrong_source_DGROUP_frames":selected(bad,"DGROUP"),"natural_source_CODE_frames":selected(good,"CALLBACK_TEXT"),"five_target_labels":targets}
    inputs=[pin(Path(__file__)),pin(ROOT/"layout/toolchain.json"),pin(ROOT/"layout/manifest.json"),pin(ROOT/"tools/compiler.py"),pin(ROOT/"tools/omf.py"),pin(Path(tc["runner"]["path"])),pin(Path(dosbox["path"]))]
    for rr in runtimes: inputs.append(pin(Path(rr["path"])))
    for profile in ("rtlink400","rtlink610"):
        linker=tc["linkers"][profile]; inputs += [pin(Path(linker["directory"])/rel) for rel in linker["files"]]
        tool_dir=compiler.pinned_tree(linker)
        for label,expected in (("wrong_dgroup_frame","FAIL"),("natural_code_frame","PASS")):
            d=OUT/"linkers"/profile/label; d.mkdir(parents=True,exist_ok=True)
            for nm in ("FRAMEFIX.EXE","FRAMEFIX.MAP","LINK.LOG","RUN.LOG","FRAMEFIX.LNK","RTLINK.CFG","RUN.BAT","dosbox.conf"): (d/nm).unlink(missing_ok=True)
            for nm in ("OWNER.OBJ","CRT.OBJ"): shutil.copyfile(od/nm,d/nm)
            shutil.copyfile(od/f"CHECK_{label}.OBJ",d/"CHECK.OBJ")
            for rr in runtimes: shutil.copyfile(Path(rr["path"]),d/Path(rr["path"]).name.upper())
            (d/"FRAMEFIX.LNK").write_bytes(("\r\n".join(["OUTPUT FRAMEFIX","MAP = FRAMEFIX S,N,A,L","NODEFLIB","LIBRARY LLIBCR, LIBH","FILE OWNER","FILE CRT","FILE CHECK",""])).encode("ascii"))
            (d/"RTLINK.CFG").write_bytes(b"SYNTAX = FREEFORMAT\r\n")
            batch=f"@echo off\r\nD:\\{linker['executable']} @FRAMEFIX.LNK < NUL > LINK.LOG\r\nif not exist FRAMEFIX.EXE goto noexe\r\nFRAMEFIX.EXE\r\nif errorlevel 1 goto fail\r\necho PASS > RUN.LOG\r\ngoto done\r\n:fail\r\necho FAIL > RUN.LOG\r\ngoto done\r\n:noexe\r\necho NOEXE > RUN.LOG\r\n:done\r\n"; (d/"RUN.BAT").write_bytes(batch.encode("ascii"))
            conf=[]
            for sec,vals in dosbox["conf"].items(): conf += [f"[{sec}]",*[f"{k}={v}" for k,v in vals.items()]]
            conf += ["[autoexec]",f'mount c "{d}"',f'mount d "{tool_dir}" -ro',"c:","call RUN.BAT","exit",""]; (d/"dosbox.conf").write_text("\n".join(conf),encoding="utf-8")
            env=os.environ.copy(); env.update(SDL_VIDEODRIVER="dummy",SDL_AUDIODRIVER="dummy")
            em=subprocess.run([dosbox["path"],"-conf",str(d/"dosbox.conf"),"-fastlaunch","-exit","-nomenu"],cwd=d,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=60,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
            actual=(d/"RUN.LOG").read_text(encoding="latin1").strip() if (d/"RUN.LOG").exists() else "NO_RUN_LOG"
            mapping=map_summary(d/"FRAMEFIX.MAP") if (d/"FRAMEFIX.MAP").exists() else {"shifted_layout_proven":False}
            log=(d/"LINK.LOG").read_text(encoding="latin1",errors="replace") if (d/"LINK.LOG").exists() else ""
            warning_lines=[x.strip() for x in log.splitlines() if x.strip().lower().startswith("warning ")]
            error_lines=[x.strip() for x in log.splitlines() if x.strip().lower().startswith("error ")]
            clean_link=not warning_lines and not error_lines
            ok=em.returncode==0 and actual==expected and mapping.get("shifted_layout_proven",False)
            if label=="natural_code_frame": ok=ok and clean_link
            cases.append({"linker":profile,"variant":label,"expected":expected,"actual":actual,"emulator_exit":em.returncode,"map":mapping,"link_warning_lines":warning_lines,"link_error_lines":error_lines,"clean_link":clean_link,"link_log_tail":log.splitlines()[-12:],"passed":ok,"exe":pin(d/"FRAMEFIX.EXE") if (d/"FRAMEFIX.EXE").exists() else None,"map_file":pin(d/"FRAMEFIX.MAP") if (d/"FRAMEFIX.MAP").exists() else None,"link_log":pin(d/"LINK.LOG") if (d/"LINK.LOG").exists() else None,"run_log":pin(d/"RUN.LOG") if (d/"RUN.LOG").exists() else None})
            print(profile,label,actual,mapping.get("prefix_offset_in_group"),flush=True)
    report={"schema":"simant-root-1b73-callback-frame-runtime-fixture-v29","root_reviewed":False,"scope":"test-owned callback fixture only; natural-frame links must be clean; no game link/execution","abi_checks":{"INT33":"sets ES=CS, compares DX to the source-owned MouseCB code offset","INT21":"sets DS=CS, compares DX to three vector callback code offsets","local":"stores LocalCB offset in typed _g5FFA and near-calls it; callback increments _called"},"fixture_sources":{"OWNER":pin(sd/"OWNER.asm"),"CRT":pin(sd/"CRT.c"),"wrong_checker":pin(sd/"CHECK_wrong_dgroup_frame.asm"),"natural_checker":pin(sd/"CHECK_natural_code_frame.asm")},"objects":object_pins,"omf_target_fixups":fixups,"cases":cases,"all_cases_pass":len(cases)==4 and all(x["passed"] for x in cases),"all_natural_frame_links_clean":all(x["clean_link"] for x in cases if x["variant"]=="natural_code_frame"),"negative_control_note":"RTLink 6.10 emits five WRT0082 illegal-fixup warnings for the deliberately wrong DGROUP frame because CALLBACK_TEXT precedes DGROUP. That test-only negative EXE was run to verify its expected FAIL result; no game or original image was involved.","inputs":inputs}
    out=OUT/"callback-frame-runtime-fixture-v29.json"; out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"report":out.relative_to(ROOT).as_posix(),"cases":[{k:x[k] for k in ("linker","variant","actual","passed")} for x in cases],"all_cases_pass":report["all_cases_pass"]},indent=2))
    return 0 if report["all_cases_pass"] else 1
if __name__=="__main__": raise SystemExit(main())


