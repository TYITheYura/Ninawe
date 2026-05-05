import ctypes
from ctypes import Structure
from ctypes import wintypes
from PyQt6.QtGui import QImage
import os
from PyQt6.QtCore import QThread, pyqtSignal, QSemaphore
from core.utils.logger import MakeLog
from core.utils import SIIGBF_RESIZETOFIT

# queue (куеуе)))
GLOBAL_THUMBNAIL_SEMAPHORE = QSemaphore(1)

ole32 = ctypes.windll.ole32
shell32 = ctypes.windll.shell32
gdi32 = ctypes.windll.gdi32

class SIZE(Structure):
    _fields_ = [("cx", ctypes.c_long), ("cy", ctypes.c_long)]

class GUID(Structure):
    _fields_ = [
        ("Data1", ctypes.c_ulong), ("Data2", ctypes.c_ushort),
        ("Data3", ctypes.c_ushort), ("Data4", ctypes.c_ubyte * 8)
    ]

class BITMAP(Structure):
    _fields_ = [
        ("bmType", ctypes.c_long), ("bmWidth", ctypes.c_long),
        ("bmHeight", ctypes.c_long), ("bmWidthBytes", ctypes.c_long),
        ("bmPlanes", ctypes.c_short), ("bmBitsPixel", ctypes.c_short),
        ("bmBits", ctypes.c_void_p),
    ]

# Magic "mysterious" numbers (no joke)
IID_IShellItemImageFactory = GUID(0xBCC18B79, 0xBA16, 0x442F, (ctypes.c_ubyte * 8)(0x80, 0xC4, 0x8A, 0x59, 0xC3, 0x0C, 0x46, 0x3B))

shell32.SHCreateItemFromParsingName.argtypes = [
    ctypes.c_wchar_p,
    ctypes.c_void_p,
    ctypes.POINTER(GUID),
    ctypes.POINTER(ctypes.c_void_p)
]
shell32.SHCreateItemFromParsingName.restype = ctypes.c_long

def GetWindowsThumbnail(filepath, size = 256):
    filepath = os.path.normpath(filepath)
    if not os.path.exists(filepath):
        return None

    ole32.CoInitialize(None)

    pFactory = ctypes.c_void_p()
    hbitmap = wintypes.HBITMAP()

    try:
        res = shell32.SHCreateItemFromParsingName(
            filepath,
            None,
            ctypes.byref(IID_IShellItemImageFactory),
            ctypes.byref(pFactory)
        )

        if res != 0 or not pFactory:
            return None

        vtable = ctypes.cast(pFactory, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)))

        GetImage = ctypes.WINFUNCTYPE(
            ctypes.c_long, ctypes.c_void_p, SIZE, ctypes.c_int, ctypes.POINTER(wintypes.HBITMAP)
        )(vtable[0][3])

        Release = ctypes.WINFUNCTYPE(
            ctypes.c_ulong, ctypes.c_void_p
        )(vtable[0][2])

        sizeStruct = SIZE(size, size)

        res = GetImage(pFactory, sizeStruct, SIIGBF_RESIZETOFIT, ctypes.byref(hbitmap))
        Release(pFactory)

        if res != 0 or not hbitmap:
            return None

        bm = BITMAP()
        gdi32.GetObjectW(hbitmap, ctypes.sizeof(BITMAP), ctypes.byref(bm))

        buffer = ctypes.create_string_buffer(bm.bmWidthBytes * bm.bmHeight)
        gdi32.GetBitmapBits(hbitmap, len(buffer), buffer)

        image = QImage(buffer, bm.bmWidth, bm.bmHeight, bm.bmWidthBytes, QImage.Format.Format_ARGB32)
        image = image.copy()

        return image

    except Exception:
        return None
    finally:
        if hbitmap:
            try:
                gdi32.DeleteObject(hbitmap)
            except Exception:
                pass
        ole32.CoUninitialize()

class ThumbnailLoaderThread(QThread):
    loadedSignal = pyqtSignal(QImage)

    def __init__(self, filepath, size, parent = None):
        super().__init__(parent)
        self.filepath = filepath
        self.size = size

    def run(self):
        GLOBAL_THUMBNAIL_SEMAPHORE.acquire()
        try:
            image = GetWindowsThumbnail(self.filepath, self.size)
            if image and not image.isNull():
                self.loadedSignal.emit(image)
        except Exception as e:
            MakeLog("[Log] [Thumbnail]", f"Failed to load thumbnail for {self.filepath}: {e}")
        finally:
            GLOBAL_THUMBNAIL_SEMAPHORE.release()
