/* SOURCE_ONLY_DOS data owner candidate: closed scalar/pointer subfamily only.
 * UI resource arrays with unresolved caps are intentionally not defined here.
 */
typedef struct {
    unsigned int age;
    int file;
    int page;
} EmsSlot;

typedef char far * far *Handle;

int far win_numOfWindows;
int far win_numOfColors;
int far win_numOfGroups;
EmsSlot far * far * far fd_50F6_3B4C;
void (far * far fd_50F6_3B58)(char far *, char far *, int, int);
Handle far fd_50F6_3B5C;
