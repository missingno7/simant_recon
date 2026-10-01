from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import autosearch
import csrc
import modctx
import variants


NAME = "SpiderScan"
OUT = ROOT / "build" / "workers" / "fleet_spider" / "variants_lifetimes"
OUT.mkdir(parents=True, exist_ok=True)
ctx = modctx.resolve(func=NAME)
base = (ROOT / "build/workers/fleet_spider/seed.c").read_text(encoding="latin1")
source = csrc.Source(base)
fn = source.function(NAME)
body = base[fn.body.s:fn.body.e]
variants_in: list[tuple[str, str, str]] = []


def add(label: str, b: str) -> None:
    text = base[:fn.body.s] + b + base[fn.body.e:]
    variants_in.append((label, text, ""))


def replace(b: str, old: str, new: str) -> str:
    if old not in b:
        raise ValueError(f"missing source fragment: {old!r}")
    return b.replace(old, new, 1)


add("scalar_baseline", body)

# Keep the earlier positive storage/lifetime candidate for direct comparison;
# remaining rows alter real declarations or actual later constant arguments.
struct = replace(body, "    int r = 0;", "    struct { int value; } r = {0};")
struct = struct.replace("r = SRand1(12)", "r.value = SRand1(12)")
struct = struct.replace("(long)r /", "(long)r.value /")
add("struct_r_first_prior", struct)

# Declaration placement controls use the same initialized, later-read local.
for label, anchor in (("after_found", "    int found = -1;\n"),
                      ("after_pass", "    int pass;\n"),
                      ("after_life", "    int life;\n")):
    b = replace(body, "    int r = 0;\n", "")
    b = replace(b, anchor, anchor + "    struct { int value; } r = {0};\n")
    b = b.replace("r = SRand1(12)", "r.value = SRand1(12)")
    b = b.replace("(long)r /", "(long)r.value /")
    add("struct_r_" + label, b)

for label, anchor in (("after_found", "    int found = -1;\n"),
                      ("after_pass", "    int pass;\n"),
                      ("after_life", "    int life;\n")):
    b = replace(body, "    int r = 0;\n", "")
    b = replace(b, anchor, anchor + "    int r = 0;\n")
    add("scalar_r_" + label, b)

# Actual later constants promoted to initialized locals. The early forms test the
# LIFE-2-style lifetime; the inner-pass forms are lifetime contrasts. Every new
# local replaces a real constant in the computation or call that consumes it.
def with_local(label: str, declaration: str, old: str, new: str,
               insertion: str = "entry", inner_scope: bool = False) -> None:
    b = body
    if insertion == "entry":
        b = replace(b, "{\n", "{\n    " + declaration + "\n",)
    elif insertion == "after_found":
        b = replace(b, "    int found = -1;\n", "    int found = -1;\n    " + declaration + "\n")
    elif insertion == "outer_body":
        b = replace(b, "    for (pass = 0; pass < 2; pass++) {\n",
                    "    for (pass = 0; pass < 2; pass++) {\n        " + declaration + "\n")
    b = b.replace(old, new)
    add(label, b)


with_local("rand_limit_int_early", "int randLimit = 12;", "SRand1(12)", "SRand1(randLimit)")
with_local("rand_limit_uint_early", "unsigned randLimit = 12;", "SRand1(12)", "SRand1(randLimit)")
with_local("rand_limit_int_outer", "int randLimit = 12;", "SRand1(12)", "SRand1(randLimit)", "outer_body")
with_local("search_plane_int_early", "int searchPlane = 1;", "FindAntIndex(1,", "FindAntIndex(searchPlane,")
with_local("search_plane_uint_early", "unsigned searchPlane = 1;", "FindAntIndex(1,", "FindAntIndex(searchPlane,")
with_local("half_angle_int_early", "int halfAngle = 32;", "dir - 32", "dir - halfAngle")
with_local("half_angle_uint_early", "unsigned halfAngle = 32;", "dir - 32", "dir - halfAngle")
with_local("half_angle_int_outer", "int halfAngle = 32;", "dir - 32", "dir - halfAngle", "outer_body")
with_local("fixed_scale_long_early", "long fixedScale = 32767L;", "32767L", "fixedScale")
with_local("fixed_scale_int_early", "int fixedScale = 32767;", "32767L", "fixedScale")
with_local("fire_offset_int_early", "int fireOffset = 7;", "+ 7", "+ fireOffset")
with_local("fire_offset_int_outer", "int fireOffset = 7;", "+ 7", "+ fireOffset", "outer_body")
with_local("x_bound_int_early", "int maxX = 127;", "x <= 127", "x <= maxX")
with_local("y_bound_int_early", "int maxY = 63;", "y <= 63", "y <= maxY")
with_local("pass_limit_int_early", "int passLimit = 2;", "pass < 2", "pass < passLimit")
with_local("pass_limit_int_outer", "int passLimit = 2;", "pass < 2", "pass < passLimit", "outer_body")
with_local("random_step_int_early", "int randomStep = 1;", "+ 1;\n            x", "+ randomStep;\n            x")
with_local("angle_low_int_early", "int angleLow = -32;", "dir - 32", "dir + angleLow")

