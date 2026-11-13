/*
 * Defines the theme song descriptor and its program and bank mapping. It also carries the
 * pointer to the separate version string and the unused MIDI filename text.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident data extension, section 27; segments 55B3:0064. Data contributions are exact;
 * original translation unit completeness is unproven.
 * Windows: none (DOS only), based on the platform-specific code or DOS release data.
 *
 * The grouping is a hypothesis: the pointer and song record could be one or
 * two files. No code module addresses these values through its own _DATA.
 * version_message_pointer targets another file (S27 relocation #365, external group).
 * snd_active_song_record targets the local song record; its _DATA relocation #1049
 * follows the 00B8-1811 object in the descending-address group, establishing
 * this contribution before that object. Song has program[14], bank[14],
 * Handle as consumed by 0000/284A; 284A loads its resource and copies the maps.
 * The following MIDI filename has no code reference.
 */

typedef char far * far *Handle;

struct Song {
    int program[14];
    unsigned bank[14];
    Handle data;
};

extern char dos_version_string[];

/*
 * Pointer to the DOS version string shown by the event handler.
 */
char *version_message_pointer = dos_version_string;

static struct Song g_0068 = {
    { 0, 7, 7, 7, 7, 5, 5, 5, 5, 5, 5, 5, 5, 5 },
    { 0, 25, 53, 3, 54, 35, 46, 50, 51, 48, 0, 12, 43, 52 },
    0
};

static char g_00A4[16] = "antthme1.mid";

/*
 * Pointer to the song record loaded and released by the player.
 */
struct Song *snd_active_song_record = &g_0068;
