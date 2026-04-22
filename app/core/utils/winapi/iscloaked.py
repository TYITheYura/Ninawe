import ctypes
from .consts import DWMWA_CLOAKED

def IsWindowCloaked(hwnd):
    #
    #   Asks Desktop Window Manager if the window is hidden by the system "cloak" (useful for UWP apps, who's not working without shell lol)
    #
    cloaked = ctypes.c_int(0)
    try:
        result = ctypes.windll.dwmapi.DwmGetWindowAttribute(
            hwnd,
            DWMWA_CLOAKED,
            ctypes.byref(cloaked),
            ctypes.sizeof(cloaked)
        )
        if result == 0:
            return cloaked.value != 0
    except Exception:
        pass
    return False
