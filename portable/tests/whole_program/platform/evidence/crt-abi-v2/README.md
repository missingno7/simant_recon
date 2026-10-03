# Bounded native CRT ABI observation

`original-runtime-observation.json` reads the original executable's initialized DGROUP through `behavior.Machine`, at the symbol-grounded `sys_errlist`, `sys_nerr`, and `_ctype` addresses. It records decoded error strings and the ASCII `_LOWER` classification only; the raw `_ctype` span is represented by a digest, not copied into source. The pin list includes the oracle/parser and source anchors.

The new `crt_abi.c` provider keeps the observed 38-entry string table (`sys_nerr == 37`), implements only the verified ASCII lowercase bit used by current source, and terminates explicitly if a byte outside that domain reaches it. `_harderr` registration stores the source callback (the actual `f_208F_058B` returns 3, `_HARDERR_FAIL`). INT 24 delivery is a retired DOS mechanism; native filesystem errors are returned by the existing host I/O boundary and are not synthesized into interrupt callbacks.

`native-provider-unit-report.json` covers strict native compile, all 38 messages, ASCII byte classifications, handler registration/invocation, and the non-ASCII fail-closed negative control. This is a bounded source-adapter/provider contract, not historical behavior proof or a general CRT replacement. No original executable, object, or table byte array is included.
