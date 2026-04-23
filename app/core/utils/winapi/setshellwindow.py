import ctypes
from .. import MakeLog

def SetShellWindow(hwnd):
    #
    #   Registers the window as the main Windows desktop.
    #
    try:
        user32 = ctypes.windll.user32
        currentShell = user32.GetShellWindow()

        if currentShell != 0:
            MakeLog("[Log] [SetShellWindow]", f"The shell is busy with another window. HWND: {currentShell}")
            return False

        result = user32.SetShellWindow(int(hwnd))

        if result:
            MakeLog("[Log] [SetShellWindow]", "Ninawe Desktop is registered in the system as a shell")
            return True
        else:
            MakeLog("[Log] [SetShellWindow]", f"Access denied: {ctypes.GetLastError()}")
            return False

    except Exception as e:
        MakeLog("[Log] [SetShellWindow]", f"SetShellWindow Error: {e}")
        return False
