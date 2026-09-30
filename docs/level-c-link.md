# Level (c): an independent historical link — plan and honest assessment

Goal: build `SIMANT.EXE` from our objects, the pinned MSC 6.00 libraries and a recorded link
script, with **no byte of the original**. The original linker, Pocket Soft RTLink/Plus
(1990/91), is not available.

## 1. What a linker model must produce

The rows follow `DESIGN.md` §7 (everything the hybrid takes today).

| Output | Size today | Derivable without RTLink? | Status |
|---|---:|---|---|
| Code/data bytes of our objects at their addresses | 369,105 own bytes | yes, if the **addresses** come from a link script (below) | addresses come from the manifest today (grounded in the original) |
| Segment layout: object order, word/paragraph alignment, frames, DOSSEG class order, S27 far-data order, DGROUP order, FAR_BSS communal order | — | yes in principle: MS-LINK-compatible rules | not modelled; open: FAR_BSS order (first appearance), DGROUP class sequence beyond MSG |
| Overlay structure: section assignment, 4 areas, load segments | 27 sections | yes, if the link script records it (it is a *source* artefact, like a makefile) | only implicit in the manifest units |
| Relocation entry values | 7,241 / 9,075 entries | yes (site + frame); DGROUP frames follow from the layout | done for own sites |
| Relocation table order: frames ascending; grouping by target symbol per frame; (object, FIXUPP) order inside a group | — | yes | the model is verified on 3,179 / 3,252 own entries in complete frames |
| **Order of the groups** (one program-wide RTLink symbol order) | every table | **no** (see §3) | blocked |
| Vector list: which procedures get a vector | 136 | largely: procedures called far from another overlay section (our fixups give that set) | 127 / 136 targets are own claims; rule not yet tested |
| **Vector order** | 136 | **no**: not sorted, not first reference, not the relocation-group order | blocked |
| Vector entry format `E8 rel16 / EA off seg / dw section` | 1,360 bytes | yes, except `rel16`, which points at a manager routine (2CFF:0529) | needs the manager |
| Section table (28 × 18 bytes + count) | 510 bytes | mostly: load_seg, file_para, mem_paras, reloc_count and file_paras follow from the layout; id = index+2; w6 = FFFF | open: `w1` = 0x2576 (manager-internal); flags 0x500 (S00) / 0x400 / 0x100 rule |
| **RTLink manager** code/data | 15,131 bytes + 40 relocation entries | **no**: third-party runtime (Pocket Soft), like LLIBCR | debt unless a pinned RTLink/Plus manager object is obtained |
| MZ header | 30 bytes | yes from the layout (sizes, count, min alloc, SS:SP); CS:IP = manager entry | needs the manager's entry offset |
| 16 bytes at 29F4C | 16 | probably yes (LINK `/DOSSEG` `_TEXT` null area) | needs a recorded rule/probe |
| Common tail (BIOS fragment) | 256 | **no**: a mastering artefact, identical in INFO.EXE and INSTALL.EXE; not linker output | permanent external artefact. Level (c) should target the file *without* it and document the append step. |
| Unrecovered code/data | 40,068 code + 23,785 data | via the ordinary work loop | ongoing |

## 2. Candidate RTLink/Plus binaries: legal and provenance status

Nothing RTLink-related is in `C:\tools` (catalog checked).

1. **Pocket Soft, Inc.** (Houston, TX; today known for RTPatch) is the rights holder.
   Asking for a historical RTLink/Plus 1990–91 distribution (linker + manager library) or
   written permission is the only route with clean provenance. **Recommended first step.**
   The user decides whether to contact them.
