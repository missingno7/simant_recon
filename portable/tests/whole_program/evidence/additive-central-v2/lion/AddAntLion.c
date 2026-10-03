#include <stdint.h>
#include "source_bounded_additive.h"
extern int16_t LionIndex; extern int8_t Dx8[8],Dy8[8];
extern int16_t IsClearTile(int16_t,int16_t,int16_t);
extern void SetMap(int16_t,int16_t,int16_t,int16_t);
static uint8_t lionRing[8] = {1, 2, 4, 7, 6, 5, 3, 0};
void  AddAntLion(int16_t x, int16_t y)
{
    int16_t i;
    int16_t lx;
    int16_t ly;

    SetMap(1, x, y, 0x38);
    for (i = 0; i < 8; i++) {
        lx = x + Dx8[i];
        if (IsClearTile(1, lx, ly = y + Dy8[i]) == 1)
            SetMap(1, lx, ly, lionRing[i] + 0x30);
    }
    native_state_LionListX.values[LionIndex] = x;
    native_state_LionListY.values[LionIndex] = y;
    native_state_LionListM.values[LionIndex] = 0;
    native_state_LionListS.values[LionIndex] = 0;
    native_state_LionListT.values[LionIndex] = 0;
    if (LionIndex < 9)
        LionIndex++;
}
