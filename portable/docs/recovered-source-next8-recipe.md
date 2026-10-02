# DOS-width history event profile

Next8 layers one correction over the [next7 profile](recovered-source-next7-recipe.md).
The S24 history handler's `unsigned code` is a 16-bit word in the original MSC
ABI. A bare host `unsigned` made that field 32 bits and included the next event
word in comparisons. The original instruction at S24:39C7:0021 reads only the
word at event offset 12. Next8 spells the generated member `uint16_t`.
Historical sources and earlier profile producers remain unchanged.

After recreating next7, run from the repository root:

```powershell
python portable/tools/recover_source_next8.py
python portable/build.py --core-profile build/workers/recovered_source_next8/generated
build/portable/simant-sdl3.exe --live-newgame --ticks 32
```

The producer records 64 original-DOS/native history-handler trace comparisons,
covering all twelve command branches and boundary codes with four values of
the following event word. All match. The old-width negative control misses
commands when that following word is nonzero. Host drawing and other leaves
are controlled callbacks, so this is event-dispatch evidence rather than a
complete history-window test. The focused regression is
`python -m unittest portable.tests.recovered.test_next8_event_width`.

All 25 source translation units compile. Only S24 changes relative to next7;
the other module and recovered-state identities are retained. The explicit
SDL build checks this extension, its parent chain, producer/source hashes and
target module identity. It remains diagnostic integration. The next7 captured
768-tick replay remains evidence for that earlier profile and its stated
370-field boundary; it is not relabeled as a next8 run.
