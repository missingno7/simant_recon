/* Functional FAR_BSS owner for the supported VGA spider composition buffer. */
typedef struct Point {
    int x;
    int y;
} Point;

typedef struct SpiderImage {
    Point dimensions;
    unsigned char pixels[6272];
} SpiderImage;

SpiderImage far fd_50F6_1F26;
