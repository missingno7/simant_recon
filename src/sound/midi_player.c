/*
 * Loads and advances MIDI songs and their tracks. It decodes timed events and sends notes
 * through the sound driver channel layer.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 284A; partial original translation unit.
 * Windows: GR, from recorded function pairs in the Windows symbol inventory.
 * Build profile: msc600ax; /AL /Os /Oe /Og /Gs /Zi.
 * Functions not yet exact: snd_song_read_be16.
 */

struct Song {
    int program[14];
    int bank[14];
    char far * far *data;
};

/*
 * Track count read from big-endian song header offset ten.
 */
int midi_track_count = 0;
/*
 * Tick position of the most recently selected MIDI event.
 */
long midi_last_event_ticks = 0;
/*
 * Track index whose parser position and status are active.
 */
int midi_current_track = 0;
/*
 * Song state: zero stopped, one active, two end reached.
 */
int midi_playback_state = 0;
/*
 * Unsigned note-velocity multiplier, applied with a seven-bit shift.
 */
unsigned midi_volume_scale = 0x7f;
int g_7572 = 0;
/*
 * Set while the MIDI service loop is decoding events.
 */
int midi_service_active = 0;
/*
 * Signed note offset loaded from the song resource header.
 */
int midi_note_transpose = 0;
/*
 * Song resource number retained for release when stopping.
 */
int midi_loaded_song_number = 0;

#define SONGP(off) ((unsigned char _based(g_8DFC) *)(off))
#define SONG(off) (*SONGP(off))

extern void far snd_service_pending(void);

int far snd_service_and_test_stopped(void)
{
    snd_service_pending();
    return midi_playback_state == 0;
}

void far StopSong(void);
extern struct Song far * far snd_active_song_record;
extern int far snd_load_song_resources(struct Song far *song, int number);
extern int far WinPrintf(char far *format, ...);
extern void far snd_control_interrupts_disable(void);
extern char far * far * far midi_song_data_handle;
/*
 * Per-track byte offsets advanced by the MIDI event parser.
 */
static int midi_track_offsets[18];
static _segment g_8DFC;
extern int far midi_song_data_bytes;
extern int far mem_Size(char far * far *handle);
void far snd_song_initialize_tracks(void);
void far snd_song_reset_clock(void);
extern int far midi_service_countdown;
extern int far midi_channel_instruments[];
extern int far midi_channel_priorities[];
extern void far snd_control_interrupts_enable(void);

void far snd_load_and_start_song(int number)
{
    int i;

    StopSong();
    if (snd_load_song_resources(snd_active_song_record, number) == -1) {
        WinPrintf("music failure\n");
        return;
    }
    snd_control_interrupts_disable();
    g_7572 = 0;
    midi_song_data_handle = snd_active_song_record->data;
    g_8DFC = ((_segment far *)midi_song_data_handle)[1];
    WinPrintf("Seg=%x, buf=%p, handle=%p", g_8DFC, *midi_song_data_handle, midi_song_data_handle);
    midi_song_data_bytes = mem_Size(midi_song_data_handle);
    snd_song_initialize_tracks();
    snd_song_reset_clock();
    midi_playback_state = 1;
    midi_service_countdown = 5;
    for (i = 0; i < 14; i++) {
        midi_channel_instruments[i] = snd_active_song_record->bank[i];
        midi_channel_priorities[i] = snd_active_song_record->program[i];
    }
    snd_control_interrupts_enable();
}

extern void far snd_release_song_resources(struct Song far *song, int number);
extern void far snd_stop_assigned_voices(void);

void far StopSong(void)
{
    if (midi_playback_state) {
        midi_playback_state = 0;
        snd_release_song_resources(snd_active_song_record, midi_loaded_song_number);
        snd_stop_assigned_voices();
    }
}


extern int far midi_header_division;
extern long far midi_track_event_ticks[];
extern unsigned char far midi_track_status[];
extern long far midi_tick_delay_scale;
extern void far snd_stop_instrument_note(int program, int note);
extern void far snd_start_instrument_note(int bank, int program, int note, int velocity);
/*
 * Read two song bytes in big-endian order without changing a track cursor.
 */
