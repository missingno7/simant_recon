/*
 * Defines the array of sample pointers managed by the sound resource free list. The resource
 * loader adds and releases entries through this table.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

struct Sample;

/*
 * Loaded sample pointers visited by deferred sample cleanup.
 */
struct Sample far * far snd_sample_release_list[39];
