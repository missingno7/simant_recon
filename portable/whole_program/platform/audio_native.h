#ifndef SIMANT_AUDIO_NATIVE_H
#define SIMANT_AUDIO_NATIVE_H
#include <stdint.h>
typedef struct PortableWholeAudioHost {
    void *context;
    void (*configure_timer)(void *, uint16_t, uint16_t, unsigned);
    void (*start_timer)(void *);
    void (*stop_timer)(void *);
    void (*out8)(void *, uint16_t, uint8_t);
    uint8_t (*in8)(void *, uint16_t);
    void (*enable_interrupts)(void *);
} PortableWholeAudioHost;
int portable_whole_audio_bind(const PortableWholeAudioHost *host);
void portable_whole_audio_unbind(void);
int portable_whole_audio_timer_armed(void);
int portable_whole_audio_interrupts_enabled(void);
void snd_select_two_channel_timer(int16_t divisor, int16_t chain);
void snd_select_four_channel_timer(int16_t divisor, int16_t chain);
void snd_start_sample_timer(void);
void snd_slow_sample_timer(void);
void snd_restore_bios_timer(int16_t divisor);
void snd_opl_write(uint8_t reg, uint8_t value);
void snd_opl_probe_tone(void);
void snd_regchip_initialize(int16_t port);
int16_t snd_regchip_detect(void);
void snd_regchip_write(int16_t reg,int16_t value);
#endif
