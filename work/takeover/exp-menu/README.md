# DoExpMenu complete TU (2026-09-30)

accepted.c owns all 744 code bytes and both private data contributions in S05:3663.
Profile: msc600ax /AL /Os /Oe /Og /Zi. _DATA: 55B3:23DE (106 bytes);
CONST: 55B3:8450 (six bytes). Code extent: 36634:3691C.

The previous S05:35F5 TU ends at 36634, after DoTab. The paragraph frame base
36630 is therefore four bytes before this object's actual WORD-aligned start.
CODEALIGN-1 and the verified neighboring extent ground this complete boundary;
no unknown prefix, byte capsule or trimmed extent was accepted.

BYTE-1 proves the final source-level distinction: reading the event word's low
byte through an unsigned-char lvalue produces CMP CX,AX. Masking the unsigned
word produces CMP AX,CX. Both controls produce the same loads and total length,
and their values agree on the historical little-endian target. The accepted cast
is relative to the local field, not an absolute-address cast or an object patch.
Declaration/statement ordering remains explicitly layout-inferred. The reviewed
multi-anchor naming decision is in evidence/cross_version/decisions.json.

The whole TU verifies exactly, including grouped cross-function relocation order.
Promotion and compiler-control transcripts are retained here. word_mask.c is the
one-byte negative contrast and is not accepted.
