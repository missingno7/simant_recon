"""Initial function inventory of SIMANT.EXE by recursive descent (evidence, not acceptance).

Entry evidence, each recorded per function:
  far_call      a relocated ``9A off seg`` (or ``EA``) in any code unit
  vector        an RTLink overlay vector (0x2CFF:0x25F6...) naming section + target
  near_call     ``E8 rel16`` reached during descent (same code segment)
  push_cs_call  ``0E E8 rel16`` (MSC same-TU far call through near call)
  far_pointer   relocated segment word preceded by an offset word, in data (weak)
  mov_far_ptr   ``B8/B9/BA/BB imm`` pair loading off/seg of a code frame (weak)

Addresses are load-relative *linear* addresses inside a *unit* (``root``,
``S00``..``S26``).  Overlay sections share linear ranges, so the unit is
part of every function identity:  ``UNIT:SEG:OFF``.

Writes build/inventory/functions.json (derived) and prints a summary.
"""
from __future__ import annotations

import json
import struct
import sys
from collections import defaultdict
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_16

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exe as exemod  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "inventory"

# Root layout facts (see docs/exe-format.md).
ROOT_CODE_END_SEG = 0x2CFB          # RTLink manager starts here (third-party runtime)
MSC_TEXT_SEG = 0x29F4               # frame of the combined MSC runtime _TEXT (crt0 entry 0x29F4:0x001C)
OVERLAY_AREAS = (0x3126, 0x35F5, 0x384C, 0x39C7)
RESIDENT_DATA_SEG = 0x3D57

md = Cs(CS_ARCH_X86, CS_MODE_16)
md.detail = False


class Unit:
    def __init__(self, x: exemod.Executable, name: str):
        self.name = name
        self.base, self.data = x.unit_bytes(name)
        self.reloc_sites = {}   # linear of relocated word -> value
        for seg, off in x.unit_relocs(name):
            lin = seg * 16 + off
            self.reloc_sites[lin] = struct.unpack_from("<H", self.data, lin - self.base)[0]
        if name == "root":
            self.code_end = ROOT_CODE_END_SEG * 16
        else:
            self.code_end = self.base + len(self.data)

    def contains(self, lin: int) -> bool:
        return self.base <= lin < self.code_end

    def byte(self, lin: int) -> int:
        return self.data[lin - self.base]

    def word(self, lin: int) -> int:
        return struct.unpack_from("<H", self.data, lin - self.base)[0]


def area_of(seg: int) -> int | None:
    for a in OVERLAY_AREAS:
        pass
    if 0x3126 <= seg < RESIDENT_DATA_SEG:
        for a in reversed(OVERLAY_AREAS):
            if seg >= a:
                return a
    return None


