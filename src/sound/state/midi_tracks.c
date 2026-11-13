/*
 * Defines MIDI track scheduler flags and deadlines. Its ten track capacity is a functional
 * choice for the shipped resource domain.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 *
 * Functional scheduler storage for the immutable shipped SOUND corpus.
 * All initialized/current/best indices belong to 0..N-1, 2 <= N <= 10.
 * Capacity 10 is an operational allocation choice, not a historical COMDEF
 * capacity, original allocating translation unit or placement claim.
 * Resource/consumer proof: evidence/canonical/shipped-resource-domain/review.md.
 */

unsigned char far midi_track_status[10];
long far midi_track_event_ticks[10];
