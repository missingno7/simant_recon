"""DOS <-> Win16 SimAnt cross-version correspondence (evidence tool, never acceptance).

    python tools/xver.py build              # extract features for both versions, rank, write the database
    python tools/xver.py show NAME          # pairs + shared evidence for a DOS or Win16 function
    python tools/xver.py strings TEXT       # where a literal occurs on both sides

Features are extracted symmetrically from the two *original executables*:
  strings    NUL-terminated DGROUP literals addressed by an immediate operand
             (``mov r16,imm`` / ``push imm``) inside the function
  constants  immediates >= 0x100 that are not string addresses (rare ones weigh most)
  runtime    names of called C runtime functions (DOS: located LLIBCR publics;
             Win16: MAPSYM names of MICROSOFT_CRT symbols)
  switches   jump-table cardinalities
  shape      size, callers/callees counts
Machine-code similarity is deliberately *not* used: compilers, ABI and platform
layer differ (MSC 6 /AL /Os 8086 vs MSC 7 /AL /G2 Windows).

Confidence:
  CONFIRMED  set only by reviewed decisions (evidence/cross_version/decisions.json)
  HIGH       >= 2 rare shared strings, or 1 rare shared string + consistent rare constant/runtime
             signature, and the pair is mutually best
  MEDIUM     1 rare shared string (mutually best), or propagated through >= 2 aligned call edges of
             HIGH/CONFIRMED neighbours
  LOW        weaker shared evidence (kept for search, never used for naming)
  REJECTED   reviewed decisions only
Only CONFIRMED/HIGH pairs may transfer a Win16 name into DOS source, and the
evidence travels with the name (layout/symbols.json history).
"""
from __future__ import annotations

import argparse
import json
import math
import re
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_16

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exe as exemod  # noqa: E402
import functions as fnmod  # noqa: E402
import symbols as symmod  # noqa: E402

ROOT = exemod.ROOT
W16 = Path("D:/Prog/simantw_recon")
OUT = ROOT / "evidence" / "cross_version" / "simantw_correspondence.json"
DECISIONS = ROOT / "evidence" / "cross_version" / "decisions.json"
FEATURES = ROOT / "build" / "xver"
DGROUP = 0x55B3
md = Cs(CS_ARCH_X86, CS_MODE_16)

IMM_RE = re.compile(r"^(?:mov\s+(?:ax|bx|cx|dx|si|di),\s*|push\s+)(0x[0-9a-f]+)$")
ANY_IMM = re.compile(r"(?<![\[\w+-])(0x[0-9a-f]+)(?![\]\w])")


def cstring(buf: bytes, off: int, minlen: int = 4) -> str | None:
    if not (0 <= off < len(buf)):
        return None
    end = buf.find(b"\0", off, off + 400)
    if end < 0 or end - off < minlen:
        return None
    s = buf[off:end]
    if not all(0x20 <= c < 0x7F or c in (9, 10, 13) for c in s):
        return None
    if off > 0 and 0x20 <= buf[off - 1] < 0x7F:     # must start a string
        return None
    return s.decode("latin1")


def features_from_insns(insns, dgroup: bytes):
    strings, consts = [], []
    for mnem, ops in insns:
        text = f"{mnem} {ops}".strip()
        m = IMM_RE.match(text)
        if m:
            v = int(m.group(1), 16)
            s = cstring(dgroup, v)
            if s:
                strings.append(s)
                continue
        if mnem in ("lcall", "call", "ljmp", "jmp") or mnem.startswith("j") or mnem.startswith("loop"):
            continue
        for mm in ANY_IMM.finditer(ops):
            v = int(mm.group(1), 16)
            if v >= 0x100 and "bp" not in ops and "[" not in ops:
                consts.append(v)
    return strings, consts


