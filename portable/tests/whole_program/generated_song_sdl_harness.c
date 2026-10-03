#define main generated_song_direct_harness_main
#include "generated_song_harness.c"
#undef main

#include "portable/platform/sdl3/whole_audio_provider.h"
#include <SDL3/SDL.h>

extern void StopSong(void);

static size_t song_tick_calls;

static int16_t counted_song_tick(void)
{
    ++song_tick_calls;
    return f_284A_067F();
}

static int any_native_voice(const PortableSdl3WholeAudio *audio)
{
    unsigned i;
    for (i = 0; i < PORTABLE_WHOLE_AUDIO_DAC_CHANNELS; ++i)
        if (audio->provider.scheduler.voices[i].pcm != NULL) return 1;
    return 0;
}

static int pump_for(PortableSdl3WholeAudio *audio, uint64_t milliseconds,
                    size_t target_frames)
{
    uint64_t deadline = SDL_GetTicksNS() + milliseconds * UINT64_C(1000000);
    while (SDL_GetTicksNS() < deadline) {
        PortableSdl3WholeAudioStatus status = portable_sdl3_whole_audio_pump(
            audio, target_frames);
        if (status != PORTABLE_SDL3_WHOLE_AUDIO_OK) {
            fprintf(stderr, "SDL whole-audio pump failed: %d: %s\n",
                    (int)status, SDL_GetError());
            return 0;
        }
        SDL_Delay(1);
    }
    return 1;
}

static int pump_until_song_end(PortableSdl3WholeAudio *audio,
                               uint64_t timeout_ms)
{
    uint64_t deadline = SDL_GetTicksNS() + timeout_ms * UINT64_C(1000000);
    while (g_756E == 1 && SDL_GetTicksNS() < deadline) {
        PortableSdl3WholeAudioStatus status = portable_sdl3_whole_audio_pump(
            audio, 2048);
        if (status != PORTABLE_SDL3_WHOLE_AUDIO_OK) {
            fprintf(stderr, "SDL whole-audio pump failed: %d: %s\n",
                    (int)status, SDL_GetError());
            return 0;
        }
        SDL_Delay(2);
    }
    return g_756E == 2;
}

static int pump_until_source_note(PortableSdl3WholeAudio *audio,
                                  uint64_t timeout_ms)
{
    uint64_t deadline = SDL_GetTicksNS() + timeout_ms * UINT64_C(1000000);
    while (SDL_GetTicksNS() < deadline) {
        PortableSdl3WholeAudioStatus status = portable_sdl3_whole_audio_pump(
            audio, 512);
        if (status != PORTABLE_SDL3_WHOLE_AUDIO_OK) return 0;
        if ((fd_50F6_4A4E[0].c2 != 0 || fd_50F6_4A4E[1].c2 != 0) &&
            any_native_voice(audio))
            return 1;
        SDL_Delay(1);
    }
    return 0;
}

