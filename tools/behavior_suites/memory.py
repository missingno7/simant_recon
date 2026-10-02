"""Differential contracts for four original DOS Ralloc heap helpers.

Runs hash-locked DOS code and a separately compiled whole-module candidate via
tools/behavior.py. Fixtures contain paragraph-aligned headers, free links,
master handles, manager counters, and deterministic user data. No proof category
is assigned by this suite.
"""
from __future__ import annotations
import argparse, hashlib, json, random, struct, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import behavior, match
from behavior_ledger import CaseLedger

SUITE = "ralloc_memory_v2_stateful"
DG = match.DGROUP_SEG
# Keep the actual heap and master handle table in the same disjoint arenas used
# by the neighboring DOS windows suite. The reserved stack remains in DGROUP.
HEAP_SEG, HEAP_PARAS = 0xA100, 0x100
HANDLE_SEG, MASTER_FIRST, MASTER_ONE_PAST = 0xA000, 0x0100, 0x0104
DISCARD_HEADER_SEG, DISCARD_DATA_SEG = 0xA200, 0xA202

def w(v): return struct.pack("<H", v & 0xffff)
def dw(v): return struct.pack("<I", v & 0xffffffff)
def far(off, seg): return struct.pack("<HH", off & 0xffff, seg & 0xffff)
def dga(off): return DG * 16 + off

def memory_globals_writes(*, heap_start, heap_end, free_head, master_off, master_seg,
                          age=100, allocated_handles=0, live_handles=0,
                          free_paras=0, used_paras=0, type_paras=None):
    """Return the shared DOS Ralloc DGROUP/BSS setup writes.

    `master_off:master_seg` is s_2F46, the far one-past handle pointer. Callers
    place the actual four-byte handle slots themselves and set each block's
    signed `handle` offset relative to this pointer.
    """
    type_paras = type_paras or {0: 0, 1: 0, 3: 0}
    values = {0x2f36:type_paras.get(0,0), 0x2f38:type_paras.get(3,0),
              0x2f3a:type_paras.get(1,0), 0x2f3c:used_paras,
              0x2f3e:free_paras, 0x2f40:used_paras+free_paras,
              0x2f42:allocated_handles, 0x2f44:live_handles, 0x2f4a:64}
    return [(dga(0x91a4),far(0,heap_start)), (dga(0x91a8),far(0,heap_end)),
            (dga(0x91ac),far(0,free_head)), (dga(0x91aa),w(heap_end)),
            (dga(0x8c70),w(heap_end)), (dga(0x2f46),far(master_off,master_seg)),
            (dga(0x2f34),w(1)), (dga(0x2f30),dw(age)), (dga(0x2f2a),w(0))] + [
            (dga(o),w(v)) for o,v in values.items()]

def header(paras, kind, *, handle=0, size=0, lock=0, age=0, nxt=0, prev=0, attr=0, name=b"fixture"):
    name = name[:13].ljust(13, b"\0")
    signed_handle = handle if handle < 0x8000 else handle - 0x10000
    return struct.pack("<hI HBBI HHB", signed_handle, size & 0xffffffff, paras & 0xffff,
                       kind & 255, lock & 255, age & 0xffffffff, nxt & 0xffff,
                       prev & 0xffff, attr & 255) + name

