void  win_YardClosed(void)
{
    if (native_game_fd_50F6_10DA) {
        clip_Push();
        clip_SetWin(0x1900);
        hanim_RemoveAllAnimObjects(native_game_fd_50F6_10DA);
        hanim_RenderAnimSet(native_game_fd_50F6_10DA);
        hanim_RemoveAnimSet(native_game_fd_50F6_10DA);
        clip_Pop();
        native_game_fd_50F6_10DA = 0;
    }
    if (win_IsWinOpen(0x1902)) {
        win_GetObjRect(0x1902, &(*((struct Rect *)native_game_fd_50F6_10D2.raw)));
        (*((struct Rect *)native_game_fd_50F6_10D2.raw)).left++;
        EraseYardCursor();
    }
}
void  f_0250_5058(void)
{
    struct Rect rects[3];

    win_GetObjRect(0x15, &(*((struct Rect *)native_game_fd_50F6_1104.raw)));
    rects[0] = (*((struct Rect *)native_game_fd_50F6_110C.raw));
    rects[1] = (*((struct Rect *)native_game_fd_50F6_1104.raw));
    rects[2].top = 0x8000;
    f_1E57_08F5(rects);
}