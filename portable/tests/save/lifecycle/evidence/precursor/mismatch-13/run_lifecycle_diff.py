"""Paired original-DOS/native save-lifecycle boundary tests; diagnostic only."""
from __future__ import annotations

import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
import behavior

EVIDENCE = ROOT / "portable/tests/save/lifecycle/evidence"
WORK = ROOT / "build/workers/save_lifecycle"
SOURCE = ROOT / "src/S09/m35F5.c"
INVENTORY = ROOT / "portable/tests/dialogs/evidence/savegame-format-source-inventory-v1/save-records.json"
ROW_MAP = ROOT / "portable/tests/save/evidence/legacy-save-codec-v3/binding-map.json"
SYMBOLS = ROOT / "layout/symbols.json"

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

class Spec(C.Structure):
    _fields_ = [("index", C.c_uint16), ("element_size", C.c_uint16),
                ("element_count", C.c_uint16), ("payload_offset", C.c_uint32),
                ("source_expression", C.c_char_p)]

class Binding(C.Structure):
    _fields_ = [("bytes", C.POINTER(C.c_uint8)), ("extent", C.c_size_t),
                ("storage_order", C.c_int)]

class State(C.Structure):
    _fields_ = [("last_filename", C.c_char * 100), ("dirty", C.c_int16),
                ("load_mode", C.c_int16)]

SELECT = C.CFUNCTYPE(C.c_int16, C.c_void_p, C.c_char_p, C.c_char_p, C.c_int16,
                     C.POINTER(C.c_char), C.c_size_t)
DIRTY = C.CFUNCTYPE(C.c_int16, C.c_void_p)
CONFIRM = C.CFUNCTYPE(C.c_int16, C.c_void_p, C.c_char_p)
OPEN = C.CFUNCTYPE(C.c_int32, C.c_void_p, C.c_char_p, C.c_int)
READWRITE = C.CFUNCTYPE(C.c_int32, C.c_void_p, C.c_int32, C.POINTER(C.c_uint8), C.c_uint16)
READONLY = C.CFUNCTYPE(C.c_int32, C.c_void_p, C.c_int32, C.POINTER(C.c_uint8), C.c_uint16)
CLOSE = C.CFUNCTYPE(C.c_int32, C.c_void_p, C.c_int32)
REMOVE = C.CFUNCTYPE(C.c_int32, C.c_void_p, C.c_char_p)
MESSAGE = C.CFUNCTYPE(None, C.c_void_p, C.c_int, C.c_char_p)
STATE_CB = C.CFUNCTYPE(None, C.c_void_p, C.POINTER(State))
VOID_CB = C.CFUNCTYPE(None, C.c_void_p)
COMPLETE_CB = C.CFUNCTYPE(None, C.c_void_p, C.c_int32, C.c_int32, C.c_int16)
MODE_CB = C.CFUNCTYPE(None, C.c_void_p, C.c_int16)

class Host(C.Structure):
    _fields_ = [("context", C.c_void_p), ("select_path", SELECT),
                ("dirty_prompt", DIRTY), ("confirm_overwrite", CONFIRM),
                ("open_file", OPEN), ("read_record", READONLY),
                ("write_record", READWRITE), ("close_file", CLOSE),
                ("remove_file", REMOVE), ("show_message", MESSAGE),
                ("before_load", STATE_CB), ("load_stream_complete", COMPLETE_CB),
                ("refresh_after_load", VOID_CB), ("update_after_load", MODE_CB),
                ("rebuild_after_load", VOID_CB), ("stop_song", VOID_CB)]

OPEN_NAMES = {0:"read-only", 1:"read-write-existing", 2:"create-truncate"}
MESSAGE_NAMES = {0:"open-error", 1:"read-error", 2:"write-error", 3:"saved"}

