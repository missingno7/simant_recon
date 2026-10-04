# Bounded S01 pattern-bank reference

Root accepts one generated source reference at S01A_TEXT:05A8 in
`_o01_3126_0523`: `SS:[BX+4220h]` becomes `SS:[BX+_g_4220]` under a scoped
DGROUP assumption. The existing 256-byte `_g_41D0` bank owns `_g_4220` at +80;
no storage or new public is added.

The bank initializes both g_3DE4 and its adjacent high-byte view g_3DE5 to
zero. The direct-reference census accounts for their declarations, zero
initializers, reads and the sole overlapping word-store producer, whose
70F0h mask restricts the high byte to 00h..70h by 10h. The selector is reduced
to 0..3 and doubled; the +2 / AND 00F7h loop cycles phase 0,2,4,6. The maximum
read displacement is therefore 76h, or C6h in the existing 100h-byte bank.
The existing sixteen-byte g_4220 row alone would not cover these reads.

The accepted startup and interrupt/display stack evidence supplies SS=DGROUP
on the reviewed entry routes; the selected TU preserves SS. This decision is
scoped to that provenance, not a universal SS assumption or a proof against
arbitrary corrupt pointers. Both shifted-DGROUP fixtures observe DS=SS=DGROUP,
check all 32 reachable style/phase addresses and pass. Wrong DATA frame and
one-byte base shift fail. Clean maps and diagnostic-free actual links are
required. An independent worker rerun confirms the same results.

The complete accepted S01 binding chain is pinned. The generated whole-object
guard admits exactly one zero-addend DGROUP OFFSET16 relocation and changes
only its two displacement bytes. Segment definitions/extents, publics and all
unrelated ordered fixups stay equal to the source-built control. Research
snapshots of mutable build reports/generated outputs remain observations;
canonical sources, accepted packets and current whole-object checks supply
the ongoing proof. No original executable enters compilation or linking.

The broader numeric/frame audit remains UNRESOLVED. The four 8ED8h sites,
their resource-dependent extent and SS provenance are outside this admission.
