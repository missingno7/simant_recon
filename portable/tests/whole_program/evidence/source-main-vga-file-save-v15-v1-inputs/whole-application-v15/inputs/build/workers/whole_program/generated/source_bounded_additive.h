/* Additive source-bounded owners V5; diagnostic until reviewed. */
#ifndef SIMANT_SOURCE_BOUNDED_ADDITIVE_V5_H
#define SIMANT_SOURCE_BOUNDED_ADDITIVE_V5_H
#include <stdint.h>

/* Cycle has an original unsigned-byte alias to the low byte of a DOS word. */
#if !defined(SIMANT_NATIVE_LITTLE_ENDIAN) || SIMANT_NATIVE_LITTLE_ENDIAN != 1
#error "V5 Cycle byte alias requires an explicitly little-endian native target"
#endif
#if defined(__BYTE_ORDER__) && defined(__ORDER_LITTLE_ENDIAN__) && (__BYTE_ORDER__ != __ORDER_LITTLE_ENDIAN__)
#error "V5 Cycle byte alias cannot be used on a big-endian native target"
#endif

typedef union { int16_t signed_value; uint8_t raw_bytes[2]; } NativeAdditive_Cycle;
extern NativeAdditive_Cycle native_state_Cycle;

typedef union { int16_t signed_value; uint8_t raw_bytes[2]; } NativeAdditive_ListIndexB;
extern NativeAdditive_ListIndexB native_state_ListIndexB;

typedef union { int16_t signed_value; uint8_t raw_bytes[2]; } NativeAdditive_ListIndexR;
extern NativeAdditive_ListIndexR native_state_ListIndexR;

typedef struct { uint8_t values[10]; } NativeAdditive_LionListM;
extern NativeAdditive_LionListM native_state_LionListM;

typedef struct { uint8_t values[10]; } NativeAdditive_LionListS;
extern NativeAdditive_LionListS native_state_LionListS;

typedef struct { uint8_t values[10]; } NativeAdditive_LionListT;
extern NativeAdditive_LionListT native_state_LionListT;

typedef struct { uint8_t values[10]; } NativeAdditive_LionListX;
extern NativeAdditive_LionListX native_state_LionListX;

typedef struct { uint8_t values[10]; } NativeAdditive_LionListY;
extern NativeAdditive_LionListY native_state_LionListY;

typedef union { int16_t signed_values[3]; uint8_t raw_bytes[6]; } NativeAdditive_SowX;
extern NativeAdditive_SowX native_state_SowX;

typedef union { int16_t signed_values[3]; uint8_t raw_bytes[6]; } NativeAdditive_SowY;
extern NativeAdditive_SowY native_state_SowY;

typedef union { int16_t signed_values[3]; uint8_t raw_bytes[6]; } NativeAdditive_SowDir;
extern NativeAdditive_SowDir native_state_SowDir;

typedef union { int16_t signed_values[3]; uint8_t raw_bytes[6]; } NativeAdditive_SowSave;
extern NativeAdditive_SowSave native_state_SowSave;

typedef union { int16_t signed_values[6]; uint8_t raw_bytes[12]; } NativeAdditive_PillarMap;
extern NativeAdditive_PillarMap native_state_PillarMap;

#endif
