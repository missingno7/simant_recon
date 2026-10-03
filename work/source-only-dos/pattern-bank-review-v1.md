# S00 pattern-bank ownership and symbolic address review

The three `SS:[SI+41D0h]` reads belong to the sixteen consecutive 16-byte
pattern records already reconstructed in `src/root/m1B4E.asm:60`. The generated
source adds `_g_41D0` as a zero-byte public at `_DATA:04B0`, sixteen bytes after
the independent colour-map object `_g_41C0`. The existing `_g_4220` public is an
interior view eighty bytes into the 256-byte bank. This does not enlarge the
colour-map object's extent or create initialized storage.

The complete five-word callee computes
`SI = 16*(mode & 15) + ((top*2) & 7)`. Every branch reloads that word before its
table read. The phase is one of 0, 2, 4, 6, and each loop's `(SI+2) & 00F7h`
preserves the selected record while cycling those phases. This includes the
zero-count LOOP wrap. The greatest possible read offset is 246, within the
256-byte source bank. The four in-tree `g_9138` calls all select record zero;
the proof also covers the callee's full selector domain. Dispatch slot four
reaches this implementation only on the no-clip path; the overlay path returns
without executing its local reads.

The neighbouring colour-map copy paths write exactly eight words. Existing
S01 references through `_g_4220` are loads. The symbolic conversion preserves
the data, so this review requires no assumption that arbitrary game pointers
can never write the bank. It makes no new immutability claim.

Fresh whole-module MASM controls preserve the owner's bytes, extents, groups,
externals and existing publics/fixups, adding only its public. The S00 control
first derives the admitted symbolic-source binding and the 64 admitted external
SS-frame corrections. The next layer changes only three two-byte displacement
fields and adds external OFFSET16 DGROUP fixups at S00B_TEXT offsets 02A9,
030B and 0352. Every previous relocation retains its order and identity.
The new packet pins both preceding packets and the entire effective control
binding; it does not revise either frozen packet.

The reproducible `pattern-bank-probe.py` uses a test-owned 256-byte formula bank
under actual MSC startup. Both RTLink 4.00 and 6.10 pass all 256 symbolic reads
with DS=SS=DGROUP and a nonzero `_DATA` group displacement. A segment frame and
a one-byte base error fail separately. No original executable is a probe or
build input. These are source/layout proofs, not a game execution claim.

This closes three numeric addresses. It does not reduce the 113-byte data
inventory, recover the ten local driver frames or the clip-pointer segment
pair, or complete the wider address audit. Historical producing-TU identity
and original COMDEF ordering are not claimed.
