"""DOS/native predicate comparison for the original file chooser wildcard."""
from pathlib import Path
import argparse
import ctypes
import fnmatch
import hashlib
import itertools
import json
import random
import subprocess
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "build/behavior/deps")]
import behavior
import exe
import functions
import unicorn

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def words(alphabet, max_length):
    return ["".join(p).encode("ascii") for n in range(max_length + 1)
            for p in itertools.product(alphabet, repeat=n)]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="build/workers/whole_program/wildcard-v1")
    args = parser.parse_args()
    out = (ROOT / args.out).resolve()
    if not out.is_relative_to(ROOT / "build/workers"):
        raise ValueError("output must be scratch under build/workers")
    out.mkdir(parents=True, exist_ok=False)
    paths = [Path(__file__), ROOT / "portable/whole_program/algorithms/wildcard.c",
        ROOT / "portable/whole_program/algorithms/wildcard.h", ROOT / "src/root/m1F66.asm",
        ROOT / "src/S09/m35F5.c", ROOT / "tools/behavior.py", ROOT / "tools/functions.py",
        ROOT / "tools/exe.py", ROOT / "layout/oracle.lock.json"]
    before = {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}
    compiler = Path("C:/msys64/mingw64/bin/gcc.exe")
    library = out / "wildcard.dll"
    command = [str(compiler), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
               "-pedantic", "-shared", str(paths[1]), "-o", str(library)]
    subprocess.run(command, capture_output=True, text=True, check=True)
    native = ctypes.CDLL(str(library))
    native.f_1F66_002D.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    native.f_1F66_002D.restype = ctypes.c_int16
    machine = behavior.Machine(SimpleNamespace(function=functions.get("f_1F66_002D"),
        sequence_targets=frozenset(), sequence_function=functions.get, vectors={}))
    directed = list(itertools.product(words("aB?*", 3), words("ab.", 3)))
    directed += [(b"*.ant", s) for s in (b"a.ant", b"A.ANT", b"ant", b".ANT", b"a.ant.b",
        b"a.ant.ant", b"thing.Ant", b"x.bmp", b"", b"a..ant")]
    # These catch substituting a conventional backtracking glob implementation.
    directed += [(b"*ab", b"aab"), (b"a*b*c", b"aabbbc"), (b"**?", b"abc")]
    seed = 0x1F66002D
    rng = random.Random(seed)
    random_cases = [(bytes(rng.choice(b"aB.?*xyz\x80\xff") for _ in range(rng.randrange(13))),
                     bytes(rng.choice(b"ab.Bxyz\x80\xff") for _ in range(rng.randrange(13))))
                    for _ in range(1024)]
    mismatches = []
    transcript = hashlib.sha256()
    for i, (pattern, name) in enumerate(directed + random_cases):
        # Nonzero offsets model the source's stack-based find_t.name use. AX
        # is a DOS near-pointer token, compared only as the source's predicate.
        p = pattern + b"\0\xa7"
        n = name + b"\0\xb9"
        dos = machine.run(behavior.Case(f"wildcard-{i}",
            args=[0x1200, 0x3000, 0x1400, 0x3000],
            writes=[(0x31200, p), (0x31400, n)],
            observe=[behavior.Range("pattern", 0x31200, len(p)),
                     behavior.Range("name", 0x31400, len(n))], return_kind="s16"))
        native_pattern = ctypes.create_string_buffer(p)
        native_name = ctypes.create_string_buffer(n)
        got = int(native.f_1F66_002D(native_pattern, native_name))
        expected = int(dos["return"] != 0)
        unchanged = (bytes.fromhex(dos["ranges"]["pattern"]) == p and
                     bytes.fromhex(dos["ranges"]["name"]) == n and
                     native_pattern.raw[:len(p)] == p and native_name.raw[:len(n)] == n)
        transcript.update(json.dumps([pattern.hex(), name.hex(), expected, got, unchanged]).encode())
        if expected != got or not unchanged:
            mismatches.append({"case": i, "pattern": pattern.hex(), "name": name.hex(),
                               "DOS": expected, "native": got, "inputs_unchanged": unchanged})
            break
    stable = before == {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}
    mutant_pattern, mutant_name = b"*.ant", b"a.ant.b"
    native_source_result = int(native.f_1F66_002D(mutant_pattern, mutant_name))
    host_glob_result = int(fnmatch.fnmatchcase(mutant_name.decode(), mutant_pattern.decode()))
    negative_caught = native_source_result == 1 and host_glob_result == 0
    report = {"status": "PASS" if not mismatches and stable and negative_caught else "FAIL",
        "claim": "Source file chooser wildcard predicate and unchanged inputs; near-pointer return identity excluded",
        "function": "root:1F66:002D", "oracle_sha256": exe.load().sha256,
        "unicorn_version": unicorn.__version__, "inputs": before, "inputs_stable": stable,
        "compiler_sha256": sha(compiler), "command": command, "library_sha256": sha(library),
        "directed": len(directed), "randomized": len(random_cases), "seed": seed,
        "cases_executed": i + 1, "mismatches": mismatches, "transcript_sha256": transcript.hexdigest(),
        "negative_control": {"replacement": "conventional host glob", "pattern": "*.ant",
            "name": "a.ant.b", "DOS_backed_native_result": native_source_result,
            "host_glob_result": host_glob_result, "caught": negative_caught},
        "excluded": ["AX near-address value", "matching name segment offset zero", "unterminated inputs",
                     "search entry root:1F66:0029 (unused by current C callers)"]}
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("status", "cases_executed", "mismatches")}))
    if report["status"] != "PASS": raise RuntimeError("wildcard discrepancy")

if __name__ == "__main__": main()