def load_native():
    WORK.mkdir(parents=True, exist_ok=True)
    dll = WORK / f"lifecycle-native-{os.getpid()}.dll"
    command = ["gcc", "-shared", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
               "-I", str(ROOT / "portable"), str(ROOT / "portable/game/save/legacy_codec.c"),
               str(ROOT / "portable/game/save/lifecycle.c"), "-o", str(dll)]
    built = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if built.returncode:
        raise RuntimeError(f"native lifecycle build failed:\n{built.stdout}{built.stderr}")
    lib = C.CDLL(str(dll))
    lib.portable_legacy_save_record_specs.argtypes = [C.POINTER(C.c_size_t)]
    lib.portable_legacy_save_record_specs.restype = C.POINTER(Spec)
    lib.portable_savegame_save.argtypes = [C.POINTER(State), C.POINTER(Spec), C.c_size_t,
        C.POINTER(Binding), C.c_size_t, C.POINTER(Host), C.c_int16]
    lib.portable_savegame_save.restype = C.c_int16
    lib.portable_savegame_load.argtypes = [C.POINTER(State), C.POINTER(Spec), C.c_size_t,
        C.POINTER(Binding), C.c_size_t, C.POINTER(Host), C.c_int16]
    lib.portable_savegame_load.restype = C.c_int16
    return lib, dll

def specs_for(lib):
    count = C.c_size_t()
    ptr = lib.portable_legacy_save_record_specs(C.byref(count))
    if count.value != 307:
        raise RuntimeError(f"legacy codec yielded {count.value} rows, expected 307")
    return ptr, count.value

def source_byte(address: int) -> int:
    x = address & 0xffffffff
    x ^= x >> 11
    x = (x * 0x045D9F3B) & 0xffffffff
    x ^= x >> 16
    return (x ^ (x >> 8) ^ (x >> 24)) & 255

