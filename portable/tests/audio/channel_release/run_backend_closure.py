"""Exercise f_295C_02E8 and its source dispatch bodies to typed hardware leaves."""
from __future__ import annotations
import hashlib,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/"tools")); import behavior  # noqa:E402
OUT=ROOT/"portable/tests/audio/channel_release/evidence/channel-backend-v3.json"
BUILD=ROOT/"build/workers/audio_channel_release/deep-v2"
NATIVE=ROOT/"portable/tests/audio/channel_release/channel_backend_contract.c"
SOURCE=ROOT/"src/root/m295C.c"
ORACLE="aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11"
INPUTS=[SOURCE,ROOT/"src/root/m277E.c",ROOT/"src/root/m290D.c",ROOT/"src/root/m2815.c",
 ROOT/"src/root/m29D6.c",ROOT/"src/root/m29F0.c",ROOT/"src/root/m283E.asm",ROOT/"src/root/m29BF.asm",
 ROOT/"src/data/d55B3_00B8.c",ROOT/"portable/tests/audio/channel_release/run_backend_closure.py",NATIVE,
 ROOT/"portable/tests/audio/channel_release/run_channel_release.py",
 ROOT/"portable/tests/audio/channel_release/channel_release_contract.c",
 ROOT/"portable/tests/audio/channel_release/evidence/channel-release-v1.json",
 ROOT/"portable/tests/audio/channel_release/evidence/channel-backend-v2.json",
 ROOT/"portable/tests/audio/stop_song_dependencies/evidence/dependencies-v4.json",
 ROOT/"tools/behavior.py",ROOT/"tools/exe.py",ROOT/"tools/functions.py",ROOT/"tools/match.py",
 ROOT/"tools/modctx.py",ROOT/"tools/modules.py",ROOT/"tools/compiler.py",ROOT/"tools/omf.py",
 ROOT/"tools/symbols.py",ROOT/"tools/autosearch.py",ROOT/"layout/functions.json",ROOT/"layout/symbols.json",
 ROOT/"layout/manifest.json",ROOT/"layout/toolchain.json",ROOT/"layout/oracle.lock.json",ROOT/"assets/SIMANT.EXE"]
KIND_BACKEND={1:"f_290D_026C",2:"f_2815_024D",3:"f_29D6_0148",4:"f_29D6_015D",5:"f_29D6_0197",6:"f_295C_04FB",7:"f_295C_053D"}
CHANNEL={1:(1,0),2:(2,0),3:(3,0),4:(4,0),5:(5,0),6:(6,1),7:(7,10)}
CASES=[(1,0,60,1,1),(1,0,60,2,1),(1,0,60,1,0),
       (2,0,60,0,0),(3,3,60,0,0),(4,3,60,0,0),(5,3,60,0,0),
       (6,0,60,0,0),(7,12,60,0,0),(1,10,100,0,0)]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def key(p):
 try:return p.resolve().relative_to(ROOT.resolve()).as_posix()
 except ValueError:return str(p.resolve()).replace("\\","/")
def hashes(ps):return {key(p):sha(p) for p in sorted(set(ps),key=lambda x:str(x).casefold())}
def eval_files():
 r=ROOT/"build/behavior/deps/unicorn"
 return [p for p in r.rglob("*") if p.is_file() and (p.suffix.lower()==".py" or p.name.lower()=="unicorn.dll")]
def msc_files():
 c=json.loads((ROOT/"layout/toolchain.json").read_text())["profiles"]["msc600ax"]
 return [(Path(c["directory"])/f).resolve() for f in sorted(c["files"])]
def gcc_files(cc):
 out=[cc.resolve()]
 for x in ("cc1","collect2","ld","as"):
  q=Path(subprocess.check_output([str(cc),f"-print-prog-name={x}"],text=True).strip())
  out.append((q if q.is_absolute() else cc.parent/q).resolve())
 return out
