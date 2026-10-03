#include <stdint.h>
#include <stdio.h>
#include "simulation_state_50f6.h"
#include "native_owners.h"
typedef struct { int16_t x, y; } Point;
int16_t fd_50F6_0FB6 = 20, fd_50F6_0FFA = 40;
static unsigned updates, resets;
void UpdateEdit(void) { ++updates; }
void f_0250_0ED2(void) { ++resets; }
void  f_004A_02AD(void)
{
    switch (native_state_MapPlane.signed_value) {
    case 1:
        (*((Point *)native_sim_state_fd_50F6_0596.raw_bytes)).x = fd_50F6_0FB6 / 2 + (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).x;
        (*((Point *)native_sim_state_fd_50F6_0596.raw_bytes)).y = fd_50F6_0FFA / 2 + (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).y;
        break;
    case 2:
        (*((Point *)native_sim_state_fd_50F6_06A6.raw_bytes)).x = fd_50F6_0FB6 / 2 + (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).x;
        (*((Point *)native_sim_state_fd_50F6_06A6.raw_bytes)).y = fd_50F6_0FFA / 2 + (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).y;
        break;
    case 3:
        (*((Point *)native_sim_state_fd_50F6_072E.raw_bytes)).x = fd_50F6_0FB6 / 2 + (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).x;
        (*((Point *)native_sim_state_fd_50F6_072E.raw_bytes)).y = fd_50F6_0FFA / 2 + (*((Point *)native_sim_state_fd_50F6_0508.raw_bytes)).y;
        break;
    }
    UpdateEdit();
    f_0250_0ED2();
}
int main(void) {
    native_sim_state_fd_50F6_0508.xy.x = 100;
    native_sim_state_fd_50F6_0508.xy.y = 200;
    for (int plane = 1; plane <= 3; ++plane) {
        native_state_MapPlane.signed_value = (int16_t)plane;
        f_004A_02AD();
    }
    NativeSimStatePointV6 *centers[3] = {
        &native_sim_state_fd_50F6_0596, &native_sim_state_fd_50F6_06A6,
        &native_sim_state_fd_50F6_072E};
    for (unsigned i = 0; i < 3; ++i)
        if (centers[i]->xy.x != 110 || centers[i]->xy.y != 220 ||
            centers[i]->raw_bytes[0] != 110 || centers[i]->raw_bytes[2] != 220)
            return 1;
    if (updates != 3 || resets != 3) return 2;
    puts("PASS: three source nest-plane center updates use shared point/raw views");
    return 0;
}
