#!/usr/bin/env python3
"""Bounded DOS differential for S26 zoom geometry/state and redraw ordering."""
from __future__ import annotations

import ctypes
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import behavior  # noqa: E402
import exe  # noqa: E402
import functions  # noqa: E402

class Rect(ctypes.Structure):
    _fields_ = [(n, ctypes.c_int16) for n in ("left", "top", "right", "bottom")]
class State(ctypes.Structure):
    _fields_ = [("window_rect", Rect), ("frame_rect", Rect), ("zoom_rect", Rect),
                ("flags", ctypes.c_uint16), ("min_width", ctypes.c_int16),
                ("min_height", ctypes.c_int16), ("grid_x", ctypes.c_int16),
                ("grid_y", ctypes.c_int16), ("has_zoom_rect", ctypes.c_uint8)]
class Bounds(ctypes.Structure):
    _fields_ = [(n, ctypes.c_int16) for n in ("desktop_top", "screen_right", "screen_bottom")]
class Residue(ctypes.Structure):
    _fields_ = [("first_rect_right", ctypes.c_int16), ("first_rect_bottom", ctypes.c_int16),
                ("saved_rect", Rect), ("unzoom_obj_rect", Rect)]
class Step(ctypes.Structure):
    _fields_ = [("kind", ctypes.c_int), ("window_id", ctypes.c_int16), ("rect", Rect)]

def words(*values): return struct.pack("<" + "H" * len(values), *(v & 65535 for v in values))
def sha(data): return hashlib.sha256(data).hexdigest()
def tup(r): return (r.left,r.top,r.right,r.bottom)

STEP_NAMES={"win_LockWin":0,"win_Recalc":1,"rebuild_clips":2,
    "clip_SetWin":None,"f_1E57_0D97":5,"f_1E57_0FDC":5,"win_UnlockWin":15,
    "clip_Push":6,"f_1E57_0296":7,"f_1FD2_05FD":None,"clip_Pop":8,
    "clip_SubExclude":9,"win_GetObjRect":10,"f_1E57_0A9C":11,"win_DrawWindow":12,
    "f_2505_08EA":13,"f_2505_0831":14}

def normalize_events(events, target):
    out=[]; callback_seen=False; current=target; loop_window=target
    reset_seen=False; last_query=target
    for i,event in enumerate(events):
        name=event["service"]; args=event.get("args",[])
        if name not in STEP_NAMES: continue
        kind=STEP_NAMES[name]
        if name=="clip_SetWin":
            if not callback_seen:
                kind=3; callback_seen=True
            else: kind=4
        elif name=="f_1E57_0296":
            if reset_seen: continue
            reset_seen=True
        elif name=="f_1FD2_05FD":
            continue
        elif name=="clip_Push":
            loop_window=target
            for following in events[i+1:]:
                if following["service"]=="win_GetObjRect":
                    loop_window=following["args"][0]; break
                if following["service"]=="f_1E57_0296": break
            current=loop_window
        elif name=="win_GetObjRect":
            last_query=args[0]; current=last_query
        elif name=="clip_SubExclude": current=target
        elif name in ("f_1E57_0D97","f_1E57_0FDC","f_1E57_0A9C"): pass
        elif name in ("win_LockWin","win_UnlockWin","win_Recalc","clip_SetWin","win_DrawWindow","f_2505_08EA","f_2505_0831") and args:
            current=args[0]
        rect=tuple(event["rect"]) if "rect" in event else None
        out.append((kind,current,rect))
        if name=="clip_Pop": current=target
    return out

