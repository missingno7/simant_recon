from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "build" / "portable" / "tests" / "legacy-save-codec.exe"
BIG_ENDIAN_OUT = ROOT / "build" / "portable" / "tests" / "legacy-save-codec-big-endian.exe"
OUT.parent.mkdir(parents=True, exist_ok=True)
subprocess.run([sys.executable, str(ROOT / "portable/tests/save/generate_legacy_records.py"), "--check"],
               cwd=ROOT, check=True)
cmd = [
    "gcc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
    "-I", str(ROOT / "portable"),
    str(ROOT / "portable/game/save/legacy_codec.c"),
    str(ROOT / "portable/tests/save/test_legacy_codec.c"),
    "-o", str(OUT),
]
subprocess.run(cmd, cwd=ROOT, check=True)
subprocess.run([str(OUT)], cwd=ROOT, check=True)
big_endian_cmd = cmd.copy()
big_endian_cmd.insert(1, "-DPORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN")
big_endian_cmd[-1] = str(BIG_ENDIAN_OUT)
subprocess.run(big_endian_cmd, cwd=ROOT, check=True)
subprocess.run([str(BIG_ENDIAN_OUT)], cwd=ROOT, check=True)
