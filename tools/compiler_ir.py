"""Research-only capture of MSC 6.00AX C1 pass intermediates.

This tool substitutes a tiny DOS file-copy program for pass 2 via /B2. It does
not patch or alter the pinned compiler files, and its output is never accepted by
the reconstruction gates. Usage:

  python tools/compiler_ir.py capture SOURCE.c --label s15-base
  python tools/compiler_ir.py matrix cases.json
  python tools/compiler_ir.py compare CAPTURE_A CAPTURE_B

The capture hook retains the raw EX/IN/ST/SY streams. EX is the useful C1
front-end stream; the other records are still saved because they may carry
symbol/type or source bookkeeping. This script deliberately reports raw byte
differences and only normalizes explicitly recognized source-name metadata.
"""
from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import compiler  # noqa: E402
import modctx  # noqa: E402

CAPTURE_ASM = ROOT / "tools" / "research" / "capture_ir.asm"
AX_PROFILE = "msc600ax"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _dosbox_conf(work: Path, pinned: Path, masm_dir: Path, runner: dict) -> str:
    conf: list[str] = []
    for section, values in runner["conf"].items():
        conf.append(f"[{section}]")
        conf.extend(f"{key}={value}" for key, value in values.items())
    conf += [
        "[autoexec]",
        f'mount d "{pinned}" -ro',
        f'mount e "{work.resolve()}"',
        f'mount m "{masm_dir}" -ro',
        "e:",
        "call RUN.BAT",
        "exit",
    ]
    return "\n".join(conf) + "\n"


def capture(source_path: Path, label: str, out_root: Path, profile: str = AX_PROFILE,
            flags: list[str] | None = None, timeout: int = 240) -> dict:
    source_path = source_path.resolve()
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    if profile != AX_PROFILE:
        raise ValueError("C1 intermediate interception is pinned to msc600ax (/EM)")
    flags = list(flags if flags is not None else ["/AL", "/Os"])
    if "/AL" not in flags:
        raise ValueError("capture requires the requested large-model profile")
    compiler.check_flags([*flags, "/EM"])
    prof = compiler.verify_profile(profile)
    tc = compiler.toolchain()
    runner = tc["runners"][prof["runner"]]
    pinned = compiler.pinned_tree(prof)
    masm = tc["profiles"]["masm510"]
    # Verify the assembler used to build the research hook; LINK is identified
    # by the recorded hash in output because it is not part of acceptance.
    compiler.verify_profile("masm510")
    masm_dir = Path(masm["directory"])
    link_exe = masm_dir / "LINK.EXE"
    if not link_exe.is_file():
        raise FileNotFoundError(f"MASM research environment lacks {link_exe}")

    out_root = modctx.under_build(out_root)
    out_root.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", label).strip("._") or "capture"
    work = out_root / safe
    if work.exists():
        raise FileExistsError(f"capture already exists: {work}; use a fresh label to preserve the evidence")
    work.mkdir(parents=True)
    ir_dir = work / "IR"
    ir_dir.mkdir()
    source = compiler.expand_includes(source_path.read_text(encoding="latin1"), prof)
    source = source.replace("\r\n", "\n").replace("\r", "\n")
    (work / "UNIT.C").write_bytes(source.replace("\n", "\r\n").encode("ascii"))
    shutil.copyfile(CAPTURE_ASM, work / "CAPTURE.ASM")
    # DOS mkdir is deterministic and the directory exists before C1 runs.
    bat = [
        "@echo off",
        "MD E:\\IR",
        "M:\\MASM.EXE E:\\CAPTURE.ASM,E:\\CAPTURE.OBJ,E:\\CAPTURE.LST; > E:\\MASM.LOG",
        "M:\\LINK.EXE E:\\CAPTURE.OBJ,E:\\CAPTURE.EXE,,,; > E:\\LINK.LOG",
        "D:\\BIN\\CL.EXE /c " + " ".join([*flags, "/EM", "/B2", "E:\\CAPTURE.EXE", "E:\\UNIT.C"]) + " > E:\\CL.LOG",
        "exit",
    ]
    (work / "RUN.BAT").write_bytes(("\r\n".join(bat) + "\r\n").encode("ascii"))
    (work / "dosbox.conf").write_text(_dosbox_conf(work, pinned, masm_dir, runner), encoding="ascii")
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    argv = [runner["path"], "-conf", str(work / "dosbox.conf"), "-fastlaunch", "-exit", "-nomenu"]
    proc = subprocess.run(argv, cwd=work, env=env, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, timeout=timeout,
                          creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    streams: dict[str, dict] = {}
    for p in sorted(ir_dir.iterdir()):
        if p.is_file() and re.fullmatch(r"[A-Z0-9]{6}(EX|IN|ST|SY)", p.name.upper()):
            raw = p.read_bytes()
            streams[p.name.upper()] = {"file": str(p.relative_to(work)), "size": len(raw), "sha256": sha(raw)}
    logs = {}
    for name in ("MASM.LOG", "LINK.LOG", "CL.LOG"):
        p = work / name
        if p.exists():
            logs[name] = p.read_text(encoding="latin1", errors="replace")
    result = {
        "schema": "msc600ax-c1-capture-v1",
        "label": label,
        "source": str(source_path),
        "source_sha256": sha(source_path.read_bytes()),
        "expanded_source_sha256": sha((work / "UNIT.C").read_bytes()),
        "profile": profile,
        "flags": ["/c", *flags, "/EM", "/B2", "CAPTURE.EXE"],
        "compiler_profile": "pinned msc600ax from layout/toolchain.json",
        "capture_executable": "research-only MASM logger built from tools/research/capture_ir.asm",
        "masm510_link_sha256": sha(link_exe.read_bytes()),
        "dosbox_returncode": proc.returncode,
        "dosbox_output_tail": proc.stdout.decode("latin1", "replace")[-2500:],
        "streams": streams,
        "logs": logs,
        "claim_limit": "C1 front-end inputs only; not original compiler IR, C2 IR, or target compiler state",
        "workdir": str(work),
    }
    (work / "capture.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def _load_capture(path: Path) -> tuple[dict, Path]:
    if path.is_dir():
        path = path / "capture.json"
    meta = json.loads(path.read_text(encoding="utf-8"))
    return meta, path.parent


def _diff_bytes(a: bytes, b: bytes) -> dict:
    n = min(len(a), len(b))
    diffs = [i for i in range(n) if a[i] != b[i]]
    return {
        "a_size": len(a), "b_size": len(b),
        "common_prefix": next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), n),
        "different_offsets": diffs,
        "different_count_in_common_length": len(diffs),
        "tail_a": a[n:].hex(), "tail_b": b[n:].hex(),
    }