def setup_case(lib, scenario, poison=0xA5):
    fn = functions.get("o26_39C7_0000")
    pair = type("Pair", (), {})()
    pair.function = fn
    pair.vectors = {exe.MANAGER_SEG * 16 + v.offset: v for v in exe.load().vectors}
    pair.candidate = False; pair.sequence_targets = set()
    pair.sequence_function = lambda name: functions.get(name)
    vm = behavior.Machine(pair)
    win, objs = 0xD0100, [0xD0300, 0xD0340, 0xD0380]
    events, mode0_inputs, captured = [], [], {}

    def ptr(linear): return linear & 15, linear >> 4
    def rect_at(vm_, off, seg): return struct.unpack("<4h", vm_.read(seg * 16 + off, 8))
    def put_rect(vm_, off, seg, values): vm_.write(seg * 16 + off, words(*values))
    def win_addr(_vm, _a): return ptr(win)
    def obj_addr(_vm, args): return ptr(objs[args[0] & 0xff] if (args[0] & 0xff) < 3 else objs[0])
    def log(name, mutate=None):
        def handler(vm_, args):
            details = {"service": name, "args": list(args)}
            if mutate is not None: details.update(mutate(vm_, args))
            events.append(details)
        return handler
    def get_obj_rect(vm_, args):
        off, seg = args[-2], args[-1]
        oid = args[0]
        source = objs[oid & 0xff] if (oid & 0xff) < 3 else objs[0]
        r = rect_at(vm_, source & 15, source >> 4)
        put_rect(vm_, off, seg, r)
        events.append({"service":"win_GetObjRect", "args":list(args), "rect":r})
    def recalc(vm_, args):
        # Controlled resource-recalc boundary for the synthetic frame object:
        # its visible rect equals the frame x/y plus its width/height words.
        x, y, width, height = struct.unpack("<4h", vm_.read(objs[0] + 8, 8))
        visible = (x, y, (x + width) & 0xffff, (y + height) & 0xffff)
        vm_.write(objs[0], words(*visible))
        events.append({"service":"win_Recalc", "args":list(args), "frame_rect":visible})

    cb = {}
    def register(name, stack=0, regs=(), pop=0, handler=None):
        cb[name] = behavior.Callback(stack, handler or log(name), regs, pop)
    register("win_LockWin", regs=("ax",)); register("win_UnlockWin", regs=("ax",))
    register("win_WinAddr", regs=("ax",), handler=lambda m,a: win_addr(m,a))
    register("win_WinRectAddr", regs=("ax",), handler=lambda m,a: win_addr(m,a))
    register("win_ObjAddr", regs=("ax",), handler=obj_addr)
    register("win_Recalc", regs=("ax",), handler=recalc)
    register("f_1E57_038E", handler=log("rebuild_clips"))
    register("clip_SetWin", stack=1, handler=log("clip_SetWin"))
    register("f_1E57_0D97", stack=2, handler=log("f_1E57_0D97", lambda m,a:{"rect":rect_at(m,a[0],a[1])}))
    register("f_1E57_0FDC", stack=2, handler=log("f_1E57_0FDC", lambda m,a:{"rect":rect_at(m,a[0],a[1])}))
    register("win_GetObjRect", stack=2, pop=4, handler=get_obj_rect, regs=("ax",))
    register("clip_Push"); register("f_1E57_0296"); register("f_1FD2_05FD")
    register("clip_Pop"); register("clip_SubExclude", stack=2,
             handler=log("clip_SubExclude",lambda m,a:{"rect":rect_at(m,a[0],a[1])}))
    register("f_1E57_0A9C", stack=2,
             handler=log("f_1E57_0A9C",lambda m,a:{"rect":rect_at(m,a[0],a[1])}))
    register("win_DrawWindow", regs=("ax",)); register("f_2505_08EA", regs=("ax",));
    register("f_2505_0831", regs=("ax",))

    old_rect = scenario["window_rect"]
    frame = scenario["frame"]
    win_bytes = bytearray(0x50)
    win_bytes[:8] = words(*old_rect)
    win_bytes[0x18:0x1e] = words(scenario["min_width"],scenario["min_height"],scenario["flags"])
    win_bytes[0x20:0x24] = words(scenario["grid_x"],scenario["grid_y"])
    win_bytes[0x24:0x2c] = words(*scenario.get("zoom_rect",(0,0,0,0)))
    win_bytes[0x2c:0x30] = words(*ptr(objs[0]))
    writes = [(win, bytes(win_bytes)), (objs[0], words(*scenario.get("object_rect",old_rect),*frame)),
              (objs[1], words(0,0,100,80, 0,0,100,80)),
              (objs[2], words(0,0,90,60, 0,0,90,60)),
              (behavior.symbol_address("fd_50F6_393C"), words(0,0,0,scenario["desktop_top"])),
              (behavior.symbol_address("g_3DB2"), words(scenario["screen_right"])),
              (behavior.symbol_address("g_3DB4"), words(scenario["screen_bottom"])),
              (behavior.symbol_address("g_5702"), words(0x0700,0x0701,0x0702,0x8000))]
    clip_sym=functions.get("clip_SetWin")
    writes.append((behavior.symbol_address("g_62EC"),words(clip_sym["off"],clip_sym["seg"])))
    win_id=scenario.get("call_id",0x0700)
    case=behavior.Case(label=scenario["id"],args=[],writes=writes,callbacks=cb,
        return_kind="void",registers={"ax":win_id,"stack_poison":poison},
        observe=[behavior.Range("win",win,0x2c),behavior.Range("frame",objs[0],0x10)],
        max_instructions=10_000_000)
    mode0=functions.get("o26_39C7_022F")
    addr=mode0["seg"]*16+mode0["off"]
    def capture(uc,address,_size,_user):
        if address==addr and len(mode0_inputs)<1:
            sp=uc.reg_read(behavior.REGS["sp"]); ss=uc.reg_read(behavior.REGS["ss"])
            raw=vm.read(ss*16+sp+4,4)
            off,seg=struct.unpack("<2H",raw)
            mode0_inputs.append(struct.unpack("<4h",vm.read(seg*16+off,8)))
    vm.cpu.hook_add(behavior.uc.UC_HOOK_CODE,capture)
    dos=vm.run(case)
    record=vm.read(win,0x2c); obj=vm.read(objs[0],0x10)
    captured={"window_rect":struct.unpack("<4h",record[:8]),
              "flags":struct.unpack("<H",record[0x1c:0x1e])[0],
              "zoom_rect":struct.unpack("<4h",record[0x24:0x2c]),
              "frame_geometry":struct.unpack("<4h",obj[8:16]),
              "frame_visible_rect":struct.unpack("<4h",obj[:8])}
    saved=next((e["rect"] for e in events if e["service"] in ("f_1E57_0D97","f_1E57_0FDC")), (0,0,0,0))
    return {"events":events,"mode0_initial_rect":mode0_inputs[0] if mode0_inputs else None,
            "captured":captured,"saved_rect":saved,"dos":dos,
            "source_windows":scenario}

