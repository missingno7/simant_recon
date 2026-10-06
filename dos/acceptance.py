"""Original-vs-reconstructed DOS acceptance at saved-game state boundaries.

Runs one scenario (dos/scenarios/*.json naming an emulated-time input script)
under the pinned acceptance DOSBox-X with fixed cycles and a fixed guest
clock, for the original oracle and for a reconstructed executable, then
compares every saved game byte for byte, reporting differing records by the
canonical S09 SaveRec schema. Input arrives at identical emulated times, so
any difference, including timer-derived fields, is a behavioural difference.

A PASS is a bounded observation for the recorded scenario; it is not closure
by itself and grants no acceptance outside that scenario.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dos import build, diagnostic


def save_schema():
    """(index, offset, bytes, element size, name) from the canonical SaveRec table."""
    text = (ROOT / "src/S09/m35F5.c").read_text(encoding="latin1")
    start = re.search(r"struct SaveRec far fd_4E4B_0000\[\d+\] = \{", text).start()
    body = text[start:text.index("};", start)]
    rows, offset = [], 0
    for index, (size, count, data) in enumerate(
            re.findall(r"\{\s*([^,{}]+),\s*([^,{}]+),\s*([^{}]+?)\s*\}", body)):
        size, count = int(size, 0), int(count, 0)
        if count == 0:
            break
        name = re.sub(r"\(void far \*\)\s*&?", "", data).strip()
        rows.append((index, offset, size * count, size, name))
        offset += size * count
    return rows


def compare_saves(a: bytes, b: bytes) -> dict:
    schema = save_schema()
    total = schema[-1][1] + schema[-1][2]
    if len(a) != total or len(b) != total:
        return {"status": "SIZE_MISMATCH", "sizes": [len(a), len(b)], "schema_bytes": total}
    differences = []
    for index, offset, size, _, name in schema:
        x, y = a[offset:offset + size], b[offset:offset + size]
        if x != y:
            differences.append({"record": index, "name": name, "bytes": size,
                                "differing_bytes": sum(p != q for p, q in zip(x, y))})
    return {"status": "EQUAL" if not differences else "DIFFERS",
            "records": len(schema), "differences": differences}


# Sound Mode 6 hardware: Sound Blaster DSP ports and the AdLib/OPL ports (the game
# also plays digitized samples by modulating OPL output levels).
SOUND_PORTS = {"sb_dsp": ("220", "22F"), "opl": ("388", "38B")}


def port_writes(path: Path) -> list[tuple[float, str, str]]:
    """(emulated ms, port, value) for every logged OUT."""
    rows = []
    for line in path.read_text().splitlines():
        parts = line.split()
        if len(parts) >= 5 and parts[1] == "out":
            rows.append((float(parts[0]), parts[2], parts[4]))
    return rows


def compare_ports(a: list, b: list) -> dict:
    equal = [r[1:] for r in a] == [r[1:] for r in b]
    deltas = [abs(y[0] - x[0]) for x, y in zip(a, b)]
    return {"status": "EQUAL" if equal else "DIFFERS", "writes": [len(a), len(b)],
            "max_timing_delta_ms": round(max(deltas), 6) if deltas else 0.0}


SCREEN_CLIP_PATTERN = bytes.fromhex("000000008002e0010080008000800080")  # g_5A9C at runtime (VGA)
DUMP_BYTES = 0xA0000


def scripted_input(scenario: dict, out: Path) -> Path:
    """The scenario script, plus a conventional-memory dump at each checkpoint."""
    lines = [line for line in (ROOT / scenario["script"]).read_text().splitlines()
             if line.strip() and not line.lstrip().startswith("#")]
    lines += [f"{ms} dump 0 {DUMP_BYTES:X} cp{ms}" for ms in scenario.get("checkpoints", [])]
    if scenario.get("sound"):
        lines += [f"0 io_watch {lo} {hi} {name} out" for name, (lo, hi) in SOUND_PORTS.items()]
    lines.sort(key=lambda line: int(line.split()[0]))
    path = out.parent / (out.name + ".scr")
    path.write_text("\n".join(lines) + "\n")
    return path


def record_addresses(map_path: Path | None) -> dict:
    """Image-relative linear address of every SaveRec owner symbol."""
    if map_path is None:
        data = json.loads((ROOT / "layout/symbols.json").read_text())["data"]
        return {name: row["seg"] * 16 + row["off"] for name, row in data.items()}
    out = {}
    for line in map_path.read_text(encoding="latin1").splitlines():
        m = re.match(r"\s*([0-9A-F]{4}):([0-9A-F]{4})\s+Res\s+_(\w+)", line)
        if m:
            out.setdefault(m.group(3), int(m.group(1), 16) * 16 + int(m.group(2), 16))
    return out


def virtual_save(memory: bytes, addresses: dict) -> bytes:
    """Assemble the 307 SaveRec records from a memory image, as SaveGame would write them."""
    hits = [m.start() for m in re.finditer(re.escape(SCREEN_CLIP_PATTERN), memory)]
    bases = {h - addresses["g_5A9C"] for h in hits}
    if len(bases) != 1:
        raise ValueError(f"runtime load base not unique: {sorted(bases)}")
    base = bases.pop()
    parts = []
    for _, _, size, _, name in save_schema():
        m = re.fullmatch(r"\((\w+) \+ (\d+)\)", name)
        symbol, extra = (m.group(1), int(m.group(2))) if m else (name, 0)
        start = base + addresses[symbol] + extra
        parts.append(memory[start:start + size])
    return b"".join(parts)


def run_once(scenario: dict, out: Path, build_report: Path | None) -> dict:
    command = [sys.executable, str(ROOT / "dos/run.py"), "--out", str(out),
               "--seconds", str(scenario["host_seconds"]), "--fixed-clock",
               "--input-script", str(scripted_input(scenario, out))]
    command += ["--original"] if build_report is None else ["--build-report", str(build_report)]
    if scenario.get("saved_game"):
        command += ["--saved-game", str(ROOT / scenario["saved_game"])]
    subprocess.run(command, cwd=ROOT, check=True, stdout=subprocess.DEVNULL,
                   timeout=scenario["host_seconds"] + 180)
    report = json.loads((out / "execution-report.json").read_text())
    map_path = None
    if build_report is not None:
        receipt = json.loads(Path(build_report).read_text())
        map_path = (ROOT / receipt["link"]["candidate_executable"]["path"]).with_name("SOURCE.MAP")
    addresses = record_addresses(map_path)
    checkpoints = {}
    for ms in scenario.get("checkpoints", []):
        dump = out / f"dump-cp{ms}"
        checkpoints[f"cp{ms}"] = virtual_save(dump.read_bytes(), addresses) if dump.is_file() else None
        if dump.is_file():
            dump.unlink()  # 640 KiB per checkpoint; only the virtual save is retained in memory
    sound = {name: port_writes(out / f"io-{name}") for name in SOUND_PORTS
             if scenario.get("sound") and (out / f"io-{name}").is_file()}
    return {"report": report, "map": map_path, "sound": sound,
            "saves": {name: (out / name).read_bytes() if (out / name).is_file() else None
                      for name in scenario["saves"]},
            "checkpoints": checkpoints}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", type=Path)
    parser.add_argument("--build-report", type=Path, required=True,
                        help="reconstructed executable receipt accepted by dos/run.py")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    scenario = json.loads(args.scenario.read_text())
    out = diagnostic.experimental_path(args.out)
    build.prepare_output(out, ROOT / "build/current/dos-acceptance")
    runs = {"original": run_once(scenario, out / "original", None),
            "reconstructed": run_once(scenario, out / "reconstructed", args.build_report)}
    result = {"schema": "simant-dos-acceptance-v2", "scenario": scenario,
              "scenario_sha256": build.digest(args.scenario.read_bytes()),
              "script_sha256": build.digest((ROOT / scenario["script"]).read_bytes()),
              "closure_eligible": False, "runs": {}, "saves": {}}
    passed = True
    for label, run in runs.items():
        report = run["report"]
        faults = report.get("runtime_faults", {}).get("count")
        result["runs"][label] = {"status": report.get("status"), "runner": report.get("runner"),
                                 "runtime_faults": faults,
                                 "executable": next((p for p in report.get("inputs", [])
                                                     if str(p.get("path", "")).upper().endswith(".EXE")
                                                     and "INSTALL" not in str(p.get("path", "")).upper()), None)}
        passed &= report.get("status") == "EMULATOR_EXITED" and not faults
    comparisons = [(name, runs["original"]["saves"][name], runs["reconstructed"]["saves"][name])
                   for name in scenario["saves"]]
    comparisons += [(name, runs["original"]["checkpoints"][name], runs["reconstructed"]["checkpoints"][name])
                    for name in runs["original"]["checkpoints"]]
    if runs["reconstructed"]["map"] is not None:
        result["reconstructed_map_sha256"] = build.digest(runs["reconstructed"]["map"].read_bytes())
    if scenario.get("sound"):
        result["sound"] = {}
        for name in SOUND_PORTS:
            a, b = runs["original"]["sound"].get(name), runs["reconstructed"]["sound"].get(name)
            row = compare_ports(a, b) if a is not None and b is not None else {"status": "MISSING"}
            result["sound"][name] = row
            passed &= row["status"] == "EQUAL"
    for name, x, y in comparisons:
        if x is None or y is None:
            result["saves"][name] = {"status": "MISSING", "present": [x is not None, y is not None]}
            passed = False
            continue
        row = compare_saves(x, y)
        row["sha256"] = [build.digest(x), build.digest(y)]
        result["saves"][name] = row
        passed &= row["status"] == "EQUAL"
    result["status"] = "PASS" if passed else "FAIL"
    (out / "acceptance.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "out": str(out / "acceptance.json"),
                      "sound": result.get("sound"),
                      "saves": {k: (v["status"], [d["name"] for d in v.get("differences", [])][:10])
                                for k, v in result["saves"].items()}}, indent=1))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
