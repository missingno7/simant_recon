"""Whole-build harness (prototype): exact contributions, oracle-assisted hybrid, provenance map.

    python tools_link.py --root REPO [--jobs 8] [--reuse] [--no-hybrid-file]

Proof levels are kept distinct (build/workers/link/DESIGN.md):

(a) exact contributions: every byte written from a freshly compiled/assembled object (or an
    accepted historical runtime member) bound by the existing gate code
    (modules.verify_module / runtime.verify_all / runtime.verify_data with the ``collect``
    hook) and placed at its accepted address.  Generated linker fill (LINK_FILL, FAR_BSS,
    FORMAT_FILL) is produced by a stated rule, never read from the original, and counted
    apart from reconstruction.
(b) hybrid: every remaining byte is *debt*, categorised by a region model of the file, and is
    copied from the original only under that category.  The hybrid must equal the original
    (SHA-256).  Because debt is taken verbatim, a mismatch can only come from our own bytes or
    our placement arithmetic; a byte that no rule accounts for is a GAP, two contributions on
    one byte are an OVERLAP -- both fail the run.  The hybrid is never reconstruction.
(c) independent historical link: not attempted here (LEVEL_C.md).

The original is read (a) to compare, (b) to fill categorised debt and to take the file
geometry (header size, section record offsets, relocation slot of each entry).  All of this
is listed in the report under ``taken_from_original``.

Writes ROOT/build/link/{provenance.json, report.txt, collection.json, contrib.bin,
SIMANT.HYBRID.EXE}.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import time
from array import array
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------------------------
# provenance classes
# ---------------------------------------------------------------------------------------------
OWN = ("C", "ASM", "DATA_IN_CODE", "PAD", "DATA", "RUNTIME", "RUNTIME_DATA")   # level (a)
GENERATED = ("LINK_FILL", "FAR_BSS", "FORMAT_FILL")                           # rule output
RELOC = ("RELOC_OWN", "RELOC_OWN_ORDER_ORACLE")      # entry value from our fixup; slot see order
UNSET = "UNSET"
DGROUP = 0x55B3
# root region model (linear, load-relative).  Evidence: docs/exe-format.md, tools/runtime.py,
# layout/manifest.json; checked by this harness (no own byte may cross a boundary it does not own).
ROOT_GAME_END = 0x29F4C       # end of the last game code frame before the runtime (29F0 extent end)
TEXT_PREFIX_END = 0x29F5C     # 16 zero bytes before crt0 _TEXT (candidate: LINK /DOSSEG null area)
RUNTIME_END = 0x2CFB0         # end of the runtime _TEXT members (library order)
MANAGER_START = 0x2CFF0       # RTLink manager frame 2CFF; frame 2CFB holds crt0dat EMULATOR_TEXT
                              # and the game ASM jump table root:2CFB, then paragraph fill


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


@dataclass
class Reloc:
    site: int                 # linear address of the relocated segment word
    key: str | None           # RTLink target group (object property)
    index: int | None         # position in the object's FIXUPP order
    frame: int | None         # entry segment field; None = combined-segment frame (layout)


@dataclass
class Contribution:
    cls: str
    owner: str                # module key / runtime member
    name: str
    unit: str                 # root | Snn
    linear: int
    data: bytes
    obj_key: str              # relocation-order unit: one object segment
    obj_complete: bool        # the object's whole segment is accepted (complete TU, data segment, member)
    relocs: list = field(default_factory=list)
    derived: list = field(default_factory=list)       # (site, width, key) oracle-derived placements
    fixups: list = field(default_factory=list)
    segname: str = ""

    @property
    def end(self) -> int:
        return self.linear + len(self.data)


# ---------------------------------------------------------------------------------------------
# file geometry
# ---------------------------------------------------------------------------------------------
@dataclass
class Region:
    kind: str                 # mz_header mz_relocs header_pad image record_pad section_relocs section_data tail
    file_start: int
    file_end: int
    unit: str | None = None
    linear: int | None = None
    table: str | None = None


class Geometry:
    """Where every file byte lies.  ``debt_of(unit, linear)`` names the debt category of an
    unowned image byte; ``tables`` = {table: (file_offset, [(seg, off)], unit)}."""

    def __init__(self, size: int, regions: list[Region], tables: dict, debt_of, fill_rules=None):
        self.size = size
        self.regions = sorted(regions, key=lambda r: r.file_start)
        self.tables = tables
        self.debt_of = debt_of
        self.fill_rules = fill_rules or {}

    def image_region(self, unit: str, linear: int, n: int) -> Region:
        for r in self.regions:
            if r.kind in ("image", "section_data") and r.unit == unit and \
                    r.linear <= linear and linear + n <= r.linear + (r.file_end - r.file_start):
                return r
        raise KeyError(f"{unit}:{linear:05X}+{n} lies in no file region")

    def file_of(self, unit: str, linear: int, n: int = 1) -> int:
        r = self.image_region(unit, linear, n)
        return r.file_start + linear - r.linear


def geometry_from_exe(x, far_bss: tuple[int, int] | None) -> Geometry:
    """The real SIMANT.EXE geometry (tools/exe.py).  Region boundaries are the oracle's; they are
    part of what the hybrid takes from the original (the RTLink file layout)."""
    import exe as exemod
    d, mz = x.raw, x.mz
    tail = len(d) - 256
    regs = [Region("mz_header", 0, mz.reloc_offset),
            Region("mz_relocs", mz.reloc_offset, mz.reloc_offset + 4 * mz.reloc_count, table="root"),
            Region("header_pad", mz.reloc_offset + 4 * mz.reloc_count, mz.header_size),
            Region("image", mz.header_size, mz.header_size + len(x.image), "root", 0),
            Region("record_pad", mz.file_size, x.sections[0].file_para * 16)]
    tables = {"root": (mz.reloc_offset, list(x.relocs), "root")}
    for s in x.sections:
        rec = s.file_para * 16
        regs.append(Region("section_relocs", rec, rec + 4 * s.reloc_count, table=s.name))
        regs.append(Region("record_pad", rec + 4 * s.reloc_count, s.data_file_offset))
        end = min(s.data_file_offset + len(s.data), tail)
        regs.append(Region("section_data", s.data_file_offset, end, s.name, s.load_linear))
        tables[s.name] = (rec, list(s.relocs), s.name)
    regs.append(Region("tail", tail, len(d)))
    mgr = exemod.MANAGER_SEG * 16
    sect_tab = (mgr + exemod.SECTION_COUNT_OFF, mgr + exemod.SECTION_TABLE_OFF + 18 * len(x.sections))
    vec = (mgr + exemod.VECTOR_TABLE_OFF, mgr + exemod.VECTOR_TABLE_OFF + 10 * len(x.vectors))

    def debt_of(unit: str, lin: int) -> str:
        if unit == "root":
            if lin < ROOT_GAME_END:
                return "debt:game_code"
            if lin < TEXT_PREFIX_END:
                return "debt:text_prefix16"
            if lin < RUNTIME_END:
                return "debt:runtime_code"
            if lin < MANAGER_START:
                return "debt:frame_2CFB"
            if sect_tab[0] <= lin < sect_tab[1]:
                return "debt:rtlink_section_table"
            if vec[0] <= lin < vec[1]:
                return "debt:rtlink_vectors"
            return "debt:rtlink_manager"
        if unit != "S27":
            return "debt:overlay_code"
        if far_bss and far_bss[0] <= lin < far_bss[1]:
            return "FAR_BSS"
        return "debt:far_data" if lin < DGROUP * 16 else "debt:dgroup_data"

    return Geometry(len(d), regs, tables, debt_of)


# ---------------------------------------------------------------------------------------------
# provenance map
# ---------------------------------------------------------------------------------------------
class ProvMap:
    def __init__(self, geom: Geometry):
        self.g = geom
        self.classes = [UNSET]
        self.cidx = {UNSET: 0}
        self.code = bytearray(geom.size)            # class index per file byte
        self.owner = array("l", [-1]) * geom.size   # contribution / entry index per byte
        self.img = bytearray(geom.size)
        self.owners: list[str] = []
        self.errors: list[str] = []
        self.overlaps: list[str] = []

    def _c(self, cls: str) -> int:
        if cls not in self.cidx:
            self.cidx[cls] = len(self.classes)
            self.classes.append(cls)
        return self.cidx[cls]

    def put(self, fo: int, data: bytes, cls: str, owner: str) -> bool:
        """Write own/generated bytes; refuse any byte that already has a provenance (OVERLAP)."""
        if fo < 0 or fo + len(data) > self.g.size:
            self.errors.append(f"{owner}: file range {fo:#x}+{len(data)} outside the file")
            return False
        taken = [i for i in range(fo, fo + len(data)) if self.code[i]]
        if taken:
            other = self.owners[self.owner[taken[0]]] if self.owner[taken[0]] >= 0 else self.classes[self.code[taken[0]]]
            self.overlaps.append(f"OVERLAP {owner} and {other} at file {taken[0]:#x} ({len(taken)} bytes)")
            return False
        oi = len(self.owners)
        self.owners.append(owner)
        c = self._c(cls)
        self.img[fo:fo + len(data)] = data
        self.code[fo:fo + len(data)] = bytes([c]) * len(data)
        for i in range(fo, fo + len(data)):
            self.owner[i] = oi
        return True

    def fill_debt(self, oracle: bytes) -> list[str]:
        """Copy every unowned byte from the original under its debt category; bytes that no
        region rule categorises are GAPs (left zero, reported)."""
        gaps = []
        for r in self.g.regions:
            i = r.file_start
            while i < r.file_end:
                if self.code[i]:
                    i += 1
                    continue
                j = i
                while j < r.file_end and not self.code[j]:
                    j += 1
                self._debt_range(r, i, j, oracle, gaps)
                i = j
        # bytes outside every region
        covered = bytearray(self.g.size)
        for r in self.g.regions:
            covered[r.file_start:r.file_end] = b"\1" * (r.file_end - r.file_start)
        for i in range(self.g.size):
            if not covered[i] and not self.code[i]:
                gaps.append(f"GAP file {i:#x}: in no region")
                break
        return gaps

    def _debt_range(self, r: Region, i: int, j: int, oracle: bytes, gaps: list) -> None:
        if r.kind in ("header_pad", "record_pad"):
            self.put(i, bytes(j - i), "FORMAT_FILL", "rule:zero padding")   # generated, not copied
            return
        if r.kind == "mz_header":
            cats = [("debt:mz_header", i, j)]
        elif r.kind == "tail":
            cats = [("debt:common_tail", i, j)]
        elif r.kind in ("mz_relocs", "section_relocs"):
            cats = []
            _, entries, unit = self.g.tables[r.table]
            for e in range((i - r.file_start) // 4, (j - r.file_start + 3) // 4):
                seg, off = entries[e]
                cat = "debt:reloc_entry." + self.g.debt_of(unit, seg * 16 + off).split(":")[-1]
                a, b = max(i, r.file_start + 4 * e), min(j, r.file_start + 4 * e + 4)
                cats.append((cat, a, b))
        elif r.kind in ("image", "section_data"):
            cats = []
            a = i
            while a < j:
                cat = self.g.debt_of(r.unit, r.linear + a - r.file_start)
                b = a + 1
                while b < j and self.g.debt_of(r.unit, r.linear + b - r.file_start) == cat:
                    b += 1
                cats.append((cat, a, b))
                a = b
        else:
            gaps.append(f"GAP file {i:#x}-{j:#x} in region {r.kind}")
            return
        for cat, a, b in cats:
            if cat == "FAR_BSS":
                self.put(a, bytes(b - a), "FAR_BSS", "rule:far communals (linker zero fill)")
            elif cat.startswith("debt:"):
                self.put(a, oracle[a:b], cat, cat)
            else:
                gaps.append(f"GAP file {a:#x}-{b:#x}: unknown category {cat}")

    def ranges(self) -> list[dict]:
        out = []
        n = self.g.size
        i = 0
        while i < n:
            c, o = self.code[i], self.owner[i]
            j = i + 1
            while j < n and self.code[j] == c and self.owner[j] == o:
                j += 1
            out.append({"file": [i, j], "class": self.classes[c], "owner": self.owners[o] if o >= 0 else None})
            i = j
        return out

    def totals(self) -> Counter:
        cnt = Counter(self.code)
        return Counter({self.classes[k]: v for k, v in cnt.items()})


def finish(pm: ProvMap, oracle: bytes) -> tuple[bytes, list[str], list[str]]:
    """Fill categorised debt from the original and compare: (hybrid, gaps, first differences
    with the provenance of the differing bytes)."""
    gaps = pm.fill_debt(oracle)
    hybrid = bytes(pm.img)
    diffs = []
    i = 0
    while hybrid != oracle and i < len(oracle) and len(diffs) < 20:
        if hybrid[i] != oracle[i]:
            j = i
            while j < len(oracle) and hybrid[j] != oracle[j]:
                j += 1
            o = pm.owner[i]
            diffs.append(f"file {i:#x}-{j:#x}: {pm.classes[pm.code[i]]} {pm.owners[o] if o >= 0 else ''}")
            i = j
        else:
            i += 1
    return hybrid, gaps, diffs


# ---------------------------------------------------------------------------------------------
# generated fill between own contributions
# ---------------------------------------------------------------------------------------------
def link_fill_gaps(contribs: list[Contribution], unit_ends: dict[str, int],
                   boundaries: dict[str, list[int]] | None = None) -> list[tuple[str, int, int]]:
    """Gaps the linker fills with zero: 1 byte before a word-aligned next object (odd MSC segment
    end), < 16 bytes before a paragraph-aligned next object, before the end of an overlay
    section's data or before a paragraph-aligned region boundary (``boundaries``, e.g. the
    RTLink manager frame).  Both neighbours must be own contributions of different objects
    (or the section end / boundary)."""
    out = []
    by_unit = defaultdict(list)
    for c in contribs:
        by_unit[c.unit].append(c)
    for unit, cs in by_unit.items():
        cs.sort(key=lambda c: c.linear)
        for a, b in zip(cs, cs[1:]):
            g = b.linear - a.end
            if g <= 0 or a.obj_key == b.obj_key:
                continue
            if (g == 1 and b.linear % 2 == 0) or (g < 16 and b.linear % 16 == 0):
                out.append((unit, a.end, b.linear))
        end = unit_ends.get(unit)
        if end is not None and cs and 0 < end - cs[-1].end < 16 and end % 16 == 0:
            out.append((unit, cs[-1].end, end))
        for bnd in (boundaries or {}).get(unit, []):
            before = [c for c in cs if c.end <= bnd]
            after = [c for c in cs if c.linear < bnd < c.end]
            if before and not after and 0 < bnd - before[-1].end < 16 and bnd % 16 == 0 and                     not any(before[-1].end <= c.linear < bnd for c in cs):
                out.append((unit, before[-1].end, bnd))
    return out


# ---------------------------------------------------------------------------------------------
# relocation order
# ---------------------------------------------------------------------------------------------
def order_status(items: list[tuple]) -> str:
    """Order of one relocation *frame unit* (all entries of a table whose segment field is one
    frame, i.e. one combined segment).  ``items`` = [(object_start, fixup_index, group)] in the
    original's table order.  RTLink groups the frame's relocations by target symbol (docs/
    exe-format.md) -- across all objects of the frame, not per object (runtime _TEXT 29F4 and
    DGROUP _DATA 55B7 interleave their members' entries).  Inside a group the entries follow
    (object link order, FIXUPP order).

    EXACT: the table order is (object, FIXUPP) order -- no group reordering visible.
    GROUPED: inside every group the order is (object, FIXUPP); the order of the groups is the
    program-wide RTLink symbol order (a linker property, taken from the original).
    DIFF: the order inside some group differs (partial module, record breaks, ZI-1).
    Returns (status, set of groups whose inside order differs)."""
    obj = sorted(range(len(items)), key=lambda i: (items[i][0], items[i][1], i))
    if obj == list(range(len(items))):
        return "EXACT", set()
    groups = defaultdict(list)
    for i, it in enumerate(items):
        groups[it[2]].append(i)
    bad = {g for g, idx in groups.items() if idx != sorted(idx, key=lambda i: (items[i][0], items[i][1], i))}
    return ("DIFF" if bad else "GROUPED"), bad


def group_key(c: "Contribution", r: Reloc) -> str:
    """RTLink group of a relocation: external and group targets are program-wide symbols; a
    segment target is qualified by its object (object-local segment piece)."""
    k = r.key or "?"
    return f"{c.obj_key.split('/')[0]}|{k}" if k.startswith("segment:") else k


def place_relocations(pm: ProvMap, contribs: list[Contribution]) -> dict:
    """Write every original relocation entry whose site one of our fixups produces.  The entry
    value is ours (site offset; frame = our code frame or far placement, or for DGROUP data the
    combined-segment frame, which is layout taken from the original); the *slot* is the
    original's.  Order status per frame unit (order_status); the order is proven (RELOC_OWN)
    only in a complete frame unit whose table order is the object order (EXACT)."""
    g = pm.g
    own = {}          # (unit, site) -> (contribution, Reloc)
    ostart = {}
    for c in contribs:
        ostart[c.obj_key] = min(ostart.get(c.obj_key, c.linear), c.linear)
        for r in c.relocs:
            own[(c.unit, r.site)] = (c, r)
    report = {}
    used = set()
    layout_frames = defaultdict(set)
    frame_units = []
    for tname, (fo, entries, unit) in g.tables.items():
        units = defaultdict(list)
        total = Counter()
        frames_in_order = []
        for j, (seg, off) in enumerate(entries):
            total[seg] += 1
            if not frames_in_order or frames_in_order[-1] != seg:
                frames_in_order.append(seg)
            hit = own.get((unit, seg * 16 + off))
            if hit is not None:
                units[seg].append((j, hit[0], hit[1]))
        stats = Counter()
        if len(frames_in_order) != len(set(frames_in_order)) or frames_in_order != sorted(frames_in_order):
            stats["frames_not_contiguous_ascending"] = 1
        for fr, lst in units.items():
            complete = len(lst) == total[fr]
            st, bad = order_status([(ostart[c.obj_key], r.index if r.index is not None else 0, group_key(c, r))
                                    for _, c, r in lst])
            sfx = "" if complete else "_partial_frame"
            label = st + sfx
            frame_units.append({"table": tname, "frame": f"{fr:04X}", "own": len(lst), "entries": total[fr],
                                "objects": len({c.obj_key.split('/')[0] for _, c, _ in lst}), "order": label})
            for j, c, r in lst:
                seg, off = entries[j]
                used.add((unit, r.site))
                if r.frame is None:
                    frame = seg                               # combined-segment frame: layout (debt)
                    layout_frames[(tname, c.segname)].add(seg)
                    stats["frame_from_layout"] += 1
                    if not (seg * 16 <= r.site < seg * 16 + 0x10000):
                        pm.errors.append(f"relocation {tname}[{j}] frame {seg:04X} cannot address {r.site:05X}")
                else:
                    frame = r.frame
                    stats["frame_own"] += 1
                    if frame != seg:
                        pm.errors.append(f"relocation {tname}[{j}] at {r.site:05X}: our frame {frame:04X}, "
                                         f"original {seg:04X} ({c.owner})")
                cls = "RELOC_OWN" if label == "EXACT" else "RELOC_OWN_ORDER_ORACLE"
                entry = "EXACT" if st == "EXACT" else ("DIFF" if group_key(c, r) in bad else "GROUPED")
                stats[f"order_{entry}{sfx}"] += 1
                pm.put(fo + 4 * j, struct.pack("<HH", (r.site - frame * 16) & 0xFFFF, frame), cls, f"reloc:{c.owner}")
        stats["entries"] = len(entries)
        stats["own"] = sum(len(v) for v in units.values())
        report[tname] = dict(stats)
    extra = [f"{u}:{s:05X} ({own[(u, s)][0].owner})" for (u, s) in own if (u, s) not in used]
    if extra:
        pm.errors.append(f"{len(extra)} own relocation sites are not in the original tables: {extra[:5]}")
    report["_frame_units"] = frame_units
    report["_layout_frames"] = {f"{t}/{s}": sorted(f"{v:04X}" for v in fr) for (t, s), fr in layout_frames.items()}
    multi = {k: v for k, v in report["_layout_frames"].items() if len(v) > 1}
    if multi:
        report["_layout_frame_conflicts"] = multi
    return report


# ---------------------------------------------------------------------------------------------
# collection: compile every module once (parallel), bind with the gate code
# ---------------------------------------------------------------------------------------------
def collect(root: Path, jobs: int) -> dict:
    import modules as modmod
    import runtime as rtmod
    if "collect" not in modmod.verify_module.__code__.co_varnames:
        raise SystemExit("tools/modules.py lacks the collect hook (apply build/workers/link/collect_hook.patch)")
    man = modmod.load_manifest()

    def one(key):
        m = man["modules"][key]
        raw = (root / m["source"]).read_bytes()
        col = {}
        res = modmod.verify_module(raw.decode("latin1"), m, m["claims"], collect=col)
        return key, {"source_ok": sha(raw) == m["source_sha256"], "res": res, "col": col}

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=jobs) as ex:
        mods = dict(ex.map(one, sorted(man["modules"])))
    t1 = time.time()
    rtc = {}
    results, derived, _conf, _ = rtmod.verify_all(collect=rtc)
    dl = []
    rows = rtmod.verify_data(results, derived, collect=dl)
    return {"manifest": man, "modules": mods, "runtime_results": results, "runtime_bound": rtc,
            "runtime_data_rows": rows, "runtime_data_bound": dl,
            "timing": {"modules_s": round(t1 - t0, 1), "runtime_s": round(time.time() - t1, 1)}}


def _enc(o):
    if isinstance(o, (bytes, bytearray)):
        return {"__hex__": bytes(o).hex()}
    if isinstance(o, dict):
        return {("__k__" + json.dumps(list(k)) if isinstance(k, tuple) else k): _enc(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_enc(v) for v in o]
    if isinstance(o, set):
        return sorted(o)
    return o


def _dec(o):
    if isinstance(o, dict):
        if set(o) == {"__hex__"}:
            return bytes.fromhex(o["__hex__"])
        return {(tuple(json.loads(k[5:])) if k.startswith("__k__") else k): _dec(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_dec(v) for v in o]
    return o


# ---------------------------------------------------------------------------------------------
# contributions from the collection
# ---------------------------------------------------------------------------------------------
def contributions(col: dict) -> tuple[list[Contribution], dict]:
    man = col["manifest"]
    out, notes = [], defaultdict(list)
    for key, mm in col["modules"].items():
        m, res, c = man["modules"][key], mm["res"], mm["col"]
        if not mm["source_ok"]:
            notes["excluded"].append(f"{key}: source differs from the manifest hash")
            continue
        if not res.get("exact"):
            notes["excluded"].append(f"{key}: module not exact ({[n for n, v in res.get('claims', {}).items() if not v['exact']][:3]})")
            continue
        complete = bool(m.get("extent"))
        tu_order = (res.get("extent") or {}).get("reloc_order")
        covered = []
        for cl in c.get("code", []):
            if not res["claims"].get(cl["name"], {}).get("exact"):
                continue
            kind = cl["kind"] if cl["kind"] in ("C", "ASM", "DATA_IN_CODE") else "C"
            out.append(Contribution(kind, key, cl["name"], cl["unit"], cl["linear"], cl["bytes"],
                                    obj_key=key, obj_complete=complete and tu_order in ("EXACT", "GROUPED"),
                                    relocs=[Reloc(a, k, i, cl["seg"]) for a, k, i in cl["relocs"]],
                                    fixups=cl["fixups"], segname="code"))
            covered.append((cl["linear"], cl["linear"] + len(cl["bytes"])))
        cs = c.get("code_segment")
        if cs and complete and covered:
            # MSC word-alignment pad inside the object segment (verify_extent): the object's byte
            covered.sort()
            if covered[-1][1] == cs["end"] - 1 and len(cs["bytes"]) == cs["end"] - cs["start"]:
                out.append(Contribution("PAD", key, key + ":pad", m["unit"], cs["end"] - 1, cs["bytes"][-1:],
                                        obj_key=key, obj_complete=True, segname="code"))
        for d in c.get("data", []):
            dres = res.get("data", {}).get(d["segment"], {})
            if not dres.get("exact"):
                continue
            far = d["seg"] != DGROUP
            out.append(Contribution("DATA", key, f"{key}/{d['segment']}", "S27", d["start"], d["bytes"],
                                    obj_key=f"{key}/{d['segment']}",
                                    obj_complete=dres.get("reloc_order", "EXACT") != "WITHIN_GROUP_PENDING",
                                    relocs=[Reloc(a, k, i, d["seg"] if far else None) for a, k, i in d["relocs"]],
                                    segname=d["segment"] if not far else f"far:{d['seg']:04X}"))
        for n, dres in res.get("data", {}).items():
            if dres.get("kind") == "BSS":
                notes["bss_placements"].append(f"{key}/{n} {dres['size']} bytes (memory only, no file bytes)")
    # historical runtime: accepted members only (validate.py's rule)
    exact = {(r["member"], r["linear"]): r for r in col["runtime_results"] if r["exact"]}
    for row in man.get("runtime", {}).get("members", []):
        r = exact.get((row["member"], row["linear"]))
        if r is None or r["size"] != row["size"] or r["extra_segments"] != row.get("extra_segments", []):
            notes["excluded"].append(f"runtime {row['member']}: no longer binds as accepted")
            continue
        for b in col["runtime_bound"].get((row["member"], row["linear"]), []):
            out.append(Contribution("RUNTIME", "runtime:" + row["member"], f"{row['member']}/{b['segment']}", "root",
                                    b["start"], b["bytes"], obj_key=f"runtime:{row['member']}/{b['segment']}",
                                    obj_complete=True,
                                    relocs=[Reloc(a, k, i, b["frame"]) for a, k, i in b["relocs"]],
                                    derived=[tuple(v) for v in b["derived"]], segname=b["segment"]))
    import runtime as rtmod
    bound = {(d["member"], d["segment"], d["start"]): d for d in col["runtime_data_bound"]}
    okrows = {(d["member"], d["segment"], d.get("linear")) for d in col["runtime_data_rows"] if d.get("exact")}
    seen = set()
    for d in rtmod.accepted_data_segments(man):
        k = (d["member"], d["segment"], d["linear"])
        if k not in okrows or k not in bound:
            notes["excluded"].append(f"runtime data {d['member']} {d['segment']}: no longer verifies")
            continue
        if (d["linear"], d["size"], d["segment"]) in seen:
            notes["common_segments"].append(f"{d['member']} {d['segment']} @{d['linear']:05X} (overlaid, placed once)")
            continue
        seen.add((d["linear"], d["size"], d["segment"]))
        b = bound[k]
        out.append(Contribution("RUNTIME_DATA", "runtime:" + d["member"], f"{d['member']}/{d['segment']}", "S27",
                                b["start"], b["bytes"], obj_key=f"runtime:{d['member']}/{d['segment']}",
                                obj_complete=True, relocs=[Reloc(a, kk, i, None) for a, kk, i in b["relocs"]],
                                derived=[tuple(v) for v in b["derived"]], segname=d["segment"]))
    return out, notes


def fixup_closure(contribs: list[Contribution], col: dict) -> dict:
    """Level (c) readiness: how many code fixups resolve to an address that one of our own
    objects defines, versus an address known only from the registry (symbols.json, grounded in
    the original) or through the original's RTLink vector table."""
    import match
    starts = {(c.unit, c.linear) for c in contribs if c.cls in ("C", "ASM")}
    for r in col["runtime_results"]:
        if r["exact"]:
            for fr, off in r["public_addresses"].values():
                starts.add(("root", fr * 16 + off))
    data_spans = sorted((c.linear, c.end) for c in contribs if c.cls in ("DATA", "RUNTIME_DATA"))
    import bisect
    dstarts = [a for a, _ in data_spans]
    cnt = Counter()
    for c in contribs:
        for f in c.fixups:
            k = f["kind"]
            if k in ("own", "group", "placed"):
                cnt[f"self_{k}"] += 1
                continue
            s = match.obj_name_lookup(f["target"])
            if s is None:
                cnt["unresolved"] += 1
                continue
            if f.get("via_vector"):
                cnt["code_via_original_vector_table"] += 1
            lin = s["seg"] * 16 + s["off"]
            if k == "code":
                cnt["code_target_own" if (s.get("unit", "root"), lin) in starts else "code_target_registry_only"] += 1
            else:
                i = bisect.bisect_right(dstarts, lin) - 1
                own = i >= 0 and data_spans[i][0] <= lin < data_spans[i][1]
                cnt["data_target_own" if own else "data_target_registry_only"] += 1
    return dict(cnt)


# ---------------------------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------------------------
def run(root: Path, jobs: int, reuse: bool, write_hybrid: bool) -> int:
    sys.path.insert(0, str(root / "tools"))
    import exe as exemod
    import modules as modmod
    out_dir = root / "build" / "link"
    out_dir.mkdir(parents=True, exist_ok=True)
    x = exemod.load()
    oracle = x.raw
    cache = out_dir / "collection.json"
    man_sha = sha(json.dumps(modmod.load_manifest(), sort_keys=True).encode())
    t0 = time.time()
    if reuse and cache.exists() and json.loads(cache.read_text()).get("manifest_sha") == man_sha:
        col = _dec(json.loads(cache.read_text())["collection"])
        col["timing"] = {"reused": True}
    else:
        col = collect(root, jobs)
        cache.write_text(json.dumps({"manifest_sha": man_sha, "collection": _enc(col)}))
    contribs, notes = contributions(col)

    # FAR_BSS: accounted exactly as validate.py does (tools/farbss.py)
    import farbss
    man = col["manifest"]
    comdefs = defaultdict(list)
    for key, mm in col["modules"].items():
        for cm in mm["res"].get("communals", []):
            if cm.get("kind") == "far":
                comdefs[cm["name"][1:] if cm["name"][:1] == "_" else cm["name"]].append((cm["length"], key))
    texts = {k: (root / m["source"]).read_bytes().decode("latin1") for k, m in man["modules"].items()
             if m.get("lang", "c") == "c"}
    placed = [(c.linear, len(c.data)) for c in contribs if c.cls in ("DATA", "RUNTIME_DATA")]
    fb = farbss.account(texts, dict(comdefs), placed)
    far_bss = (farbss.FAR_BSS_SEG * 16, farbss.FAR_BSS_SEG * 16 + fb["size"]) if fb["accounted"] else None

    geom = geometry_from_exe(x, far_bss)
    pm = ProvMap(geom)
    # (a) own bytes
    for c in sorted(contribs, key=lambda c: (c.unit, c.linear)):
        try:
            fo = geom.file_of(c.unit, c.linear, len(c.data))
        except KeyError as e:
            pm.errors.append(f"{c.owner} {c.name}: {e}")
            continue
        pm.put(fo, c.data, c.cls, f"{c.owner}|{c.name}")
    own_bytes = {k: v for k, v in pm.totals().items() if k in OWN}
    # generated link fill
    unit_ends = {s.name: s.load_linear + len(s.data) for s in x.sections[:27]}
    fills = link_fill_gaps(contribs, unit_ends, {"root": [MANAGER_START]})
    for unit, a, b in fills:
        pm.put(geom.file_of(unit, a, b - a), bytes(b - a), "LINK_FILL", f"rule:link fill {unit}")
    link_fill_code = sum(b - a for u, a, b in fills if u != "S27")
    link_fill_data = sum(b - a for u, a, b in fills if u == "S27")
    link_fill_far = sum(b - a for u, a, b in fills if u == "S27" and b <= DGROUP * 16)
    # relocation entries
    rel = place_relocations(pm, contribs)
    # (b) debt from the original, by category
    hybrid, gaps, diffs = finish(pm, oracle)
    equal = hybrid == oracle
    tot = pm.totals()
    debt = {k: v for k, v in sorted(tot.items()) if k.startswith("debt:")}
    derived_fields = sum(len(c.derived) for c in contribs)
    derived_bytes = sum(w for c in contribs for _, w, _ in c.derived)
    closure = fixup_closure(contribs, col)
    # reconcile with validate.py's accounting (docs/progress.json)
    prog_p = root / "docs" / "progress.json"
    recon = {}
    if prog_p.exists():
        prog = json.loads(prog_p.read_text())
        pairs = {"exact_c_bytes": own_bytes.get("C", 0), "exact_asm_bytes": own_bytes.get("ASM", 0),
                 "exact_code_segment_data_bytes": own_bytes.get("DATA_IN_CODE", 0),
                 "historical_runtime_bytes_accepted": own_bytes.get("RUNTIME", 0),
                 "data_bytes_accepted": own_bytes.get("DATA", 0),
                 "historical_runtime_data_bytes_accepted": own_bytes.get("RUNTIME_DATA", 0),
                 "data_link_fill_bytes": link_fill_data,
                 "far_bss_zero_fill_bytes": tot.get("FAR_BSS", 0)}
        # region-level equivalents of validate.py's residual measures
        def cls_count(regions, exclude):
            n = 0
            for lo, hi in regions:
                cnt = Counter(pm.code[lo:hi])
                n += sum(v for k, v in cnt.items() if pm.classes[k] not in exclude)
            return n
        hdr = x.mz.header_size
        ovl = [(r.file_start, r.file_end) for r in geom.regions if r.kind == "section_data" and r.unit != "S27"]
        s27r = [(r.file_start, r.file_end) for r in geom.regions if r.kind == "section_data" and r.unit == "S27"]
        s27_end = x.sections[27].data_file_offset + len(x.sections[27].data)
        code_like = ("C", "ASM", "DATA_IN_CODE", "PAD")
        pairs["unresolved_code_bytes"] = cls_count([(hdr, hdr + TEXT_PREFIX_END)] + ovl, code_like)
        pairs["rtlink_manager_bytes_unaccepted"] = cls_count([(hdr + MANAGER_START, hdr + len(x.image))], OWN)
        pairs["unresolved_data_bytes"] = cls_count(s27r + [(s27r[-1][1], s27_end)],
                                                   ("DATA", "RUNTIME_DATA", "FAR_BSS")) - link_fill_far
        pairs["data_link_fill_bytes"] = link_fill_far
        why = {"unresolved_code_bytes": "validate counts root:2CFB (50 ASM bytes, frame 2CFB) as exact code but "
                                        "outside its game span 0..29F5C, so its residual is 50 bytes too low",
               "rtlink_manager_bytes_unaccepted": "validate starts the manager at 2CFB0; frame 2CFB holds root:2CFB "
                                                  "(50 ASM) and 12 bytes of paragraph fill -- the manager starts at 2CFF0",
               "unresolved_data_bytes": "validate counts only far paragraph fill as link fill"}
        recon = {k: {"validate": prog.get(k), "harness": v, "same": prog.get(k) == v,
                     **({"note": why[k]} if k in why and prog.get(k) != v else {})} for k, v in pairs.items()}
    vec_owned = sum(1 for v in x.vectors if ("root" if v.section == 0xFFFF else f"S{v.section:02d}",
                                              v.target_seg * 16 + v.target_off)
                    in {(c.unit, c.linear) for c in contribs if c.cls in ("C", "ASM")})
    failures = pm.errors + pm.overlaps + gaps + (["hybrid differs from the original"] if not equal else [])
    report = {
        "schema": "simant-link-provenance-v0",
        "oracle_sha256": x.sha256,
        "hybrid_sha256": sha(hybrid),
        "hybrid_equal": equal,
        "verdict": "PASS" if not failures else "FAIL",
        "failures": failures[:50],
        "first_differences": diffs,
        "level_a_exact_contributions": {
            "bytes_by_class": own_bytes, "bytes_total": sum(own_bytes.values()),
            "contributions": len(contribs),
            "runtime_fields_with_placement_derived_from_original": {"fields": derived_fields, "bytes": derived_bytes},
            "fixup_closure": closure,
            "bss_placements_memory_only": notes.get("bss_placements", []),
        },
        "generated_fill": {"LINK_FILL_code": link_fill_code, "LINK_FILL_data": link_fill_data,
                           "LINK_FILL_far_paragraph": link_fill_far,
                           "FAR_BSS": tot.get("FAR_BSS", 0), "FORMAT_FILL": tot.get("FORMAT_FILL", 0),
                           "far_bss_sizes": {k: fb[k] for k in ("bytes_verified", "bytes_consistent", "bytes_unverified")}},
        "relocations": rel,
        "reloc_bytes": {k: tot.get(k, 0) for k in RELOC},
        "debt_bytes": debt, "debt_total": sum(debt.values()),
        "taken_from_original": {
            "bytes": sum(debt.values()),
            "geometry": ["MZ header length and relocation-table offset", "section record file offsets "
                         "(file_para) and relocation counts", "relocation slot of every own entry "
                         "(program-wide RTLink group order and position among debt entries)",
                         "combined-segment frame of DGROUP relocation entries (layout frame)"],
            "layout_inputs_from_accepted_records": ["claim/extent addresses (manifest)", "data placements (manifest)",
                                                    "registry addresses of targets (layout/symbols.json)",
                                                    "RTLink vector addresses for cross-section calls (original vector table)",
                                                    "runtime data placements derived from original operands (runtime.py)"]},
        "vectors": {"count": len(x.vectors), "target_is_own_code_start": vec_owned},
        "reconciliation_with_validate": recon,
        "notes": {k: v for k, v in notes.items() if k != "bss_placements"},
        "timing": col.get("timing"),
        "class_list": pm.classes,
        "ranges": pm.ranges(),
    }
    (out_dir / "provenance.json").write_text(json.dumps(report, indent=1))
    contrib_img = bytes(v if pm.classes[pm.code[i]] in OWN + GENERATED + RELOC else 0 for i, v in enumerate(pm.img))
    (out_dir / "contrib.bin").write_bytes(contrib_img)
    if write_hybrid:
        (out_dir / "SIMANT.HYBRID.EXE").write_bytes(hybrid)
    txt = render(report, time.time() - t0)
    (out_dir / "report.txt").write_text(txt)
    print(txt)
    return 0 if not failures else 1


def render(r: dict, secs: float) -> str:
    a = r["level_a_exact_contributions"]
    L = [f"whole-build harness (prototype)  verdict {r['verdict']}  ({secs:.0f}s, timing {r['timing']})",
         f"original {r['oracle_sha256']}", f"hybrid   {r['hybrid_sha256']}  equal={r['hybrid_equal']}", "",
         "(a) exact contributions (own objects at accepted addresses):"]
    for k, v in sorted(a["bytes_by_class"].items()):
        L.append(f"    {k:<14}{v:>9,}")
    L.append(f"    {'total':<14}{a['bytes_total']:>9,}  in {a['contributions']} contributions")
    d = a["runtime_fields_with_placement_derived_from_original"]
    L.append(f"    of which runtime fixup fields bound via placements derived from original operands: "
             f"{d['fields']} fields / {d['bytes']} bytes")
    L.append(f"    fixup closure: {a['fixup_closure']}")
    g = r["generated_fill"]
    L += ["", f"generated (rule output, not reconstruction): LINK_FILL code {g['LINK_FILL_code']}, "
               f"data {g['LINK_FILL_data']}; FAR_BSS {g['FAR_BSS']:,}; FORMAT_FILL {g['FORMAT_FILL']:,}", "",
          "relocation tables (entries own / total; order status of own entries):"]
    tot_e = tot_o = 0
    agg = Counter()
    for t, s in r["relocations"].items():
        if t.startswith("_"):
            continue
        tot_e += s["entries"]
        tot_o += s["own"]
        for k, v in s.items():
            if k.startswith("order_") or k.startswith("frame_"):
                agg[k] += v
        L.append(f"    {t:<5} {s['own']:>5}/{s['entries']:<5} " + " ".join(
            f"{k[6:]}={v}" for k, v in sorted(s.items()) if k.startswith("order_")))
    L.append(f"    total {tot_o}/{tot_e}; " + ", ".join(f"{k}={v}" for k, v in sorted(agg.items())))
    fu = r["relocations"]["_frame_units"]
    L.append(f"    frame units: {len(fu)}; " + ", ".join(f"{k}={v}" for k, v in sorted(Counter(u['order'] for u in fu).items()))
             + f"; multi-object frames {sum(1 for u in fu if u['objects'] > 1)}")
    L.append(f"    DGROUP layout frames (from the original): {r['relocations']['_layout_frames']}")
    L.append(f"    reloc table bytes: {r['reloc_bytes']}")
    L += ["", f"debt (taken from the original in the hybrid, never reconstruction): {r['debt_total']:,} bytes"]
    for k, v in r["debt_bytes"].items():
        L.append(f"    {k:<34}{v:>9,}")
    L += ["", f"vectors: {r['vectors']}", "", "reconciliation with validate.py (docs/progress.json):"]
    for k, v in r["reconciliation_with_validate"].items():
        L.append(f"    {k:<34} validate {v['validate']!s:>8}  harness {v['harness']:>8}  {'ok' if v['same'] else 'DIFF'}"
                 + (f"  ({v['note']})" if v.get("note") else ""))
    for k, v in r["notes"].items():
        L.append(f"notes {k}: {len(v)}" + (f" e.g. {v[:3]}" if v else ""))
    if r["failures"]:
        L += ["", "FAILURES:"] + [f"    {f}" for f in r["failures"]]
    if r["first_differences"]:
        L += ["first differences:"] + [f"    {f}" for f in r["first_differences"]]
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="repository (or sandbox) root")
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--reuse", action="store_true", help="reuse build/link/collection.json if the manifest is unchanged")
    ap.add_argument("--no-hybrid-file", action="store_true")
    a = ap.parse_args()
    return run(Path(a.root).resolve(), a.jobs, a.reuse, not a.no_hybrid_file)


if __name__ == "__main__":
    raise SystemExit(main())
