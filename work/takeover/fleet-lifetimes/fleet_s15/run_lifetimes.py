"""Bounded S15 call-argument lifetime sweep; writes only below this worker."""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
import csrc
import modctx
import variants

NAME = "o15_384C_0239"
BASE_PATH = OUT / "s15-base.c"
BASE = BASE_PATH.read_text(encoding="latin1")
CTX = modctx.resolve(func=NAME, source=BASE_PATH)
FN = csrc.Source(BASE).function(NAME)
BODY = BASE[FN.body.s:FN.body.e]
VARIANTS: list[tuple[str, str, dict]] = []


def put_local(label: str, typename: str, init: str, use_edits: list[tuple[str, str]],
              insert_before: str, meta: dict) -> None:
    body = BODY
    body = body.replace("    int result;\n", f"    int result;\n    {typename} {label};\n", 1)
    for old, new in use_edits:
        if old not in body:
            raise RuntimeError(f"missing call-argument anchor: {old}")
        body = body.replace(old, new, 1)
    if insert_before not in body and insert_before.startswith("    win_PrintTextInRect(0,"):
        insert_before = insert_before.replace("win_PrintTextInRect(0,", "win_PrintTextInRect(draw,", 1)
    if insert_before not in body:
        raise RuntimeError(f"missing initialization anchor: {insert_before}")
    body = body.replace(insert_before, f"    {label} = {init};\n" + insert_before, 1)
    text = BASE[:FN.body.s] + body + BASE[FN.body.e:]
    VARIANTS.append((meta["name"], text, meta))


def put_id_local(label: str, value: str, edits: list[tuple[str, str]],
                 insert_before: str, meta: dict) -> None:
    body = BODY.replace("    int result;\n", f"    int result;\n    int {label};\n", 1)
    for old, new in edits:
        if old not in body:
            raise RuntimeError(f"missing ID call-argument anchor: {old}")
        body = body.replace(old, new, 1)
    if insert_before not in body and insert_before.startswith("    win_Open(0x2100);"):
        insert_before = insert_before.replace("win_Open(0x2100);", "win_Open(winID);", 1)
    if insert_before not in body and insert_before.startswith("    win_GetObjRect(0x2101,"):
        insert_before = insert_before.replace("win_GetObjRect(0x2101,", "win_GetObjRect(itemID,", 1)
    if insert_before not in body:
        raise RuntimeError(f"missing ID initialization anchor: {insert_before}")
    body = body.replace(insert_before, f"    {label} = {value};\n" + insert_before, 1)
    text = BASE[:FN.body.s] + body + BASE[FN.body.e:]
    VARIANTS.append((meta["name"], text, meta))


def anchor(position: str) -> str:
    return {
        "entry": "    win_Open(0x2100);",
        "after_open": "    h = f_1A53_00F0((0x41 - which) * 2, 10, 1);",
        "after_handle": "    text = f_171C_1B84(h);",
        "after_text": "    f_24AB_02AD(g_3DB2 == 0x140 ? 2 : 4);",
        "after_font": "    if (g_5A97 & 1) {",
        "before_print": "    win_PrintTextInRect(0, text, &r);",
        "before_item": "    win_GetObjRect(0x2101, &r);",
    }[position]


ZERO_USES = {
    "all": [
        ("(*g_9128)(0, 0, 0);", "(*g_9128)(draw, draw, draw);"),
        ("win_PrintTextInRect(0, text, &r);", "win_PrintTextInRect(draw, text, &r);"),
        ("f_24AB_02AD(0);", "f_24AB_02AD(draw);"),
    ],
    "rect+print": [
        ("(*g_9128)(0, 0, 0);", "(*g_9128)(draw, draw, draw);"),
        ("win_PrintTextInRect(0, text, &r);", "win_PrintTextInRect(draw, text, &r);"),
    ],
    "print+clear": [
        ("win_PrintTextInRect(0, text, &r);", "win_PrintTextInRect(draw, text, &r);"),
        ("f_24AB_02AD(0);", "f_24AB_02AD(draw);"),
    ],
}

# A real draw/clear argument is initialized at successive points around the
# text segment's live range. Each read replaces an existing literal argument.
for uses in ("all", "rect+print"):
    for position in ("entry", "after_open", "after_handle", "after_text", "after_font"):
        for typename in ("int", "unsigned", "unsigned char"):
            tag = f"draw-{uses}-{position}-{typename.replace(' ', '_')}"
            put_local("draw", typename, "0", ZERO_USES[uses], anchor(position),
                      {"name": tag, "local": "draw", "type": typename,
                       "value": 0, "uses": uses, "initialization": position})
