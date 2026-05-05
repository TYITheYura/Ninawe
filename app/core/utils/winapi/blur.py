import ctypes
from enum import Enum

class WindowCompositionAttribute(Enum):
    WCA_ACCENT_POLICY = 19

class AccentState(Enum):
    ACCENT_DISABLED = 0
    ACCENT_ENABLE_GRADIENT = 1
    ACCENT_ENABLE_TRANSPARENTGRADIENT = 2
    ACCENT_ENABLE_BLURBEHIND = 3
    ACCENT_ENABLE_ACRYLICBLURBEHIND = 4
    ACCENT_INVALID_STATE = 5

class ACCENTPOLICY(ctypes.Structure):
    _fields_ = [
        ("AccentState", ctypes.c_int),
        ("AccentFlags", ctypes.c_int),
        ("GradientColor", ctypes.c_int),
        ("AnimationId", ctypes.c_int)
    ]

class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
    _fields_ = [
        ("Attribute", ctypes.c_int),
        ("Data", ctypes.POINTER(ACCENTPOLICY)),
        ("SizeOfData", ctypes.c_int)
    ]

def MakeBlur(hwnd: int, enable: bool = True, blurMode: int = AccentState.ACCENT_ENABLE_ACRYLICBLURBEHIND.value, colorHEX: str = "#00000000"):
    #
    #   Creates a blur effect on the specified window.
    #   hwnd - window ID (by default - int(self.winId()))
    #   enable - on/off blur (config file param)
    #   colorHEX - background color
    #
    user32 = ctypes.windll.user32
    SetWCA = user32.SetWindowCompositionAttribute
    SetWCA.argtypes = [ctypes.c_void_p, ctypes.POINTER(WINDOWCOMPOSITIONATTRIBDATA)]
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
    except Exception:
        gradientColor = 0

    accent = ACCENTPOLICY()
    data = WINDOWCOMPOSITIONATTRIBDATA()
    data.Attribute = WindowCompositionAttribute.WCA_ACCENT_POLICY.value
    data.Data = ctypes.pointer(accent)
    data.SizeOfData = ctypes.sizeof(accent)

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