def compare(a_path: Path, b_path: Path, out: Path | None = None) -> dict:
    a, abase = _load_capture(a_path)
    b, bbase = _load_capture(b_path)
    names = sorted(set(a["streams"]) | set(b["streams"]))
    stream_diffs = {}
    for name in names:
        if name not in a["streams"] or name not in b["streams"]:
            stream_diffs[name] = {"missing": "a" if name not in a["streams"] else "b"}
            continue
        ba = (abase / a["streams"][name]["file"]).read_bytes()
        bb = (bbase / b["streams"][name]["file"]).read_bytes()
        d = _diff_bytes(ba, bb)
        d["a_sha256"] = sha(ba)
        d["b_sha256"] = sha(bb)
        # The EX stream records the input file name twice. The matrix fixes the
        # basename to UNIT.C, so this is usually empty; report markers instead
        # of guessing which other bytes are metadata.
        markers = [b"UNIT.C", b"UNIT.c"]
        d["recognized_source_name_markers"] = {
            marker.decode("ascii"): {"a": [m.start() for m in re.finditer(re.escape(marker), ba)],
                                      "b": [m.start() for m in re.finditer(re.escape(marker), bb)]}
            for marker in markers if marker in ba or marker in bb
        }
        stream_diffs[name] = d
    report = {
        "schema": "msc600ax-c1-compare-v1",
        "a": a.get("label"), "b": b.get("label"),
        "same_source_bytes": a.get("source_sha256") == b.get("source_sha256"),
        "streams": stream_diffs,
        "normalization": "No opaque EX/IN/ST/SY bytes were normalized. Only source-name marker offsets are identified. Review raw differences before attributing a byte to syntax, source metadata, or debug metadata.",
        "interpretation_limit": "These are C1 front-end temporary streams from a diagnostic compile, not the original compiler's retained IR or the original source's compiler state.",
    }
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def capture_summary(r: dict) -> dict:
    return {"label": r["label"], "workdir": r["workdir"],
            "streams": {n: s["size"] for n, s in r["streams"].items()},
            "cl_result": r["logs"].get("CL.LOG", "").strip().splitlines()[-1:]}


