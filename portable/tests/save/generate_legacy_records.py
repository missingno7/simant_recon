"""Emit or verify the C row schema from the pinned source-derived inventory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
INVENTORY = ROOT / "portable/tests/dialogs/evidence/savegame-format-source-inventory-v1/save-records.json"
OUTPUT = ROOT / "portable/game/save/legacy_records.inc"


def expected_text() -> str:
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    lines = []
    offset = 0
    for index, record in enumerate(inventory["table"]["records"]):
        if record["index"] != index:
            raise ValueError(f"record index gap at {index}")
        expression = record["pointer_expression"].replace("\\", "\\\\").replace('"', '\\"')
        lines.append(
            f'    {{{index}u, {record["element_size"]}u, {record["element_count"]}u, '
            f'{offset}u, "{expression}"}},'
        )
        offset += record["serialized_bytes"]
    if offset != 48386 or len(lines) != 307:
        raise ValueError(f"unexpected schema dimensions: {len(lines)} rows, {offset} bytes")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = expected_text()
    if args.check:
        actual = OUTPUT.read_text(encoding="utf-8")
        if actual != expected:
            raise SystemExit("legacy_records.inc differs from source-derived inventory")
        print("legacy_record_schema=PASS rows=307 bytes=48386")
    else:
        OUTPUT.write_text(expected, encoding="utf-8")
        print(f"wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
