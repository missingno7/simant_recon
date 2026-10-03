#include "dos_types.h"
#include "portable/whole_program/platform/dos_memory.h"
#include "portable/whole_program/platform/dos_io.h"
uint8_t dos_keyboard_modifiers(void);
#include "portable/whole_program/platform/graphics_source_fields.h"
#include "source_bounded_additive.h"
#include "native_owners.h"
#pragma pack(push, 2)
/* root:10F7 draft: recovered prefix */
extern int8_t  Dx8[];
extern int8_t  Dy8[];
extern uint8_t  LifeA[128][64];
extern uint8_t  LifeB[64][64];
extern uint8_t  LifeR[64][64];
extern uint8_t  MapA[128][64];
extern uint8_t  MapB[64][64];
extern uint8_t  MapR[64][64];
extern int16_t  MeLocX;
extern int16_t  MeLocY;
extern int16_t  fd_50F6_0496;
extern int16_t  fd_50F6_04C2;
extern int16_t  MePlane;
extern int16_t  fd_50F6_048E;
extern int16_t  fd_3D57_0C22;
extern int8_t  fd_3D57_0094[];
extern int16_t  fd_50F6_0A06;
extern int16_t  fd_3D57_0798;
extern int8_t  fd_3D57_006C[];
extern uint8_t  HoleMapB[];
extern uint8_t  HoleMapR[];
extern int16_t  TERRAINset;
extern int16_t  fd_3D57_0C16;
extern int32_t  fd_50F6_0472;
extern void  *  *  fd_50F6_034C;
extern int16_t  fd_3D57_0C26;
extern int16_t  fd_3D57_02AC[];
extern int16_t  fd_3D57_0C24;
extern int16_t  ListIndexA;
extern uint8_t  AlistX[];
extern uint8_t  AlistY[];
extern uint8_t  AlistT[];
extern uint8_t  AlistM[];
extern uint8_t  AlistS[];
extern uint8_t  BlistX[];
extern uint8_t  BlistY[];
extern uint8_t  BlistT[];
extern uint8_t  BlistM[];
extern uint8_t  BlistS[];
extern uint8_t  RlistX[];
extern uint8_t  RlistY[];
extern uint8_t  RlistT[];
extern uint8_t  RlistM[];
extern uint8_t  RlistS[];

int16_t  IsValidA(int16_t, int16_t);
int16_t  IsClearTile(int16_t, int16_t, int16_t);
int16_t  GetLife(int16_t, int16_t, int16_t);
int16_t  GetMap(int16_t, int16_t, int16_t);
void  SetLife(int16_t, int16_t, int16_t, int16_t);
int16_t  IsItDigable(int16_t, int16_t, int16_t);
void  AddAntToAList(int16_t, int16_t, int16_t, int16_t, int16_t);
void  AddAntToBList(int16_t, int16_t, int16_t, int16_t, int16_t);
void  AddAntToRList(int16_t, int16_t, int16_t, int16_t, int16_t);
void  DigMyTile(int16_t, int16_t, int16_t);
void  myBeginSound(int16_t, int16_t, int16_t);
void  ZapEuMapAt(int16_t, int16_t, int16_t);
int16_t  IsItFood(int16_t);
void  DoEditUpdateDraw(void);
void  ResetYellowVars(int16_t, int16_t, int16_t);
int16_t  IsItYellow(int16_t, int16_t, int16_t);
void  SetMyHealth(int16_t);
int16_t  DigMyNewHole(int16_t, int16_t);
void  o25_3BA4_1035(void);
void  GotoMyAnt(void);
int16_t  IsItHole(int16_t, int16_t);
void  PickupFoodA(int16_t, int16_t);
uint32_t  GetDis(int16_t, int16_t, int16_t, int16_t);
int16_t  IsItDirt(int16_t);
int16_t  IsSamePlane(int16_t);
int16_t  IsValidB(int16_t, int16_t);
void  JamScentBT(int16_t, int16_t, int16_t);
void  SetDefaultWindPrompt(int16_t);
void  YellowDialog(int16_t, int16_t);
void  EditMessage(void  *, int32_t, int16_t);
int16_t  SRand1(int16_t);
int16_t  SRand8(void);
int16_t  SRand16(void);
int16_t  IsItAHole(int16_t, int16_t, int16_t);
int16_t  GetDir(int16_t, int16_t, int16_t, int16_t);
void  DropFoodA(int16_t, int16_t);
void  PauseGame(int16_t);
void  EndTargetMode(void);
void  EndLifeTransferMode(void);
int16_t  DoLifeExchange(int16_t, int16_t, int16_t);
int16_t  mySoundIsDone(void);
void  myDelay(int32_t);
void  myBeginSong(uint16_t, uint16_t);
int16_t  IsItNFood(int16_t);
int16_t  IsValidB(int16_t, int16_t);

int16_t  IsValidLocation(int16_t map, int16_t index, int16_t out)
{
    if (map <= 1)
        return IsValidA(index, out);
    else
        return IsValidB(index, out);
}

int16_t  IsYellowAnt(int16_t value)
{
    if (value != 0xff && value != 0xfe) return 0;
    return 1;
}

int16_t  GetAntIndex(int16_t list, int16_t index, int16_t  *life, int16_t  *column,
                    int16_t  *attribute, int16_t  *state, int16_t  *direction)
{
    if (list <= 1) {
        if (index < 0 || index >= ListIndexA)
            return 0;
        *life = AlistX[index];
        *column = AlistY[index];
        *attribute = AlistT[index];
        *state = AlistM[index];
        *direction = AlistS[index];
    } else if (list == 2) {
        if (index < 0 || index >= native_state_ListIndexB.signed_value)
            return 0;
        *life = BlistX[index];
        *column = BlistY[index];
        *attribute = BlistT[index];
        *state = BlistM[index];
        *direction = BlistS[index];
    } else {
        if (index < 0 || index >= native_state_ListIndexR.signed_value)
            return 0;
        *life = RlistX[index];
        *column = RlistY[index];
        *attribute = RlistT[index];
        *state = RlistM[index];
        *direction = RlistS[index];
    }
    return 1;
}