int far snd_song_read_be16(int off)
{
    return SONG(off) << 8 | SONG(off + 1);
}


/*
 * Read four song bytes in big-endian order without changing a track cursor.
 */
long far snd_song_read_be32(int off)
{
    long v;
    int i;

    v = 0;
    for (i = 0; i < 4; i++) {
        v = (v << 8) + SONG(off);
        off++;
    }
    return v;
}

/*
 * Index track payload offsets by walking length-prefixed song chunks.
 */
void far snd_song_index_track_chunks(int count, int off)
{
    int i;
    long len;

    for (i = 0; i < count; i++) {
        len = snd_song_read_be32(off + 4);
        midi_track_offsets[i] = off + 8;
        off += len + 8;
    }
}

/*
 * Pointer to the active track's mutable byte-offset entry.
 */
static int far *midi_active_offset_pointer;

/*
 * Decode a variable-length quantity and advance the selected track cursor.
 */
long far snd_song_read_varlen(void)
{
    long v;
    unsigned char c;
    int pos;

    pos = *midi_active_offset_pointer;
    if ((v = SONG(pos++)) & 0x80) {
        v &= 0x7f;
        do {
            c = SONG(pos++);
            v = (v << 7) + (c & 0x7f);
        } while (c & 0x80);
    }
    *midi_active_offset_pointer = pos;
    return v;
}

/*
 * Set the song velocity scale; 128 represents unity.
 */
void far snd_song_set_volume(unsigned volume)
{
    midi_volume_scale = volume;
}


/*
 * Read the song header and initialize track positions, times and status bytes.
 */
void far snd_song_initialize_tracks(void)
{
    long len;
    int i;

    len = snd_song_read_be32(4);
    midi_track_count = snd_song_read_be16(10);
    midi_header_division = snd_song_read_be16(12);
    snd_song_index_track_chunks(midi_track_count, len + 8);
    for (i = 0; i < midi_track_count; i++) {
        midi_active_offset_pointer = &midi_track_offsets[i];
        midi_track_event_ticks[i] = snd_song_read_varlen();
        midi_track_status[i] = SONG(*midi_active_offset_pointer);
    }
}

/*
 * Pointer to the active track's running-status byte.
 */
static unsigned char far *midi_active_status_pointer;
void far snd_song_set_tempo(unsigned division, long tempo);

/*
 * Reset the sequencer clock and select track zero with the default tempo.
 */
void far snd_song_reset_clock(void)
{
    midi_last_event_ticks = 0;
    midi_current_track = 0;
    midi_active_offset_pointer = midi_track_offsets;
    midi_active_status_pointer = midi_track_status;
    snd_song_set_tempo(0x1e0, 500000L);
    midi_service_countdown = 99;
}

void far f_284A_0324(void)
{
}


/*
 * Compute the scheduler scale from division and tempo in microseconds per quarter note.
 */
void far snd_song_set_tempo(unsigned division, long tempo)
{
    long v;

    if (division == 0)
        v = 0;
    else
        v = tempo / 1000 * 1194 / division;
    midi_tick_delay_scale = v / 13;
}

/*
 * Select the next due track and return its delay; mark playback finished when none remain.
 */
int far snd_song_schedule_next_track(void)
{
    long delta;
    long t;
    int best;
    int i;

    if (*midi_active_status_pointer != 0x2f) {
        delta = snd_song_read_varlen();
        midi_track_event_ticks[midi_current_track] += delta;
    } else
        midi_track_event_ticks[midi_current_track] = 0x7fffffffL;
    best = 0;
    for (i = 1; i < midi_track_count; i++)
        if (midi_track_event_ticks[best] > midi_track_event_ticks[i] && midi_track_status[i] != 0x2f)
            best = i;
    if (midi_track_status[best] != 0x2f) {
        t = midi_track_event_ticks[best];
        if (t != 0x7fffffffL) {
            delta = t - midi_last_event_ticks;
            midi_last_event_ticks = t;
            midi_active_offset_pointer = &midi_track_offsets[best];
            midi_active_status_pointer = &midi_track_status[best];
            midi_current_track = best;
            return (int)(midi_tick_delay_scale * delta >> 8);
        }
    }
    midi_playback_state = 2;
    f_284A_0324();
    return 0;
}


