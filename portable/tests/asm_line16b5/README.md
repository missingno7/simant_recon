# Root m16B5 line provider

`portable/whole_program/algorithms/line16b5.c` is a standalone native
translation of the public `f_16B5_0033` initializer and `f_16B5_0008` line
entry, including the three dispatched pixel modes and `f_16B5_04D8` clipping
behavior. It is not added to the default build.

The typed core is `PortableLine16B5`, initialized with an explicit payload
pointer and capacity using `portable_line16b5_init`, then used through
`portable_line16b5_draw`. The source-name wrappers retain the historical
pointer-plus-16-bit-mode and five-word line-call ABI. The initializer adapter
expects the historical inline layout: two signed 16-bit words `{width,height}`
followed immediately by pixel bytes. It does not treat offset 4 as a native
font `Bitmap.bits` pointer. Callers must provide the source-derived maximum
6276-byte inline owner (four-byte prefix plus at most 6272 payload bytes).
`portable_line16b5_unbind` releases the provider's one legacy binding.

The portable core accepts square geometries only. The source clipper compares
its register axes `(SI,DI)=(y,x)` against `(width,height)` while the row table
contains `height` entries; non-square input can address beyond that table. The
current DrawSpider caller establishes square buffers of 84 or 112 pixels. Its
mode mapping is mode 0 one-bit, mode 1 packed four-bit, and mode 2 four-plane
four-bit.

Run `python portable/tests/asm_line16b5/run_differential.py` to compile under
strict GCC warnings and compare all payload bytes against direct 16-bit
Unicorn execution of the frozen root `f_16B5_0033` / `f_16B5_0008` entries.
The runner refuses to overwrite its default receipt; pass a new `--report`
path for another evidence version. `evidence/dos-native-v2.json` records the
264-case result, three source-name adapter controls, native negative controls,
compiler/linker tools, preprocessor dependencies, and before/after source,
runtime, and oracle pins. The earlier receipt and runner are preserved under
`archive/`.

This is a pixel-buffer differential for the historical line provider. It does
not validate SDL framebuffer integration or the unknown historical allocation
extent of `fd_50F6_1F26`.
