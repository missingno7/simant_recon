/* Native reference for the source-visible release/reset helper contracts.
 * Test-only model: it does not implement DOS heap internals or ISA writes.
 */
#include <stdint.h>
#include <inttypes.h>
#include <stdio.h>
#include <string.h>

enum { BANKS = 14, CHANNELS = 6, FREE_CAP = 39 };

typedef struct Sample {
    uint32_t data_handle;
    int16_t loaded;
} Sample;

typedef struct Instrument {
    int16_t kind;
    int16_t sample_index;
} Instrument;

typedef struct Song {
    uint16_t bank[BANKS];
    uint32_t data_handle;
} Song;

typedef struct Channel {
    uint8_t type, num, c2, c3, c4, c5;
} Channel;

typedef struct FreeList {
    int count;
    int sample[FREE_CAP];
} FreeList;

static const int kinds[BANKS] = { 1, 1, 2, 1, 1, 1, 2, 1, 1, 1, 2, 1, 1, 1 };
static const int sample_indices[BANKS] = { 0, 1, 2, -1, 4, 5, 6, 7, 8, 9, 10, -1, 12, 13 };
static const int initial_loaded[BANKS] = { 2, 1, 1, 0, 0, 2, 1, 2, 1, 0, 1, 0, 2, 1 };

static void release_handle(const char *kind, uint32_t handle)
{
    printf("%s|handle=%" PRIu32 "\n", kind, handle);
}

static void flush(Sample samples[BANKS], FreeList *free_list)
{
    int i;
    printf("flush_begin|count=%d|samples=", free_list->count);
    for (i = 0; i < free_list->count; ++i)
        printf("%s%d", i == 0 ? "" : ",", free_list->sample[i]);
    putchar('\n');
    for (i = 0; i < free_list->count; ++i) {
        Sample *sample = &samples[free_list->sample[i]];
        if (sample->loaded == 1 && sample->data_handle != 0) {
            release_handle("free_sample_data", sample->data_handle);
            sample->data_handle = 0;
            sample->loaded = 0;
        }
    }
    free_list->count = 0;
    printf("flush_end|count=%d\n", free_list->count);
}

static void release_song(Song *song, Instrument instruments[BANKS],
                         Sample samples[BANKS], FreeList *free_list,
                         int busy, int song_number)
{
    int i;
    (void)song_number; /* f_0000_039B declares but never reads this argument. */
    if (song->data_handle != 0) {
        release_handle("free_song_data", song->data_handle);
        song->data_handle = 0;
    }
    for (i = 0; i < BANKS; ++i) {
        const uint16_t bank = song->bank[i];
        const int index = instruments[bank].sample_index;
        if (instruments[bank].kind == 1 && index >= 0) {
            Sample *sample = &samples[index];
            if (sample->loaded == 2) sample->loaded = 1;
            if (free_list->count >= FREE_CAP) return;
            free_list->sample[free_list->count++] = index;
            if (!busy) flush(samples, free_list);
        }
    }
}

static void reset_channels(Channel channels[CHANNELS + 1])
{
    int i;
    for (i = 0; channels[i].type != 0; ++i) {
        /* c3 is uint8_t; source's c3 >= 0 is tautological. */
        if (channels[i].c2 != 0)
            printf("noteoff|device=%u|note=%u\n", channels[i].c3, channels[i].c4);
    }
}

static void initialize(Song *song, Instrument instruments[BANKS],
                       Sample samples[BANKS], FreeList *free_list)
{
    int i;
    memset(song, 0, sizeof(*song));
    memset(instruments, 0, sizeof(Instrument) * BANKS);
    memset(samples, 0, sizeof(Sample) * BANKS);
    memset(free_list, 0, sizeof(*free_list));
    song->data_handle = 900;
    for (i = 0; i < BANKS; ++i) {
        song->bank[i] = (uint16_t)i;
        instruments[i].kind = (int16_t)kinds[i];
        instruments[i].sample_index = (int16_t)sample_indices[i];
        samples[i].loaded = (int16_t)initial_loaded[i];
        samples[i].data_handle = initial_loaded[i] != 0 ? (uint32_t)(1000 + i) : 0;
    }
}

static void run_release(int deferred)
{
    Song song;
    Instrument instruments[BANKS];
    Sample samples[BANKS];
    FreeList free_list;
    int calls = deferred ? 2 : 1;
    int i, call;
    initialize(&song, instruments, samples, &free_list);
    for (call = 0; call < calls; ++call) {
        printf("release_call|index=%d|busy=%d\n", call, deferred);
        release_song(&song, instruments, samples, &free_list, deferred, 11006);
    }
    printf("queue_state|count=%d|song_handle=%" PRIu32 "\n",
           free_list.count, song.data_handle);
    if (deferred) flush(samples, &free_list);
    for (i = 0; i < BANKS; ++i)
        printf("sample|index=%d|loaded=%d|data=%" PRIu32 "\n",
               i, samples[i].loaded, samples[i].data_handle);
    printf("final|queue=%d|song_handle=%" PRIu32 "\n",
           free_list.count, song.data_handle);
}

static void run_reset(int unsigned_boundary)
{
    Channel channels[CHANNELS + 1];
    int i;
    memset(channels, 0, sizeof(channels));
    for (i = 0; i < CHANNELS; ++i) {
        channels[i].type = (uint8_t)(i + 1);
        channels[i].num = (uint8_t)i;
        channels[i].c2 = (uint8_t)(i != 1 && i != 4);
        channels[i].c3 = (uint8_t)i;
        channels[i].c4 = (uint8_t)(60 + i);
        channels[i].c5 = (uint8_t)(i + 2);
    }
    if (unsigned_boundary) {
        channels[2].c3 = 0xff;
        channels[2].c2 = 1;
    }
    channels[CHANNELS].type = 0;
    reset_channels(channels);
    puts("reset_done");
}

int main(int argc, char **argv)
{
    if (argc != 2) return 2;
    if (strcmp(argv[1], "release-immediate") == 0) run_release(0);
    else if (strcmp(argv[1], "release-deferred-repeat") == 0) run_release(1);
    else if (strcmp(argv[1], "reset-six") == 0) run_reset(0);
    else if (strcmp(argv[1], "reset-u8-boundary") == 0) run_reset(1);
    else return 2;
    return 0;
}
