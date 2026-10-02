# Save codec scope correction

The lifecycle V1 README says that “Full-file payload encoding/decoding is separately covered by the V3 codec/binding packet.” That sentence is too broad and should not be relied on as a decode claim; the pinned README is retained unchanged.

The V3/V5 binding evidence compares one independently constructed address-keyed sentinel state against all 307 writes from the original DOS `SaveGame`, then checks native emitted bytes against that resulting 48,386-byte stream (including the recorded little-endian and forced-big-endian variants). V5 strengthens execution-input identity for that writer experiment. It does not execute the original DOS `LoadGame` against a DOS-produced stream and therefore does not establish general payload decoding.

The lifecycle paired report separately does execute original DOS `LoadGame` with controlled read callbacks, including a partial read. Those cases prove read-loop/callback ordering and partial mutation for the controlled byte inputs; they do not bridge the SaveGame stream fixture into LoadGame or certify disk decoding.

Relevant immutable evidence: `portable/tests/save/evidence/legacy-save-codec-v3/README.md`, `portable/tests/save/evidence/legacy-save-codec-v5/README.md`, and `portable/tests/save/lifecycle/evidence/paired-report-v1.json`.
