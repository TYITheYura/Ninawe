import ctypes
from ctypes import Structure, POINTER, sizeof, windll
import ctypes.wintypes as wintypes
from enum import Enum

# ==========[> Blur

class WindowCompositionAttribute(Enum):
    WCA_ACCENT_POLICY = 19

class AccentState(Enum):
    ACCENT_DISABLED = 0
    ACCENT_ENABLE_GRADIENT = 1
    ACCENT_ENABLE_TRANSPARENTGRADIENT = 2
    ACCENT_ENABLE_BLURBEHIND = 3
    ACCENT_ENABLE_ACRYLICBLURBEHIND = 4
    ACCENT_INVALID_STATE = 5

class ACCENTPOLICY(Structure):
    _fields_ = [
        ("AccentState", ctypes.c_int),
        ("AccentFlags", ctypes.c_int),
        ("GradientColor", ctypes.c_int),
        ("AnimationId", ctypes.c_int)
    ]

class WINDOWCOMPOSITIONATTRIBDATA(Structure):
    _fields_ = [
        ("Attribute", ctypes.c_int),
        ("Data", POINTER(ACCENTPOLICY)),
        ("SizeOfData", ctypes.c_int)
    ]

# ***info***
# hwnd - window ID (by default - int(self.winId()))
# enable - on/off blur (config file param)
# colorHEX - background color
# **********
def MakeBlur(hwnd: int, enable: bool = True, blurMode: int = AccentState.ACCENT_ENABLE_ACRYLICBLURBEHIND.value, colorHEX: str = "#00000000"):
    user32 = windll.user32
    SetWCA = user32.SetWindowCompositionAttribute
    SetWCA.argtypes = [ctypes.c_void_p, POINTER(WINDOWCOMPOSITIONATTRIBDATA)]
    SetWCA.restype = ctypes.c_int

    try:
        colorHEX = colorHEX.replace("#", "")
        if len(colorHEX) == 6:
            colorHEX = "FF" + colorHEX

        a = int(colorHEX[0:2], 16)
        r = int(colorHEX[2:4], 16)
        g = int(colorHEX[4:6], 16)
        b = int(colorHEX[6:8], 16)

        gradientColor = (a << 24) | (b << 16) | (g << 8) | r
    except:
        gradientColor = 0

    accent = ACCENTPOLICY()
    data = WINDOWCOMPOSITIONATTRIBDATA()
    data.Attribute = WindowCompositionAttribute.WCA_ACCENT_POLICY.value
    data.Data = ctypes.pointer(accent)
    data.SizeOfData = sizeof(accent)

    # "restart" or disable blur, context required
    accent.AccentState = AccentState.ACCENT_DISABLED.value
    accent.GradientColor = 0
    accent.AccentFlags = 0

    SetWCA(int(hwnd), ctypes.pointer(data))

    if enable:
        blurMode = AccentState.ACCENT_ENABLE_ACRYLICBLURBEHIND.value if blurMode == 1 else AccentState.ACCENT_ENABLE_BLURBEHIND.value
        accent.AccentState = blurMode
        accent.GradientColor = gradientColor
        accent.AccentFlags = 1

        SetWCA(int(hwnd), ctypes.pointer(data))

# ==========[> File properties window maker 4000

# very necessary constants (no joke)
SEE_MASK_INVOKEIDLIST = 0x0000000C

class SHELLEXECUTEINFO(Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("fMask", ctypes.c_ulong),
        ("hwnd", wintypes.HWND),
        ("lpVerb", ctypes.c_wchar_p),
        ("lpFile", ctypes.c_wchar_p),
        ("lpParameters", ctypes.c_wchar_p),
        ("lpDirectory", ctypes.c_wchar_p),
        ("nShow", ctypes.c_int),
        ("hInstApp", wintypes.HINSTANCE),
        ("lpIDList", ctypes.c_void_p),
        ("lpClass", ctypes.c_wchar_p),
        ("hkeyClass", wintypes.HKEY),
        ("dwHotKey", wintypes.DWORD),
        ("hIcon", wintypes.HANDLE),
        ("hProcess", wintypes.HANDLE)
    ]

# ==========[> File deleter/mover/copyer/f#cker 5000

# very necessary constants (no joke)
FO_MOVE = 0x0001
FO_COPY = 0x0002
FO_DELETE = 0x0003
FO_RENAME = 0x0004
FOF_ALLOWUNDO = 0x0040
FOF_NOCONFIRMATION = 0x0010

class SHFILEOPSTRUCTW(Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("wFunc", wintypes.UINT),
        ("pFrom", wintypes.LPCWSTR),
        ("pTo", wintypes.LPCWSTR),
        ("fFlags", wintypes.WORD),
        ("fAnyOperationsAborted", wintypes.BOOL),
        ("hNameMappings", wintypes.LPVOID),
        ("lpszProgressTitle", wintypes.LPCWSTR)
    ]

def WindowsFileOperation(hwnd, operation, sourcePaths, destDir, flags = 0):
    pFromStr = '\0'.join(sourcePaths) + '\0\0'
    pToStr = destDir + '\0\0' if destDir else None

    pFromBuffer = ctypes.create_unicode_buffer(pFromStr)
    pToBuffer = ctypes.create_unicode_buffer(pToStr) if pToStr else None

    fo = SHFILEOPSTRUCTW()
    fo.hwnd = hwnd
    fo.wFunc = operation
    fo.pFrom = ctypes.cast(pFromBuffer, wintypes.LPCWSTR)
    fo.pTo = ctypes.cast(pToBuffer, wintypes.LPCWSTR) if pToBuffer else None
    fo.fFlags = flags

    result = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(fo))

    return result == 0 and not fo.fAnyOperationsAborted

# ==========[> Bin. Just a bin.

class SHQUERYRBINFO(Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint32),
        ("i64Size", ctypes.c_int64),
        ("i64NumItems", ctypes.c_int64),
    ]

def IsRecycleBinEmpty():
    try:
        info = SHQUERYRBINFO()
        info.cbSize = ctypes.sizeof(info)
        res = ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(info))
        if res == 0:
            return info.i64NumItems == 0
        return True
    except Exception:
        return True