class Scenario:
    def __init__(self, cfg):
        self.cfg = cfg
        self.events = []
        self.raw = []
        self.select_i = self.open_i = self.close_i = self.write_i = self.read_i = self.remove_i = 0
        self.prompt_i = self.confirm_i = self.read_offset = 0
        self.last_io_error = None
        self.buffers = []
        self.binding_array = None
        self._load_stream = b""
        self.remove_i = 0

    def state_tuple(self):
        if hasattr(self, "native_state"):
            s = self.native_state.contents if isinstance(self.native_state, C.POINTER(State)) else self.native_state
            return [bytes(s.last_filename).split(b"\0",1)[0].decode("latin1"), int(s.dirty), int(s.load_mode)]
        m = self.machine
        return [m.read(self.filename_addr,100).split(b"\0",1)[0].decode("latin1"),
                int.from_bytes(m.read(self.dirty_addr,2),"little",signed=True),
                int.from_bytes(m.read(self.loadmode_addr,2),"little",signed=True)]

    def event(self, name, *args):
        self.events.append({"event":name,"args":list(args),"state":self.state_tuple()})

    def pop(self, key, index_name, default):
        arr = self.cfg.get(key, [])
        i = getattr(self, index_name)
        setattr(self, index_name, i+1)
        return arr[i] if i < len(arr) else default

    def selected(self, title, verb, save):
        item = self.pop("selections","select_i",None)
        if item is None:
            self.event("select",title,verb,save,0,"")
            return 0, ""
        self.event("select",title,verb,save,1,item)
        return 1,item

    def opened(self, path, mode):
        result = self.pop("opens","open_i",-1)
        self.last_io_error = "open" if result <= 0 else None
        self.event("open",OPEN_NAMES[mode],path,result)
        return result

    def read_data(self, buffer, count, original_machine=None, farptr=None):
        idx = self.read_i
        scripted = self.cfg.get("read_results", {})
        result = int(scripted.get(str(idx), count))
        nwrite = count if result == count else max(0, min(count, int(self.cfg.get("read_partial_bytes",0))))
        data = bytes(((self.read_offset + j) & 255) for j in range(nwrite))
        if original_machine is None:
            if nwrite: C.memmove(buffer, data, nwrite)
        else:
            if nwrite: original_machine.write(farptr, data)
        digest = sha(data)
        self.event("read",idx,count,result,nwrite,digest)
        self.read_i += 1
        self.read_offset += count
        return result

    def write_data(self, buffer, count, original_machine=None, farptr=None):
        idx = self.write_i
        result = int(self.cfg.get("write_results",{}).get(str(idx),count))
        data = (C.string_at(buffer,count) if original_machine is None else original_machine.read(farptr,count))
        self.event("write",idx,count,result,sha(data))
        self.write_i += 1
        if result == -1: self.last_io_error = "write"
        return result

    def close_data(self, fd):
        result = int(self.pop("close_results","close_i",0))
        self.event("close",fd,result)
        return result

    def snapshot_rows_native(self):
        return [C.string_at(b, len(b)) for b in self.buffers]

    def make_native(self, lib, row_map):
        self.native_state = State()
        self.native_state.last_filename = (self.cfg.get("last","").encode("latin1") + b"\0")[:100]
        self.native_state.dirty = self.cfg.get("dirty",0)
        self.native_state.load_mode = self.cfg.get("load_mode",0)
        spec_ptr, count = specs_for(lib)
        arr = (Binding * count)()
        self.buffers = []
        for i,row in enumerate(row_map):
            n = row["serialized_bytes"]
            if row["portable_member"] == "fd_50F6_0EAC":
                buf = (C.c_uint8 * n).from_address(C.addressof(self.native_state) + State.load_mode.offset)
            else:
                buf = (C.c_uint8 * n)()
            addr = row["source_linear_address"]
            if row["portable_member"] != "fd_50F6_0EAC":
                for j in range(n): buf[j] = source_byte(addr+j)
            self.buffers.append(buf)
            arr[i] = Binding(C.cast(buf,C.POINTER(C.c_uint8)),n,0)
        self.binding_array = arr
        keep = []

        @SELECT
        def select(_ctx,title,verb,save,out,cap):
            ok,path = self.selected(title.decode(),verb.decode(),int(save))
            data=path.encode("latin1")+b"\0"
            if ok:
                if len(data)>cap: return 0
                C.memmove(out,data,len(data))
            return ok
        @DIRTY
        def dirty(_ctx):
            result=int(self.pop("dirty_results","prompt_i",0))
            self.event("dirty-prompt",result)
            return result
        @CONFIRM
        def confirm(_ctx,text):
            result=int(self.pop("confirm_results","confirm_i",0))
            self.event("confirm-overwrite",text.decode("latin1"),result)
            return result
        @OPEN
        def opn(_ctx,path,mode): return self.opened(path.decode("latin1"),int(mode))
        @READONLY
        def rd(_ctx,fd,buf,count): return self.read_data(buf,int(count))
        @READWRITE
        def wr(_ctx,fd,buf,count): return self.write_data(buf,int(count))
        @CLOSE
        def close(_ctx,fd): return self.close_data(int(fd))
        @REMOVE
        def remove(_ctx,path):
            result=int(self.pop("remove_results","remove_i",0))
            self.event("remove",path.decode("latin1"),result)
            return result
        @MESSAGE
        def message(_ctx,kind,text):
            kind=int(kind); msg=text.decode("latin1") if text else None
            self.event("message",MESSAGE_NAMES[kind],msg)
        @STATE_CB
        def before(_ctx,state): self.event("before-load")
        @COMPLETE_CB
        def complete(_ctx,start,end,mode): self.event("stream-complete",int(start),int(end),int(mode))
        @VOID_CB
        def refresh(_ctx): self.event("refresh")
        @MODE_CB
        def update(_ctx,mode): self.event("update-after-load",int(mode))
        @VOID_CB
        def rebuild(_ctx): self.event("rebuild")
        @VOID_CB
        def stop(_ctx): self.event("stop-song")
        callbacks=[select,dirty,confirm,opn,rd,wr,close,remove,message,before,complete,refresh,update,rebuild,stop]
        keep.extend(callbacks)
        host=Host(C.c_void_p(1),*callbacks)
        self._keep_native=keep
        return spec_ptr,count,host

def farstr(machine,args,index,maxlen=2048):
    off,seg=args[index:index+2]
    start=seg*16+off
    raw=bytearray()
    for i in range(maxlen):
        b=machine.read(start+i,1)[0]
        if b==0: break
        raw.append(b)
    return raw.decode("latin1")

def dos_state(machine, addresses):
    filename,dirty,loadmode=addresses
    return [machine.read(filename,100).split(b"\0",1)[0].decode("latin1"),
            int.from_bytes(machine.read(dirty,2),"little",signed=True),
            int.from_bytes(machine.read(loadmode,2),"little",signed=True)]

