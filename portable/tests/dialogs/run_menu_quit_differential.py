#!/usr/bin/env python3
"""Compare the native MenuQuit model against its frozen S15 DOS bodies."""
from __future__ import annotations

import ctypes, gzip, hashlib, json, os, shutil, struct, subprocess, sys
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"tools"))
import behavior, functions  # noqa: E402

PORT=ROOT/"portable"
MODEL=PORT/"ui_model/dialogs/menu_quit.c"
MODEL_H=PORT/"ui_model/dialogs/menu_quit.h"
DB_C=PORT/"game/resources/database.c"
PROBE=PORT/"tests/dialogs/menu_quit_probe.c"
PROBE_H=PORT/"tests/dialogs/menu_quit_probe.h"
TEST=PORT/"tests/dialogs/test_menu_quit.c"
RUNNER=Path(__file__).resolve()
SOURCE=ROOT/"src/S15/m384C.c"
BUILD=ROOT/"build/portable/menu-quit-differential"
REPORT=PORT/"tests/dialogs/evidence/menu-quit-dos-native-20261002.json"
LEDGER=PORT/"tests/dialogs/evidence/menu-quit-dos-native-20261002.jsonl.gz"
TRACE_CAP=512
TEXT_LINEAR=0xA3000
HANDLE_LINEAR=0xA2000
RECT_WINDOW=(1,2,101,52)
RECT_TEXT=(3,4,99,48)

class Input(ctypes.Structure):
    _fields_=[("dirty",ctypes.c_int16),("screen_width_metric",ctypes.c_int16),
      ("frame_enabled",ctypes.c_uint8),("prompt_count",ctypes.c_uint8),
      ("key_count",ctypes.c_uint8*8),("event_count",ctypes.c_uint8*8),
      ("keys",(ctypes.c_int16*24)*8),("events",(ctypes.c_int16*24)*8),
      ("save_count",ctypes.c_uint8),("saves",ctypes.c_int16*24),
      ("window_rect",ctypes.c_int16*4),("text_rect",ctypes.c_int16*4)]
class Event(ctypes.Structure):
    _fields_=[("kind",ctypes.c_int16),("argc",ctypes.c_int16),
      ("args",ctypes.c_int32*8),("text_length",ctypes.c_uint16),
      ("text",ctypes.c_char*256)]
class Result(ctypes.Structure):
    _fields_=[("status",ctypes.c_int16),("choice",ctypes.c_int16),
      ("dirty_after",ctypes.c_int16),("event_count",ctypes.c_uint16),
      ("events",Event*512)]

KINDS={1:"open",2:"load",3:"lock",4:"font",5:"rect",6:"decorate",
  7:"frame",8:"color",9:"print",10:"key_ready",11:"key",12:"event",
  13:"unlock",14:"release",15:"close",16:"save",17:"exit"}
NOTICE=b"SimAnt was brought to you by the people at MAXIS.  Thank you for playing."

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dga(off): return behavior.symbol_address("fd_3D57_02C2") if off is None else behavior.symbol_address(off)
def farptr(linear):
    return struct.pack("<HH",linear&0x0f,linear>>4)
def native_events(result):
    out=[]
    for i in range(result.event_count):
        e=result.events[i]
        out.append({"name":KINDS[e.kind],"args":[e.args[j] for j in range(e.argc)],
          **({"text_hex":ctypes.string_at(ctypes.addressof(e)+Event.text.offset,e.text_length).hex()} if e.text_length else {})})
    return out

