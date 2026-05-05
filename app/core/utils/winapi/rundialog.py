import ctypes

def RunDialog():
    RunFileDlg = ctypes.windll.shell32[61]

    RunFileDlg.argtypes = [
        ctypes.c_void_p,    # HWND
        ctypes.c_void_p,    # HICON
        ctypes.c_wchar_p,   # Work dir
        ctypes.c_wchar_p,   # Window name
        ctypes.c_wchar_p,   # Description text
        ctypes.c_uint32     # Flags
    ]

    ctypes.windll.user32.AllowSetForegroundWindow(-1)

    RunFileDlg(0, 0, None, None, None, 0)
