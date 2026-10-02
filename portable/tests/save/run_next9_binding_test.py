from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
GEN = ROOT / "build/workers/recovered_source_next9/generated"
OUT = ROOT / "build/portable/tests/legacy-save-next9.exe"
BE_OUT = ROOT / "build/portable/tests/legacy-save-next9-big-endian.exe"
OUT.parent.mkdir(parents=True, exist_ok=True)
cmd = [
    "gcc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
    "-I", str(ROOT / "portable"), "-I", str(GEN),
    str(ROOT / "portable/game/save/legacy_codec.c"),
    str(ROOT / "portable/game/save/next9_bindings.c"),
    str(GEN / "recovered_state.c"),
    str(ROOT / "portable/tests/save/test_next9_bindings.c"),
    "-o", str(OUT),
]
subprocess.run(cmd, cwd=ROOT, check=True)
subprocess.run([str(OUT), *sys.argv[1:]], cwd=ROOT, check=True)
be_cmd = cmd.copy()
be_cmd.insert(1, "-DPORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN")
be_cmd[-1] = str(BE_OUT)
subprocess.run(be_cmd, cwd=ROOT, check=True)
subprocess.run([str(BE_OUT), *sys.argv[1:]], cwd=ROOT, check=True)
