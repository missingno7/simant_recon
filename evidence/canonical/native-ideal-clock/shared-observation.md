# Shared ideal-v1 observation results

2026-11-15. Both documented observer rules now apply to every ideal-v1 variant,
through one shared schema/configuration/receipt path. **18/18 sound-on and
18/18 sound-off gameplay lanes have equal state, frames and raw audio; 22/22
playback lanes are equal at 1 ns.** The production clock/audio implementation
is unchanged. No tolerance was widened, no tape retired and no commit made.

## Contract and controls

ideal_observation.py prepares the 1032-view schema, produces both DOS/native
serializations from the same census, and validates both receipts and all three
pinned sidecars. step_record, ideal_check and playback_check use it for every
variant. The DOS/native observers reject ideal mode without either rule.
Sound-off alone still selects CFG Mode 0 and checks zero sound hardware work.

The existing [Event proof](../native-input-irq/normal-words.md) and
[animation proof](animation-identity.md) describe how the game uses the words,
independently of Sound Mode. The helper headers/proof files are unchanged.
keyboard-context-v1 applies only to three bound global Event views (current,
previous and input_queue[7]), only FAxx/F081..F087, only h/v bytes 8..11, only
the supplied 640-wide EGA/VGA domain. All other bytes and mouse/object records
remain literal. anim-id-pattern-v1 applies only to three yard arrays and eight
instruction-bound scalar holders: preserve -1, equality pattern, and invalid
high-bit words; no arithmetic/order/SaveRec use is projected. No other view is
qualified. Category/verdict policy stays unchanged; full raw hashes, dumps and
all ID words remain diagnostic.

The existing exhaustive C/C++ event-code/byte tests, ID sentinel/equality/invalid
word tests, unlisted/adjacent/SaveRec controls remain. New tests require matching
censuses in both serializations, reject missing/changed receipts and sidecars,
broadened omitted offsets, wrong widths and an unproved display domain; the
real native observer rejects either omitted rule. Acceptance discovery passes
all 80 tests. Both helpers have one implementation; sound_off retains only a
compatibility import of Event helpers and its configuration selector.

## Reference recording and preservation

Re-recorded exactly 22 sound-on original/canonical captures under
build/reference/sound-on-identity-v1, using the US launch environment, ideal
clock native-clock-v1-irq-v3 and the shared 1032 views. This is needed for the
8 extra scalar views and both qualified hash streams. Old sound-on-clock-v3
captures remain historical controls. In every new capture all original 1024
raw per-entry view hashes equal the old prefix, and .audio/.content/.timer
files are byte-identical. The changes add observation, not a different game
execution.

**No sound-off reference was re-recorded.** All 18 manifests and every payload
file match the before-run SHA256 census. Their schemas/receipts/configuration
are identical under the common path. Fresh full scratch-only byte controls on
ant-commands/original and random-17/canonical equal the retained raw/qualified
hashes, ID words, audio and timer sidecars byte for byte. A new compact observer
build took 191.13 s; the 22 sound-on recordings took 272.19 s. The unchanged
native production build was reused after all 505 input pins matched.

## Measured check results

Each gameplay variant covers 26,128 entries and 152 exact checkpoint frames.
Playback covers 28,176 entries, including two focused recipes; its state,
frames and raw audio also pass. A lane time below includes native process,
preparation and comparisons for that lane; three workers overlap lane times.

