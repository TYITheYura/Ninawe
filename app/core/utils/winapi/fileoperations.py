import ctypes
import ctypes.wintypes as wintypes

class SHFILEOPSTRUCTW(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("wFunc", wintypes.UINT),
        ("pFrom", wintypes.LPCWSTR),
        ("pTo", wintypes.LPCWSTR),
        ("fFlags", wintypes.WORD),
        ("fAnyOperationsAborted", wintypes.BOOL),
        ("hNameMappings", wintypes.LPVOID),
        ("lpszProgressTitle", wintypes.LPCWSTR)
    ]

def WindowsFileOperation(hwnd, operation, sourcePaths, destDir, flags = 0):
    #
    #   Calls copy/move operations, etc. (depending on the passed operation) for the passed paths
    #
    pFromStr = '\0'.join(sourcePaths) + '\0\0'
    pToStr = destDir + '\0\0' if destDir else None

    pFromBuffer = ctypes.create_unicode_buffer(pFromStr)
    pToBuffer = ctypes.create_unicode_buffer(pToStr) if pToStr else None

    fo = SHFILEOPSTRUCTW()
    fo.hwnd = hwnd
    fo.wFunc = operation
    fo.pFrom = ctypes.cast(pFromBuffer, wintypes.LPCWSTR)
    fo.pTo = ctypes.cast(pToBuffer, wintypes.LPCWSTR) if pToBuffer else None
    fo.fFlags = flags

    result = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(fo))

    return result == 0 and not fo.fAnyOperationsAborted
