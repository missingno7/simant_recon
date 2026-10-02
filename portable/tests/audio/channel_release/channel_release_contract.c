/* Native readable contract for root:m295C f_295C_02E8. Hardware is an event. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

enum { DEVICE_COUNT = 56, CHANNEL_CAP = 8 };
typedef struct { uint8_t type, num, c2, c3, c4, c5; } Channel;

static const char *backend_name(int kind)
{
    static const char *const names[8] = {
        "invalid", "f_290D_026C", "f_2815_024D", "f_29D6_0148", "f_29D6_015D",
        "f_29D6_0197", "f_295C_04FB", "f_295C_053D"
    };
    return kind >= 0 && kind < 8 ? names[kind] : "invalid";
}

static void release_note(const uint8_t kinds[DEVICE_COUNT], Channel *channels,
                         int dev, int note)
{
    int i;
    for (i = 0; channels[i].type != 0; ++i) {
        if (channels[i].c4 == note && channels[i].c3 == dev) {
            printf("backend|kind=%u|name=%s|note=%d|channel=%u|device=%d\n",
                   kinds[dev], backend_name(kinds[dev]), note, channels[i].num, dev);
            channels[i].c4 = 0;
            channels[i].c2 = 0;
            channels[i].c5 = 15;
        }
    }
}

static void run(int kind, int dev, int note, int channel_type, int channel_num)
{
    uint8_t kinds[DEVICE_COUNT] = {0};
    Channel channels[CHANNEL_CAP] = {0};
    int i;
    kinds[dev] = (uint8_t)kind;
    channels[0] = (Channel){(uint8_t)channel_type, (uint8_t)channel_num,
                            9, (uint8_t)dev, (uint8_t)note, 4};
    channels[1] = (Channel){(uint8_t)channel_type, (uint8_t)(channel_num+1),
                            0, (uint8_t)dev, (uint8_t)note, 5};
    channels[2] = (Channel){(uint8_t)channel_type, (uint8_t)(channel_num+2),
                            9, (uint8_t)(dev+1), (uint8_t)note, 6};
    channels[3] = (Channel){(uint8_t)channel_type, (uint8_t)(channel_num+3),
                            9, (uint8_t)dev, (uint8_t)(note+1), 7};
    channels[4].type = 0;
    release_note(kinds, channels, dev, note);
    puts("repeat");
    release_note(kinds, channels, dev, note);
    for (i = 0; i < 5; ++i)
        printf("channel|index=%d|bytes=%u,%u,%u,%u,%u,%u\n", i,
               channels[i].type, channels[i].num, channels[i].c2,
               channels[i].c3, channels[i].c4, channels[i].c5);
}

int main(int argc, char **argv)
{
    if (argc != 6) return 2;
    run(atoi(argv[1]), atoi(argv[2]), atoi(argv[3]), atoi(argv[4]), atoi(argv[5]));
    return 0;
}
