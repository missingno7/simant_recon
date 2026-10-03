# Whole-program DOS varargs boundary

`portable/whole_program/conversions/varargs.py` is called as
`adapt(source_text, source_path)` before whole-program word conversion. It
returns the converted source and a per-TU ledger. The adapter removes legacy
CRT declarations, routes source identifiers to `dos_printf`, `dos_sprintf`,
and `dos_vsprintf`, and replaces recognized stack-address varargs with
`va_start`, `va_copy` where a list is replayed, and matching `va_end` calls.
The signed fixed-parameter APIs `win_SetObjFormatStr` and `win_ObjFormatPrint`
are widened to `int32_t _dos_obj_wide` in their definitions and all source
prototypes; each definition keeps an `int16_t obj` local for original body
uses. This ensures `va_start` receives a non-promotable last named parameter.

`portable/whole_program/platform/dos_format.[ch]` implements the native
formatting boundary. Unqualified integer conversions use DOS 16-bit values;
`l`-qualified integer conversions consume `int32_t` or `uint32_t` and never
depend on host `long` width. It supports `d/i/u/o/x/X`, `s`, `c`, `p`, `%%`, the
observed flags/widths/precision, and dynamic width/precision. It rejects
unknown conversions, floating point, `%n`, and fields above 4096 with `-1`.
`%p` uses native host pointer text for diagnostics; it is not a DOS far-pointer
emulation.

Run the standalone native controls with:

```powershell
python portable/tests/recovered/whole_program_varargs/run_varargs.py
```

The immutable v5 control packet pins the scanned source TUs, conversion
helper, formatter, source-alias evidence and compiler. The source-owned
no-argument strings reached through `fd_55B3_1CD8` and `fd_55B3_1CDC` are
resolved through `source_expression_aliases` to the actual `m15F8.c` pointer
table and checked for zero percent conversions. `printf(msg)` in `m205F.c` is
checked against its actual literal assignment and branch; unsupported adapter
values can still leave `msg` uninitialized as in the frozen body, and that
source path remains explicit debt. These are source strings, not database
resource records. Dynamic source formats passed to
variadic functions are still interpreted by the runtime; the API cannot infer
the number of arguments supplied by C callers.

Tests compile the actual translated m22BF TU and run its generated
`win_SetObjFormatStr` body with the repeated arguments. A test-only sidecar
normalizes the single far-pointer record slot at object offset `0x2a`, because
the host pointer is wider than the DOS pointer and overlaps the following
source string at `0x2e`. This is a native ABI/content control, not a DOS output
comparison. No DOS formatting-equivalence claim is made.
