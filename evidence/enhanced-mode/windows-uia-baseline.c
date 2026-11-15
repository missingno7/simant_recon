/* Independent authored Win32 control, with no game/toolkit/layout dependency.
 * Compile with MinGW gcc FILE -lole32 -o OUTPUT. Query UIA while it runs.
 * Development observation: the stock Button was returned as ControlType.Pane,
 * just like workspace controls. This diagnoses a local provider/proxy limit;
 * it is not a waiver of the workspace accessibility requirement. */
#include <windows.h>
int main(void) {
    CoInitializeEx(NULL,COINIT_APARTMENTTHREADED);
    HWND root=CreateWindowExA(0,"STATIC","UIA standard control baseline",
        WS_OVERLAPPEDWINDOW|WS_VISIBLE,200,100,400,300,NULL,NULL,GetModuleHandle(NULL),NULL);
    CreateWindowExA(0,"BUTTON","Accessible button",WS_CHILD|WS_VISIBLE|WS_TABSTOP,
        10,10,180,40,root,NULL,GetModuleHandle(NULL),NULL);
    ULONGLONG end=GetTickCount64()+15000;
    while(GetTickCount64()<end) {
        MSG message;while(PeekMessage(&message,NULL,0,0,PM_REMOVE)) {
            TranslateMessage(&message);DispatchMessage(&message);
        }
        Sleep(10);
    }
    DestroyWindow(root);CoUninitialize();return 0;
}
