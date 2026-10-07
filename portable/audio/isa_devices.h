#ifndef SIMANT_ISA_AUDIO_DEVICES_H
#define SIMANT_ISA_AUDIO_DEVICES_H
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
void *sim_isa_audio_create(void);
void sim_isa_audio_destroy(void *device);
void sim_isa_audio_out(void *device, uint16_t port, uint8_t value, uint64_t ns);
uint8_t sim_isa_audio_in(void *device, uint16_t port, uint64_t ns);
void sim_isa_audio_render(void *device, int16_t stereo[2], uint64_t ns);
/* Traces are optional observations, never inputs to device execution. */
int sim_isa_audio_trace(void *device, const char *directory);
#ifdef __cplusplus
}
#endif
#endif
