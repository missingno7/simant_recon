#include "recovered_state.h"
#include <stdint.h>
#include <stddef.h>




struct TriLevel { uint16_t frac; uint16_t mid; uint16_t weight; };
typedef void * Handle;
extern void  win_GetObjRect(int16_t obj, struct Rect  *rect);
extern void f_208F_0419(struct Pt *size, int16_t id);
extern void hanim_RemoveAnimSet(Handle handle);






















extern void  InitTriVars(int16_t obj, struct TriPoints  *tri);
extern void  SetTriLatPoint(uint16_t  *level, struct TriPoints  *tri, struct Pt  *out);
extern void  cvtLevels2IdealCaste(int16_t  *ideal);
extern void  win_ModeControlChanged(void);
extern void  win_CasteControlChanged(void);
extern void  win_ModeControlClosed(void);
extern void  win_CasteControlClosed(void);

void  InitTriVars(int16_t obj, struct TriPoints  *tri)
{
    struct Rect rect;
    uint16_t half;

    win_GetObjRect(obj, &rect);
    triWidth = rect.right - rect.left;
    half = triWidth >> 1;
    triWidthR = half;
    triWidthL = half;
    triHeight = rect.bottom - rect.top;
    fd_50F6_382E = ((int32_t)half << 8) / (int32_t)triHeight;
    tri->apexX = half + rect.left;
    tri->apexY = rect.top;
    tri->leftY = tri->rightY = rect.bottom;
    tri->leftX = rect.left;
    tri->rightX = rect.right;
}


void  SetTriLatPoint(uint16_t  *level, struct TriPoints  *tri, struct Pt  *out)
{
    uint16_t w;
    int16_t row;

    out->y = (triHeight - 2) * (0xffffUL - level[0]) / 0xffffUL + tri->apexY;
    w = (uint32_t)triWidthL * level[0] / 0xffffUL;
    row = triWidth - w * 2;
    if (level[0] == 0xffff || row < 3)
        out->x = tri->apexX + 2;
    else
        out->x = (int32_t)(row - 3) * level[2] / (int32_t)(0xffffU - level[0]) + tri->leftX + w + 2;
}


void  cvtLevels2IdealCaste(int16_t  *ideal)
{
    ideal[0] = (100UL * casteLevels[1] + 0x3fff) / 0xffff;
    ideal[1] = (100UL * casteLevels[2] + 0x3fff) / 0xffff;
    ideal[2] = (50UL * casteLevels[0] + 0x3fff) / 0xffff;
    ideal[3] = (50UL * casteLevels[0] + 0x3fff) / 0xffff;
}


void  win_ModeControlClosed(void)
{
    if (fd_50F6_37F6) {
        hanim_RemoveAnimSet(fd_50F6_37F6);
        fd_50F6_37F6 = 0;
    }
}


void  win_CasteControlClosed(void)
{
    if (fd_50F6_37F2) {
        hanim_RemoveAnimSet(fd_50F6_37F2);
        fd_50F6_37F2 = 0;
    }
}


void  win_ModeControlChanged(void)
{
    InitTriVars(0x120d, &fd_50F6_3816);
    SetTriLatPoint(modeLevels, &fd_50F6_3816, &fd_50F6_0358);
    win_ModeControlClosed();
}


void  win_CasteControlChanged(void)
{
    InitTriVars(0x130d, &fd_50F6_3822);
    SetTriLatPoint(casteLevels, &fd_50F6_3822, &fd_50F6_022E);
    win_CasteControlClosed();
}


void  initControls(void)
{
    struct Rect rect;
    int16_t i;

    f_208F_0419(&knobSize, 0x578);
    win_GetObjRect(0x120d, &rect);
    ModeAuto = 1;
    CasteAuto = 1;
    fd_50F6_0468 = 1;
    fd_3D57_07EA = 1;
    fd_50F6_0370 = -1;
    fd_50F6_024E = -1;
    for (i = 0; i < 3; i++) {
        modeLevels[i] = fd_3D57_080A[i];
        fd_3D57_0810[i] = fd_3D57_080A[i];
        casteLevels[i] = fd_3D57_07EC[i];
        fd_3D57_07F2[i] = fd_3D57_07EC[i];
    }
    win_ModeControlChanged();
    win_CasteControlChanged();
    cvtLevels2IdealCaste(IdealCaste);
}

/* Explicit state-bound native entry points; original bodies remain unchanged. */
