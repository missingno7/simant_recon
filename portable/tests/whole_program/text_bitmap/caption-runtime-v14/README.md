# v14 blank-caption runtime diagnostic

This packet captures the normal VGA full-game replay that reproduced the blank
title bars. It is diagnostic evidence only; it does not claim a full caption
rendering proof.

`caption-runtime-v14.json` pins the executable identity, v14 application and
bridge sources, replay, GDB script/logs, screenshot, and every runtime asset
and BIOS-font file by size and SHA-256. The application/bridge snapshots are
copied byte-for-byte from the v14 build input tree. The executable and asset
payloads are not copied into this packet. The runtime used scratch copies of
assets whose hashes match the v14 report and canonical asset files.

The captured trace has five title calls: four `Surface View` requests at
`(271,66)` and one `SimAnt - Full Game` request at `(144,26)`. Every call sees
`graphics_status=OK` and `source_bridge.bound=0`; none reaches text preparation
or the bitmap callback. That is the first demonstrated loss stage for this
run. The screenshot remains useful to confirm the visible blank bars.
