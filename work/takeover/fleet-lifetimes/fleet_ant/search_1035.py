from pathlib import Path
import hashlib
import json
import sys

sys.path.insert(0, "tools")
import csrc
import modctx
import variants


NAME = "o25_3BA4_1035"
WORK = Path("build/workers/fleet_ant")
BASE = (WORK / "1035-base.c").read_text(encoding="latin1")
FUNC = csrc.Source(BASE).function(NAME)
BODY = BASE[FUNC.body.s:FUNC.body.e]
CTX = modctx.resolve(func=NAME)
TARGET_X = "fd_50F6_047C"
ARGS = "fd_50F6_048C, fd_50F6_047C, fd_50F6_048A"


def replace_body(label: str, body: str):
    return label, BASE[:FUNC.body.s] + body + BASE[FUNC.body.e:], ""


def call_phase_body(pointer_name: str, start_before_update: bool = False):
    start = BODY.index("    if (fd_50F6_048C == 2)")
    end = BODY.index("    f_10F7_0A44(", start)
    phase = BODY[start:end]
    phase = phase.replace(
        "DigMyTile(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A)",
        f"DigMyTile(fd_50F6_048C, *{pointer_name}, fd_50F6_048A)",
    )
    if start_before_update:
        early = BODY.index("    fd_50F6_047C = fd_50F6_048A;")
        # The same phase, now scoped from the coordinate write through DigMyTile.
        phase_start = early
        prefix = BODY[phase_start:start]
        return (BODY[:phase_start] + "    {\n"
                + f"        int far *{pointer_name} = &{TARGET_X};\n"
                + prefix + phase + "    }\n" + BODY[end:])

    return BODY[:start] + "    {\n" + f"        int far *{pointer_name} = &{TARGET_X};\n" + phase + "    }\n" + BODY[end:]


variants_to_run = [("base", BASE, "")]

# A distinct far-pointer value is acquired for the earlier draw call, then dies.
# Its only effect is changing how the same global lvalue is reached at that call.
initial = BODY.index("    f_10F7_09A8(")
initial_end = BODY.index(";", initial) + 1
draw_call = BODY[initial:initial_end]
draw_call = draw_call.replace(TARGET_X, "*earlyX")
early_ptr = (BODY[:initial] + "    {\n"
             + f"        int far *earlyX = &{TARGET_X};\n"
             + draw_call + "\n    }" + BODY[initial_end:])
variants_to_run.append(replace_body("early-call-pointer", early_ptr))

# The later tile argument gets a separate pointer local. Test initialization at
# the actual argument phase and before the preceding coordinate write.
variants_to_run.append(replace_body("dig-call-pointer", call_phase_body("digX")))
variants_to_run.append(replace_body("dig-pointer-before-coordinate-write",
                                    call_phase_body("digX", start_before_update=True)))

# Value-result control: take the actual post-update field value immediately
# before the identical branch calls and use it as that real call argument.
value_start = BODY.index("    if (fd_50F6_048C == 2)")
value_end = BODY.index("    f_10F7_0A44(", value_start)
value_phase = BODY[value_start:value_end].replace(
    "DigMyTile(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A)",
    "DigMyTile(fd_50F6_048C, digX, fd_50F6_048A)",
)
value_body = (BODY[:value_start] + "    {\n        register int digX = fd_50F6_047C;\n"
              + value_phase + "    }\n" + BODY[value_end:])
variants_to_run.append(replace_body("dig-call-value", value_body))

# One function-local pointer serves two non-overlapping source phases. This is
# the negative contrast for the split-phase pointer control.
split_body = (BODY.replace("{\n", "{\n    int far *phaseX;\n", 1))
split_start = split_body.index("    f_10F7_09A8(")
split_end = split_body.index(";", split_start) + 1
split_call = split_body[split_start:split_end].replace(TARGET_X, "*phaseX")
split_body = (split_body[:split_start] + "    phaseX = &" + TARGET_X + ";\n"
              + split_call + split_body[split_end:])
later_start = split_body.index("    if (fd_50F6_048C == 2)")
later_end = split_body.index("    f_10F7_0A44(", later_start)
later = "    phaseX = &" + TARGET_X + ";\n" + split_body[later_start:later_end].replace(
    "DigMyTile(fd_50F6_048C, fd_50F6_047C, fd_50F6_048A)",
    "DigMyTile(fd_50F6_048C, *phaseX, fd_50F6_048A)",
)
split_body = split_body[:later_start] + later + split_body[later_end:]
variants_to_run.append(replace_body("one-pointer-two-phases", split_body))

out_dir = WORK / "compiled"
out_dir.mkdir(parents=True, exist_ok=True)
rows = variants.run(CTX, variants_to_run, extra_funcs=[NAME], claims_only=True,
                    jobs=2, out_dir=out_dir)
(WORK / "1035-results.json").write_text(
    json.dumps({"function": NAME, "profile": CTX.profile, "flags": CTX.flags,
                "placements": CTX.placements, "variants": rows}, indent=2),
    encoding="utf-8")

for row in rows:
    result = row["result"]
    target = result.get("claims", {}).get(NAME, {})
    losses = [claim["name"] for claim in CTX.claims
              if not result.get("claims", {}).get(claim["name"], {}).get("exact")]
    data = {k: v.get("exact") for k, v in result.get("data", {}).items()}
    source = row.get("file")
    source_hash = hashlib.sha256(Path(source).read_bytes().replace(b"\r\n", b"\n")).hexdigest() if source else ""
    print(row["name"], "target=", target.get("exact"), target.get("reasons"),
          "peer-losses=", losses, "data=", data, "source=", source_hash, flush=True)
