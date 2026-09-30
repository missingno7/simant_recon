typedef struct { int kind; int id; } Entry;
extern int far g_count;
extern Entry far * far g_ptr;
extern int far f(int a, int b);
extern void far h(int x);

int far target(int a, int b)
{
    int i;
    int t;
    int u;

    t = a + b;
    if (a < 3 || b == 0)
        return 0;
    if (a > 5 && b != 2) {
        h(t);
    } else
        h(b);
    u = t = f(a, b);
    h(u);
    for (i = 0; i < b; i++)
        h(i);
    i = a ? 1 : 2;
    g_count = g_count + 1;
    if (!a)
        return b;
    return t;
}
