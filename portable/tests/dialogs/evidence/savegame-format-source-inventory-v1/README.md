# Saved-game serialization inventory (source-derived)

Read-only inventory of S09 `LoadGame`, `SaveGame`, and the `fd_4E4B_0000` record table. This is a format inventory, not a portable serializer implementation. Source: [m35F5.c](D:/Prog/simant_recon/src/S09/m35F5.c), SHA-256 `028e1575990d5d45233f9102a0d2a060810349bd2f1297182c4af435ecbe912a`. The full pointer-table transcription is pinned in `pins.json`.

`fd_4E4B_0000` is declared as 308 entries: 307 nonzero data records followed by a zero terminator. `SaveGame`/`LoadGame` iterate in that order, treating each row as `element_size * element_count` bytes at the row's pointer. The resulting current payload length is **48,386 bytes**. A 16-bit far `SaveRec` row occupies 8 in-memory bytes, so the table metadata itself occupies 2,464 bytes; it is not part of the saved payload. Pointer addresses and row metadata are not serialized. No endian conversion occurs in these loops.

Payload partition by declared element width:

| Element size | Records | Payload bytes |
|---:|---:|---:|
| 1 | 42 | 45,978 |
| 2 | 234 | 2,284 |
| 4 | 31 | 124 |

The first records are five maps `&MapA, &MapB, &MapR, &ExitMapB, &ExitMapR` with respective byte lengths 8,192 and 4,096 each; then five A-list and five B/R-list parallel arrays; pheromone and hole maps; followed by 4-byte and 2-byte scalars/arrays. The full ordered table, including every target expression, is in `save-records.json`. One record points to `(fd_3D57_087A + 20)` for 10 16-bit values; this interior offset is part of the source schema.

The `.ant` extension is appended by `o09_35F5_0D2B`; FileSelect filters for `*.ant`. The code defines `g_2776[128]` with a comment calling it a MacBinary-style header, but neither `SaveGame` nor `LoadGame` references it. The implemented byte stream therefore starts with record 0, `MapA`, with no such header.

`SaveGame` first tries to open an existing path with `O_RDWR`; when it does not find one it creates/truncates. Existing-file overwrite confirmation continues into writes without truncating the file, so a previous longer tail can remain. It writes the records sequentially and checks only `write(...) == -1`; it does not detect positive short writes. After all writes it sets the dirty word to zero before the success message and `close`.

`LoadGame` clears the dirty word before attempting `open`, and on a readable file it calls `o09_35F5_0D7A` before loading: this resets selected yard globals and calls `RandYard`. It then reads each record directly into live memory and requires each individual read to equal its requested length. A short read reports an error and sets `fd_50F6_0EAC=-1`, but there is no rollback for prior or partial writes. It does not check for trailing bytes after the expected 48,386-byte stream. Successful reads call UI update helpers and `o09_35F5_0DBB`, which rebuilds life maps and derived counts.

## Source anchors

- `src/S09/m35F5.c:14`: `SaveRec` fields.
- `src/S09/m35F5.c:78`: declared 128-byte header array.
- `src/S09/m35F5.c:89`: load routine.
- `src/S09/m35F5.c:141`: save routine.
- `src/S09/m35F5.c:553`: pre-load yard reset.
- `src/S09/m35F5.c:563`: post-load derived-state rebuild.
- `src/S09/m35F5.c:893`: ordered stream table.

## Runtime integration boundary

A faithful portable file service needs an explicit versioned source-state codec over the exact 307 ordered fields, with owned temporary snapshots, exact 48,386-byte payload validation, and a defined policy for failed/truncated loads before mutating live state. Those guarantees cannot be inferred from the current in-place DOS `LoadGame` behavior; keeping the host format boundary explicit is necessary until compatibility policy is decided. This inventory adds no save/load implementation and changes no engine or live adapter.
