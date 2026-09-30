"""Classify every ASM claim as GENUINE assembly or C-SHAPED (worker asmrole).

    python build/workers/asmrole/features.py      # first
    python work/asmrole/classify.py      # -> classify_raw.json (+ table on stdout)

Proc-level exclusion codes.  Probes: build/workers/asmrole/probe/shape*.json (MSC 6.00AX, MSC 5.10),
probe/tc (Turbo C 2.0 -S listings), evidence/codegen/ASM-1, ASM-2, GS-1, FRAME-1, TU-1.

strong (no C compiler of the period emits this, and MSC 6 inline _asm cannot produce it either):
  SELF_MOD        store through cs: into the instruction bytes of a proc of the same frame
  FALLTHROUGH     proc does not end in ret/retf/iret/jmp: it runs into the next proc
  JMP_OUT/JMP_IN  jumps between procs (shared tails; compilers never jump across functions)
  RETN_IN_FAR     far proc that also contains near 'ret' subroutine code
  NEAR_SUB        proc returns with near 'ret' (register-convention subroutine inside a far module)
  NEAR_CALL       E8 call not preceded by push cs (large model C calls near only as push cs; call)
  IRET_NONSTD     iret without the MSC _interrupt prologue (push ax cx dx bx sp bp si di ds es)
  ODD_FRAME       'sub sp,odd'
  OP386           66h/67h prefixed 386 instructions (MSC 6 inline asm and TC 2.0 stop at 286)
  ADD_BP          'add bp,6' argument-pointer frame (sound driver shell convention)
  ASM1_NOFRAME    instructions only reachable through _asm (int/xlat/loop/jcxz/lods/scas/cmps/cli/
                  sti/pushf/popf/lahf/sahf/stc/clc/std/cld, byte/memory xchg, non-rep movs/stos) without
                  the BP frame and
                  'mov sp,bp; pop bp' epilogue MSC 6 always gives an _asm function (ASM-1; probe
                  shape2 asm_noframe/asm_arg)
  SEGREG_SAVE     ds/es saved at entry without the _loadds (mov ds,DGROUP) or _saveregs shape
  LJMP            far jmp (tail jump / thunk)
  EMPTY_SAVE      saves and restores SI/DI around an empty body (compilers save used regs only)
  NOP_ONLY        a lone nop between procs (assembler padding)
  REGARG_CALL     calls a far proc that takes register arguments
  DATA            undecodable bytes inside the proc
medium (not MSC 5.10 / 6.00 / 6.00A / 6.00AX output; an all-_asm body could still spell it):
  ASM2_SI_DI      push si before push di (ASM-2).  Turbo C 2.0 and MASM 'USES si di' order.
  AND_RR          'and r,r' zero test (MSC 5.10/6.x and TC 2.0: or r,r; probe shape ret0, tc f4/f5)
  MOV_R_0         'mov r16,0' (MSC: sub r,r; TC: xor r,r)
  XOR_ZERO        'xor r,r' outside the chkstk prologue and the string intrinsics (which use
                  'xor ax,ax; repne scasb', probe shape5); elsewhere MSC 6 uses sub r,r (shape3)
  POP_AX_CLEANUP  'pop ax' argument cleanup (MSC 6: pop bx; MSC 5.10: add sp,2; TC 2.0: pop cx)
  ADD_SP_EPILOG   'add sp,N; pop bp' after a call in a BP frame (MSC 6 and TC: mov sp,bp)
  OWN_FARCALL     relocated far call into its own code frame (TU-1: MSC emits push cs; call near
                  when the callee is in the same file)
  REG_ARGS        reads AX/BX/CX/DX/SI/DI/ES before writing them (register arguments)
  SS_DGROUP       ss: override on DGROUP variables (DS repointed inside the proc)
  LES_PUSH_ARG    'les bx,[bp+n]; push es; push bx' to pass a far pointer (MSC/TC push the words)
  LES_COPY        far pointer copied through les/es (MSC 6 copies through ax/dx; probe shape3 fpcopy, shape4 fpparam)
  BYTE_FROM_WORD  'mov ax,[bp+n]' then byte use of al (MSC loads 'mov al,[bp+n]'; probe shape3 bytestore, shape4 maskstore)
  IO_SEQ          port I/O with 'mov al,imm' / 'inc dx' (MSC outp intrinsic: mov ax,v; mov dx,p)
  DS_ES_VIA_AX    'mov ax,ds; mov es,ax' (informational only: MSC 6 /Ox and memcmp intrinsics emit it, shape5)
  ABS_ES_DIRECT   es:[imm] absolute access after mov es,0 (MSC 6 and TC: mov bx,imm; es:[bx])
  XOR_HALF        'xor ah,ah' zero extension (MSC: sub ah,ah; TC: mov ah,0)
  MUL_REG_SHAPE   16x16 multiply with register subtraction (MSC: sub ax,[bp+n]; mul cx)
C-shape evidence:  MSC_DI_SI (push di; push si), CHKSTK (call __aFchkstk), MOVSPBP (mov sp,bp).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[2]

C_ONLY_ASM = {"int", "into", "int3", "xlatb", "loop", "loope", "loopne", "jcxz", "lodsb", "lodsw",
              "lodsd", "scasb", "scasw", "cmpsb", "cmpsw", "cli", "sti", "pushf", "popf", "lahf",
              "sahf", "stc", "clc", "cmc", "std", "cld", "iret", "hlt",
              # non-rep string moves/stores: MSC 6 intrinsics and struct copies only emit the rep forms
              # (probe shape5); TC 2.0 copies structs through SCOPY@
              "movsb", "movsw", "stosb", "stosw"}
STRONG = {"SELF_MOD", "FALLTHROUGH", "JMP_OUT", "JMP_IN", "RETN_IN_FAR", "NEAR_SUB", "NEAR_CALL",
          "IRET_NONSTD", "ODD_FRAME", "OP386", "ADD_BP", "ASM1_NOFRAME", "SEGREG_SAVE", "DATA", "LJMP",
          "EMPTY_SAVE", "NOP_ONLY", "REGARG_CALL"}
MEDIUM = {"ASM2_SI_DI", "AND_RR", "MOV_R_0", "XOR_ZERO", "POP_AX_CLEANUP", "ADD_SP_EPILOG",
          "OWN_FARCALL", "REG_ARGS", "SS_DGROUP", "LES_PUSH_ARG", "LES_COPY", "BYTE_FROM_WORD",
          "IO_SEQ", "MUL_REG_SHAPE", "DS_ES_VIA_AX", "ABS_ES_DIRECT", "XOR_HALF"}
# compilers each medium idiom excludes (probes: shape*.json for MSC 6.00AX / 5.10, probe/tc for TC 2.0)
EXCLUDES = {
    "ASM2_SI_DI": {"msc600ax", "msc510"}, "AND_RR": {"msc600ax", "msc510", "tc20"},
    "MOV_R_0": {"msc600ax", "msc510", "tc20"}, "XOR_ZERO": {"msc600ax", "msc510"},
    "XOR_HALF": {"msc600ax", "msc510", "tc20"}, "POP_AX_CLEANUP": {"msc600ax", "msc510", "tc20"},
    "ADD_SP_EPILOG": {"msc600ax", "tc20"}, "OWN_FARCALL": {"msc600ax"}, "REG_ARGS": {"msc600ax", "msc510", "tc20"},
    "SS_DGROUP": {"msc600ax", "msc510", "tc20"}, "LES_PUSH_ARG": {"msc600ax", "msc510", "tc20"},
    "LES_COPY": {"msc600ax", "msc510", "tc20"}, "BYTE_FROM_WORD": {"msc600ax", "msc510", "tc20"},
    "IO_SEQ": {"msc600ax", "msc510"}, "MUL_REG_SHAPE": {"msc600ax"}, "DS_ES_VIA_AX": set(),
    "ABS_ES_DIRECT": {"msc600ax", "tc20"},
}
COMPILERS = ("msc600ax", "msc510", "tc20")
JUMPS = re.compile(r"^(j\w+|loop\w*|jcxz)$")


def target(op: str):
    m = re.fullmatch(r"0x([0-9a-f]+)|(\d+)", op.strip())
    if not m:
        return None
    return int(m.group(1), 16) if m.group(1) else int(m.group(2))


def classify(f, frame_ranges, jumped_into, regarg_callers):
    ev = []
    ins = f["ins"]
    mn = [i[1] for i in ins]
    ops = [i[2] for i in ins]
    raw = [bytes.fromhex(i[3]) for i in ins]
    body = [f"{m} {o}".strip() for m, o in zip(mn, ops)]
    lo, hi = f["off"], f["off"] + f["size"]
    frame = f["bp_frame"]
    # ---------------- strong
    for m, o in zip(mn, ops):
        dst = o.split(",")[0]
        if m.startswith("mov") and "cs:[" in dst:
            t = re.search(r"cs:\[(0x[0-9a-f]+|\d+)\]", dst)
            if t and any(a <= int(t.group(1), 0) < b for a, b, kind in frame_ranges if kind == "ASM"):
                ev.append("SELF_MOD")
                break
    last = mn[-1] if mn else ""
    if last not in ("ret", "retf", "iret", "jmp", "ljmp") and body != ["nop"]:
        ev.append("FALLTHROUGH")
    for m, o, r in zip(mn, ops, raw):
        if JUMPS.match(m) or (m == "jmp" and r[:1] in (b"\xe9", b"\xeb")):
            t = target(o)
            if t is not None and not (lo <= t < hi):
                ev.append("JMP_OUT")
                break
    if f["name"] in jumped_into:
        ev.append("JMP_IN:" + ",".join(sorted(jumped_into[f["name"]])))
    if "ret" in mn:
        ev.append("RETN_IN_FAR" if "retf" in mn else "NEAR_SUB")
    for k, (m, r) in enumerate(zip(mn, raw)):
        if m == "call" and r[:1] == b"\xe8" and not (k and body[k - 1] == "push cs"):
            ev.append("NEAR_CALL")
            break
    if "iret" in mn and body[:5] != ["push ax", "push cx", "push dx", "push bx", "push sp"]:
        ev.append("IRET_NONSTD")
    for m, o in zip(mn[:6], ops[:6]):
        if m == "sub" and o.startswith("sp,"):
            v = target(o.split(",")[1])
            if v is not None and v % 2:
                ev.append("ODD_FRAME")
    if f["prefix66"]:
        ev.append("OP386")
    if "add bp, 6" in body[:4]:
        ev.append("ADD_BP")
    asm_only = {m for m in mn if m in C_ONLY_ASM}
    # xchg: MSC intrinsics emit 'xchg si,di' (probe shape5 strcpy); byte or memory xchg is asm only (ASM-1)
    if any(m == "xchg" and (re.search(r"[a-d][lh]", o) or "[" in o) for m, o in zip(mn, ops)):
        asm_only.add("xchg")
    asm_only = sorted(asm_only)
    if asm_only and (not frame or not f["mov_sp_bp"]):
        ev.append("ASM1_NOFRAME:" + ",".join(asm_only))
    if ("ds" in f["saves"] or "es" in f["saves"]) and not any(m == "mov" and o.startswith("ds,") for m, o in zip(mn[:8], ops[:8])):
        ev.append("SEGREG_SAVE")
    elif not frame and any(b in ("push ds", "push es") for b in body[:3]):
        ev.append("SEGREG_SAVE")
    if "db" in mn:
        ev.append("DATA")
    if "ljmp" in mn:
        ev.append("LJMP")
    if body and all(b in ("push bp", "mov bp, sp", "push si", "push di", "pop si", "pop di", "pop bp", "retf") for b in body) \
            and any(b in ("push si", "push di") for b in body):
        ev.append("EMPTY_SAVE")
    if body == ["nop"]:
        ev.append("NOP_ONLY")
    if f["name"] in regarg_callers:
        ev.append("REGARG_CALL:" + regarg_callers[f["name"]])
    # ---------------- medium
    if f["save_order"] == "si,di":
        ev.append("ASM2_SI_DI")
    for m, o in zip(mn, ops):
        p = [x.strip() for x in o.split(",")]
        if m == "and" and len(p) == 2 and p[0] == p[1] and re.fullmatch(r"[a-d][xlh]|[sd]i|bp", p[0]):
            ev.append("AND_RR")
            break
    for m, o in zip(mn, ops):
        p = [x.strip() for x in o.split(",")]
        if m == "mov" and len(p) == 2 and re.fullmatch(r"[a-d]x|[sd]i", p[0]) and p[1] == "0":
            ev.append("MOV_R_0")
            break
    for k, (m, o) in enumerate(zip(mn, ops)):
        p = [x.strip() for x in o.split(",")]
        if m == "xor" and len(p) == 2 and p[0] == p[1] and not (f["chkstk"] and k + 1 < len(mn) and mn[k + 1] == "lcall")                 and not any(mn[j].startswith(("repne", "repe")) for j in range(k + 1, min(k + 3, len(mn)))):
            ev.append("XOR_ZERO")
            break
    for k in range(1, len(mn)):
        if body[k] == "pop ax" and mn[k - 1] in ("lcall", "call"):
            ev.append("POP_AX_CLEANUP")
            break
    if frame:
        for k in range(len(mn) - 1):
            if mn[k] == "add" and ops[k].startswith("sp,") and body[k + 1] == "pop bp":
                ev.append("ADD_SP_EPILOG")
                break
    for m, r in zip(mn, raw):
        if m == "lcall" and r[:1] == b"\x9a" and int.from_bytes(r[3:5], "little") == f["seg"]:
            ev.append("OWN_FARCALL")
            break
    if f["reg_in"]:
        ev.append("REG_ARGS:" + ",".join(f["reg_in"]))
    if any("ss:[" in o and "bp" not in o for o in ops):
        ev.append("SS_DGROUP")
    for k in range(len(mn) - 2):
        if mn[k] == "les" and "[bp +" in ops[k] and body[k + 1] == "push es":
            ev.append("LES_PUSH_ARG")
            break
    for k in range(len(mn) - 1):
        if mn[k] == "les" and any(mn[j] == "mov" and ops[j].endswith(", es") for j in range(k + 1, min(k + 4, len(mn)))):
            ev.append("LES_COPY")
            break
    for k in range(len(mn) - 1):
        if mn[k] == "mov" and ops[k].startswith("ax, word ptr [bp +") and (ops[k + 1].endswith(", al") or ops[k + 1].startswith("al, ")):
            ev.append("BYTE_FROM_WORD")
            break
    if any(m in ("out", "in") for m in mn) and any(b in ("inc dx", "dec dx") or b.startswith("mov al, ") for b in body):
        ev.append("IO_SEQ")
    for k in range(len(mn) - 1):
        if body[k] == "mov ax, ds" and body[k + 1] == "mov es, ax":
            ev.append("DS_ES_VIA_AX")
            break
    if any(re.search(r"es:\[0x[0-9a-f]+\]", o) for o in ops) and any(re.fullmatch(r"es, [a-d]x", o) for m, o in zip(mn, ops) if m == "mov"):
        ev.append("ABS_ES_DIRECT")
    for m, o in zip(mn, ops):
        p = [x.strip() for x in o.split(",")]
        if m == "xor" and len(p) == 2 and p[0] == p[1] and p[0] in ("ah", "bh", "ch", "dh"):
            ev.append("XOR_HALF")
            break
    if "mul" in mn and any(m == "sub" and re.fullmatch(r"[a-d]x, [a-d]x", o) for m, o in zip(mn, ops)):
        ev.append("MUL_REG_SHAPE")
    # ---------------- C shape
    cs = []
    if f["save_order"] == "di,si":
        cs.append("MSC_DI_SI")
    if f["chkstk"]:
        cs.append("CHKSTK")
    if f["mov_sp_bp"]:
        cs.append("MOVSPBP")
    return ev, cs


def main():
    feats = json.loads((HERE / "features.json").read_text())
    man = json.loads((ROOT / "layout/manifest.json").read_text())
    ranges = {}
    for key, m in man["modules"].items():
        for c in m["claims"]:
            ranges.setdefault((c["unit"], c["seg"]), []).append((c["off"], c["off"] + c["size"], c["kind"]))
    byframe = {}
    for f in feats:
        if f["kind"] == "ASM":
            byframe.setdefault((f["unit"], f["seg"]), []).append(f)
    jumped_into, regarg_callers = {}, {}
    for f in feats:
        if f["kind"] != "ASM":
            continue
        lo, hi = f["off"], f["off"] + f["size"]
        for a, m, o, r in f["ins"]:
            if JUMPS.match(m) or m == "jmp":
                t = target(o)
                if t is None or lo <= t < hi:
                    continue
                for g in byframe[(f["unit"], f["seg"])]:
                    if g is not f and g["off"] <= t < g["off"] + g["size"]:
                        jumped_into.setdefault(g["name"], set()).add(f["name"])
            rb = bytes.fromhex(r)
            if m == "lcall" and rb[:1] == b"\x9a":
                toff = int.from_bytes(rb[1:3], "little")
                tseg = int.from_bytes(rb[3:5], "little")
                for g in byframe.get((f["unit"], tseg), []) + byframe.get(("root", tseg), []):
                    if g["off"] == toff and not g["bp_frame"] and set(g["reg_in"]) - {"ax"}:
                        regarg_callers.setdefault(f["name"], g["name"])
    out = []
    for f in feats:
        if f["kind"] != "ASM":
            out.append({"module": f["module"], "name": f["name"], "kind": f["kind"], "size": f["size"], "off": f["off"],
                        "compatible_compilers": [], "proc_level": "data", "exclusions": ["DATA_IN_CODE"], "c_shape": []})
            continue
        ev, cs = classify(f, ranges[(f["unit"], f["seg"])], jumped_into, regarg_callers)
        strong = [e for e in ev if e.split(":")[0] in STRONG]
        medium = [e for e in ev if e.split(":")[0] in MEDIUM]
        level = "proc-strong" if strong else "proc-medium" if medium else "none"
        compat = set(COMPILERS)
        if strong:
            compat = set()
        for e in medium:
            compat -= EXCLUDES[e.split(":")[0]]
        if not f["bp_frame"] and not strong and "msc510" in compat:
            pass
        out.append({"module": f["module"], "name": f["name"], "kind": f["kind"], "size": f["size"], "off": f["off"],
                    "seg": f["seg"], "unit": f["unit"], "lin": f["lin"], "proc_level": level, "exclusions": ev, "compatible_compilers": sorted(compat),
                    "c_shape": cs, "head": f["head"], "tail": f["tail"]})
    (HERE / "classify_raw.json").write_text(json.dumps(out, indent=1))
    for o in out:
        if o["kind"] == "ASM":
            print(f"{o['module']:14} {o['name']:16} {o['size']:5} {o['proc_level']:12} {' '.join(o['exclusions'])}  | {' '.join(o['c_shape'])} | {','.join(o['compatible_compilers'])}")


if __name__ == "__main__":
    main()
