from __future__ import annotations
import hashlib
from . import main_preflight
MAIN_PATH = 'src/root/m15F8.c'
S15_PATH = 'src/S15/m384C.c'
BREAK_CALL = 'signal(0x15, (void (far *)(int))1L);'
INT_CALL = 'signal(2, (void (far *)(int))1L);'
BIOS_FUNCTION = 'void far o15_384C_0125(void)\n{\n    int drive;\n\n    for (drive = 0; drive < 12; drive++) {\n        _asm {\n            mov dl, byte ptr drive\n            or dl, 80h\n            mov ah, 1\n            int 13h\n            jc skip\n            mov ah, 0\n            int 13h\n        skip:\n        }\n    }\n}'
RETIRED_BIOS_FUNCTION = 'void far o15_384C_0125(void)\n{\n    dos_host_retire_bios_reset_loop();\n}'

def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

def _replace_once(source: str, old: str, new: str, label: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f'startup source anchor changed: {label}')
    return source.replace(old, new, 1)

def convert_startup_sources(main_text: str, s15_text: str) -> tuple[dict[str, str], dict]:
    """Convert the canonical main preflight/signals and retire the BIOS reset loop.

    The m15F8 helper retains five real simultaneous opens and closes, including
    the closed descriptor number and its later reuse by the DOS I/O table.
    The S15 helper is external physical BIOS state and is explicitly retired.
    """
    main_text = main_text.replace('\r\n', '\n')
    s15_text = s15_text.replace('\r\n', '\n')
    (main, main_meta) = main_preflight.adapt(main_text)
    main = _replace_once(main, BREAK_CALL, 'dos_host_ignore_legacy_break();', 'SIGBREAK ignore')
    main = _replace_once(main, INT_CALL, 'dos_host_ignore_legacy_interrupt();', 'SIGINT ignore')
    host_include = '#include "platform/startup_host.h"\n'
    main = host_include + main
    s15_hash = _sha(s15_text)
    s15 = _replace_once(s15_text, BIOS_FUNCTION, RETIRED_BIOS_FUNCTION, 'S15 INT 13h reset loop')
    s15 = host_include + s15
    converted = {MAIN_PATH: main, S15_PATH: s15}
    metadata = {'schema': 'whole-program-startup-conversion-v1', 'public_api': 'startup_bundle.convert_startup_sources(main_text, s15_text)', 'sources': {MAIN_PATH: {'sha256': _sha(main_text), 'adapter': main_meta}, S15_PATH: {'sha256': s15_hash, 'retired_function_sha256': hashlib.sha256(BIOS_FUNCTION.encode()).hexdigest()}}, 'outputs': {path: _sha(text) for (path, text) in converted.items()}, 'boundaries': {'install_probe': 'Five real simultaneous INSTALL.EXE opens and closes preserve the closed fh[0] number; the first retained database data open reuses that number for original trailer loading.', 'interrupt_policy': 'Numeric MSC SIGBREAK/SIGINT calls map to native SIGBREAK/SIGINT ignore policy.', 'bios_reset': 'The physical INT 13h drive scan is retired through an explicit no-I/O host policy.'}}
    return (converted, metadata)
