from pathlib import Path
import hashlib
import json
import re
import sys

sys.path.insert(0, "tools")
import csrc
import modctx
import variants


NAME = "f_1C62_0415"
WORK = Path("build/workers/fleet_question")
BASE = (WORK / "question-base.c").read_text(encoding="latin1")
FUNC = csrc.Source(BASE).function(NAME)
BODY = BASE[FUNC.body.s:FUNC.body.e]
CTX = modctx.resolve(func=NAME)


def with_body(label: str, body: str, why: str):
    return label, BASE[:FUNC.body.s] + body + BASE[FUNC.body.e:], why


def replace_id_calls(body: str, object_base: str, include_draw: bool = True):
    if include_draw:
        body = body.replace("j + 0x900", "j + " + object_base)
    body = body.replace("c, &sel, count, 0x900", "c, &sel, count, " + object_base)
    body = body.replace("i + 0x900", "i + " + object_base)
    return body


rows = [("base", BASE, "frozen 653-byte candidate; scalar coordinates and distinct scan/draw counters")]

# The real object-ID base is shared by drawing, the keyboard fallback, and cleanup.
id_decl = "    int sel;\n"
early_id = BODY.replace(id_decl, id_decl + "    int objectBase;\n", 1)
early_id = early_id.replace("    sel = -1;\n", "    sel = -1;\n    objectBase = 0x900;\n", 1)
early_id = replace_id_calls(early_id, "objectBase")
rows.append(with_body("object-id-early-shared", early_id,
                      "same 0x900 object IDs across three real call sites; initialized before setup"))

decl_id = BODY.replace(id_decl, id_decl + "    int objectBase = 0x900;\n", 1)
decl_id = replace_id_calls(decl_id, "objectBase")
rows.append(with_body("object-id-declarator-init", decl_id,
                      "same shared call-argument value initialized by its local declaration"))

draw_id = BODY.replace(id_decl, id_decl + "    int objectBase;\n", 1)
draw_id = draw_id.replace("    g_9128(0x404, 0xc0c, 0xc0);\n",
                          "    objectBase = 0x900;\n    g_9128(0x404, 0xc0c, 0xc0);\n", 1)
draw_id = replace_id_calls(draw_id, "objectBase")
rows.append(with_body("object-id-before-draw", draw_id,
                      "same shared ID initialized before drawing and retained for later calls"))

key_id = BODY.replace(id_decl, id_decl + "    int objectBase;\n", 1)
key_id = key_id.replace("    f_1FD2_02FF();\n", "    objectBase = 0x900;\n    f_1FD2_02FF();\n", 1)
key_id = replace_id_calls(key_id, "objectBase", include_draw=False)
rows.append(with_body("object-id-before-key", key_id,
                      "same helper/cleanup ID initialized after drawing; shorter shared-argument lifetime"))

# The selected-key output is initialized at function entry in the candidate and
# at BP-12 on the original listing. Declarator form keeps that lifetime; the late
# control initializes the same default immediately before its only address use.
sel_decl = BODY.replace("    int sel;\n", "    int sel = -1;\n", 1).replace("    sel = -1;\n", "", 1)
rows.append(with_body("default-key-declarator-init", sel_decl,
                      "same early -1 initialization and same out-parameter lifetime"))

sel_late = BODY.replace("    sel = -1;\n", "", 1)
sel_late = sel_late.replace("    f_1FD2_02FF();\n    for (;;) {",
                            "    f_1FD2_02FF();\n    sel = -1;\n    for (;;) {", 1)
rows.append(with_body("default-key-before-input-loop", sel_late,
                      "same default before the stateful out-parameter loop; no reset between key events"))

# Snapshot the returned event code before cleanup calls, then return the local.
ans_decl = BODY.replace("    int sel;\n", "    int sel;\n    int answer;\n", 1)
done = ans_decl.index("done:")
ans_early = ans_decl[:done + len("done:")] + "\n    answer = (unsigned char)ev.code;" + ans_decl[done + len("done:"):]
ans_early = ans_early.replace("    return (unsigned char)ev.code;", "    return answer;", 1)
rows.append(with_body("return-snapshot-before-cleanup", ans_early,
                      "real event result copied before cleanup and retained across cleanup calls"))