/*
 * Scale song velocity and dispatch a note-on or note-off request.
 */
void far snd_song_dispatch_note(int chan, int note, unsigned velocity)
{
    velocity = midi_volume_scale * velocity >> 7;
    if (velocity == 0)
        snd_stop_instrument_note(midi_channel_instruments[chan], note);
    else
        snd_start_instrument_note(midi_channel_priorities[chan], midi_channel_instruments[chan], note, velocity);
}

/*
 * Set the instrument selector for one song channel.
 */
void far snd_song_set_channel_instrument(int chan, int program)
{
    midi_channel_instruments[chan] = program;
}

/*
 * Data-byte counts indexed by decoded MIDI channel-message type.
 */
int midi_event_data_lengths[] = { 2, 2, 2, 2, 1, 1, 2 };

/*
 * Dispatch a channel event and advance its data cursor; the literal case 12 is unreachable.
 */
void far snd_song_dispatch_channel_event(unsigned status)
{
    int type;
    int chan;

    type = (status & 0x70) >> 4;
    chan = status & 0xf;
    if (chan < 14) {
        switch (type) {
        case 0:
            snd_song_dispatch_note(chan, SONG(*midi_active_offset_pointer) + midi_note_transpose, 0);
            break;
        case 1:
            snd_song_dispatch_note(chan, SONG(*midi_active_offset_pointer) + midi_note_transpose, SONGP(*midi_active_offset_pointer)[1]);
            break;
        case 12:
            snd_song_set_channel_instrument(chan, SONG(*midi_active_offset_pointer));
            break;
        }
    }
    *midi_active_offset_pointer += midi_event_data_lengths[type];
}

/*
 * Handle track-end and tempo meta events; skip other meta payloads.
 */
void far snd_song_dispatch_meta_event(void)
{
    long tempo;
    int pos;

    if (SONG(*midi_active_offset_pointer) == 0x2f) {
        *midi_active_status_pointer = SONG(*midi_active_offset_pointer);
        (*midi_active_offset_pointer)--;
    } else if (SONG(*midi_active_offset_pointer) == 0x51) {
        *midi_active_offset_pointer += 2;
        pos = *midi_active_offset_pointer;
        tempo = ((((long)SONGP(pos)[0] << 8) + SONGP(pos)[1]) << 8) + SONGP(pos)[2];
        *midi_active_offset_pointer += 3;
        snd_song_set_tempo(midi_header_division, tempo);
    } else {
        (*midi_active_offset_pointer)++;
        *midi_active_offset_pointer += (int)snd_song_read_varlen();
    }
}

/*
 * Skip a length-prefixed system-exclusive payload in the selected track.
 */
void far snd_song_skip_sysex_payload(unsigned char status)
{
    *midi_active_offset_pointer += (int)snd_song_read_varlen();
}

/*
 * Process due song events and return the next timer delay, or -1 when inactive.
 */
int far snd_song_process_due_events(void)
{
    int r;

    if (midi_playback_state != 1)
        return -1;
    midi_service_active = 1;
    g_8DFC = ((_segment far *)midi_song_data_handle)[1];
    do {
        if (SONG(*midi_active_offset_pointer) & 0x80) {
            *midi_active_status_pointer = SONG(*midi_active_offset_pointer);
            (*midi_active_offset_pointer)++;
        }
        if (*midi_active_status_pointer == 0xf7 || *midi_active_status_pointer == 0xf0)
            snd_song_skip_sysex_payload(*midi_active_status_pointer);
        else if (*midi_active_status_pointer == 0xff)
            snd_song_dispatch_meta_event();
        else
            snd_song_dispatch_channel_event(*midi_active_status_pointer);
        r = snd_song_schedule_next_track();
    } while (r == 0 && midi_playback_state != 2);
    midi_service_active = 0;
    return r ? r : 1;
}