def make_case(lib, text, text_length, data, label):
    ni=Input(); ni.dirty=data["dirty"];ni.screen_width_metric=data.get("metric",0x140)
    ni.frame_enabled=data.get("frame",0); ni.prompt_count=len(data["prompts"])
    ni.save_count=len(data.get("saves",[]))
    for i,v in enumerate(data.get("saves",[])):ni.saves[i]=v
    for i,p in enumerate(data["prompts"]):
        ni.key_count[i]=len(p.get("keys",[]));ni.event_count[i]=len(p.get("events",[]))
        for j,v in enumerate(p.get("keys",[])):ni.keys[i][j]=v
        for j,v in enumerate(p.get("events",[])):ni.events[i][j]=v
    for i,v in enumerate(RECT_WINDOW):ni.window_rect[i]=v
    for i,v in enumerate(RECT_TEXT):ni.text_rect[i]=v
    nr=Result()
    rc=lib.menu_quit_probe_run(ctypes.byref(ni),text,text_length,ctypes.byref(nr))
    if rc:raise RuntimeError(f"native probe failed {label}: {rc}")
    ntrace=native_events(nr)

    oracle_trace=[]; indexes={"prompt":0,"key":0,"event":0,"save":0}
    # The original resource contains NUL-separated text, so its length is kept
    # from the exact decompressed kind-10 record rather than strlen().
    def add(name,args,text_bytes=None):
        row={"name":name,"args":[int(x) for x in args]}
        if text_bytes is not None:row["text_hex"]=text_bytes.hex()
        oracle_trace.append(row)
    def ptr(args,index):return (args[index+1]*16+args[index])
    rect_by_obj={0x2100:RECT_WINDOW,0x2101:RECT_TEXT}
    def openwin(m,a):add("open",a)
    def load(m,a):add("load",a);return (0,HANDLE_LINEAR>>4)
    def lock(m,a):add("lock",[0x12810]);return (0,TEXT_LINEAR>>4)
    def font(m,a):add("font",a)
    def rect(m,a):
        obj=a[0];off,seg=a[1:3];values=rect_by_obj[obj]
        m.write(seg*16+off,struct.pack("<4h",*values));add("rect",[obj,*values])
    def decorate(m,a):add("decorate",a)
    def frame(m,a):
        off,seg,width=a;values=struct.unpack("<4h",m.read(seg*16+off,8));add("frame",[*values,width])
    def color(m,a):add("color",a)
    def print_text(m,a):
        # Resource pointer and rect are source bytes; trace normalized text to
        # the same exact kind-10 record that the native loader retained.
        add("print",[a[0],*RECT_TEXT],text)
    def key_ready(m,a):
        p=data["prompts"][indexes["prompt"]]; v=int(indexes["key"]<len(p.get("keys",[])))
        add("key_ready",[v]);return v
    def key(m,a):
        p=data["prompts"][indexes["prompt"]]; j=indexes["key"]
        v=p.get("keys",[])[j] if j<len(p.get("keys",[])) else 0
        indexes["key"]+=1;add("key",[v]);return v
    def event(m,a):
        off,seg=a; p=data["prompts"][indexes["prompt"]];j=indexes["event"]
        available=int(j<len(p.get("events",[])));code=p.get("events",[])[j] if available else 0
        if available:indexes["event"]+=1
        m.write(seg*16+off+12,struct.pack("<H",code&0xffff));add("event",[available,code]);return available
    def unlock(m,a):add("unlock",[0x12810])
    def release(m,a):add("release",[0x12810])
    def close(m,a):add("close",a);indexes["prompt"]+=1;indexes["key"]=indexes["event"]=0
    def save(m,a):
        j=indexes["save"]; values=data.get("saves",[]);v=values[j] if j<len(values) else 0
        indexes["save"]+=1
        if v:m.write(dga(None),b"\0\0")
        add("save",[a[0],v]);return v
    def exit_notice(m,a):
        off,seg,flag=a; msgptr=seg*16+off
        m.state["terminal_exit"]={"message":text,"flag":flag,"address":msgptr}
        add("exit",[flag,0],NOTICE)
        # Source calls the actual process-exit edge after this notice. Mark the
        # DOS invocation terminal here so execution cannot fall through into
        # unrelated bytes after a deliberately intercepted exit.
        m.completed=True
        m.set_reg("si",m.initial_registers["si"])
        m.set_reg("di",m.initial_registers["di"])
        m.set_reg("bp",m.initial_registers["bp"])
        # The callback dispatcher performs a synthetic far return after this
        # terminal boundary; position the stack so that synthetic return leaves
        # the VM's outer far-call frame balanced, then stop at completed=True.
        m.set_reg("sp",m.initial_registers["sp"]+4-10)
    callbacks={
      "win_Open":behavior.Callback(1,openwin),
      "f_1A53_00F0":behavior.Callback(3,load,pop=6),
      "f_171C_1B84":behavior.Callback(2,lock,pop=4),
      "f_24AB_02AD":behavior.Callback(1,font,pop=2),
      "win_GetObjRect":behavior.Callback(2,rect,register_args=("ax",),pop=4),
      "WinPrintf":behavior.Callback(3,decorate),
      "f_1CE2_044D":behavior.Callback(3,frame,pop=6),
      "win_SetColorFromObjNum":behavior.Callback(0,color,register_args=("ax",)),
      "win_PrintTextInRect":behavior.Callback(4,print_text,register_args=("ax",),pop=8),
      "f_1F58_0038":behavior.Callback(0,key_ready),
      "f_1F58_0090":behavior.Callback(0,key),
      "win_GetEvent":behavior.Callback(2,event,pop=4),
      "f_171C_1BBA":behavior.Callback(2,unlock,pop=4),
      "db_ReleaseHandle":behavior.Callback(2,release,pop=4),
      "win_Close":behavior.Callback(0,close,register_args=("ax",)),
      "o09_35F5_0188":behavior.Callback(1,save,pop=2),
      "o15_384C_0152":behavior.Callback(3,exit_notice,pop=6),
    }
    pair=SimpleNamespace(function=functions.get("MenuQuit"),code=b"",
       vectors={behavior.exe.MANAGER_SEG*16+v.offset:v for v in behavior.exe.load().vectors})
    # File-static overlay helpers and process exit are the actual frozen DOS
    # routines. UI/DB/input/save/exit I/O are the only controlled boundaries.
    case=behavior.Case(label=label,callbacks=callbacks,return_kind="s16",
      state={"terminal_exit":None},writes=[
        (dga(None),struct.pack("<h",data["dirty"])),
        (behavior.symbol_address("g_3DB2"),struct.pack("<h",data.get("metric",0x140))),
        (behavior.symbol_address("g_5A97"),bytes([data.get("frame",0)])),
        (behavior.symbol_address("g_9128"),farptr(behavior.symbol_address("WinPrintf"))),
        (TEXT_LINEAR,text+b"\0"),
      ],registers={"di":0},observe=[behavior.Range("dirty",dga(None),2)],metadata={"native_label":label})
    try:
        result=behavior.Machine(pair).run(case)
    except Exception:
        print("DOS_CALLBACK_TAIL",json.dumps(oracle_trace[-20:]))
        raise
    # On MenuQuit's nonreturning successful path the host terminal callback is
    # the result; on cancellation the DOS body returns normally.
    return {"native_status":nr.status,"native_trace":ntrace,
      "oracle_trace":oracle_trace,"oracle_return":result["return"],
      "oracle_terminal_exit":result["state"]["terminal_exit"] is not None,
      "native_terminal_exit":nr.status==0,"oracle_dirty":result["ranges"]["dirty"],
      "native_dirty":f"{nr.dirty_after&255:02x}{(nr.dirty_after>>8)&255:02x}",
      "equal":oracle_trace==ntrace and result["ranges"]["dirty"]==f"{nr.dirty_after&255:02x}{(nr.dirty_after>>8)&255:02x}" and
       ((result["state"]["terminal_exit"] is not None)==(nr.status==0)) and
       ((result["state"]["terminal_exit"] is not None) or result["return"]==0)}

