#ifndef SIMANT_WHOLE_PROGRAM_PLATFORM_INPUT_TIME_H
#define SIMANT_WHOLE_PROGRAM_PLATFORM_INPUT_TIME_H

#include <stdint.h>

typedef enum PortableInputTimeStatus {
    PORTABLE_INPUT_TIME_OK = 0,
    PORTABLE_INPUT_TIME_BAD_ARGUMENT,
    PORTABLE_INPUT_TIME_PROVIDER_MISSING,
    PORTABLE_INPUT_TIME_PROVIDER_FAILED,
    PORTABLE_INPUT_TIME_INVALID_LIFETIME
} PortableInputTimeStatus;

typedef void (*PortableInputTimeCleanup)(void *context);

typedef struct PortableInputTimeServices {
    void *context;
    /* Returns the source BIOS TickCount domain: modulo-2^32 18.2Hz logical
     * ticks. The provider owns timing and must not use SDL event timestamps. */
    int (*read_logical_bios_ticks)(void *context, uint32_t *ticks);
    /* key_available returns 1 with a BIOS AX word, 0 for no key, -1 on error. */
    int (*key_available)(void *context, uint16_t *bios_key);
    /* Blocking source read: returns 1 with a BIOS AX word or -1 on failure.
     * It must not synthesize an empty key when the host has no input. */
    int (*read_key_blocking)(void *context, uint16_t *bios_key);
    /* Clear BIOS NumLock state when the source g_53BD policy byte is nonzero. */
    int (*clear_numlock_state)(void *context);
    /* Atomically install/restore the caller's Ctrl-Break vector. A failed
     * install must leave the current vector unchanged. Vectors are
     * represented offset in low 16 bits and segment in high 16 bits. */
    int (*install_ctrl_break)(void *context, uint32_t new_vector,
                              uint32_t *old_vector);
    int (*restore_ctrl_break)(void *context, uint32_t old_vector);
    /* Registers the source atexit-style restoration with the application. */
    int (*register_exit_cleanup)(void *context,
                                 PortableInputTimeCleanup cleanup,
                                 void *cleanup_context);
} PortableInputTimeServices;

typedef struct PortableInputTime {
    PortableInputTimeServices services;
    uint16_t pending_key;
    uint16_t second_pending_key;
    uint32_t saved_ctrl_break_vector;
    uint8_t clear_numlock_policy; /* source g_53BD */
    uint8_t ctrl_break_installed;
    uint8_t ctrl_break_saved_valid;
    PortableInputTimeStatus cleanup_status;
} PortableInputTime;

void portable_input_time_init(PortableInputTime *input_time,
                              const PortableInputTimeServices *services);
PortableInputTimeStatus portable_input_time_bind(PortableInputTime *input_time);
void portable_input_time_unbind(PortableInputTime *input_time);
void portable_input_time_set_numlock_policy(PortableInputTime *input_time,
                                            uint8_t source_g_53BD);
PortableInputTimeStatus portable_input_time_read_ticks(PortableInputTime *input_time,
                                                        uint32_t *ticks);
PortableInputTimeStatus portable_input_time_key_available(PortableInputTime *input_time,
                                                           int16_t *bios_ax);
PortableInputTimeStatus portable_input_time_read_char(PortableInputTime *input_time,
                                                      int16_t *character);
PortableInputTimeStatus portable_input_time_read_key(PortableInputTime *input_time,
                                                     int16_t *key);
PortableInputTimeStatus portable_input_time_pushback(PortableInputTime *input_time,
                                                     uint8_t character);
PortableInputTimeStatus portable_input_time_restore_ctrl_break(PortableInputTime *input_time);

/* Original public entrypoint spellings. Native pointers replace DOS far
 * pointers; callers must bind a configured provider before hardware services. */
uint32_t f_1F58_0006(void);
int16_t f_1F58_0014(void);
void f_1F58_0017(uint8_t *destination, uint8_t *source, uint16_t count);
int16_t f_1F58_0038(void);
int16_t f_1F58_005A(void);
void f_1F58_007F(uint16_t character);
int16_t f_1F58_0090(void);
void f_1F58_00A1(void);
void f_1F58_00B8(const uint16_t *new_vector_words);

#endif