void  SetAntIndex(int16_t list, int16_t index, int16_t life, int16_t column,
                      int16_t attribute, int16_t state, int16_t direction)
{
    if (list <= 1) {
        if (index < 0 || index >= ListIndexA)
            return;
        AlistX[index] = (uint8_t)life;
        AlistY[index] = (uint8_t)column;
        AlistT[index] = (uint8_t)attribute;
        AlistM[index] = (uint8_t)state;
        AlistS[index] = (uint8_t)direction;
    } else if (list == 2) {
        if (index < 0 || index >= native_state_ListIndexB.signed_value)
            return;
        BlistX[index] = (uint8_t)life;
        BlistY[index] = (uint8_t)column;
        BlistT[index] = (uint8_t)attribute;
        BlistM[index] = (uint8_t)state;
        BlistS[index] = (uint8_t)direction;
    } else {
        if (index < 0 || index >= native_state_ListIndexR.signed_value)
            return;
        RlistX[index] = (uint8_t)life;
        RlistY[index] = (uint8_t)column;
        RlistT[index] = (uint8_t)attribute;
        RlistM[index] = (uint8_t)state;
        RlistS[index] = (uint8_t)direction;
    }
}

int16_t  FindLifeIndex(int16_t list, int16_t matchLife, int16_t matchColumn, int16_t low, int16_t high, int16_t mask)
{
    uint8_t  *lifeArr;
    uint8_t  *columnArr;
    uint8_t  *attrArr;
    int16_t count;
    int16_t i;
    int16_t masked;

    if (list <= 1) {
        count = ListIndexA;
        lifeArr = AlistX;
        columnArr = AlistY;
        attrArr = AlistT;
    } else if (list == 2) {
        count = native_state_ListIndexB.signed_value;
        lifeArr = BlistX;
        columnArr = BlistY;
        attrArr = BlistT;
    } else {
        count = native_state_ListIndexR.signed_value;
        lifeArr = RlistX;
        columnArr = RlistY;
        attrArr = RlistT;
    }
    for (i = count - 1; i >= 0; i--) {
        masked = attrArr[i] & mask;
        if (lifeArr[i] == matchLife && columnArr[i] == matchColumn &&
            masked >= low && masked <= high)
            break;
    }
    return i;
}

int16_t  FindAntIndex(int16_t list, int16_t matchLife, int16_t matchColumn, int16_t attribute)
{
    uint8_t  *lifeArr;
    uint8_t  *columnArr;
    uint8_t  *attrArr;
    int16_t count;
    int16_t i;

    if (list <= 1) {
        count = ListIndexA;
        lifeArr = AlistX;
        columnArr = AlistY;
        attrArr = AlistT;
    } else if (list == 2) {
        count = native_state_ListIndexB.signed_value;
        lifeArr = BlistX;
        columnArr = BlistY;
        attrArr = BlistT;
    } else {
        count = native_state_ListIndexR.signed_value;
        lifeArr = RlistX;
        columnArr = RlistY;
        attrArr = RlistT;
    }
    for (i = count - 1; i >= 0; i--) {
        if (lifeArr[i] == matchLife && columnArr[i] == matchColumn &&
            attrArr[i] == attribute)
            break;
    }
    return i;
}

int16_t  IsClear3x3(int16_t type, int16_t y, int16_t x)
{
     int16_t index;

    if (IsClearTile(type, y, x) == 1) {
        for (index = 0; index < 8; ++index) {
            if (!IsClearTile(type, y + Dx8[index], x + Dy8[index]))
                return 0;
        }
        return 1;
    }
    return 0;
}

int16_t  IsClearTile(int16_t plane, int16_t x, int16_t y)
{
    int16_t result;
    int16_t tile;
    int16_t life;

    result = 0;
    tile = GetMap(plane, x, y);
    if (tile >= 0) {
        life = GetLife(plane, x, y);
        if (life < 0 || IsYellowAnt(life) == 1) {
            if (plane <= 1) {
                if (tile < 16)
                    result = 1;
            } else {
                if (tile < 8)
                    result = 1;
            }
        }
    }
    return result;
}

int16_t  AddAntToList(int16_t plane, int16_t x, int16_t y, int16_t type, int16_t a, int16_t b)
{
    int16_t added;

    added = 0;
    if (plane <= 1) {
        if (ListIndexA < 1000) {
            AddAntToAList(x, y, type, a, b);
            added = 1;
        }
    } else if (plane == 2) {
        if (native_state_ListIndexB.signed_value < 500) {
            AddAntToBList(x, y, type, a, b);
            added = 1;
        }
    } else if (native_state_ListIndexR.signed_value < 500) {
        AddAntToRList(x, y, type, a, b);
        added = 1;
    }
    if (added == 1)
        SetLife(plane, x, y, type);
    return added;
}

void  SetLife(int16_t plane, int16_t x, int16_t y, int16_t value)
{
    if (IsValidLocation(plane, x, y) == 1) {
        switch (plane) {
        case 0:
        case 1:
            LifeA[x][y] = value;
            break;
        case 2:
            LifeB[x][y] = value;
            if (value > 0 && IsItDigable(plane, x, y) == 1) {
                DigMyTile(plane, x, y);
                myBeginSound(0x13, 0, 0x3f);
            }
            break;
        case 3:
            LifeR[x][y] = value;
            if (value > 0 && IsItDigable(plane, x, y) == 1) {
                DigMyTile(plane, x, y);
                myBeginSound(0x13, 0, 0x3f);
            }
            break;
        }
        ZapEuMapAt(plane, x, y);
    }
}

