"""Generate bounded, listing-grounded pointer-form variants for f_20E8_0903."""
from __future__ import annotations

import hashlib
import itertools
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WORKER = ROOT / "build" / "workers" / "ptr_small"
SEED = WORKER / "seed.c"
OUT = WORKER / "variants"
TARGET = re.compile(
    r"void _fastcall f_20E8_0903\(int obj, int far \*rect\)\n\{.*?\n\}",
    re.S,
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    seed_bytes = SEED.read_bytes()
    source = seed_bytes.decode("latin1")
    match = TARGET.search(source)
    if not match:
        raise SystemExit("target definition not found in frozen seed")
    body = match.group(0)
    OUT.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []

    def save(name: str, changed: str, hypothesis: str) -> None:
        if changed == body:
            raise SystemExit(f"empty generated variant: {name}")
        path = OUT / f"{name}.c"
        full_source = source[: match.start()] + changed + source[match.end() :]
        content = full_source.encode("latin1")
        path.write_bytes(content)
        normalized = path.read_text(encoding="latin1").encode("latin1")
        rows.append({
            "name": name,
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "hypothesis": hypothesis,
            "source_sha256_file_bytes": sha(content),
            "source_sha256_search_text": sha(normalized),
        })

    # The listing shows three successive far-pointer base additions from o,
    # followed by indexed accesses through those same pointers.
    base_forms = {
        "origin": ("origin = o + 4;", "origin = &o[4];"),
        "mode": ("mode = o + 12;", "mode = &o[12];"),
        "ref": ("ref = o + 8;", "ref = &o[8];"),
    }
    for mask in range(1, 1 << len(base_forms)):
        changed = body
        selected: list[str] = []
        for bit, name in enumerate(base_forms):
            if mask & (1 << bit):
                old, new = base_forms[name]
                if changed.count(old) != 1:
                    raise SystemExit(f"expected one {old!r}")
                changed = changed.replace(old, new, 1)
                selected.append(name)
        save(
            "base_addr_" + "_".join(selected),
            changed,
            "Replace selected constant pointer additions (o + field-index) with the equivalent address-of-index form (&o[field-index]); retain original assignment order.",
        )

    # Test the lvalue/rvalue forms as a complete factorial across the five
    # pointer variables which the listing indexes in the three loops.
    indexed = ("origin", "mode", "ref", "o", "rect")
    for mask in range(1, 1 << len(indexed)):
        changed = body
        selected = []
        for bit, name in enumerate(indexed):
            if not mask & (1 << bit):
                continue
            pattern = re.compile(rf"\b{re.escape(name)}\[(i|j)\]")
            changed, count = pattern.subn(lambda m: f"*({name} + {m.group(1)})", changed)
            if not count:
                raise SystemExit(f"no indexed accesses found for {name}")
            selected.append(name)
        save(
            "index_ptradd_" + "_".join(selected),
            changed,
            "Replace selected indexed far-pointer accesses p[i]/p[j] with equivalent dereferenced pointer additions *(p + i)/ *(p + j); retain statements and evaluation structure.",
        )

    # The target explicitly moves the scaled loop index between registers
    # while loading rect and o. Compare the C additive operand order in each
    # subtraction operand independently.
    for name, old, new in (
        ("rhs_rect_index_first", "rect[i] - o[i]", "*(i + rect) - o[i]"),
        ("rhs_o_index_first", "rect[i] - o[i]", "rect[i] - *(i + o)"),
    ):
        changed = body
        if changed.count(old) != 2:
            raise SystemExit(f"expected two RHS occurrences for {name}")
        changed = changed.replace(old, new)
        save(
            name,
            changed,
            "Change only the additive operand order for one far-pointer subscript in both existing rect[i] - o[i] expressions; values and store order are unchanged.",
        )

    if len(rows) != 40:
        raise SystemExit(f"expected 40 variants, generated {len(rows)}")
    report = {
        "target": "f_20E8_0903",
        "module": "root:20E8",
        "seed": "build/workers/ptr_small/seed.c",
        "seed_sha256_file_bytes": sha(seed_bytes),
        "seed_sha256_search_text": sha(SEED.read_text(encoding="latin1").encode("latin1")),
        "source_basis": "frozen whole-module source at work/takeover/full-search/f_20E8_0903/best.c; target listing from python tools/context.py f_20E8_0903",
        "limits": {"max_new_variants": 40, "generated": len(rows)},
        "variants": rows,
    }
    (WORKER / "generated.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"generated {len(rows)} whole-module variants")
    print(f"seed sha256 (compile text): {report['seed_sha256_search_text']}")


if __name__ == "__main__":
    main()
