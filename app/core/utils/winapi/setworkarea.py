import ctypes
from .. import MakeLog
from . import RECT
import win32con

def SetWorkArea(screenWidth, screenHeight, taskbarHeight = 0):
    #
    #   Changes the size of the working area on the screen available to the user (desktop - taskbar)
    #   If taskbarHeight > 0, it cuts the bottom of the screen to fit your taskbar
    #   Else (0) - fullscreen
    #
    try:
        rect = RECT()
        rect.left = 25
        rect.top = 75
        rect.right = screenWidth - 25
        rect.bottom = screenHeight - 50

        result = ctypes.windll.user32.SystemParametersInfoW(
            win32con.SPI_SETWORKAREA,
            0,
            ctypes.byref(rect),
            win32con.SPIF_SENDCHANGE
        )

        if result:
            MakeLog("[Log] [SetWorkArea]", f"A new working area of {rect.bottom} pixels has been set")
        else:
            MakeLog("[Log] [SetWorkArea]", "Unable to resize working area")

    except Exception as e:
        MakeLog("[Log] [SetWorkArea]", f"Error: {e}")