int16_t  IsThisEgg(value)
uint8_t value;
{
    int16_t normalized;
    normalized = value;
    normalized &= 0x7f;
    if (normalized >= 1 && normalized <= 7) return 1;
    return 0;
}

int16_t  IsThisGrass(int16_t category, int16_t tile)
{
    if (category < 2)
        return 0;
    if (tile < 0x1c || tile > 0x1f)
        return 0;
    return 1;
}

int16_t  IsThisFood(int16_t category, int16_t tile)
{
    if (category <= 1)
        return IsItFood(tile);
    return IsItNFood(tile);
}

int16_t  IsThisPebble(int16_t plane, int16_t tile)
{
    if (plane <= 1) {
        if (plane == 1 && tile >= 0x51 && tile <= 0x53)
            return 1;
        return 0;
    }
    if (tile >= 0x30 && tile <= 0x31)
        return 1;
    return 0;
}

int16_t  IsItNFood(int16_t value)
{
    if (value < 0x10 || value > 0x13) return 0;
    return 1;
}

int16_t  IsItFoodAt(int16_t plane, int16_t x, int16_t y)
{
     int16_t tile;

    tile = GetMap(plane, x, y);
    if (tile < 0)
        return 0;
    if (plane <= 1)
        return IsItFood(tile);
    return IsItNFood(tile);
}

int16_t  GetLife(int16_t plane, int16_t x, int16_t y)
{
    int16_t result;

    result = -1;
    if (IsValidLocation(plane, x, y) == 1) {
        switch (plane) {
        case 0:
        case 1:
            result = LifeA[x][y];
            break;
        case 2:
            result = LifeB[x][y];
            break;
        case 3:
            result = LifeR[x][y];
            break;
        }
        if (result == 0)
            result = -1;
    }
    return result;
}

int16_t  GetMap(int16_t plane, int16_t x, int16_t y)
{
    int16_t result;

    result = -1;
    if (IsValidLocation(plane, x, y) == 1) {
        switch (plane) {
        case 0:
        case 1:
            result = MapA[x][y];
            break;
        case 2:
            result = MapB[x][y];
            break;
        case 3:
            result = MapR[x][y];
            break;
        }
    }
    return result;
}

void  SetMap(int16_t plane, int16_t x, int16_t y, int16_t value)
{
    if (IsValidLocation(plane, x, y) == 1) {
        switch (plane) {
        case 0:
        case 1:
            MapA[x][y] = value;
            break;
        case 2:
            MapB[x][y] = value;
            break;
        case 3:
            MapR[x][y] = value;
            break;
        }
        ZapEuMapAt(plane, x, y);
    }
}

void  ClearLife(int16_t plane, int16_t x, int16_t y, int16_t value)
{
    if (IsValidLocation(plane, x, y) == 1) {
        if (GetLife(plane, x, y) == value)
            SetLife(plane, x, y, 0);
        ZapEuMapAt(plane, x, y);
    }
}

void  ClearMyLife(int16_t plane, int16_t x, int16_t y, int16_t type, int16_t dir)
{
    ClearLife(plane, x, y, 0xff);
    if (type == 0x60)
        ClearLife(plane, x + Dx8[dir ^ 4], y + Dy8[dir ^ 4], 0xfe);
}

void  SetQueenTail(int16_t plane, int16_t x, int16_t y, int16_t dir, int16_t value)
{
    SetLife(plane, x + Dx8[dir ^ 4], y + Dy8[dir ^ 4],
                (value == 0xff) ? 0xfe : value);
}

void  SetMyLife(int16_t plane, int16_t x, int16_t y, int16_t type, int16_t dir, int16_t life)
{
    if (IsValidLocation(plane, x, y) == 1) {
        SetLife(plane, x, y, life);
        if (type == 0x60)
            SetQueenTail(plane, x, y, dir, life);
        if (life != 0) {
            MeLocX = x;
            MeLocY = y;
            fd_50F6_0496 = dir;
            fd_50F6_04C2 = type;
            MePlane = plane;
        }
    }
}

void  MoveMyLife(int16_t plane, int16_t x, int16_t y, int16_t type, int16_t dir)
{
    ClearMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496);
    SetMyLife(plane == 0 ? 1 : plane, x, y, type, dir, 0xff);
}

void  DoMapUpdateDraw(void)
{
}

void  DoEditAndMapUpdateDraw(void)
{
    DoMapUpdateDraw();
    DoEditUpdateDraw();
}

void  TargetAnt(void)
{
    if (native_state_fd_50F6_105E.signed_value == 0xb) {
        EndTargetMode();
        return;
    }
    fd_50F6_048E = native_state_fd_50F6_047E.signed_value;
    native_state_fd_50F6_105E.signed_value = 0xb;
    PauseGame(1);
}

void  EndTargetMode(void)
{
    native_state_fd_50F6_105E.signed_value = -1;
    PauseGame(fd_50F6_048E);
}

void  StartLifeTransfer(void)
{
    if (native_state_fd_50F6_105E.signed_value == 0xa) {
        EndLifeTransferMode();
        return;
    }
    fd_50F6_048E = native_state_fd_50F6_047E.signed_value;
    native_state_fd_50F6_105E.signed_value = 0xa;
    PauseGame(1);
}

void  EndLifeTransferMode(void)
{
    native_state_fd_50F6_105E.signed_value = -1;
    PauseGame(fd_50F6_048E);
}