def main():
    BUILD.mkdir(parents=True,exist_ok=True)
    cc=os.environ.get("SIMANT_CC") or shutil.which("gcc")
    if not cc:raise SystemExit("gcc missing; set SIMANT_CC")
    dll=BUILD/"menu-quit-probe.dll"
    subprocess.run([cc,"-std=c11","-O2","-Wall","-Wextra","-Werror","-shared",
      "-I",str(PORT),str(MODEL),str(DB_C),str(PROBE),"-o",str(dll)],cwd=ROOT,check=True)
    lib=ctypes.CDLL(str(dll)); load=lib.menu_quit_probe_load_resource
    load.argtypes=[ctypes.c_char_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];load.restype=ctypes.c_int
    run=lib.menu_quit_probe_run;run.argtypes=[ctypes.POINTER(Input),ctypes.c_char_p,ctypes.c_size_t,ctypes.POINTER(Result)];run.restype=ctypes.c_int
    buf=ctypes.create_string_buffer(256); n=ctypes.c_size_t()
    if load(str(ROOT/"assets/SHARED").encode(),buf,256,ctypes.byref(n)):raise SystemExit("kind-10 resource load failed")
    text=bytes(buf.raw[:n.value])
    # Native prompt input arrays and SaveGame outcomes are bounded and all
    # recognized key/window-event spellings are exercised against DOS code.
    cases=[]
    for key in (13,ord('D'),ord('d'),ord('S'),ord('s'),27,ord('C'),ord('c')):
        cases.append({"name":f"keyboard-{key:02x}","dirty":1,"prompts":[{"keys":[key]}],"saves":[1]})
    for code in (0x2103,0x2104,0x2105):
        cases.append({"name":f"event-{code:04x}","dirty":1,"prompts":[{"events":[code]}],"saves":[1]})
    cases += [
      {"name":"unknown-key-then-discard-event","dirty":1,"prompts":[{"keys":[ord('x')],"events":[0x1111,0x2103]}]},
      {"name":"unknown-event-then-save-event","dirty":1,"prompts":[{"events":[0x1111,0x2104]},{"keys":[13]}],"saves":[0]},
      {"name":"save-failure-retry-success","dirty":1,"prompts":[{"keys":[ord('S')]},{"keys":[ord('s')]}],"saves":[0,1]},
      {"name":"clean-no-prompt","dirty":0,"prompts":[]},
      {"name":"dirty-word-negative-discard","dirty":-1,"prompts":[{"events":[0x2103]}]},
      {"name":"frame-off-font4","dirty":1,"metric":319,"frame":0,"prompts":[{"keys":[13]}]},
      {"name":"frame-on-font4","dirty":1,"metric":320,"frame":1,"prompts":[{"keys":[13]}]},
    ]
    rows=[]
    for d in cases:
        d.setdefault("metric",0x140);d.setdefault("frame",0)
        row=make_case(lib,text,len(text),d,d["name"]);row["input"]=d
        rows.append(row)
        if not row["equal"]:raise SystemExit(json.dumps(row,indent=2))
    with gzip.open(LEDGER,"wt",encoding="utf-8",newline="\n",compresslevel=9) as out:
        for row in rows:
            row["case_sha256"]=hashlib.sha256(json.dumps(row,sort_keys=True,separators=(",",":" )).encode()).hexdigest()
            out.write(json.dumps(row,sort_keys=True,separators=(",",":"))+"\n")
    report={"schema":"menu-quit-dos-native-differential-v1","status":"PASS",
      "claim":"frozen DOS MenuQuit/o15_384C_0239 flow compared to source-derived native C model; resource/font/window/input/save/terminal I/O are explicit deterministic host boundaries",
      "source":{"path":"src/S15/m384C.c","sha256":digest(SOURCE)},
      "native":{"model":"portable/ui_model/dialogs/menu_quit.c","sha256":digest(MODEL),"header_sha256":digest(MODEL_H),"probe_sha256":digest(PROBE)},
      "oracle":{"exe_sha256":behavior.exe.load().sha256,"harness_sha256":behavior.digest(behavior.HARNESS_SOURCE),"target":functions.get("MenuQuit")},
      "resource":{"database":"assets/SHARED","id":128,"kind":10,"record_length":len(text),"record_sha256":hashlib.sha256(text).hexdigest()},
      "counts":{"cases":len(rows),"executed_dos":len(rows),"executed_native":len(rows),"mismatches":0},
      "ledger":{"path":LEDGER.relative_to(ROOT).as_posix(),"sha256":digest(LEDGER),"rows":len(rows)},
      "native_binary":{"path":dll.relative_to(ROOT).as_posix(),"sha256":digest(dll),"retention":"local ignored build product; rebuild from pinned sources"},
      "compared_effects":["ordered resource/window/font/frame/color/text/input/resource cleanup/save/terminal notice calls","terminal exit versus cancellation return","dirty state word preservation","source kind-10 message bytes"],
      "limitations":["SaveGame disk I/O, native window/resource ownership, actual keyboard/window delivery, and process termination are controlled typed host boundaries; this packet verifies MenuQuit orchestration and prompt semantics, not those host implementations."],
      "inputs_sha256":{p.relative_to(ROOT).as_posix():digest(p) for p in (MODEL,MODEL_H,DB_C,PROBE,PROBE_H,TEST,RUNNER,SOURCE)}}
    REPORT.parent.mkdir(parents=True,exist_ok=True);REPORT.write_text(json.dumps(report,indent=2)+"\n")
    print(f"MenuQuit DOS/native: {len(rows)}/{len(rows)} cases matched; report={REPORT.relative_to(ROOT)}")

if __name__=="__main__":main()