# ---------------------------------------------------------------------------------------- DOS
def dos_features() -> dict:
    x = exemod.load()
    s27 = x.sections[27]
    dgroup = s27.data[DGROUP * 16 - s27.load_linear:]
    inv = json.loads((ROOT / "build" / "inventory" / "functions.json").read_text())
    syms = symmod.load()
    rt_by_addr = {(r["unit"], r["seg"], r["off"]): n for n, r in syms["runtime"].items()}
    code_by_lin = {}
    for f in inv["functions"]:
        code_by_lin[f"{f['unit']}:{f['linear']:05X}"] = f
    feats = {}
    for f in inv["functions"]:
        if f["region"] != "game_or_library":
            continue
        base, data = x.unit_bytes(f["unit"])
        b = data[f["linear"] - base:f["end"] - base]
        insns = [(i.mnemonic, i.op_str) for i in md.disasm(b, f["off"])]
        strings, consts = features_from_insns(insns, dgroup)
        runtime = []
        for c in f.get("callees", []):
            u, lin = c.split(":")
            lin = int(lin, 16)
            for (ru, rs, ro), n in rt_by_addr.items():
                if ru == u and rs * 16 + ro == lin:
                    runtime.append(n.lstrip("_"))
        name = fnmod.name_of(f["unit"], f["seg"], f["off"])
        feats[name] = {"address": f"{f['unit']}:{f['seg']:04X}:{f['off']:04X}", "size": f["size"],
                       "strings": sorted(set(strings)), "constants": sorted(set(consts)),
                       "runtime": sorted(set(runtime)),
                       "switches": sorted(t["count"] for t in f.get("jump_tables", [])),
                       "callers": [c for c in f.get("callers", [])], "callees": [c for c in f.get("callees", [])],
                       "call_seq": list(f.get("call_seq", []))}
    # translate edge ids to names
    lin2name = {}
    for n, r in feats.items():
        u, s, o = r["address"].split(":")
        lin2name[f"{u}:{int(s, 16) * 16 + int(o, 16):05X}"] = n
    rt_lin = {f"{u}:{sg * 16 + o:05X}": "rt:" + n.lstrip("_") for (u, sg, o), n in rt_by_addr.items()}
    for r in feats.values():
        r["callers"] = sorted({lin2name.get(c, c) for c in r["callers"]})
        r["callees"] = sorted({lin2name.get(c, c) for c in r["callees"]})
        r["call_seq"] = [rt_lin.get(c) or lin2name.get(c, c) for c in r["call_seq"]]
    return feats


# -------------------------------------------------------------------------------------- Win16
def w16_dgroup() -> bytes:
    raw = (W16 / "assets" / "SIMANTW.EXE").read_bytes()
    segs = json.loads((W16 / "evidence" / "census" / "segments.json").read_text())["segments"]
    dg = next(s for s in segs if s["name"] == "DGROUP")
    return raw[dg["file_offset"]:dg["file_offset"] + dg["logical_size"]]


def w16_features() -> dict:
    dgroup = w16_dgroup()
    inv = {r["name"] if "name" in r else None: r for r in []}
    crt = set()
    invp = W16 / "evidence" / "symbols" / "inventory.json"
    if invp.exists():
        for r in json.loads(invp.read_text()).get("symbols", json.loads(invp.read_text()) if isinstance(
                json.loads(invp.read_text()), list) else []):
            if isinstance(r, dict) and r.get("ownership") in ("MICROSOFT_CRT", "FLOAT_RUNTIME"):
                crt.add(r["name"])
    rec = json.loads((W16 / "src" / "recovery.json").read_text())["targets"]
    feats = {}
    callers = defaultdict(set)
    rows = []
    with (W16 / "evidence" / "disassembly" / "cards.jsonl").open() as fh:
        for line in fh:
            rows.append(json.loads(line))
    for r in rows:
        name = r["symbol"]
        insns = [(d["mnemonic"], d["operands"]) for d in r["disassembly"]]
        strings, consts = features_from_insns(insns, dgroup)
        callees = set()
        runtime = []
        seq = []
        site_calls = []
        for d in r["disassembly"]:
            if d["mnemonic"] in ("lcall", "call"):
                for ref in d.get("references", []):
                    if ref.get("names"):
                        site_calls.append({"names": ref["names"]})
                        break
        for c in site_calls:
            for n in (c.get("names", []) or [])[:1]:
                callees.add(n)
                if n in crt:
                    runtime.append(n.lstrip("_"))
                    seq.append("rt:" + n.lstrip("_"))
                else:
                    seq.append(n)
        for c in callees:
            callers[c].add(name)
        ext = r.get("extent") or {}
        feats[name] = {"address": f"{r['segment']}:{r['offset']:04X}", "segment_name": r.get("segment_name"),
                       "size": ext.get("size") or 0, "ownership": r.get("ownership"),
                       "strings": sorted(set(strings)), "constants": sorted(set(consts)),
                       "runtime": sorted(set(runtime)),
                       "switches": sorted(len(t.get("targets", [])) if isinstance(t, dict) else 0
                                          for t in ext.get("jump_tables", [])),
                       "callees": sorted(callees), "call_seq": seq,
                       "recovered_source": (rec.get(name) or {}).get("source"),
                       "proof": (rec.get(name) or {}).get("proof")}
    for n, r in feats.items():
        r["callers"] = sorted(callers.get(n, ()))
    return feats


