# `fd_50F6_0EB6` owner candidate — v22

This is an unreviewed source-functional storage candidate for one natural
`int far fd_50F6_0EB6[32]` object. The provider is data-only and emits a
64-byte FAR common under MSC 6.00AX `/AL /Os /Gs`; its OMF records 32 elements
of two bytes each. It does not claim the historical COMDEF-producing TU,
object order, or original absolute placement.

The pinned inventory covers 127 canonical manifest sources and the 29
confirmed strict-effective source paths. The exact symbol occurs 21 times,
all in [root `m0BE8.c` / `CountAnts`](../../src/root/m0BE8.c:58): one
`int far[32]` extern, the 0–31 zero loop, byte-list bucket increments,
reductions into the separately owned `0AEC`/`0AFA` arrays, and their uses.
The scan found no other named source views, numeric address spellings,
address-taking/SaveRec escapes, or registered interior names within the
candidate 64-byte interval. The registered target row itself grounds
`50F6:0EB6` as a 32-word counter array.

The source-derived index expressions do not all carry the same domain proof.
Nonzero `unsigned char` list values become indices 0–31 after `v >> 3`.
The two expressions based on signed `fd_50F6_04C2` have no bound proven by this
storage audit. An invalid index would not change the candidate's declared
type or extent, and this candidate does not establish safety for malformed
state.

The reproducible probe is [ant-histogram-owner-probe-v22.py](ant-histogram-owner-probe-v22.py),
with the candidate definition in [ant-class-histogram.c](providers/ant-class-histogram.c).
Its fresh-run receipt is
`build/workers/dos_ant_histogram_v22/run-20261004T031319Z-ca15a6bce736/candidate-receipt.json`
(SHA-256 `6f45d2d9b928e98a2dbf27d7c872db8d879c78cad08af38d3e5ea7d8dfd03c18`).
All eight test-owned cases passed under RTLink 4.00 and 6.10: all 32 CRT-zero
words, signed word access and all raw bytes; relative wrong-base detection;
initialized-owner rejection; and an unsigned-consumer type contrast. OMF
controls distinguish 31 words and 64 bytes from the expected 32 words. OMF
does not encode `int` versus `unsigned int`, so signedness remains source-pinned.
The short owner is rejected by its 62-byte OMF common without a runtime
overrun test; no adjacent guard or layout assumption is used.

No original pre-main value, historical initialization, original owner order,
or historical layout is asserted. The candidate receipt is `root_reviewed: false`.