def dos_callbacks(sc):
    callbacks={}
    def wrap(name,words,fn):
        callbacks[name]=behavior.Callback(words,handler=fn)
    def select(machine,args):
        title=farstr(machine,args,2); verb=farstr(machine,args,4); save=args[6]
        ok,path=sc.selected(title,verb,save)
        off,seg=args[0:2]
        if ok: machine.write(seg*16+off,path.encode("latin1")+b"\0")
        return ok
    def dirty(machine,args):
        result=int(sc.pop("dirty_results","prompt_i",0)); sc.event("dirty-prompt",result); return result
    def confirm(machine,args):
        prompt=farstr(machine,args,0); result=int(sc.pop("confirm_results","confirm_i",0))
        sc.event("confirm-overwrite",prompt,result); return result
    def opn(machine,args):
        path=farstr(machine,args,0); flags=args[2]
        mode=2 if flags & 0x0300 else (0 if (flags & 3)==0 else 1)
        result=sc.opened(path,mode)
        sc.raw.append({"name":"open","args":args,"path":path,"mode_word":flags,
                       "extra_word":args[3] if mode==2 and len(args)>3 else None})
        return result
    def rd(machine,args):
        fd,off,seg,count=args
        return sc.read_data(None,count,machine,seg*16+off)
    def wr(machine,args):
        fd,off,seg,count=args
        return sc.write_data(None,count,machine,seg*16+off)
    def close(machine,args): return sc.close_data(args[0])
    def remove(machine,args):
        path=farstr(machine,args,0); result=int(sc.pop("remove_results","remove_i",0))
        sc.event("remove",path,result); return result
    def io_error(machine,args):
        text=farstr(machine,args,0)
        if text == "  Read error  \ngame not loaded":
            sc.event("message","read-error",text)
            return None
        kind={"open":"open-error","write":"write-error"}.get(sc.last_io_error,"open-error")
        sc.event("message",kind,None)
        sc.raw.append({"name":"io-error-text","text":text})
        return None
    def read_error(machine,args):
        text=farstr(machine,args,0)
        sc.event("message","read-error",text)
        return None
    def saved(machine,args):
        text=farstr(machine,args,0); sc.event("message","saved",text); return None
    def before(machine,args): sc.event("before-load"); return None
    def complete(machine,args):
        if len(args)!=5: raise RuntimeError(f"unexpected stream completion args {args}")
        start=args[0] | (args[1]<<16)
        end=args[2] | (args[3]<<16)
        if start & 0x80000000: start-=0x100000000
        if end & 0x80000000: end-=0x100000000
        sc.event("stream-complete",start,end,args[4])
        sc.raw.append({"name":"f_15D9_009C","raw_args":args})
        return None
    def refresh(machine,args): sc.event("refresh"); return None
    def update(machine,args): sc.event("update-after-load",args[0]); return None
    def rebuild(machine,args): sc.event("rebuild"); return None
    def stop(machine,args): sc.event("stop-song"); return None
    wrap("o09_35F5_03C6",7,select)
    wrap("o15_384C_0239",1,dirty)
    wrap("f_1C62_0415",3,confirm)
    wrap("open",4,opn); wrap("read",4,rd); wrap("write",4,wr)
    wrap("close",1,close); wrap("remove",2,remove)
    wrap("f_1C62_00AC",2,io_error); wrap("f_1C62_00C0",2,saved)
    wrap("o09_35F5_0D7A",0,before); wrap("f_15D9_009C",5,complete)
    wrap("o11_35F5_0000",0,refresh); wrap("o11_35F5_0088",1,update)
    wrap("o09_35F5_0DBB",0,rebuild); wrap("StopSong",0,stop)
    return callbacks

class OverlayVectorCallbacks(dict):
    """Keep cross-overlay hooks at manager vectors, not colliding physical offsets."""
    def __init__(self, values, machine, source_unit):
        super().__init__(values)
        self.machine=machine
        self.source_unit=source_unit
    def items(self):
        yield from super().items()
        # Machine.run installs both physical symbol addresses and RTLink vector
        # addresses. Overlay segments intentionally alias each other, so only
        # the latter identifies an external S11/S15 service call here.
        for name in self:
            sym=behavior.symbol(name)
            if sym.get("unit") == "S11" and self.source_unit == "S09":
                addr=sym["seg"]*16+sym["off"]
                self.machine.callback_addresses.pop(addr,None)

