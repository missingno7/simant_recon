You are Codex research worker "relorder" on the DOS SimAnt reconstruction in D:\Prog\simant_recon.
Read README.md and docs/exe-format.md ("Relocation order"). Do not edit anything outside work/relorder/.

Question: what rule did the Pocket Soft RTLink/Plus linker (1991) use to order MZ relocation entries within
one object module? Once known, the gate can check relocation order (today recorded as PENDING_RTLINK_MODEL).

Established facts (verify quickly, then build on them):
- tools/exe.py parses SIMANT.EXE (x.relocs = ordered MZ relocation list; x.sections[i].relocs for overlays).
- Entries follow link order; each entry's segment field = frame of the containing module.
- For the 101 located historical runtime members (evidence/toolchain/runtime-location.json; the exact
  historical OMF objects are in C:/tools/msc-6.00/LIB/llibcr.lib and libh.lib, parse with tools/omf.py
  OmfReader.split_library/read), relocations within a member are GROUPED BY TARGET SYMBOL (DGROUP group
  fixups form a group too); inside a group the object's FIXUPP order is preserved; the group order is
  consistent with ONE global symbol order across all members (0 pairwise conflicts).
- Rejected so far: per-object EXTDEF order, definition address order, first-reference order (table or
  address), and simple hashes (sum, rotate-xor, multiplicative, PJW mod N) — see the scripts here
  (relorder.py, hashsearch.py, insertion.py, relorder_seqs.json).
- Game modules show the same grouping (e.g. root module 0093: srand, __aFchkstk..., rand, TickCount).

Explore further hypotheses, e.g.: linker symbol-table order built while reading objects in link order
(consider that library members are pulled in by library-dictionary search passes, and that RTLink may
read the libraries' dictionary hash buckets); order of PUBDEF definition during library extraction
(member extraction order may differ from placement order); MS LIB dictionary hash (block/bucket) order;
RTLink-specific hashes including the length byte / uppercase names; order of first FIXUPP reference
across the whole link. Use all available constraints (runtime members + game modules where targets are
runtime publics or DGROUP). If you find a rule, write build/workers/relorder/model.py with a function
predict(module_objects...) and a test showing it reproduces the oracle order for all runtime members and
the recovered game module root:0093 (src/root/m0093.c compiled with tools/compiler.py, profile msc600,
flags /AL /Os /Oe). Otherwise report the strongest partial result and remaining constraints.
Write build/workers/relorder/REPORT.md. Final answer <= 15 lines.
