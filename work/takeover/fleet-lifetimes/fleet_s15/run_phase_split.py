"""Five bounded controls for distinct actual arguments in disjoint setup phases."""
from __future__ import annotations

import hashlib
import json
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

CASES = [
    ("clear-after-handle_print-after-rect",
     "    text = f_171C_1B84(h);", "    win_GetObjRect(0x2101, &r);"),
    ("clear-after-text_print-after-rect",
     "    f_24AB_02AD(g_3DB2 == 0x140 ? 2 : 4);", "    win_GetObjRect(0x2101, &r);"),
    ("clear-after-font_print-after-rect",
     "    if (g_5A97 & 1) {", "    win_GetObjRect(0x2101, &r);"),
    ("clear-after-text_print-at-call",
     "    f_24AB_02AD(g_3DB2 == 0x140 ? 2 : 4);", "    win_PrintTextInRect(printArg, text, &r);"),
    ("clear-after-handle_print-early",
     "    text = f_171C_1B84(h);", "    win_Open(0x2100);"),
]

drafts = []
for case, clear_anchor, print_anchor in CASES:
    body = BODY.replace("    int result;\n",
                        "    int result;\n    int clearArg;\n    int printArg;\n", 1)
    body = body.replace("(*g_9128)(0, 0, 0);",
                        "(*g_9128)(clearArg, clearArg, clearArg);", 1)
    body = body.replace("win_PrintTextInRect(0, text, &r);",
                        "win_PrintTextInRect(printArg, text, &r);", 1)
    body = body.replace("f_24AB_02AD(0);", "f_24AB_02AD(printArg);", 1)
    if clear_anchor not in body or print_anchor not in body:
        raise RuntimeError(f"missing phase anchor in {case}")
    body = body.replace(clear_anchor, "    clearArg = 0;\n" + clear_anchor, 1)
    body = body.replace(print_anchor, "    printArg = 0;\n" + print_anchor, 1)
    text = BASE[:FN.body.s] + body + BASE[FN.body.e:]
    drafts.append((case, text, ""))

OUTDIR = OUT / "variants" / "split_phases"
OUTDIR.mkdir(parents=True, exist_ok=True)
rows = variants.run(CTX, drafts, extra_funcs=[NAME], claims_only=False,
                    jobs=2, out_dir=OUTDIR)
for i, (_, source, _) in enumerate(drafts):
    rows[i]["source_sha256"] = hashlib.sha256(source.encode("latin1")).hexdigest()
result_path = OUT / "phase-split-results.json"
result_path.write_text(json.dumps({
    "function": NAME,
    "module": CTX.key,
    "profile": CTX.profile,
    "flags": CTX.flags,
    "base_source_sha256": hashlib.sha256(BASE_PATH.read_bytes()).hexdigest(),
    "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "control_count": len(rows),
    "jobs": 2,
    "rows": rows,
}, indent=1), encoding="utf-8")
print("results_sha256", hashlib.sha256(result_path.read_bytes()).hexdigest(), flush=True)
for row in rows:
    r = row["result"]
    target = r["claims"][NAME]
    print(row["name"], "compile", r["compile_ok"], "target", target.get("reasons"),
          "module", r.get("exact"), "peers",
          [n for n, v in r["claims"].items() if n != NAME and not v.get("exact")],
          "data", {n: v.get("exact") for n, v in r.get("data", {}).items()}, flush=True)
