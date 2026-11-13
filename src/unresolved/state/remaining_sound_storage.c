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
struct Pt far window_scroll_arrow_size;
void far * far font_loaded_font_pointers[4];
struct AnimObj far * far anim_last_added_object;
char far * far * far midi_song_data_handle;
int far midi_song_data_bytes;
int far midi_header_division;
long far midi_tick_delay_scale;
int far midi_channel_instruments[14];
int far midi_channel_priorities[14];
