"""Conditional viewport control using current whole S26 TU and original DOS helpers.

This is research, not acceptance. It models cursor delivery, button lifetime,
cursor warp and rendering; the DOS resize/constraint, lock/repoint/recalc,
resize-icon lookup and viewport-size producers execute. Resources are loaded
from assets into isolated VMs; their bytes never enter a source or executable.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys

sys.dont_write_bytecode = True
from resources_probe import find_root, fresh_output, collect_report, resource_payload

ROOT = find_root()
OUT = None
sys.path.insert(0,str(ROOT / "tools"))
import behavior as b
from behavior_suites import memory as heap
import compiler
import exe
import functions
import match
import modctx

def sha(data): return hashlib.sha256(data).hexdigest()
def far(off,seg): return struct.pack("<HH",off,seg)
def s16(v): return struct.unpack("<h",b.words(v))[0]
def rect(raw): return list(struct.unpack("<4h",raw))

def resource(ident,kind):
    return resource_payload(ROOT,ident,kind)

def prepare(target="o26_39C7_0671",key="S26:39C7",active=("o26_39C7_0671","o26_39C7_022F")):
    program_raw=(ROOT/"src/program.json").read_bytes()
    program=json.loads(program_raw)
    manifest_raw=(ROOT/"layout/manifest.json").read_bytes()
    module=next(u for u in program["modules"] if u["key"]==key)
    raw=(ROOT/module["source"]).read_bytes()
    if sha(raw)!=module["source_sha256"]: raise ValueError("source inventory drift")
    source=raw.decode("latin1")
    compiler.WORK=OUT/"compiler"
    ctx=modctx.resolve(func=target,source=ROOT/module["source"],profile=module["profile"],flags=module["flags"])
    compiled=compiler.compile_c(source,ctx.profile,ctx.flags)
    tag=key.replace(":","_")
    (OUT/(tag+"-compile.log")).write_text(compiled.log)
    if not compiled.ok: raise RuntimeError(compiled.log)
    (OUT/(tag+"-candidate.obj")).write_bytes(compiled.obj)
    obj=modctx.read_obj(compiled.obj)
    _,public=match.public_in(obj,target)
    segment=public["segment"]
    rawcode=obj.segments[segment]
    fn=functions.get(target)
    linked=b.ExecutionBinder(match.Target(fn["unit"],b.CODE_SEG,0,len(rawcode)),obj,segment,None,
                             ctx.placements_bind,span=(0,len(rawcode))).bind()
    if linked.unbound: raise ValueError(linked.unbound)
    pair=b.PreparedPair.__new__(b.PreparedPair)
    pair.function=fn
    pair.sequence_targets=frozenset(active)
    pair.code=linked.candidate
    pair.candidate_entry=(b.CODE_SEG,public["offset"])
    pair.candidate_entries={}
    pair.delegate={}
    for p in obj.publics+getattr(obj,"local_publics",[]):
        if p["segment"]!=segment: continue
        name=p["name"][1:] if p["name"].startswith(("_","@")) else p["name"]
        address=b.CODE_SEG*16+p["offset"]
        pair.candidate_entries[name]=address
        if name not in pair.sequence_targets: pair.delegate[address]=b.symbol(name)
    pair.vectors={exe.MANAGER_SEG*16+v.offset:v for v in exe.load().vectors}
    pair.identity={"oracle_sha256":exe.load().sha256,"source":module["source"],
                   "source_sha256":sha(raw),"object_sha256":sha(compiled.obj),
                   "linked_code_sha256":sha(linked.candidate),"profile":ctx.profile,"flags":ctx.flags,
                   "program_read_time_sha256":sha(program_raw),"manifest_read_time_sha256":sha(manifest_raw)}
    pair.original_machine=b.Machine(pair)
    pair.candidate_machine=b.Machine(pair,True)
    return pair

DG=match.DGROUP_SEG*16
WINDOW=0xA102*16
HEAPSEG=0xA100
HANDLESEG=0x90FF

def noop(m,args): return None
def warp(m,args):
    m.set_word(b.symbol_address("g_9122"),args[0])
    m.set_word(b.symbol_address("g_9124"),args[1])
def held_init(m,args): m.state["held_count"]=0
def held(m,args):
    m.state["held_count"]+=1
    if m.state["held_count"]==1:
        m.set_word(b.symbol_address("g_9122"),m.state["cursor"][0])
        m.set_word(b.symbol_address("g_9124"),m.state["cursor"][1])
        return 1
    return 0

def make_case(label,root_height,screen_height,cursor,*,top=22,width=404,icon_stale=0):
    raw=bytearray(resource(0,0))
    # Actual shipped window/object records; only the logical root origin varies.
    struct.pack_into("<4h",raw,136+8,14,top,width,root_height)
    struct.pack_into("<4h",raw,0,14,top,14+width,top+root_height)
    struct.pack_into("<H",raw,0x1c,0x050e|0x200)
    # Pointers are repointed by the real first lock; Win rect initially agrees.
    count=struct.unpack_from("<H",raw,0xc)[0]
    raw[0x2c:0x2c+count*4]=bytes(count*4)
    arena=heap.heap_case(label,[(128,1,{"size":len(raw),"lock":0,"name":b"viewport"}),(0x500-128,0x80)],
        handles=[0],heap_seg=HEAPSEG,heap_paras=0x500,handle_seg=HANDLESEG,
        discard_header_seg=0xA900,discard_data_seg=0xA902)
    # Fresh lower-right resize control produced by f_2505_06B9:
    # border 2, bitmap 16x16, centre = root right/bottom minus 10.
    right,bottom=14+width,top+root_height
    icon=(right-18,bottom-18-icon_stale,right-2,bottom-2-icon_stale)
    hot=b.symbol_address("fd_5071_03C4")
    cb=b.symbol("f_00BA_01C3")
    writes=list(arena.writes)+[(WINDOW,bytes(raw)),(DG+0x644c,b.words(1,0)),
        (DG+0x8cf2,bytes(45*4+45)),(b.symbol_address("win_handles"),far(0xfffc,HANDLESEG)),
        (b.symbol_address("win_numOfWindows"),b.words(45)),(b.symbol_address("g_6300"),b.words(0)),
        (b.symbol_address("g_5702"),b.words(0,0x8000)),
        (b.symbol_address("g_3DB2"),b.words(640)),(b.symbol_address("g_3DB4"),b.words(screen_height)),
        (b.symbol_address("fd_50F6_393C"),b.words(0,0,640,17)),
        (b.symbol_address("g_62EC"),far(cb["off"],cb["seg"])),
        (b.symbol_address("MapPlane"),b.words(1)),(b.symbol_address("fd_50F6_0508"),b.words(0,0)),
        (b.symbol_address("fd_55B3_19BE"),b.words(16,16)),
        (hot-2,b.words(45,1)+b.words(*icon)+bytes(4)+b.words(0xf084)+bytes(4))]
    callbacks={n:b.Callback(words,noop,regs,pop) for n,words,regs,pop in (
        ("f_1E57_0351",0,(),0),("f_1E57_038E",0,(),0),
        ("GRectInvOutline",3,(),0),("f_21FA_0B4B",2,(),4),
        ("f_2505_08EA",0,("ax",),0),("f_2505_0831",0,("ax",),0),
        ("win_FlushEvents",0,(),0),("win_CasteControlChanged",0,(),0),
        ("win_ModeControlChanged",0,(),0),("f_00F8_00A4",0,(),0),("f_00F8_0002",0,(),0))}
    callbacks.update({"f_1B73_09E9":b.Callback(2,warp),"ButtonHeldInit":b.Callback(0,held_init),
                      "ButtonHeld":b.Callback(0,held)})
    return b.Case(label=label,args=[0,0],writes=writes,observe=[
        b.Range("window",WINDOW,len(raw)),b.Range("viewport_counts",b.symbol_address("fd_50F6_10DE"),4),
        b.Range("viewport_rect",b.symbol_address("fd_50F6_110C"),8)],callbacks=callbacks,
        return_kind="void",callee_pop=4,state={"cursor":list(cursor)},observe_at_calls=False,
        metadata={"screen":[640,screen_height],"root":[14,top,width,root_height],"icon":list(icon),
                  "cursor":list(cursor),"fresh_icon":not icon_stale})

def file_pin(path):
    raw=path.read_bytes()
    return {"sha256":sha(raw),"size":len(raw)}

def support_pins():
    support={}
    toolroot=(ROOT/"tools").resolve()
    for module in tuple(sys.modules.values()):
        name=getattr(module,"__file__",None)
        if not name: continue
        path=Path(name).resolve()
        if path.is_file() and path.is_relative_to(toolroot):
            support[path.relative_to(ROOT).as_posix()]=file_pin(path)
    return dict(sorted(support.items()))

def main():
    global OUT
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",required=True,help="fresh directory beneath repository build/; relative paths use the repository root")
    args=parser.parse_args()
    try:
        OUT=fresh_output(ROOT,args.out)
    except ValueError as exc:
        parser.error(str(exc))
    resource_report=collect_report(ROOT)
    resource_report["probe_sha256"]=sha((Path(__file__).parent/"resources_probe.py").read_bytes())
    (OUT/"resource-observation.json").write_text(json.dumps(resource_report,indent=2)+"\n",encoding="utf-8")
    pair=prepare()
    cases=[]
    for screen,initial in ((350,325),(480,357)):
        for y in (0,screen-1):
            cases.append(make_case(f"boundary/{screen}/{y}",initial,screen,(407,y)))
        # Maximal class-aligned legal sizes, and a moved window whose bottom
        # is outside the screen. This does not increase root height.
        maxheight=325 if screen==350 else 453
        cases.append(make_case(f"max/{screen}",maxheight,screen,(639,screen-1),width=628))
        cases.append(make_case(f"moved/{screen}",maxheight,screen,(407,screen-1),top=screen-8))
    # Necessary-premise contrast: source permits an out-of-screen cursor.
    cases.append(make_case("negative/outside-cursor",453,480,(407,540)))
    # Necessary-premise contrast: an icon from earlier geometry removes the bound.
    cases.append(make_case("negative/stale-icon",453,480,(407,479),icon_stale=96))
    results=[]
    for case in cases:
        try:
            comparison=pair.compare(case)
        except Exception:
            machine=pair.original_machine
            print(json.dumps({"case":case.label,"trace":machine.raw_trace,
                              "regs":{r:machine.reg(r) for r in b.REGS}},indent=2))
            raise
        if not comparison.equal: raise RuntimeError({"case":case.label,"diff":comparison.diff})
        out=comparison.original["ranges"]
        dims=struct.unpack("<2h",bytes.fromhex(out["viewport_counts"]))
        result={"label":case.label,"equal":comparison.equal,"input":case.metadata,
                "root_rect":rect(bytes.fromhex(out["window"])[:8]),
                "object4_rect":rect(bytes.fromhex(out["viewport_rect"])),"rows":dims[0],"columns":dims[1],
                "max_cache_index":(dims[0]-1)*40+dims[1]-1,
                "oracle_block_count":comparison.original["blocks"],
                "candidate_block_count":comparison.candidate["blocks"]}
        if not case.label.startswith("negative/") and not result["max_cache_index"]<1200:
            raise RuntimeError(result)
        if case.label.startswith("negative/") and not result["max_cache_index"]>=1200:
            raise RuntimeError("contrast failed: "+str(result))
        results.append(result)
    cache_pair=prepare("ZapEuMapAt","root:0250",("ZapEuMapAt","InvalEuMap"))
    cache_results=[]
    for target,args in (("ZapEuMapAt",[1,1,30]),("InvalEuMap",[1,30,1,30])):
        target_pair=cache_pair
        function=functions.get(target)
        target_pair.function=function
        public=target_pair.candidate_entries[target]
        target_pair.candidate_entry=(b.CODE_SEG,public-b.CODE_SEG*16)
        adjacent=b.symbol_address("fd_50F6_1F26")
        case=b.Case(label="conditional-cache-crossing/"+target,args=args,
            writes=[(b.symbol_address("fd_50F6_10DE"),b.words(31,22)),
                    (b.symbol_address("MapPlane"),b.words(1)),
                    (b.symbol_address("fd_50F6_0508"),b.words(0,0)),(adjacent,b.words(0x1234,0x5678))],
            observe=[b.Range("spider_image_dimensions",adjacent,4)],return_kind="void")
        comparison=cache_pair.compare(case)
        if not comparison.equal: raise RuntimeError({"target":target,"diff":comparison.diff})
        observed=comparison.original["ranges"]["spider_image_dimensions"]
        if observed!="ffff7856": raise RuntimeError(observed)
        cache_results.append({"target":target,"equal":True,"world_or_rectangle":args,
            "viewport":[22,31],"write_index":1201,"historical_write":"50F6:1F26",
            "separate_source_owner":"fd_50F6_1F26.x (spider image width)",
            "before":"34127856","after":observed,
            "scope":"Conditional function-entry state produced by the out-of-domain resize contrasts; no shipped UI reachability claim."})
    inputs=["src/program.json","src/S26/m39C7.c","src/root/m0250.c","src/root/m00BA.c","src/root/m20E8.c",
            "src/root/m23AE.c","src/root/m2505.c","src/root/m218D.c","src/root/m1FD2.c","src/root/m1B73.asm",
            "src/root/m208F.c","src/root/m22BF.c","src/root/m00F8.c","src/S09/m35F5.c",
            "src/S00/m31AD.asm","src/S00/m31AD_2AB4.asm","src/state/remaining-misc-storage.c",
            "src/state/remaining-ui-state.c","src/state/remaining-window-state.c","src/state/window-initialized-views.c",
            "tools/behavior.py","tools/compiler.py","tools/modctx.py","tools/match.py",
            "layout/toolchain.json","layout/oracle.lock.json","assets/HCEGANT.DAT","assets/HCEGANT.NDX",
            "assets/SHARED.DAT","assets/SHARED.NDX"]
    report={"schema":"viewport-layout-current-conditional-control-v1","admitted":False,
        "root_reviewed":False,"compiled_current_whole_tus":[pair.identity,cache_pair.identity],
        "inputs":{p:{"sha256":sha((ROOT/p).read_bytes()),"size":(ROOT/p).stat().st_size} for p in inputs},
        "packet":{name:file_pin(Path(__file__).parent/name) for name in ("review.md","resize_probe.py","resources_probe.py")},
        "support_tools":support_pins(),"unicorn_version":getattr(b.uc,"__version__",None),
        "resource_observation_sha256":sha((OUT/"resource-observation.json").read_bytes()),
        "cases":results,"cache_crossing_controls":cache_results,
        "limits":"Finite corroboration of the fresh-icon/in-screen-cursor premise; not whole-game reachability or all-resource proof. Renderer, warp and button delivery are explicit parametric boundaries."}
    (OUT/"receipt.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"equal":len(results),"rows":[r["rows"] for r in results],"cache_pairs_equal":len(cache_results),"receipt":str(OUT/"receipt.json")},indent=2))

if __name__=="__main__": main()
