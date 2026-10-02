#ifndef SIMANT_PORTABLE_UI_MODEL_BALLOONS_BALLOONS_H
#define SIMANT_PORTABLE_UI_MODEL_BALLOONS_BALLOONS_H

#include <stdint.h>

typedef enum PortableBalloonCueKind {
    PORTABLE_BALLOON_FIGHT = 0,
    PORTABLE_BALLOON_EGG = 1,
    PORTABLE_BALLOON_QUEEN = 2,
    PORTABLE_BALLOON_REST = 3,
    PORTABLE_BALLOON_CUE_COUNT = 4
} PortableBalloonCueKind;

typedef struct PortableBalloonPoint {
    int16_t x;
    int16_t y;
} PortableBalloonPoint;

typedef struct PortableBalloonViewport {
    int16_t plane;
    int16_t left;
    int16_t top;
    int16_t columns;
    int16_t rows;
} PortableBalloonViewport;

/* Source-owned state needed by BalloonIsVisible, the four cue submitters,
 * DoAntSim's cue reset, and DrawCurBalloons' pending-to-displayed transfer.
 * The four displayed point/plane pairs are absent from recovered next2, so an
 * engine binding must add these fields to its reviewed state profile before
 * using this DTO as authoritative runtime state. */
typedef struct PortableBalloonCueState {
    int16_t active;
    PortableBalloonPoint displayed;
    int16_t displayed_plane;
    PortableBalloonPoint pending;
    int16_t pending_plane;
} PortableBalloonCueState;

typedef struct PortableBalloonState {
    PortableBalloonCueState cue[PORTABLE_BALLOON_CUE_COUNT];
} PortableBalloonState;

typedef struct PortableBalloonFrameResult {
    uint8_t activated_count;
    PortableBalloonCueKind activation_order[PORTABLE_BALLOON_CUE_COUNT];
    uint8_t activated_mask;
} PortableBalloonFrameResult;

typedef enum PortableBalloonStatus {
    PORTABLE_BALLOON_OK = 0,
    PORTABLE_BALLOON_BAD_ARGUMENT
} PortableBalloonStatus;

/* C startup's zero initialization. The source simulation reset is a separate
 * operation because it deliberately preserves previously displayed points. */
void portable_balloons_init(PortableBalloonState *state);

/* BalloonIsVisible. The viewport end and y-3 calculations wrap as signed
 * 16-bit DOS int arithmetic before their comparisons. */
int portable_balloon_is_visible(const PortableBalloonViewport *viewport,
                                int16_t plane, int16_t x, int16_t y);

/* EggBalloons/FightBalloons/QueenBalloons/RestBalloons state mutations. */
PortableBalloonStatus portable_balloon_submit(
    PortableBalloonState *state, PortableBalloonCueKind kind,
    const PortableBalloonViewport *viewport,
    int16_t x, int16_t y, int16_t plane);

/* The DoAntSim mode-1 reset: clear active flags and set pending points to
 * (-1,-1); source leaves pending planes and displayed point/plane untouched. */
void portable_balloons_simulation_reset(PortableBalloonState *state,
                                        int16_t simulation_mode);

/* PreDrawBalloons/DrawCurBalloons pending-to-displayed transition. `enabled`
 * represents fd_3D57_07B2 and `sprite_state` represents fd_3D57_07BE. */
PortableBalloonStatus portable_balloons_prepare_frame(
    PortableBalloonState *state, int enabled, int16_t sprite_state,
    PortableBalloonFrameResult *result);

#endif
