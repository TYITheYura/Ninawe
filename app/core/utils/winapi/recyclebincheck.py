import ctypes

class SHQUERYRBINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint32),
        ("i64Size", ctypes.c_int64),
        ("i64NumItems", ctypes.c_int64),
    ]

def IsRecycleBinEmpty():
    #
    #   Checks if recycle bin is empty. Returns False if no, otherwise True
    #
    try:
        info = SHQUERYRBINFO()
        info.cbSize = ctypes.sizeof(info)
        result = ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(info))
        if result == 0:
            return info.i64NumItems == 0
        return True
    except Exception:
        return True
