/* Fixed source-bounded shared simulation owners, V6. */
#ifndef SIMANT_SOURCE_BOUNDED_SIMULATION_STATE_V6_H
#define SIMANT_SOURCE_BOUNDED_SIMULATION_STATE_V6_H
#include <stdint.h>
#if !defined(SIMANT_NATIVE_LITTLE_ENDIAN) || SIMANT_NATIVE_LITTLE_ENDIAN != 1
#error "V6 serialized-byte overlays require an explicitly little-endian native target"
#endif
#if defined(__BYTE_ORDER__) && defined(__ORDER_LITTLE_ENDIAN__) && (__BYTE_ORDER__ != __ORDER_LITTLE_ENDIAN__)
#error "V6 serialized-byte overlays cannot be used on a big-endian native target"
#endif
typedef union { struct { int16_t x, y; } xy; struct { int16_t v, h; } vh; int16_t words[2]; uint8_t raw_bytes[4]; } NativeSimStatePointV6;
typedef union { int16_t signed_values[64]; uint8_t raw_bytes[128]; } NativeSimStateHistoryV6;

extern NativeSimStatePointV6 native_sim_state_fd_50F6_0508;
extern NativeSimStatePointV6 native_sim_state_fd_50F6_0596;
extern NativeSimStatePointV6 native_sim_state_fd_50F6_06A6;
extern NativeSimStatePointV6 native_sim_state_fd_50F6_072E;
extern NativeSimStatePointV6 native_sim_state_fd_50F6_07BC;
extern NativeSimStatePointV6 native_sim_state_fd_50F6_07CA;
extern NativeSimStatePointV6 native_sim_state_fd_50F6_0852;
extern NativeSimStatePointV6 native_sim_state_fd_50F6_08DE;
extern NativeSimStatePointV6 native_sim_state_fd_50F6_08EC;
extern NativeSimStatePointV6 native_sim_state_fd_50F6_09F2;
extern NativeSimStatePointV6 native_sim_state_fd_50F6_0A02;
extern NativeSimStatePointV6 native_sim_state_fd_50F6_0A8A;
extern NativeSimStatePointV6 native_sim_state_fd_50F6_0AA2;
extern NativeSimStatePointV6 native_sim_state_fd_50F6_0AB2;
extern NativeSimStateHistoryV6 native_sim_state_fd_50F6_0516;
extern NativeSimStateHistoryV6 native_sim_state_fd_50F6_05A0;
extern NativeSimStateHistoryV6 native_sim_state_fd_50F6_0626;
extern NativeSimStateHistoryV6 native_sim_state_fd_50F6_06AE;
extern NativeSimStateHistoryV6 native_sim_state_fd_50F6_073C;
extern NativeSimStateHistoryV6 native_sim_state_fd_50F6_07CE;
extern NativeSimStateHistoryV6 native_sim_state_fd_50F6_0856;
extern NativeSimStateHistoryV6 native_sim_state_fd_50F6_08F0;
extern NativeSimStateHistoryV6 native_sim_state_fd_50F6_0970;
extern NativeSimStateHistoryV6 native_sim_state_fd_50F6_0A0A;

#endif
