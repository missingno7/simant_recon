#include "../../game/recovered/balloon_adapter.h"

typedef struct BalloonAdapterProbeInput {
    int16_t kind;
    int16_t x;
    int16_t y;
    int16_t plane;
    int16_t map_plane;
    int16_t view_left;
    int16_t view_top;
    int16_t columns;
    int16_t rows;
    int16_t active;
    int16_t displayed_x;
    int16_t displayed_y;
    int16_t displayed_plane;
    int16_t pending_x;
    int16_t pending_y;
    int16_t pending_plane;
} BalloonAdapterProbeInput;

typedef struct BalloonAdapterProbeOutput {
    int16_t active;
    int16_t displayed_x;
    int16_t displayed_y;
    int16_t displayed_plane;
    int16_t pending_x;
    int16_t pending_y;
    int16_t pending_plane;
} BalloonAdapterProbeOutput;

__declspec(dllexport) void portable_test_balloon_adapter_case(
    const BalloonAdapterProbeInput *input, BalloonAdapterProbeOutput *output)
{
    RecoveredState state;
    RecoveredBindingFrame frame;
    if (input == 0 || output == 0)
        return;
    recovered_state_init(&state);
    state.MapPlane = input->map_plane;
    state.fd_50F6_0508[0] = input->view_left;
    state.fd_50F6_0508[1] = input->view_top;
    state.fd_50F6_10E0 = input->columns;
    state.fd_50F6_10DE = input->rows;
    switch (input->kind) {
    case PORTABLE_BALLOON_FIGHT:
        state.fd_50F6_0F06 = input->active;
        state.fd_50F6_09F2.x = input->displayed_x;
        state.fd_50F6_09F2.y = input->displayed_y;
        state.fd_50F6_0B06 = input->displayed_plane;
        state.fd_50F6_08EC.v = input->pending_x;
        state.fd_50F6_08EC.h = input->pending_y;
        state.fd_50F6_0AEA = input->pending_plane;
        break;
    case PORTABLE_BALLOON_EGG:
        state.fd_50F6_0EF6 = input->active;
        state.fd_50F6_08DE.x = input->displayed_x;
        state.fd_50F6_08DE.y = input->displayed_y;
        state.fd_50F6_0AD8 = input->displayed_plane;
        state.fd_50F6_0852.v = input->pending_x;
        state.fd_50F6_0852.h = input->pending_y;
        state.fd_50F6_0ACA = input->pending_plane;
        break;
    case PORTABLE_BALLOON_QUEEN:
        state.fd_50F6_0F10 = input->active;
        state.fd_50F6_0A8A.x = input->displayed_x;
        state.fd_50F6_0A8A.y = input->displayed_y;
        state.fd_50F6_0C3A = input->displayed_plane;
        state.fd_50F6_0A02.v = input->pending_x;
        state.fd_50F6_0A02.h = input->pending_y;
        state.fd_50F6_0B08 = input->pending_plane;
        break;
    case PORTABLE_BALLOON_REST:
        state.fd_50F6_0F2E = input->active;
        state.fd_50F6_0AB2.x = input->displayed_x;
        state.fd_50F6_0AB2.y = input->displayed_y;
        state.fd_50F6_0D9A = input->displayed_plane;
        state.fd_50F6_0AA2.v = input->pending_x;
        state.fd_50F6_0AA2.h = input->pending_y;
        state.fd_50F6_0D68 = input->pending_plane;
        break;
    default:
        return;
    }
    recovered_bind_begin(&frame, &state);
    switch (input->kind) {
    case PORTABLE_BALLOON_FIGHT:
        sim_recovered_fight_balloons(input->x, input->y, input->plane);
        break;
    case PORTABLE_BALLOON_EGG:
        sim_recovered_egg_balloons(input->x, input->y, input->plane);
        break;
    case PORTABLE_BALLOON_QUEEN:
        sim_recovered_queen_balloons(input->x, input->y, input->plane);
        break;
    case PORTABLE_BALLOON_REST:
        sim_recovered_rest_balloons(input->x, input->y, input->plane);
        break;
    default:
        break;
    }
    recovered_bind_end(&frame, &state);
    switch (input->kind) {
    case PORTABLE_BALLOON_FIGHT:
        output->active = state.fd_50F6_0F06;
        output->displayed_x = state.fd_50F6_09F2.x;
        output->displayed_y = state.fd_50F6_09F2.y;
        output->displayed_plane = state.fd_50F6_0B06;
        output->pending_x = state.fd_50F6_08EC.v;
        output->pending_y = state.fd_50F6_08EC.h;
        output->pending_plane = state.fd_50F6_0AEA;
        break;
    case PORTABLE_BALLOON_EGG:
        output->active = state.fd_50F6_0EF6;
        output->displayed_x = state.fd_50F6_08DE.x;
        output->displayed_y = state.fd_50F6_08DE.y;
        output->displayed_plane = state.fd_50F6_0AD8;
        output->pending_x = state.fd_50F6_0852.v;
        output->pending_y = state.fd_50F6_0852.h;
        output->pending_plane = state.fd_50F6_0ACA;
        break;
    case PORTABLE_BALLOON_QUEEN:
        output->active = state.fd_50F6_0F10;
        output->displayed_x = state.fd_50F6_0A8A.x;
        output->displayed_y = state.fd_50F6_0A8A.y;
        output->displayed_plane = state.fd_50F6_0C3A;
        output->pending_x = state.fd_50F6_0A02.v;
        output->pending_y = state.fd_50F6_0A02.h;
        output->pending_plane = state.fd_50F6_0B08;
        break;
    case PORTABLE_BALLOON_REST:
        output->active = state.fd_50F6_0F2E;
        output->displayed_x = state.fd_50F6_0AB2.x;
        output->displayed_y = state.fd_50F6_0AB2.y;
        output->displayed_plane = state.fd_50F6_0D9A;
        output->pending_x = state.fd_50F6_0AA2.v;
        output->pending_y = state.fd_50F6_0AA2.h;
        output->pending_plane = state.fd_50F6_0D68;
        break;
    default:
        break;
    }
}
