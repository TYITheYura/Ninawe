import ctypes
from .. import MakeLog
from . import RECT
import win32con
import win32gui

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
            KickMaximizedWindows()
        else:
            MakeLog("[Log] [SetWorkArea]", "Unable to resize working area")

    except Exception as e:
        MakeLog("[Log] [SetWorkArea]", f"Error: {e}")

def KickMaximizedWindows():
    #
    #   Sends a request to recalculate the screen boundaries of open full-screen windows
    #
    def Callback(hwnd, ctx):
        if win32gui.IsWindowVisible(hwnd) and ctypes.windll.user32.IsZoomed(hwnd):
            try:
                win32gui.SetWindowPos(
                    hwnd, 0, 0, 0, 0, 0,
                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE |
                    win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED
                )
            except Exception:
                pass
        return True

    win32gui.EnumWindows(Callback, 0)