void  ExchangeLives(int16_t a, int16_t b, int16_t c)
{
    native_state_fd_50F6_1074.signed_value = 1;
    if (DoLifeExchange(a, b, c) == 1) {
        EndLifeTransferMode();
        if (fd_50F6_04C2 == 0x60) {
            myBeginSound(0xf, 0, 0x7e);
            DoEditUpdateDraw();
            while (!mySoundIsDone())
                myDelay(5L);
            myBeginSong(0x2afe, 0x7e);
        } else
            myBeginSound(0xf, 0, 0x7e);
    } else
        myBeginSound(1, 0, 0x7e);
}

int16_t  DoLifeExchange(int16_t plane, int16_t x, int16_t y)
{
    int16_t newLife;
    int16_t t;
    int16_t index;
    int16_t caste;
    int16_t x2;
    int16_t y2;
    int16_t index2;
    int16_t egg;
    int16_t life;
    int16_t direction;
    int16_t state;
    int16_t attribute;
    int16_t column;
    int16_t lifeField;
    int16_t u;

    life = GetLife(plane, x, y);
    if (life <= 0) {
        if (plane != 1)
            goto fail;
        if (GetDis(x * 16 + 8, y * 16 + 8, native_state_fd_50F6_0F12.signed_value, native_state_fd_50F6_0F34.signed_value) >= 0x200)
            goto fail;
        newLife = (fd_50F6_04C2 & 0x78) >> 3;
        egg = 0;
        if (fd_50F6_04C2 & 8) {
            if (newLife == 5 || newLife == 9)
                newLife = fd_3D57_0094[newLife];
            else if (newLife == 1)
                egg = fd_3D57_0C22;
        }
        life = (native_state_fd_50F6_04E2.signed_value & 0x80) | fd_50F6_0496 | (newLife << 3);
        if (fd_50F6_04C2 == 0x60)
            t = 9;
        else
            t = 0;
        if (!AddAntToList(MePlane, MeLocX, MeLocY, life, t, egg))
            goto fail;
        if (fd_50F6_04C2 == 0x60) {
            if (!AddAntToList(MePlane, MeLocX + Dx8[fd_50F6_0496 ^ 4],
                             MeLocY + Dy8[fd_50F6_0496 ^ 4], life + 8, t, 0))
                goto fail;
        }
        SetMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496, 0);
        native_state_Starg.signed_value = -2;
        native_state_SuserX.signed_value = native_state_fd_50F6_0F12.signed_value >> 4;
        native_state_SuserY.signed_value = native_state_fd_50F6_0F34.signed_value >> 4;
        fd_50F6_0A06 = 1;
        native_state_SMode.signed_value = 0;
        native_state_fd_50F6_06AC.signed_value = 0;
        native_state_fd_50F6_04E2.signed_value = 0;
        ResetYellowVars(plane, native_state_SuserX.signed_value, native_state_SuserY.signed_value);
        SetMyHealth(100);
        goto done;
    }
    if (IsItYellow(plane, x, y) || IsYellowAnt(life))
        goto done;
    caste = (life & 0x78) >> 3;
    if (caste == 0xc) {
        x2 = x + Dx8[(life ^ 4) & 7];
        y2 = y + Dy8[(life ^ 4) & 7];
        newLife = GetLife(plane, x2, y2);
    } else if (caste == 0xd) {
        x2 = x;
        y2 = y;
        newLife = life;
        x += Dx8[life & 7];
        y += Dy8[life & 7];
        life = GetLife(plane, x, y);
        caste = 0xc;
    }
    index = FindAntIndex(plane, x, y, life);
    if (caste == 0xc)
        index2 = FindAntIndex(plane, x2, y2, newLife);
    if (index < 0)
        goto fail;
    if (fd_50F6_0A06 == 0) {
        int16_t c;

        u = (fd_50F6_04C2 & 0x78) >> 3;
        egg = 0;
        if (fd_50F6_04C2 & 8) {
            if (u == 5 || u == 9)
                u = fd_3D57_0094[u];
            else if (u == 1)
                egg = fd_3D57_0C22;
        }
        newLife = (u << 3) | fd_50F6_0496 | (life & 0x80);
        if (life & 0x80) {
            if (!(dos_keyboard_modifiers() & 8) || !(dos_keyboard_modifiers() & 3))
                goto fail;
        }
        c = (life & 0x78) >> 3;
        if (c <= 0 || c > 0xd || c == 0xa || c == 0xb) {
            if (!(dos_keyboard_modifiers() & 8) || !(dos_keyboard_modifiers() & 3) || !fd_3D57_0798)
                goto fail;
        }
        if (c == 5 || c == 9)
            life = (fd_3D57_0094[(life & 0x78) >> 3] << 3) | (life & 7);
        else if (c == 1) {
            GetAntIndex(plane, index, &lifeField, &column, &attribute, &state, &direction);
            fd_3D57_0C22 = direction;
        }
        t = (fd_50F6_04C2 == 0x60) ? 9 : 0;
        ZapEuMapAt(MePlane, MeLocX, MeLocY);
        if (t)
            ZapEuMapAt(MePlane, MeLocX + Dx8[fd_50F6_0496 ^ 4],
                        MeLocY + Dy8[fd_50F6_0496 ^ 4]);
        ZapEuMapAt(plane, x, y);
        if (caste == 0xc)
            ZapEuMapAt(plane, x2, y2);
        SetAntIndex(plane, index, 0, 0, 0, 0, 0);
        if (caste == 0xc)
            SetAntIndex(plane, index2, 0, 0, 0, 0, 0);
        if (!AddAntToList(MePlane, MeLocX, MeLocY, newLife, t, egg))
            goto fail;
        if (fd_50F6_04C2 == 0x60) {
            if (!AddAntToList(MePlane, MeLocX + Dx8[fd_50F6_0496 ^ 4],
                             MeLocY + Dy8[fd_50F6_0496 ^ 4], newLife + 8, t, 0))
                goto fail;
        }
    } else {
        int16_t c;

        if (life & 0x80) {
            if (!(dos_keyboard_modifiers() & 8) || !(dos_keyboard_modifiers() & 3))
                goto fail;
        }
        c = (life & 0x78) >> 3;
        if (c <= 0 || c > 0xd || c == 0xa || c == 0xb) {
            if (!(dos_keyboard_modifiers() & 8) || !(dos_keyboard_modifiers() & 3) || !fd_3D57_0798)
                goto fail;
        }
        if (c == 5 || c == 9)
            life = (fd_3D57_0094[(life & 0x78) >> 3] << 3) | (life & 7);
        else if (c == 1) {
            GetAntIndex(plane, index, &lifeField, &column, &attribute, &state, &direction);
            fd_3D57_0C22 = direction;
        }
        SetAntIndex(plane, index, 0, 0, 0, 0, 0);
        if (caste == 0xc)
            SetAntIndex(plane, index2, 0, 0, 0, 0, 0);
    }
    native_state_fd_50F6_04E2.signed_value = life & 0x80;
    native_state_fd_50F6_049A.signed_value = 0;
    fd_50F6_0A06 = 0;
    native_state_fd_50F6_06AC.signed_value = 0;
    SetMyHealth(100);
    SetMyLife(plane, x, y, life & 0x78, life & 7, 0xff);
    if (fd_50F6_04C2 < 8)
        native_state_fd_50F6_0502.signed_value = fd_50F6_0496;