def heap_case(label, rows, *, args=(), handles=(), result="s16", extra=(), contract="", content_seed=0):
    """rows=(paras,type,options), in physical address order."""
    starts, seg = [], HEAP_SEG
    for row in rows:
        paras, kind = row[:2]
        opts = dict(row[2]) if len(row) > 2 else {}
        starts.append((seg, paras, kind, opts)); seg += paras
    end = seg
    if not starts or end > HEAP_SEG + HEAP_PARAS: raise ValueError("heap fixture out of bounds")
    free = [b for b in starts if b[2] == 0x80]
    occupied = [b for b in starts if b[2] not in (0x80, 2)]
    # Real master tables grow down from s_2F46 (f_171C_0A5C starts at
    # s_2F46-1). Initialize only the slots used by this case.
    writes = [(HANDLE_SEG*16+0x00c0,b"\0"*(MASTER_ONE_PAST-0x00c0))]
    for i, (hidx, block) in enumerate(zip(handles, occupied)):
        slot = MASTER_FIRST - 4 * hidx
        block[3]["handle"] = (slot - MASTER_ONE_PAST) & 0xffff
        writes.append((HANDLE_SEG * 16 + slot, far(0, block[0] + 2)))
    counters = {0x2f36: 0, 0x2f38: 0, 0x2f3a: 0}
    for _, paras, kind, _ in starts:
        if kind in (0, 1, 3): counters[{0:0x2f36,1:0x2f3a,3:0x2f38}[kind]] += paras
    total_free = sum(p for _, p, k, _ in starts if k == 0x80)
    total_used = sum(p for _, p, k, _ in starts if k != 0x80)
    for i, (s, paras, kind, opts) in enumerate(starts):
        if kind == 0x80:
            j = next(j for j, item in enumerate(free) if item[0] == s)
            prev = free[j-1][0] if j else 0; nxt = free[j+1][0] if j+1 < len(free) else 0
        else: prev = nxt = 0
        body = header(paras, kind, handle=opts.get("handle",0), size=opts.get("size",max(0,(paras-2)*16)),
                      lock=opts.get("lock",0), age=opts.get("age",i+1), nxt=nxt, prev=prev,
                      attr=opts.get("attr",0), name=opts.get("name",f"B{i}".encode()))
        body += bytes((content_seed + i*43 + j*29 + kind) & 255 for j in range(paras*16-32))
        writes.append((s*16, body))
    writes += memory_globals_writes(heap_start=HEAP_SEG,heap_end=end,
        free_head=free[0][0] if free else 0,master_off=MASTER_ONE_PAST,master_seg=HANDLE_SEG,
        allocated_handles=len(handles),live_handles=len(handles),free_paras=total_free,
        used_paras=total_used,type_paras={0:counters[0x2f36],1:counters[0x2f3a],3:counters[0x2f38]})
    # A real discarded-handle target: a type-5 block with the same 32-byte
    # header shape as the allocator's permanent DiscardEntry allocation.
    discard = header(4, 5, size=32, name=b"DiscardEntry")
    writes += [(DISCARD_HEADER_SEG*16, discard),
               (behavior.symbol_address("fd_50F6_3948"), far(0, DISCARD_DATA_SEG)),
               (behavior.symbol_address("fd_50F6_3950"), w(end))]
    writes += list(extra)
    observe = [behavior.Range("heap",HEAP_SEG*16,(end-HEAP_SEG)*16),
               behavior.Range("handle_table",HANDLE_SEG*16+0xf00,0x100),
               behavior.Range("allocator_globals",dga(0x2f2a),0x28),
               behavior.Range("free_list_head",dga(0x91ac),4),
               behavior.Range("heap_bounds",dga(0x91a4),12),
               behavior.Range("ems_limit",dga(0x8c70),2),
               behavior.Range("discard_entry_pointer",behavior.symbol_address("fd_50F6_3948"),4),
               behavior.Range("discard_entry_header",DISCARD_HEADER_SEG*16,32)]
    return behavior.Case(label=label,args=list(args),writes=writes,observe=observe,return_kind=result,
        registers={"ds":DG,"ss":DG},
        metadata={"suite":SUITE,"contract":contract,"heap_start":HEAP_SEG,"heap_end":end,
                  "blocks":[{"seg":s,"paras":p,"type":k,**o} for s,p,k,o in starts]})

def directed():
    h=[0xffc,HANDLE_SEG]
    resize=[
      heap_case("09cc/shrink-small",[(48,1,{"size":700}),(48,0x80)],args=h+[44,3],handles=[0],contract="shrink below split threshold"),
      heap_case("09cc/shrink-split",[(96,1,{"size":1400}),(64,0x80)],args=h+[40,3],handles=[0],contract="shrink and add a free tail"),
      heap_case("09cc/grow-adjacent-free",[(20,1,{"size":288}),(36,0x80),(32,0)],args=h+[48,0],handles=[0],contract="grow into adjacent free block"),
      heap_case("09cc/grow-locked-neighbor",[(20,1,{"size":288}),(36,3,{"lock":1}),(32,0x80)],args=h+[48,0],handles=[0],contract="reject growth across locked block"),
      heap_case("09cc/grow-too-large",[(20,1,{"size":288}),(8,0x80),(32,0)],args=h+[40,1],handles=[0],contract="reject insufficient adjacent space"),
    ]
    move=[
      heap_case("0adc/move-soft",[(24,0x80),(20,3,{"size":275}),(22,0x80),(16,0)],args=[0,HEAP_SEG],result="void",handles=[0],contract="move eligible soft block into preceding hole and repair handle"),
      heap_case("0adc/move-firm",[(16,0x80),(24,1,{"size":350,"age":9}),(18,0),(20,0x80),(16,0)],args=[0,HEAP_SEG],result="void",handles=[0],contract="move firm block while retaining other free-list nodes"),
    ]
    compact=[
      heap_case("0cf4/immediate-soft",[(22,0x80),(18,3,{"size":250}),(20,0x80),(16,0)],args=[0],handles=[0],contract="move immediate unlocked soft block into an adjacent hole"),
      heap_case("0cf4/later-firm",[(34,0x80),(14,1,{"lock":1}),(20,1,{"size":300}),(18,0x80)],args=[0],handles=[0],contract="skip locked block, move later fitting firm block"),
      heap_case("0cf4/no-eligible",[(20,0x80),(14,1,{"lock":1}),(18,3,{"attr":0x10}),(20,0x80)],args=[0],handles=[0],contract="leave locked or pinned blocks in place"),
      heap_case("0cf4/discarded-barrier",[(26,0x80),(16,5,{"attr":0x10}),(20,0x80)],args=[0],contract="discarded blocks are not compacted as firm or soft allocations"),
      heap_case("0cf4/ems-boundary",[(20,0x80),(18,3,{"size":260}),(20,0x80)],args=[1],handles=[0],extra=[(dga(0x3950),w(HEAP_SEG+2))],contract="respect EMS-only upper boundary"),
    ]
    alloc=[
      heap_case("0fbc/split",[(18,1,{"size":250,"lock":1}),(24,0x80),(72,0x80)],args=[24,3],result="farptr",handles=[0],contract="select last fit and split prefix for soft allocation"),
      heap_case("0fbc/whole",[(28,0x80),(40,1,{"lock":1}),(24,0)],args=[24,1],result="farptr",contract="consume near-fit block below split threshold"),
      heap_case("0fbc/later-fit",[(18,0x80),(30,0),(42,0x80),(20,1,{"lock":1})],args=[36,0],result="farptr",contract="select a later adequate free block"),
      heap_case("0fbc/reclaim-oldest-soft",[(10,0x80),(18,3,{"size":200,"age":1,"attr":0x10}),(10,0x80),(20,0)],args=[25,1],result="farptr",handles=[0],extra=[(dga(0x3948),far(0,0x7100))],contract="reclaim an unlocked soft handle when total free plus soft space can satisfy allocation"),
    ]
    return {"f_171C_09CC":resize,"f_171C_0ADC":move,"f_171C_0CF4":compact,"f_171C_0FBC":alloc}

