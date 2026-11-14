# Uninitialised automatic storage in the native projection

This is a **partial class review**. The main stamp is repaired on DOS evidence.
The checked census deliberately retains unadjudicated candidates. Passing its
regression proves inventory coverage against this baseline, not that every
candidate is harmless or every DOS automatic-storage input has been recovered.
Canonical `src/`, declarations, layout and original binaries were not changed.

## main's first Yard stamp

`stamp-origin.json` records independent original and canonical startup runs.
`startup-writer.json` retains the CRT instructions, the pinned DOSBox source
excerpt responsible for the final write, and the current canonical main object's
profile/hash. The earlier `build/workers/quiet-inputs/main-stamp-evidence.json`
records the same bytes still present at the first simulation entry. No original
code/data bytes are included in a native runtime initializer or runtime resource.

At the final descriptor-status `INT 21h`, the original CRT has AX=4400h, BX=0,
CX=7FE2h, SS=5DD7h, SP=A4CEh. Hardware pushes six bytes. The DOSBox DOS handler
saves BX at callback SP-16 = A4B8h and CX at callback SP-14 = A4BAh. Those two
words become main BP-0Ah/BP-8 after the CRT's ten argument bytes, far call and
saved BP. The low word was 1 immediately before the last interrupt (the previous
descriptor number); it becomes 0 across that interrupt. The high word already
contains 7FE2h from previous iterations and is saved again. These host DOS writes
are outside the CPU-instruction-only watch, explaining the misleading earlier
last logged CPU writer.

The CRT scans the environment for `_C_FILE_INFO=`. On the last environment
string `BLASTER=A220 I7 D1 H5 P330 T6`, its first comparison mismatches and consumes
one character. REPNE SCASB starts at CX=7FFFh and consumes the remaining 28
characters and NUL: 7FFFh-29 = 7FE2h. The descriptor loop does not change CX.
The original and canonical CRT have different linked addresses/SS but leave the
same two words. This is neither a far-pointer segment nor a canonical C store.

An extra final variable `SIMANT_UNINIT=abc` changes the high word to 7FEEh,
including a one-paragraph load-address change. Memory size 16 MB versus 8 MB
leaves 7FE2h. Thus **the value depends on the DOS environment**. The selected
native input is explicitly the locked reference environment's 0x7FE20000,
signed 2145517568: a large positive value above the observed first TickCount.
This selects the first reset arm and skips the delay-comparison TickCount.
There is no claim of a universal value for arbitrary DOS versions/environments,
`_C_FILE_INFO` settings or long-running tick domains.

The typed frontend inserts `int32_t stamp = 2145517568L` once on entry to the
converted main. Normal subsequent WaitedEnough writes remain canonical. The
per-TU `automatic_storage` receipt pins the source and observation receipt and
names the reference-environment choice. Source/anchor/evidence drift rejects
conversion. The adapter has an explicit disabled control. A regression compiles
the canonical WaitedEnough body at O0/O2 with positive reference residue versus
the concretely observed negative native residue -1373232089: two versus three
TickCount calls, including the distinct short-circuit arm.

## Census method and boundaries

`census.json` has two independent AST inventories: all 171 canonical C TUs,
and all 170 converted pre-expression TUs actually compiled by this build. It
also retains every automatic declaration and canonical source digest. Included
headers are expanded as in the existing evaluation-order census. Inline ASM is
removed only for C parsing; its outputs must be reviewed separately.

The conservative CFG uses explicit edges for loops, switch fallthrough, labels,
gotos, break/continue and returns. Member/element facts stay separate; changing
an index invalidates symbolic element facts. A local address/array escape is a
candidate even when GCC cannot see into the callee. Unknown calls do not become
initializers. The following reviewed complete-object output summaries are used:

| Callee | Output / guarantee | Canonical evidence |
|---|---|---|
| win_GetObjRect | argument 1, full Rect | src/window/object_geometry.c: complete `*rect` copy |
| win_GetObjSize | argument 1, both Point fields | src/window/object_attributes.c |
| win_get_obj_layout_rect | argument 1, full Rect | src/window/object_attributes.c: `*r` copy |
| gr_BitMapSize | argument 0, both size words, including failure | src/window/text_bitmap_helpers.c |
| GetMousePos | argument 0, x/y | src/window/menu_helpers.c |
| win_GetEvent | argument 0, accepted event only on success | src/window/events.c (registered win_GetEvent owner; original instructions in function-evidence) |
| input_pop_event | output-address exposure only; return is remaining count, not Boolean success | src/platform/input_timer.asm |
| GetAntIndex | arguments 2..6 only on nonzero return | src/simulation/life_tiles.c: all three list branches |

