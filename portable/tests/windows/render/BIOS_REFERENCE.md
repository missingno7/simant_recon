# BIOS font reference input

Run `python portable/tests/windows/render/evidence/fetch_bios_reference.py` to
download DOSBox Staging `v0.83.0` at immutable commit
`7b40053b7ac580843d0461eba8c36a47a990e66c`. It extracts the upstream
`int10_font_08` and `int10_font_14` arrays into ignored
`build/bios-reference/dosbox-staging-v0.83.0/` and retains the source file,
upstream license, table hashes, and extraction manifest there. The upstream
license is GPL-2.0-or-later. These are reference-host BIOS tables, not
SIMANT-owned assets and not proof of the user's physical BIOS contents.

The caller reads the two generated `.bin` files and passes their borrowed
buffers to `portable_bios_font_provider_init`. Set `provider_id` to the pinned
release and commit, then assign the initialized provider to
`PortableWindowRenderer.bios_fonts`. The provider must remain alive as long as
the renderer uses it. Source font IDs 0 and 1 select between these tables based
on source screen width; IDs 2 through 5 continue to use FONT1 through FONT4.

`evidence/bios_font_provider_dos_diff.py` validates source font selection and
glyph-table addressing against the original DOS `f_1B4E_0110` routine with a
generated fixture. It does not claim physical DOS display equivalence. The
selected DOSBox font is explicitly a host presentation choice.