CASES=[
 {"name":"save-cancel","op":"save","selections":[],"dirty":1},
 {"name":"save-useLast-overwrite","op":"save","last":"OLD.ANT","use_last":1,"opens":[7],"confirm_results":[0],"close_results":[-1]},
 {"name":"save-overwrite-reselect-cancel","op":"save","last":"OLD.ANT","use_last":1,"opens":[7],"confirm_results":[1],"selections":[]},
 {"name":"save-create-open-fail","op":"save","selections":["NEW.ANT"],"opens":[-1,-1],"dirty":1},
 {"name":"save-write-minus-one","op":"save","selections":["WRITEFAIL.ANT"],"opens":[-1,7],"write_results":{"0":-1},"close_results":[-1],"remove_results":[-1],"dirty":1},
 {"name":"save-positive-short-write","op":"save","last":"SHORT.ANT","use_last":1,"opens":[7],"write_results":{"0":1}},
 {"name":"load-cancel","op":"load","selections":[],"dirty":0},
 {"name":"load-dirty-cancel","op":"load","selections":[],"dirty":1,"dirty_results":[2]},
 {"name":"load-dirty-save-cancel-then-prompt-cancel","op":"load","selections":[],"dirty":1,"dirty_results":[1,2]},
 {"name":"load-open-fail","op":"load","selections":["MISSING.ANT"],"opens":[-1],"dirty":1,"dirty_results":[0]},
 {"name":"load-partial-read","op":"load","selections":["PARTIAL.ANT"],"opens":[7],"read_results":{"1":5},"read_partial_bytes":5,"dirty":0,"load_mode":2},
 {"name":"load-complete-stop-song","op":"load","selections":["FULL.ANT"],"opens":[7],"dirty":0,"load_mode":0,"stop_song":1},
 {"name":"load-complete-keep-song","op":"load","selections":["FULL2.ANT"],"opens":[7],"dirty":0,"load_mode":2,"stop_song":0},
]

def original_case(pair,cfg,row_map,addresses):
    sc=Scenario(cfg); sc.machine=pair.original_machine
    sc.filename_addr,sc.dirty_addr,sc.loadmode_addr=addresses
    writes=[]
    for row in row_map:
        addr=row["source_linear_address"]; n=row["serialized_bytes"]
        writes.append((addr,bytes(source_byte(addr+i) for i in range(n))))
    filename,dirty,loadmode=addresses
    state_writes=[(filename,(cfg.get("last","").encode("latin1")+b"\0").ljust(100,b"\0")),
                  (dirty,int(cfg.get("dirty",0)).to_bytes(2,"little",signed=True)),
                  (loadmode,int(cfg.get("load_mode",0)).to_bytes(2,"little",signed=True)),
                  (behavior.symbol_address("fd_3D57_07AA"),int(cfg.get("inactive_flag",1 if not cfg.get("stop_song",0) else 0)).to_bytes(2,"little",signed=True))]
    callbacks=OverlayVectorCallbacks(dos_callbacks(sc),pair.original_machine,"S09")
    case=behavior.Case("save-lifecycle/"+cfg["name"],args=[cfg.get("use_last",0)] if cfg["op"]=="save" else [],
        writes=writes+state_writes,callbacks=callbacks,return_kind="s16",
        observe=[behavior.Range("last_filename",filename,100),behavior.Range("dirty",dirty,2),behavior.Range("load_mode",loadmode,2)],
        registers={"ax":0},max_instructions=8_000_000,max_blocks=1_000_000)
    target="o09_35F5_0188" if cfg["op"]=="save" else "LoadGame"
    result=pair.original_machine.run(case,function=target)
    final_rows=[pair.original_machine.read(r["source_linear_address"],r["serialized_bytes"]) for r in row_map]
    return sc,result,final_rows

def native_case(lib,cfg,row_map):
    sc=Scenario(cfg); spec_ptr,count,host=sc.make_native(lib,row_map)
    state=sc.native_state
    if cfg["op"]=="save":
        rc=lib.portable_savegame_save(C.byref(state),spec_ptr,count,sc.binding_array,count,C.byref(host),cfg.get("use_last",0))
    else:
        rc=lib.portable_savegame_load(C.byref(state),spec_ptr,count,sc.binding_array,count,C.byref(host),cfg.get("stop_song",0))
    return sc,rc,sc.snapshot_rows_native()

