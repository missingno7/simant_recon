#include <stdint.h>
static uint16_t calls;
static uint16_t index_calls;
static uint16_t cells[2];
static uint16_t next(void) { calls++; return 65535; }
static uint16_t index(void) { index_calls++; return 0; }
int main(void)
{
    uint16_t result;
    int16_t negative = -1;
    uint16_t simant_int_lvalue = 7;
    result = (next() + 3) / 2;
    if (result != 1 || calls != 1) return 1;
    if (0 && next() + 1) return 2;
    if (calls != 1) return 3;
    cells[0] = 65535;
    cells[index()] += next();
    if (cells[0] != 65534 || calls != 2 || index_calls != 1) return 4;
    result = 1 ? 7 : next();
    if (result != 7 || calls != 2) return 5;
    result = (uint16_t)(next() + (uint16_t)-1);
    if (result != 65534 || calls != 3) return 6;
    cells[0] = 1;
    cells[index()] /= negative;
    if (cells[0] != 0 || index_calls != 2) return 7;
    cells[0] = 21;
    cells[0] /= simant_int_lvalue;
    if (cells[0] != 3) return 8;
    return 0;
}
