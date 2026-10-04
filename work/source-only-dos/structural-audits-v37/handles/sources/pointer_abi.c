typedef char far *WindowData;
typedef WindowData far *WindowHandle;
struct PointerABI {
 unsigned near_outer,far_outer,handle,window_data;
};
struct PointerABI probe = {sizeof(WindowHandle near *),sizeof(WindowHandle far *),sizeof(WindowHandle),sizeof(WindowData)};