class Inventory:
    def __init__(self):
        self.x = exemod.load()
        self.units = {u: Unit(self.x, u) for u in self.x.units() if u != "S27"}
        self.sections = self.x.sections
        # function key: (unit, linear) -> record
        self.funcs: dict[tuple[str, int], dict] = {}
        self.insn_owner: dict[tuple[str, int], tuple[str, int]] = {}
        self.jump_tables = []
        self.problems = []
        self.call_sites = []   # (unit, site, callee_unit, callee_linear, kind)
        self.vector_by_off = {v.offset: v for v in self.x.vectors}

    # -- entry resolution --------------------------------------------------------------
    def resolve_far(self, from_unit: str, seg: int, off: int, section: int | None = None):
        """Unit owning far target seg:off when referenced from ``from_unit``."""
        lin = seg * 16 + off
        if seg < ROOT_CODE_END_SEG:
            return "root", lin, "exact"
        if seg >= RESIDENT_DATA_SEG:
            return None, lin, "data"
        if section is not None and section != 0xFFFF:
            return f"S{section:02d}", lin, "vector"
        area = area_of(seg)
        if from_unit != "root" and self.sections[int(from_unit[1:])].load_seg == area:
            return from_unit, lin, "same-section"
        # Ambiguous: pick sections of that area with a prologue-like start at target.
        cands = []
        for s in self.sections[:27]:
            if s.load_seg != area:
                continue
            rel = lin - s.load_linear
            if 0 <= rel < len(s.data) - 3 and s.data[rel:rel + 3] in (b"\x55\x8b\xec", b"\xc8"):
                cands.append(s.name)
        if len(cands) == 1:
            return cands[0], lin, "prologue-unique"
        return None, lin, f"ambiguous:{','.join(cands)}"

    def add(self, unit: str, lin: int, seg: int, how: str, src: str | None = None):
        key = (unit, lin)
        f = self.funcs.get(key)
        if f is None:
            f = {"unit": unit, "linear": lin, "seg": seg, "off": lin - seg * 16,
                 "evidence": defaultdict(int), "callers": set()}
            self.funcs[key] = f
        f["evidence"][how] += 1
        if src:
            f["callers"].add(src)
        return f

    # -- seeds ----------------------------------------------------------------------------
    def seed(self):
        # Program entry points.
        self.add("root", 0x29F4 * 16 + 0x1C, 0x29F4, "msc_entry")
        for v in self.x.vectors:
            u, lin, why = self.resolve_far("root", v.target_seg, v.target_off, v.section)
            if u:
                self.add(u, lin, v.target_seg, "vector", f"vector:{v.offset:04X}")
        for un, U in self.units.items():
            for site, val in U.reloc_sites.items():
                if not U.contains(site) and un == "root":
                    continue
                op = U.data[site - 3 - U.base] if site - 3 >= U.base else None
                if op in (0x9A, 0xEA):
                    off = U.word(site - 2)
                    if val == exemod.MANAGER_SEG and off in self.vector_by_off:
                        v = self.vector_by_off[off]
                        tu, lin, why = self.resolve_far(un, v.target_seg, v.target_off, v.section)
                        self.call_sites.append((un, site - 3, tu, lin, "vector_call"))
                        continue
                    tu, lin, why = self.resolve_far(un, val, off)
                    if op == 0x9A:
                        self.call_sites.append((un, site - 3, tu, lin, "far_call"))
                    if tu:
                        self.add(tu, lin, val, "far_call" if op == 0x9A else "far_jmp", f"{un}:{site - 3:05X}")
                    elif why != "data":
                        self.problems.append({"site": f"{un}:{site - 3:05X}", "target": f"{val:04X}:{off:04X}", "why": why})

    # -- descent -----------------------------------------------------------------------
    def descend(self, key):
        unit, entry = key
        U = self.units[unit]
        f = self.funcs[key]
        seg = f["seg"]
        work = [entry]
        seen = set()
        extent_hi = entry
        while work:
            pc = work.pop()
            while True:
                if pc in seen or not U.contains(pc):
                    break
                owner = self.insn_owner.get((unit, pc))
                if owner and owner != key:
                    f.setdefault("overlaps", set()).add(owner)
                    break
                code = U.data[pc - U.base:pc - U.base + 16]
                insn = next(md.disasm(code, pc - seg * 16), None)
                if insn is None:
                    f.setdefault("bad", []).append(pc)
                    break
                seen.add(pc)
                self.insn_owner[(unit, pc)] = key
                n = insn.size
                extent_hi = max(extent_hi, pc + n)
                m = insn.mnemonic
                b = insn.bytes
                if m == "call" and b[0] == 0xE8:
                    tgt = seg * 16 + ((insn.address + n + struct.unpack_from("<h", b, 1)[0]) & 0xFFFF)
                    push_cs = pc - 1 >= U.base and U.byte(pc - 1) == 0x0E
                    g = self.add(unit, tgt, seg, "push_cs_call" if push_cs else "near_call", f"{unit}:{pc:05X}")
                    self.call_sites.append((unit, pc, unit, tgt, "near_call"))
                    self.pending.append((unit, tgt))
                elif m.startswith("j") or m in ("loop", "loope", "loopne", "jcxz"):
                    if b[0] in (0xEB, 0xE9) or (b[0] & 0xF0) == 0x70 or b[0] in (0xE0, 0xE1, 0xE2, 0xE3):
                        tgt = seg * 16 + int(insn.op_str, 16)
                        work.append(tgt)
                        if m == "jmp":
                            break
                    elif b[0] == 0x2E and b[1] == 0xFF and (b[2] & 0x38) == 0x20:
                        self.jump_table(unit, seg, pc, insn, work, f)
                        break
                    elif m in ("ljmp",):
                        break
                    else:
                        # indirect jmp without a table: stop
                        f.setdefault("indirect_jmp", []).append(pc)
                        break
                elif m in ("ret", "retf", "iret"):
                    break
                pc += n
        f["insns"] = len(seen)
        f["extent_end"] = extent_hi

    def jump_table(self, unit, seg, pc, insn, work, f):
        """MSC switch: ``jmp cs:[bx+T]``.  Table lies in the code segment."""
        U = self.units[unit]
        b = insn.bytes
        modrm = b[2]
        if modrm == 0xA7:  # [bx+disp16]
            tbl = seg * 16 + struct.unpack_from("<H", b, 3)[0]
        else:
            f.setdefault("indirect_jmp", []).append(pc)
            return
        # Bound: look back for "cmp ax/bx, N ; ja" to get the count.
        count = None
        for back in range(3, 30):
            code = U.data[pc - back - U.base:pc - U.base]
            ins = list(md.disasm(code, 0))
            if ins and sum(i.size for i in ins) == back:
                for i in ins:
                    if i.mnemonic == "cmp" and i.op_str.split(",")[0].strip() in ("ax", "bx", "si", "di", "cx", "dx"):
                        try:
                            count = int(i.op_str.split(",")[1], 16) + 1
                        except ValueError:
                            pass
                if count:
                    break
        if not count or count > 256:
            f.setdefault("indirect_jmp", []).append(pc)
            return
        targets = []
        for k in range(count):
            t = U.word(tbl + 2 * k)
            targets.append(t)
            work.append(seg * 16 + t)
        self.jump_tables.append({"unit": unit, "site": pc, "table": tbl, "count": count, "size": 2 * count})
        f.setdefault("jump_tables", []).append({"site": pc, "table": tbl, "count": count})

    def run(self):
        self.seed()
        self.pending = list(self.funcs.keys())
        done = set()
        while self.pending:
            key = self.pending.pop()
            if key in done or key[0] not in self.units:
                continue
            done.add(key)
            self.descend(key)
        return self

    # -- output -----------------------------------------------------------------------
    def records(self):
        # table extents are data inside code
        tables = defaultdict(list)
        for t in self.jump_tables:
            tables[t["unit"]].append((t["table"], t["table"] + t["size"]))
        callers = defaultdict(set)
        callees = defaultdict(set)
        for un, site, tu, tlin, kind in self.call_sites:
            src = self.insn_owner.get((un, site))
            if src is None or tu is None:
                continue
            a = f"{src[0]}:{src[1]:05X}"
            b = f"{tu}:{tlin:05X}"
            callers[b].add(a)
            callees[a].add(b)
        self.edges = (callers, callees)
        seqs = defaultdict(list)
        for un, site, tu, tlin, kind in sorted(self.call_sites, key=lambda c: (c[0], c[1])):
            src = self.insn_owner.get((un, site))
            if src is None or tu is None:
                continue
            seqs[f"{src[0]}:{src[1]:05X}"].append(f"{tu}:{tlin:05X}")
        self.call_seqs = seqs
        by_unit = defaultdict(list)
        for (u, lin), f in self.funcs.items():
            by_unit[u].append(f)
        out = []
        for u, fs in by_unit.items():
            fs.sort(key=lambda f: f["linear"])
            for i, f in enumerate(fs):
                nxt = fs[i + 1]["linear"] if i + 1 < len(fs) else None
                end = f.get("extent_end", f["linear"])
                # jump tables placed right after the body belong to the function
                for a, bnd in sorted(tables[u]):
                    if a >= end - 1 and a <= end + 1 and (nxt is None or bnd <= nxt):
                        end = max(end, bnd)
                rec = {
                    "id": f"{u}:{f['seg']:04X}:{f['off']:04X}",
                    "unit": u, "seg": f["seg"], "off": f["off"], "linear": f["linear"],
                    "end": end, "size": end - f["linear"],
                    "next_entry": nxt,
                    "evidence": dict(f["evidence"]),
                    "callers": sorted(callers.get(f"{u}:{f['linear']:05X}", ())),
                    "callees": sorted(callees.get(f"{u}:{f['linear']:05X}", ())),
                    "call_seq": self.call_seqs.get(f"{u}:{f['linear']:05X}", []),
                    "insns": f.get("insns", 0),
                }
                for k in ("jump_tables", "indirect_jmp", "bad"):
                    if f.get(k):
                        rec[k] = f[k]
                if f.get("overlaps"):
                    rec["overlaps"] = sorted(f"{a}:{b:05X}" for a, b in f["overlaps"])
                out.append(rec)
        return out


def classify_region(unit: str, lin: int) -> str:
    if unit == "root":
        if lin >= ROOT_CODE_END_SEG * 16:
            return "rtlink"
        if lin >= MSC_TEXT_SEG * 16:
            return "msc_runtime_text"
    return "game_or_library"


def main() -> int:
    inv = Inventory().run()
    recs = inv.records()
    for r in recs:
        r["region"] = classify_region(r["unit"], r["linear"])
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "functions.json").write_text(json.dumps({"functions": recs, "jump_tables": inv.jump_tables,
                                                    "problems": inv.problems}, indent=1))
    by = defaultdict(lambda: [0, 0])
    for r in recs:
        by[r["unit"]][0] += 1
        by[r["unit"]][1] += r["size"]
    total_code = sum(len(inv.units[u].data) if u != "root" else inv.units[u].code_end for u in inv.units)
    print(f"functions {len(recs)}; bytes covered {sum(v[1] for v in by.values())} of code units {total_code}")
    for u in sorted(by):
        U = inv.units[u]
        span = (U.code_end - U.base)
        print(f"  {u}: {by[u][0]:4d} functions, {by[u][1]:6d}/{span} bytes")
    print(f"jump tables {len(inv.jump_tables)}; unresolved far targets {len(inv.problems)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
