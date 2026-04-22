import ctypes
import ctypes.wintypes as wintypes
import win32con
from .. import MakeLog

class ANIMATIONINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("iMinAnimate", ctypes.c_int)  # 0 = off, 1 = on
    ]

def SetGlobalAnimations(enable = False):
    #
    #   Turns on or off system animations for minimizing windows
    #
    try:
        info = ANIMATIONINFO()
        info.cbSize = ctypes.sizeof(ANIMATIONINFO)

        ctypes.windll.user32.SystemParametersInfoW(
            win32con.SPI_GETANIMATION, info.cbSize, ctypes.byref(info), 0
        )

        info.iMinAnimate = 1 if enable else 0

        result = ctypes.windll.user32.SystemParametersInfoW(
            win32con.SPI_SETANIMATION, info.cbSize, ctypes.byref(info), win32con.SPIF_SENDCHANGE
        )

        status = "turned on" if enable else "turned off"

        if result:
            MakeLog("[Log] [WinAPI.SetWindowAnimations]", f"Minimizing animations is {status}")
            pass
        else:
            MakeLog("[Log] [WinAPI.SetWindowAnimations]", "Failed to change animation settings")
            pass

    except Exception as e:
        MakeLog("[Log] [WinAPI.SetWindowAnimations]", f"Error: {e}")
        pass