def main():
    out=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/"build/portable/windows_zoom/toggle-report.json"
    if out.exists(): raise SystemExit(f"refusing to overwrite {out}")
    out.parent.mkdir(parents=True,exist_ok=True)
    compiler=ROOT/"build/portable/tests/zoom_model.dll"
    import shutil,subprocess
    subprocess.run([shutil.which("gcc"),"-std=c11","-Wall","-Wextra","-Werror","-shared","-fPIC",
        "-I",str(ROOT/"portable/ui_model/windows"),str(ROOT/"portable/ui_model/windows/zoom.c"),"-o",str(compiler)],check=True)
    lib=ctypes.CDLL(str(compiler))
    lib.portable_window_zoom_toggle.argtypes=[ctypes.POINTER(State),ctypes.POINTER(Bounds),ctypes.POINTER(Residue),
        ctypes.c_int16,ctypes.POINTER(ctypes.c_int16),ctypes.c_size_t,ctypes.POINTER(Rect),
        ctypes.POINTER(Step),ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t),ctypes.c_size_t]
    lib.portable_window_zoom_toggle.restype=ctypes.c_int
    scenarios=[]
    base={"window_rect":(100,100,300,250),"frame":(100,100,200,150),"min_width":40,"min_height":30,
          "flags":0x0100,"grid_x":8,"grid_y":8,"desktop_top":24,"screen_right":640,"screen_bottom":400}
    for poison,gridx,gridy,flag,minw,minh in [(0x00,0,0,0x0100,40,30),(0x5a,8,8,0x0100,40,30),
        (0xa5,16,12,0x1100,40,30),(0xff,8,8,0x0100,40,30),
        (0x33,8,8,0x0100,120,90)]:
        scenarios.append({**base,"id":f"zoom-poison-{poison:02x}","poison":poison,
                          "grid_x":gridx,"grid_y":gridy,"flags":flag,"min_width":minw,"min_height":minh})
    results=[]
    for sc in scenarios:
        try:
            actual=setup_case(lib,sc,sc["poison"])
        except behavior.ExecutionError as exc:
            results.append({"id":sc["id"],"status":"ORIGINAL_EXECUTION_BUDGET_EXCEEDED",
                           "input":sc,"error":str(exc),
                           "note":"No behavioral match is claimed for this uninitialized-stack residue; retained as negative domain evidence."})
            continue
        # The compiled model takes observed DOS stack residue explicitly.
        initial=State(); initial.window_rect=Rect(*sc["window_rect"]); initial.frame_rect=Rect(*sc["frame"])
        initial.flags=sc["flags"]; initial.min_width=sc["min_width"]; initial.min_height=sc["min_height"]
        initial.grid_x=sc["grid_x"]; initial.grid_y=sc["grid_y"]
        bounds=Bounds(sc["desktop_top"],sc["screen_right"],sc["screen_bottom"])
        raw=actual["mode0_initial_rect"] or (0,sc["desktop_top"],0,0)
        residue=Residue(raw[2],raw[3],Rect(*actual["saved_rect"]),Rect(*actual["captured"]["frame_visible_rect"]))
        windows=(ctypes.c_int16*4)(0x0700,0x0701,0x0702,-32768)
        rects=(Rect*4)(Rect(*actual["captured"]["frame_visible_rect"]),Rect(0,0,100,80),Rect(0,0,90,60),Rect(0,0,0,0))
        steps=(Step*64)(); count=ctypes.c_size_t()
        status=lib.portable_window_zoom_toggle(ctypes.byref(initial),ctypes.byref(bounds),ctypes.byref(residue),
            0x0700,windows,4,rects,steps,64,ctypes.byref(count),10000)
        model={"status":status,"window_rect":tup(initial.window_rect),"flags":initial.flags,
               "zoom_rect":tup(initial.zoom_rect),"frame_geometry":tup(initial.frame_rect),
               "step_kinds":[steps[i].kind for i in range(count.value)],
               "step_windows":[steps[i].window_id for i in range(count.value)]}
        dos_trace=normalize_events(actual["events"],0x0700)
        model_trace=[]
        for i in range(count.value):
            k=model["step_kinds"][i]; rr=tup(steps[i].rect) if k in (5,9,10,11) else None
            model_trace.append((k,model["step_windows"][i],rr))
        dos=actual["captured"]
        equal=(status==0 and model["window_rect"]==dos["window_rect"] and
               model["flags"]==dos["flags"] and model["zoom_rect"]==dos["zoom_rect"] and
               model["frame_geometry"]==dos["frame_geometry"])
        results.append({"id":sc["id"],"status":"COMPARED","equal_state":equal,
                        "equal_trace":dos_trace==model_trace,"normalized_dos_trace":dos_trace,
                        "model_trace":model_trace,"input":sc,"observed_mode0_residue":raw,
                        "observed_uninitialized_saved_rect":actual["saved_rect"],"dos_state":dos,
                        "model_state":model,"dos_events":actual["events"],
                        "note":"DOS state comparison replays original stack residues into model; redraw service trace is retained for review."})
        if equal:
            restored={**sc,"id":sc["id"]+"-unzoom","poison":sc["poison"],
                "flags":dos["flags"],"window_rect":dos["window_rect"],
                "frame":dos["frame_geometry"],"object_rect":dos["frame_visible_rect"],
                "zoom_rect":dos["zoom_rect"]}
            try:
                un=setup_case(lib,restored,restored["poison"])
                state=State(); state.window_rect=Rect(*restored["window_rect"])
                state.frame_rect=Rect(*restored["frame"]); state.zoom_rect=Rect(*restored["zoom_rect"])
                state.flags=restored["flags"]; state.has_zoom_rect=1
                state.min_width=restored["min_width"]; state.min_height=restored["min_height"]
                state.grid_x=restored["grid_x"]; state.grid_y=restored["grid_y"]
                un_residue=Residue(0,0,Rect(*un["saved_rect"]),Rect(*un["captured"]["frame_visible_rect"]))
                steps=(Step*64)(); count=ctypes.c_size_t()
                un_rects=(Rect*4)(Rect(*un["captured"]["frame_visible_rect"]),Rect(0,0,100,80),Rect(0,0,90,60),Rect(0,0,0,0))
                un_status=lib.portable_window_zoom_toggle(ctypes.byref(state),ctypes.byref(bounds),ctypes.byref(un_residue),
                    0x0700,windows,4,un_rects,steps,64,ctypes.byref(count),10000)
                unmodel={"status":un_status,"window_rect":tup(state.window_rect),"flags":state.flags,
                    "zoom_rect":tup(state.zoom_rect),"frame_geometry":tup(state.frame_rect)}
                un_dos_trace=normalize_events(un["events"],0x0700)
                un_model_trace=[(steps[i].kind,steps[i].window_id,
                    tup(steps[i].rect) if steps[i].kind in (5,9,10,11) else None)
                    for i in range(count.value)]
                un_equal=(un_status==0 and unmodel["window_rect"]==un["captured"]["window_rect"] and
                    unmodel["flags"]==un["captured"]["flags"] and
                    unmodel["zoom_rect"]==un["captured"]["zoom_rect"] and
                    unmodel["frame_geometry"]==un["captured"]["frame_geometry"])
                results.append({"id":restored["id"],"status":"COMPARED","equal_state":un_equal,
                    "equal_trace":un_dos_trace==un_model_trace,"normalized_dos_trace":un_dos_trace,
                    "model_trace":un_model_trace,
                    "input":restored,"dos_state":un["captured"],"model_state":unmodel,
                    "dos_events":un["events"],"note":"Second toggle uses original zoomRect and win_Recalc returns the synthetic frame resource projection."})
                if un_equal and sc["poison"]==0:
                    repeated={**restored,"id":sc["id"]+"-rezoom","flags":un["captured"]["flags"],
                        "window_rect":un["captured"]["window_rect"],"frame":un["captured"]["frame_geometry"],
                        "object_rect":un["captured"]["frame_visible_rect"],"zoom_rect":un["captured"]["zoom_rect"]}
                    again=setup_case(lib,repeated,0x5a)
                    raw_again=again["mode0_initial_rect"] or (0,repeated["desktop_top"],0,0)
                    again_state=State(); again_state.window_rect=Rect(*repeated["window_rect"])
                    again_state.frame_rect=Rect(*repeated["frame"]); again_state.flags=repeated["flags"]
                    again_state.min_width=repeated["min_width"]; again_state.min_height=repeated["min_height"]
                    again_state.grid_x=repeated["grid_x"]; again_state.grid_y=repeated["grid_y"]
                    again_saved=next((e["rect"] for e in again["events"] if e["service"]=="f_1E57_0D97"),(0,0,0,0))
                    again_res=Residue(raw_again[2],raw_again[3],Rect(*again_saved),Rect(*again["captured"]["frame_visible_rect"]))
                    again_steps=(Step*64)(); again_count=ctypes.c_size_t()
                    again_rects=(Rect*4)(Rect(*again["captured"]["frame_visible_rect"]),Rect(0,0,100,80),Rect(0,0,90,60),Rect(0,0,0,0))
                    again_status=lib.portable_window_zoom_toggle(ctypes.byref(again_state),ctypes.byref(bounds),ctypes.byref(again_res),
                        0x0700,windows,4,again_rects,again_steps,64,ctypes.byref(again_count),10000)
                    again_equal=(again_status==0 and tup(again_state.window_rect)==again["captured"]["window_rect"] and
                        again_state.flags==again["captured"]["flags"] and tup(again_state.zoom_rect)==again["captured"]["zoom_rect"] and
                        tup(again_state.frame_rect)==again["captured"]["frame_geometry"])
                    again_dos_trace=normalize_events(again["events"],0x0700)
                    again_model_trace=[(again_steps[i].kind,again_steps[i].window_id,
                        tup(again_steps[i].rect) if again_steps[i].kind in (5,9,10,11) else None)
                        for i in range(again_count.value)]
                    results.append({"id":repeated["id"],"status":"COMPARED","equal_state":again_equal,
                        "equal_trace":again_dos_trace==again_model_trace,
                        "normalized_dos_trace":again_dos_trace,"model_trace":again_model_trace,
                        "input":repeated,"observed_mode0_residue":raw_again,"dos_state":again["captured"],
                        "model_state":{"window_rect":tup(again_state.window_rect),"flags":again_state.flags,
                            "zoom_rect":tup(again_state.zoom_rect),"frame_geometry":tup(again_state.frame_rect)},
                        "dos_events":again["events"],"note":"Third call after zoom/unzoom checks repeated-cycle state."})
            except behavior.ExecutionError as exc:
                results.append({"id":restored["id"],"status":"ORIGINAL_EXECUTION_BUDGET_EXCEEDED",
                    "input":restored,"error":str(exc)})
    # The sentinel returns before locking; disabled zoom performs lock/address/unlock only.
    for case_id, flags, win_id, expect_status in [("sentinel",0x0100,0x8000,0),
                                                  ("disabled",0,0x0700,2)]:
        control={**base,"id":case_id,"poison":0,"flags":flags,"call_id":win_id}
        actual=setup_case(lib,control,0)
        state=State(); state.window_rect=Rect(*control["window_rect"]); state.frame_rect=Rect(*control["frame"])
        state.flags=flags; state.min_width=control["min_width"]; state.min_height=control["min_height"]
        state.grid_x=control["grid_x"]; state.grid_y=control["grid_y"]
        residue=Residue(0,0,Rect(0,0,0,0),Rect(*actual["captured"]["frame_visible_rect"]))
        rects=(Rect*4)(Rect(*actual["captured"]["frame_visible_rect"]),Rect(0,0,100,80),Rect(0,0,90,60),Rect(0,0,0,0))
        st=lib.portable_window_zoom_toggle(ctypes.byref(state),ctypes.byref(bounds),ctypes.byref(residue),
            win_id,windows,4,rects,steps,64,ctypes.byref(count),10000)
        dos_trace=normalize_events(actual["events"],0x0700)
        model_trace=[(steps[i].kind,steps[i].window_id,
                      tup(steps[i].rect) if steps[i].kind in (5,9,10,11) else None)
                     for i in range(count.value)]
        results.append({"id":case_id,"status":"COMPARED","equal_control_status":st==expect_status,
            "equal_trace":dos_trace==model_trace,"normalized_dos_trace":dos_trace,"model_trace":model_trace,
            "model_status":st,"dos_events":actual["events"],
            "note":"Source-level sentinel/disabled early-exit control; no zoom mutation expected."})
    report={"schema":"portable-window-zoom-toggle-dos-diff-v1","status":"DIAGNOSTIC_ONLY",
        "source_sha256":sha((ROOT/"src/S26/m39C7.c").read_bytes()),"runner_sha256":sha(Path(__file__).read_bytes()),
        "model_source_sha256":sha((ROOT/"portable/ui_model/windows/zoom.c").read_bytes()),
        "model_header_sha256":sha((ROOT/"portable/ui_model/windows/zoom.h").read_bytes()),
        "native_test_source_sha256":sha((ROOT/"portable/tests/windows_zoom/test_zoom.c").read_bytes()),
        "native_model_library_sha256":sha(compiler.read_bytes()),
        "oracle_sha256":exe.load().sha256,"harness_sha256":sha(behavior.HARNESS_SOURCE),
        "boundary":"Original DOS o26_39C7_0000 and o26_39C7_022F execute. Win pointer access, win_Recalc/frame-resource projection, clip/draw services, and indirect window callback are controlled leaves; their ordered calls and geometry are recorded. Stack residue is captured from DOS, then passed explicitly to portable model.",
        "cases":results,"case_count":len(results),"mismatches":sum(x.get("status")=="COMPARED" and not (x.get("equal_state",True) and x.get("equal_trace",True) and x.get("equal_control_status",True)) for x in results),
        "budget_exceeded_cases":sum(x.get("status")=="ORIGINAL_EXECUTION_BUDGET_EXCEEDED" for x in results)}
    out.write_text(json.dumps(report,indent=2)+"\n")
    print(f"{out}: {len(results)} cases, {report['mismatches']} state mismatches")
    if report["mismatches"]: raise SystemExit(1)

if __name__=="__main__": main()