int main(int argc, char **argv)
{
    const char *sound_root = argc > 1 ? argv[1] : "assets/SOUND";
    PortableSdl3WholeAudio audio;
    uint64_t first_tick_calls;
    uint64_t cancel_cursor;
    uint64_t restart_cursor;
    uint64_t sequence_before_cancel;
    uint64_t sequence_after_cancel;
    int16_t active_divider;
    size_t voices_before_cancel;
    size_t voices_after_cancel = 0;
    size_t max_active = 0;
    uint64_t started = SDL_GetTicksNS();
    PortableDbStatus db_status = portable_db_open(&sound_db, sound_root);
    if (db_status != PORTABLE_DB_OK) {
        fprintf(stderr, "cannot open %s: %s\n", sound_root,
                portable_db_status_string(db_status));
        return 2;
    }

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
    if (!portable_sdl3_whole_audio_open(
            &audio, &event_queue,
            PORTABLE_SDL3_WHOLE_AUDIO_MODE1_SAMPLED_DAC)) {
        fputs("cannot open SDL3 dummy output stream\n", stderr);
        return 3;
    }
    portable_sdl3_whole_audio_set_sequencer(&audio, &fd_55B3_6B42,
                                             counted_song_tick);

    f_284A_0013(10001);
    if (g_756E != 1 || fd_55B3_6B42 != 5) {
        fprintf(stderr, "first source start failed: state=%d divider=%d\n",
                g_756E, fd_55B3_6B42);
        return 4;
    }
    if (!pump_for(&audio, 200, 512)) return 5;
    if (song_tick_calls == 0 || audio.provider.sample_cursor == 0) {
        fputs("generated song sequencer did not advance on SDL stream frames\n",
              stderr);
        return 6;
    }
    active_divider = fd_55B3_6B42;
    if (!pump_until_source_note(&audio, 2000)) {
        fputs("actual song did not activate a source MIDI voice and SDL sample\n",
              stderr);
        return 8;
    }
    if (audio.provider.scheduler.allocator.channels[0].active)
        ++max_active;
    if (audio.provider.scheduler.allocator.channels[1].active)
        ++max_active;

    first_tick_calls = song_tick_calls;
    voices_before_cancel =
        (size_t)audio.provider.scheduler.allocator.channels[0].active +
        (size_t)audio.provider.scheduler.allocator.channels[1].active;
    sequence_before_cancel = audio.provider.last_sequence;
    StopSong();
    cancel_cursor = audio.provider.sample_cursor;
    if (g_756E != 0 || !pump_for(&audio, 120, 512)) {
        fprintf(stderr, "source StopSong failed: state=%d\n", g_756E);
        return 9;
    }
    voices_after_cancel =
        (size_t)audio.provider.scheduler.allocator.channels[0].active +
        (size_t)audio.provider.scheduler.allocator.channels[1].active;
    sequence_after_cancel = audio.provider.last_sequence;
    if (audio.provider.sample_cursor <= cancel_cursor ||
        sequence_after_cancel <= sequence_before_cancel ||
        voices_after_cancel >= voices_before_cancel) {
        fprintf(stderr, "source cancellation produced no applied voice stop: before=%zu after=%zu sequence=%llu..%llu\n",
                voices_before_cancel, voices_after_cancel,
                (unsigned long long)sequence_before_cancel,
                (unsigned long long)audio.provider.last_sequence);
        return 10;
    }

    f_284A_0013(10001);
    if (g_756E != 1 || fd_55B3_6B42 != 5) {
        fprintf(stderr, "source song restart failed: state=%d divider=%d\n",
                g_756E, fd_55B3_6B42);
        return 11;
    }
    restart_cursor = audio.provider.sample_cursor;
    if (!pump_until_song_end(&audio, 10000)) {
        fprintf(stderr, "restarted original song did not reach source end (state=%d)\n",
                g_756E);
        return 12;
    }
    if (audio.provider.sample_cursor <= restart_cursor ||
        song_tick_calls <= first_tick_calls) {
        fputs("restarted sequencer did not advance on the second song pass\n",
              stderr);
        return 13;
    }
    printf("PASS SDL3 dummy song=10001 cursor=%llu source-end=%d first-ticks=%llu total-ticks=%llu active-during-play=%zu cancellation-voices=%zu->%zu cancellation-events=%llu divider-after-first-pass=%d elapsed-ms=%llu\n",
           (unsigned long long)audio.provider.sample_cursor, g_756E,
           (unsigned long long)first_tick_calls,
           (unsigned long long)song_tick_calls, max_active,
           voices_before_cancel, voices_after_cancel,
           (unsigned long long)(sequence_after_cancel -
                                sequence_before_cancel), active_divider,
           (unsigned long long)((SDL_GetTicksNS() - started) / 1000000u));
    portable_sdl3_whole_audio_close(&audio);
    release_resources();
    portable_db_close(&sound_db);
    SDL_Quit();
    return 0;
}