2. **RTLink for Clipper** (`RTLINK.EXE` shipped with Nantucket/CA Clipper 5.0x, 1990–92).
   A copy is known in a third-party GitHub repository (docs/next-steps.md). It was **not
   downloaded**: its provenance is unverified and redistribution by that repository is very
   likely unlicensed. The user decides.
   * If used, store it in `C:\tools\` with a provenance record, pin its hash in
     `layout/toolchain.json`, and never commit it.
   * Technical caveat: it is a Clipper-bundled edition. Its overlay manager and possibly its
     version differ from RTLink/Plus, so it can serve as an *experimental instrument*: does
     its symbol order match the runtime-only constraints, and is its section table format
     the same? It is not a proven historical tool.
   * Its manager bytes would not be accepted as SimAnt's manager unless they match exactly.
3. **Other executables linked with RTLink/Plus** (e.g. other 1990–92 DOS titles carrying
   the `.RTLink CACHE` banner) could show that the manager is library code: compare the
   manager region across executables. This is a diagnostic only; it gives no object file.
4. **Clean-room re-implementation** of the RTLink layout rules (the `link-model` below) is
   fully legitimate. It can reproduce everything except the group/vector orders and the
   manager.

## 3. The relocation-group order: what we know now

* Constraints from own entries only: 115 frame units, 285,399 ordered pairs of global
  groups, only **24 contradictory pairs** (2 units with non-contiguous groups). One
  program-wide order explains almost everything.
* Rejected in this session (`exp_symbol_order.py`, `logs/exp_symbol_order.log`), using our
  123 freshly compiled objects plus the runtime members:
  * symbol-table insertion order, reading objects in link order (root by address, overlays
    by section, then libraries, or libraries first);
  * the same with names in OMF record order, EXTDEFs first, or PUBDEFs first.
  * Every variant satisfies **48.6 %**, i.e. chance level; alphabetical scores 49.9 %.
* Earlier (build/workers/relorder), on runtime members with true names: definition address,
  first reference, per-object EXTDEF order and simple name hashes were all rejected.
* Near-random agreement with every structural order, plus near-perfect consistency, points
  to **iteration over a hash table keyed by symbol name**. That has a hard consequence:
  * The order depends on the *original* names. Our placeholder names (`fd_50F6_0226`,
    `f_29F0_0038`) and any Win16-derived name that differs from the DOS original would
    give a different order, even with the genuine linker.
  * So a byte-identical relocation table needs either the true names (unknowable for most
    statics/globals) or a recorded symbol order.
  * Conversely, once the hash function is known, the table order becomes **evidence about
    original names**: a cheap membership test for name hypotheses.

Next experiments, all oracle-read-only analysis:
* **E3**: learn the hash from runtime-only frames (true library names). Test two-level
  keys (bucket = h(name) mod P, then insertion order within a bucket) for MS-LIB-style
  dictionary hashes, rotate/xor over upper-cased names, with and without the length
  byte, for P up to 1024. If a family fits all runtime constraints, test it on
  Win16-confirmed game names.
* **E4 — layout closure**: record a link script (`layout/link.rsp` proposal: root object
  order, SECTION/AREA statements, library order). Check that alignment rules reproduce
  every accepted module start from the previous module's end. This makes the addresses of
  level (a) *derived* instead of *given*, with no linker needed.
* **E5 — vector set**: predict the vector set from our fixups (far calls into another
  overlay section) and compare it with the 136 vectors.

## 4. What an honest level (c) can be

* **(c-core)** is achievable without RTLink: every own code/data byte, every relocation
  value, the frame/group structure, the section-table fields and the MZ header fields
  derived from a recorded link script. It is proven by comparison, and the only oracle use
  is comparison. The pieces still unknown are *reported as unknown* rather than filled:
  group order, vector order, manager.
* **(c-full)**, a byte-identical file with no original bytes, needs **all** of:
  1. the RTLink/Plus manager object, legally obtained and pinned;
  2. the RTLink symbol order rule, and names that reproduce it (or a recorded order,
     which is an input derived from the original and must then be labelled level (b+),
     not (c));
  3. the vector order rule;
  4. all remaining code and data recovered;
  5. the mastering tail treated as a declared external artefact.
* **Assessment.** (c-core) is realistic and worth building next as `tools/link.py --model`.
  (c-full) is unlikely without the genuine RTLink/Plus distribution. Even with it, relocation
  order may be unreachable for symbols whose original names cannot be recovered. The
  manager (≈ 3.4 % of the file) stays **third-party debt** in every scenario without the
  distribution. The project should report (a), (b) and (c-core) side by side and never
  collapse them into one number.

## Findings with real RTLink linkers (worker rtlink, 2026-09-30)

Tools (C:\tools, provenance.json each): .RTLink/Plus 6.10 (1993; archive.org BBS dump "prog21-29",
warez-scene copy, research instrument only, kept outside Git), .RTLink for Clipper 3.11 and 3.13
(Clipper 5.0 / 5.01 from WinWorld, SHA-512 verified). The Dec 1991 RTLink/Plus (4.x/5.0) that
linked SIMANT.EXE was not found; the clean route is Pocket Soft (today RTPatch).

* **Relocation group order is not a hash of names.** Entries are grouped per frame by target
  symbol; groups are ordered by a 101-bucket hash of the target's internal record *handle*
  (most recently inserted first). The handle is the symbol record's creation index while objects
  are read in command-line order: PUBDEF creates it at once, an external at its first FIXUPP
  reference, an unreferenced declared external at the end of its object. The chain position is
  that of the first relocating fixup. Names, EXTDEF order, unreferenced externals, site
  addresses, fixup counts and extra segments do not matter. The bucket function differs between
  versions (3.11 = 3.13, 6.10 differs); SimAnt's order matches none of them (<= 66%), so level
  (c) needs the exact 1991 linker and the complete object set in the original command-line order.
  This refutes the "hash of original names" hypothesis above.
* **Vectors**: `ALWAYS` lists create vectors first, in listed order (the 18 up-front vectors of
  VEC-1; the original list happened to be alphabetical); all others follow first reference.
  6.10 vectors every cross-unit reference to an overlay symbol, including data pointers, so the
  original's direct references into S00-S03 require `NEVER` directives. Vector entry format is
  identical.
* **Manager**: SIMANT's is the RELOAD variant (`$$RTLOVLINITR`, reload stack 0x1800 =
  `RELOAD FAR 400`) plus the real cache modules, in 6.10's pull-in order for `RELOAD FAR` + `CACHE`;
  no available version is byte-identical (masked similarity 20-55% per module to 6.10). Section
  record words: 3-byte file position + flags byte (0x05 PRELOAD+CACHE, 0x04 CACHE, 0x01 PRELOAD).
* **Trial link t3** (6.10; `python tools/rtlink.py`, build/rtlink/t3): 83/85 complete modules
  land at their accepted addresses (exceptions: root:19A9 accepted at odd 0x19A95 while its MSC
  code segment is WORD aligned; root:2CFB MEMHOOK_TEXT placed after the runtime _TEXT in the
  original, i.e. read after the library search); the section table's relative load segments,
  flags, ids and memory sizes match; the 13 overlay sections built only from real objects have
  identical relocation sets, frames and within-group order and all 63,102 non-fixup bytes
  identical. Script inputs read from the original (ALWAYS/NEVER lists, areas, PRELOAD/RELOAD)
  are labelled as such in build/workers/rtlink/linkscripts/SIMANT_derived.lnk.