# ------------------------------------------------------------------------------------ matching
def norm_string(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def rank(dos: dict, w16: dict, decisions: dict) -> list[dict]:
    dstr = defaultdict(set)
    wstr = defaultdict(set)
    for n, r in dos.items():
        for s in r["strings"]:
            dstr[norm_string(s)].add(n)
    for n, r in w16.items():
        for s in r["strings"]:
            wstr[norm_string(s)].add(n)
    dconst = Counter(c for r in dos.values() for c in r["constants"])
    wconst = Counter(c for r in w16.values() for c in r["constants"])
    scores = defaultdict(lambda: {"score": 0.0, "evidence": [], "rare_strings": 0, "rare_consts": 0})
    for s in set(dstr) & set(wstr):
        dn, wn = dstr[s], wstr[s]
        if len(s) < 5:
            continue
        rare = len(dn) <= 2 and len(wn) <= 2
        w = math.log(1 + 40 / (len(dn) * len(wn))) * (1.5 if len(s) >= 12 else 1.0)
        for a in dn:
            for b in wn:
                e = scores[(a, b)]
                e["score"] += w
                e["evidence"].append(f'string "{s[:60]}"' + ("" if rare else f" (shared by {len(dn)}/{len(wn)})"))
                e["rare_strings"] += 1 if rare else 0
    for (a, b), e in list(scores.items()):
        shared = set(dos[a]["constants"]) & set(w16[b]["constants"])
        for c in shared:
            if dconst[c] <= 3 and wconst[c] <= 3:
                e["score"] += 1.0
                e["rare_consts"] += 1
                e["evidence"].append(f"constant {c:#x}")
        rt = set(dos[a]["runtime"]) & set(w16[b]["runtime"])
        if rt:
            e["score"] += 0.2 * len(rt)
            e["evidence"].append("runtime " + ",".join(sorted(rt)))
        if dos[a]["switches"] and dos[a]["switches"] == w16[b]["switches"]:
            e["score"] += 1.0
            e["evidence"].append(f"switch cardinality {dos[a]['switches']}")
    # constant-only anchors for functions without strings (very rare constants on both sides)
    cd = defaultdict(set)
    cw = defaultdict(set)
    for n, r in dos.items():
        for c in r["constants"]:
            if dconst[c] == 1 and c >= 0x400:
                cd[c].add(n)
    for n, r in w16.items():
        for c in r["constants"]:
            if wconst[c] == 1 and c >= 0x400:
                cw[c].add(n)
    for c in set(cd) & set(cw):
        (a,), (b,) = cd[c], cw[c]
        if (a, b) not in scores:
            e = scores[(a, b)]
            e["score"] += 1.0
            e["rare_consts"] += 1
            e["evidence"].append(f"unique constant {c:#x}")
    best_d = {}
    best_w = {}
    for (a, b), e in scores.items():
        if e["score"] > best_d.get(a, (None, -1))[1]:
            best_d[a] = (b, e["score"])
        if e["score"] > best_w.get(b, (None, -1))[1]:
            best_w[b] = (a, e["score"])
    pairs = []
    for (a, b), e in scores.items():
        mutual = best_d[a][0] == b and best_w[b][0] == a
        if e["rare_strings"] >= 2 or (e["rare_strings"] >= 1 and e["rare_consts"] >= 1):
            conf = "HIGH" if mutual else "MEDIUM"
        elif e["rare_strings"] == 1 and mutual:
            conf = "MEDIUM"
        elif e["rare_consts"] >= 2 and mutual:
            conf = "MEDIUM"
        else:
            conf = "LOW"
        if conf == "LOW" and not mutual:
            continue
        pairs.append({"dos": a, "dos_address": dos[a]["address"], "win16": b, "win16_address": w16[b]["address"],
                      "confidence": conf, "score": round(e["score"], 3), "mutual_best": mutual,
                      "evidence": sorted(set(e["evidence"]))[:12], "method": "features-v1"})
    # propagation through call graph from HIGH anchors
    anchors = {p["dos"]: p["win16"] for p in pairs if p["confidence"] == "HIGH"}
    for d, w in decisions.items():
        if w.get("confidence") == "CONFIRMED":
            anchors[d] = w["win16"]
    known_w = set(anchors.values())
    prop = defaultdict(lambda: defaultdict(int))
    for a, b in anchors.items():
        dc = [c for c in dos.get(a, {}).get("callees", []) if c in dos]
        wc = [c for c in w16.get(b, {}).get("callees", []) if c in w16]
        if len(dc) == 1 and len(wc) == 1:
            prop[dc[0]][wc[0]] += 2
        dp = [c for c in dos.get(a, {}).get("callers", []) if c in dos]
        wp = [c for c in w16.get(b, {}).get("callers", []) if c in w16]
        if len(dp) == 1 and len(wp) == 1:
            prop[dp[0]][wp[0]] += 2
    have = {(p["dos"], p["win16"]) for p in pairs}
    for d, cands in prop.items():
        if d in anchors:
            continue
        (w, votes), = sorted(cands.items(), key=lambda kv: -kv[1])[:1]
        if w in known_w or (d, w) in have:
            continue
        pairs.append({"dos": d, "dos_address": dos[d]["address"], "win16": w, "win16_address": w16[w]["address"],
                      "confidence": "MEDIUM" if votes >= 2 else "LOW", "score": float(votes), "mutual_best": True,
                      "evidence": [f"sole callee/caller of an anchored pair ({votes} aligned edge votes)"],
                      "method": "callgraph-propagation-v1"})
    pairs += align_propagate(dos, w16, pairs, decisions)
    pairs += neighbourhood_propagate(dos, w16, pairs, decisions)
    # reviewed decisions override
    for d, w in decisions.items():
        for p in pairs:
            if p["dos"] == d and p["win16"] == w["win16"]:
                p["confidence"] = w["confidence"]
                p["evidence"] = w.get("evidence", []) + p["evidence"]
                p["method"] += "+reviewed"
                break
        else:
            pairs.append({"dos": d, "dos_address": dos.get(d, {}).get("address"), "win16": w["win16"],
                          "win16_address": w16.get(w["win16"], {}).get("address"), "confidence": w["confidence"],
                          "score": None, "mutual_best": None, "evidence": w.get("evidence", []), "method": "reviewed"})
    order = {"CONFIRMED": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "REJECTED": 4}
    pairs.sort(key=lambda p: (order[p["confidence"]], -(p["score"] or 0)))
    return pairs


def align_propagate(dos: dict, w16: dict, pairs: list, decisions: dict) -> list:
    """Propose pairs from ordered call sequences of anchored pairs.

    Both compilers keep source call order.  Between two consecutive aligned
    known calls (runtime names or already anchored functions), a gap holding
    exactly one unknown DOS callee and exactly one unknown Win16 callee votes
    for that pair.  Iterates to a fixed point; only HIGH/CONFIRMED anchors vote.
    """
    anchors = {p["dos"]: p["win16"] for p in pairs if p["confidence"] == "HIGH"}
    for d, w in decisions.items():
        if w.get("confidence") == "CONFIRMED":
            anchors[d] = w["win16"]
        elif w.get("confidence") == "REJECTED":
            anchors.pop(d, None) if anchors.get(d) == w["win16"] else None
    rejected = {(d, w["win16"]) for d, w in decisions.items() if w.get("confidence") == "REJECTED"}
    out = {}
    for _ in range(6):
        inv = {v: k for k, v in anchors.items()}
        votes = defaultdict(lambda: defaultdict(set))
        for a, b in anchors.items():
            ds = dos.get(a, {}).get("call_seq", [])
            ws = [c for c in w16.get(b, {}).get("call_seq", [])]
            dt = [anchors.get(c, c) if not c.startswith("rt:") else c for c in ds]
            known_d = [i for i, c in enumerate(dt) if c.startswith("rt:") or c in inv]
            sm = __import__("difflib").SequenceMatcher(a=dt, b=ws, autojunk=False)
            blocks = [blk for blk in sm.get_matching_blocks() if blk.size]
            prev_i, prev_j = 0, 0
            for blk in blocks + [type("B", (), {"a": len(dt), "b": len(ws), "size": 0})()]:
                gap_d = [c for c in dt[prev_i:blk.a] if not c.startswith("rt:") and c not in inv and c in dos]
                gap_w = [c for c in ws[prev_j:blk.b] if not c.startswith("rt:") and c not in anchors.values() and c in w16]
                if len(set(gap_d)) == 1 and len(set(gap_w)) == 1:
                    votes[gap_d[0]][gap_w[0]].add(a)
                prev_i, prev_j = blk.a + blk.size, blk.b + blk.size
        changed = False
        for d, cands in votes.items():
            if d in anchors:
                continue
            ranked = sorted(cands.items(), key=lambda kv: -len(kv[1]))
            w, srcs = ranked[0]
            if len(ranked) > 1 and len(ranked[1][1]) == len(srcs):
                continue
            if (d, w) in rejected or w in anchors.values():
                continue
            n = len(srcs)
            conf = "HIGH" if n >= 3 else "MEDIUM" if n >= 2 else "LOW"
            prev = out.get(d)
            if prev is None or prev["score"] < n:
                out[d] = {"dos": d, "dos_address": dos[d]["address"], "win16": w,
                          "win16_address": w16[w]["address"], "confidence": conf, "score": float(n),
                          "mutual_best": True,
                          "evidence": [f"aligned call-sequence gap in {len(srcs)} anchored caller(s): "
                                       + ", ".join(sorted(srcs)[:4])],
                          "method": "callseq-alignment-v1"}
            if conf == "HIGH" and d not in anchors:
                anchors[d] = w
                changed = True
        if not changed:
            break
    have = {(p["dos"], p["win16"]) for p in pairs}
    return [p for p in out.values() if (p["dos"], p["win16"]) not in have]


def neighbourhood_propagate(dos: dict, w16: dict, pairs: list, decisions: dict) -> list:
    """Pair unknown functions whose anchored callers/callees map onto each other.

    score(c, c') = |{anchored callers of c} mapped  &  callers of c'| +
                   |{anchored callees of c} mapped  &  callees of c'|
    Accepted only when c' is c's unique best and c is c''s unique best.
    >= 3 shared anchored neighbours -> HIGH (becomes an anchor), 2 -> MEDIUM, 1 -> LOW (not kept).
    """
    anchors = {p["dos"]: p["win16"] for p in pairs if p["confidence"] in ("HIGH", "CONFIRMED")}
    for d, w in decisions.items():
        if w.get("confidence") == "CONFIRMED":
            anchors[d] = w["win16"]
    rejected = {(d, w["win16"]) for d, w in decisions.items() if w.get("confidence") == "REJECTED"}
    out = {}
    for _ in range(10):
        inv = {v: k for k, v in anchors.items()}
        score = defaultdict(lambda: defaultdict(set))
        for d, r in dos.items():
            if d in anchors:
                continue
            for c in r["callers"]:
                if c in anchors:
                    for cand in w16.get(anchors[c], {}).get("callees", []):
                        if cand in w16 and cand not in inv:
                            score[d][cand].add("caller:" + c)
            for c in r["callees"]:
                if c in anchors:
                    for cand in w16.get(anchors[c], {}).get("callers", []):
                        if cand in w16 and cand not in inv:
                            score[d][cand].add("callee:" + c)
        best_for_w = defaultdict(lambda: (None, 0, 0))
        for d, cands in score.items():
            for w, ev in cands.items():
                b = best_for_w[w]
                if len(ev) > b[1]:
                    best_for_w[w] = (d, len(ev), 1)
                elif len(ev) == b[1]:
                    best_for_w[w] = (b[0], b[1], b[2] + 1)
        changed = False
        for d, cands in score.items():
            ranked = sorted(cands.items(), key=lambda kv: -len(kv[1]))
            w, ev = ranked[0]
            n = len(ev)
            if n < 2 or (len(ranked) > 1 and len(ranked[1][1]) == n):
                continue
            bw = best_for_w[w]
            if bw[0] != d or bw[2] != 1 or (d, w) in rejected:
                continue
            ratio = dos[d]["size"] / max(1, w16[w]["size"] or 1)
            plausible = 0.5 <= ratio <= 2.0
            conf = "HIGH" if n >= 3 and plausible else "MEDIUM"
            out[d] = {"dos": d, "dos_address": dos[d]["address"], "win16": w, "win16_address": w16[w]["address"],
                      "confidence": conf, "score": float(n), "mutual_best": True,
                      "evidence": [f"{n} anchored neighbours agree: " + ", ".join(sorted(ev)[:5]),
                                   f"size ratio {ratio:.2f}"],
                      "neighbours": n, "method": "neighbourhood-v1"}
            if conf == "HIGH" and d not in anchors:
                anchors[d] = w
                changed = True
        if not changed:
            break
    have = {(p["dos"], p["win16"]) for p in pairs}
    return [p for p in out.values() if (p["dos"], p["win16"]) not in have]


def build() -> int:
    FEATURES.mkdir(parents=True, exist_ok=True)
    dos = dos_features()
    w16 = w16_features()
    (FEATURES / "dos_features.json").write_text(json.dumps(dos, indent=0))
    (FEATURES / "w16_features.json").write_text(json.dumps(w16, indent=0))
    raw = json.loads(DECISIONS.read_text())["pairs"] if DECISIONS.exists() else {}
    by_addr = {r["address"]: n for n, r in dos.items()}
    decisions = {by_addr.get(k, k): v for k, v in raw.items()}
    pairs = rank(dos, w16, decisions)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    counts = Counter(p["confidence"] for p in pairs)
    db = {"schema": "simant-xver-correspondence-v1",
          "dos_oracle_sha256": exemod.EXPECTED_SHA256,
          "win16_exe": "D:/Prog/simantw_recon/assets/SIMANTW.EXE",
          "policy": "Only CONFIRMED/HIGH pairs may transfer names; acceptance is always the DOS compiler output.",
          "counts": dict(counts),
          "pairs": pairs}
    # bidirectional: attach DOS recovery status, export DOS findings for simantw_recon
    man = json.loads((ROOT / "layout" / "manifest.json").read_text())
    claimed = {}
    for key, m in man["modules"].items():
        for c in m["claims"]:
            claimed[c["name"]] = {"status": f"EXACT_{c.get('kind', 'C')}", "module": key, "source": m["source"],
                                  "profile": m["profile"], "flags": m["flags"]}
    for p in pairs:
        if p["dos"] in claimed:
            p["dos_recovery"] = claimed[p["dos"]]
    findings = []
    for p in pairs:
        if p["confidence"] in ("CONFIRMED", "HIGH") and p["dos"] in claimed:
            findings.append({"win16": p["win16"], "dos": p["dos"], "confidence": p["confidence"],
                             "dos_source": claimed[p["dos"]]["source"],
                             "dos_compiler": "MSC 6.00 " + " ".join(claimed[p["dos"]]["flags"]),
                             "evidence": p["evidence"][:4]})
    (OUT.parent / "dos_findings.json").write_text(json.dumps(
        {"schema": "simant-dos-findings-v1",
         "note": "DOS functions proven byte-exact whose Win16 counterparts are CONFIRMED/HIGH. The DOS source is "
                 "the natural MSC 6 form; it is a semantic hint for Win16, never a Win16 byte proof.",
         "findings": findings}, indent=1) + "\n")
    OUT.write_text(json.dumps(db, indent=1) + "\n")
    print(f"DOS functions {len(dos)}, Win16 functions {len(w16)}; pairs {dict(counts)}")
    return 0


def show(name: str) -> int:
    db = json.loads(OUT.read_text())
    for p in db["pairs"]:
        if name in (p["dos"], p["win16"], p["win16"].lstrip("_")):
            print(f"{p['dos']:<22} <-> {p['win16']:<28} {p['confidence']:<9} score {p['score']}  "
                  f"{'; '.join(p['evidence'][:6])}")
    return 0


def strings(text: str) -> int:
    dos = json.loads((FEATURES / "dos_features.json").read_text())
    w16 = json.loads((FEATURES / "w16_features.json").read_text())
    t = text.lower()
    for side, feats in (("DOS", dos), ("W16", w16)):
        for n, r in feats.items():
            for s in r["strings"]:
                if t in s.lower():
                    print(f"{side} {n:<28} {s[:80]}")
    return 0


def name_eligible(p: dict) -> bool:
    """Name transfer policy (conservative): CONFIRMED; HIGH anchored by rare strings or constants;
    neighbourhood HIGH with >= 4 agreeing anchored neighbours."""
    if p["confidence"] == "CONFIRMED":
        return True
    if p["confidence"] != "HIGH":
        return False
    if p["method"].startswith("features"):
        return any(e.startswith("string") or "constant" in e for e in p["evidence"])
    return p["method"].startswith("neighbourhood") and p.get("neighbours", 0) >= 4


def apply_names(dry: bool) -> int:
    db = json.loads(OUT.read_text())
    syms = symmod.load()
    taken = set(syms["code"]) | set(syms["data"])
    done = 0
    for p in db["pairs"]:
        if not name_eligible(p):
            continue
        old = p["dos"]
        new = p["win16"].lstrip("_")
        if new.upper() in ("WINMAIN", "LIBMAIN", "WEP") or new.upper().endswith(("WNDPROC", "DLGPROC")):
            continue                      # platform entry points keep DOS-appropriate names
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]{0,30}$", new) or old not in syms["code"] or new in taken:
            continue
        if not re.match(r"^(f|o\d\d)_[0-9A-F]{4}_[0-9A-F]{4}$", old):
            continue                      # already named
        print(f"{'would rename' if dry else 'rename'} {old} -> {new}  [{p['confidence']}] {p['evidence'][0][:70]}")
        if not dry:
            rec = syms["code"].pop(old)
            rec.setdefault("history", []).append({"was": old, "why": f"xver {p['confidence']} {p['method']}: "
                                                  + "; ".join(p["evidence"][:3])})
            syms["code"][new] = rec
            taken.add(new)
        done += 1
    if not dry:
        man = json.loads((ROOT / "layout" / "manifest.json").read_text())
        claimed = {c["name"] for m in man["modules"].values() for c in m["claims"]}
        renamed_claimed = claimed - set(syms["code"]) - {n for n in claimed if n in syms["runtime"]}
        if renamed_claimed:
            raise SystemExit(f"refusing: would rename claimed functions {sorted(renamed_claimed)}")
        symmod.save(syms)
    print(f"{done} names {'eligible' if dry else 'applied'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    an = sub.add_parser("apply-names"); an.add_argument("--dry-run", action="store_true")
    s = sub.add_parser("show"); s.add_argument("name")
    t = sub.add_parser("strings"); t.add_argument("text")
    a = ap.parse_args()
    if a.cmd == "build":
        return build()
    if a.cmd == "apply-names":
        return apply_names(a.dry_run)
    if a.cmd == "show":
        return show(a.name)
    return strings(a.text)


if __name__ == "__main__":
    raise SystemExit(main())
