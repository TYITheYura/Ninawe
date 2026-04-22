import win32gui
import win32con
from .. import MakeLogExtra

def SetWindowState(hwnd, targetX, targetY, action = "MINIMIZE"):
    #
    #   Used to minimize a window to the specified coordinates, or restore a window from the specified coordinates
    #   In fact, bypassing the AppBar functionality so as not to use it in the shell :)
    #
    try:
        if action == "MINIMIZE":
            # 1-pixel jiggle because of DWM cache
            rect = win32gui.GetWindowRect(hwnd)
            x, y = rect[0], rect[1]

            win32gui.SetWindowPos(
                hwnd, 0, x + 1, y, 0, 0,
                win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE
            )

            win32gui.SetWindowPos(
                hwnd, 0, x, y, 0, 0,
                win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE | win32con.SWP_FRAMECHANGED
            )

            flags, showCMD, ptMin, ptMax, rcNormal = win32gui.GetWindowPlacement(hwnd)

            cleanFlags = (flags & win32con.WPF_RESTORETOMAXIMIZED) | win32con.WPF_SETMINPOSITION
            newPlacement = (cleanFlags, showCMD, (int(targetX - 80), int(targetY - 12)), ptMax, rcNormal)

            win32gui.SetWindowPlacement(hwnd, newPlacement)
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)

        elif action == "RESTORE":
            flags, showCMD, ptMin, ptMax, rcNormal = win32gui.GetWindowPlacement(hwnd)

            cleanFlags = (flags & win32con.WPF_RESTORETOMAXIMIZED) | win32con.WPF_SETMINPOSITION
            newPlacement = (cleanFlags, showCMD, (int(targetX - 320), int(targetY - 12)), ptMax, rcNormal)

            win32gui.SetWindowPlacement(hwnd, newPlacement)
            win32gui.PostMessage(hwnd, win32con.WM_SYSCOMMAND, win32con.SC_RESTORE, 0)

    except Exception as e:
        MakeLogExtra("[Log] [SetWindowState]", f"Error: {e}")
        pass