for position in ("after_text", "after_font", "before_print"):
    for typename in ("int", "unsigned", "unsigned char"):
        tag = f"draw-print+clear-{position}-{typename.replace(' ', '_')}"
        put_local("draw", typename, "0", ZERO_USES["print+clear"], anchor(position),
                  {"name": tag, "local": "draw", "type": typename,
                   "value": 0, "uses": "print+clear", "initialization": position})

# Reuse window IDs as real call arguments. These cross an actual text-pointer
# setup boundary in the listing and remain live to a later call or cleanup.
window_edits = [
    ("win_Open(0x2100);", "win_Open(winID);"),
    ("win_GetObjRect(0x2100, &r);", "win_GetObjRect(winID, &r);"),
    ("win_Close(0x2100);", "win_Close(winID);"),
]
for position in ("entry", "after_open", "after_handle", "after_text", "after_font"):
    edits = window_edits if position == "entry" else window_edits[1:]
    label = f"window-2100-{position}"
    put_id_local("winID", "0x2100", edits, anchor(position),
                 {"name": label, "local": "winID", "value": "0x2100",
                  "uses": [e[0] for e in edits], "initialization": position})

item_edits = [
    ("win_GetObjRect(0x2101, &r);", "win_GetObjRect(itemID, &r);"),
    ("win_SetColorFromObjNum(0x2101);", "win_SetColorFromObjNum(itemID);"),
]
for position in ("after_text", "after_font", "before_item"):
    put_id_local("itemID", "0x2101", item_edits, anchor(position),
                 {"name": f"window-2101-{position}", "local": "itemID",
                  "value": "0x2101", "uses": [e[0] for e in item_edits],
                  "initialization": position})

if len(VARIANTS) != 47:
    raise RuntimeError(f"expected 47 controls, generated {len(VARIANTS)}")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    out = OUT / "variants"
    out.mkdir(exist_ok=True)
    rows = []
    (out / "00_base").mkdir(parents=True, exist_ok=True)
    baseline = variants.run(CTX, [("base", BASE, "")], extra_funcs=[NAME],
                            claims_only=False, jobs=2, out_dir=out / "00_base")
    rows.extend(baseline)
    print("batch 00_base", _brief(baseline[0]), flush=True)
    for start in range(0, len(VARIANTS), 6):
        batch = VARIANTS[start:start + 6]
        batch_no = start // 6 + 1
        batch_dir = out / f"{batch_no:02d}_controls"
        batch_dir.mkdir(parents=True, exist_ok=True)
        got = variants.run(CTX, [(n, src, "") for n, src, _ in batch],
                           extra_funcs=[NAME], claims_only=False, jobs=2,
                           out_dir=batch_dir)
        rows.extend(got)
        meta_by_name = {m["name"]: m for _, _, m in batch}
        for row in got:
            row["meta"] = meta_by_name[row["name"]]
            row["source_sha256"] = sha256(Path(row["file"]).read_bytes())
        print(f"batch {batch_no:02d}",
              [(_brief(row)) for row in got], flush=True)
        (OUT / "variants-progress.json").write_text(
            json.dumps({"controls": len(rows), "rows": rows}, indent=1),
            encoding="utf-8")
        if any(_target_exact(row) for row in got):
            print("EXACT TARGET SEEN; stopping additional controls", flush=True)
            break

    # Attach base source hash and run-wide context to the final result inventory.
    if rows and rows[0]["name"] == "base":
        rows[0]["source_sha256"] = sha256(BASE_PATH.read_bytes())
    result = {
        "function": NAME,
        "module": CTX.key,
        "profile": CTX.profile,
        "flags": CTX.flags,
        "base_source_sha256": sha256(BASE_PATH.read_bytes()),
        "generator_sha256": sha256(Path(__file__).read_bytes()),
        "control_count_including_baseline": len(rows),
        "constraints": {"jobs": 2, "max_controls": 60, "writes": str(OUT)},
        "rows": rows,
    }
    dest = OUT / "results.json"
    dest.write_text(json.dumps(result, indent=1), encoding="utf-8")
    print("results_sha256", sha256(dest.read_bytes()), flush=True)


def _target_exact(row: dict) -> bool:
    target = row.get("result", {}).get("claims", {}).get(NAME, {})
    return bool(target.get("exact"))


def _brief(row: dict) -> dict:
    result = row.get("result", {})
    target = result.get("claims", {}).get(NAME, {})
    return {"name": row.get("name"), "target": target.get("reasons", "EXACT" if target.get("exact") else None),
            "all_claims_exact": result.get("all_exact"),
            "data": {k: v.get("exact") for k, v in result.get("data", {}).items()},
            "source_sha256": row.get("source_sha256")}


if __name__ == "__main__":
    main()
