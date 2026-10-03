#include <stdint.h>
struct Event { int16_t what, message, x4, x6, h, v, code, xE; };
extern int16_t WinPrintf(char *format, ...);
extern void YardToMap(void);
extern void f_1B73_030F(int16_t, int16_t, int16_t, int16_t, int16_t);
extern void YellowCommand(int16_t);
extern void YellowCommandKey(int16_t);
extern void DoTab(void);
void  o19_384C_0383(struct Event  *ev)
{
    int16_t cmd;

    WinPrintf("\nKEYEVENT=%x, %x", ev->code, ev->message);
    if (ev->message & 4) {
        switch (ev->code) {
        case 0xfa05:
            YardToMap();
            return;
        case 0xfa06:
            cmd = 0xfd22;
            break;
        case 0xfa07:
            cmd = 0xfd23;
            break;
        case 0xfa08:
            cmd = 0xfd24;
            break;
        case 0xfa09:
            cmd = 0xfd26;
            break;
        case 0xfa0a:
            cmd = 0xfd27;
            break;
        case 0xfa0b:
            cmd = 0xfd28;
            break;
        case 0xfa17:
            cmd = 0xfd16;
            break;
        case 0xfa23:
            cmd = 0xfd15;
            break;
        default:
            return;
        }
        f_1B73_030F(cmd, 0, 0, 0, 0);
    } else if (ev->message & 8) {
        switch (ev->code) {
        case 0xfa03:
            YellowCommand(3);
            break;
        }
    } else {
        switch (ev->code) {
        case 0xfa0e:
            YellowCommandKey(0x88);
            break;
        case 0xfa0f:
            DoTab();
            break;
        }
    }
}