ans_reg_decl = BODY.replace("    int sel;\n", "    int sel;\n    register int answer;\n", 1)
done = ans_reg_decl.index("done:")
ans_register = ans_reg_decl[:done + len("done:")] + "\n    answer = (unsigned char)ev.code;" + ans_reg_decl[done + len("done:"):]
ans_register = ans_register.replace("    return (unsigned char)ev.code;", "    return answer;", 1)
rows.append(with_body("return-snapshot-register", ans_register,
                      "same early result snapshot but requested in SI/DI register class"))

ans_late_decl = BODY.replace("    int sel;\n", "    int sel;\n    int answer;\n", 1)
ans_late = ans_late_decl.replace("    return (unsigned char)ev.code;",
                                 "    answer = (unsigned char)ev.code;\n    return answer;", 1)
rows.append(with_body("return-snapshot-after-cleanup", ans_late,
                      "negative contrast: result copied only at final return after cleanup"))

# c has two real roles separated by drawing: the spacing accumulator and the
# later key. Keep loop order and exactly-once update semantics unchanged.
def split_width_and_key(key_register: bool = False, inner_scope: bool = False):
    body = BODY.replace("    int c;\n", "    int minWidth;\n", 1)
    key_decl = "register int key;" if key_register else "int key;"
    if inner_scope:
        body = body.replace("    for (;;) {\n", "    for (;;) {\n        " + key_decl + "\n", 1)
    else:
        body = body.replace("    int minWidth;\n", "    int minWidth;\n    " + key_decl + "\n", 1)
    body = body.replace("c = v = h = j = 0;", "minWidth = v = h = j = 0;", 1)
    body = body.replace("c += 2;", "minWidth += 2;", 1)
    body = body.replace("if (width < c)", "if (width < minWidth)", 1)
    body = body.replace("        width = c;", "        width = minWidth;", 1)
    key_loop = body.index("    for (;;) {")
    done_at = body.index("\ndone:", key_loop)
    body = body[:key_loop] + re.sub(r"\bc\b", "key", body[key_loop:done_at]) + body[done_at:]
    return body


rows.append(with_body("split-spacing-and-key", split_width_and_key(),
                      "separates width spacing from late key input; loop semantics unchanged"))
rows.append(with_body("split-spacing-and-key-register", split_width_and_key(key_register=True),
                      "same phase split with the late key eligible for SI/DI"))
rows.append(with_body("split-spacing-and-key-inner", split_width_and_key(inner_scope=True),
                      "same phase split with key scoped inside the input loop"))

out_dir = WORK / "compiled"
out_dir.mkdir(parents=True, exist_ok=True)
results = variants.run(CTX, rows, extra_funcs=[NAME], claims_only=True, jobs=2,
                       out_dir=out_dir)
seed_hash = hashlib.sha256(BASE.replace("\r\n", "\n").encode("latin1")).hexdigest()
manifest_hash = hashlib.sha256(Path("layout/manifest.json").read_bytes()).hexdigest()
payload = {"function": NAME, "module": CTX.key, "profile": CTX.profile, "flags": CTX.flags,
           "placements": CTX.placements, "seed_sha256_lf": seed_hash,
           "manifest_sha256": manifest_hash, "variants": results}
(WORK / "question-results.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

for row in results:
    result = row["result"]
    target = result.get("claims", {}).get(NAME, {})
    peer_losses = [c["name"] for c in CTX.claims
                   if not result.get("claims", {}).get(c["name"], {}).get("exact")]
    data = {k: v.get("exact") for k, v in result.get("data", {}).items()}
    source_hash = hashlib.sha256(Path(row["file"]).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    print(row["name"], "compile=", result.get("compile_ok"), "target=", target.get("exact"),
          target.get("reasons"), "peer-losses=", peer_losses, "data=", data,
          "source=", source_hash, flush=True)
