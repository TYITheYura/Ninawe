import win32gui
import win32con
import win32api

class DesktopToggler:
    def __init__(self):
        self.hiddenHWNDs = []

    def ToggleDesktop(self, ignoreHWNDs=None):
        from core.workers import CallInPipe

        if ignoreHWNDs is None:
            ignoreHWNDs = []

        visibleWindows = []

        win32gui.EnumWindows(self.CheckVisibleEnumHandler, (ignoreHWNDs, visibleWindows))

        if visibleWindows:
            self.hiddenHWNDs.clear()
            for hwnd in visibleWindows:
                self.hiddenHWNDs.append(hwnd)

                x, y = self.GetCenter(hwnd, "MINIMIZE")
                CallInPipe("winapi", "SetWindowState", hwnd, x, y, "MINIMIZE")

        else:
            if self.hiddenHWNDs:
                for hwnd in reversed(self.hiddenHWNDs):
                    if win32gui.IsWindow(hwnd):
                        x, y = self.GetCenter(hwnd, "RESTORE")
                        CallInPipe("winapi", "SetWindowState", hwnd, x, y, "RESTORE")
                self.hiddenHWNDs.clear()

    def CheckVisibleEnumHandler(self, hwnd, args):
        ignoreHWNDs, visibleWindows = args

        if hwnd in ignoreHWNDs:
            return True

        if not win32gui.IsWindowVisible(hwnd) or win32gui.IsIconic(hwnd):
            return True

        exStyle = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        if (exStyle & win32con.WS_EX_TOOLWINDOW) == win32con.WS_EX_TOOLWINDOW:
            return True

        className = win32gui.GetClassName(hwnd)
        forbiddenClasses = ["Progman", "WorkerW", "Windows.UI.Core.CoreWindow", "ApplicationFrameWindow"]
        title = win32gui.GetWindowText(hwnd)

        if className in forbiddenClasses and not title:
            return True
        if not title:
            return True

        visibleWindows.append(hwnd)

        return True

    def GetNearestCorner(self, hwnd):
        #
        #   Looks cool but i don't like visual bugs there, so i don't use this.
        #
        screenW = win32api.GetSystemMetrics(0)
        screenH = win32api.GetSystemMetrics(1)
        rect = win32gui.GetWindowRect(hwnd)

        centerX = (rect[0] + rect[2]) // 2
        centerY = (rect[1] + rect[3]) // 2

        MARGIN = 0

        if centerX < screenW // 2:
            targetX = MARGIN
        else:
            targetX = (screenW - MARGIN)

        if centerY < screenH // 2:
            targetY = MARGIN
        else:
            targetY = (screenH - MARGIN)

        return targetX, targetY

    def GetCenter(self, hwnd, pickedOffset = None):
        screenW = win32api.GetSystemMetrics(0)
        screenH = win32api.GetSystemMetrics(1)

        centerX = screenW // 2
        centerY = screenH // 2

        OFFSET_X = OFFSET_Y = 0

        # Don't ask me how I found these offsets. It was terrible.
        if pickedOffset == "MINIMIZE":
            OFFSET_X = -105
            OFFSET_Y = -81
        elif pickedOffset == "RESTORE":
            OFFSET_X = -292
            OFFSET_Y = -81

        targetX = centerX + OFFSET_X
        targetY = centerY + OFFSET_Y

        return targetX, targetY
