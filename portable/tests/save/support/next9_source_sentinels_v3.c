#include "next9_source_sentinels_v3.h"
#include <stdint.h>
#include <stddef.h>
static uint8_t source_sentinel_byte(uint32_t address)
{
    uint32_t x = address;
    x ^= x >> 11;
    x *= 0x45D9F3Bu;
    x ^= x >> 16;
    return (uint8_t)(x ^ (x >> 8) ^ (x >> 24));
}
void portable_next9_fill_source_address_sentinels(RecoveredState *state)
{
    if (state == NULL) return;
    { uint8_t *p = (uint8_t *)(void *)&state->AlistM;
      size_t n = sizeof(state->AlistM); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(297762) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->AlistS;
      size_t n = sizeof(state->AlistS); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(299764) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->AlistT;
      size_t n = sizeof(state->AlistT); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(298763) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->AlistX;
      size_t n = sizeof(state->AlistX); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(295760) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->AlistY;
      size_t n = sizeof(state->AlistY); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(296761) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->AntsEatenByLions;
      size_t n = sizeof(state->AntsEatenByLions); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334184) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334184) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->BAntsEaten;
      size_t n = sizeof(state->BAntsEaten); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335488) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335488) + (uint32_t)((i / 4u) * 4u + (3u - (i % 4u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->Barrier;
      size_t n = sizeof(state->Barrier); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332768) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332768) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->BlistM;
      size_t n = sizeof(state->BlistM); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(301767) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->BlistS;
      size_t n = sizeof(state->BlistS); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(302769) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->BlistT;
      size_t n = sizeof(state->BlistT); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(302268) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->BlistX;
      size_t n = sizeof(state->BlistX); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(300765) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->BlistY;
      size_t n = sizeof(state->BlistY); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(301266) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->BpopT;
      size_t n = sizeof(state->BpopT); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332432) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332432) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->CasteAuto;
      size_t n = sizeof(state->CasteAuto); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(253272) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(253272) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->CasteModeTabB;
      size_t n = sizeof(state->CasteModeTabB); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254318) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->CasteTabB;
      size_t n = sizeof(state->CasteTabB); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254166) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254166) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->ChaseSpid;
      size_t n = sizeof(state->ChaseSpid); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332200) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332200) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->CurExpTool;
      size_t n = sizeof(state->CurExpTool); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335788) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335788) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->CurGndTileID;
      size_t n = sizeof(state->CurGndTileID); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(253200) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(253200) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->Cycle;
      size_t n = sizeof(state->Cycle); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335464) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335464) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->DROPdir;
      size_t n = sizeof(state->DROPdir); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335514) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335514) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->DeathCnt;
      size_t n = sizeof(state->DeathCnt); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335866) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335866) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->Dx8;
      size_t n = sizeof(state->Dx8); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(251248) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->Dx9;
      size_t n = sizeof(state->Dx9); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(251264) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->Dy8;
      size_t n = sizeof(state->Dy8); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(251256) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->Dy9;
      size_t n = sizeof(state->Dy9); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(251274) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->EatCnt;
      size_t n = sizeof(state->EatCnt); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335796) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335796) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->ExitMapB;
      size_t n = sizeof(state->ExitMapB); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(271184) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->ExitMapR;
      size_t n = sizeof(state->ExitMapR); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(275280) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->ExpSubStates;
      size_t n = sizeof(state->ExpSubStates); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(253222) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->FoodB;
      size_t n = sizeof(state->FoodB); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335792) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335792) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->FoodR;
      size_t n = sizeof(state->FoodR); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335808) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335808) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->FuzLocX;
      size_t n = sizeof(state->FuzLocX); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332170) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332170) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->FuzLocY;
      size_t n = sizeof(state->FuzLocY); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332184) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332184) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->HealthB;
      size_t n = sizeof(state->HealthB); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335902) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335902) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->HealthR;
      size_t n = sizeof(state->HealthR); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332126) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332126) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->HoleMapB;
      size_t n = sizeof(state->HoleMapB); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(251796) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->HoleMapR;
      size_t n = sizeof(state->HoleMapR); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(251860) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->IdealCaste;
      size_t n = sizeof(state->IdealCaste); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(253258) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(253258) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->InitialLions;
      size_t n = sizeof(state->InitialLions); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(333898) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(333898) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->LifeA;
      size_t n = sizeof(state->LifeA); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(279376) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->LifeB;
      size_t n = sizeof(state->LifeB); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(287568) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->LifeR;
      size_t n = sizeof(state->LifeR); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(291664) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->LionIndex;
      size_t n = sizeof(state->LionIndex); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254394) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254394) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->LionListM;
      size_t n = sizeof(state->LionListM); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334362) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->LionListS;
      size_t n = sizeof(state->LionListS); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334380) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->LionListT;
      size_t n = sizeof(state->LionListT); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334398) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->LionListX;
      size_t n = sizeof(state->LionListX); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334322) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->LionListY;
      size_t n = sizeof(state->LionListY); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334344) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->ListIndexA;
      size_t n = sizeof(state->ListIndexA); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335050) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335050) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->ListIndexB;
      size_t n = sizeof(state->ListIndexB); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335112) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335112) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->ListIndexR;
      size_t n = sizeof(state->ListIndexR); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335370) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335370) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->MapA;
      size_t n = sizeof(state->MapA); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254800) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->MapB;
      size_t n = sizeof(state->MapB); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(262992) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->MapPlane;
      size_t n = sizeof(state->MapPlane); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332430) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332430) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->MapR;
      size_t n = sizeof(state->MapR); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(267088) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->MeHealth;
      size_t n = sizeof(state->MeHealth); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335576) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335576) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->MeLocX;
      size_t n = sizeof(state->MeLocX); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332764) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332764) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->MeLocY;
      size_t n = sizeof(state->MeLocY); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332778) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332778) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->MePlane;
      size_t n = sizeof(state->MePlane); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332780) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332780) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->ModeAuto;
      size_t n = sizeof(state->ModeAuto); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332504) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332504) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->ModeMe;
      size_t n = sizeof(state->ModeMe); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254336) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254336) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->ModeTabB;
      size_t n = sizeof(state->ModeTabB); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254174) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254174) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->ModeTabSB;
      size_t n = sizeof(state->ModeTabSB); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254270) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->ModeTabWB;
      size_t n = sizeof(state->ModeTabWB); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254222) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->PherMapA;
      size_t n = sizeof(state->PherMapA); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(307823) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->PherMapBN;
      size_t n = sizeof(state->PherMapBN); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(311919) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->PherMapBT;
      size_t n = sizeof(state->PherMapBT); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(313967) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->PherMapRN;
      size_t n = sizeof(state->PherMapRN); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(316015) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->PherMapRT;
      size_t n = sizeof(state->PherMapRT); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(318064) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->PillDir;
      size_t n = sizeof(state->PillDir); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334748) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334748) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->PillarMap;
      size_t n = sizeof(state->PillarMap); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335100) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335100) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->PillarSeg;
      size_t n = sizeof(state->PillarSeg); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334742) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334742) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->PillarState;
      size_t n = sizeof(state->PillarState); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254396) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254396) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->PillarX;
      size_t n = sizeof(state->PillarX); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254398) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254398) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->PillarY;
      size_t n = sizeof(state->PillarY); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254400) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254400) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->RAntsEaten;
      size_t n = sizeof(state->RAntsEaten); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335584) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335584) + (uint32_t)((i / 4u) * 4u + (3u - (i % 4u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->RT3;
      size_t n = sizeof(state->RT3); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(253640) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->RT5;
      size_t n = sizeof(state->RT5); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(253490) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->RedLocX;
      size_t n = sizeof(state->RedLocX); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332784) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332784) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->RedLocY;
      size_t n = sizeof(state->RedLocY); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332788) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332788) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->RedPlane;
      size_t n = sizeof(state->RedPlane); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332792) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332792) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->RlistM;
      size_t n = sizeof(state->RlistM); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(304272) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->RlistS;
      size_t n = sizeof(state->RlistS); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(305274) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->RlistT;
      size_t n = sizeof(state->RlistT); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(304773) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->RlistX;
      size_t n = sizeof(state->RlistX); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(303270) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->RlistY;
      size_t n = sizeof(state->RlistY); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(303771) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->RpopT;
      size_t n = sizeof(state->RpopT); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332464) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332464) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->SCorpseBase;
      size_t n = sizeof(state->SCorpseBase); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335802) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335802) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->SMode;
      size_t n = sizeof(state->SMode); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335640) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335640) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->Scycle;
      size_t n = sizeof(state->Scycle); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335778) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335778) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->Scycle2;
      size_t n = sizeof(state->Scycle2); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335826) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335826) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->SowDir;
      size_t n = sizeof(state->SowDir); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335482) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335482) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->SowSave;
      size_t n = sizeof(state->SowSave); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335496) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335496) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->SowTab;
      size_t n = sizeof(state->SowTab); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254402) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->SowX;
      size_t n = sizeof(state->SowX); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335374) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335374) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->SowY;
      size_t n = sizeof(state->SowY); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335456) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335456) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->SpidBurpCnt;
      size_t n = sizeof(state->SpidBurpCnt); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335830) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335830) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->SpidRevenge;
      size_t n = sizeof(state->SpidRevenge); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335850) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335850) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->Starg;
      size_t n = sizeof(state->Starg); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335708) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335708) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->StargLife;
      size_t n = sizeof(state->StargLife); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335886) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335886) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->StrategicModeB;
      size_t n = sizeof(state->StrategicModeB); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335860) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335860) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->SuserX;
      size_t n = sizeof(state->SuserX); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335522) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335522) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->SuserY;
      size_t n = sizeof(state->SuserY); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335582) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335582) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->TERRAINset;
      size_t n = sizeof(state->TERRAINset); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335492) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335492) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->TilesDugR;
      size_t n = sizeof(state->TilesDugR); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332178) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332178) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->Tindex;
      size_t n = sizeof(state->Tindex); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335480) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335480) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->TurnTab;
      size_t n = sizeof(state->TurnTab); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(251284) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->YardMode;
      size_t n = sizeof(state->YardMode); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332476) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332476) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->casteLevels;
      size_t n = sizeof(state->casteLevels); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332770) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332770) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_006C;
      size_t n = sizeof(state->fd_3D57_006C); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(251356) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0074;
      size_t n = sizeof(state->fd_3D57_0074); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(251364) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(251364) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0094;
      size_t n = sizeof(state->fd_3D57_0094); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(251396) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_00A4;
      size_t n = sizeof(state->fd_3D57_00A4); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(251412) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0164;
      size_t n = sizeof(state->fd_3D57_0164); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(251604) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_02A4;
      size_t n = sizeof(state->fd_3D57_02A4); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(251924) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(251924) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_02A8;
      size_t n = sizeof(state->fd_3D57_02A8); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(251928) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(251928) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_02AC;
      size_t n = sizeof(state->fd_3D57_02AC); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(251932) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(251932) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_02B0;
      size_t n = sizeof(state->fd_3D57_02B0); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(251936) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(251936) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_02B4;
      size_t n = sizeof(state->fd_3D57_02B4); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(251940) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(251940) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_02B8;
      size_t n = sizeof(state->fd_3D57_02B8); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(251944) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(251944) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_02BC;
      size_t n = sizeof(state->fd_3D57_02BC); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(251948) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(251948) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_02C0;
      size_t n = sizeof(state->fd_3D57_02C0); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(251952) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(251952) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_02C2;
      size_t n = sizeof(state->fd_3D57_02C2); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(251954) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(251954) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0798;
      size_t n = sizeof(state->fd_3D57_0798); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(253192) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(253192) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_07A2;
      size_t n = sizeof(state->fd_3D57_07A2); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(253202) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(253202) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_07A4;
      size_t n = sizeof(state->fd_3D57_07A4); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(253204) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(253204) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_07A6;
      size_t n = sizeof(state->fd_3D57_07A6); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(253206) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(253206) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_07A8;
      size_t n = sizeof(state->fd_3D57_07A8); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(253208) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(253208) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_07BE;
      size_t n = sizeof(state->fd_3D57_07BE); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(253230) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(253230) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_07C0;
      size_t n = sizeof(state->fd_3D57_07C0); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(253232) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(253232) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_07C8;
      size_t n = sizeof(state->fd_3D57_07C8); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(253240) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(253240) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_07CC;
      size_t n = sizeof(state->fd_3D57_07CC); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(253244) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(253244) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_07EA;
      size_t n = sizeof(state->fd_3D57_07EA); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(253274) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(253274) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_07EC;
      size_t n = sizeof(state->fd_3D57_07EC); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(253276) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(253276) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_07F2;
      size_t n = sizeof(state->fd_3D57_07F2); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(253282) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(253282) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_080A;
      size_t n = sizeof(state->fd_3D57_080A); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(253306) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(253306) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0810;
      size_t n = sizeof(state->fd_3D57_0810); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(253312) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(253312) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0828;
      size_t n = sizeof(state->fd_3D57_0828); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(253336) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(253336) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_087A;
      size_t n = sizeof(state->fd_3D57_087A); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(253418) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0994;
      size_t n = sizeof(state->fd_3D57_0994); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(253700) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_099C;
      size_t n = sizeof(state->fd_3D57_099C); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(253708) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_09A4;
      size_t n = sizeof(state->fd_3D57_09A4); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(253716) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_09AC;
      size_t n = sizeof(state->fd_3D57_09AC); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(253724) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0B14;
      size_t n = sizeof(state->fd_3D57_0B14); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254084) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254084) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0B24;
      size_t n = sizeof(state->fd_3D57_0B24); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254100) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0B36;
      size_t n = sizeof(state->fd_3D57_0B36); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254118) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0C0E;
      size_t n = sizeof(state->fd_3D57_0C0E); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254334) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254334) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0C12;
      size_t n = sizeof(state->fd_3D57_0C12); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254338) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254338) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0C14;
      size_t n = sizeof(state->fd_3D57_0C14); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254340) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254340) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0C16;
      size_t n = sizeof(state->fd_3D57_0C16); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254342) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254342) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0C18;
      size_t n = sizeof(state->fd_3D57_0C18); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254344) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254344) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0C1A;
      size_t n = sizeof(state->fd_3D57_0C1A); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254346) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254346) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0C1C;
      size_t n = sizeof(state->fd_3D57_0C1C); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254348) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254348) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0C1E;
      size_t n = sizeof(state->fd_3D57_0C1E); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254350) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254350) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0C20;
      size_t n = sizeof(state->fd_3D57_0C20); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254352) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254352) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0C22;
      size_t n = sizeof(state->fd_3D57_0C22); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254354) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254354) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0C24;
      size_t n = sizeof(state->fd_3D57_0C24); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254356) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254356) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0C26;
      size_t n = sizeof(state->fd_3D57_0C26); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254358) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254358) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0C28;
      size_t n = sizeof(state->fd_3D57_0C28); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254360) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254360) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0C2A;
      size_t n = sizeof(state->fd_3D57_0C2A); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254362) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254362) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0C2C;
      size_t n = sizeof(state->fd_3D57_0C2C); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254364) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254364) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0C2E;
      size_t n = sizeof(state->fd_3D57_0C2E); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254366) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254366) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0C30;
      size_t n = sizeof(state->fd_3D57_0C30); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254368) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254368) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0C32;
      size_t n = sizeof(state->fd_3D57_0C32); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254370) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254370) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0C34;
      size_t n = sizeof(state->fd_3D57_0C34); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254372) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254372) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0C36;
      size_t n = sizeof(state->fd_3D57_0C36); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254374) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0C3A;
      size_t n = sizeof(state->fd_3D57_0C3A); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254378) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0C3E;
      size_t n = sizeof(state->fd_3D57_0C3E); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254382) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254382) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0C40;
      size_t n = sizeof(state->fd_3D57_0C40); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254384) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254384) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0C42;
      size_t n = sizeof(state->fd_3D57_0C42); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254386) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254386) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0C44;
      size_t n = sizeof(state->fd_3D57_0C44); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254388) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254388) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0C46;
      size_t n = sizeof(state->fd_3D57_0C46); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254390) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254390) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3D57_0C48;
      size_t n = sizeof(state->fd_3D57_0C48); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254392) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254392) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3E1D_0000;
      size_t n = sizeof(state->fd_3E1D_0000); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(254416) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(254416) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3E1D_C89F;
      size_t n = sizeof(state->fd_3E1D_C89F); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(305775) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_3E1D_D89F;
      size_t n = sizeof(state->fd_3E1D_D89F); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(309871) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0200;
      size_t n = sizeof(state->fd_50F6_0200); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332128) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332128) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0202;
      size_t n = sizeof(state->fd_50F6_0202); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332130) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332130) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0204;
      size_t n = sizeof(state->fd_50F6_0204); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332132) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332132) + (uint32_t)((i / 4u) * 4u + (3u - (i % 4u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0208;
      size_t n = sizeof(state->fd_50F6_0208); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332136) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332136) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_020E;
      size_t n = sizeof(state->fd_50F6_020E); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332142) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332142) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0210;
      size_t n = sizeof(state->fd_50F6_0210); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332144) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332144) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0212;
      size_t n = sizeof(state->fd_50F6_0212); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332146) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332146) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0214;
      size_t n = sizeof(state->fd_50F6_0214); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332148) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332148) + (uint32_t)((i / 4u) * 4u + (3u - (i % 4u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0220;
      size_t n = sizeof(state->fd_50F6_0220); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332160) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332160) + (uint32_t)((i / 4u) * 4u + (3u - (i % 4u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0224;
      size_t n = sizeof(state->fd_50F6_0224); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332164) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332164) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0226;
      size_t n = sizeof(state->fd_50F6_0226); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332166) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332166) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0228;
      size_t n = sizeof(state->fd_50F6_0228); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332168) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332168) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_022C;
      size_t n = sizeof(state->fd_50F6_022C); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332172) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332172) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_022E;
      size_t n = sizeof(state->fd_50F6_022E); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332174) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332174) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_023E;
      size_t n = sizeof(state->fd_50F6_023E); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332190) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332190) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0240;
      size_t n = sizeof(state->fd_50F6_0240); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332192) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332192) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0242;
      size_t n = sizeof(state->fd_50F6_0242); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332194) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332194) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0244;
      size_t n = sizeof(state->fd_50F6_0244); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332196) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332196) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0246;
      size_t n = sizeof(state->fd_50F6_0246); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332198) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332198) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_024E;
      size_t n = sizeof(state->fd_50F6_024E); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332206) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332206) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0254;
      size_t n = sizeof(state->fd_50F6_0254); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332212) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332212) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0256;
      size_t n = sizeof(state->fd_50F6_0256); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332214) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_02BE;
      size_t n = sizeof(state->fd_50F6_02BE); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332318) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332318) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_02C0;
      size_t n = sizeof(state->fd_50F6_02C0); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332320) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_032C;
      size_t n = sizeof(state->fd_50F6_032C); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332428) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332428) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0332;
      size_t n = sizeof(state->fd_50F6_0332); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332434) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332434) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0334;
      size_t n = sizeof(state->fd_50F6_0334); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332436) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332436) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0352;
      size_t n = sizeof(state->fd_50F6_0352); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332466) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332466) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0354;
      size_t n = sizeof(state->fd_50F6_0354); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332468) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332468) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0356;
      size_t n = sizeof(state->fd_50F6_0356); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332470) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332470) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0358;
      size_t n = sizeof(state->fd_50F6_0358); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332472) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332472) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_035E;
      size_t n = sizeof(state->fd_50F6_035E); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332478) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332478) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0364;
      size_t n = sizeof(state->fd_50F6_0364); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332484) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332484) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0366;
      size_t n = sizeof(state->fd_50F6_0366); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332486) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332486) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_036C;
      size_t n = sizeof(state->fd_50F6_036C); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332492) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332492) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_036E;
      size_t n = sizeof(state->fd_50F6_036E); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332494) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332494) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0370;
      size_t n = sizeof(state->fd_50F6_0370); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332496) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332496) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0376;
      size_t n = sizeof(state->fd_50F6_0376); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332502) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332502) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_037A;
      size_t n = sizeof(state->fd_50F6_037A); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332506) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332506) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_037C;
      size_t n = sizeof(state->fd_50F6_037C); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332508) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_03E0;
      size_t n = sizeof(state->fd_50F6_03E0); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332608) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332608) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_03E2;
      size_t n = sizeof(state->fd_50F6_03E2); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332610) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332610) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0400;
      size_t n = sizeof(state->fd_50F6_0400); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332640) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332640) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0402;
      size_t n = sizeof(state->fd_50F6_0402); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332642) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332642) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0404;
      size_t n = sizeof(state->fd_50F6_0404); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332644) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0468;
      size_t n = sizeof(state->fd_50F6_0468); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332744) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332744) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_046A;
      size_t n = sizeof(state->fd_50F6_046A); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332746) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332746) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0470;
      size_t n = sizeof(state->fd_50F6_0470); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332752) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332752) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0472;
      size_t n = sizeof(state->fd_50F6_0472); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332754) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332754) + (uint32_t)((i / 4u) * 4u + (3u - (i % 4u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0476;
      size_t n = sizeof(state->fd_50F6_0476); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332758) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332758) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0478;
      size_t n = sizeof(state->fd_50F6_0478); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332760) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332760) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_047A;
      size_t n = sizeof(state->fd_50F6_047A); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332762) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332762) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_047E;
      size_t n = sizeof(state->fd_50F6_047E); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332766) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332766) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0488;
      size_t n = sizeof(state->fd_50F6_0488); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332776) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332776) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_048E;
      size_t n = sizeof(state->fd_50F6_048E); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332782) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332782) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0492;
      size_t n = sizeof(state->fd_50F6_0492); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332786) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332786) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0496;
      size_t n = sizeof(state->fd_50F6_0496); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332790) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332790) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_049A;
      size_t n = sizeof(state->fd_50F6_049A); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332794) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332794) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_04A4;
      size_t n = sizeof(state->fd_50F6_04A4); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332804) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332804) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_04BE;
      size_t n = sizeof(state->fd_50F6_04BE); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332830) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332830) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_04C2;
      size_t n = sizeof(state->fd_50F6_04C2); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332834) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332834) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_04C4;
      size_t n = sizeof(state->fd_50F6_04C4); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332836) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332836) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_04C6;
      size_t n = sizeof(state->fd_50F6_04C6); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332838) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332838) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_04E0;
      size_t n = sizeof(state->fd_50F6_04E0); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332864) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332864) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_04E2;
      size_t n = sizeof(state->fd_50F6_04E2); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332866) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332866) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_04E4;
      size_t n = sizeof(state->fd_50F6_04E4); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332868) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332868) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_04F2;
      size_t n = sizeof(state->fd_50F6_04F2); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332882) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332882) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_04F4;
      size_t n = sizeof(state->fd_50F6_04F4); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332884) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332884) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0502;
      size_t n = sizeof(state->fd_50F6_0502); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332898) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332898) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0504;
      size_t n = sizeof(state->fd_50F6_0504); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332900) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332900) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0506;
      size_t n = sizeof(state->fd_50F6_0506); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332902) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332902) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0508;
      size_t n = sizeof(state->fd_50F6_0508); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332904) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332904) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0510;
      size_t n = sizeof(state->fd_50F6_0510); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332912) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332912) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0516;
      size_t n = sizeof(state->fd_50F6_0516); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332918) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332918) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0596;
      size_t n = sizeof(state->fd_50F6_0596); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(333046) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(333046) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_059E;
      size_t n = sizeof(state->fd_50F6_059E); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(333054) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(333054) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_05A0;
      size_t n = sizeof(state->fd_50F6_05A0); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(333056) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(333056) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0624;
      size_t n = sizeof(state->fd_50F6_0624); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(333188) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(333188) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0626;
      size_t n = sizeof(state->fd_50F6_0626); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(333190) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(333190) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_06A6;
      size_t n = sizeof(state->fd_50F6_06A6); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(333318) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(333318) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_06AA;
      size_t n = sizeof(state->fd_50F6_06AA); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(333322) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(333322) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_06AC;
      size_t n = sizeof(state->fd_50F6_06AC); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(333324) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(333324) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_06AE;
      size_t n = sizeof(state->fd_50F6_06AE); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(333326) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(333326) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_072E;
      size_t n = sizeof(state->fd_50F6_072E); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(333454) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(333454) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0736;
      size_t n = sizeof(state->fd_50F6_0736); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(333462) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(333462) + (uint32_t)((i / 4u) * 4u + (3u - (i % 4u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_073A;
      size_t n = sizeof(state->fd_50F6_073A); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(333466) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(333466) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_073C;
      size_t n = sizeof(state->fd_50F6_073C); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(333468) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(333468) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_07BC;
      size_t n = sizeof(state->fd_50F6_07BC); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(333596) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(333596) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_07C0;
      size_t n = sizeof(state->fd_50F6_07C0); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(333600) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(333600) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_07C2;
      size_t n = sizeof(state->fd_50F6_07C2); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(333602) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(333602) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_07C8;
      size_t n = sizeof(state->fd_50F6_07C8); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(333608) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(333608) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_07CA;
      size_t n = sizeof(state->fd_50F6_07CA); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(333610) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(333610) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_07CE;
      size_t n = sizeof(state->fd_50F6_07CE); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(333614) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(333614) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_084E;
      size_t n = sizeof(state->fd_50F6_084E); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(333742) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(333742) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0850;
      size_t n = sizeof(state->fd_50F6_0850); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(333744) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(333744) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0852;
      size_t n = sizeof(state->fd_50F6_0852); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(333746) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(333746) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0856;
      size_t n = sizeof(state->fd_50F6_0856); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(333750) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(333750) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_08DA;
      size_t n = sizeof(state->fd_50F6_08DA); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(333882) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(333882) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_08DC;
      size_t n = sizeof(state->fd_50F6_08DC); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(333884) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(333884) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_08DE;
      size_t n = sizeof(state->fd_50F6_08DE); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(333886) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(333886) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_08E2;
      size_t n = sizeof(state->fd_50F6_08E2); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(333890) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(333890) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_08E8;
      size_t n = sizeof(state->fd_50F6_08E8); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(333896) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(333896) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_08EC;
      size_t n = sizeof(state->fd_50F6_08EC); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(333900) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(333900) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_08F0;
      size_t n = sizeof(state->fd_50F6_08F0); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(333904) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(333904) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0970;
      size_t n = sizeof(state->fd_50F6_0970); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334032) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334032) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_09F0;
      size_t n = sizeof(state->fd_50F6_09F0); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334160) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334160) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_09F2;
      size_t n = sizeof(state->fd_50F6_09F2); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334162) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334162) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_09FA;
      size_t n = sizeof(state->fd_50F6_09FA); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334170) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334170) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_09FC;
      size_t n = sizeof(state->fd_50F6_09FC); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334172) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334172) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0A00;
      size_t n = sizeof(state->fd_50F6_0A00); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334176) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334176) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0A02;
      size_t n = sizeof(state->fd_50F6_0A02); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334178) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334178) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0A06;
      size_t n = sizeof(state->fd_50F6_0A06); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334182) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334182) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0A0A;
      size_t n = sizeof(state->fd_50F6_0A0A); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334186) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334186) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0A8A;
      size_t n = sizeof(state->fd_50F6_0A8A); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334314) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334314) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0A8E;
      size_t n = sizeof(state->fd_50F6_0A8E); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334318) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334318) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0A90;
      size_t n = sizeof(state->fd_50F6_0A90); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334320) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334320) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0A9C;
      size_t n = sizeof(state->fd_50F6_0A9C); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334332) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334332) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0A9E;
      size_t n = sizeof(state->fd_50F6_0A9E); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334334) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334334) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0AA0;
      size_t n = sizeof(state->fd_50F6_0AA0); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334336) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334336) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0AA2;
      size_t n = sizeof(state->fd_50F6_0AA2); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334338) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334338) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0AA6;
      size_t n = sizeof(state->fd_50F6_0AA6); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334342) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334342) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0AB2;
      size_t n = sizeof(state->fd_50F6_0AB2); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334354) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334354) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0AB6;
      size_t n = sizeof(state->fd_50F6_0AB6); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334358) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334358) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0AC4;
      size_t n = sizeof(state->fd_50F6_0AC4); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334372) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334372) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0AC6;
      size_t n = sizeof(state->fd_50F6_0AC6); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334374) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334374) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0AC8;
      size_t n = sizeof(state->fd_50F6_0AC8); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334376) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334376) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0ACA;
      size_t n = sizeof(state->fd_50F6_0ACA); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334378) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334378) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0AD6;
      size_t n = sizeof(state->fd_50F6_0AD6); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334390) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334390) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0AD8;
      size_t n = sizeof(state->fd_50F6_0AD8); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334392) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334392) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0ADA;
      size_t n = sizeof(state->fd_50F6_0ADA); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334394) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334394) + (uint32_t)((i / 4u) * 4u + (3u - (i % 4u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0AE8;
      size_t n = sizeof(state->fd_50F6_0AE8); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334408) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334408) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0AEA;
      size_t n = sizeof(state->fd_50F6_0AEA); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334410) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334410) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0AEC;
      size_t n = sizeof(state->fd_50F6_0AEC); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334412) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334412) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0AF8;
      size_t n = sizeof(state->fd_50F6_0AF8); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334424) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334424) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0AFA;
      size_t n = sizeof(state->fd_50F6_0AFA); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334426) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334426) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0B06;
      size_t n = sizeof(state->fd_50F6_0B06); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334438) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334438) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0B08;
      size_t n = sizeof(state->fd_50F6_0B08); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334440) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334440) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0B12;
      size_t n = sizeof(state->fd_50F6_0B12); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334450) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334450) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0B1E;
      size_t n = sizeof(state->fd_50F6_0B1E); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334462) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334462) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0B20;
      size_t n = sizeof(state->fd_50F6_0B20); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334464) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334464) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0C26;
      size_t n = sizeof(state->fd_50F6_0C26); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334726) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334726) + (uint32_t)((i / 4u) * 4u + (3u - (i % 4u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0C2A;
      size_t n = sizeof(state->fd_50F6_0C2A); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334730) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334730) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0C38;
      size_t n = sizeof(state->fd_50F6_0C38); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334744) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334744) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0C3A;
      size_t n = sizeof(state->fd_50F6_0C3A); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334746) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334746) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0C3E;
      size_t n = sizeof(state->fd_50F6_0C3E); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(334750) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(334750) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0D40;
      size_t n = sizeof(state->fd_50F6_0D40); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335008) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335008) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0D68;
      size_t n = sizeof(state->fd_50F6_0D68); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335048) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335048) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0D6C;
      size_t n = sizeof(state->fd_50F6_0D6C); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335052) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335052) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0D70;
      size_t n = sizeof(state->fd_50F6_0D70); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335056) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335056) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0D72;
      size_t n = sizeof(state->fd_50F6_0D72); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335058) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335058) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0D9A;
      size_t n = sizeof(state->fd_50F6_0D9A); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335098) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335098) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0EAC;
      size_t n = sizeof(state->fd_50F6_0EAC); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335372) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335372) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0EB6;
      size_t n = sizeof(state->fd_50F6_0EB6); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335382) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335382) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0EF6;
      size_t n = sizeof(state->fd_50F6_0EF6); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335446) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335446) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0EF8;
      size_t n = sizeof(state->fd_50F6_0EF8); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335448) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335448) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0EFA;
      size_t n = sizeof(state->fd_50F6_0EFA); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335450) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335450) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0EFC;
      size_t n = sizeof(state->fd_50F6_0EFC); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335452) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335452) + (uint32_t)((i / 4u) * 4u + (3u - (i % 4u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0F06;
      size_t n = sizeof(state->fd_50F6_0F06); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335462) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335462) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0F0C;
      size_t n = sizeof(state->fd_50F6_0F0C); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335468) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335468) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0F0E;
      size_t n = sizeof(state->fd_50F6_0F0E); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335470) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335470) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0F10;
      size_t n = sizeof(state->fd_50F6_0F10); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335472) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335472) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0F12;
      size_t n = sizeof(state->fd_50F6_0F12); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335474) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335474) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0F26;
      size_t n = sizeof(state->fd_50F6_0F26); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335494) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335494) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0F2E;
      size_t n = sizeof(state->fd_50F6_0F2E); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335502) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335502) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0F30;
      size_t n = sizeof(state->fd_50F6_0F30); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335504) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335504) + (uint32_t)((i / 4u) * 4u + (3u - (i % 4u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0F34;
      size_t n = sizeof(state->fd_50F6_0F34); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335508) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335508) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0F36;
      size_t n = sizeof(state->fd_50F6_0F36); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335510) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335510) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0F3E;
      size_t n = sizeof(state->fd_50F6_0F3E); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335518) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335518) + (uint32_t)((i / 4u) * 4u + (3u - (i % 4u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0F44;
      size_t n = sizeof(state->fd_50F6_0F44); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335524) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335524) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0F46;
      size_t n = sizeof(state->fd_50F6_0F46); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335526) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0F84;
      size_t n = sizeof(state->fd_50F6_0F84); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335588) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0FB6;
      size_t n = sizeof(state->fd_50F6_0FB6); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335638) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335638) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0FBA;
      size_t n = sizeof(state->fd_50F6_0FBA); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335642) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335642) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0FBC;
      size_t n = sizeof(state->fd_50F6_0FBC); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335644) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335644) + (uint32_t)((i / 4u) * 4u + (3u - (i % 4u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0FC2;
      size_t n = sizeof(state->fd_50F6_0FC2); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335650) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335650) + (uint32_t)((i / 4u) * 4u + (3u - (i % 4u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0FC6;
      size_t n = sizeof(state->fd_50F6_0FC6); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335654) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0FFA;
      size_t n = sizeof(state->fd_50F6_0FFA); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335706) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335706) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_0FFE;
      size_t n = sizeof(state->fd_50F6_0FFE); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335710) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335710) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_1000;
      size_t n = sizeof(state->fd_50F6_1000); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335712) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335712) + (uint32_t)((i / 4u) * 4u + (3u - (i % 4u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_1004;
      size_t n = sizeof(state->fd_50F6_1004); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335716) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335716) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_1006;
      size_t n = sizeof(state->fd_50F6_1006); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335718) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335718) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_1008;
      size_t n = sizeof(state->fd_50F6_1008); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335720) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_103C;
      size_t n = sizeof(state->fd_50F6_103C); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335772) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335772) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_1040;
      size_t n = sizeof(state->fd_50F6_1040); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335776) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335776) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_1044;
      size_t n = sizeof(state->fd_50F6_1044); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335780) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335780) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_1048;
      size_t n = sizeof(state->fd_50F6_1048); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335784) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335784) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_104E;
      size_t n = sizeof(state->fd_50F6_104E); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335790) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335790) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_1058;
      size_t n = sizeof(state->fd_50F6_1058); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335800) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335800) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_105C;
      size_t n = sizeof(state->fd_50F6_105C); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335804) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335804) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_105E;
      size_t n = sizeof(state->fd_50F6_105E); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335806) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335806) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_1066;
      size_t n = sizeof(state->fd_50F6_1066); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335814) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335814) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_1068;
      size_t n = sizeof(state->fd_50F6_1068); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335816) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335816) + (uint32_t)((i / 4u) * 4u + (3u - (i % 4u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_106C;
      size_t n = sizeof(state->fd_50F6_106C); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335820) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_1074;
      size_t n = sizeof(state->fd_50F6_1074); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335828) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335828) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_107E;
      size_t n = sizeof(state->fd_50F6_107E); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335838) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335838) + (uint32_t)((i / 4u) * 4u + (3u - (i % 4u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_1082;
      size_t n = sizeof(state->fd_50F6_1082); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335842) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335842) + (uint32_t)((i / 4u) * 4u + (3u - (i % 4u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_108C;
      size_t n = sizeof(state->fd_50F6_108C); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335852) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335852) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_108E;
      size_t n = sizeof(state->fd_50F6_108E); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335854) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335854) + (uint32_t)((i / 4u) * 4u + (3u - (i % 4u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_109C;
      size_t n = sizeof(state->fd_50F6_109C); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335868) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335868) + (uint32_t)((i / 4u) * 4u + (3u - (i % 4u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_10A0;
      size_t n = sizeof(state->fd_50F6_10A0); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335872) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335872) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_10A2;
      size_t n = sizeof(state->fd_50F6_10A2); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335874) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335874) + (uint32_t)((i / 4u) * 4u + (3u - (i % 4u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_10A6;
      size_t n = sizeof(state->fd_50F6_10A6); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335878) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335878) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_10AC;
      size_t n = sizeof(state->fd_50F6_10AC); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335884) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335884) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_10B0;
      size_t n = sizeof(state->fd_50F6_10B0); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335888) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335888) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_10B2;
      size_t n = sizeof(state->fd_50F6_10B2); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335890) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335890) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_10B8;
      size_t n = sizeof(state->fd_50F6_10B8); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335896) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335896) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_10BA;
      size_t n = sizeof(state->fd_50F6_10BA); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335898) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335898) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_10BC;
      size_t n = sizeof(state->fd_50F6_10BC); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335900) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335900) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_10C0;
      size_t n = sizeof(state->fd_50F6_10C0); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335904) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335904) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_10D2;
      size_t n = sizeof(state->fd_50F6_10D2); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335922) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335922) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_10DE;
      size_t n = sizeof(state->fd_50F6_10DE); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335934) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335934) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_10E0;
      size_t n = sizeof(state->fd_50F6_10E0); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335936) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335936) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_110C;
      size_t n = sizeof(state->fd_50F6_110C); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(335980) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(335980) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_3816;
      size_t n = sizeof(state->fd_50F6_3816); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(345974) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(345974) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_3822;
      size_t n = sizeof(state->fd_50F6_3822); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(345986) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(345986) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_382E;
      size_t n = sizeof(state->fd_50F6_382E); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(345998) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(345998) + (uint32_t)((i / 4u) * 4u + (3u - (i % 4u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_383A;
      size_t n = sizeof(state->fd_50F6_383A); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(346010) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(346010) + (uint32_t)((i / 4u) * 4u + (3u - (i % 4u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_3856;
      size_t n = sizeof(state->fd_50F6_3856); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(346038) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(346038) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_50F6_3858;
      size_t n = sizeof(state->fd_50F6_3858); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(346040) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(346040) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_55B3_19BE;
      size_t n = sizeof(state->fd_55B3_19BE); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(357614) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(357614) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_55B3_19C0;
      size_t n = sizeof(state->fd_55B3_19C0); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(357616) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(357616) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_55B3_29A2;
      size_t n = sizeof(state->fd_55B3_29A2); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(361682) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(361682) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_55B3_2A42;
      size_t n = sizeof(state->fd_55B3_2A42); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(361842) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(361842) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->fd_55B3_2CBC;
      size_t n = sizeof(state->fd_55B3_2CBC); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(362476) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(362476) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->g_3DB2;
      size_t n = sizeof(state->g_3DB2); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(366818) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(366818) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->g_5A97;
      size_t n = sizeof(state->g_5A97); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(374215) + (uint32_t)i; (void)a;
        p[i] = source_sentinel_byte(a);
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->knobSize;
      size_t n = sizeof(state->knobSize); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(346002) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(346002) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->modeLevels;
      size_t n = sizeof(state->modeLevels); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(332798) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(332798) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->triHeight;
      size_t n = sizeof(state->triHeight); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(345966) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(345966) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->triWidth;
      size_t n = sizeof(state->triWidth); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(345972) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(345972) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->triWidthL;
      size_t n = sizeof(state->triWidthL); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(345968) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(345968) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
    { uint8_t *p = (uint8_t *)(void *)&state->triWidthR;
      size_t n = sizeof(state->triWidthR); size_t i;
      for (i = 0; i < n; ++i) { uint32_t a = UINT32_C(345970) + (uint32_t)i; (void)a;
#ifdef PORTABLE_LEGACY_SAVE_TEST_FORCE_BIG_ENDIAN
        p[i] = source_sentinel_byte(UINT32_C(345970) + (uint32_t)((i / 2u) * 2u + (1u - (i % 2u))));
#else
        p[i] = source_sentinel_byte(a);
#endif
      } };
}
