# Monochrome pattern exclusion in the default VGA lifetime

The existing `shipped-default-vga-successful-lifetime` domain performs no read
or write through `g_8ED8`. Canonical source therefore owns one near byte solely
to provide the external linker symbol. One byte is the smallest C object with
external linkage; it is not the supported data footprint, a recovered DOS
capacity, a tail of `g_8EC0`, or an allocation for monochrome display modes.

## Mode invariant and complete access routes

The reviewed default-VGA proof fixes `g_5A97` at 8 after `ReadConfig` and proves
that startup, aliases and ordinary saves preserve it for the successful main
lifetime. Its whole-inventory pin and negative controls remain authoritative;
`mode_probe.py` composes that proof rather than creating another selector
assumption.

The original function table gives `LoadMonoPats` exactly one caller, `main`.
Canonical `main`, which is an exact whole-module reconstruction, calls it only
when `g_5A97 & 1`; mode 8 skips the call. The S15 producer is therefore not
entered in the supported domain.

The four S01 consumers have two routes. `InitMapFunctions` is the only source
writer of `fd_50F6_38B8` and `fd_50F6_38BC`. Its mode-8 case stores the S00 color
converters; only cases 3, 5 and 7 store `o01_328E_000A` and
`o01_328E_009D`. `Mini_MakeTable` calls `o01_328E_012C` or
`o01_328E_01D5` only in those same odd cases; its mode-8 case calls S00 color
converters. The complete token census pins all eight producer, consumer and
dispatch identifiers across the current C/ASM inventory.

An original-instruction control executes `Mini_MakeTable`: mode 8 selects
`o00_3126_06A3`, while changing only the mode to 7 selects
`o01_328E_01D5`. The retained `asm_witness.py` controls show that the odd-mode
S01 bodies really read the pattern table and that a row-72/y-7 miniature case
observes displacement 584. Those are necessary negative controls. They are not
covered by the one-byte provider.

## Source contract and limits

`src/state/mono-pattern-vga-linkage.c` compiles under the pinned MSC 6.00AX
large-model profile to one one-byte near COMDEF and no code, initialized bytes,
publics, fixups, imports or live segments. Static duration is sufficient because
no supported access occurs. The provider changes no game algorithm or supported
observable state.

MONONT/L256NT resources, odd display modes, direct external entry, corrupted
control flow and replacement configuration remain outside this contract. The
Win16 584-byte pattern allocation and resource are corroboration only and do not
establish a DOS allocation. Supporting an odd DOS mode still requires its own
resource, producer, complete consumer bounds and real owner extent.

Run `python evidence/canonical/monochrome-owner/mode_probe.py` and
`python -m unittest tests.test_monochrome_vga_domain` after publication. The
probe compares against reviewed `mode-facts.json`; it does not refresh facts.
