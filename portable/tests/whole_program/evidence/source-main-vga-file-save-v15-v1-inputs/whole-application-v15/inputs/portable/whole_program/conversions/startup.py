"""Explicit host boundary for the S15 BIOS disk-status/reset loop.

The loop and its caller-visible void result remain source-owned. The leaf is
unprovided until the native filesystem shutdown contract is implemented. This
does not require emulating BIOS disks, and is not a successful placeholder.
"""
from __future__ import annotations
import hashlib
import re

SOURCE_SHA256 = "01b51eecedcd28e2213819572c846a9754039f4a527e6da5e56e57783398bdd5"

ASM = """        _asm {
            mov dl, byte ptr drive
            or dl, 80h
            mov ah, 1
            int 13h
            jc skip
            mov ah, 0
            int 13h
        skip:
        }"""


def adapt(source: str) -> tuple[str, dict]:
    # Tokens pin the real boundary without depending on CRLF spelling.
    source = source.replace("\r\n", "\n")
    if source.count(ASM) != 1:
        raise ValueError("S15 BIOS disk reset source changed")
    result = source.replace(ASM, "        dos_host_reset_disk_if_ready((unsigned char)(drive | 0x80));")
    result = "extern void dos_host_reset_disk_if_ready(unsigned char drive);\n" + result
    return result, {"kind": "BIOS_DISK_RESET_HOST_BOUNDARY", "function": "o15_384C_0125",
        "assembly_source_sha256": hashlib.sha256(ASM.encode()).hexdigest(),
        "source_sha256": SOURCE_SHA256,
        "changes": "BIOS INT13 AH=1/status then AH=0/reset becomes explicit host disk-lifecycle leaf; original 12-drive loop remains",
        "leaf_status": "UNPROVIDED: native lifecycle policy required; no BIOS emulation or successful stub"}
