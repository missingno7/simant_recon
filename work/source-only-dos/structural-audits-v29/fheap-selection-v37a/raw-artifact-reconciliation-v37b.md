# v37b raw-artifact reconciliation

This append-only receipt pins the frozen v37a logs/maps by their on-disk bytes. No v37a file was modified, and no compiler, librarian, or linker was rerun. All generated executables remain unexecuted.

The v37a JSON has 20 LOG/MAP hash fields. None matches its file’s raw-byte SHA-256. All 20 match the hash recorded by v37a’s exact text-read/re-encode algorithm. In [the frozen builder](probe_fdata_selection_cause_v37a.py), lines 114–115 read each artifact with `Path.read_text(encoding="latin1", errors="replace")`; lines 137–138 hash the resulting string after `.encode("latin1", errors="replace")`. Python text I/O translated CRLF to LF. Every frozen LOG/MAP has CRLF-only line endings, so the serialized text is one byte shorter per newline pair. The stored values are valid hashes of that normalized text representation, but they are not raw artifact hashes.

I reopened all ten raw logs and maps and reparsed the selected custom/LLIBCR members, unresolved symbols, warnings, target public rows, and heap-symbol map rows. All ten selection summaries match the v37a receipt. The separately recorded raw hashes below are the file pins.

| Control | Linker | Raw LOG bytes / SHA-256 | Raw MAP bytes / SHA-256 | Reopened result |
|---|---|---|---|---|
| natural_main_llibcr_baseline | rtlink400 | 1055 / `12ff50d754a3334caf134c022884ccb787bb6e6dfccf3cd675fdb8f2ce316057` | 20943 / `0edac93d000e2bb26a8c313ebe8fb1140445a3b66386136c1352fec1efc6d6a6` | no custom member; agrees |
| natural_main_llibcr_baseline | rtlink610 | 1585 / `79ea51bc91d98e64c0a943c80bd79a27eed2f913e5ddd159b96c2dbc7143e1ac` | 26754 / `a08ecad6211dfb4039d3fd4f2c9366df2fa954461fbc38fddeafd3952d9acd90` | no custom member; agrees |
| both_unreferenced | rtlink400 | 1096 / `b93cd3b7559a5ab10e439cae66d7f7863d5dc02dd904c0b84ab7218767112c44` | 20943 / `0edac93d000e2bb26a8c313ebe8fb1140445a3b66386136c1352fec1efc6d6a6` | no custom member; agrees |
| both_unreferenced | rtlink610 | 1626 / `7dbfc55165b6a5a75aa41a9c4c0d0cba70e2f06d3b147a898970165abbeacfa6` | 26754 / `a08ecad6211dfb4039d3fd4f2c9366df2fa954461fbc38fddeafd3952d9acd90` | no custom member; agrees |
| referenced_data_only | rtlink400 | 1095 / `9d6c2bb98886b2875f17db6f73cc7fbce83ee4fed58cac0329a156ae965010d0` | 21490 / `544da529ca516127984e92011a62a33cb2938143a6fc95c350cfc964b368b504` | DONLY.C; agrees |
| referenced_data_only | rtlink610 | 1625 / `401d1396bdfcfc5c0786c845a90b38191a4225f44f63d74c5d8489ebedd50ec6` | 27601 / `654924a4a09debe85e12006689fff99f4d5d79d5587a660d01c6f619367c8fd5` | DONLY.C; agrees |
| referenced_comdef_only | rtlink400 | 1303 / `d000349be4a4398965d359ee91fe9b5db95c842b0f7a4cee2f5781f93e6a77e7` | 21157 / `64c74f63d707533e8469dbd231179ee128e490a771d54b0a617619d07c62c86b` | no custom member; undefined _probe_common_only; agrees |
| referenced_comdef_only | rtlink610 | 1920 / `492ffc5be4da8a394c46e42341b723cee918c6af17b38cc5ad38db813449c3ca` | 26976 / `ef1254072ac51be8004726b4fdd1d8cbd2621cbb3cf7f02ff968c4ad31f10186` | no custom member; undefined _probe_common_only; agrees |
| referenced_code_plus_data | rtlink400 | 1093 / `e690c437a93bf3b42ebcd56a9c44132440f5673d0034b6dffe0b46d5a2cde388` | 21432 / `2f59b1ff14c3d70fae6ebfc0f0810909a54c227f9b6fe8a1cb282f3fab3034a7` | CDMEM.C; agrees |
| referenced_code_plus_data | rtlink610 | 1623 / `9112ba1660250a2fe7a7a9fb80cd20168308639889be6ecb326493d99a0dc57f` | 27535 / `145a879d10f936ab7d5d8e8c712ff63e67fad51fbfa0ce981b130e3009bd5b66` | CDMEM.C; agrees |

The complete per-file record also includes each old v37a text hash, its reproduced normalized-text hash, CRLF counts, raw byte size, and map/log reparse results in [raw-artifact-reconciliation-v37b.json](raw-artifact-reconciliation-v37b.json). That JSON also hashes the frozen v37a receipt, builder, and three LIB outputs; the archive hashes match the prior receipt.

This correction changes only the interpretation of the v37a hash fields. It does not change the selected-member findings, explain the app-specific RTLink 6.10 `fdata.asm` selection, or establish historical `DGROUP:79F0` placement.
