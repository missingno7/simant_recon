#ifndef SIMANT_WHOLE_AUDIO_PROVIDER_H
#define SIMANT_WHOLE_AUDIO_PROVIDER_H
#include <stdint.h>
#include <stddef.h>
typedef struct PortableWholeAudioProvider {
    void *devices;
    uint64_t time_ns, irq_ns, irq_fraction, frame_cursor;
    uint16_t divisor, chain, mix_divider;
    unsigned channels;
    unsigned timer_generation;
    int armed, fast, in_render, pending_irq;
} PortableWholeAudioProvider;
int portable_whole_audio_provider_init(PortableWholeAudioProvider *p);
void portable_whole_audio_provider_close(PortableWholeAudioProvider *p);
void portable_whole_audio_provider_configure(PortableWholeAudioProvider *p,uint16_t divisor,uint16_t chain,unsigned channels);
void portable_whole_audio_provider_start(PortableWholeAudioProvider *p);
void portable_whole_audio_provider_stop(PortableWholeAudioProvider *p);
void portable_whole_audio_provider_enable_interrupts(PortableWholeAudioProvider *p);
void portable_whole_audio_provider_render_frame(PortableWholeAudioProvider *p,int16_t stereo[2]);
#endif
