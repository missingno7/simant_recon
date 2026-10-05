"""Differential contracts for four original DOS Ralloc heap helpers.

Runs hash-locked DOS code and a separately compiled whole-module candidate via
tools/behavior.py. Fixtures contain paragraph-aligned headers, free links,
master handles, manager counters, and deterministic user data. No proof category
is assigned by this suite.
"""
from __future__ import annotations
import argparse, hashlib, json, random, struct, sys, time
from pathlib import Path
ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'layout/functions.json').is_file())

import behavior, match
from behavior_ledger import CaseLedger

SUITE = "ralloc_memory_v3_startup_handles"
DG = match.DGROUP_SEG
# Original startup stores an offset-zero s_2F46; four-byte master slots wrap
# below it in the same segment. These 64 slots end one paragraph before the
# heap, matching f_171C_07BE's master reservation plus its extra paragraph.
# The reserved stack remains in DGROUP.
HEAP_SEG, HEAP_PARAS = 0xA100, 0x100
HANDLE_SEG, MASTER_FIRST, MASTER_ONE_PAST = 0x90FF, 0xFFFC, 0
MASTER_CAPACITY, MASTER_START = 64, 0xFF00
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
    place the actual four-byte handle slots themselves. Original startup gives
    this pointer offset zero, and allocation stores raw OFF(h) in Block.handle;
    pointer recovery and movement add that signed word to this offset-zero base.
    A nonzero master_off is useful only for explicit invalid-premise controls.
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

def heap_case(label, rows, *, args=(), handles=(), result="s16", extra=(), contract="", content_seed=0,
              heap_seg=None, heap_paras=None, handle_seg=None,
              discard_header_seg=None, discard_data_seg=None):
    """rows=(paras,type,options), in physical address order."""
    heap_seg = HEAP_SEG if heap_seg is None else heap_seg
    heap_paras = HEAP_PARAS if heap_paras is None else heap_paras
    handle_seg = HANDLE_SEG if handle_seg is None else handle_seg
    discard_header_seg = DISCARD_HEADER_SEG if discard_header_seg is None else discard_header_seg
    discard_data_seg = DISCARD_DATA_SEG if discard_data_seg is None else discard_data_seg
    if discard_data_seg != discard_header_seg + 2:
        raise ValueError("discarded pointer must resolve to the seeded template header")
    starts, seg = [], heap_seg
    for row in rows:
        paras, kind = row[:2]
        opts = dict(row[2]) if len(row) > 2 else {}
        starts.append((seg, paras, kind, opts)); seg += paras
    end = seg
    if not starts or end > heap_seg + heap_paras: raise ValueError("heap fixture out of bounds")
    free = [b for b in starts if b[2] == 0x80]
    occupied = [b for b in starts if b[2] not in (0x80, 2)]
    if MASTER_ONE_PAST != 0 or MASTER_FIRST != 0xFFFC:
        raise ValueError("heap fixture requires the original offset-zero master base")
    if len(handles) != len(occupied):
        raise ValueError("each live heap block requires one master handle")
    if (len(set(handles)) != len(handles) or
            any(not isinstance(i, int) or not 0 <= i < MASTER_CAPACITY - 1 for i in handles)):
        raise ValueError("master handle indices must be unique and below the allocator capacity")
    if any(p < 2 for _, p, _, _ in starts):
        raise ValueError("physical heap blocks must contain their two-paragraph header")
    table_start = handle_seg * 16 + MASTER_START
    table_end = table_start + MASTER_CAPACITY * 4
    if table_start < end * 16 and table_end > heap_seg * 16:
        raise ValueError("master handle table overlaps the physical heap")
    # f_171C_0A5C starts at s_2F46-1. Clear every reserved descending slot.
    writes = [(handle_seg*16+MASTER_START,b"\0"*(MASTER_CAPACITY*4))]
    for i, (hidx, block) in enumerate(zip(handles, occupied)):
        slot = MASTER_FIRST - 4 * hidx
        block[3]["handle"] = slot & 0xffff
        writes.append((handle_seg * 16 + slot, far(0, block[0] + 2)))
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
    writes += memory_globals_writes(heap_start=heap_seg,heap_end=end,
        free_head=free[0][0] if free else 0,master_off=MASTER_ONE_PAST,master_seg=handle_seg,
        allocated_handles=max(handles,default=-1)+1,live_handles=len(handles),free_paras=total_free,
        used_paras=total_used,type_paras={0:counters[0x2f36],1:counters[0x2f3a],3:counters[0x2f38]})
    # Startup copies s_2F4E {0,0L,0,5} into its 32-byte DiscardEntry payload.
    # fd_3948 points at that copied template; reclaim adds two paragraphs so
    # HDR(discarded handle) subtracts them again and reads this type-5 header.
    # The enclosing permanent allocation remains a bounded fixture proxy.
    discard = header(0, 5, size=0, name=b"")
    writes += [(discard_header_seg*16, discard),
               (behavior.symbol_address("fd_50F6_3948"), far(0, discard_header_seg)),
               (behavior.symbol_address("fd_50F6_3950"), w(end))]
    writes += list(extra)
    observe = [behavior.Range("heap",heap_seg*16,(end-heap_seg)*16),
               behavior.Range("handle_table",handle_seg*16+MASTER_START,MASTER_CAPACITY*4),
               behavior.Range("allocator_globals",dga(0x2f2a),0x28),
               behavior.Range("free_list_head",dga(0x91ac),4),
               behavior.Range("heap_bounds",dga(0x91a4),12),
               behavior.Range("ems_limit",dga(0x8c70),2),
               behavior.Range("discard_entry_pointer",behavior.symbol_address("fd_50F6_3948"),4),
               behavior.Range("discard_entry_header",discard_header_seg*16,32)]
    return behavior.Case(label=label,args=list(args),writes=writes,observe=observe,return_kind=result,
        registers={"ds":DG,"ss":DG},
        metadata={"suite":SUITE,"contract":contract,"heap_start":heap_seg,"heap_end":end,
                  "blocks":[{"seg":s,"paras":p,"type":k,**o} for s,p,k,o in starts]})







