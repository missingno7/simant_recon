#include "portable/game/resources/database.h"
#include "portable/audio/intent.h"
#include "portable/whole_program/platform/audio_events.h"
#include "portable/whole_program/platform/whole_audio_provider.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#pragma pack(push, 1)
struct HostSample {
    char **data;
    uint16_t len;
    uint16_t loop;
    char looped;
    uint8_t octave;
    int16_t tune;
    int16_t loaded;
    char name[15];
    int16_t object;
};
#pragma pack(pop)

#pragma pack(push, 2)
struct HostSong {
    int16_t program[14];
    int16_t bank[14];
    char **data;
};

struct HostVoice {
    int16_t kind;
    void *payload;
};

struct HostChannel {
    char type;
    char num;
    char c2;
    char c3;
    char c4;
    char c5;
};

struct HostSndChannel {
    uint16_t pos;
    struct HostSample *snd;
    uint16_t end;
    uint16_t start;
    uint16_t step;
    uint16_t voltab;
    uint8_t frac;
    uint8_t flags;
    struct HostSample *owner;
};

struct HostSlot {
    int32_t busy;
    int16_t w4;
    int16_t w6;
    int16_t w8;
    int16_t wA;
    int16_t wC;
    void *snd;
    int16_t w12;
};
#pragma pack(pop)

typedef struct HostResource {
    char *bytes;
    char **handle;
    size_t size;
} HostResource;

static PortableDatabase sound_db;
static PortableWholeAudioEventQueue event_queue;
static PortableWholeAudioProvider provider;
static HostResource host_resources[64];
static size_t host_resource_count;

/* These BSS symbols are original source-owned state shared by the generated
 * modules. Their field layouts are taken from the generated TU declarations. */
struct HostVoice fd_50F6_0000[56];
struct HostChannel fd_50F6_4A4E[64];
struct HostSlot fd_55B3_6B4E[64];
struct HostSndChannel fd_55B3_6B4C[2];
int16_t fd_50F6_01F0[8];
int16_t fd_50F6_4A48;
int16_t fd_50F6_4A4C;
int16_t fd_50F6_4B2C;
int16_t fd_50F6_4B2E;
char **fd_50F6_4B28;
int16_t fd_50F6_4B8E[14];
int16_t fd_50F6_4BAA[14];
int32_t fd_50F6_4B42[18];
uint8_t fd_50F6_4B30[18];
int32_t fd_50F6_4B8A;
int16_t fd_55B3_6B42;
int16_t fd_55B3_74AD = 0x100;
int16_t fd_55B3_6B9C;
uint16_t fd_55B3_6B9E;
extern int16_t fd_55B3_74C0;

extern struct HostSong *fd_55B3_00B4;
extern struct HostVoice fd_55B3_0C42[56];
extern void f_284A_0013(int16_t number);
extern int16_t f_284A_067F(void);
extern int16_t f_290D_0193(int16_t instrument, int16_t note,
                            int16_t volume, int16_t channel);
extern void f_295C_01EC(int16_t priority, int16_t device,
                         int16_t note, int16_t velocity);
extern int16_t g_756E;
extern int16_t g_7576;
extern int16_t g_7578;

static uint16_t read_be16(const uint8_t *p)
{
    return (uint16_t)(((uint16_t)p[0] << 8) | p[1]);
}

static HostResource *retain_resource(void *bytes, size_t size)
{
    HostResource *r;
    if (host_resource_count == sizeof(host_resources) / sizeof(host_resources[0]))
        return NULL;
    r = &host_resources[host_resource_count++];
    r->bytes = (char *)bytes;
    r->handle = (char **)malloc(sizeof(*r->handle));
    if (r->handle == NULL) return NULL;
    *r->handle = r->bytes;
    r->size = size;
    return r;
}

static void release_resources(void)
{
    size_t i;
    for (i = 0; i < host_resource_count; ++i) {
        free(host_resources[i].handle);
        free(host_resources[i].bytes);
    }
    host_resource_count = 0;
}

static int load_database_record(int16_t id, int16_t kind,
                                HostResource **out)
{
    PortableDbRecord record;
    PortableDbStatus status = portable_db_load(&sound_db, id, kind, &record);
    HostResource *r;
    if (status != PORTABLE_DB_OK) {
        fprintf(stderr, "SOUND record %d/%d: %s\n", id, kind,
                portable_db_status_string(status));
        return 0;
    }
    r = retain_resource(record.data, record.size);
    if (r == NULL) {
        portable_db_record_free(&record);
        return 0;
    }
    record.data = NULL;
    portable_db_record_free(&record);
    *out = r;
    return 1;
}

