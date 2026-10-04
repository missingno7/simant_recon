# DOS v36 worker receipt inventory

Read-only byte bookkeeping for the four named v36 worker packets. No acceptance decision or functional claim is made.

Scanned 30 JSON files and enumerated 1067 nested dictionaries with `path` plus `sha256`.

Pin checks: 1060 exact, 7 drift, 0 missing, 0 unreadable, 0 malformed.
Drifted diagnostic output pins: 2 (observed hashes remain in `inventory.json`; no pins were changed).
Binary files pinned only: 533 occurrences. They are excluded from the preservation list.
Current text preservation candidates: 237 unique files.

## Preservation candidates by worker

These are current text files referenced by packet pins inside the four worker directories, plus the requested packet reports/scripts and unpinned text evidence at packet roots. Each row carries its pin status; unpinned files have only a current snapshot hash and drifted files stay visibly marked. No files were copied or archived.

- `dos_tail_clear_v36`: 72 files (25 raw `.log`/`.map`; .bat 12, .c 3, .conf 12, .json 7, .log 19, .map 6, .md 1, .py 6, .txt 6).
- `dos_ctype_sequence_v36`: 131 files (31 raw `.log`/`.map`; .bat 20, .c 4, .cfg 9, .conf 20, .json 15, .log 22, .map 9, .md 1, .py 3, .txt 28).
- `dos_database_exit_v36`: 17 files (1 raw `.log`/`.map`; .asm 1, .json 1, .log 1, .md 1, .py 1, .txt 12).
- `dos_clip_owner_v36`: 17 files (4 raw `.log`/`.map`; .c 4, .json 6, .log 4, .md 1, .py 2).

## Drifted diagnostic-only pins

- `build/workers/dos_ctype_sequence_v36/links/sequence-initial/rtlink610/receipt.json` `$/artifacts/4` pins `build/workers/dos_ctype_sequence_v36/links/sequence/rtlink610/LINK.LOG`; expected `44346115fa9d3593d5f26325b3786507f0a54184e8807f99222398b7f8798199`, current `eec82f3829d049167bea58b7a13463cd12997d9529688c899fd04a0d0388a0fe`.
- `build/workers/dos_ctype_sequence_v36/links/sequence-initial/rtlink610/receipt.json` `$/artifacts/5` pins `build/workers/dos_ctype_sequence_v36/links/sequence/rtlink610/PROBE.MAP`; expected `505c6669b2e2eb308e16d7a2a5560a39b6002e00deb85dba8aeebd537b0a07f0`, current `f465daa8bb22e9189db252b151061577165b98f9976783f6781f872c8516e289`.

## Other drifted pins

- `build/workers/dos_ctype_sequence_v36/links/sequence-initial/rtlink610/receipt.json` `$/input_objects/0` pins `build/workers/dos_ctype_sequence_v36/links/sequence/rtlink610/MAIN.OBJ`; expected `459e4c0604727ce1a2de6c9def07035e864a3421b27fbe9e6d22351a0b21f7c6`, current `6ead2ac7158a6d7a67ac1b6e279a289d74db15a76d6dc605a34c2e305a57399d` (binary_pin_only). The recorded pin was left unchanged.
- `build/workers/dos_ctype_sequence_v36/links/sequence-initial/rtlink610/receipt.json` `$/artifacts/6` pins `build/workers/dos_ctype_sequence_v36/links/sequence/rtlink610/PROBE.EXE`; expected `8bfa03e781f12bfa2385afb809c395d57ba55f92688e709c14a857888dc00869`, current `5123f2d3b4871f6833d2f43c2d3f8f710adc5d02bf7add8cd9aa69d9aa450ffd` (binary_pin_only). The recorded pin was left unchanged.
- `build/workers/dos_ctype_sequence_v36/links/sequence-initial/rtlink610/receipt.json` `$/runtime/artifacts/2` pins `build/workers/dos_ctype_sequence_v36/links/sequence/rtlink610/OUTPUT.TXT`; expected `83d9c6211d0adfd0e27772638b84a4299e82ac8e309ebaf2ea763505c5489c28`, current `d873e2e7d7b5473e7b9f9497e9b459717c0388082646bbf48c0c515b74d5ca27` (source_or_reference). The recorded pin was left unchanged.
- `build/workers/dos_ctype_sequence_v36/main-model-initial.json` `$/source` pins `build/workers/dos_ctype_sequence_v36/MAIN.C`; expected `853cba342b7cb48c13c5b806e9b6d2100c756dc29afad57643d51095a5686a3a`, current `a79648eae81198d3bf43694e3108ed2724f671ee73e10264acbe5989b8ebc324` (source_or_reference). The recorded pin was left unchanged.
- `build/workers/dos_ctype_sequence_v36/main-model-initial.json` `$/object` pins `build/workers/dos_ctype_sequence_v36/MAIN.OBJ`; expected `459e4c0604727ce1a2de6c9def07035e864a3421b27fbe9e6d22351a0b21f7c6`, current `6ead2ac7158a6d7a67ac1b6e279a289d74db15a76d6dc605a34c2e305a57399d` (binary_pin_only). The recorded pin was left unchanged.

The JSON inventory retains every pin occurrence, expected hash/size, current hash/size when readable, source JSON pointer, and status. Binary `.OBJ`/`.EXE`/`.LIB` and similar artifacts remain hash-pinned only; original assets are never preservation candidates.