The output-address classification means the address exposure itself does not
read old contents. It never blesses subsequent reads after a failed output call.
CRT formatting/copy destination exposures are likewise distinguished from
source/range reads; initialized string prefixes are not treated as initialized
array tails. The successful decompression domain excludes malformed streams.

GCC checks the final generated C with `-Wuninitialized -Wmaybe-uninitialized`
at O0 (the actual port build has no `-O` option) and O2 (diagnostic contrast).
All 340 compilations pass; 46 warning emissions include repeated inline sites.
The exact compiler identity, omitted adapted C owner, warning inventory and
individual warning-to-site reviews are recorded. New warnings, candidate reads,
address escapes, declarations or source changes reject the checked baseline.
`--candidates-only` produces scratch data and never updates classifications.
Parser line coordinates include expanded headers; source/function/expression identities
are authoritative, rather than interpreting them as original physical source lines.

## Confirmed effectful sites

| Function / object | Result |
|---|---|
| ui_edit_text_field / lastTick | read-with-effect-open: BP-8..BP-5 is compared with TickCount at S09:36EE:01A8/01AD before the first store at 01B7/01BA. Entry history determines its value; the bounded new-game-save raw input observation did not reach this PC. No all-caller residue contract established. |
| PopUpInfoWindow / frame | read-with-effect-open: If res_load_with_alloc_type(rez,10,1) fails, frame and bits remain unassigned but are passed to gfx_restore_and_free_rect. This resource-failure path depends on caller stack history; no single DOS value or shipped successful-path discrepancy established. |
| PopUpInfoWindow / bits | read-with-effect-open: If res_load_with_alloc_type(rez,10,1) fails, frame and bits remain unassigned but are passed to gfx_restore_and_free_rect. This resource-failure path depends on caller stack history; no single DOS value or shipped successful-path discrepancy established. |
| initStuff / resourceError | read-with-effect-open: Unassigned automatic word is printed only after db_LoadObject(1000,9) fails. DOS value depends on the failing caller history; shipped successful startup does not enter that branch. Retained explicitly open for resource-failure diagnostics. |
| dos_game_main / stamp | read-with-effect-fixed: Final CRT INT 21h saves BX=0 and environment-scan CX=7FE2h at future main BP-0Ah; explicit reference value 2145517568. See stamp-origin.json and review.md. |
| win_PrintTextInRect / len | read-with-effect-open: len is assigned only when first<=line, then text+=len runs unconditionally. A skipped leading line (first>line) consumes original stack residue. No single value established across caller/scroll histories; original instructions retained in function-evidence.json. |
| snd_probe_dsp_reset_ack / c | read-with-effect-open: Original root:29B8:003D tests byte BP-1 before store at 0050; bit 7 controls status-port polling. The bounded shipped-CFG startup did not hit the read. Other DSP probing paths need their caller-frame residue; no arbitrary zero supplied. |

The raw-input new-game-save probe exited without hitting the lastTick read PC;
the shipped-CFG startup probe did not hit the DSP read. Both observations and
logs remain under `build/workers/uninit/`. A no-hit is not unreachability proof.
The confirmed open reads require path/caller-specific DOS value evidence before
any further conversion initializer. The remaining open candidate/domain rows
may contain additional effectful reads: this review does not call their triage
complete. Fatal-Punt false positives apply only to ordinary first fatal entry;
re-entrant fatal handling that returns from Punt is excluded explicitly.

## Reproduction

Run from the repository; fresh outputs stay in the worker directory:

```powershell
python evidence/canonical/uninitialised-locals/stamp_origin.py --out build/workers/uninit/repro-origin
python evidence/canonical/uninitialised-locals/function_evidence.py --out build/workers/uninit/repro-functions.json
python -m unittest portable.tests.uninitialised_locals.test_uninitialised_locals
python portable/tests/uninitialised_locals/census.py --report build/workers/uninit/native/report.json --out build/workers/uninit/repro-census
```

The ignored memory frames are reproducible observations, not runtime dependencies.
The startup proof's extra-environment control modifies only its disposable BAT;
the memory-size control modifies only its disposable DOSBox configuration. Runs
are synchronous and exit the emulator explicitly. The native suites, reference
identities, lane results and remaining work are in the worker RESULT.md.
