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
void f_28BC_0488(int16_t divisor, int16_t chain);
void f_28BC_046B(int16_t divisor, int16_t chain);
void f_28BC_03CC(void);
void f_28BC_040C(void);
void f_28BC_04E0(int16_t divisor);
void f_283E_000A(uint8_t reg, uint8_t value);
void f_283E_0035(void);
void f_29BF_0008(int16_t port);
int16_t f_29BF_0139(void);
void f_29BF_00E6(int16_t reg,int16_t value);
#endif
