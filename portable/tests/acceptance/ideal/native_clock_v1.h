#ifndef DOS_CLOCK_NATIVE_V1_H
#define DOS_CLOCK_NATIVE_V1_H
#include <stdint.h>
#include <string.h>
/* Independent DOS spelling of native-clock-v1, shared with the emulator and
 * tested using the unmodified native golden-vector fixture. No read history. */
static uint64_t DosClockReadQuantum(const char *service,uint64_t quantum_ns) {
    static const char *const reads[]={
        "TickCount","host_ticks","portable_m1b73_source_countdown_get",
        "host_key_available","host_read_key_blocking","input_event_count",
        "kbd_scan_state","kbd_scroll_lock_state","dos_keyboard_modifiers",
        "portable_input_time_host_get_input_state","mouse_refresh_cursor"
    };
    if(!service) return 0;
    for(unsigned i=0;i<sizeof(reads)/sizeof(reads[0]);++i)
        if(!strcmp(service,reads[i])) return quantum_ns;
    return 0;
}
#endif
