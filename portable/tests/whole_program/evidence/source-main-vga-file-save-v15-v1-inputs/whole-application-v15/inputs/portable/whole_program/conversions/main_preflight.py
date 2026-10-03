"""Strict source adapter for root m15F8's five-file startup preflight block."""
from __future__ import annotations

import hashlib
from pathlib import Path

SOURCE = Path("src/root/m15F8.c")
SOURCE_SHA256 = "d6d4daddab943ee3436ca0e9c8dbc866a9d67659f7448f3c307f858abe06b70a"

OLD_BLOCK = '''    for (i = 0; i < 5; i++) {
        if ((fh[i] = open("install.exe", 0)) <= 0) {
            if (errno == 24) {
                printf(fd_4E37_0000, 5 - i);
                exit(1);
            } else {
                printf("DOS Error %d: %s", errno, sys_errlist[errno]);
                exit(2);
            }
        }
    }
    for (i = 0; i < 5; i++)
        close(fh[i]);
    fd_50F6_10D0 = fh[0];'''

NEW_BLOCK = '''    {
        int16_t opened_before_failure;
        if (dos_startup_preflight("INSTALL.EXE", &fd_50F6_10D0,
                                  &opened_before_failure) < 0) {
            if (dos_errno == 24) {
                printf(fd_4E37_0000, 5 - opened_before_failure);
                exit(1);
            } else {
                printf("DOS Error %d: %s", dos_errno,
                       dos_startup_error_text(dos_errno));
                exit(2);
            }
        }
    }'''


def adapt(source: str) -> tuple[str, dict]:
    source = source.replace("\r\n", "\n")
    digest = hashlib.sha256(source.encode()).hexdigest()
    if SOURCE_SHA256 and digest != SOURCE_SHA256:
        raise ValueError("root m15F8 source identity changed")
    if source.count(OLD_BLOCK) != 1:
        raise ValueError("root m15F8 install preflight block changed")
    result = source.replace(OLD_BLOCK, NEW_BLOCK)
    include = '#include "platform/startup_preflight.h"\n'
    if include not in result:
        result = include + result
    io_include = '#include "platform/dos_io.h"\n'
    if io_include not in result:
        result = include + io_include + result[len(include):] if result.startswith(include) else io_include + result
    result = result.replace("extern int near errno;", "extern int16_t dos_errno;", 1)
    result = result.replace("extern char far * near sys_errlist[];", "", 1)
    result = result.replace("extern int far open(char far *name, int mode, ...);", "", 1)
    result = result.replace("extern int far close(int fh);", "", 1)
    result = result.replace("extern void far exit(int code);", "extern void far exit(int code);\nextern char *dos_startup_error_text(int16_t error);", 1)
    return result, {
        "kind": "MAIN_INSTALL_PREFLIGHT",
        "source_path": str(SOURCE),
        "source_sha256": digest,
        "old_block_sha256": hashlib.sha256(OLD_BLOCK.encode()).hexdigest(),
        "new_block_sha256": hashlib.sha256(NEW_BLOCK.encode()).hexdigest(),
        "policy": "Preserve the closed numeric fh[0] slot after five simultaneous INSTALL.EXE opens; the virtual DOS allocator reuses it for the first retained database data file (language.dat if present, otherwise SHARED.DAT). This restores m00BA's original descriptor-number alias without treating INSTALL.EXE as the later file.",
    }
