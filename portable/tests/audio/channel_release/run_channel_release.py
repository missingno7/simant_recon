"""DOS differential for f_295C_02E8 channel-note release semantics."""
from __future__ import annotations
import hashlib, json, shutil, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/"tools"))
import behavior  # noqa: E402

OUT=ROOT/"portable/tests/audio/channel_release/evidence/channel-release-v1.json"
BUILD=ROOT/"build/workers/audio_channel_release/final"
NATIVE=ROOT/"portable/tests/audio/channel_release/channel_release_contract.c"
SOURCE=ROOT/"src/root/m295C.c"
ORACLE_SHA="aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11"
BACKENDS={1:"f_290D_026C",2:"f_2815_024D",3:"f_29D6_0148",4:"f_29D6_015D",
          5:"f_29D6_0197",6:"f_295C_04FB",7:"f_295C_053D"}
CHANNELS={1:(1,0),2:(2,0),3:(3,0),4:(4,0),5:(5,0),6:(6,1),7:(7,10)}
# Source-backed combinations: instrument ID / kind / SFX note source row /
# output-channel type and number produced by root:m277E setup loops.
CASES=[(1,0,60),(2,0,60),(3,3,60),(4,3,60),(5,3,60),(6,0,60),(7,12,60),(1,10,100)]
INPUTS=[SOURCE,ROOT/"src/root/m277E.c",ROOT/"src/root/m290D.c",ROOT/"src/root/m2815.c",
 ROOT/"src/root/m29D6.c",ROOT/"src/data/d55B3_00B8.c",
 ROOT/"portable/tests/audio/channel_release/run_channel_release.py",NATIVE,
 ROOT/"tools/behavior.py",ROOT/"tools/exe.py",ROOT/"tools/functions.py",ROOT/"tools/match.py",
 ROOT/"tools/modctx.py",ROOT/"tools/modules.py",ROOT/"tools/compiler.py",ROOT/"tools/omf.py",
 ROOT/"tools/symbols.py",ROOT/"tools/autosearch.py",ROOT/"layout/functions.json",
 ROOT/"layout/symbols.json",ROOT/"layout/manifest.json",ROOT/"layout/toolchain.json",
 ROOT/"layout/oracle.lock.json",ROOT/"assets/SIMANT.EXE"]

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def key(p):
 try: return p.resolve().relative_to(ROOT.resolve()).as_posix()
 except ValueError: return str(p.resolve()).replace("\\","/")
def hashes(paths): return {key(p):sha(p) for p in sorted(set(paths),key=lambda x:str(x).casefold())}
def evaluator_files():
 r=ROOT/"build/behavior/deps/unicorn"
 return [p for p in r.rglob("*") if p.is_file() and (p.suffix.lower()==".py" or p.name.lower()=="unicorn.dll")]
def msc_files():
 d=json.loads((ROOT/"layout/toolchain.json").read_text())["profiles"]["msc600ax"]
 return [(Path(d["directory"])/x).resolve() for x in sorted(d["files"])]
def gcc_files(cc):
 out=[cc.resolve()]
 for t in ("cc1","collect2","ld","as"):
  value=subprocess.check_output([str(cc),f"-print-prog-name={t}"],text=True).strip()
  p=Path(value); out.append((p if p.is_absolute() else cc.parent/p).resolve())
 return out
def compile_native(cc,out):
 p=subprocess.run([str(cc),"-std=c11","-O2","-Wall","-Wextra","-Werror",str(NATIVE),"-o",str(out)],
  cwd=ROOT,capture_output=True,text=True)
 if p.returncode: raise RuntimeError(p.stdout+p.stderr)
def parse_native(text):
 events=[]; states=[]
 for line in text.splitlines():
  kind,*fields=line.split("|"); data=dict(x.split("=",1) for x in fields if "=" in x)
  if kind=="backend": events.append({"kind":int(data["kind"]),"name":data["name"],"note":int(data["note"]),
                                      "channel":int(data["channel"]),"device":int(data["device"])})
  elif kind=="channel": states.append([int(x) for x in data["bytes"].split(",")])
  elif kind!="repeat": raise RuntimeError(f"unknown native output: {line}")
 return events,states

def case_bytes(kind,dev,note):
 row=bytearray(56*6)
 for i in range(56):
  k=kind if i==dev else 1
  ptr=(0x0100).to_bytes(2,"little")+(0xA300).to_bytes(2,"little")
  row[i*6:i*6+6]=k.to_bytes(2,"little")+ptr
 ch=bytearray(5*6)
 type_,num=CHANNELS[kind]
 specs=[(type_,num,9,dev,note,4),(type_,num+1,0,dev,note,5),
        (type_,num+2,9,dev+1,note,6),(type_,num+3,9,dev,(note+1)&255,7),(0,0,0,0,0,0)]
 for i,s in enumerate(specs): ch[i*6:i*6+6]=bytes(s)
 return bytes(row),bytes(ch)

