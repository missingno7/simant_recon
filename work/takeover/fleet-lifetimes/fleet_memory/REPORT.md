# Root 171C memory-helper lifetime probes

Bounded whole-module probes for `f_171C_09CC`, `f_171C_0ADC`, and
`f_171C_0FBC`. Each positive source changes one real value lifetime and keeps
the original helper calls and C types. Its paired negative source is the same
draft with that function unscaffolded and the direct-expression form retained.
“Positive” labels the hypothesis under test; it does not mean a target match.

## Results

All six sources compile. Both members of every pair keep all 57 accepted module
claims exact and reproduce `_DATA` (1,726 bytes), `CONST` (14 bytes), and
`_BSS` (18 bytes). Each `promote.py --verify-only` run refuses only because the
new target claim fails.

| Function | Negative source result | Positive lifetime form result | Remaining target residue |
|---|---|---|---|
| `f_171C_09CC` | 146 bytes | 146 bytes | Target is 144 bytes; 85 bytes differ from `+0x9`. The compiler emits the same code for both forms. |
| `f_171C_0ADC` | 260 bytes | 260 bytes | Target is 262 bytes; 212 bytes differ from `+0x5`. Both have one relocation, but its address is `0x17CDD` versus target `0x17CE1`. |
| `f_171C_0FBC` | 568 bytes | 562 bytes | Target is 566 bytes; both differ at 437 bytes from `+0x5`; relocation count is 10, with different sites. Capturing the `f_0CF4` result shortens the source by 6 bytes and reduces opcode similarity from 0.931 to 0.925. |

The 09CC positive reuses the now-dead neighbor pointer local for the far pointer
returned by `f_171C_0160`, then passes it to `f_171C_068C`. The 0ADC positive
computes the next block once and uses that actual far pointer and its paragraph
count as `f_194D_0006` arguments. The 0FBC positive stores `f_171C_0CF4(0)`'s
real Boolean result in the existing `compacted` state before branching.

## Gate transcripts

`search-*.log` contains six strict `search.py` runs. They all return the expected
mismatch status after successful compilation. `verify-*.log` contains the six
whole-module `promote.py --verify-only` results. In each verify transcript all
57 accepted peers and all three private-data contributions are exact; only the
requested helper fails. No promotion, canonical-source edit, rule-evidence
change, or global validation was run.

The paired whole-module C sources and their LF-normalized SHA-256 values are:

| Function | Negative source (SHA-256) | Positive source (SHA-256) |
|---|---|---|
| `f_171C_09CC` | `f_171C_09CC-negative.c` — `8a0ef3adbe1e9ead0193f6aaf512eaeddd9c6606bd54a528948fee59bb529fa8` | `f_171C_09CC-next_result_lifetime.c` — `7adfd2e87a1153b70b63800eb3b28762938c14ec556268ab822f4c38803f15b2` |
| `f_171C_0ADC` | `f_171C_0ADC-negative.c` — `fbd63577f149fdbdf30dbfb566431e2120cbe4bb8102d6f9db44ddbc26c54003` | `f_171C_0ADC-next_argument_lifetime.c` — `d1e674e33b5709822100d6c30f2a6454bfa575eea27e6c9fdbd878bec2d6f2b2` |
| `f_171C_0FBC` | `f_171C_0FBC-negative.c` — `0c2a06c60bd91da62ea3c23112f6592bfda34ef9a7e06e5b4dcb9e36b86e4078` | `f_171C_0FBC-compaction_result_lifetime.c` — `29f2338b4345b64f4065cf5a9ddbcea780a7314623c0f6ab854cd4dde6e770cd` |

`run_controls.py` SHA-256: `aa1e585c32205eb6be54481d24abd097818d62d1f5f0660bec23cc1e83a5aa8a`.
`memory.c` seed SHA-256: `7decbec511e93ca79a5b4238561aa24e3fb1c794506f337af6d3aa11506bbfac`.
`search-results.json` SHA-256: `66bff3647f7f4a8e90cdd57396f8b4af5c2216c88dc88a6d2830ff507fa78a9d`.

The search JSON keeps the compiler results and scores. Full mismatch disassembly,
including the differing relocation-site lists for 0ADC and 0FBC, is retained in
the corresponding `search-*.log` files.
