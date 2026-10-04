NULL segment word public 'BEGDATA'
db 0
NULL ends
PREFIX segment word public 'DATA'
public FrameMarker, LiteralMarker
db 0AEh dup (?)
FrameMarker db 0C7h
db 8ED7h dup (?)
LiteralMarker db 0A5h
PREFIX ends
_DATA segment para public 'DATA'
public _g_8ED8, _g_8EC0
_g_8ED8 label byte
db 4 dup (?)
_g_8EC0 label byte
db 0FCh dup (?)
db 35h
db 3 dup (?)
db 0D3h
_DATA ends
DGROUP group NULL, PREFIX, _DATA
end
