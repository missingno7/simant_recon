# StopSong source contract and native integration boundary

This note records a bounded study of `StopSong` (`root:284A:010A`). It does
not change the native engine, the portable audio implementation, or any
historical source. The current executable differential receipt is
[`stop-song-contract-v2.json`](../tests/audio/stop_song/evidence/stop-song-contract-v2.json).
V1 is preserved; its evaluator-package pin omission is superseded by V2, which
hashes the isolated Unicorn Python modules and native DLL before and after the
run. V1's decimal song-ID annotation typo is corrected by its attached
[`erratum`](../tests/audio/stop_song/evidence/stop-song-contract-v1-erratum.json).

`src/root/m284A.c` defines `StopSong` as a state-guarded two-stage transition.
For any nonzero `g_756E`, it first stores zero, then calls
`f_0000_039B(fd_55B3_00B4, g_7578)`, and then calls `f_295C_0391()`. When
`g_756E` is zero it returns without either call. The same behavior holds for
the source's two named states, 1 (playing) and 2 (finished); the test also
repeats the call after the first transition and verifies there are no repeated
cleanup/reset events.

The release helper in `src/root/m0000.c` owns the song-resource transition:
if `song->data` is non-null it calls `f_171C_1C0A` and clears that field. It
then scans the 14 bank entries. For each bank whose instrument kind is 1 and
whose sample pointer is non-null, it changes `loaded` from 2 to 1 and calls
`f_0000_0149` regardless of the prior loaded value. Its `number` parameter is
not read. `f_0000_0149` appends the sample to the freelist and may flush it
when the audio busy flag is clear. Those allocator/freelist internals were not
executed by this focused test.

The reset helper in `src/root/m295C.c` scans six-byte channel records until a
zero `type` sentinel. `c3` is declared `unsigned char`, so the source predicate
`c3 >= 0` is always true; the effective gate is nonzero `c2`. It then invokes
`f_295C_02E8(c3, c4)`. That helper dispatches note-off for matching
device/note records, then clears `c4` and `c2` and sets `c5` to 15. Device
register or ISA operations are below this contract boundary and were not
compared here.

The test invokes the frozen DOS function and its exact MSC source candidate,
intercepting only the two cross-module helper boundaries. The release callback
records the passed Song far pointer and signed song number, then models the
source helper's ownership effect by clearing the synthetic Song data handle.
The reset callback records the state visible after release. A small native C
adapter models the same interface using an opaque `current-song` token instead
of a DOS pointer. Three source-domain cases cover inactive/playing/finished
states and three real positive song identifiers (0x2AFE, 0x2711, 0x4E27);
each calls stop twice. The JSON summary's `domains.source_backed_song_numbers`
has a metadata-only decimal typo for 0x2711: it says 10003, while the scenario
and raw callback rows correctly record 10001. The companion erratum fixes only
that summary field; no execution output or test result changed.
Historical and native callbacks and final state agreed for all six calls. The
historical candidate also passed the existing exact claim gate for `StopSong`.

The present portable intent API is not itself the whole game-level contract:
`portable_audio_stop_song()` unconditionally queues `STOP_SONG`, while DOS
`StopSong` is a no-op when inactive and also releases current song-owned
resources before resetting MIDI voices. A future adapter should own the
nonzero state guard and sequence typed callbacks along these lines:

```c
typedef struct PortableSongControl {
    int16_t state;                 /* source states 0, 1, and 2 */
    int16_t resource_id;
    void *current_song_owner;      /* opaque stream plus bank/sample ownership */
} PortableSongControl;

typedef struct PortableSongStopOps {
    void *context;
    void (*release_song_resources)(void *context,
                                   PortableSongControl *song);
    void (*reset_active_song_voices)(void *context);
} PortableSongStopOps;

void portable_game_stop_song(PortableSongControl *song,
                             const PortableSongStopOps *ops)
{
if (song->state != 0) {
    song->state = 0;
    ops->release_song_resources(ops->context, song);
    ops->reset_active_song_voices(ops->context);
}
}
```

The release operation should cover the stream handle and the 14 bank/sample
references associated with the Song. The reset operation should emit note-off
for active MIDI/song voices and clear their logical active state. The existing
SDL audio host can translate those intents to its host backend; it should not
pretend to reproduce DOS ISA writes.

This is a narrow orchestration contract, not a general music-driver proof or a
`BEHAVIOR_EXACT` registration. `f_0000_039B`'s memory-manager effects,
`f_0000_0149`'s freelist timing, and the actual `f_295C_0391` device-command
sequence remain separate work if the port exposes them. The test's synthetic
song handle is only a boundary marker; no resource bytes or hardware behavior
are inferred from it.
