/* Six source-bounded parallel balloon slots; native pointers keep process lifetime. */
#ifndef SIMANT_BALLOON_QUEUE_STATE_V1_H
#define SIMANT_BALLOON_QUEUE_STATE_V1_H
#include <stdint.h>
typedef struct NativeBalloonPointV1 { int16_t x; int16_t y; } NativeBalloonPointV1;
_Static_assert(sizeof(NativeBalloonPointV1) == 4, "source Pnt has two Win16 int fields");
#define Pnt NativeBalloonPointV1
extern char * native_balloon_message_slots_v1[6];
extern NativeBalloonPointV1 native_balloon_position_slots_v1[6];
extern int16_t native_balloon_style_slots_v1[6];
extern int16_t native_balloon_plane_slots_v1[6];
#endif