static int attach_actual_sample(struct HostSample *sample)
{
    uint8_t *pcm = NULL;
    size_t pcm_size = 0;
    HostResource *resource;
    PortableAudioPcmStatus status;
    if (sample->loaded != 0) return 1;
    status = portable_audio_load_sample_pcm(&sound_db, sample->object,
                                            &pcm, &pcm_size);
    if (status != PORTABLE_AUDIO_PCM_OK || pcm_size > UINT16_MAX) {
        fprintf(stderr, "SOUND sample %d load failed (%d, %zu bytes)\n",
                sample->object, (int)status, pcm_size);
        portable_audio_free_pcm(pcm);
        return 0;
    }
    resource = retain_resource((char *)pcm, pcm_size);
    if (resource == NULL) {
        portable_audio_free_pcm(pcm);
        return 0;
    }
    sample->data = resource->handle;
    sample->len = (uint16_t)pcm_size;
    sample->loaded = 2; /* Source marks song-held samples while its data is live. */
    return 1;
}

/* Bounded host implementation of f_0000_0193's DB/handle boundary. Header and
 * MIDI payloads are the actual SOUND kind-18/kind-20 resources. The generated
 * m284A parser, scheduler, voice allocator, and m290D sampler remain in-band. */
int16_t f_0000_0193(struct HostSong *song, int16_t number)
{
    HostResource *header;
    HostResource *midi;
    uint16_t midi_id;
    unsigned i;
    if (song == NULL || !load_database_record(number, 0x12, &header) ||
        header->size < 8)
        return -1;
    midi_id = read_be16((const uint8_t *)header->bytes);
    g_7576 = (int16_t)read_be16((const uint8_t *)header->bytes + 6);
    g_7578 = (int16_t)midi_id;
    if (!load_database_record((int16_t)midi_id, 0x14, &midi))
        return -1;
    song->data = midi->handle;
    for (i = 0; i < 14; ++i) {
        struct HostVoice *voice;
        if (song->bank[i] < 0 || song->bank[i] >= 56) return -1;
        voice = &fd_50F6_0000[song->bank[i]];
        if (voice->kind == 1 &&
            !attach_actual_sample((struct HostSample *)voice->payload))
            return -1;
    }
    return 0;
}

int32_t f_171C_1C1C(char **handle)
{
    size_t i;
    for (i = 0; i < host_resource_count; ++i)
        if (host_resources[i].handle == handle)
            return (int32_t)host_resources[i].size;
    return 0;
}

/* These are synchronous host boundaries called only for resource ownership,
 * diagnostics, and interrupt exclusion in this deterministic harness. */
void f_0000_039B(struct HostSong *song, int16_t number)
{
    (void)song;
    (void)number;
}
void f_0000_046F(void) {}
int16_t f_0000_0090(struct HostSample *sample) { (void)sample; return 0; }
void f_0000_0149(struct HostSample *sample) { (void)sample; }
void f_29F0_000A(void) {}
void f_29F0_0012(void) {}
void f_29F0_001A(void) {}
void f_29F0_0022(void) {}
void f_28BC_03CC(void) {}
void WinPrintf(char *format, ...) { (void)format; }
void dos_audio_host_song_bounds_fault(void)
{ fputs("source song read escaped the loaded record\n", stderr); abort(); }

/* Unselected instrument families remain explicit non-implementations. The
 * chosen mode-1 table entries dispatch through f_290D from actual m295C. */
void f_2815_0165(void) {}
void f_2815_024D(void) {}
void f_2815_0275(void) {}
void f_29D6_000A(void) {}
void f_29D6_0082(void) {}
void f_29D6_00D9(void) {}
void f_29D6_0148(void) {}
void f_29D6_015D(void) {}
void f_29D6_0197(void) {}
uint8_t f_29F0_0038(int16_t port) { (void)port; return 0; }
void f_29F0_002A(int16_t port, int16_t value)
{ (void)port; (void)value; }