done:
    return 1;
fail:
    return 0;
}

int16_t  DropMyFood(int16_t plane, int16_t x, int16_t y, int16_t tx, int16_t ty)
{
    int16_t i;
    int16_t dir;
    int16_t done;
    int16_t tile;
    int16_t nx;
    int16_t ny;
    int16_t d;

    if (fd_50F6_04C2 != 0x18 && fd_50F6_04C2 != 0x38)
        return 0;
    done = 0;
    dir = GetDir(x, y, tx, ty);
    if (dir > 0)
        dir--;
    else
        dir = fd_50F6_0496;
    for (i = 0; !done; i++) {
        if (i >= 8)
            break;
        d = (fd_3D57_006C[i] + dir) & 7;
        nx = x + Dx8[d];
        ny = y + Dy8[d];
        if (IsValidLocation(plane, nx, ny)) {
            if (GetLife(plane, nx, ny) < 0) {
                tile = GetMap(plane, nx, ny);
                if (IsThisFood(plane, tile) && (tile & 3) < 3) {
                    tile++;
                    done = 1;
                } else if (IsClearTile(plane, nx, ny) || tile == 0x38) {
                    tile = 0x10;
                    done = 1;
                }
            }
        }
    }
    if (!done) {
        d = dir;
        nx = x;
        ny = y;
        if (IsValidLocation(plane, nx, ny)) {
            tile = GetMap(plane, nx, ny);
            if (IsThisFood(plane, tile) && (tile & 3) < 3) {
                tile++;
                done = 1;
            } else if (IsClearTile(plane, nx, ny) || tile == 0x38) {
                tile = 0x10;
                done = 1;
            }
        }
    }
    if (done) {
        fd_50F6_0496 = d;
        if (plane <= 1)
            DropFoodA(nx, ny);
        else {
            SetMap(plane, nx, ny, tile);
            if (plane == 2)
                native_state_FoodB.signed_value++;
            else
                native_state_FoodR.signed_value++;
        }
        if (!((dos_keyboard_modifiers() & 3) && (dos_keyboard_modifiers() & 8)))
            fd_50F6_04C2 &= 0xf7;
        myBeginSound(0x1d, 0, 0x7e);
    }
    return done;
}

void  DropPebble(int16_t plane, int16_t x, int16_t y)
{
    int16_t tile;

    if (plane <= 1) {
        if (IsItAHole(plane, x, y)) {
            if (x < 0x40 && HoleMapB[y] == x)
                MapB[y][0] = 0x31;
            else if (HoleMapR[y] == x)
                MapR[y][0] = 0x31;
        }
        tile = 0x51;
    } else if (IsItAHole(plane, x, y)) {
        MapA[plane == 2 ? HoleMapB[x] : HoleMapR[x]][x] = 0x51;
        tile = 0x31;
    } else
        tile = 0x30;
    SetMap(plane, x, y, tile);
}

int16_t  DropMyRock(int16_t plane, int16_t x, int16_t y, int16_t tx, int16_t ty)
{
    int16_t tile;
    int16_t i;
    int16_t dir;
    int16_t done;
    int16_t ny;
    int16_t nx;
    int16_t d;

    if (fd_50F6_04C2 != 0x28 && fd_50F6_04C2 != 0x48)
        return 0;
    done = 0;
    dir = GetDir(x, y, tx, ty);
    if (dir > 0)
        dir--;
    else
        dir = fd_50F6_0496;
    for (i = 0; !done; i++) {
        if (i >= 8)
            break;
        d = (fd_3D57_006C[i] + dir) & 7;
        nx = x + Dx8[d];
        ny = y + Dy8[d];
        if (IsValidLocation(plane, nx, ny)) {
            if (GetLife(plane, nx, ny) < 0) {
                if (IsClearTile(plane, nx, ny))
                    done = 1;
                else {
                    tile = GetMap(plane, nx, ny);
                    if (!IsThisFood(plane, tile) && !IsThisPebble(plane, tile) &&
                        (IsItAHole(plane, nx, ny) || tile == 0x38))
                        done = 1;
                }
            }
        }
    }
    if (!done) {
        d = dir;
        nx = x;
        ny = y;
        if (IsValidLocation(plane, nx, ny)) {
            if (IsClearTile(plane, nx, ny))
                done = 1;
            else {
                tile = GetMap(plane, nx, ny);
                if (!IsThisFood(plane, tile) && !IsThisPebble(plane, tile) &&
                    (IsItAHole(plane, nx, ny) || tile == 0x38))
                    done = 1;
            }
        }
    }
    if (done) {
        fd_50F6_0496 = d;
        DropPebble(plane, nx, ny);
        if (!((dos_keyboard_modifiers() & 3) && (dos_keyboard_modifiers() & 8))) {
            if (fd_50F6_04C2 == 0x28 || fd_50F6_04C2 == 0x48)
                fd_50F6_04C2 -= 0x18;
        }
        myBeginSound(0x1e, 0, 0x7e);
    }
    return done;
}

