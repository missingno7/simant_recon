# Decoder control addendum v34a

**Append-only follow-up.** The previously reported v34 review and JSON remain untouched. This addendum corrects the ring initialization model and checks whether it affects the SHARED MENU object 0 result.

`DBRecall` finds SHARED kind-6 object 0 with entry flags `0x01`: the packed bit is set and the special bit `0x04` is clear. Its record header gives `size=455`. Following the actual branch, the decoder reads a two-byte expanded-size prefix (`514`) and receives `size-2 = 453` compressed bytes. The stream consumes all 453 bytes.

`src/root/m1B05.asm` allocates a zero-initialized 4,113-byte ring region, but each decoder initialization fills only indexes 0 through 4,077 with spaces. The 4 KiB masked ring indexes 4,078 through 4,095 retain their prior contents until this decode writes them. The control ran the same pinned stream with a fresh zero tail, an all-space tail, and a deterministic random tail. It tracked every read of those 18 slots before the current decode's first write.

All variants consumed the same input, made no pre-write reads from the retained tail, and produced the same 514-byte expanded payload hash, five-title sentinel count, and item-table counts 8, 7, 8, 6, 6. The expanded hash matches the v34 review. The observed menu result is independent of the previous contents of the final 18 ring slots.

The JSON pins the source files, strict-effective FindIndex review, v34 receipt, and DAT/NDX hashes. It stores hashes and structural counts only; no executable or asset bytes or decoded strings are retained.
