/*
 * Loads song resources and decompresses sampled sounds through a database hook. It also manages
 * the sample free list and releases sound resources.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 0000; complete original translation unit.
 * Windows: unknown; no confirmed function pair identifies a symbol group.
 * Build profile: msc600ax; /AL /Os /Oe /Og /Gs /Zi.
 */

typedef char far * far *Handle;

#pragma pack(1)
struct Sample {
    Handle data;
    unsigned len;
    unsigned loop;
    char looped;
    unsigned char octave;
    int tune;
    int loaded;
    char name[15];
    int object;
};
#pragma pack()

struct Song {
    int program[14];
    unsigned bank[14];
    Handle data;
};

struct Instr {
    int kind;
    struct Sample far *sample;
};

int g_181C = 0;

extern Handle far Ralloc(long size, int flags, char far *name);
extern char far * far mem_Lock(Handle h);
extern char far *snd_decode_delta_nibbles(unsigned char far *src, char far *dst, unsigned n);
extern Handle far mem_Unlock(Handle h);
extern void far mem_Free(Handle h);

void far snd_expand_sample_resource(Handle far *handle, unsigned far *size, int object, int type)
{
    Handle h;
    unsigned n;

    if (type == 5) {
        n = (*size - 16) << 1;
        *size = n;
        h = Ralloc((long)n, 0x18, "DACsample");
        snd_decode_delta_nibbles(mem_Lock(*handle), *h, n);
        mem_Unlock(*handle);
        mem_Free(*handle);
        *handle = h;
    }
}

extern Handle far res_load_firm_object(int object, int kind);
extern long far mem_Size(Handle h);

int far snd_load_sample_resource(struct Sample far *s)
{
    Handle h;

    if (s->loaded != 0)
        return 1;
    h = res_load_firm_object(s->object, 5);
    s->data = h;
    s->len = mem_Size(h);
    s->loaded = 1;
    return 0;
}

extern void far snd_sample_interrupts_disable(void);
extern struct Sample far * far snd_sample_release_list[];
extern void far db_ReleaseHandle(Handle h);
extern void far snd_sample_interrupts_enable(void);

void far snd_drain_sample_release_queue(void)
{
    int i;
    struct Sample far *s;

    snd_sample_interrupts_disable();
    for (i = 0; i < g_181C; i++) {
        s = snd_sample_release_list[i];
        if (s->loaded == 1 && s->data != 0) {
            db_ReleaseHandle(s->data);
            s->data = 0;
            s->loaded = 0;
        }
    }
    g_181C = 0;
    snd_sample_interrupts_enable();
}

extern void far Punt(char far *message);
extern int far midi_service_active;

void far snd_queue_sample_release(struct Sample far *s)
{
    if (g_181C > 38)
        Punt("FREELIST > 38");
    snd_sample_release_list[g_181C++] = s;
    if (midi_service_active == 0)
        snd_drain_sample_release_queue();
}

extern int far snd_service_and_test_stopped(void);
extern void far StopSong(void);
extern unsigned far FlipWord(unsigned value);
extern int far midi_note_transpose;
extern int far midi_loaded_song_number;
extern void far db_UnhookObject(int object, int kind);
extern void far mem_set_alloc_type(Handle h, int flags);
extern int far mem_handle_above_ems_boundary(Handle h);
extern void far RallocFree(Handle h);
extern void far * far _fmemcpy(void far *dst, void far *src, unsigned n);
extern struct Instr far snd_instrument_descriptors[];
void far snd_release_song_resources(struct Song far *song, int number);

int far snd_load_song_resources(struct Song far *song, int number)
{
    Handle h;
    Handle old;
    int far *hdr;
    unsigned n;
    int i;

    if (snd_service_and_test_stopped() == 0)
        StopSong();
    h = res_load_firm_object(number, 0x12);
    if (h == 0)
        return -1;
    hdr = (int far *)mem_Lock(h);
    number = FlipWord(hdr[0]);
    midi_note_transpose = hdr[3];
    midi_note_transpose = FlipWord(midi_note_transpose);
    mem_Unlock(h);
    db_ReleaseHandle(h);
    midi_loaded_song_number = number;
    song->data = res_load_firm_object(number, 0x14);
    db_UnhookObject(number, 0x14);
    mem_set_alloc_type(song->data, 0x31);
    if (song->data == 0)
        return -1;
    if (mem_handle_above_ems_boundary(song->data) != 0) {
        old = song->data;
        n = mem_Size(old);
        song->data = Ralloc((long)n, 0x39, "song");
        if (song->data == 0) {
            RallocFree(old);
            return -1;
        }
        _fmemcpy(*song->data, *old, n);
        RallocFree(old);
    }
    mem_Size(song->data);
    for (i = 0; i < 14; i++) {
        if (snd_instrument_descriptors[song->bank[i]].kind == 1) {
            if (snd_load_sample_resource(snd_instrument_descriptors[song->bank[i]].sample) == -1) {
                snd_release_song_resources(song, number);
                return -1;
            }
            snd_instrument_descriptors[song->bank[i]].sample->loaded = 2;
        }
    }
    return 0;
}

void far snd_release_song_resources(struct Song far *song, int number)
{
    int i;
    struct Sample far *s;

    if (song->data != 0) {
        mem_Free(song->data);
        song->data = 0;
    }
    for (i = 0; i < 14; i++) {
        if (snd_instrument_descriptors[song->bank[i]].kind == 1 && (s = snd_instrument_descriptors[song->bank[i]].sample) != 0) {
            if (s->loaded == 2)
                s->loaded = 1;
            snd_queue_sample_release(s);
        }
    }
}

extern void far snd_stop_assigned_voices(void);

void far snd_stop_and_release_samples(void)
{
    int i;

    StopSong();
    snd_stop_assigned_voices();
    for (i = 0; i < 56; i++)
        if (snd_instrument_descriptors[i].kind == 1)
            snd_queue_sample_release(snd_instrument_descriptors[i].sample);
}

extern int far snd_driver_capabilities[];
extern int far midi_playback_state;
extern struct Song far * far snd_active_song_record;
extern void far snd_reap_finished_sample_voices(void);

void far snd_service_pending(void)
{
    if (snd_driver_capabilities[0] != 0) {
        if (midi_playback_state == 2)
            StopSong();
        if (snd_active_song_record->data != 0)
            snd_reap_finished_sample_voices();
        snd_drain_sample_release_queue();
    }
}
