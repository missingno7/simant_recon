# Historical DGROUP layout debt (30 bytes)

Decision (project owner, 2026-10-06): the five residual DGROUP ranges below are
accepted as documented **historical layout debt**. They no longer block the
canonical DOS link. This is a scope decision, not a proof: the bytes remain
unattributed, and no owner, padding, global, initializer or original byte is
added to canonical source.

| ID | Original DGROUP range | Bytes | Original contents |
| --- | --- | ---: | --- |
| `dgroup_56fe` | `[56FE,5702)` | 4 | zero |
| `dgroup_5a28` | `[5A28,5A2A)` | 2 | zero |
| `dgroup_5a96` | `[5A96,5A97)` + `[5A98,5A9C)` | 5 | partly typed shared UI region |
| `dgroup_60b0` | `[60B0,60C2)` | 18 | hot-box-shaped record with a real callback relocation, no inbound reference |
| `common_tail_overlap_3` | `[8B9D,8B9E)` | 1 | loaded mastering-tail byte `72h`; CRT clearing starts at `8B9E` |

## What the canonical build claims

* Every storage symbol has a canonical owner; no provisional storage provider
  and no original executable-byte fallback are used.
* Functional equivalence is claimed only within the documented supported
  execution domain (`src/program.json:dos.supported_execution_domain`) and is
  evidenced by deterministic original-vs-reconstructed acceptance
  (`dos/acceptance.py`), not by a proof.
* **Physical DGROUP layout equivalence is not claimed.** The reconstruction
  keeps each TU contribution's internal offsets but not the original
  contribution order, and uninitialized globals live in BSS. The 30 bytes have
  no counterpart address in the reconstruction.

## Evidence gathered before the decision

* No relocation or immediate operand addresses any of the ranges.
* The only symbol-indexed site overlapping `[60B0,60BE)` is the small-font fold
  table (`[bx+_g_5FBE]`, `src/root/m1FBD.asm`); display mode 8 never installs
  the small font, so this is outside the supported domain.
* The `g_610C[g_5A97]` selector alias is excluded in mode 8; hot-box queue
  insertions come only from `g_6004`/`g_6016`/`g_603A`; the 17 registered
  indirect dispatch edges are safe; 500 direct neighbour accesses show no
  residual witness.
* A 640 s deterministic game recorded no game access to any range (corroboration
  only).

## Caveat (open, not waived)

A complete computed-pointer exclusion was not established: a whole-program
pointer-root analysis leaves most dynamic accesses at unknown root, and a global
stack floor above `8B9E` is not bounded (window-lock recursion, chained BIOS/DOS
interrupt stack use). Any supported-domain out-of-bounds access that reads these
bytes, or more generally crosses a TU contribution boundary, could behave
differently in the reconstruction. Reopen the matching entry if a concrete
behavioral difference is observed.