int16_t  DropMyEgg(int16_t plane, int16_t x, int16_t y, int16_t tx, int16_t ty)
{
    int16_t i;
    int16_t done;
    int16_t dir;
    int16_t ny;
    int16_t nx;
    int16_t d;

    if (fd_50F6_04C2 != 8)
        return 0;
    done = 0;
    dir = GetDir(x, y, tx, ty);
    if (dir > 0)
        dir--;
    else
        dir = fd_50F6_0496;
    for (i = 0; !done; i++) {
        if (i >= 8)
            break;
        d = (fd_3D57_006C[i] + dir) & 7;
        nx = x + Dx8[d];
        ny = y + Dy8[d];
        if (IsValidLocation(plane, nx, ny)) {
            if (GetLife(plane, nx, ny) < 0) {
                if (IsClearTile(plane, nx, ny) || GetMap(plane, nx, ny) == 0x38)
                    done = 1;
            }
        }
    }
    if (!done) {
        d = dir;
        nx = x;
        ny = y;
        if (IsValidLocation(plane, nx, ny)) {
            if (IsClearTile(plane, nx, ny) || GetMap(plane, nx, ny) == 0x38)
                done = 1;
        }
    }
    if (done)
        done = AddAntToList(plane, nx, ny, fd_3D57_0C22, 8, 0);
    if (done) {
        fd_50F6_0496 = d;
        if (!((dos_keyboard_modifiers() & 3) && (dos_keyboard_modifiers() & 8))) {
            fd_50F6_04C2 = 0x10;
            fd_3D57_0C22 = 0xfd;
        }
        SetMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, fd_50F6_0496, 0xff);
        myBeginSound(0x1c, 0, 0x7e);
    }
    return done;
}

int16_t  PickupMyRock(int16_t plane, int16_t x, int16_t y)
{
    int16_t tile;
    int16_t done;

    if (fd_50F6_04C2 != 0x10 && fd_50F6_04C2 != 0x30)
        return 0;
    done = 0;
    tile = GetMap(plane, x, y);
    if (plane <= 1) {
        if (IsThisPebble(plane, tile)) {
            if (x < 0x40) {
                if (HoleMapB[y] == x) {
                    MapB[y][0] = 0x18;
                    done = 1;
                }
            } else if (HoleMapR[y] == x) {
                MapR[y][0] = 0x18;
                done = 1;
            }
            if (done) {
                if (TERRAINset == 0)
                    MapA[x][y] = 0x50;
                else
                    MapA[x][y] = SRand1(7) + 0x59;
            } else {
                if (TERRAINset == 0)
                    MapA[x][y] = SRand16();
                else
                    MapA[x][y] = 0;
                done = 1;
            }
        }
    } else if (tile == 0x30) {
        SetMap(plane, x, y, SRand8());
        done = 1;
    } else if (tile == 0x31) {
        if (plane == 2) {
            MapB[x][y] = 0x18;
            MapA[HoleMapB[x]][x] = 0x50;
        } else {
            MapR[x][y] = 0x18;
            MapA[HoleMapR[x]][x] = 0x50;
        }
        done = 1;
    }
    if (done) {
        if (fd_50F6_04C2 == 0x10)
            fd_50F6_04C2 = 0x28;
        else
            fd_50F6_04C2 = 0x48;
        myBeginSound(0x1e, 0, 0x7e);
    }
    return done;
}

int16_t  FindEggAt(int16_t  *index, int16_t plane, int16_t x, int16_t y)
{
    int16_t i;
    int16_t life;
    int16_t direction;
    int16_t state;
    int16_t column;
    int16_t lifeField;

    life = GetLife(plane, x, y);
    if (IsThisEgg(life) && !IsYellowAnt(life)) {
        *index = FindAntIndex(plane, x, y, life);
        return life;
    }
    i = FindLifeIndex(plane, x, y, 1, 7, 0x7f);
    if (i >= 0) {
        GetAntIndex(plane, i, &lifeField, &column, &life, &state, &direction);
        *index = i;
        return life;
    }
    *index = -1;
    return -1;
}

int16_t  FindLifeAt(int16_t  *index, int16_t plane, int16_t x, int16_t y)
{
    int16_t i;
    int16_t life;
    int16_t direction;
    int16_t state;
    int16_t column;
    int16_t lifeField;

    life = GetLife(plane, x, y);
    if (life >= 0 && !IsYellowAnt(life)) {
        *index = FindAntIndex(plane, x, y, life);
        return life;
    }
    i = FindLifeIndex(plane, x, y, 1, 0x7f, 0x7f);
    if (i >= 0) {
        GetAntIndex(plane, i, &lifeField, &column, &life, &state, &direction);
        *index = i;
        return life;
    }
    *index = -1;
    return -1;
}

