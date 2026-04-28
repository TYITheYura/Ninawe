import ctypes
from .. import MakeLog
from . import RECT
import win32con
import win32gui

class WorkAreaSetter:
    def __init__(self):
        from ui.desktop import WAConfig
        WAConfig.configUpdated.connect(self.SetWorkArea)
        self.SetWorkArea()

    def SetWorkArea(self):
        #
        #   Changes the size of the working area on the screen available to the user (desktop - taskbar)
        #   If taskbarHeight > 0, it cuts the bottom of the screen to fit your taskbar
        #   Else (0) - fullscreen
        #
        from ui.desktop import WAConfig
        try:
            rect = RECT()
            rect.top = WAConfig.workArea.top + WAConfig.taskbarMarginY
            rect.right = WAConfig.sw - WAConfig.workArea.right
            rect.bottom = WAConfig.sh - WAConfig.workArea.bottom
            rect.left = WAConfig.workArea.left

            result = ctypes.windll.user32.SystemParametersInfoW(
                win32con.SPI_SETWORKAREA,
                0,
                ctypes.byref(rect),
                win32con.SPIF_SENDCHANGE
            )

            if result:
                MakeLog("[Log] [SetWorkArea]", f"A new working area of {WAConfig.sw - rect.left + rect.right}x{WAConfig.sh - rect.top + rect.bottom} pixels has been set")
                self.KickMaximizedWindows()
            else:
                MakeLog("[Log] [SetWorkArea]", "Unable to resize working area")

        except Exception as e:
            MakeLog("[Log] [SetWorkArea]", f"Error: {e}")

    def KickMaximizedWindows(self):
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
