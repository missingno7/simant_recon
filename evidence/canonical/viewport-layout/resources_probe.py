"""Observe selected current resource geometry; emit metadata only under build.

Importing this module performs no writes. Selected packed geometry is refused:
the conditional HCEGANT profile-0/profile-8 packet covers plain records only.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys

sys.dont_write_bytecode = True


def find_root():
    for parent in Path(__file__).resolve().parents:
        if (parent / "src/program.json").is_file() and (parent / "tools/context.py").is_file():
            return parent
    raise RuntimeError("cannot locate repository containing src/program.json and tools/context.py")


def fresh_output(root, requested):
    output = Path(requested)
    if not output.is_absolute():
        output = root / output
    output = output.resolve()
    build = (root / "build").resolve()
    if output == build or not output.is_relative_to(build):
        raise ValueError("--out must name a fresh directory strictly beneath the repository build/")
    if output.exists() or output.is_symlink():
        raise ValueError("--out already exists; choose a fresh directory")
    output.mkdir(parents=True, exist_ok=False)
    return output


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def index_rows(root, stem):
    index = (root / "assets" / (stem + ".NDX")).read_bytes()
    count = struct.unpack_from("<H", index)[0]
    if 20 + count * 8 > len(index):
        raise ValueError(stem + ": truncated resource index")
    return [struct.unpack_from("<IHBB", index, 20 + i * 8) for i in range(count)]


def plain_payload(root, stem, row):
    offset, ident, kind, flags = row
    if flags & 1:
        raise ValueError(f"{stem}:{ident}:{kind}: selected geometry is packed; outside this packet")
    data = (root / "assets" / (stem + ".DAT")).read_bytes()
    size = struct.unpack_from("<H", data, offset + 20)[0]
    if offset + 24 + size > len(data):
        raise ValueError(f"{stem}:{ident}:{kind}: truncated payload")
    return data[offset + 24:offset + 24 + size]


def resource_payload(root, ident, kind, stem="HCEGANT"):
    found = [row for row in index_rows(root, stem) if row[1:3] == (ident, kind)]
    if len(found) != 1:
        raise ValueError(f"{stem}:{ident}:{kind}: expected one record, found {len(found)}")
    return plain_payload(root, stem, found[0])


def obj_fields(payload, number):
    # RepointObjects starts after the fixed header plus DOS far pointer table.
    count = struct.unpack_from("<h", payload, 0xC)[0]
    at = 0x2C + 4 * count
    for _ in range(number):
        at += struct.unpack_from("<h", payload, at + 0x22)[0]
    return dict(offset=at, rect=struct.unpack_from("<4h", payload, at),
                origin=struct.unpack_from("<4h", payload, at + 8),
                refs=struct.unpack_from("<4h", payload, at + 0x10),
                modes=struct.unpack_from("<4h", payload, at + 0x18),
                type=payload[at + 0x21], flags=struct.unpack_from("<H", payload, at + 0x24)[0],
                border_byte28=payload[at + 0x28])


def collect_report(root):
    report = {"schema": "viewport-layout-resource-observation-v1",
              "scope": "Current HCEGANT and SHARED root, profile-0/profile-8 offsets and control bitmap geometry; selected plain records only.",
              "assets": {}, "resource_matches": {}, "record_counts": {}}
    for stem in ("HCEGANT", "SHARED"):
        for extension in (".DAT", ".NDX"):
            name = stem + extension
            raw = (root / "assets" / name).read_bytes()
            report["assets"][name] = {"size": len(raw), "sha256": sha(raw)}
        rows = index_rows(root, stem)
        report["record_counts"][stem] = len(rows)
        for row in rows:
            offset, ident, kind, flags = row
            selected = (kind == 9 and ident in range(9)) or (ident == 0 and kind == 0) or (ident in (0x70, 0x6F) and kind == 2)
            if not selected:
                continue
            payload = plain_payload(root, stem, row)
            key = f"{stem}:{ident}:{kind}"
            if key in report["resource_matches"]:
                raise ValueError(key + ": duplicate selected record")
            fields = dict(record_offset=offset, flags=flags, size=len(payload))
            if kind == 9:
                fields.update(root_origin=struct.unpack_from("<4h", payload),
                              signed_fields=list(struct.unpack_from("<4h", payload)))
            elif kind == 0:
                fields.update(window_flags=struct.unpack_from("<H", payload, 0x1C)[0],
                              min_size=struct.unpack_from("<2h", payload, 0x18),
                              grid=struct.unpack_from("<2h", payload, 0x20),
                              objects={str(i): obj_fields(payload, i) for i in (0, 1, 3, 4)})
            else:
                fields.update(first_words=list(struct.unpack_from("<8h", payload)))
            report["resource_matches"][key] = fields
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="fresh directory beneath repository build/; relative paths use the repository root")
    args = parser.parse_args()
    root = find_root()
    try:
        output = fresh_output(root, args.out)
    except ValueError as exc:
        parser.error(str(exc))
    report = collect_report(root)
    report["probe_sha256"] = sha(Path(__file__).read_bytes())
    destination = output / "resource-observation.json"
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"records_observed": len(report["resource_matches"]), "observation": str(destination)}))


if __name__ == "__main__":
    main()
