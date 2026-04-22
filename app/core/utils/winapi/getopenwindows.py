import win32gui
import win32con
from .getopenwindowgroupkey import GetWindowGroupKey
from .iscloaked import IsWindowCloaked

def GetOpenWindows():
    #
    #   Returns a grouped dictionary of open windows.
    #   example: {"path_to_exe_or_class_name": [{hwnd, title}, ...], ...}
    #
    groupedWindows = {}

    def EnumHandler(hwnd, ctx):
        if win32gui.IsWindowVisible(hwnd) and not IsWindowCloaked(hwnd):
            title = win32gui.GetWindowText(hwnd)
            exStyle = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)

            if (exStyle & win32con.WS_EX_TOOLWINDOW) == 0:
                if title and title not in ["Program Manager", "Microsoft Text Input Application"]:
                    groupKey = GetWindowGroupKey(hwnd)
                    if groupKey not in groupedWindows:
                        groupedWindows[groupKey] = []
                    groupedWindows[groupKey].append({"hwnd": hwnd, "title": title})

    win32gui.EnumWindows(EnumHandler, None)
    return groupedWindows
