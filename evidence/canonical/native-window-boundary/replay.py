"""Replay current window resource/helper controls; write outputs only to build/.

After installation:
  python evidence/canonical/native-window-boundary/replay.py --out build/window-boundary-current

Requires local pinned game assets and a C11 compiler. No draft checkout,
archived executable, scratch receipt generator, or cached generated C is read.
The controls corroborate resource/representation checks, not whole-game parity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess


HERE = Path(__file__).resolve().parent


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalized(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


def find_root() -> Path:
    for candidate in HERE.parents:
        if (candidate / "src/program.json").is_file() and \
                (candidate / "portable/build.py").is_file():
            return candidate
    raise ValueError("repository root not found; use --root")


def parse_resources(root: Path) -> tuple[dict, dict]:
    rows = []
    offsets = {}
    ndxs = sorted((root / "assets").glob("*.NDX"))
    if not ndxs:
        raise ValueError("local database assets are missing")
    for ndx in ndxs:
        idx = ndx.read_bytes()
        data = ndx.with_suffix(".DAT").read_bytes()
        for row in range(struct.unpack_from("<H", idx, 0)[0]):
            offset, ident, kind, flags = struct.unpack_from("<IhBB", idx, 20 + row * 8)
            if kind != 0 or not 0 <= ident <= 40 or not flags & 8:
                continue
            header = 14 + offset
            size = struct.unpack_from("<H", data, header + 6)[0]
            wire = data[header + 10:header + 10 + size]
            if len(wire) != size or size < 0x2c:
                raise ValueError("truncated window resource")
            count = struct.unpack_from("<H", wire, 0x0c)[0]
            cursor = 0x2c + 4 * count
            if cursor > size:
                raise ValueError("truncated serialized object table")
            objects = []
            mode5 = []
            for i in range(count):
                if cursor + 0x24 > size:
                    raise ValueError("truncated object header")
                extent = struct.unpack_from("<h", wire, cursor + 0x22)[0]
                if extent < 0x28 or cursor + extent > size:
                    raise ValueError("invalid sequential object extent")
                modes = struct.unpack_from("<4h", wire, cursor + 0x18)
                refs = struct.unpack_from("<4h", wire, cursor + 0x10)
                for axis, (mode, ref) in enumerate(zip(modes, refs)):
                    if mode == 5:
                        mode5.append(dict(object=i, axis=axis, parameter=ref))
                objects.append(dict(index=i, offset=cursor, size=extent,
                    type=wire[cursor + 0x21], modes=list(modes), refs=list(refs)))
                cursor += extent
            key = (ndx.stem, ident)
            if key in offsets:
                raise ValueError("multiple active window resource rows")
            offsets[key] = header + 10
            rows.append(dict(database=ndx.stem, resource_id=ident, flags=flags,
                window_flags=struct.unpack_from("<H", wire, 0x1c)[0], size=size,
                count=count, initial_parameters=list(struct.unpack_from("<4h", wire, 0x10)),
                mode5=mode5, objects=objects, payload_sha256=sha(wire)))
    result = dict(scope="All active kind-0 window records, IDs 0..40, in all local .NDX/.DAT pairs",
        assets={p.name:sha(p.read_bytes()) for p in sorted((root / "assets").glob("*"))
                if p.suffix in {".NDX", ".DAT"}}, resources=rows)
    return result, offsets


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--out", type=Path, default=Path("build/window-boundary-current"))
    parser.add_argument("--cc", default=shutil.which("gcc") or "C:/msys64/mingw64/bin/gcc.exe")
    args = parser.parse_args()
    root = (args.root or find_root()).resolve()
    out = (args.out if args.out.is_absolute() else root / args.out).resolve()
    if not out.is_relative_to((root / "build").resolve()):
        raise ValueError("replay outputs must remain inside repository build/")
    if out.exists():
        raise ValueError("fresh build output directory required")
    out.mkdir(parents=True)
    correspondence = json.loads((HERE / "installed-correspondence.json").read_text())
    sources = {}
    for row in correspondence["installed_files"]:
        path = root / row["installed_path"]
        raw = path.read_bytes()
        actual = sha(raw)
        normalized_sha = sha(raw if row["comparison_mode"] == "binary_exact" else normalized(raw))
        if normalized_sha != row["installed_lf_sha256"]:
            raise ValueError(f"reviewed installed source changed: {row['installed_path']}")
        sources[row["installed_path"]] = dict(sha256=actual, lf_sha256=normalized_sha)
    current_resources, offsets = parse_resources(root)
    (out / "resources.json").write_text(json.dumps(current_resources, indent=2) + "\n")
    if current_resources != json.loads((HERE / "resources.json").read_text()):
        raise ValueError("asset/resource domain differs from reviewed shipped records")
    cc = shutil.which(args.cc) or args.cc
    control = HERE / "resource_helper_control.c"
    exe = out / "resource-helper-control.exe"
    command = [cc, "-std=c11", "-O0", "-Wall", "-Wextra", "-Wconversion", "-Werror",
        "-I" + str(root / "portable/whole_program"), str(control),
        str(root / "portable/whole_program/window_refs.c"),
        str(root / "portable/whole_program/window_parameters.c"), "-o", str(exe)]
    compiled = subprocess.run(command, cwd=root, capture_output=True, text=True)
    (out / "compile.txt").write_text(compiled.stdout + compiled.stderr)
    compiled.check_returncode()
    controls = []
    for record in current_resources["resources"]:
        database = record["database"]
        ident = record["resource_id"]
        count = max([axis["parameter"] + 1 for axis in record["mode5"]] + [0])
        if count not in (0, 2, 4):
            raise ValueError("shipped supplied-count domain changed")
        run = subprocess.run([str(exe), str(root / "assets" / f"{database}.DAT"),
            str(offsets[(database, ident)]), str(record["size"]), str(ident), str(count)],
            cwd=root, capture_output=True, text=True)
        controls.append(dict(database=database, resource=ident, supplied_count=count,
            exit_code=run.returncode, stdout=run.stdout, stderr=run.stderr))
        run.check_returncode()
    report = dict(schema="canonical-native-window-boundary-current-replay-v1", status="PASS",
        current_sources=sources, current_resources_sha256=sha((out / "resources.json").read_bytes()),
        controls=controls, compile_command=command, compiler_sha256=sha(Path(cc).read_bytes()),
        control_source_sha256=sha(control.read_bytes()), executable_sha256=sha(exe.read_bytes()),
        controls_scope="Actual 34 shipped records: required 0/2/4 count succeeds; missing coordinates and count=1 reject before any write; successful four int16 words preserve values/order.",
        nonclaim="No original DOS execution differential, complete native-game parity, raw-state equivalence, or arbitrary resource/window-stack domain claim.")
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(dict(status="PASS", resources=len(controls), report=str(out / "report.json"))))


if __name__ == "__main__":
    main()