def randomized(count=300,seed=0x171c):
    rng=random.Random(seed); out={k:[] for k in directed()}
    for i in range(count):
        kind=rng.choice(tuple(out))
        if kind=="f_171C_09CC":
            old=rng.randrange(18,72); nb=rng.randrange(8,40)
            request=max(4,rng.choice((old-2,old//2,old+rng.randrange(1,nb+1),old+nb+8)))
            rows=[(old,rng.choice((0,1,3)),{"size":(old-2)*16}),(nb,rng.choice((0x80,0,1,3)),{"lock":rng.choice((0,0,1))}),(16,0x80)]
            c=heap_case(f"random/{seed:08x}/{i}/resize",rows,args=[0xffc,HANDLE_SEG,request,rng.choice((0,1,3))],handles=[0],contract="resize branches")
        elif kind=="f_171C_0ADC":
            b,z=rng.randrange(6,32),rng.randrange(6,32); a=rng.randrange(b,40)
            rows=[(a,0x80),(b,rng.choice((1,3)),{"size":(b-2)*16,"attr":rng.choice((0,0,0x10)),"lock":rng.choice((0,0,1))}),(z,0x80)]
            c=heap_case(f"random/{seed:08x}/{i}/move",rows,args=[0,HEAP_SEG],result="void",handles=[0],contract="move state/preconditions")
        elif kind=="f_171C_0CF4":
            # Keep the first free hole large enough for the sole eligible later
            # firm/soft block; the locked separator exercises skip semantics.
            movable=rng.randrange(6,24); hole=rng.randrange(movable,36)
            rows=[(hole,0x80),(rng.randrange(6,18),1,{"lock":1}),
                  (movable,rng.choice((1,3)),{"size":100}),
                  (rng.randrange(6,24),0x80)]
            c=heap_case(f"random/{seed:08x}/{i}/compact",rows,args=[rng.choice((0,1))],handles=[0],extra=[(dga(0x3950),w(HEAP_SEG+rng.randrange(1,10)))],contract="compaction/reclaim")
        else:
            available=rng.randrange(24,64)
            rows=[(available,0x80),(rng.randrange(6,30),rng.choice((0,5)),{}),
                  (rng.randrange(6,30),1,{"lock":1}),(rng.randrange(6,30),0x80)]
            c=heap_case(f"random/{seed:08x}/{i}/alloc",rows,args=[rng.randrange(6,available+1),rng.choice((0,1,3))],result="farptr",handles=[0],contract="allocation fit/split with locked/pinned neighbors")
        out[kind].append(c)
    return out

def run(target,cases,outdir):
    pair=behavior.PreparedPair(target,out=outdir/target); failures=[]; errors=[]; started=time.time()
    for i,case in enumerate(cases):
        try: cmp=pair.compare(case)
        except behavior.ExecutionError as e:
            errors.append({"index":i,"label":case.label,"error":str(e),"fixture":case.metadata}); continue
        if not cmp.equal:
            failures.append({"index":i,"label":case.label,"diff":cmp.diff,"original":cmp.original,"candidate":cmp.candidate,"fixture":case.metadata})
            if len(failures)>=20: break
    report={"schema":"behavior-suite-run-v1","suite":SUITE,"function":target,
      "suite_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      "address":pair.identity["address"],"source":pair.identity["source"],"source_sha256":pair.identity["source_sha256"],
      "compiled_source_sha256":pair.identity["compiled_source_sha256"],"object_sha256":pair.identity["object_sha256"],
      "oracle_sha256":pair.identity["oracle_sha256"],"harness_sha256":pair.identity["harness_sha256"],
      "profile":pair.identity["profile"],"flags":pair.identity["flags"],
      "candidate_strict":pair.strict.get("claims",{}).get(target,{}),
      "whole_module_peers_and_data":"PreparedPair gates passed","cases_generated":len(cases),
      "cases_run":len(cases)-len(errors),"mismatches":len(failures),"execution_errors":errors,
      "failures":failures,"elapsed_seconds":round(time.time()-started,3),
      "behavioral_status":"UNRESOLVED; pending supervisor review"}
    (outdir/f"{target}.json").write_text(json.dumps(report,indent=2)+"\n")
    return report

def function_body(text,name):
    import re
    match_sig=re.search(r"^[^\n;]*\b"+re.escape(name)+r"\s*\([^;]*?\)\s*\{",text,re.M)
    if not match_sig: raise ValueError(f"cannot locate definition of {name}")
    start=match_sig.end()-1; depth=0
    for pos in range(start,len(text)):
        if text[pos]=="{": depth+=1
        elif text[pos]=="}":
            depth-=1
            if depth==0: return start,pos+1,text[start:pos+1]
    raise ValueError(f"unterminated definition of {name}")

def negative_controls(outdir,cases):
    """Compile one source mutant per function and require oracle sensitivity."""
    specs={
      "f_171C_09CC":("return 1;","return 0;",0),
      "f_171C_0ADC":("(unsigned long)b + 0x20000L","(unsigned long)b + 0x30000L",0),
      "f_171C_0CF4":("return *(int near *)&moved;","return 0;",1),
      "f_171C_0FBC":("return n;","return 0L;",0),
    }
    report=[]; mutant_root=outdir/"negative"; mutant_root.mkdir(parents=True,exist_ok=True)
    for target,(old,new,case_index) in specs.items():
        seed=ROOT/"work/takeover/hardtail/seeds"/Path(next(
            r["best_source"] for r in json.loads((ROOT/"work/takeover/hardtail/catalog.json").read_text())["records"]
            if r["function"]==target)).name
        original=seed.read_text(encoding="latin1"); start,end,body=function_body(original,target)
        if body.count(old)<1: raise RuntimeError(f"negative control anchor missing for {target}: {old!r}")
        mutant_text=original[:start]+body.replace(old,new,1)+original[end:]
        mutant_path=mutant_root/f"{target}.c"; mutant_path.write_text(mutant_text,encoding="latin1")
        pair=behavior.PreparedPair(target,source=mutant_path,out=mutant_root/target)
        case=cases[target][case_index]
        comparison=pair.compare(case)
        row={"function":target,"source":str(mutant_path.relative_to(ROOT)),
             "source_sha256":pair.identity["source_sha256"],"object_sha256":pair.identity["object_sha256"],
             "candidate_strict":pair.strict.get("claims",{}).get(target,{}),
             "case":case.label,"detected":not comparison.equal,"diff":comparison.diff,
             "oracle":comparison.original,"mutant":comparison.candidate}
        if comparison.equal: raise AssertionError(f"behavior oracle failed to detect negative control: {target}")
        report.append(row)
    (outdir/"negative-controls.json").write_text(json.dumps(report,indent=2)+"\n")
    return report


TARGETS = ("f_171C_09CC", "f_171C_0ADC", "f_171C_0CF4", "f_171C_0FBC")
TRACKED_FUNCTIONS = TARGETS + ("f_171C_1B84", "f_171C_1BBA", "f_171C_0BE2", "f_171C_13E4")
SEQUENCE_EFFECTS = ["operation return", "allocator and master-table state",
    "heap headers and payload bytes", "handle identity and payload preservation",
    "free-list topology", "lock/unlock/free/reclaim effects", "all nonstack writes",
    "ordered actual helper calls", "caller ABI"]
MODULE_SEED = ROOT / "work/takeover/hardtail/seeds/root_171C_7decbec511e9.c"


def source_copy(outdir):
    """Retain the exact whole-module C input beside its immutable run reports."""
    path = outdir / "source" / "ralloc-module.c"
    path.parent.mkdir(parents=True, exist_ok=True)
    text = MODULE_SEED.read_text(encoding="latin1")
    alias = "return *(int near *)&moved;"
    if text.count(alias) != 1:
        raise RuntimeError("expected one private moved-result alias in the 0CF4 draft")
    # Keep the function's C type natural for a semantic oracle proof. The
    # historical low-word alias was only a code-generation hypothesis.
    raw = text.replace(alias,"return (int)moved;",1).encode("latin1")
    if path.exists() and path.read_bytes() != raw:
        raise RuntimeError(f"refusing to replace retained source {path}")
    if not path.exists(): path.write_bytes(raw)
    return path


def make_sequence(sequence_id, *, hole=86, soft=50, gap=16, firm=18, tail=32,
                  soft_lock=0, firm_lock=0, pinned=False, seed=None,
                  resize_delta=32, allocation_mode="partial", allocation_type=1,
                  firm_type=1, content_seed=0, soft_age=7, firm_age=11):
    """A valid paragraph heap and a sequence that carries its live state forward.

    The first hole is at least as large as its following movable soft block.
    Free-list links are segment-sorted, each live type-1/type-3 block has one
    descending master-table slot, and all size/counter/boundary globals agree.
    """
    if hole < soft or soft < 40 or soft - 32 < 6 or min(gap,firm,tail) < 6:
        raise ValueError("invalid compaction/resize dimensions")
    resize_to=soft-resize_delta if resize_delta>=32 else soft
    if resize_to < 4: raise ValueError("resize target below safe block size")
    total_paras=hole+soft+gap+firm+tail
    alloc_requests={"exact-fit":total_paras,"threshold-plus-four":total_paras-4,
                    "split-plus-five":total_paras-5,
                    "partial":min(10,total_paras-6)}
    if allocation_mode not in alloc_requests: raise ValueError("unknown allocation mode")
    allocation_paras=alloc_requests[allocation_mode]
    rows = [(hole,0x80),
            (soft,3,{"size":(soft-2)*16,"age":soft_age,"lock":soft_lock,
                     "attr":0x10 if pinned else 0,"name":b"soft-live"}),
            (gap,0x80),
            (firm,firm_type,{"size":(firm-2)*16,"age":firm_age,"lock":firm_lock,
                     "name":b"firm-live"}),
            (tail,0x80)]
    # Master slots descend from s_2F46, as the original _Handle helpers do.
    handles = [0,1]
    direct_move = not (pinned or soft_lock)
    first_target = "f_171C_0ADC" if direct_move else "f_171C_0CF4"
    initial = heap_case(f"{sequence_id}/00-initialize-and-prepare-move", rows,
        args=([0,HEAP_SEG] if direct_move else [0]), handles=handles,
        result=("void" if direct_move else "s16"),
        contract=("actual free-list arena; direct 0ADC relocation of unlocked next soft block"
                  if direct_move else "actual free-list arena; compact while respecting lock/pin eligibility"),
        content_seed=content_seed)
    operations = [
        (first_target, initial, "move/compact the valid live arena"),
        ("f_171C_0CF4", None, "compact later fitting blocks; preserve handles and contents"),
        ("f_171C_1B84", None, "lock the live soft handle through original manager helper"),
        ("f_171C_1BBA", None, "unlock the same live soft handle through original manager helper"),
        ("f_171C_09CC", None, "resize the relocated soft handle and split a real free tail"),
        ("f_171C_0BE2", None, "reclaim the oldest unlocked soft handle into DiscardEntry"),
        ("f_171C_13E4", None, "free the relocated firm handle through original manager helper"),
        ("f_171C_0FBC", None, "allocate from the updated free list after reclaim/free"),
        ("f_171C_0CF4", None, "compact the resulting live arena a second time"),
    ]
    plan = [op[0] for op in operations]
    plan_meta = {"sequence_id":sequence_id,"ordered_operation_plan":plan,
                 "fixture_seed":seed,"hole_paras":hole,"soft_paras":soft,
                 "gap_paras":gap,"firm_paras":firm,"tail_paras":tail,
                 "resize_delta_paras":resize_delta,"resize_to_paras":resize_to,
                 "allocation_mode":allocation_mode,"allocation_paras":allocation_paras,
                 "allocation_type":allocation_type,"firm_type":firm_type,
                 "content_seed":content_seed,"soft_age":soft_age,"firm_age":firm_age,
                 "soft_lock_initial":soft_lock,"firm_lock_initial":firm_lock,
                 "soft_pinned_initial":pinned,
                 "initial_master_slots":{"soft":MASTER_FIRST,"firm":MASTER_FIRST-4},
                 "heap_segment":HEAP_SEG,"master_table_end":MASTER_ONE_PAST,
                 "fixture_validity":"paragraph aligned; ordered free chain; matching counters; live handles point to payload; discard block initialized"}
    steps=[]
    for index,(target,case,contract) in enumerate(operations):
        if case is None:
            if target == "f_171C_0CF4": args=[0]; result="s16"
            elif target == "f_171C_1B84": args=[MASTER_FIRST,HANDLE_SEG]; result="farptr"
            elif target == "f_171C_1BBA": args=[MASTER_FIRST,HANDLE_SEG]; result="farptr"
            elif target == "f_171C_09CC": args=[MASTER_FIRST,HANDLE_SEG,resize_to,3]; result="s16"
            elif target == "f_171C_0BE2": args=[0]; result="s16"
            elif target == "f_171C_13E4": args=[MASTER_FIRST-4,HANDLE_SEG]; result="void"
            elif target == "f_171C_0FBC": args=[allocation_paras,allocation_type]; result="farptr"
            else: raise ValueError(target)
            case=behavior.Case(label=f"{sequence_id}/{index:02d}-{target}",args=args,
                observe=initial.observe,return_kind=result,registers={"ds":DG,"ss":DG},
                metadata={"suite":SUITE,"contract":contract,"sequence":plan_meta,
                          "operation_index":index,"helpers":"all same-module non-target helpers execute original DOS code"})
        else:
            case.label=f"{sequence_id}/{index:02d}-{target}"
            case.metadata={"suite":SUITE,"contract":contract,"sequence":plan_meta,
                           "operation_index":index,"helpers":"all same-module non-target helpers execute original DOS code"}
        steps.append((target,case))
    return steps


def operation_plan(sequence_id, *, seed=None, random_case=False):
    if random_case:
        rng=random.Random(seed)
        soft=rng.randrange(40,66)
        hole=rng.randrange(soft,90)
        soft_age=rng.randrange(1,60)
        firm_age=min(99,soft_age+rng.randrange(1,30))
        resize_delta=rng.choice((31,32,33,40) if soft>=44 else (31,32,33))
        allocation_mode=rng.choice(("exact-fit","threshold-plus-four","split-plus-five","partial"))
        return make_sequence(sequence_id,hole=hole,soft=soft,gap=rng.randrange(8,21),
            firm=rng.randrange(8,22),tail=rng.randrange(20,41),
            soft_lock=0,firm_lock=0,pinned=bool(rng.randrange(2)),seed=seed,
            resize_delta=resize_delta,allocation_mode=allocation_mode,
            allocation_type=rng.choice((0,1,3)),firm_type=rng.choice((0,1)),
            content_seed=rng.randrange(256),soft_age=soft_age,firm_age=firm_age)
    return make_sequence(sequence_id,seed=seed)


class _StepIdentity:
    """Per-invoked-function identity view for CaseLedger over one live pair."""
    def __init__(self,pair,target):
        self.original_machine,self.candidate_machine=pair.original_machine,pair.candidate_machine
        fn=behavior.functions.get(target)
        self.identity={**pair.identity,"function":target,
                       "address":{k:fn[k] for k in ("unit","seg","off","size")}}


def function_body(text,name):
    import re
    sig=re.search(r"^[^\n;]*\b"+re.escape(name)+r"\s*\([^;]*?\)\s*\{",text,re.M)
    if not sig: raise ValueError(f"cannot locate definition of {name}")
    start=sig.end()-1; depth=0
    for pos in range(start,len(text)):
        if text[pos]=="{": depth+=1
        elif text[pos]=="}":
            depth-=1
            if depth==0:return start,pos+1,text[start:pos+1]
    raise ValueError(f"unterminated definition of {name}")


def _mutant(source_text,target):
    specs={
      "f_171C_09CC":("if (b->paras < paras + 0x20)","if (b->paras <= paras + 0x20)"),
      "f_171C_0ADC":("(unsigned long)b + 0x20000L","(unsigned long)b + 0x30000L"),
      "f_171C_0CF4":("return (int)moved;","return 0;"),
      "f_171C_0FBC":("return n;","return 0L;")}
    old,new=specs[target]
    start,end,body=function_body(source_text,target)
    if body.count(old)!=1: raise RuntimeError(f"mutant anchor is not unique in {target}: {old}")
    return source_text[:start]+body.replace(old,new,1)+source_text[end:]


def _pointer_arithmetic_mutant(source_text):
    target="f_171C_0CF4"
    start,end,body=function_body(source_text,target)
    old_nb="(long)nb + 0x20000L"
    old_n="(long)n + 0x20000L"
    if body.count(old_nb)!=2 or body.count(old_n)!=1:
        raise RuntimeError("unexpected far-pointer expression count in 0CF4")
    body=body.replace(old_nb,"(char far *)nb + 0x20000L")
    body=body.replace(old_n,"(char far *)n + 0x20000L")
    return source_text[:start]+body+source_text[end:]


def _run_negative_controls(outdir,source_path,steps):
    negroot=outdir/"negative"; negroot.mkdir(parents=True,exist_ok=True)
    source_text=source_path.read_text(encoding="latin1")
    report=[]
    for target in TARGETS:
        mutant=negroot/f"{target}.c"
        mutant.write_text(_mutant(source_text,target),encoding="latin1")
        pair=behavior.PreparedPair(TARGETS[0],source=mutant,out=negroot/target,
                                  sequence_targets=TARGETS)
        control_steps=(make_sequence("negative/cf4-moved-return",hole=70,soft=48,
                         gap=18,firm=20,tail=32,soft_lock=1,seed=0x171C)
                       if target=="f_171C_0CF4" else steps)
        errors=[]; detected=None; compared=0
        for (step_target,case),cmp in zip(control_steps,pair.compare_sequence(control_steps)):
            compared+=1
            if not cmp.equal:
                detected={"step":case.label,"operation":step_target,"diff":cmp.diff}
                break
        row={"target":target,"source":pair.identity["source"],
             "source_sha256":pair.identity["source_sha256"],
             "object_sha256":pair.identity["object_sha256"],
             "oracle_sha256":pair.identity["oracle_sha256"],
             "manifest_sha256":pair.identity["manifest_sha256"],
             "mutant_detected":detected is not None,"first_difference":detected,
             "steps_executed":compared,"errors":errors}
        if detected is None: raise AssertionError(f"stateful negative control not detected: {target}")
        report.append(row)
    # A minimized valid arena proves that byte-wise far-pointer arithmetic in
    # 0CF4 wraps differently from the original's packed-long paragraph update.
    pointer_steps=make_sequence("negative/pointer-arithmetic",hole=70,soft=48,
        gap=18,firm=20,tail=32,soft_lock=1,seed=0x171C)
    pointer_case=pointer_steps[0][1]
    pointer_case.metadata["contract"]="single-call locked-soft barrier; later firm block is moved into first free hole"
    baseline=behavior.PreparedPair(TARGETS[0],source=source_path,
        out=negroot/"pointer-arithmetic-baseline",sequence_targets=TARGETS)
    baseline_cmp=next(baseline.compare_sequence([("f_171C_0CF4",pointer_case)]))
    if not baseline_cmp.equal:
        raise RuntimeError(f"pointer arithmetic control baseline is not semantically matched: {baseline_cmp.diff}")
    mutant=negroot/"f_171C_0CF4-pointer-arithmetic.c"
    mutant.write_text(_pointer_arithmetic_mutant(source_text),encoding="latin1")
    pair=behavior.PreparedPair(TARGETS[0],source=mutant,out=negroot/"pointer-arithmetic-mutant",
                              sequence_targets=TARGETS)
    cmp=next(pair.compare_sequence([("f_171C_0CF4",pointer_case)]))
    if cmp.equal: raise AssertionError("pointer arithmetic negative control did not reproduce the semantic difference")
    report.append({"target":"f_171C_0CF4","id":"far-pointer-arithmetic-wrap",
        "source":pair.identity["source"],"source_sha256":pair.identity["source_sha256"],
        "object_sha256":pair.identity["object_sha256"],"oracle_sha256":pair.identity["oracle_sha256"],
        "manifest_sha256":pair.identity["manifest_sha256"],"baseline_matched":True,
        "fixture":pointer_case.metadata,"steps_executed":1,"mutant_detected":True,
        "first_difference":{"step":pointer_case.label,"operation":"f_171C_0CF4","diff":cmp.diff}})
    (outdir/"negative-controls.json").write_text(json.dumps(report,indent=2)+"\n")
    return report


def run_stateful(random_count,seed,outdir,*,negative_controls=True):
    outdir.mkdir(parents=True,exist_ok=True)
    source=source_copy(outdir)
    pair=behavior.PreparedPair(TARGETS[0],source=source,out=outdir/"candidate",
                              sequence_targets=TARGETS)
    ledgers={target:CaseLedger(outdir/f"{target}-case-ledger.jsonl.gz",
                _StepIdentity(pair,target),SEQUENCE_EFFECTS) for target in TRACKED_FUNCTIONS}
    per_target={target:{"calls":0,"equal":0,"mismatches":0,"errors":0,
                        "original_nonstack_dgroup_write_observations":0,
                        "candidate_nonstack_dgroup_write_observations":0}
                for target in TRACKED_FUNCTIONS}
    dgroup_samples={target:{"original":set(),"candidate":set()} for target in TRACKED_FUNCTIONS}
    failures=[]; errors=[]; completed_sequences=0; started=time.monotonic()
    directed=[operation_plan("directed/basic",seed=seed),
              make_sequence("directed/large-arena",hole=90,soft=58,gap=18,firm=20,tail=34,seed=seed+1),
              make_sequence("directed/locked-soft",hole=70,soft=48,gap=18,firm=20,tail=32,
                            soft_lock=1,seed=seed+2),
              # A locked and a pinned soft block before a later movable firm
              # block exercise the second compaction scan and skip conditions.
              make_sequence("directed/lock-and-pin",hole=72,soft=48,gap=18,firm=20,tail=32,
                            soft_lock=0,firm_lock=0,pinned=True,seed=seed+3),
              make_sequence("directed/resize-boundary-noop",hole=86,soft=50,gap=16,firm=18,tail=32,
                            resize_delta=31,seed=seed+4),
              make_sequence("directed/resize-boundary-split",hole=86,soft=50,gap=16,firm=18,tail=32,
                            resize_delta=33,seed=seed+5),
              make_sequence("directed/alloc-exact-fit",hole=86,soft=50,gap=16,firm=18,tail=32,
                            allocation_mode="exact-fit",seed=seed+6),
              make_sequence("directed/alloc-plus-four",hole=86,soft=50,gap=16,firm=18,tail=32,
                            allocation_mode="threshold-plus-four",seed=seed+7),
              make_sequence("directed/alloc-plus-five",hole=86,soft=50,gap=16,firm=18,tail=32,
                            allocation_mode="split-plus-five",seed=seed+8)]
    generated=list(directed)
    for i in range(random_count):
        generated.append(operation_plan(f"random/{seed:08x}/{i}",seed=seed+i+1,random_case=True))
    random_meta=[steps[0][1].metadata["sequence"] for steps in generated[len(directed):]]
    def histogram(key):
        from collections import Counter
        return dict(sorted(Counter(str(meta[key]) for meta in random_meta).items()))
    random_coverage={"sequence_count":len(random_meta),
        "distinct_payload_patterns":len({meta["content_seed"] for meta in random_meta}),
        "resize_delta_histogram":histogram("resize_delta_paras"),
        "allocation_mode_histogram":histogram("allocation_mode"),
        "firm_type_histogram":histogram("firm_type"),
        "pinned_soft_sequences":sum(bool(meta["soft_pinned_initial"]) for meta in random_meta),
        "three_separated_free_nodes_per_initial_heap":len(random_meta),
        "paragraph_ranges":{key:[min(meta[key] for meta in random_meta),max(meta[key] for meta in random_meta)]
            for key in ("hole_paras","soft_paras","gap_paras","firm_paras","tail_paras")}
        } if random_meta else {"sequence_count":0}
    for seq_index,steps in enumerate(generated):
        lane="directed" if seq_index<len(directed) else "randomized"
        try:
            for step_index,((target,case),cmp) in enumerate(zip(steps,pair.compare_sequence(steps))):
                per_target[target]["calls"]+=1
                for side,machine,observation in (("original",pair.original_machine,cmp.original),
                                                  ("candidate",pair.candidate_machine,cmp.candidate)):
                    lower,upper=machine.stack_bounds
                    addresses={at for at in observation["written_addresses"]
                               if DG*16 <= at < (DG+0x1000)*16 and not lower <= at < upper}
                    per_target[target][side+"_nonstack_dgroup_write_observations"]+=len(addresses)
                    dgroup_samples[target][side].update(addresses)
                row=ledgers[target].record(case,cmp,lane=lane)
                if cmp.equal: per_target[target]["equal"]+=1
                else:
                    per_target[target]["mismatches"]+=1
                    failures.append({"sequence":case.metadata.get("sequence",{}).get("sequence_id"),
                                     "step":step_index,"target":target,"label":case.label,
                                     "diff":cmp.diff,"ledger_row":row})
                    break
            else:
                completed_sequences+=1
        except Exception as exc:
            target=steps[min(step_index if "step_index" in locals() else 0,len(steps)-1)][0] if steps else "unknown"
            per_target[target]["errors"]+=1
            errors.append({"sequence_index":seq_index,"sequence_id":steps[0][1].metadata.get("sequence",{}).get("sequence_id") if steps else None,
                           "step":step_index if "step_index" in locals() else None,
                           "error":str(exc)})
            continue
    ledger_pins={target:ledgers[target].finalize() for target in TRACKED_FUNCTIONS}
    negative=_run_negative_controls(outdir,source,directed[0]) if negative_controls else []
    suite_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    summary={"schema":"behavior-suite-run-v1","suite":SUITE,"suite_sha256":suite_hash,
        "source_sha256":pair.identity["source_sha256"],"source":pair.identity["source"],
        "compiled_source_sha256":pair.identity["compiled_source_sha256"],
        "object_sha256":pair.identity["object_sha256"],"oracle_sha256":pair.identity["oracle_sha256"],
        "harness_sha256":pair.identity["harness_sha256"],"manifest_sha256":pair.identity["manifest_sha256"],
        "sequence_targets":list(TARGETS),"identity":pair.identity,
        "seed":seed,"directed_sequences":len(directed),"randomized_sequences_requested":random_count,
        "randomized_sequences_generated":random_count,"sequences_completed":completed_sequences,
        "randomized_fixture_coverage":random_coverage,
        "execution_errors":errors,"errors":len(errors),"mismatches":len(failures),"failures":failures,
        "per_target":per_target,"case_ledgers":ledger_pins,
        "nonstack_dgroup_write_samples":{target:{side:sorted(values)[:32]
            for side,values in dgroup_samples[target].items()} for target in TRACKED_FUNCTIONS},
        "negative_controls":negative,
        "contract":"persistent live original-DOS vs compiler-produced whole-module C; all same-module non-target helper calls execute original DOS code on both sides; first case initializes only; later steps preserve each VM's state",
        "domains":"valid 3-hole paragraph heaps with initialized linked free lists, descending master slots, matching counters, patterned payloads and discard sentinel; direct and noncontiguous relocation; soft lock/pin and firm/hard types; resize deltas 31/32/33/40; exact-fit, best==request+4 and +5 split thresholds; unlock/reclaim/free/allocate/second compact",
        "status":"UNRESOLVED; diagnostic behavioral differential only; supervisor review required",
        "elapsed_seconds":round(time.monotonic()-started,3)}
    for target in TARGETS:
        report={"schema":"behavior-suite-run-v1","suite":SUITE,"function":target,
            "source":pair.identity["source"],"source_sha256":pair.identity["source_sha256"],
            "object_sha256":pair.identity["object_sha256"],"oracle_sha256":pair.identity["oracle_sha256"],
            "manifest_sha256":pair.identity["manifest_sha256"],"harness_sha256":pair.identity["harness_sha256"],
            "suite_sha256":suite_hash,"candidate_strict":pair.strict.get("claims",{}).get(target,{}),
            "case_ledger":ledger_pins[target],"calls":per_target[target]["calls"],
            "matched":per_target[target]["equal"],"mismatches":per_target[target]["mismatches"],
            "errors":per_target[target]["errors"],"negative_control_detected":next((x["mutant_detected"] for x in negative if x["target"]==target),None),
            "behavioral_status":"UNRESOLVED; diagnostic behavioral differential only; supervisor review required"}
        (outdir/f"{target}.json").write_text(json.dumps(report,indent=2)+"\n")
    (outdir/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    return summary

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--random-count",type=int,default=256)
    p.add_argument("--seed",type=lambda s:int(s,0),default=0x171c)
    p.add_argument("--no-negative-controls",action="store_true")
    p.add_argument("--out",type=Path,default=ROOT/"build/workers/behavior_memory/stateful-20261002")
    a=p.parse_args()
    report=run_stateful(a.random_count,a.seed,a.out,negative_controls=not a.no_negative_controls)
    print(json.dumps(report,indent=2))
if __name__=="__main__": main()