def main():
 if OUT.exists(): raise SystemExit(f"refusing to overwrite immutable receipt {OUT}")
 if sha(ROOT/"assets/SIMANT.EXE")!=ORACLE_SHA: raise RuntimeError("oracle hash mismatch")
 BUILD.mkdir(parents=True,exist_ok=True)
 cc=Path(shutil.which("gcc") or "").resolve()
 if not cc.is_file(): raise RuntimeError("gcc not found")
 evals=evaluator_files(); msc=msc_files(); gcc=gcc_files(cc); py=Path(sys.executable).resolve()
 py_id={"path":str(py),"sha256":sha(py),"version":sys.version,"impl":sys.implementation.name}
 gcc_ver=subprocess.check_output([str(cc),"--version"],text=True).splitlines()[0]
 before=hashes([*INPUTS,*evals,*msc,*gcc])
 native=BUILD/"channel_release.exe"; compile_native(cc,native)
 pair=behavior.PreparedPair("f_295C_02E8",source=SOURCE,out=BUILD/"prepared")
 if pair.strict["claims"].get("f_295C_02E8",{}).get("exact") is not True:
  raise RuntimeError("strict candidate failed its existing module gate")
 table=0x50F60; channels=0x50F60+0x4A4E
 callbacks={}
 callback_events={"dos":[],"candidate":[]}
 for kind,name in BACKENDS.items():
  def handler(machine,args,k=kind,n=name):
   side="candidate" if machine.candidate else "dos"
   if len(args)!=3: raise RuntimeError(f"{n} receives unexpected call words: {args}")
   callback_events[side].append({"kind":k,"name":n,"note":args[0],"channel":args[1],"device":args[2]})
  callbacks[name]=behavior.Callback(3,handler=handler)
 reports=[]
 for kind,dev,note in CASES:
  ch_type,ch_num=CHANNELS[kind]
  if not (0<=dev<=54 and note in (60,100)): raise AssertionError("test escaped source SfxNote domain")
  drv,chan=case_bytes(kind,dev,note)
  callbacks_by_side={"dos":[],"candidate":[]}
  # Each case starts a fresh VM snapshot, then the second invocation is an
  # explicit repeat over the first call's state.
  for side,machine in (("dos",pair.original_machine),("candidate",pair.candidate_machine)):
   callback_events[side].clear()
   setup=behavior.Case(f"release/k{kind}/d{dev}/n{note}/first",args=[dev,note],
    writes=[(table,drv),(channels,chan)],callbacks=callbacks,
    observe=[behavior.Range("channels",channels,len(chan))],return_kind="void")
   first=machine.run(setup)
   second=machine.run(behavior.Case(f"release/k{kind}/d{dev}/n{note}/repeat",args=[dev,note],
    callbacks=callbacks,observe=[behavior.Range("channels",channels,len(chan))],return_kind="void"),preserve=True)
   callbacks_by_side[side]=list(callback_events[side])
   if side=="dos": dos_raw=[first,second]
   else: candidate_raw=[first,second]
  if callbacks_by_side["candidate"]!=callbacks_by_side["dos"]:
   raise AssertionError({"case":(kind,dev,note),"dos":callbacks_by_side["dos"],"candidate":callbacks_by_side["candidate"]})
  if [r["ranges"] for r in dos_raw] != [r["ranges"] for r in candidate_raw]:
   raise AssertionError({"case":(kind,dev,note),"dos_ranges":[r["ranges"] for r in dos_raw],
                        "candidate_ranges":[r["ranges"] for r in candidate_raw]})
  proc=subprocess.run([str(native),str(kind),str(dev),str(note),str(ch_type),str(ch_num)],
   cwd=ROOT,capture_output=True,text=True,check=True)
  native_events,native_state=parse_native(proc.stdout)
  if native_events!=callbacks_by_side["dos"]:
   raise AssertionError({"case":(kind,dev,note),"dos_events":callbacks_by_side["dos"],"native":native_events})
  actual=[list(bytes.fromhex(dos_raw[-1]["ranges"]["channels"])[i:i+6]) for i in range(0,len(chan),6)]
  if actual!=native_state: raise AssertionError({"case":(kind,dev,note),"dos_state":actual,"native_state":native_state})
  reports.append({"kind":kind,"backend":BACKENDS[kind],"device":dev,"note":note,
   "channel_type":ch_type,"channel_number":ch_num,"callbacks":callbacks_by_side["dos"],
   "repeat_added_callbacks":len(callbacks_by_side["dos"])-2,
   "final_channels":actual,"status":"PASS"})
 after=hashes([*INPUTS,*evals,*msc,*gcc])
 py_after={"path":str(py),"sha256":sha(py),"version":sys.version,"impl":sys.implementation.name}
 gcc_after=subprocess.check_output([str(cc),"--version"],text=True).splitlines()[0]
 if before!=after or py_id!=py_after or gcc_ver!=gcc_after: raise RuntimeError("pinned input/tool identity drift")
 report={"schema":"simant-midi-channel-release-diagnostic-v1","status":"PASS_DIAGNOSTIC_NOT_ACCEPTANCE",
  "oracle_sha256":ORACLE_SHA,"candidate":pair.identity,"strict_exact_candidate":True,
  "cases":reports,"case_count":len(reports),"dos_candidate_mismatches":0,
  "native_source_sha256":sha(NATIVE),"native_executable_sha256":sha(native),
  "inputs_before_sha256":before,"inputs_after_sha256":after,"python_before":py_id,"python_after":py_after,
  "gcc_version_before":gcc_ver,"gcc_version_after":gcc_after,
  "scope":{"compared":["ordered dispatch kind and function target","3-word backend call arguments",
                          "all six bytes of each channel record through sentinel","repeat-call effects"],
    "hardware":"backend entry is the boundary; physical MIDI, FM, PSG, and DAC register/ISA effects are excluded",
    "domain":"device indices in active SfxNote records and active instrument-kind mappings are source-derived; invalid table indexes/kinds are excluded"}}
 OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8",newline="")
 print(f"channel release PASS_DIAGNOSTIC: {len(reports)} source-derived kind/device cases")
 print(f"evidence={OUT.relative_to(ROOT).as_posix()}")

if __name__=="__main__": main()
