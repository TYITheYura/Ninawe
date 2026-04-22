import win32gui
import win32process
import ctypes
import ctypes.wintypes as wintypes

def GetWindowGroupKey(hwnd):
    #
    #   Gets a unique identifier for grouping windows.
    #
    try:
        className = win32gui.GetClassName(hwnd)
        # UWP (ApplicationFrameWindow)
        if className == "ApplicationFrameWindow":
            innerHWND = [0]

            def EnumChild(c, ctx):
                if win32gui.GetClassName(c) == "Windows.UI.Core.CoreWindow":
                    innerHWND[0] = c
                return True
            win32gui.EnumChildWindows(hwnd, EnumChild, None)

            # PID of the inner window (the application itself)
            targetHWND = innerHWND[0] if innerHWND[0] else hwnd
            _, pid = win32process.GetWindowThreadProcessId(targetHWND)
        else:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)

        # Path to .exe via PID
        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if handle:
            buffer = ctypes.create_unicode_buffer(260)
            size = wintypes.DWORD(260)
            if ctypes.windll.kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
                exePath = buffer.value
                ctypes.windll.kernel32.CloseHandle(handle)
                return exePath.lower()
            ctypes.windll.kernel32.CloseHandle(handle)

    except Exception:
        pass

    # Fallback (group by window class name)
    return win32gui.GetClassName(hwnd)