TARGETS = ("f_171C_09CC", "f_171C_0ADC", "f_171C_0CF4", "f_171C_0FBC")
TRACKED_FUNCTIONS = TARGETS + ("f_171C_1B84", "f_171C_1BBA", "f_171C_0BE2", "f_171C_13E4")
SEQUENCE_EFFECTS = ["operation return", "allocator and master-table state",
    "heap headers and payload bytes", "handle identity and payload preservation",
    "free-list topology", "lock/unlock/free/reclaim effects", "all nonstack writes",
    "ordered actual helper calls", "caller ABI"]




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
    ]
    # 0FBC returns a raw Block*, before its f_171C_1D40 caller copies a live
    # header/payload and installs the handle. That intermediate helper state
    # cannot be fed to another compaction as a completed live allocation.
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
                 "fixture_validity":"paragraph aligned; ordered free chain; matching counters; offset-zero master base; live Block.handle stores raw OFF(h); discard block initialized",
                 "terminal_boundary":"0FBC raw Block* return; caller handle installation has not executed"}
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


def completed_allocation_sequence(sequence_id="directed/completed-allocation"):
    """Real public allocations establish raw handle offsets before a live move.

    Only the first call seeds a free arena. Original 125C/13E4/2136 helpers execute
    in both machines; the reviewed 0CF4 candidate compacts their actual state.
    """
    initial = heap_case(sequence_id + "/00-allocate-first", [(HEAP_PARAS,0x80)],
        args=[160,0,1,0,0xB200], result="farptr", extra=[(0xB2000,b"public-live\0")],
        contract="free arena for two completed original public allocations")
    plan = [
        ("f_171C_125C", initial, "farptr"),
        ("f_171C_125C", [32,0,1,0,0xB200], "farptr"),
        ("f_171C_13E4", [MASTER_FIRST,HANDLE_SEG], "void"),
        ("f_171C_0CF4", [0], "s16"),
        ("f_171C_2136", [0,HEAP_SEG+2], "farptr"),
        ("f_171C_13E4", [MASTER_FIRST-4,HANDLE_SEG], "void"),
        ("f_171C_0CF4", [0], "s16"),
    ]
    steps = []
    for index,(target,args,result) in enumerate(plan):
        case = args if index == 0 else behavior.Case(
            label=f"{sequence_id}/{index:02d}-{target}", args=args,
            observe=initial.observe, return_kind=result, registers={"ds":DG,"ss":DG})
        case.metadata = {"suite":SUITE,"operation_index":index,
            "contract":"completed public allocation/free/compact/pointer-recovery history",
            "helpers":"original 125C/13E4/2136 execute; 0CF4 is the active reviewed candidate",
            "expected_second_handle":(HANDLE_SEG<<16)|(MASTER_FIRST-4)}
        steps.append((target,case))
    return steps


class _StepIdentity:
    """Per-invoked-function identity view for CaseLedger over one live pair."""
    def __init__(self,pair,target):
        self.original_machine,self.candidate_machine=pair.original_machine,pair.candidate_machine
        fn=behavior.functions.get(target)
        self.identity={**pair.identity,"function":target,
                       "address":{k:fn[k] for k in ("unit","seg","off","size")}}











