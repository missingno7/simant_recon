# fdata EXTDEF selection census v38

**Status: `ROOT_REVIEW_PENDING`.**

The pinned source-only report contains 188 translation units; every one of its object SHA-256 pins was verified before parsing.
Build report SHA-256: `0edcb3285074975704645520158975bd20a32a7cae542127812b54a9e78cffbf`. Expected parent commit: `e4227d5`.

## Result

Stock `fdata.asm` publics: `__fheap`.
Application EXTDEF matches: 0. Application live external fixup matches: 0.

No application object declares an OMF EXTDEF matching a public defined by stock `fdata.asm`. Therefore an unused app-side assembler `EXTRN __fheap` (or another `fdata.asm` public) is absent from this 188-object build and cannot account for the partial link’s `fdata.asm` selection. No conditional link controls were run because the required candidate does not exist.

## Pinned stock CRT dependency chain

| Member | Publics | Live external fixups |
|---|---|---|
| `dos\stdalloc.asm` | __myalloc | __amblksiz, _malloc, __amblksiz, __amsg_exit |
| `malloc.asm` | _malloc | __fmalloc |
| `fmalloc.asm` | __ffree, __fmalloc | __fheap, __searchseg, __fheap, __fheap, __fheap, __fheap, __growseg, __growseg, __searchseg, __fheap, __newseg, __searchseg, __fheap, __fheap |
| `fdata.asm` | __fheap | — |

The natural CRT chain is `stdalloc.asm → malloc.asm → fmalloc.asm → fdata.asm`, with live edges `_malloc`, `__fmalloc`, and `__fheap` respectively. This chain describes ordinary runtime dependencies; the census found no matching fdata public in any app object.

## Scope

This is a negative result for app-object EXTDEF-driven extraction in the pinned 188-object build. It does not identify the cause of the earlier 186-object partial-link selection, and it says nothing about historical `DGROUP:79F0` placement. No linker control was run and no generated executable was run.

Machine-readable per-object EXTDEF and live-fixup inventories are in [extdef-census-v38.json](extdef-census-v38.json).
