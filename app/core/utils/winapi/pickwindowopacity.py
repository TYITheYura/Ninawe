import ctypes
import win32gui
import win32con
from .. import MakeLogExtra

def PickWindowOpacityMain(hwnd, setZeroAlpha):
    #
    #   Makes window transparent (1) or remove transperent (100), depending on the given setZeroAlpha.
    #   Returns True if state was changed, False otherwise.
    #
    exStyle = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)

    if setZeroAlpha:
        if not (exStyle & win32con.WS_EX_LAYERED):
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, exStyle | win32con.WS_EX_LAYERED)

        ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0, 1, win32con.LWA_ALPHA)

        win32gui.SetWindowPos(
            hwnd, 0, 0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE |
            win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED | win32con.SWP_NOACTIVATE
        )
        return True

    else:
        if exStyle & win32con.WS_EX_LAYERED:
            newStyle = exStyle & ~win32con.WS_EX_LAYERED
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, newStyle)

            win32gui.SetWindowPos(
                hwnd, 0, 0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE |
                win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED | win32con.SWP_NOACTIVATE
            )
            return True
        return False

def PickWindowOpacity(hwnd, setZeroAlpha):
    #
    #   Wrapper
    #
    try:
        return PickWindowOpacityMain(hwnd, setZeroAlpha)
    except Exception:
        from core.workers import CallInPipe
        try:
            CallInPipe("winapi", "PickWindowOpacityMain", hwnd, setZeroAlpha)
            return True
        except Exception as e:
            MakeLogExtra("[Log] [PickWindowOpacityPipe]", f"Error: {e}")
            return False