| Scenario | Target | Entries | Sound-off state/frame/raw audio | Off lane s | Sound-on state/frame/raw audio | On lane s | Playback | Playback lane s |
|---|---|---:|---|---:|---|---:|---|---:|
| ant-commands | original | 1000 | equal | 2.59 | equal | 9.20 | equal | 10.12 |
| ant-commands | canonical | 1000 | equal | 2.60 | equal | 9.29 | equal | 10.10 |
| experiment | original | 1000 | equal | 2.34 | equal | 7.57 | equal | 8.21 |
| experiment | canonical | 1000 | equal | 2.10 | equal | 7.60 | equal | 7.87 |
| full-game | original | 1000 | equal | 1.90 | equal | 8.70 | equal | 8.93 |
| full-game | canonical | 1000 | equal | 1.90 | equal | 8.71 | equal | 8.99 |
| interactive-play | original | 2000 | equal | 2.86 | equal | 19.36 | equal | 20.15 |
| interactive-play | canonical | 2000 | equal | 2.85 | equal | 19.17 | equal | 20.12 |
| load-from-save | original | 1000 | equal | 3.05 | equal | 8.00 | equal | 8.01 |
| load-from-save | canonical | 1000 | equal | 3.04 | equal | 7.81 | equal | 8.03 |
| long-run | original | 3000 | equal | 6.53 | equal | 22.66 | equal | 23.34 |
| long-run | canonical | 3000 | equal | 6.57 | equal | 22.47 | equal | 23.16 |
| new-game-save | original | 64 | equal | 0.85 | equal | 1.74 | equal | 1.73 |
| new-game-save | canonical | 64 | equal | 0.83 | equal | 1.76 | equal | 1.77 |
| quick-game | original | 2000 | equal | 4.60 | equal | 17.22 | equal | 17.77 |
| quick-game | canonical | 2000 | equal | 4.54 | equal | 17.23 | equal | 17.71 |
| random-17 | original | 2000 | equal | 4.44 | equal | 15.64 | equal | 16.05 |
| random-17 | canonical | 2000 | equal | 4.39 | equal | 15.71 | equal | 16.05 |
| audio-controls | original | 512 | focused audio recipe | - | equal (playback observation) | - | equal | 4.16 |
| audio-controls | canonical | 512 | focused audio recipe | - | equal (playback observation) | - | equal | 4.22 |
| audio-restart | original | 512 | focused audio recipe | - | equal (playback observation) | - | equal | 4.47 |
| audio-restart | canonical | 512 | focused audio recipe | - | equal (playback observation) | - | equal | 4.36 |

Sequential command walls: sound-off 32.04 s, sound-on 84.69 s, playback 129.41 s;
combined **246.14 s (4.10 min)** with cached references, including each command's
observer preparation/build. The [proposal](tape-retirement-proposal.md) budgets
4?5 minutes and distinguishes recording/build/gate costs.

Playback content, rates/volume/metadata, bytes and event order agree. Song/note
events and sample start/stop timestamps agree at zero. A fresh comparison of
the same 22 captures at zero gives 8 equal / 14 different, solely interior
sample timestamps with maximum 1 ns; at 1 ns all 22 equal. Therefore 1 ns is
the smallest justified uniform integer-nanosecond bound. Raw bytes are never
masked. DOS/native coverage is identical: 8 MIDI identities, 23 effects,
18 sample identities, overlap in 16 lanes; no shipped looping voice or wrap
was observed, so the independent synthetic loop tests stay required.

The two sound-off new-game-save entry-time clock diagnostics at entry 37 are
identical to the pre-change baseline. They remain explicitly diagnostic and do
not change state/frame/raw-audio acceptance. All 18 sound-on entry clocks match.
Raw Event/animation differences remain reported in each result and the receipt;
qualified equality is not a claim that physical IDs/register words are equal.

## Independent validation and practical limits

Gate passes (594.48 s) in an isolated current-source snapshot; its status pages
are generated only in scratch. An uncommitted isolated index supplied the file
census because the snapshot is outside the root Git ancestor. The root index
is untouched. All 80 acceptance tests pass (150.11 s process wall). RNG,
database, simulation, VGA, audio, save/load, diagnostics, evaluation order,
virtual clock/audio, idle/yield, Windows and modern presentation suites pass.
The retained tape rerun still has 18/18 state/frame equality and the same 9 equal
/ 9 different audio results; complete audio and raw-diagnostic objects compare
identically to the prior run. Its exit 1 is the established result.

D: filled during earlier attempts; those incomplete runs are rejected and
retained. Accepted outputs are off3/on3/playback3, acceptance3 and gate4. To
finish without deleting evidence, completed older compiled scratch and check
outputs were moved to the system TEMP archive with junctions at the original
paths. Current shared scratch is physically in
C:/Users/jiriv/AppData/Local/Temp/simant-sound-on-archive-20261115/shared-live,
linked from build/workers/sound-on/shared. Reference captures and tapes stayed
in place. Timing includes this storage setup. No evidence/tape was retired.
Toolhelp full-image process census and EnumWindows find no task process/window
left. No src/, include/, layout/, production runtime, gate, tape entry point or
known-findings policy was edited. Root docs/progress/status are unchanged.

The [machine-readable receipt](shared-observation.json) pins source/helpers,
proofs, all reference manifests, result files, controls, suite/gate logs and
per-lane times. The final replacement/coverage table is a proposal only.
