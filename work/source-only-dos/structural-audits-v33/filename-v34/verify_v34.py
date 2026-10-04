"""Read-only verifier for receipt.json. Run from the repository root."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RECEIPT = Path(__file__).with_name("receipt.json")


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def read_repo_path(path: str) -> Path:
    return Path(path) if re.match(r"^[A-Za-z]:/", path) else ROOT / path


receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
checked = 0
for pin in receipt["pins"]:
    path = read_repo_path(pin["path"])
    if not path.is_file():
        fail(f"missing pinned input: {pin['path']}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != pin["sha256"]:
        fail(f"hash mismatch: {pin['path']} expected {pin['sha256']} got {digest}")
    checked += 1

contract = json.loads((ROOT / receipt["active_production_state"]["contract"]).read_text(encoding="utf-8"))
if contract.get("admitted") is not True:
    fail("active production contract no longer reports admitted=true")
owners = {item["name"]: item["length"] for item in contract.get("communals", [])}
expected = {"_fd_50F6_385A": 4, "_fd_50F6_385E": 4}
if owners != expected or any("3862" in name for name in owners):
    fail(f"production contract owner set changed: {owners}")

acceptance = json.loads((ROOT / "work/source-only-dos/storage-admission-v27/handles/root-acceptance.json").read_text(encoding="utf-8"))
if "Filename3862 excluded" not in acceptance.get("source_extent_basis", ""):
    fail("v27 root acceptance no longer explicitly excludes 3862")
policy = json.loads((ROOT / "work/source-only-dos/storage-admission-v27/handles/independent-literal-policy.json").read_text(encoding="utf-8"))
if policy.get("independent_type_policy", {}).get("do_not_infer_3862_extent") is not True:
    fail("v27 policy no longer forbids inferring the 3862 extent")

source = (ROOT / "src/S09/m35F5.c").read_text(encoding="utf-8")
for required in (
    "extern char far fd_50F6_3862[];",
    "_fstrcpy(fd_50F6_3862, name);",
    "o09_36EE_0092(x, y, name, 9, 0);",
    'sprintf(name, "%s%s", path, buf);',
):
    if required not in source:
        fail(f"source fact missing: {required}")
editor = (ROOT / "src/S09/m36EE.c").read_text(encoding="utf-8")
if "if (maxLen <= 0)" not in editor or "maxLen--;" not in editor:
    fail("editor maxLen behavior changed")

win16 = read_repo_path("D:/Prog/simantw_recon/src/recovered/ClearLastFileName.c").read_text(encoding="utf-8")
if "editBufInvalidFlag[1834] = 0;" not in win16 or re.search(r"\b(?:char|unsigned char)\s+far\s+\*?\s*lastFileName\b", win16, re.I):
    fail("Win16 ClearLastFileName finding changed")

print(f"PASS: {checked} SHA-256 pins and v34 source/contract/exclusion assertions verified; no files modified")