def compile_native(cc,out):
 p=subprocess.run([str(cc),"-std=c11","-O2","-Wall","-Wextra","-Werror",str(NATIVE),"-o",str(out)],cwd=ROOT,capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
def parse_native(text):
 outs=[];channels=[];voice=None;queue=None
 for line in text.splitlines():
  if line.startswith("queue_count="):
   queue=int(line.split("=",1)[1]); continue
  h,*parts=line.split("|"); d=dict(x.split("=",1) for x in parts if "=" in x)
  if h=="out":outs.append((int(d["port"],16),int(d["size"]),int(d["value"],16)))
  elif h=="channel":channels.append([int(x) for x in d["bytes"].split(",")])
  elif h=="voice_owner":voice=[int(d["0"]),int(d["1"])]
  elif h in ("pause","queue_sample","resume"): pass
  else:raise RuntimeError(f"unexpected native row {line!r}")
 return outs,channels,voice,queue
def main():
 if OUT.exists():raise SystemExit(f"refusing to overwrite {OUT}")
 if sha(ROOT/"assets/SIMANT.EXE")!=ORACLE:raise RuntimeError("oracle hash mismatch")
 BUILD.mkdir(parents=True,exist_ok=True)
 cc=Path(shutil.which("gcc") or "").resolve()
 if not cc.is_file():raise RuntimeError("gcc not found")
 ev=eval_files();msc=msc_files();gcc=gcc_files(cc);py=Path(sys.executable).resolve()
 pyid={"path":str(py),"sha256":sha(py),"version":sys.version,"implementation":sys.implementation.name}
 gccver=subprocess.check_output([str(cc),"--version"],text=True).splitlines()[0]
 before=hashes([*INPUTS,*ev,*msc,*gcc])
 native=BUILD/"channel_backend_contract.exe";compile_native(cc,native)
 pair=behavior.PreparedPair("f_295C_02E8",source=SOURCE,out=BUILD/"prepared")
 if pair.strict["claims"].get("f_295C_02E8",{}).get("exact") is not True:raise RuntimeError("strict candidate gate failed")
 ds=0x55B3; seg50=0x50F6
 drivers=seg50*16; chanbase=seg50*16+0x4A4E
 voicebase=behavior.symbol_address("fd_55B3_6B4C")
 busy=behavior.symbol_address("g_7574"); count=ds*16+0x181C
 psg_port=behavior.symbol_address("fd_50F6_4B14")
 info_off,info_seg=0x0200,0xA300; sample_off,sample_seg=0x1000,0xA300
 cases=[]
 for kind,dev,note,loaded,owner in CASES:
  ctype,chnum=CHANNEL[kind]
  if not (dev in (0,3,10,12) and note in (60,100)):raise AssertionError("outside source SfxNote domain")
  driver_rows=bytearray(56*6)
  # Overlay table format is kind word + far pointer to instrument-specific info.
  for i in range(56):
   k=kind if i==dev else 1
   driver_rows[i*6:i*6+6]=k.to_bytes(2,"little",signed=True)+info_off.to_bytes(2,"little")+info_seg.to_bytes(2,"little")
  info_values=(103,-30,-14) if dev==0 else ((69,0,0) if dev==12 else (60,0,0))
  info=bytearray().join((v&0xffff).to_bytes(2,"little") for v in info_values)
  channel_rows=bytearray(5*6)
  second=10 if kind==7 else chnum+1
  rows=[(kind,chnum,9,dev,note,4),(kind,second,0,dev,note,5),
        (kind,chnum+2,9,dev+1,note,6),(kind,chnum+3,9,dev,(note+1)&255,7),(0,0,0,0,0,0)]
  for i,r in enumerate(rows):channel_rows[i*6:i*6+6]=bytes(r)
  voices=bytearray(2*20)
  sample_ptr=sample_off.to_bytes(2,"little")+sample_seg.to_bytes(2,"little") if owner else bytes(4)
  for i in range(2):
   voices[i*20+2:i*20+6]=sample_ptr # snd pointer
   voices[i*20+16:i*20+20]=sample_ptr # owner pointer
  sample=bytearray(20);sample[12:14]=loaded.to_bytes(2,"little")
  writes=[(drivers,bytes(driver_rows)),(chanbase,bytes(channel_rows)),(voicebase,bytes(voices)),
          (sample_seg*16+sample_off,bytes(sample)),(info_seg*16+info_off,bytes(info)),
          (count,b"\0\0"),(busy,(1).to_bytes(2,"little")),(psg_port,(0x220).to_bytes(2,"little")),
          (seg50*16+0x150,bytes(39*4))]
  def reads(machine,port,size):
   if port==0x330:return 0xfe
   if port==0x221:
    for event in reversed(machine.io):
     if event[0]=="out" and event[1]==port:return event[3]
    return 0
   return 0
  ios={p:reads for p in (0x388,0x221,0x330,0x331)}
  observe=[behavior.Range("channels",chanbase,len(channel_rows)),behavior.Range("voices",voicebase,40),
           behavior.Range("freelist",seg50*16+0x150,39*4),behavior.Range("freelist_count",count,2)]
  per_side={};raw={}
  for side,machine in (("dos",pair.original_machine),("candidate",pair.candidate_machine)):
   first=machine.run(behavior.Case(f"deep/k{kind}/d{dev}/n{note}/first",args=[dev,note],writes=writes,
       observe=observe,io_reads=ios,return_kind="void",max_instructions=5000000,max_blocks=500000))
   second_result=machine.run(behavior.Case(f"deep/k{kind}/d{dev}/n{note}/repeat",args=[dev,note],
       observe=observe,io_reads=ios,return_kind="void",max_instructions=5000000,max_blocks=500000),preserve=True)
   raw[side]=[first,second_result]
  if [x["ranges"] for x in raw["dos"]] != [x["ranges"] for x in raw["candidate"]]:
   raise AssertionError({"case":(kind,dev,note,loaded,owner),"dos":raw["dos"],"candidate":raw["candidate"]})
  def outs(r): return [(e[1],e[2],e[3]) for e in r["io"] if e[0]=="out"]
  if [outs(x) for x in raw["dos"]] != [outs(x) for x in raw["candidate"]]:
   raise AssertionError({"case":(kind,dev,note),"DOS_io":[outs(x) for x in raw["dos"]],
                        "candidate_io":[outs(x) for x in raw["candidate"]]})
  if outs(raw["dos"][1]):raise AssertionError({"case":(kind,dev,note),"repeat unexpectedly emitted output":outs(raw["dos"][1])})
  # Native model captures observable writes/driver state. Actual target lane
  # executes the historical per-kind wrapper and its source-proven primitives.
  proc=subprocess.run([str(native),str(kind),str(dev),str(note),str(chnum),str(loaded),str(owner),
                       str(info_values[0]),str(info_values[2])],cwd=ROOT,capture_output=True,text=True,check=True)
  expected_out,expected_channels,expected_voice,expected_queue=parse_native(proc.stdout)
  actual_io=raw["dos"][0]["io"]
  actual_out=[(e[1],e[2],e[3]) for e in actual_io if e[0]=="out"]
  if actual_out!=expected_out:raise AssertionError({"case":(kind,dev,note),"DOS_OUT":actual_out,"native_OUT":expected_out,"io":actual_io})
  actual_channels=[list(bytes.fromhex(raw["dos"][-1]["ranges"]["channels"])[i:i+6]) for i in range(0,len(channel_rows),6)]
  if actual_channels!=expected_channels:raise AssertionError({"case":(kind,dev,note),"DOS_channels":actual_channels,"native":expected_channels})
  voice_raw=bytes.fromhex(raw["dos"][0]["ranges"]["voices"])
  actual_queue=int.from_bytes(bytes.fromhex(raw["dos"][0]["ranges"]["freelist_count"]),"little",signed=True)
  if kind==1:
   actual_owners=[int(any(voice_raw[i*20+16:i*20+20])) for i in range(2)]
   actual_sounds=[int(any(voice_raw[i*20+2:i*20+6])) for i in range(2)]
   freelist=bytes.fromhex(raw["dos"][0]["ranges"]["freelist"])
   actual_ptrs=[(int.from_bytes(freelist[i*4:i*4+2],"little"),
                 int.from_bytes(freelist[i*4+2:i*4+4],"little")) for i in range(actual_queue)]
   expected_ptrs=[(sample_off,sample_seg)]*expected_queue
   if actual_owners!=expected_voice or actual_sounds!=[0,0] or actual_queue!=expected_queue or actual_ptrs!=expected_ptrs:
    raise AssertionError({"case":(kind,dev,note,loaded,owner),"DOS_owners":actual_owners,"model_owners":expected_voice,
                          "DOS_snd":actual_sounds,"DOS_queue":actual_queue,"model_queue":expected_queue,
                          "DOS_queue_ptrs":actual_ptrs,"model_queue_ptrs":expected_ptrs})
  cases.append({"kind":kind,"backend":KIND_BACKEND[kind],"device":dev,"note":note,"loaded":loaded,
   "owner_present":bool(owner),"channel_type":ctype,"channel_number":chnum,"native_expected_out":expected_out,
   "dos_actual_out":actual_out,"dos_repeat_out":outs(raw["dos"][1]),
   "dos_channel_state":actual_channels,"dos_freelist_count":actual_queue,
   "pcm_voice_state":({"snd_live":[int(any(voice_raw[i*20+2:i*20+6])) for i in range(2)],
                       "owner_live":[int(any(voice_raw[i*20+16:i*20+20])) for i in range(2)]} if kind==1 else None),
   "io_reads":sum(1 for e in actual_io if e[0]=="in"),"status":"PASS"})
 after=hashes([*INPUTS,*ev,*msc,*gcc]); pyafter={"path":str(py),"sha256":sha(py),"version":sys.version,"implementation":sys.implementation.name}
 gccafter=subprocess.check_output([str(cc),"--version"],text=True).splitlines()[0]
 if before!=after or pyid!=pyafter or gccver!=gccafter:raise RuntimeError("proof input/tool identity drift")
 report={"schema":"simant-midi-channel-release-deep-diagnostic-v1","status":"PASS_DIAGNOSTIC_NOT_ACCEPTANCE",
  "oracle_sha256":ORACLE,"candidate":pair.identity,"strict_exact_candidate":True,"cases":cases,
  "case_count":len(cases),"mismatches":0,"inputs_before_sha256":before,"inputs_after_sha256":after,
  "python_before":pyid,"python_after":pyafter,"gcc_version_before":gccver,"gcc_version_after":gccafter,
  "native_source_sha256":sha(NATIVE),"native_executable_sha256":sha(native),
  "boundary":{"executed":"f_295C_02E8 and real g_7524-selected wrappers; for DAC the real f_290D_026C cleanup/freelist path also runs",
   "typed_hardware":"hardware-facing I/O is observed as ordered port/width/value writes; deterministic IN providers return ready/readback values",
   "excluded":"physical ISA device timing, hardware acknowledgement/failure modes, DAC timer consumption and freed database-memory lifetime are not modeled"}}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8",newline="")
 print(f"deep channel release diagnostic PASS: {len(cases)} cases")
 print(f"evidence={OUT.relative_to(ROOT).as_posix()}")
if __name__=="__main__":main()