def compare_summary(r: dict) -> dict:
    return {"a": r["a"], "b": r["b"], "same_source_bytes": r["same_source_bytes"],
            "streams": {n: ({"missing": v["missing"]} if "missing" in v else
                            {"a_size": v["a_size"], "b_size": v["b_size"],
                             "different_offsets": v["different_count_in_common_length"],
                             "common_prefix": v["common_prefix"],
                             "tail_a_bytes": len(v["tail_a"]) // 2,
                             "tail_b_bytes": len(v["tail_b"]) // 2})
                        for n, v in r["streams"].items()},
            "full_report": str(r.get("_out")) if r.get("_out") else None}


def inspect_id_fields(a_path: Path, b_path: Path, out: Path | None = None,
                      source_path: Path | None = None) -> dict:
    """Conservatively inspect probe-confirmed EX identity operands.

    Tiny same-line controls show that EX sequences 26/29/3A followed by a
    little-endian 16-bit value behave as identifier references/declarations:
    adding one prior extern increments them, while renaming a referenced
    extern changes SY but leaves EX untouched. This routine scans aligned
    bytes only. It is a hypothesis report, not a general EX parser.
    """
    a, abase = _load_capture(a_path)
    b, bbase = _load_capture(b_path)
    aname, bname = "000352EX", "000352EX"
    if aname not in a["streams"] or bname not in b["streams"]:
        raise ValueError("both captures must contain 000352EX")
    aa = (abase / a["streams"][aname]["file"]).read_bytes()
    bb = (bbase / b["streams"][bname]["file"]).read_bytes()
    raw_diffs = [i for i, (x, y) in enumerate(zip(aa, bb)) if x != y]
    markers = {0x26: "0x26", 0x29: "0x29", 0x3A: "0x3a"}
    fields = []
    overlapping = []
    covered: set[int] = set()
    for pos in range(min(len(aa), len(bb)) - 2):
        op = aa[pos]
        if op not in markers or bb[pos] != op:
            continue
        # If the first operand byte is itself a probe-confirmed prefix, the
        # outer interpretation is ambiguous. Keep the nested candidate and
        # record the overlap instead of guessing which prefix owns the bytes.
        if aa[pos + 1] in markers and bb[pos + 1] == aa[pos + 1]:
            overlapping.append({"offset": pos, "outer_marker": markers[op],
                                "next_marker": markers[aa[pos + 1]],
                                "outer_values": [aa[pos + 1] | aa[pos + 2] << 8,
                                                 bb[pos + 1] | bb[pos + 2] << 8]})
            continue
        old = aa[pos + 1] | (aa[pos + 2] << 8)
        new = bb[pos + 1] | (bb[pos + 2] << 8)
        if old == new:
            continue
        changed_bytes = [i for i in (pos + 1, pos + 2) if aa[i] != bb[i]]
        covered.update(changed_bytes)
        fields.append({"offset": pos, "marker": markers[op], "a_value": old,
                       "b_value": new, "delta": new - old,
                       "changed_value_offsets": changed_bytes,
                       "status": "heuristic-large-stream-candidate; local pattern only"})
    diff_set = set(raw_diffs)
    context_rows = []
    line_method = None
    if source_path:
        source_path = source_path.resolve()
        source_lines = source_path.read_text(encoding="latin1").splitlines()
        sy_raw = (abase / a["streams"]["000352SY"]["file"]).read_bytes()
        sy_spellings = {m.group().decode("latin1") for m in
                        re.finditer(rb"[A-Za-z_][A-Za-z0-9_.$@]*", sy_raw)
                        if len(m.group()) > 1}
        line_markers = []
        pos = 0
        while pos + 2 < len(aa):
            if aa[pos:pos + 2] == b"\x4f\x01":
                if aa[pos + 2] == 0x80 and pos + 4 < len(aa):
                    line_no, width = aa[pos + 3] | (aa[pos + 4] << 8), 5
                else:
                    line_no, width = aa[pos + 2], 3
                line_markers.append((pos, line_no))
                pos += width
            else:
                pos += 1
        marker_positions = [x[0] for x in line_markers]
        for offset in sorted(diff_set - covered):
            at = bisect.bisect_right(marker_positions, offset) - 1
            line_no = line_markers[at][1] if at >= 0 else None
            line_text = source_lines[line_no - 1].strip() if line_no and line_no <= len(source_lines) else None
            identifiers = sorted(set(re.findall(r"[A-Za-z_][A-Za-z0-9_.$@]*", line_text or "")) & sy_spellings)
            control_context = None
            if line_no:
                for prior in range(min(line_no, len(source_lines)), max(0, line_no - 33), -1):
                    text = source_lines[prior - 1].strip()
                    if re.search(r"\b(if|for|while|switch|case|goto)\b", text):
                        names = sorted(set(re.findall(r"[A-Za-z_][A-Za-z0-9_.$@]*", text)) & sy_spellings)
                        control_context = {"line": prior, "source": text, "SY_spellings": names}
                        break
            context_rows.append({
                "offset": offset,
                "a_window": aa[max(0, offset - 5):offset + 6].hex(" "),
                "b_window": bb[max(0, offset - 5):offset + 6].hex(" "),
                "preceding_line_marker": line_no,
                "source_line": line_text,
                "SY_spellings_on_source_line": identifiers,
                "nearest_control_context": control_context,
                "interpretation": "unclassified byte; source line is contextual only, and SY overlap does not prove this byte belongs to a named symbol",
            })
        line_method = "4F 01 followed by a one-byte line number, or 80 + little-endian 16-bit line number; spot-checked against S15 statement text. Used only to attach source context."
    report = {
        "schema": "msc600ax-ex-identity-probe-v1",
        "a": a.get("label"), "b": b.get("label"),
        "ex_sizes": [len(aa), len(bb)],
        "raw_differing_offsets": len(raw_diffs),
        "candidate_marker_fields": fields,
        "ambiguous_overlapping_marker_interpretations": overlapping,
        "marker_field_value_delta_counts": {
            str(delta): sum(1 for f in fields if f["delta"] == delta)
            for delta in sorted({f["delta"] for f in fields})
        },
        "raw_diff_bytes_covered_by_marker_fields": len(diff_set & covered),
        "unclassified_raw_diff_offsets": sorted(diff_set - covered),
        "unclassified_count": len(diff_set - covered),
        "unclassified_contexts": context_rows,
        "source_context_method": line_method,
        "method_limit": "Tiny controls confirm local 26/29/3A + little-endian-16 patterns. Fields scanned in a large EX stream are heuristic candidates, not parsed fields. Overlapping prefixes are explicitly left ambiguous. No bytes are normalized.",
    }
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    pcap = sub.add_parser("capture", help="capture C1 EX/IN/ST/SY for one source")
    pcap.add_argument("source", type=Path)
    pcap.add_argument("--label", default="capture")
    pcap.add_argument("--out", type=Path, default=ROOT / "build" / "workers" / "compiler_ir")
    pcap.add_argument("--profile", default=AX_PROFILE)
    pcap.add_argument("--flags", nargs="*", default=["/AL", "/Os"])
    pm = sub.add_parser("matrix", help="run a JSON list of {label, source} captures")
    pm.add_argument("manifest", type=Path)
    pm.add_argument("--out", type=Path, default=ROOT / "build" / "workers" / "compiler_ir")
    pc = sub.add_parser("compare", help="compare two capture directories")
    pc.add_argument("a", type=Path)
    pc.add_argument("b", type=Path)
    pc.add_argument("--out", type=Path)
    pid = sub.add_parser("inspect-ids", help="inspect probe-confirmed EX identity operand fields")
    pid.add_argument("a", type=Path)
    pid.add_argument("b", type=Path)
    pid.add_argument("--out", type=Path)
    pid.add_argument("--source", type=Path, help="candidate C source for contextual line mapping")
    args = ap.parse_args()
    if args.command == "capture":
        print(json.dumps(capture_summary(capture(args.source, args.label, args.out, args.profile, args.flags)), indent=2))
    elif args.command == "matrix":
        spec = json.loads(args.manifest.read_text(encoding="utf-8"))
        results = []
        for case in spec["cases"]:
            src = Path(case["source"])
            if not src.is_absolute():
                src = (args.manifest.parent / src).resolve()
            results.append(capture(src, case["label"], args.out, case.get("profile", AX_PROFILE), case.get("flags")))
        print(json.dumps({"captures": [capture_summary(r) for r in results]}, indent=2))
    elif args.command == "compare":
        report = compare(args.a, args.b, args.out)
        if args.out:
            report["_out"] = str(args.out)
        print(json.dumps(compare_summary(report), indent=2))
    else:
        report = inspect_id_fields(args.a, args.b, args.out, args.source)
        print(json.dumps({k: v for k, v in report.items() if k not in
                          ("candidate_marker_fields", "unclassified_contexts")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
