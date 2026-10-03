/* Native static storage; capacity is source-guarded, not gap-derived. */
#include "balloon_queue_state_v1.h"
char * native_balloon_message_slots_v1[6];
NativeBalloonPointV1 native_balloon_position_slots_v1[6];
int16_t native_balloon_style_slots_v1[6];
int16_t native_balloon_plane_slots_v1[6];
