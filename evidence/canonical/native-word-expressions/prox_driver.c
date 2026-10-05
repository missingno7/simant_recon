#include <stdint.h>
#include <stdio.h>

extern int16_t win_DoProxMenu(int16_t, int16_t, int16_t, int16_t, int16_t);
static int16_t event_code;
static int checks;

void __wrap_win_Open(int16_t win, int16_t count, int16_t p0, int16_t p1, int16_t p2, int16_t p3) {
    (void)win; (void)count; (void)p0; (void)p1; (void)p2; (void)p3;
}
void __wrap__win_SetProxItem(int16_t item) { (void)item; }
void __wrap_ButtonHeldInit(void) {}
int16_t __wrap_win_IsWinOpen(int16_t win) { (void)win; return ++checks == 1; }
int16_t __wrap_ButtonHeld(void) { return 0; }
int16_t __wrap_win_GetProxEvent(void) { return event_code; }
int16_t __wrap_win_GetEvent(void *event) { (void)event; return 0; }
void __wrap_win_Close(int16_t win) { (void)win; }

int main(void) {
    unsigned win, ev;
    while (scanf("%u %u", &win, &ev) == 2) {
        int16_t result;
        event_code = (int16_t)ev;
        checks = 0;
        result = win_DoProxMenu((int16_t)win, -1, 2, 0, 0);
        printf("%u %u %d %d\n", win, ev, result, checks);
    }
    return 0;
}
