import win32gui
import win32api
import win32process
from .. import MakeLogExtra

def ToggleWindow(hwnd, targetX = -1, targetY = -1, normalize = False):
    #
    #   If the window is minimized, it expands; if it is maximized, it collapses (fascinating)
    #   "normalize" subtracts the error that is created when minimizing/maximizing a window to/from a point
    #
    #   P.S. Standard minimized window size: 146x28
    #
    from core.workers import CallInPipe
    try:
        if win32gui.IsIconic(hwnd):
            if normalize:
                targetX -= 292
                targetY -= 14
            CallInPipe("winapi", "SetWindowState", hwnd, targetX, targetY, "RESTORE")
            CallInPipe("win32gui", "SetForegroundWindow", hwnd)
        else:
            if normalize:
                targetX -= 73
                targetY -= 14
            fgHWND = win32gui.GetForegroundWindow()
            if fgHWND == hwnd:
                CallInPipe("winapi", "SetWindowState", hwnd, targetX, targetY, "MINIMIZE")
            else:
                if fgHWND:
                    try:
                        currentThread = win32api.GetCurrentThreadId()
                        fgThread = win32process.GetWindowThreadProcessId(fgHWND)[0]
                        if currentThread != fgThread:
                            win32process.AttachThreadInput(currentThread, fgThread, True)
                            win32gui.SetForegroundWindow(hwnd)
                            win32process.AttachThreadInput(currentThread, fgThread, False)
                        else:
                            win32gui.SetForegroundWindow(hwnd)
                    except Exception:
                        win32gui.SetForegroundWindow(hwnd)
                else:
                    win32gui.SetForegroundWindow(hwnd)

    except Exception as e:
        MakeLogExtra("[Log] [ToggleWindow]", f"Error: {e}")