void  SetMyHealth(int16_t health)
{
    if (!fd_3D57_0C16)
        native_state_MeHealth.signed_value = health;
    else
        native_state_MeHealth.signed_value = 100;
    if (native_state_MeHealth.signed_value > 0)
        native_state_fd_50F6_1006.signed_value = 0;
    if (native_state_MeHealth.signed_value > 100)
        native_state_MeHealth.signed_value = 100;
    else if (native_state_MeHealth.signed_value < 0)
        native_state_MeHealth.signed_value = 0;
    if (native_state_MeHealth.signed_value > native_state_fd_50F6_0FBA.signed_value && native_state_MeHealth.signed_value >= 10)
        native_state_fd_50F6_1044.signed_value = 0;
    else
        native_state_fd_50F6_1044.signed_value = 1;
}

void  EatMyFood(int16_t kind)
{
    switch (kind) {
    case 0:
        myBeginSound(0x2c, 0, 0x7e);
        SetDefaultWindPrompt(1);
        break;
    case 1:
        YellowDialog(0x2396, -1);
        fd_50F6_0472 = 0L;
        EditMessage(fd_50F6_034C[11], 120L, 0);
        break;
    case 2:
        EditMessage(fd_50F6_034C[12], 120L, 0);
        break;
    case 3:
        myBeginSound(0x2c, 0, 0x7e);
        while (!mySoundIsDone())
            myDelay(5L);
        myBeginSound(10, 0, 0x7e);
        fd_50F6_0472 = 0L;
        EditMessage(fd_50F6_034C[13], 180L, 0);
        break;
    }
    if (kind != 2) {
        if (native_state_MeHealth.signed_value + 100 > 100 && kind != 1 && native_state_BpopT.signed_value - 1 > 0) {
            native_state_HealthB.signed_value += native_state_MeHealth.signed_value / (native_state_BpopT.signed_value - 1);
            if (native_state_HealthB.signed_value > 100)
                native_state_HealthB.signed_value = 100;
        }
        SetMyHealth(100);
    } else if (native_state_MeHealth.signed_value > 10)
        SetMyHealth(native_state_MeHealth.signed_value - 10);
}

int16_t  PickupMyEgg(int16_t plane, int16_t x, int16_t y)
{
    int16_t egg;
    int16_t index;

    if (fd_50F6_04C2 == 0x10 || native_state_MeHealth.signed_value < 10) {
        fd_3D57_0C22 = 0xfd;
        egg = FindEggAt(&index, plane, x, y);
        if (egg >= 0) {
            SetAntIndex(plane, index, 0, 0, 0, 0, 0);
            if (x != MeLocX || y != MeLocY)
                SetLife(plane, x, y, 0);
            if (native_state_MeHealth.signed_value >= 10) {
                myBeginSound(0x1c, 0, 0x7e);
                fd_3D57_0C22 = egg;
                fd_50F6_04C2 = 8;
            } else
                fd_3D57_0C26 = 3;
            return 1;
        }
    }
    return 0;
}

int16_t  PickupMyFood(int16_t plane, int16_t x, int16_t y)
{
    int16_t eat;
    int16_t tile;

    if (!IsItFoodAt(plane, x, y))
        return 0;
    if (native_state_fd_50F6_1044.signed_value)
        eat = 1;
    else if (fd_50F6_04C2 == 0x10 || fd_50F6_04C2 == 0x30)
        eat = 0;
    else
        return 0;
    if (plane <= 1) {
        PickupFoodA(x, y);
        if (!eat) {
            native_state_fd_50F6_04C4.signed_value = 200;
            native_state_fd_50F6_0B1E.signed_value = GetDis(x, y, fd_3D57_02AC[0], fd_3D57_02AC[1]);
            native_state_fd_50F6_0C38.signed_value = native_state_fd_50F6_0B1E.signed_value + 1;
            JamScentBT(x, y, native_state_fd_50F6_04C4.signed_value);
        }
    } else {
        tile = GetMap(plane, x, y);
        if (tile == 0x10)
            tile = SRand8();
        else
            tile--;
        SetMap(plane, x, y, tile);
        if (plane == 2) {
            if (native_state_FoodB.signed_value > 0)
                native_state_FoodB.signed_value--;
        } else if (native_state_FoodR.signed_value > 0)
            native_state_FoodR.signed_value--;
    }
    if (eat)
        fd_3D57_0C26 = 0;
    else {
        myBeginSound(0x1d, 0, 0x7e);
        fd_50F6_04C2 += 8;
    }
    return 1;
}

int16_t  DropMyObject(int16_t first, int16_t second, int16_t third, int16_t fourth, int16_t fifth)
{
    switch (fd_50F6_04C2) {
    case 8:
        return DropMyEgg(first, second, third, fourth, fifth);
    case 0x18:
    case 0x38:
        return DropMyFood(first, second, third, fourth, fifth);
    case 0x28:
    case 0x48:
        return DropMyRock(first, second, third, fourth, fifth);
    }
    return 0;
}

int16_t  PickupMyObject(int16_t plane, int16_t x, int16_t y)
{
    int16_t result;

    if (fd_50F6_04C2 & 8)
        return 0;
    result = PickupMyEgg(plane, x, y);
    if (result == 0) {
        result = PickupMyRock(plane, x, y);
        if (result == 0)
            result = PickupMyFood(plane, x, y);
    }
    return result;
}

