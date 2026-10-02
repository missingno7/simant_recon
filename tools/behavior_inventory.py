#!/usr/bin/env python3
"""Build a source-grounded behavioral-debt inventory from the retained hard-tail report.

This is descriptive evidence only. It cannot change historical ownership or mark a
function EXACT/BEHAVIOR_EXACT. The report and source hashes are pinned in its output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / "work/takeover/hardtail/all-open.json"
DEFAULT_CATALOG = ROOT / "work/takeover/hardtail/catalog.json"
DEFAULT_OUT = ROOT / "work/takeover/behavioral-oracle/inventory.json"

# Category choices come from the reviewed whole-module source and callers, not from
# diagnostic class names. Uncertain mappings stay UNKNOWN rather than being guessed.
TAXONOMY = {
    "f_0250_1018": ("rendering", "Per-cell ant/pheromone view selection and draw dispatch."),
    "f_0250_129E": ("rendering", "Cache-check and redraw one ant/map cell."),
    "DrawBalloons": ("rendering", "Draw balloon overlays; exact drawing commands are not captured."),
    "SpiderScan": ("core simulation", "Scan candidate cells around the spider, fire at a found ant, optionally kill it."),
    "LessonDone": ("tutorial/support", "Tutorial completion flow; original switch-table and shared-tail semantics need differential coverage."),
    "f_171C_09CC": ("memory infrastructure", "Resize/rehome a memory-manager block by handle and paragraph count."),
    "f_171C_0ADC": ("memory infrastructure", "Move/compact a DOS heap block and repair links/handle address."),
    "f_171C_0FBC": ("memory infrastructure", "Find/create a free block for a requested paragraph size and type."),
    "f_171C_0CF4": ("memory infrastructure", "Compact or reclaim allocator blocks; current reviewed candidate exchanges six BP homes."),
    "FindIndex": ("database/resource infrastructure", "Find a key in the module's sorted index table; return/cursor contract needs direct confirmation."),
    "f_1C62_0415": ("UI", "Interactive choice dialog with labels, selection, event handling and cleanup."),
    "f_1E57_038E": ("clipping", "Rebuild clipping rectangles for the current window stack."),
    "f_20E8_0903": ("windowing", "Set an object's per-edge origins/relationships and recalculate its window."),
    "win_UnlockWin": ("windowing", "Unlock a window and run its release/update path."),
    "f_23E6_0000": ("UI", "Resolve a visible list line to a string pointer while locking/unlocking backing text."),
    "f_2505_0453": ("windowing", "Return a window object's indexed field, or the invalid sentinel."),
    "win_DrawBitMap": ("rendering", "Draw a bitmap through window/resource helpers."),
    "f_2815_0165": ("audio", "Program an AdLib voice's level and pitch registers for an instrument/note."),
    "f_284A_0138": ("audio", "Decode a Tandy/audio byte pair into a packed result; channel/data contract needs differential tests."),
    "f_29D6_000A": ("audio", "Emit a Tandy/audio note command; target register/port sequence is not yet compared."),
    "o10_35F5_0384": ("UI", "Process a pull-down menu selection/key event."),
    "DrawMapCursor": ("rendering", "Compute/draw map cursor from paired global origins and scale values."),
    "InvertPatch": ("rendering", "Draw/invert a patch at a computed screen origin."),
    "o15_384C_0239": ("UI", "Text/font helper; exact observable return and font-buffer effects need a named contract."),
    "win_PrintStyleTextInRect": ("rendering", "Lay out and draw styled text within a rectangle."),
    "DisplayCard": ("UI", "Populate/display an information card; resource and window effects need comparison."),
    "drawHistGraph": ("rendering", "Render history graph from accumulated values."),
    "o25_3BA4_1035": ("gameplay support", "Move an ant into a nest and update map/ant state."),
    "o25_3BA4_1686": ("core simulation", "Choose a legal neighboring move with direction/rotation hysteresis and update caller state."),
}

RESIDUE = {
    "SpiderScan": ("apparently local/dead initialization residue", "Target clears AX and stores zero at BP-2 and BP-8; candidate stores only the BP-8 zero. This may be an overwritten local, but no oracle test has established observability."),
    "o25_3BA4_1035": ("apparently compiler register/home residue", "Equal 281-byte extents and matching normalized instruction skeleton/CFG. Retained review localizes the remaining material difference to the DigMyTile argument pointer register (SI versus BX); semantic equivalence remains untested."),
    "o25_3BA4_1686": ("mixed / source-control-flow residue", "516 target versus 520 candidate bytes; normalized skeleton and CFG differ, including sentinel home and branch layout. Do not characterize as allocator-only."),
    "f_171C_0CF4": ("apparently stack-home allocation residue", "Equal 490-byte extents and matching normalized skeleton/CFG; six operand sites exchange BP-22 and BP-26. Compaction semantics still need replay comparison."),
    "FindIndex": ("control-flow/source lowering residue", "Equal 267-byte extents but CFG differs; target and candidate use opposite condition polarity/block order around upper/lower updates."),
    "f_0250_129E": ("apparently register-allocation residue", "Normalized skeleton/CFG match at 264/265 bytes, with an encoding-length difference; behavior not yet compared."),
    "o15_384C_0239": ("apparently stack-home allocation residue", "Equal 326-byte extents and matching skeleton/CFG; target segment word uses BP-6 while candidate uses BP-2. Compiler probes do not establish the real historical home decision."),
    "f_0250_1018": ("mixed / unlocalized", "CFG matches but normalized instruction skeleton does not; source-level rendering semantics have not been exhaustively compared."),
    "DrawBalloons": ("mixed / unlocalized", "CFG matches, but the target is 1060 bytes and the candidate 1053; multiple register, extension and call-frame differences remain."),
    "f_171C_09CC": ("mixed / dataflow residue", "CFG matches, but block/value materialization differs around resize/rehome and helper results."),
    "f_171C_0ADC": ("mixed / dataflow residue", "CFG matches; target materializes long/word values in homes where candidate uses registers, with later operand-width/form differences."),
    "f_171C_0FBC": ("width/type and control residue", "CFG differs; target zero-extends a byte before word comparisons while candidate performs direct byte tests, with another unsigned-branch polarity difference."),
    "LessonDone": ("structural / shared-tail residue", "Selected reviewed seed is 727 bytes versus target 723 and CFG differs (64 versus 65 blocks); earlier 715-byte split-case draft is weaker. See hardtail archive for negative evidence."),
    "f_1C62_0415": ("mixed / compare operand lowering", "CFG matches; target/candidate reverse compare operands and signed branch polarity at repeated sites."),
    "f_1E57_038E": ("structural / dataflow residue", "CFG differs; a substantial helper-result/pointer-value island differs in addition to frame/home changes."),
    "f_20E8_0903": ("apparently expression/addressing lowering", "CFG matches; target copies the current object pointer before loading the far destination, candidate folds the address into a memory operand."),
    "win_UnlockWin": ("apparently expression/addressing lowering", "CFG matches; target materializes an adjusted base and LES, candidate folds the offset into indirect addressing."),
    "f_23E6_0000": ("unknown local lifetime/CSE residue", "Target contains a reload from BP-10 absent from the candidate; semantic observability is not established."),
    "f_2505_0453": ("width/type and home residue", "CFG matches, but target masks a word from BP-14 while candidate reads a byte from BP-12 before comparing."),
    "win_DrawBitMap": ("structural / call-flow residue", "CFG differs; target returns from a helper and branches, while candidate makes a further helper call and changes the loop path."),
    "f_2815_0165": ("width/type and pointer-lowering residue", "CFG matches, but target LES-loads a far pointer and adds a volume field differently from candidate's split loads/clamp store."),
    "f_284A_0138": ("expression/byte-lane residue", "Both 25 bytes and CFG matches, but target uses AL zero-extension and CH/CL packing while candidate uses AH; same size does not imply equivalence."),
    "f_29D6_000A": ("expression/CSE residue", "Target 120 bytes versus candidate 116; shifts/multiply controls did not close it, and nearby variants had relocation/assumption issues."),
    "o10_35F5_0384": ("structural menu-lowering residue", "CFG differs; target's key dispatch shares two destinations through compact equality branches while candidate emits extra branch/jump paths."),
    "DrawMapCursor": ("expression evaluation-order residue", "CFG matches; paired global reads and multiply operands are evaluated in a different order."),
    "InvertPatch": ("expression evaluation-order residue", "CFG matches; candidate reads/subtracts global origin before computing stride product; target does the product first."),
    "win_PrintStyleTextInRect": ("apparently stack-home allocation residue", "CFG matches; target stores a live word in BP-12 while candidate holds it in SI through compare/divide."),
    "DisplayCard": ("apparently compare lowering residue", "Equal extents and matching CFG; same compare is expressed with reversed operands and equivalent-looking signed branch polarity. Runtime boundary still required."),
    "drawHistGraph": ("structural plus stack-home residue", "CFG differs; comparison uses different frame homes and branch polarity, and stack slots are not confidently mapped."),
}

CONTRACTS = {
    "f_0250_1018": ("render commands/framebuffer, selected map/life/pheromone reads, globals g_94E4/g_9126, helper-call order", "Sweep map planes, pheromone modes, cell values 0/0xfe/0xff and valid boundaries; compare normalized draw commands and touched cache/global state."),
    "f_0250_129E": ("cell cache entry, selected screen rectangle and normalized draw helper trace", "Exhaust 40x30 cells, cache hit/miss/sentinel, viewport offsets, top-row flag and map redraw state."),
    "DrawBalloons": ("normalized draw/blit/text/clip trace or framebuffer, balloon state, resource references, calls", "Cross balloon count/state, positions, screen bounds, resource misses and clipping rectangles."),
    "LessonDone": ("tutorial flags/counters, selected UI flow, dialog/window/audio callback trace, return/termination behavior", "Enumerate every original switch case/key result and tutorial completion state, including shared-tail cases and early returns."),
    "f_171C_09CC": ("resize result, handle validity, block type/size/content, lock state and normalized returned address", "Replay valid resize cases at exact-fit, split/coalesce threshold, locked, adjacent-free, EMS/non-EMS and failure boundaries."),
    "f_171C_0ADC": ("logical block ordering, handles, contents, predecessor/successor links and allocation totals; normalize physical segments", "Construct adjacent/nonadjacent free blocks, head/tail blocks and handle references; verify data preservation and link invariants."),
    "f_171C_0FBC": ("allocation success/pointer-handle identity, requested size/type, block list, preserved contents and allocator counters", "Vary size/type, exact-fit/split/fragmentation, reclaimable/discardable blocks, no-space, lock and EMS constraints."),
    "f_171C_0CF4": ("compaction result, logical handle order/validity, block metadata/content and free-space totals; physical addresses normalized", "Replay randomized valid heap topologies and sequences; compare every extant handle's content and normalized adjacency."),
    "FindIndex": ("found/missing result, returned index/pointer offset and any global search cursor", "Exhaust small sorted tables over all keys; then randomized duplicate-free/duplicate tables, empty/singleton/first/last/missing boundaries."),
    "f_1C62_0415": ("selection result, event consumption/order, dialog/window state, text/labels and save/restore region callbacks", "Exercise all choices, Escape/Enter/arrows/mouse, empty labels, narrow/wide text and event queue boundaries."),
    "f_1E57_038E": ("ordered logical clipping rectangle list, window origins, visibility, allocations/releases and window lock state", "Compare nested/overlapping/hidden windows, all screen edges, empty/full clip regions and 45-entry cache pressure."),
    "f_20E8_0903": ("object origin fields, dependent-object relationships, recalculated rectangles and lock/unlock state", "Vary all four edge modes/ref objects, direct/relative edge cases and repeated recalculation."),
    "win_UnlockWin": ("window lock count/state, pending update/draw callbacks and object visibility/clip state", "Exercise nested locks, final unlock, invalid handle, deferred redraw/update and already-unlocked behavior."),
    "f_23E6_0000": ("returned string contents/logical byte offset, text handle lock count and list state", "Sweep line before/at/after top, visible range, endOff, embedded empty/terminal strings and early NUL."),
    "f_2505_0453": ("returned object-field value or 0x8000 sentinel, lock/unlock trace and object state", "Exhaust valid/invalid window numbers, object indices at count boundary, kind/field indices and closed windows."),
    "win_DrawBitMap": ("normalized draw/blit/clip command trace, framebuffer, bitmap resource identity, window state and helper order", "Compare transparent/opaque modes, clipping edges, source offsets, missing resource, repeated draw and loop exit conditions."),
    "f_2815_0165": ("ordered AdLib register/value writes; instrument arguments/table values and final voice state", "Enumerate boundary instrument/note/volume/voice values, clamps, pitch-table transitions and invalid notes."),
    "f_284A_0138": ("packed return value and read-only input bytes; any global/audio effects", "Exhaust all input byte pairs or the full declared byte-domain, including zero/high-bit values."),
    "f_29D6_000A": ("ordered Tandy/audio port/register writes, arguments, channel state and any globals", "Sweep note/volume/channel boundaries and relevant mode bits; compare every write and its order."),
    "o10_35F5_0384": ("menu return/selection mutation, consumed key/event, menu/window state and callback trace", "Enumerate menu keys, selection positions, disabled/missing items, cancel/confirm and edge positions."),
    "DrawMapCursor": ("cursor draw command/framebuffer and cursor/map-origin state read from globals", "Cross both paired origin sets, coordinate extrema, scale values, map planes and clipping boundaries."),
    "InvertPatch": ("normalized invert/fill/line command trace or framebuffer and computed rectangle", "Sweep patch index/origin/stride, screen clipping, zero/negative coordinates and neighboring pixels."),
    "o15_384C_0239": ("function return plus text/font source bytes, output buffer/state and any draw/callback trace identified by oracle instrumentation", "Sweep selector argument and font/text modes; compare output content/length, invalid selector and any shared globals."),
    "win_PrintStyleTextInRect": ("normalized text/glyph/clip commands or framebuffer, measured extents, rectangle changes and returned status", "Vary style flags, wrapping, empty/long strings, rectangle sizes and clipping boundaries."),
    "DisplayCard": ("info-card model fields, window state, text/render commands, resource lookups and callbacks", "Cross card types, absent resource fields, boundary dimensions, selected entity states and open/closed window transitions."),
    "drawHistGraph": ("graph draw command/framebuffer, axes/points, clip state and read-only history samples", "Exercise empty, min/max, wraparound, equal, signed/boundary samples and all graph widths/heights."),
}

ORACLE = {
    "SpiderScan": {
        "status": "UNRESOLVED", "proposed_level": "BEHAVIOR_EXACT after differential pass",
        "source_semantics_evidence": "Current whole-module C body at src/root/m0CDB.c; HIGH Win16 pairing _SpiderScan at 5:5536 in evidence/cross_version/simantw_correspondence.json, with four anchored neighbors (DeadAntHere, SRand1, SRand4, caller). Pairing is semantic evidence, not behavioral proof.",
        "observable_boundary": ["integer return (found ant index or -1)", "all spider globals read/written by this routine: fd_50F6_1004, fd_50F6_0F12, fd_50F6_0F34 and any additional writes found by oracle instrumentation", "LifeA target cells", "AlistT[found]", "DeadAntHere effects on ant/death state", "DoLaserFire argument tuple and order", "SRand1 call count, arguments, returned values and final RNG state", "SRand4 call count/result and final RNG state", "FindAntIndex arguments/results", "all state reachable through DeadAntHere and DoLaserFire within the declared test fixture"],
        "dependency_abi": {
            "entry": "int far SpiderScan(void); no explicit parameters; far-call ABI state is harness-controlled.",
            "direct_globals": ["fd_50F6_1004 (direction basis)", "fd_50F6_0F12 / fd_50F6_0F34 (fixed-point spider position)", "LifeA[128][64] (candidate target cells)", "AlistT[] (found-ant type/liveness slot)"],
            "direct_calls": ["SRand1(12) -> int; called for each sampled direction/radius", "fracCOS(angle) / fracSIN(angle) -> long/fixed fraction; used to compute candidate cell", "FindAntIndex(1,x,y,life) -> index or negative sentinel", "DoLaserFire(old_x,old_y,(x<<4)+7,(y<<4)+7) -> void callback", "SRand4() -> int; gates ant removal", "DeadAntHere(x,y,life & 0x80) -> void callback when removal succeeds"],
            "dependency_contract_status": "Signatures/uses above come from current C declarations and calls. Purity, hidden globals, callback side effects, reentrancy and exact legacy calling behavior are UNKNOWN until instrumented against the DOS oracle. Capture ordered arguments, return values and logical post-state for each call."
        },
        "controls": ["Initialize the same full logical simulation state before each invocation; normalize addresses but compare pointed-to logical entities.", "Inject deterministic RNG return streams, recording every call; if DOS binary cannot intercept RNG, seed and compare final generator state plus outputs.", "Vary spider fixed-point position and direction, SMode-related state, all candidate LifeA values (0, 1..0xfd, 0xfe, 0xff), ant-list membership and boundary positions.", "Exercise no target, first/last target, valid/invalid list index, both pass loops, SRand4 kill/no-kill, and every SRand1 return lane.", "Compare post-state only for touched simulation fields and objects, plus explicit callback traces; exclude stack padding and DOS physical addresses."],
        "critical_discriminant": "The current candidate omits `sub ax,ax; mov [bp-2],ax` and retains the zero store to BP-8. BP-2 appears local, but an oracle run must show no output/RNG/callback/state difference over the boundary cases before calling it dead.",
        "coverage": {"directed": 0, "randomized": 0, "mismatches": None, "oracle_invocations": 0},
        "limitations": "No original-function invocation harness or differential cases are present in this inventory. The semantic claim is unproved."},
    "o25_3BA4_1035": {
        "status": "UNRESOLVED", "proposed_level": "BEHAVIOR_EXACT after differential pass",
        "source_semantics_evidence": "Current whole-module C body in src/S25/m3BA4.c and retained reviewed seed. Function is a void transition that calls ant-removal/map helpers, updates plane/x/y/direction/type globals, invokes DigMyTile, then writes the destination ant/map entry. No matching CONFIRMED/HIGH Win16 pair was found by exact DOS symbol name.",
        "observable_boundary": ["entry/exit values of fd_50F6_048C (plane), fd_50F6_047C/x, fd_50F6_048A/y, fd_50F6_0496/direction, fd_50F6_04C2/type and fd_50F6_104E gate", "relevant source and destination map tiles on both nest planes", "ant-list membership, ant type/state/direction and coordinates", "ordered calls and arguments to f_0BE8_0EB7, o22_39C7_1A57 when enabled, f_10F7_09A8, DigMyTile, and f_10F7_0A44", "all transitive map/ant mutations from those helpers, including returned/error state if any"],
        "dependency_abi": {
            "entry": "void far o25_3BA4_1035(void); no explicit parameters; semantic inputs are module globals.",
            "direct_globals": ["fd_50F6_048C (plane)", "fd_50F6_047C (x)", "fd_50F6_048A (y)", "fd_50F6_04C2 (ant type)", "fd_50F6_0496 (direction/state)", "fd_50F6_104E (optional edit/update gate)"],
            "direct_calls": ["f_0BE8_0EB7() -> void; called first", "o22_39C7_1A57(0,1) -> void; conditional on fd_50F6_104E", "f_10F7_09A8(old_plane,old_x,old_y,type,direction) -> void; source ant removal/update", "DigMyTile(new_plane,new_x,new_y) -> void; destination dig side effect", "f_10F7_0A44(new_plane,new_x,new_y,type,4,0xff) -> void; destination ant/map add"],
            "dependency_contract_status": "Names and signatures reflect current module declarations. The specific state reachable through each helper and its failure behavior remain unknown; record callback trace and the transitive logical tile/ant changes."
        },
        "controls": ["Cover both destination plane branches (x <= 0x40 and x > 0x40), all relevant x/y boundaries, type 0x60 and other types, fd_50F6_104E zero/nonzero, and destination tile states.", "Vary nest target occupancy, dig success/failure/side effects, ant list capacity and any helper-recognized digging state.", "Compare ordered helper traces as well as final logical map/list/global state; normalize handle/address identities."],
        "critical_discriminant": "Current report: target and candidate are both 281 bytes with matching normalized instruction skeleton and CFG. Retained analysis localizes codegen difference to SI versus BX for the DigMyTile coordinate argument. That supports a compiler-register explanation only; it does not prove call arguments/state are behaviorally identical.",
        "coverage": {"directed": 0, "randomized": 0, "mismatches": None, "oracle_invocations": 0},
        "limitations": "Helper callbacks and global/data effects must be observable in the harness. No tests have run."},
    "o25_3BA4_1686": {
        "status": "UNRESOLVED", "proposed_level": "BEHAVIOR_EXACT only after source reconciliation and exhaustive differential pass",
        "source_semantics_evidence": "Current whole-module C body in src/S25/m3BA4.c, with direct caller-state signature (far int* rot, far int* dir, plane, x, y, target a/b). Related adjacent helper logic supplies direction-delta arrays and TileCanBeMovedOn. The retained current candidate is 520 bytes versus 516 target and its normalized CFG differs; do not infer source certainty from its decompiler-like appearance.",
        "observable_boundary": ["return direction/sentinel", "the two caller-owned words *rot and *dir", "all globals read or written transitively by TileCanBeMovedOn and distance/direction helpers", "queried map/obstacle state and any mutation/callback trace", "RNG calls/final RNG state: no direct RNG call is visible in the current function body, but instrument transitive dependencies and verify zero consumption rather than assuming it"],
        "dependency_abi": {
            "entry": "int far o25_3BA4_1686(int far *rot, int far *dir, int plane, int x, int y, int a, int b); first two arguments are mutable far pointers; five remaining 16-bit integer inputs.",
            "direct_globals": ["fd_50F6_0A8E (movement mode/flag in candidate)", "fd_50F6_0AB6 / fd_50F6_0AC6 (previous position)", "fd_50F6_0AF8 / fd_50F6_0AD6 / fd_50F6_0AE8 (other ant/goal state passed to moveability query)", "fd_3D57_0000[] / fd_3D57_0008[] (8-neighbor x/y delta tables)"],
            "direct_calls": ["f_0BE8_0B83(x,y,a,b) -> int threshold/distance", "TileCanBeMovedOn(plane,nx,ny,fd_50F6_0AF8,fd_50F6_0AD6,fd_50F6_0AE8,flag) -> truth-valued int; candidate uses this to form the legal-neighbor mask", "f_0BE8_0B21(x,y,a,b) -> direction value; candidate writes return-minus-one to *dir on rotation reset/target reach"],
            "dependency_contract_status": "Signatures/uses reflect current C. No direct random call is visible, but helpers may have hidden reads, state or RNG effects; instrument them. The original instruction CFG mismatch means these are candidate-derived ABI roles and must be checked against the target call operands/data references."
        },
        "controls": ["Exhaustively enumerate rot and dir values in -2..9 plus representative out-of-range 16-bit values; all 8 legal neighbor masks; every target-distance tie class; previous-position equality and inequality; movement flag values and both plane classes.", "Sweep valid map edges/corners and invalid candidate coordinates; include each obstacle/movable result vector across 8 neighbors.", "Cross all direction vectors, target direction outputs of f_0BE8_0B21, threshold/dis values around equality, and direction preference rot=0, positive, negative.", "Use a very large seeded random campaign over logical map/ant states after directed partitions. Require zero mismatches; shrink every failure to minimal neighbor mask/rot/dir/geometry.", "Record every TileCanBeMovedOn query and exact order/arguments, plus all relevant globals and pointer outputs."],
        "critical_discriminant": "The function's C candidate has a different CFG/branch layout from the target; the candidate can therefore hide semantic source errors. First reconcile target predicates and branch destinations from the original stream, then run the same oracle inputs. The prompt's proposed exhaustive/random campaign has not been performed.",
        "coverage": {"directed": 0, "randomized": 0, "mismatches": None, "oracle_invocations": 0},
        "limitations": "This is highest risk. Do not label behavior-exact until target control-flow semantics and oracle results are both resolved."},
}

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def xver_status(name: str, root: Path) -> dict:
    findings = json.loads((root / "evidence/cross_version/dos_findings.json").read_text(encoding="utf-8"))
    corr = json.loads((root / "evidence/cross_version/simantw_correspondence.json").read_text(encoding="utf-8"))
    exact = [x for x in findings.get("findings", []) if x.get("dos") == name]
    pairs = [x for x in corr.get("pairs", []) if x.get("dos") == name]
    return {"dos_findings": exact, "correspondence": pairs,
            "semantic_pair_status": (pairs[0].get("confidence") if pairs else (exact[0].get("confidence") if exact else "NO_EXACT_NAME_PAIR_FOUND"))}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    ap.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ns = ap.parse_args()
    report = json.loads(ns.report.read_text(encoding="utf-8"))
    catalog = json.loads(ns.catalog.read_text(encoding="utf-8"))
    cat = {r["function"]: r for r in catalog["records"]}
    outrows = []
    for f in report["functions"]:
        name = f["function"]
        category, role = TAXONOMY.get(name, ("UNKNOWN", "No reviewed behavioral category is assigned."))
        c = cat.get(name, {})
        source_rel = c.get("best_source") or f.get("best_archived_source") or f.get("reviewed_seed")
        source = ROOT / source_rel if source_rel else None
        source_hash = sha256(source) if source and source.exists() else None
        resid = RESIDUE.get(name, ("unknown", "No function-specific residue characterization."))
        if resid[0].startswith("apparently"):
            semanticity = "CODEGEN_OR_LOWERING_SUSPECTED_NOT_PROVEN_BEHAVIOR_NEUTRAL"
        elif any(word in resid[0] for word in ("structural", "control-flow", "width/type")):
            semanticity = "SOURCE_OR_LOWERING_DIFFERENCE_UNRESOLVED"
        else:
            semanticity = "UNKNOWN_OR_MIXED"
        exact_name = name
        xver = xver_status(exact_name, ROOT)
        # In this phase every not-yet-proved claim remains UNRESOLVED. The proposed
        # category is a test destination, not an acceptance assertion.
        proposal = "BEHAVIOR_EXACT after contract-specific differential pass"
        if name in ("SpiderScan", "o25_3BA4_1035"):
            proposal = "BEHAVIOR_EXACT after differential pass"
        elif name == "o25_3BA4_1686":
            proposal = "BEHAVIOR_EXACT only after source reconciliation and exhaustive differential pass"
        row = {
            "function": name, "module": f["module"], "category": category,
            "category_basis": role, "status": "UNRESOLVED", "proposed_acceptance": proposal,
            "best_current_source": source_rel, "source_sha256": source_hash,
            "target_bytes": f["target_size"], "candidate_bytes": f["candidate_size"],
            "historical_candidate_exact": bool(f.get("strict", {}).get("exact")),
            "normalized_skeleton": f.get("semantic_skeleton"),
            "cfg_status": f.get("cfg", {}).get("status"),
            "cfg_similarity": f.get("cfg", {}).get("similarity"),
            "original_stream_evidence": {
                "target_instructions": len(f.get("normalized_instructions", {}).get("target", [])),
                "target_far_call_offsets": [i.get("placement", {}).get("offset") for i in f.get("normalized_instructions", {}).get("target", []) if i.get("mnemonic") in ("call", "lcall")],
                "target_relocation_sites": f.get("target_relocation_sites", []),
                "call_target_names": "Not available in this normalized stream; relocation sites are preserved as bound fixup markers. Candidate C declarations provide hypotheses only."
            },
            "likely_class": f.get("likely_class"),
            "residue_assessment": resid[0], "known_residue": resid[1],
            "residue_semanticity": semanticity,
            "next_hypothesis": f.get("recommended_next_hypothesis"),
            "retained_negative_evidence": c.get("exhausted_dimensions", []),
            "semantic_evidence": xver,
            "semantic_evidence_note": "The whole-module candidate compiles and preserves its reviewed accepted peers/private data per the retained catalog, but this is not proof that its source semantics match the DOS function. Exact-name cross-version evidence is listed separately; no pair means no such claim is made here.",
            "oracle_contract": ORACLE.get(name),
            "required_behavioral_oracle": (
                {"observable_boundary": ORACLE[name]["observable_boundary"], "minimum_directed_domain": ORACLE[name]["controls"], "coverage_recorded": False}
                if name in ORACLE else
                {"observable_boundary": list(CONTRACTS[name][0].split(", ")), "minimum_directed_domain": CONTRACTS[name][1], "coverage_recorded": False}
                if name in CONTRACTS else None
            ),
            "diagnostic_report_authority": report.get("authority"),
        }
        outrows.append(row)
    payload = {
        "schema": "behavioral-debt-inventory-v1",
        "authority": "DESCRIPTIVE_ONLY; no EXACT or BEHAVIOR_EXACT claims are made",
        "main_commit": "54cb824d19c2f897ab17c8b163a954121d4e4843",
        "historical_manifest_sha256": "c2850fb5d252bd490bb9d0d2994e1463b25a5e6a4f187ed4f4730dcf91e2f4fd",
        "source_report": str(ns.report.relative_to(ROOT) if ns.report.is_relative_to(ROOT) else ns.report),
        "source_report_sha256": sha256(ns.report),
        "catalog": str(ns.catalog.relative_to(ROOT) if ns.catalog.is_relative_to(ROOT) else ns.catalog),
        "functions": len(outrows),
        "target_function_bytes": sum(r["target_bytes"] for r in outrows),
        "unresolved_game_code_bytes": 15355,
        "unresolved_game_data_bytes": 129,
        "unresolved_code_outside_open_functions_bytes": 316,
        "inventory_note": "These 29 rows total 15,039 target function bytes. The separate 316 code-span bytes and 129 data bytes remain explicit historical debt; this inventory does not assign semantic ownership to them.",
        "functions_detail": outrows,
    }
    ns.out.parent.mkdir(parents=True, exist_ok=True)
    ns.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md = ns.out.with_suffix(".md")
    lines = [
        "# Behavioral debt inventory (diagnostic only)", "",
        "This report does not claim any function EXACT or BEHAVIOR_EXACT. All 29 remain UNRESOLVED until the required proof is recorded.", "",
        f"Source main: `{payload['main_commit']}`; manifest SHA-256 `{payload['historical_manifest_sha256']}`.",
        f"Known function target bytes: {payload['target_function_bytes']}; unresolved game code: {payload['unresolved_game_code_bytes']}; unresolved game data: {payload['unresolved_game_data_bytes']}.",
        "The additional 316 code-span bytes are outside the known open functions and remain separate historical debt.", "",
        "| Function | Category | Target/candidate | Skeleton / CFG | Residue reading | Proposed closure |",
        "|---|---|---:|---|---|---|",
    ]
    for r in outrows:
        lines.append(f"| {r['function']} | {r['category']} | {r['target_bytes']}/{r['candidate_bytes']} | {r['normalized_skeleton']} / {r['cfg_status']} | {r['residue_assessment']} | {r['proposed_acceptance']} |")
    lines += ["", "## Simulation oracle boundaries", "", "The JSON contains explicit contracts for SpiderScan, o25_3BA4_1035, and o25_3BA4_1686. Each has zero recorded oracle invocations and remains UNRESOLVED. A normalized instruction match or source review is not behavioral proof.", "", "## Evidence limits", "", "The normalized CFG and residue are diagnostic readings from the retained hard-tail report. Exact-name Win16 evidence is joined only when present; absence of a pair is reported as such and is not interpreted as semantic disagreement. Negative-search references are retained from the seed catalog without deleting or reclassifying them.", ""]
    md.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"functions": len(outrows), "target_function_bytes": payload["target_function_bytes"], "json": str(ns.out), "markdown": str(md)}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
