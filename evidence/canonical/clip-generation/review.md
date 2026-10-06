# Clip generation boundary package

**Scope:** supported-domain clip-generation boundary for `graphics-computed-copy-layout`. This package supports preservation of the selected overflow `Punt` call for the checked producers. It does not establish that an overflow is reachable in shipped play, and it does not close the canonical gate by itself.

## Recomputed window-stack bound

`probe.py` reruns the shipped-resource geometry calculation in `bound.py` and the all-C opener/callback census in `census.py`. It reuses the existing database/LZSS decoder and pins deterministic results in `facts.json`. The decoded census is 34 window resource IDs; the reviewed supported catalog permits at most nine simultaneous windows: persistent IDs `{0,1,5,18,19,21,25}` plus at most two transient windows.

Within [bound-proof.md](bound-proof.md)'s premises—successful pinned VGA8 resource acquisition, the reviewed nominal supported window/event/save domain, the conservative lifetime catalog, nonempty normalized window rectangles, and ordinary first-fatal `Punt` behavior—the source-order cut bound is `B(n)=2n^2+n+1`. Thus `f_1E57_038E` has C097 <=137, C098 <=137, and C099 <=172 generated records, with at most 173 including the sentinel. These checks occur before their destination emission. This is only the window-stack part of the generation argument.

## Producer bounds before the check

The clip-owner induction supplies `M <= 255` accepted current records plus sentinel before the first `Punt`. The source-token check and helper body establish the following generation ceilings; they do not assume rectangle outputs are disjoint.

| Producer | Records before its check | Diagnostic call |
|---|---:|---|
| `clip_SubInclude` | `M <= 255` | `CL074:Temp clip overflow in SubInclude` |
| `f_1E57_08F5`, checked current-list branch | `2M <= 510` | `CL074:Temp clip overflow in SubInclude` |
| `clip_SubExclude` | `4M <= 1020` | `CL074:Temp clip overflow in SubExclude` |
| `f_1E57_0C2D` | `5M <= 1275` | `CL174:Temp clip overflow in SubExclude` |

`f_1E57_08F5` also has a separate unchecked null-current-list branch. Its only canonical caller is `f_0250_5058`, which supplies two rectangles plus a sentinel. Arbitrary direct entry with a longer list is excluded.

The current-list sentinel controls iteration independently of the caller rectangle values. `p` advances only through `f_1D8E_003F` output; that helper emits at most four outside records and does not retreat the output pointer. With `M=255`, the maximum 5M output has 1,275 records, a 10,200-byte record span. Its sentinel top word starts at temporary offset 10,202 and ends at 10,204; the last written byte is 10,203. The C pointer difference is 1,275 records, below the signed 16-bit limit, and neither that difference nor the far-pointer offset wraps.

The allocator token checks bind the temporary to the conventional arena obtained by `_dos_allocmem` in `f_171C_07BE`. `f_171C_125C` returns payload at normalized offset zero after its 32-byte header; the handle table precedes the block arena. The EMS mapping endpoint is calculated as `F000 + 1 + 0xBF8` paragraphs in the maximum-frame calculation; adding the 10,204-byte write envelope remains below 1 MiB. The ordinary post-image DOS allocation premise separates the forward envelope from the loaded current list (`fd_50F6_3C14`), screen rect (`g_5A9C`), caller stack, executing code/return addresses, and Punt guard. Any alternate link or allocator placement must retain the same explicit range-separation proof.

## Contract and limits

The admitted wording is: **same overflow diagnostic call selected; counts, generated rectangles and heap state after capacity exhaustion are not claimed equivalent.** Each checked producer retains its own existing diagnostic branch; these diagnostics pass no count argument. Successful prefixes retain their source algorithms. The window-stack branch is separately bounded below capacity.

Exclude the physical effects of out-of-temporary stores from the first capacity-exceeding store, including effects before `Punt` entry: adjacent heap headers and payloads, animation objects and rectangles, later heap reads, and intervening asynchronous consumers of damaged heap data. Exact producer instructions do not establish these effects as equivalent, and the contract does not promise arbitrary post-corruption machine progress.

Also exclude diagnostic formatting/drawing, nested or returning `Punt`, heap dumping/cleanup, successful completion of exit, and subsequent game continuation. The real Punt guard and all source behavior remain intact. Prior-Punt, corrupt, or malformed helper states are excluded separately from source-produced geometry that first crosses capacity.

The claim does not promise a particular overflow count, generated rectangle contents, heap adjacency, printed fatal text, destination copy after a returning `Punt`, or completed abort. The clip-owner's 256/guard-1 control remains a negative contrast: original `Punt` returns and the destination copy writes eight bytes beyond its owner.

## Retained controls

Every probe recomputes, without trusting saved result JSON:

* Original `f_1E57_038E` replay for the synthetic 29-window control (225 visible rectangles, completion) and 31-window control (256 records, sentinel store at displacement 2050, then C097 Punt entry).
* `animation-fixture.json` contains only the synthetic 255-record incoming list and its excluded rectangle. The probe reruns this single `clip_SubExclude` call from original instructions; it reaches `CL074` at 256 records for the reviewed same-anchor loop-2 `swarm-old-1-1` geometry. The ordinary-play RNG/state prefix remains unknown.
* Original clip-owner 255-record positive, 256-record first-Punt boundary, and 256-record returning-Punt destination overrun control.

## Independent review

The independent verdict was **SUFFICIENT-WITH-CHANGES**: the nine-window stack bound was sound in its stated domain, while the broader clip claim had to preserve only overflow-call selection. Its required edits are incorporated here: retain the `M/2M/4M/5M` table and two-record unchecked `08F5` branch; include offset-zero allocator provenance, finite traversal and the nonwrapping 10,204-byte envelope with conventional/EMS read-range separation; exclude heap corruption and all cleanup or continuation after capacity crossing; and carry both destination-owner and temporary-overflow boundaries with the original controls. No overflow count, generated rectangles, heap state, or fatal-path completion is claimed equivalent.

## Integration handoff

The supervisor's authoritative closure ledger needs both boundaries together: fixed destination ownership through the first `Punt` entry, and the separately limited temporary-overflow failure behavior above. Retain these controls with that ledger change. This worker package is not itself canonical evidence and does not modify `src/`, `evidence/`, or `tests/`.
