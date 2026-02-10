import ctypes
from ctypes import c_int, c_void_p, Structure, POINTER, sizeof, windll
from enum import Enum
from PyQt6.QtGui import QFontDatabase
import os

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

class AccentPolicy(Structure):
    _fields_ = [
        ("AccentState", c_int),
        ("AccentFlags", c_int),
        ("GradientColor", c_int),
        ("AnimationId", c_int)
    ]

class WindowCompositionAttributeData(Structure):
    _fields_ = [
        ("Attribute", c_int),
        ("Data", POINTER(AccentPolicy)),
        ("SizeOfData", c_int)
    ]

# ***info***
# hwnd - window ID (by default - int(self.winId()))
# enable - on/off blur (config file param)
# colorHEX - background color
# **********
def MakeBlur(hwnd: int, enable: bool = True, blurMode: int = AccentState.ACCENT_ENABLE_ACRYLICBLURBEHIND.value, colorHEX: str = "#00000000"):
    user32 = windll.user32
    SetWCA = user32.SetWindowCompositionAttribute
    SetWCA.argtypes = [c_void_p, POINTER(WindowCompositionAttributeData)]
    SetWCA.restype = c_int

    try:
        colorHEX = colorHEX.replace("#", "")
        if len(colorHEX) == 6: colorHEX = "FF" + colorHEX
        
        a = int(colorHEX[0:2], 16)
        r = int(colorHEX[2:4], 16)
        g = int(colorHEX[4:6], 16)
        b = int(colorHEX[6:8], 16)
        
        gradientColor = (a << 24) | (b << 16) | (g << 8) | r
    except:
        gradientColor = 0

    accent = AccentPolicy()
    data = WindowCompositionAttributeData()
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


# ==========[> Load fonts from file

def LoadFont(fontFromConfig):
    if str(fontFromConfig).lower().endswith((".ttf", ".otf")):
        if os.path.exists(fontFromConfig):
            fontID = QFontDatabase.addApplicationFont(fontFromConfig)
            if fontID != -1:
                families = QFontDatabase.applicationFontFamilies(fontID)
                if families:
                    return families[0]
            else:
                print(f"[Log] [FontLoader] Could not load font from file: {fontFromConfig}")
        else:
            print(f"[Log] [FontLoader] Font file not found: {fontFromConfig}")
    return fontFromConfig