static uint64_t event_clock(void *context)
{
    PortableWholeAudioProvider *p = (PortableWholeAudioProvider *)context;
    return p->sample_cursor + 1;
}

int main(int argc, char **argv)
{
    const char *sound_root = argc > 1 ? argv[1] : "assets/SOUND";
    uint8_t block[256];
    uint64_t frames = 0;
    uint64_t frame_limit = 11932u * 60u;
    size_t nonzero = 0;
    size_t max_active = 0;
    unsigned i;
    PortableDbStatus db_status;
    PortableWholeAudioProviderStatus provider_status;
    if (argc > 2) frame_limit = strtoull(argv[2], NULL, 10);
    db_status = portable_db_open(&sound_db, sound_root);
    if (db_status != PORTABLE_DB_OK) {
        fprintf(stderr, "cannot open %s: %s\n", sound_root,
                portable_db_status_string(db_status));
        return 2;
    }

    /* Source f_277E_010A copies the selected mode-1 voice table. The test
     * seeds that exact table and source channel topology from its DATA owner. */
    memcpy(fd_50F6_0000, fd_55B3_0C42, sizeof(fd_50F6_0000));
    memset(fd_50F6_4A4E, 0, sizeof(fd_50F6_4A4E));
    memset(fd_55B3_6B4E, 0, sizeof(fd_55B3_6B4E));
    fd_50F6_4A4E[0].type = 1;
    fd_50F6_4A4E[0].num = 0;
    fd_50F6_4A4E[0].c3 = -1;
    fd_50F6_4A4E[1].type = 1;
    fd_50F6_4A4E[1].num = 1;
    fd_50F6_4A4E[1].c3 = -1;
    fd_50F6_4A48 = 2;
    fd_50F6_01F0[1] = 2;
    fd_55B3_74C0 = 0x40;

    portable_whole_audio_event_queue_init(&event_queue);
    portable_whole_audio_provider_init(&provider);
    if (!portable_whole_audio_event_queue_bind_clock(&event_queue,
                                                     event_clock, &provider))
        return 4;
    portable_whole_audio_provider_set_sequencer(&provider, &fd_55B3_6B42,
                                                 f_284A_067F);

    f_284A_0013(10001);
    if (g_756E != 1 || fd_50F6_4B2C <= 0) {
        fprintf(stderr, "song failed to enter PLAYING: state=%d size=%d\n",
                g_756E, fd_50F6_4B2C);
        return 5;
    }

    while (frames < frame_limit && g_756E == 1) {
        size_t count = (size_t)((frame_limit - frames) < sizeof(block) ?
                                frame_limit - frames : sizeof(block));
        provider_status = portable_whole_audio_provider_render(
            &provider, &event_queue, block, count);
        if (provider_status != PORTABLE_WHOLE_AUDIO_PROVIDER_OK) {
            fprintf(stderr, "native song render error %d at frame %llu\n",
                    (int)provider_status, (unsigned long long)frames);
            return 6;
        }
        for (i = 0; i < count; ++i) nonzero += block[i] != 0x80;
        {
            size_t active = 0;
            for (i = 0; i < PORTABLE_WHOLE_AUDIO_DAC_CHANNELS; ++i)
                active += provider.scheduler.voices[i].pcm != NULL;
            if (active > max_active) max_active = active;
        }
        frames += count;
    }

    if (g_756E != 2) {
        fprintf(stderr, "song did not reach source end state: state=%d frames=%llu\n",
                g_756E, (unsigned long long)frames);
        return 7;
    }
    if (max_active == 0 || provider.last_sequence == 0 || nonzero == 0) {
        fprintf(stderr, "generated source produced no DAC timeline/audio: active=%zu events=%llu noncenter=%zu\n",
                max_active, (unsigned long long)provider.last_sequence,
                nonzero);
        return 8;
    }

    printf("PASS source-song=10001 midi-resource=%d transpose=%d midi-bytes=%d frames=%llu source-end=%d max-active-voices=%zu committed-events=%llu noncenter-samples=%zu\n",
           g_7578, g_7576, fd_50F6_4B2C, (unsigned long long)frames,
           g_756E, max_active,
           (unsigned long long)provider.last_sequence, nonzero);
    portable_whole_audio_event_queue_close(&event_queue);
    portable_whole_audio_provider_close(&provider);
    release_resources();
    portable_db_close(&sound_db);
    return 0;
}
