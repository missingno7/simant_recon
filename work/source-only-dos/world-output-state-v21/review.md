# RandWorld outputs source review v21

Status: `research_only_candidate_pending_root_review`. Sources: 156 pinned paths (156/156 hash and size matches).

The batch has 16 individually routed objects. Fifteen have a complete typed scalar view and a matching raw SaveRec byte extent; `50F6:0472` is the evidence-based four-byte exception described below. Exact aliases, registered interiors, pointer escapes, declaration rows, every producer/consumer receipt, raw SaveRec rows, and source pins are recorded in `source-audit-v21.json`. Numeric address-cue and ASM token matches are included per object. No extent is inferred from neighboring addresses.

| Address | Type views | Extent | Producers | Readers | SaveRec bytes | Alias/interior/non-save escapes |
|---|---|---:|---:|---:|---:|---|
| `50F6:0200` | `extern int far fd_50F6_0200;` | 2 | 3 | 1 | 2 | fd_50F6_0200 / 0 / 0 |
| `50F6:020E` | `extern int far fd_50F6_020E;` | 2 | 3 | 1 | 2 | fd_50F6_020E / 0 / 0 |
| `50F6:0224` | `extern int far fd_50F6_0224;` | 2 | 4 | 21 | 2 | fd_50F6_0224 / 0 / 0 |
| `50F6:0242` | `extern int far fd_50F6_0242;` | 2 | 3 | 4 | 2 | fd_50F6_0242 / 0 / 0 |
| `50F6:035E` | `extern int far fd_50F6_035E;` | 2 | 4 | 3 | 2 | fd_50F6_035E / 0 / 0 |
| `50F6:036C` | `extern int far fd_50F6_036C;` | 2 | 4 | 3 | 2 | fd_50F6_036C / 0 / 0 |
| `50F6:0472` | `extern long far fd_50F6_0472;, extern unsigned long far fd_50F6_0472;` | 4 | 4 | 0 | — | fd_50F6_0472 / 0 / 0 |
| `50F6:09FA` | `extern int far fd_50F6_09FA;` | 2 | 3 | 2 | 2 | fd_50F6_09FA / 0 / 0 |
| `50F6:0A00` | `extern int far fd_50F6_0A00;` | 2 | 3 | 1 | 2 | fd_50F6_0A00 / 0 / 0 |
| `50F6:1040` | `extern int far fd_50F6_1040;` | 2 | 15 | 5 | 2 | fd_50F6_1040 / 0 / 0 |
| `50F6:1068` | `extern long far fd_50F6_1068;` | 4 | 5 | 3 | 4 | fd_50F6_1068 / 0 / 0 |
| `50F6:1082` | `extern long far fd_50F6_1082;` | 4 | 5 | 3 | 4 | fd_50F6_1082 / 0 / 0 |
| `50F6:108E` | `extern long far fd_50F6_108E;` | 4 | 5 | 3 | 4 | fd_50F6_108E / 0 / 0 |
| `50F6:10A2` | `extern long far fd_50F6_10A2;` | 4 | 5 | 3 | 4 | fd_50F6_10A2 / 0 / 0 |
| `50F6:10B2` | `extern int far fd_50F6_10B2;` | 2 | 3 | 1 | 2 | fd_50F6_10B2 / 0 / 0 |
| `50F6:10C0` | `extern int far fd_50F6_10C0;` | 2 | 3 | 1 | 2 | fd_50F6_10C0 / 0 / 0 |

## Audit outcome

Hash pins match: 156/156. ASM occurrences by identifier: 0. The coarse cue scan reports 3 matches; the explicit-hex/segment audit finds four unrelated modifier-mask spellings (one `0x0200`, three `0x0A00`) and no FAR_BSS address references.

### 50F6:0472

Both pinned declarations are complete four-byte views: `long far` and `unsigned long far`. All four observed stores (RandWorld, `o09_35F5_0D7A`, and two in EatMyFood) write zero, so the complete target-machine object bits are accounted for as zero. There are no direct reads, SaveRec byte views, address escapes, registered interiors, ASM identifier occurrences, or numeric FAR_BSS address cues. Because no observed operation distinguishes signed from unsigned interpretation, the signedness split alone does not require excluding this four-byte storage. The candidate owner uses a natural union to retain both source views. Purpose, nonzero range, lifetime, and persistence remain unknown; no SaveRec row or gameplay meaning is claimed.

The other 15 remain separate zero-initialized scalar candidates: eleven two-byte `int` views and four four-byte `long` views, each with a same-size raw SaveRec view. No common struct, historical COMDEF owner/order, or arbitrary value range is asserted. Probe success remains a separate admission condition.