def run():
    WORK.mkdir(parents=True,exist_ok=True); EVIDENCE.mkdir(parents=True,exist_ok=True)
    lib,dll=load_native()
    table=json.loads(INVENTORY.read_text(encoding="utf-8"))["table"]["records"]
    row_map=json.loads(ROW_MAP.read_text(encoding="utf-8"))["rows"]
    if len(table)!=307 or len(row_map)!=307: raise RuntimeError("pinned source row inventory must have 307 rows")
    addresses=(behavior.symbol_address("fd_50F6_3862"),behavior.symbol_address("fd_3D57_02C2"),behavior.symbol_address("fd_50F6_0EAC"))
    pair=behavior.PreparedPair("LoadGame",source=SOURCE,out="build/workers/save_lifecycle/prepared")
    results=[]; failures=[]
    for cfg in CASES:
        dos,dos_result,dos_rows=original_case(pair,cfg,row_map,addresses)
        native,native_result,native_rows=native_case(lib,cfg,row_map)
        checks={"return":dos_result["return"]==native_result,
                "events":dos.events==native.events,
                "state":dos_state(pair.original_machine,addresses)==native.state_tuple(),
                "row_bytes":dos_rows==native_rows}
        if cfg["op"]=="save":
            checks["write_row_count"]=dos.write_i==native.write_i
            checks["read_row_count"]=dos.read_i==native.read_i
        row={"name":cfg["name"],"operation":cfg["op"],"status":"PASS" if all(checks.values()) else "MISMATCH",
             "checks":checks,"original_return":dos_result["return"],"native_return":native_result,
             "original_event_count":len(dos.events),"native_event_count":len(native.events),
             "original_write_calls":dos.write_i,"native_write_calls":native.write_i,
             "original_read_calls":dos.read_i,"native_read_calls":native.read_i,
             "original_events":dos.events,"native_events":native.events,"raw_dos_callback_inputs":dos.raw,
             "final_state_original":dos_state(pair.original_machine,addresses),"final_state_native":native.state_tuple(),
             "final_row_sha256_original":sha(b"".join(dos_rows)),"final_row_sha256_native":sha(b"".join(native_rows))}
        results.append(row)
        if row["status"]!="PASS": failures.append(cfg["name"])
        print(f"{cfg['name']}={'PASS' if row['status']=='PASS' else 'MISMATCH'} original={dos_result['return']} native={native_result} events={len(dos.events)}")
    identity={"schema":"simant-save-lifecycle-paired-dos-native-v1","status":"PASS" if not failures else "MISMATCH",
      "source":{"path":"src/S09/m35F5.c","sha256":sha(SOURCE.read_bytes())},
      "native_sources":[{"path":"portable/game/save/lifecycle.c","sha256":sha((ROOT/'portable/game/save/lifecycle.c').read_bytes())},
                        {"path":"portable/game/save/lifecycle.h","sha256":sha((ROOT/'portable/game/save/lifecycle.h').read_bytes())}],
      "spec_inventory_sha256":sha(INVENTORY.read_bytes()),"source_row_map_sha256":sha(ROW_MAP.read_bytes()),
      "oracle_sha256":behavior.exe.load().sha256,"harness_sha256":behavior.digest(behavior.HARNESS_SOURCE),
      "prepared_pair_identity":pair.identity,"native_library_sha256":sha(dll.read_bytes()),
      "scenario_count":len(results),"passed":len(results)-len(failures),"failed_cases":failures,
      "limitations":["Controlled file/UI callbacks are paired; no live filesystem is accessed.",
          "Save/Load stream payload semantics are checked separately by the V3 binding packet; this suite checks per-row callback order, state transitions and partial-read behavior.",
          "The original S09 reset and post-load rebuild bodies are represented by named controlled callbacks in this bounded lifecycle contract; they are not claimed as native game-state rebuilds.",
          "Platform CRT error text is normalized to its source call class; read-error literal and successful save text remain compared exactly."],
      "cases":results}
    output=EVIDENCE/"paired-report.json"
    output.write_text(json.dumps(identity,indent=2)+"\n",encoding="utf-8",newline="")
    return identity

if __name__=="__main__":
    report=run()
    raise SystemExit(0 if report["status"]=="PASS" else 1)
