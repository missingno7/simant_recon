void  f_1E57_0009(void)
{
    if (g_5742) {
        f_171C_1C0A(g_5742);
        g_5742 = 0;
    }
    if (g_5746)
        g_5746 = 0;
    g_5AAC = 0;
}

void  clip_Push(void)
{
    struct Rect  *p;
    int16_t size;
    Handle h;
    Handle  *node;

    size = 0;
    if ((p = g_5AAC) != 0) {
        for (; p->top != (int16_t)0x8000; p++)
            ;
        size = (char  *)p - (char  *)g_5AAC + sizeof(struct Rect);
        g_5758 += size / (int16_t)sizeof(struct Rect);
    }
    if (!(h = f_171C_1A9E(size + (int32_t)(2 * sizeof(Handle)), 1, "clip_Push")))
        Punt("Cannot allocate memory in clip_Push");
    node = (Handle  *)f_171C_1B84(h);
    if (size)
        _fmemcpy(node + 2, g_5AAC, size);
    node[0] = fd_50F6_3B5C;
    ((struct Rect  *  *)node)[1] = g_5AAC;
    fd_50F6_3B5C = h;
    if (++g_5756 > 20)
        Punt("Error CL98463: Pushed it too far");
    f_171C_1BBA(h);
}

void  clip_Pop(void)
{
    Handle  *node;
    struct Rect  *p;
    int16_t size;

    if (!g_5756)
        Punt("Clip_Pop w/ nothing on the stack: E9073");
    f_1E57_0009();
    g_5742 = fd_50F6_3B5C;
    node = (Handle  *)f_171C_1B84(g_5742);
    fd_50F6_3B5C = node[0];
    if (!((struct Rect  *  *)node)[1])
        g_5AAC = 0;
    else if ((p = g_5AAC = (struct Rect  *)(node + 2)) != 0) {
        for (; p->top != (int16_t)0x8000; p++)
            ;
        size = (char  *)p - (char  *)g_5AAC + sizeof(struct Rect);
        _fmemcpy(fd_50F6_3C14, g_5AAC, size);
        g_5AAC = fd_50F6_3C14;
    }
    g_5756--;
    f_171C_1BBA(g_5742);
}