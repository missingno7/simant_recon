"""Read-only bitmap ownership/domain audit. Writes only beside this script.

No compiler, executable generator, promotion, acceptance or oracle bytes in source.
Original instructions are retained as readable disassembly research evidence.
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import re
import struct
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import context as ctx
import exe
import functions


def pin(path: str | Path) -> dict:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    b = p.read_bytes()
    try:
        label = p.relative_to(ROOT).as_posix()
    except ValueError:
        label = p.as_posix()
    return {"path": label, "sha256": hashlib.sha256(b).hexdigest(), "size": len(b)}


def hits(path: str, pattern: str) -> dict:
    p = ROOT / path
    rx = re.compile(pattern, re.I)
    return {**pin(p), "hits": [{"line": i, "text": line.strip()}
                               for i, line in enumerate(p.read_text(encoding="latin1").splitlines(), 1)
                               if rx.search(line)]}


manifest = json.loads((ROOT / "layout/manifest.json").read_text())
symbols = json.loads((ROOT / "layout/symbols.json").read_text())
prior_path = "work/source-only-dos/structural-audits-v27/dos_bitmap_1f26_owner_v32/receipt.json"
prior = json.loads((ROOT / prior_path).read_text())
# Reopen the previous strict-effective source inventory and every canonical source.
# The full old source census stays in its retained receipt; this audit pins its aggregate.
sources = set(m["source"] for m in manifest["modules"].values())
sources.update(p["path"] for p in prior["source_pins"])
sources.update(p.relative_to(ROOT).as_posix()
               for p in (ROOT / "work/source-only-dos/providers").glob("*.c"))
source_pins = [pin(p) for p in sorted(sources)]
source_census = {
    "source_count": len(source_pins),
    "pin_list_sha256": hashlib.sha256(json.dumps(source_pins, sort_keys=True).encode()).hexdigest(),
    "target_identifier_files": [], "numeric_base_files": [],
    "dimension_or_alias_writes": [], "selector_mentions": [],
}
target_rx = r"\b_?fd_50F6_1F26\b"
number_rx = r"(?<![\w])(?:0x1f26[uUlL]*|1f26h|7974[uUlL]*)(?![\w])"
write_rx = r"\b(?:g_19BE|g_19C0|fd_55B3_19BE|fd_55B3_19C0)\s*(?:=(?!=)|\+=|-=|\+\+|--)"
for path in sorted(sources):
    for key, rx in [("target_identifier_files", target_rx), ("numeric_base_files", number_rx),
                    ("dimension_or_alias_writes", write_rx),
                    ("selector_mentions", r"\bfd_50F6_1102\b")]:
        row = hits(path, rx)
        if row["hits"]:
            source_census[key].append(row)
(OUT / "source-census-pins.json").write_text(json.dumps(source_pins, indent=2) + "\n")

targets = ["LoadTiles", "PreDrawSpider", "DrawSpider", "f_0250_13A6",
           "f_1B4E_003B", "f_16B5_0033", "f_16B5_007F", "f_16B5_00A5", "f_16B5_00AB",
           "f_2662_1120", "o00_35A6_0406", "o01_32B5_024F", "o03_3258_175F",
           "o00_35A6_02FD", "o01_32B5_0152", "o03_3258_05A7",
           "o00_35A6_0007", "o00_35A6_0177", "o01_32B5_000F", "o01_32B5_00AA",
           "o03_3258_040D", "o03_3258_04CE"]
all_context = []
contexts = {}
for target in targets:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ctx.show(target, raw=False, no_asm=False)
    text = buf.getvalue()
    contexts[target] = text
    all_context.append(text)
(OUT / "original-disassembly.txt").write_text("\n".join(all_context), encoding="utf-8")

x = exe.load()
const = manifest["modules"]["root:0250"]["placements"]["CONST"]
const_start = const["seg"] * 16 + const["off"]
const_end = const_start + const["size"]
run = 0
previous = None
const_relocations = []
for i, (seg, off) in enumerate(x.sections[27].relocs):
    site = seg * 16 + off
    value = struct.unpack("<H", x.read("S27", site, 2))[0]
    if value != previous:
        run += 1
    previous = value
    if const_start <= site < const_end:
        const_relocations.append({"ordinal": i, "dgroup_site": f"{site-0x55B3*16:04X}",
                                  "target_frame": f"{value:04X}", "target_frame_run": run})
target_word = next(r for r in const_relocations if r["dgroup_site"] == "7EEA")
assert target_word["target_frame"] == "50F6"
const_runs = sorted({r["target_frame_run"] for r in const_relocations if r["target_frame"] == "50F6"})
assert len(const_runs) > 1
payload_segment_site = 0x250 * 16 + 0x1A60
assert payload_segment_site in x.reloc_sites("root")
assert struct.unpack("<H", x.read("root", payload_segment_site, 2))[0] == 0x50F6

original_literal_candidates = []
for f in functions.table()["functions"]:
    name = functions.name_of(f["unit"], f["seg"], f["off"])
    for insn in ctx.md.disasm(x.read(f["unit"], f["seg"]*16+f["off"], f["size"]), f["off"]):
        if re.search(r"\b0x1f(?:26|28|2a)\b", insn.op_str):
            original_literal_candidates.append({"function": name, "unit": f["unit"],
                                                 "frame": f"{f['seg']:04X}",
                                                 "instruction_offset": f"{insn.address:04X}",
                                                 "instruction": f"{insn.mnemonic} {insn.op_str}"})

callback_shapes = []
for name, rows, words, pitch_shift in [("o00_35A6_0406", 64, 1, 3),
                                      ("o01_32B5_024F", 16, 1, 3),
                                      ("o03_3258_175F", 12, 3, 1)]:
    text = contexts[name]
    movsw = len(re.findall(r"(?m)^\s+[0-9A-F]+\s+movsw\b", text))
    add_di_bx = len(re.findall(r"(?m)^\s+[0-9A-F]+\s+add di, bx\b", text))
    assert movsw == rows * words and add_di_bx == rows
    callback_shapes.append({"function": name, "unrolled_rows": rows,
                            "bytes_copied_per_row": words * 2,
                            "row_pitch": f"destination_width >> {pitch_shift}",
                            "original_movsw_count": movsw, "original_add_di_bx_count": add_di_bx})

tile_cases = []
for modes, cell, selector, cb, tile_rows, tile_width_bytes, shift, divisor in [
    ([0,4,8],16,1,"o00_35A6_0406",64,2,3,2),
    ([2],12,2,"o03_3258_175F",12,6,1,2),
    ([3,5,7],16,3,"o01_32B5_024F",16,2,3,8)]:
    width = height = 7 * cell
    row_pitch = width >> shift
    advance = (cell // divisor) * width
    last_written_end = 6 * advance + 6 * tile_width_bytes + (tile_rows-1)*row_pitch + tile_width_bytes
    assert last_written_end == (width*height*4//8 if selector==1 else
                                width*height//2 if selector==2 else width*height//8)
    tile_cases.append({"graphics_modes": modes, "cell_width_and_height": cell,
                       "tile_selector": selector, "header_dimensions": [width,height],
                       "raster_callback": cb, "row_pitch_bytes": row_pitch,
                       "tile_row_advance_bytes": advance,
                       "tile_raster_required_payload_bytes": last_written_end,
                       "tile_raster_header_plus_written_extent": last_written_end+4,
                       "scope": "conditional initialized single-startup case; not capacity or all-writer closure"})

aliases = [{"name": n, **r} for n,r in symbols["data"].items()
           if r.get("seg") == 0x50F6 and r.get("off") == 0x1F26]
save_rows = []
for row in range(307):
    count, size, off, seg = struct.unpack("<HHHH",x.read("S27",0x4E4B*16+row*8,8))
    if seg==0x50F6 and off==0x1F26:
        save_rows.append({"row": row,"count": count,"element_bytes": size})
assert not save_rows
gap = 0x37D2 - 0x1F26

related = ["README.md", "AGENTS.md", "docs/codegen-rules.md", "docs/tu-evidence.md",
           "docs/cross-version.md", "layout/oracle.lock.json", "layout/manifest.json", "layout/symbols.json",
           "work/source-only-dos/static-completeness/index-v1.json", prior_path,
           "work/source-only-dos/event-resource-domain-v22/source-review-v22.md",
           "work/source-only-dos/event-resource-domain-v22/resource-observations-v22.json",
           "work/source-only-dos/g5a97-startup-dominance-review-v1.md",
           "work/source-only-dos/display-mode-selector-contract-v1.json",
           "work/takeover/residue-controls/bitmap_picture_views.py",
           "work/takeover/residue-controls/bitmap-picture-views.json",
           "work/takeover/fleet-lifetimes/fleet_root/bitmap_word_view.py",
           "work/takeover/fleet-lifetimes/fleet_root/bitmap_actual_args.py",
           "src/root/m0250.c", "src/root/m205F.c", "src/S20/m39F1.c", "src/root/m15F8.c",
           "src/root/m1B4E.asm", "src/root/m16B5.asm", "src/root/m1629.c", "src/root/m24AB.c",
           "src/root/m2662.c", "src/root/m1986.c", "src/root/m1A53.c", "src/S09/m35F5.c",
           "src/S00/m35A6.asm", "src/S01/m32B5.asm", "src/S03/m3258.asm",
           "work/source-only-dos/corrections/DrawBalloons/module.c",
           "work/source-only-dos/providers/remaining-ui-state.c",
           "evidence/cross_version/simantw_correspondence.json", "evidence/cross_version/decisions.json"]
win = Path("D:/Prog/simantw_recon/src/recovered/data_03_spider_point-0c795d9207.c")
receipt = {
    "schema": "simant-bitmap-storage-owner-audit-v37", "verdict": "UNRESOLVED",
    "admission_recommended": False, "canonical_or_production_edits": False,
    "oracle_usage": {"executable_sha256": x.sha256, "use": "read-only disassembly/relocation/zero-state/save-table research",
                     "bytes_copied_into_sources": 0, "game_or_fixture_execution": False},
    "inputs": [pin(p) for p in related] + [pin(win)], "audit_script": pin(Path(__file__)),
    "source_census": source_census,
    "source_census_full_pins": pin(OUT/"source-census-pins.json"),
    "original_disassembly": pin(OUT/"original-disassembly.txt"),
    "header_facts": {
        "base": "50F6:1F26", "header_bytes": 4, "fields": "signed DOS int width and height",
        "producer": "PreDrawSpider root:0250:1897/18A2 stores 7*g_19BE and 7*g_19C0",
        "payload": "DrawSpider root:0250:1A58/1A5D constructs 50F6:1F2A (=base+4)",
        "screen_consumer": "f_1B4E_003B reads +0/+2, passes +4 and dimensions to g_914C",
        "line_consumer": "f_16B5_0033 reads dimensions and installs payload+4 in near line state; no capacity field",
        "registered_exact_base_aliases": aliases,
        "persistent_SaveRec_at_exact_base": save_rows,
    },
    "private_data_and_fixups": {
        "root0250_CONST_placement": const,
        "bitmap_segment_word": target_word,
        "root0250_50F6_target_frame_runs": const_runs,
        "interpretation": "Many separated external target runs exclude using the common 50F6 frame as evidence that root0250 defines this far object. The target segment word and relocated payload far pointer identify an external base/prefix, not COMDEF type or length.",
        "payload_pointer_segment_relocation": {"frame":"0250","offset":"1A60","target_frame":"50F6"},
        "whole_original_function_table_literal_candidates": original_literal_candidates,
        "literal_scan_limit": "Direct immediate/displacement tokens are reviewed candidates; no claim that this excludes computed indirect aliases or malformed cross-object accesses.",
    },
    "independent_original_callback_shapes": callback_shapes,
    "conditional_tile_write_extents": tile_cases,
    "dimension_domain": {
        "source_initial_values": [16,16],
        "only_source_write": "LoadTiles mode 2 writes both dimensions to 12; accepted fixed-base aliases fd_55B3_19BE/fd_55B3_19C0 are consumers only in this census",
        "scope": "Single ordinary startup yields {16,16} or {12,12}; no resetting of 12 to 16 if startup/LoadTiles were called again.",
        "initialized_selector_modes": {"1":[0,4,8],"2":[2],"3":[3,5,7]},
        "uninitialized_selector_modes": [1,6],
        "mode1_path": "f_205F_0004 can detect CGA mode 1; its driver and resource paths are explicit. No inspected source guard establishes that every such startup exits before map rendering.",
        "mode6_path": "IBMInitStuff accepts /d2 and assigns graphics mode 6, dispatches S02 graphics and l256nt database; LoadTiles still omits mode 6.",
        "original_bad_selector_site": "DrawSpider 1A26..1A3D assigns [bp-10] only for selector 1/2/3. Other selectors branch directly to 1A3D; IDIV [bp-10] at 1A4A consumes an unassigned stack word.",
        "owned_selector_limit": "The existing source-functional far communal fd_50F6_1102 starts at zero under its startup contract; that is not the missing raster case, and cannot initialize DrawSpider's stack divisor or prove a write extent.",
    },
    "ordered_writer_and_consumer_paths": [
        "IBMInitStuff: f_205F_0004 installs mode callbacks before LoadTiles; LoadTiles precedes application map hook setup.",
        "f_0250_13A6: PreDrawSpider initializes sentinel/header on the visible spider path, PreDrawBalloons creates messages, DrawSpider runs only when tile-left !=500, then DrawBalloons composites, then screen consumer reads the bitmap. The final viewport-cell condition also reaches the screen call when tile-left==500; this relies on the existing sentinel/clip state, not fresh header production.",
        "DrawSpider: 49 tile callbacks write payload, f_16B5_0033 installs a header-limited line destination, f_2662_1120 overlays a resource, then DrawLegs/DrawPalps write through that installed line state.",
        "DrawBalloons: font index 2 -> MakeBalloon -> separately allocated balbuf -> intersection-copy callback reads spider into balbuf -> image decoder draws into balbuf -> intersection-copy writes balbuf into spider; copies are conditional on tile-left !=500.",
    ],
    "font_and_copy_domain_limits": {
        "font_buffer_separate": "MakeBalloon in m1629 derives width from font string widths, height from font height/newline count, and allocates balloon storage; DrawBalloons separately derives/allocates balbuf. Those allocations do not define the static spider object's capacity.",
        "copy_callbacks": "S00/S01/S03 copy callbacks intersect the supplied rects and compute raster offsets/strides from rect widths. In valid, consistent header/rectangle states the spider rect is 7 cells wide/high. Complete malformed font/string/balloon arithmetic and computed alias behavior is not proven by that intersection.",
        "line_state": "The line assembly installs +4 and width/height and a mode plotter, builds a 200-word row table. No complete static buffer declaration or length is supplied by the line state; bounds hold only for consistent positive header/domain inputs.",
    },
    "resource_domain": {
        "kind": 2, "normal_ids": ["03E8..03EF","041A..041D"],
        "packages": {"0/8":"hcegant", "odd":"monont", "2":"tdygant", "4":"lcegant", "6":"l256nt"},
        "lookup_order": "optional language, shared, optional lrshare for mode 2/4, selected graphics DB; cache keyed by object+kind; sound opens after initialization",
        "typed_shape": "f_2662_1120 dispatches type 3 to fd_50F6_37EA or type 0 to fd_50F6_3B58 with resource+8 and destination header",
        "normal_HCEGANT_limit": "Prior v22 pins positive heights and normal ID-specific endpoints inside 112x112 only for supplied HCEGANT and normal source-generated spider state. It expressly does not establish capacity.",
        "unchecked_rows": "Decoders clamp source height to remaining dest height but enter DEC/JNE row loops before testing termination; zero/negative row counts and unrestricted horizontal resource dimensions/shifts are integration facts, not a capacity bound.",
        "restored_selectors": "LoadGame copies SMode/Scycle/direction words directly; out-of-range values can index draw tables before resource lookup. No restored-state validation or same-layout behavior is established by current normal-state bounds.",
    },
    "adjacency_rejected_as_capacity": {"next_named_offset":"37D2", "address_gap_bytes":gap,
        "all_zero_initial_gap":not any(x.read("S27",0x50F6*16+0x1F26,gap)),
        "gap_exceeds_largest_initialized_tile_extent_by":gap-6276,
        "meaning":"6316 is registry/public adjacency only. Zero fill and a 40-byte surplus do not recover array capacity, record tail, original COMDEF declaration, or alias ownership."},
    "win16_limit": {"identity":"DrawSpider HIGH under xver (four anchored neighbours); PreDrawSpider reviewed CONFIRMED decision",
        "evidence":"Recovered Win16 data_03_spider_point explicitly owns only MapPoint x/y and declines its 6316-byte public span. It supplies no independently recovered DOS pixels declaration."},
    "exact_missing_facts": [
        "The defining source-owned complete header-plus-pixels object/COMDEF declaration and its full pixel extent. The canonical external Pnt names only the 4-byte header; no definition, sizeof/allocation/copy-size producer independently establishes the tail.",
        "For a functional extent derived from all writer paths, a justified reachable rendering domain must exclude or recover modes 1/6 selector handling and establish consistent positive dimensions and selectors; the observed unassigned stack divisor cannot be replaced by a default.",
        "An independent full selected-resource/font/restored-state domain for every writer/copy/line path, or a recovered original capacity/layout owner that preserves specified alias effects. Conditional HCEGANT endpoints, screen bounds and adjacent publics do not supply this contract.",
    ],
    "no_new_compiler_experiments": "Stopped at missing declaration/domain facts. Syntactic matching variants cannot recover an absent capacity; retained searches reviewed but not rerun. No new acceptance or runtime result is claimed.",
}
(OUT / "receipt-v37.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"verdict":receipt["verdict"],"admission_recommended":False,
                  "source_count":len(sources),"target_files":len(source_census["target_identifier_files"]),
                  "numeric_base_files":len(source_census["numeric_base_files"]),
                  "callback_shapes":callback_shapes,"tile_extents":tile_cases,
                  "source_outputs":["receipt-v37.json","source-census-pins.json","original-disassembly.txt"]},indent=2))
