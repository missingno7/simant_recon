/* Fixed source-bounded simulation-array owners V7. */
#ifndef SIMANT_SOURCE_BOUNDED_SIMULATION_STATE_V7_H
#define SIMANT_SOURCE_BOUNDED_SIMULATION_STATE_V7_H
#include <stdint.h>
typedef struct NativeV7TriLevel { uint16_t frac, mid, weight; } NativeV7TriLevel;
#if !defined(SIMANT_NATIVE_LITTLE_ENDIAN) || SIMANT_NATIVE_LITTLE_ENDIAN != 1
#error "V7 raw SaveRec byte overlays require an explicitly little-endian native target"
#endif
#if defined(__BYTE_ORDER__) && defined(__ORDER_LITTLE_ENDIAN__) && (__BYTE_ORDER__ != __ORDER_LITTLE_ENDIAN__)
#error "V7 raw SaveRec byte overlays cannot be used on a big-endian target"
#endif

typedef union { int8_t signed_values[50]; uint8_t unsigned_values[50]; uint8_t raw_bytes[50]; } NativeV7_fd_50F6_0F46;
extern NativeV7_fd_50F6_0F46 native_sim_state_fd_50F6_0F46;
typedef union { int8_t signed_values[50]; uint8_t unsigned_values[50]; uint8_t raw_bytes[50]; } NativeV7_fd_50F6_0FC6;
extern NativeV7_fd_50F6_0FC6 native_sim_state_fd_50F6_0FC6;
typedef union { int8_t signed_values[50]; uint8_t unsigned_values[50]; uint8_t raw_bytes[50]; } NativeV7_fd_50F6_0F84;
extern NativeV7_fd_50F6_0F84 native_sim_state_fd_50F6_0F84;
typedef union { int8_t signed_values[50]; uint8_t unsigned_values[50]; uint8_t raw_bytes[50]; } NativeV7_fd_50F6_1008;
extern NativeV7_fd_50F6_1008 native_sim_state_fd_50F6_1008;
typedef union { uint8_t unsigned_values[100]; uint8_t raw_bytes[100]; } NativeV7_fd_50F6_0256;
extern NativeV7_fd_50F6_0256 native_sim_state_fd_50F6_0256;
typedef union { uint8_t unsigned_values[100]; uint8_t raw_bytes[100]; } NativeV7_fd_50F6_02C0;
extern NativeV7_fd_50F6_02C0 native_sim_state_fd_50F6_02C0;
typedef union { int16_t signed_values[12]; uint16_t unsigned_values[12]; uint8_t raw_bytes[24]; } NativeV7_fd_50F6_0334;
extern NativeV7_fd_50F6_0334 native_sim_state_fd_50F6_0334;
typedef union { int16_t signed_values[6]; uint16_t unsigned_values[6]; uint8_t raw_bytes[12]; } NativeV7_fd_50F6_0AEC;
extern NativeV7_fd_50F6_0AEC native_sim_state_fd_50F6_0AEC;
typedef union { int16_t signed_values[6]; uint16_t unsigned_values[6]; uint8_t raw_bytes[12]; } NativeV7_fd_50F6_0AFA;
extern NativeV7_fd_50F6_0AFA native_sim_state_fd_50F6_0AFA;
typedef union { int16_t signed_values[6]; uint16_t unsigned_values[6]; uint8_t raw_bytes[12]; } NativeV7_fd_50F6_0B12;
extern NativeV7_fd_50F6_0B12 native_sim_state_fd_50F6_0B12;
typedef union { int16_t signed_values[6]; uint16_t unsigned_values[6]; uint8_t raw_bytes[12]; } NativeV7_fd_50F6_0C2A;
extern NativeV7_fd_50F6_0C2A native_sim_state_fd_50F6_0C2A;
typedef union { NativeV7TriLevel tri; int16_t signed_values[3]; uint16_t unsigned_values[3]; uint8_t raw_bytes[6]; } NativeV7_casteLevels;
extern NativeV7_casteLevels native_sim_state_casteLevels;
typedef union { NativeV7TriLevel tri; int16_t signed_values[3]; uint16_t unsigned_values[3]; uint8_t raw_bytes[6]; } NativeV7_modeLevels;
extern NativeV7_modeLevels native_sim_state_modeLevels;

#endif
