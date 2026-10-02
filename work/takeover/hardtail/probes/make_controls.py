from pathlib import Path
import sys

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "tools" / "csrc.py").is_file())
sys.path.insert(0, str(ROOT / "tools"))
import csrc

base_path = Path(__file__).with_name("base.c")
base = base_path.read_text(encoding="latin1")
function = csrc.Source(base).function("FindIndex")
body = base[function.body.s:function.body.e]
old = """        if (!(fd_50F6_3952->kind < kind || (fd_50F6_3952->kind == kind && fd_50F6_3952->id < id)))
            top = mid - 1;
        else
            fd_50F6_3956 = mid + 1;"""
assert old in body

# The outer <= guard is chosen so MSC can emit JG directly to the upper-bound
# update. The two nested rejection tests then have the target's JNE/JL edges to
# one low-update label. Every form gives the loop continuation a real reference.
forms = {
    "v0_guard_gotos": """        if (fd_50F6_3952->kind <= kind) {
            if (fd_50F6_3952->kind != kind)
                goto lower_update;
            if (fd_50F6_3952->id < id)
                goto lower_update;
        }
        top = mid - 1;
        goto iteration_end;
lower_update:
        fd_50F6_3956 = mid + 1;
iteration_end: ;""",
    "v1_guard_conditionals": """        if (fd_50F6_3952->kind <= kind) {
            if (fd_50F6_3952->kind != kind || fd_50F6_3952->id < id)
                goto lower_update;
        }
        top = mid - 1;
        goto iteration_end;
lower_update:
        fd_50F6_3956 = mid + 1;
iteration_end: ;""",
    "v2_direct_priority": """        if (fd_50F6_3952->kind > kind)
            goto upper_update;
        if (fd_50F6_3952->kind != kind)
            goto lower_update;
        if (fd_50F6_3952->id < id)
            goto lower_update;
upper_update:
        top = mid - 1;
        goto iteration_end;
lower_update:
        fd_50F6_3956 = mid + 1;
iteration_end: ;""",
    "v3_nested_equal": """        if (fd_50F6_3952->kind <= kind) {
            if (fd_50F6_3952->kind == kind) {
                if (fd_50F6_3952->id < id)
                    goto lower_update;
            } else {
                goto lower_update;
            }
        }
        top = mid - 1;
        goto iteration_end;
lower_update:
        fd_50F6_3956 = mid + 1;
iteration_end: ;""",
}

out = Path(__file__).parent
for name, replacement in forms.items():
    candidate = base[:function.body.s] + body.replace(old, replacement) + base[function.body.e:]
    (out / f"{name}.c").write_text(candidate, encoding="latin1", newline="\n")
print("generated", len(forms), "whole-module controls")
