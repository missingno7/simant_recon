/*
 * Bundles MIDI scheduler state with font pointers, an animation object pointer and a window
 * geometry point. These independent fields have no established historical grouping.
 * The opaque or residual file name is retained; folder placement is ours (inferred).
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

struct Pt { int x; int y; };
struct AnimObj;
/*
 * Dimensions of bitmap 0x6f used for list scroll arrows.
 */
struct Pt far window_scroll_arrow_size;
/*
 * Font pointers selected by font number minus two.
 */
void far * far font_loaded_font_pointers[4];
/*
 * Pointer retained for setting the last added animation object's id.
 */
struct AnimObj far * far anim_last_added_object;
/*
 * Handle for the active song data used by the MIDI decoder.
 */
char far * far * far midi_song_data_handle;
/*
 * Size reported by mem_Size for the active song handle.
 */
int far midi_song_data_bytes;
/*
 * Big-endian division field read at song offset 12.
 */
int far midi_header_division;
/*
 * Fixed-point scale multiplied by track tick delta, then shifted eight.
 */
long far midi_tick_delay_scale;
/*
 * Instrument descriptor index selected for each MIDI channel.
 */
int far midi_channel_instruments[14];
/*
 * Voice-allocation priority supplied by each MIDI channel's note-on call.
 */
int far midi_channel_priorities[14];
