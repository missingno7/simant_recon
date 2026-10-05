from __future__ import annotations
import hashlib
from pathlib import Path
SOURCE = Path('src/root/m15F8.c')
OLD_BLOCK = '    for (i = 0; i < 5; i++) {\n        if ((fh[i] = open("install.exe", 0)) <= 0) {\n            if (errno == 24) {\n                printf(fd_4E37_0000, 5 - i);\n                exit(1);\n            } else {\n                printf("DOS Error %d: %s", errno, sys_errlist[errno]);\n                exit(2);\n            }\n        }\n    }\n    for (i = 0; i < 5; i++)\n        close(fh[i]);\n    fd_50F6_10D0 = fh[0];'
NEW_BLOCK = '    {\n        int16_t opened_before_failure;\n        if (dos_startup_preflight("INSTALL.EXE", &fd_50F6_10D0,\n                                  &opened_before_failure) < 0) {\n            if (dos_errno == 24) {\n                printf(fd_4E37_0000, 5 - opened_before_failure);\n                exit(1);\n            } else {\n                printf("DOS Error %d: %s", dos_errno,\n                       dos_startup_error_text(dos_errno));\n                exit(2);\n            }\n        }\n    }'

def adapt(source: str) -> tuple[str, dict]:
    source = source.replace('\r\n', '\n')
    digest = hashlib.sha256(source.encode()).hexdigest()
    if source.count(OLD_BLOCK) != 1:
        raise ValueError('root m15F8 install preflight block changed')
    result = source.replace(OLD_BLOCK, NEW_BLOCK)
    include = '#include "platform/startup_preflight.h"\n'
    if include not in result:
        result = include + result
    io_include = '#include "platform/dos_io.h"\n'
    if io_include not in result:
        result = include + io_include + result[len(include):] if result.startswith(include) else io_include + result
    result = result.replace('extern int near errno;', 'extern int16_t dos_errno;', 1)
    result = result.replace('extern char far * near sys_errlist[];', '', 1)
    result = result.replace('extern int far open(char far *name, int mode, ...);', '', 1)
    result = result.replace('extern int far close(int fh);', '', 1)
    result = result.replace('extern void far exit(int code);', 'extern void far exit(int code);\nextern char *dos_startup_error_text(int16_t error);', 1)
    return (result, {'kind': 'MAIN_INSTALL_PREFLIGHT', 'source_path': str(SOURCE), 'source_sha256': digest, 'old_block_sha256': hashlib.sha256(OLD_BLOCK.encode()).hexdigest(), 'new_block_sha256': hashlib.sha256(NEW_BLOCK.encode()).hexdigest(), 'policy': "Preserve the closed numeric fh[0] slot after five simultaneous INSTALL.EXE opens; the virtual DOS allocator reuses it for the first retained database data file (language.dat if present, otherwise SHARED.DAT). This restores m00BA's original descriptor-number alias without treating INSTALL.EXE as the later file."})
