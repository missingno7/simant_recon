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
uint32_t timer_bios_tick_count(void);
int16_t input_return_zero(void);
void mem_exchange_byte_ranges(uint8_t *destination, uint8_t *source, uint16_t count);
int16_t kbd_poll_bios_key(void);
int16_t kbd_read_bios_char(void);
void kbd_unread_char(uint16_t character);
int16_t kbd_read_key_code(void);
void kbd_restore_ctrl_break_vector(void);
void kbd_install_ctrl_break_vector(const uint16_t *new_vector_words);

/* Test-only input observations. Inactive unless explicitly enabled by the
 * acceptance driver; declarations live in this pinned input-service interface. */
#ifdef SIMANT_TEST_OBSERVER_IMPLEMENTATION
#define SIMANT_OBSERVER_WEAK
#else
#define SIMANT_OBSERVER_WEAK __attribute__((weak))
#endif
uint32_t portable_test_clock_read(char kind, void *pc, uint32_t fallback) SIMANT_OBSERVER_WEAK;
void portable_test_pump(void) SIMANT_OBSERVER_WEAK;
void portable_test_window_pump(void) SIMANT_OBSERVER_WEAK;
void portable_test_before_poll(void) SIMANT_OBSERVER_WEAK;
int portable_test_refresh_mode(void) SIMANT_OBSERVER_WEAK;
void portable_test_input_sample(unsigned kind, unsigned value) SIMANT_OBSERVER_WEAK;
void portable_test_irq_context(uint16_t *cx, uint16_t *dx) SIMANT_OBSERVER_WEAK;
void portable_test_replay_error(const char *message) __attribute__((weak));
int portable_test_clock_is_stateful(void) __attribute__((weak));
#undef SIMANT_OBSERVER_WEAK
uint64_t portable_test_pump_ordinal(void);
unsigned portable_test_input_count(void);
void portable_test_input_delivered(unsigned sequence);
static inline uint32_t portable_test_observed_clock(char kind,void *pc,uint32_t fallback)
{
#ifdef SIMANT_TEST_OBSERVER_IMPLEMENTATION
    return portable_test_clock_read(kind,pc,fallback);
#else
    return portable_test_clock_read ? portable_test_clock_read(kind,pc,fallback) : fallback;
#endif
}

#endif