# Real argument/value locals combined in pairs test whether the register and home
# allocation responds to overlapping versus sequential value lifetimes.
def combined(label: str, declarations: list[str], edits: list[tuple[str, str]]) -> None:
    b = replace(body, "{\n", "{\n" + "".join("    " + d + "\n" for d in declarations))
    for old, new in edits:
        b = b.replace(old, new)
    add(label, b)


combined("range_and_plane_early", ["int randLimit = 12;", "int searchPlane = 1;"],
         [("SRand1(12)", "SRand1(randLimit)"), ("FindAntIndex(1,", "FindAntIndex(searchPlane,")])
combined("range_and_half_angle_early", ["int randLimit = 12;", "int halfAngle = 32;"],
         [("SRand1(12)", "SRand1(randLimit)"), ("dir - 32", "dir - halfAngle"), ("dir + 32", "dir + halfAngle")])
combined("plane_and_fire_offset_early", ["int searchPlane = 1;", "int fireOffset = 7;"],
         [("FindAntIndex(1,", "FindAntIndex(searchPlane,"), ("+ 7", "+ fireOffset")])
combined("scale_and_half_angle_early", ["long fixedScale = 32767L;", "int halfAngle = 32;"],
         [("32767L", "fixedScale"), ("dir - 32", "dir - halfAngle"), ("dir + 32", "dir + halfAngle")])
combined("range_and_fire_offset_early", ["int randLimit = 12;", "int fireOffset = 7;"],
         [("SRand1(12)", "SRand1(randLimit)"), ("+ 7", "+ fireOffset")])
combined("bounds_and_plane_early", ["int maxX = 127;", "int maxY = 63;", "int searchPlane = 1;"],
         [("x <= 127", "x <= maxX"), ("y <= 63", "y <= maxY"), ("FindAntIndex(1,", "FindAntIndex(searchPlane,")])
combined("range_scale_offset_early", ["int randLimit = 12;", "long fixedScale = 32767L;", "int fireOffset = 7;"],
         [("SRand1(12)", "SRand1(randLimit)"), ("32767L", "fixedScale"), ("+ 7", "+ fireOffset")])
combined("passlimit_plane_early", ["int passLimit = 2;", "int searchPlane = 1;"],
         [("pass < 2", "pass < passLimit"), ("FindAntIndex(1,", "FindAntIndex(searchPlane,")])

if len(variants_in) > 40:
    raise RuntimeError(f"control cap exceeded: {len(variants_in)}")

rows = variants.run(ctx, variants_in, extra_funcs=[NAME], jobs=2, out_dir=OUT)
summary = []
for row in rows:
    res = row["result"]
    c = res.get("claims", {}).get(NAME, {})
    summary.append({
        "name": row["name"],
        "file": row.get("file"),
        "compile_ok": res.get("compile_ok"),
        "exact": c.get("exact"),
        "length": c.get("length"),
        "reasons": c.get("reasons", res.get("reasons", [])),
        "claims": {k: (v.get("exact") if v else None) for k, v in res.get("claims", {}).items()},
        "data": {k: v.get("exact") for k, v in res.get("data", {}).items()},
        "module_reasons": res.get("module_reasons", []),
    })
(OUT / "summary.json").write_text(json.dumps({"module": ctx.key, "profile": ctx.profile,
                                               "flags": ctx.flags, "placements": ctx.placements,
                                               "control_count": len(summary), "rows": summary},
                                              indent=2), encoding="utf-8")
print(f"module={ctx.key} profile={ctx.profile} flags={ctx.flags}")
print(f"placements={ctx.placements}")
print(f"controls={len(summary)}")
for row in summary:
    print(f"{row['name']}: compile={row['compile_ok']} exact={row['exact']} length={row['length']} "
          f"reasons={row['reasons'][:2]}")
print(f"wrote {OUT / 'summary.json'}")