int16_t  TileCanBeMovedOn(int16_t plane, int16_t x, int16_t y, int16_t fromPlane, int16_t fromX, int16_t fromY, int16_t digging)
{
    int16_t dig;
    int16_t ok;
    int16_t tile;

    if (plane <= 1) {
        if (x >= 0 && x <= 127 && y >= 0 && y <= 63) {
            dig = MapA[x][y];
            if (!TERRAINset)
                ok = dig <= 0x53;
            else
                ok = dig <= 0x90;
        } else
            ok = 0;
    } else if (x >= 0 && x <= 63 && y >= 0 && y <= 63) {
        if (plane == 2)
            tile = MapB[x][y];
        else
            tile = MapR[x][y];
        if (tile <= 0x18 || (tile >= 0x30 && tile <= 0x31)) {
            ok = 1;
            dig = 0;
        } else if (digging && ((tile >= 0x20 && tile <= 0x2e) || (tile >= 0x1c && tile <= 0x1f))) {
            ok = 1;
            dig = 1;
        } else
            ok = 0;
        if (ok && y <= 1 && fromPlane == plane) {
            if (!digging) {
                if (y == 0) {
                    if (fromX != x || fromY != y)
                        ok = 0;
                } else if (fromX != x && !fromY)
                    ok = 0;
            } else if (dig) {
                if (fromX != x)
                    ok = 0;
                else if (y == 0) {
                    if (plane == 2)
                        tile = MapB[x][y + 1];
                    else
                        tile = MapR[x][y + 1];
                    if (tile >= 0x20 && tile <= 0x2e)
                        ok = 0;
                }
            } else if (y == 0 && (fromX != x || fromY != y))
                ok = 0;
        }
    } else
        ok = 0;
    return ok;
}

int16_t  IsNotBarrier(int16_t x)
{
    if (!TERRAINset)
        return x <= 0x50;
    return x <= 0x5f;
}

int16_t  IsNotObstacle(int16_t plane, int16_t x, int16_t y)
{
    int16_t tile;
    int16_t ok;

    tile = GetMap(plane, x, y);
    if (tile < 0)
        ok = 0;
    else if (plane <= 1) {
        if (!TERRAINset)
            ok = tile <= 0x53;
        else
            ok = IsNotBarrier(tile);
    } else if (tile <= 0x18 || IsThisPebble(plane, tile))
        ok = 1;
    else
        ok = 0;
    return ok;
}

int16_t  IsItDigable(int16_t plane, int16_t x, int16_t y)
{
    int16_t tile;

    if (plane >= 2 && IsValidB(x, y)) {
        tile = GetMap(plane, x, y);
        if (IsItDirt(tile))
            return 1;
        if (IsThisGrass(plane, tile))
            return 1;
    }
    return 0;
}

int16_t  IsItYellow(int16_t plane, int16_t x, int16_t y)
{
    int16_t life;

    if (!IsSamePlane(plane))
        return 0;
    if (fd_50F6_0A06 == 1) {
        if (plane > 1)
            return 0;
        if (GetDis(x * 16 + 8, y * 16 + 8, native_state_fd_50F6_0F12.signed_value, native_state_fd_50F6_0F34.signed_value) < 0x200)
            return 1;
        return 0;
    }
    switch (plane) {
    case 0:
    case 1:
        life = LifeA[x][y];
        break;
    case 2:
        life = LifeB[x][y];
        break;
    case 3:
        life = LifeR[x][y];
        break;
    }
    return IsYellowAnt(life);
}

int16_t  IsLessThanHole(int16_t x)
{
    if (!TERRAINset)
        return x < 0x50;
    return x < 0x59;
}

int16_t  IsSamePlane(int16_t plane)
{
    if (MePlane == (plane == 0 ? 1 : plane))
        return 1;
    return 0;
}

int16_t  IsLiftable(int16_t plane, int16_t x, int16_t y)
{
    int16_t tile;
    int16_t eggIndex;
    int16_t egg;

    egg = FindEggAt(&eggIndex, plane, x, y);
    tile = GetMap(plane, x, y);
    return IsThisFood(plane, tile) || IsThisPebble(plane, tile) || IsThisEgg(egg);
}

int16_t  TryMyDropOrLift(int16_t plane, int16_t x, int16_t y)
{
    int16_t dir;
    int16_t result;

    if (fd_50F6_04C2 & 8)
        result = DropMyObject(plane, MeLocX, MeLocY, x, y) ? 1 : -1;
    else if (!PickupMyObject(plane, x, y)) {
        if ((fd_3D57_0798 || (fd_50F6_04C2 == 0x40 && !fd_3D57_0C24)) &&
            MePlane == 1 && MeLocX == x && MeLocY == y) {
            if (DigMyNewHole(x, y)) {
                o25_3BA4_1035();
                GotoMyAnt();
                result = 1;
            } else
                result = -1;
        } else
            result = 0;
    } else {
        dir = GetDir(MeLocX, MeLocY, x, y);
        if (dir > 0)
            MoveMyLife(MePlane, MeLocX, MeLocY, fd_50F6_04C2, dir - 1);
        DoEditUpdateDraw();
        if (fd_3D57_0C26 >= 0) {
            EatMyFood(fd_3D57_0C26);
            fd_3D57_0C26 = -1;
        }
        result = 1;
    }
    return result;
}

int16_t  IsItAHole(int16_t plane, int16_t x, int16_t y)
{
    if (plane <= 1)
        return IsItHole(x, y);
    if (y > 0)
        return 0;
    if (GetMap(plane, x, y) == 0x18)
        return 1;
    return 0;
}

int16_t  IsValidA(int16_t x, int16_t y)
{
    if (x >= 0 && x <= 127 && y >= 0 && y <= 63)
        return 1;
    return 0;
}

int16_t  IsValidB(int16_t x, int16_t y)
{
    if (x >= 0 && x <= 63 && y >= 0 && y <= 63)
        return 1;
    return 0;
}

#pragma pack(pop)
