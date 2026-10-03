#include <stdint.h>
#include <stdio.h>
#include "simulation_state_50f6.h"
#include "native_owners.h"
int16_t fd_3D57_0828 = 4, fd_50F6_0EAC = 1;
uint8_t fd_3D57_00A4[12][16];
static char weights[8] = { 13, 17, 19, 23, 29, 31, 37, 41 };
int32_t  CalcScore(int16_t  *scores)
{
    int16_t i, j, k, n, t;
    int16_t sum, sum2;
    int32_t score, q;

    for (i = 0; i < 8; i++)
        scores[i] = 0;

    k = (native_state_fd_50F6_04F4.signed_value - fd_3D57_0828) & 0x3f;
    sum = 0;
    for (i = 0; i < fd_3D57_0828; i++) {
        sum += native_sim_state_fd_50F6_073C.signed_values[k];
        k = (k + 1) & 0x3f;
    }
    if (i > 0)
        scores[0] = sum / i;
    else
        scores[0] = 0;

    {
        int16_t historyIndex;
        historyIndex = (native_state_fd_50F6_04F4.signed_value - fd_3D57_0828) & 0x3f;
        sum = sum2 = 0;
        for (k = 0; k < fd_3D57_0828; k++) {
            sum += native_sim_state_fd_50F6_0626.signed_values[historyIndex];
            sum2 += native_sim_state_fd_50F6_06AE.signed_values[historyIndex];
            historyIndex = (historyIndex + 1) & 0x3f;
        }
        historyIndex = sum2 + sum;
        if (historyIndex > 0)
            scores[1] = (int32_t)sum * 100 / historyIndex;
        else
            scores[1] = 0;
    }

    if (native_state_fd_50F6_0FC2.signed_value > 0)
        scores[2] = (native_state_fd_50F6_0FC2.signed_value - native_state_fd_50F6_1000.signed_value) * 100 / native_state_fd_50F6_0FC2.signed_value;
    else
        scores[2] = 100;

    n = native_state_fd_50F6_09FA.signed_value + native_state_fd_50F6_0A00.signed_value;
    if (n > 0)
        scores[3] = native_state_fd_50F6_09FA.signed_value * 100 / n;
    else
        scores[3] = 100;

    if (fd_50F6_0EAC == 2 || fd_50F6_0EAC == 3) {
        n = native_state_fd_50F6_0AC4.signed_value + native_state_fd_50F6_0A90.signed_value;
        if (n > 0)
            scores[4] = (int32_t)native_state_fd_50F6_0A90.signed_value * 100 / n;
        else
            scores[4] = 100;
        n = native_state_fd_50F6_0A9E.signed_value + native_state_fd_50F6_0A90.signed_value;
        if (n > 0)
            scores[5] = (int32_t)native_state_fd_50F6_0A90.signed_value * 100 / n;
        else
            scores[5] = 100;

        sum = 0;
        for (j = 0; j < 16; j++)
            for (k = j < 5 ? 3 : 2; k < 12; k++)
                if (fd_3D57_00A4[k][j])
                    sum++;
        if (sum > 0)
            scores[6] = (int32_t)sum * 100 / 155;
        else
            scores[6] = 0;

        sum = 0;
        for (j = 0; j < 16; j++)
            for (k = 0; k < 2 || (j < 5 && k < 3); k++)
                if (fd_3D57_00A4[k][j])
                    sum++;
        if (sum > 0)
            scores[7] = (int32_t)sum * 100 / 37;
        else
            scores[7] = 0;
    }

    score = native_state_MeHealth.signed_value;
    for (k = 0; k < 8; k++)
        score += (int32_t)scores[k] * weights[k] * 51;

    if (fd_50F6_0EAC != 2) {
        score = score * 29 / 10;
        if (native_state_fd_50F6_0C26.signed_value < 4100) {
            q = native_state_fd_50F6_0C26.signed_value / 100;
            if (q <= 0)
                q = 1;
            score = q * score / 41;
        }
    } else {
        if (native_state_fd_50F6_0C26.signed_value < 8100) {
            q = native_state_fd_50F6_0C26.signed_value / 100;
            if (q <= 0)
                q = 1;
            score = q * score / 81;
        }
        score *= 5;
    }
    return native_state_fd_50F6_0C26.signed_value + score;
}
int main(void) {
    int16_t scores[8] = {0};
    native_state_fd_50F6_04F4.signed_value = 5;
    native_state_fd_50F6_0C26.signed_value = 5000;
    native_state_MeHealth.signed_value = 100;
    for (int i = 0; i < 4; ++i) {
        int k = (1 + i) & 63;
        native_sim_state_fd_50F6_073C.signed_values[k] = (int16_t)(10 * (i + 1));
        native_sim_state_fd_50F6_0626.signed_values[k] = (int16_t)(i + 1);
        native_sim_state_fd_50F6_06AE.signed_values[k] = (int16_t)(2 * (i + 1));
    }
    if (CalcScore(scores) <= 0 || scores[0] != 25 || scores[1] != 33) return 3;
    if (native_sim_state_fd_50F6_073C.raw_bytes[2] != 10 ||
        native_sim_state_fd_50F6_073C.raw_bytes[3] != 0) return 4;
    puts("PASS: original CalcScore reads the selected history/raw owners");
    return 0;
}
