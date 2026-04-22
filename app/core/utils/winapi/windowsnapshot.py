import ctypes
import win32gui
import win32ui
from PyQt6.QtGui import QPixmap, QImage
from .rectstruct import RECT
from .consts import PW_RENDERFULLCONTENT, DWMWA_EXTENDED_FRAME_BOUNDS

LIVE_THUMBNAIL_CACHE = {}

def GetWindowSnapshot(hwnd):
    #
    #   Returns the window image
    #
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    width = right - left
    height = bottom - top

    if width <= 0 or height <= 0:
        return None

    frame = RECT()
    result = ctypes.windll.dwmapi.DwmGetWindowAttribute(hwnd, DWMWA_EXTENDED_FRAME_BOUNDS, ctypes.byref(frame), ctypes.sizeof(frame))

    if result == 0:
        cropLeft = frame.left - left
        cropTop = frame.top - top
        cropRight = right - frame.right
        cropBottom = bottom - frame.bottom
    else:
        cropLeft = cropTop = cropRight = cropBottom = 0

    hdcWindow = None
    hdcMemory = None
    hbmp = None

    try:
        hdcWindow = win32gui.GetWindowDC(hwnd)
        hdcMemory = win32ui.CreateDCFromHandle(hdcWindow).CreateCompatibleDC()
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(win32ui.CreateDCFromHandle(hdcWindow), width, height)
        hdcMemory.SelectObject(hbmp)

        result = ctypes.windll.user32.PrintWindow(hwnd, hdcMemory.GetSafeHdc(), PW_RENDERFULLCONTENT)

        if result == 1:
            bmpinfo = hbmp.GetInfo()
            bmpstr = hbmp.GetBitmapBits(True)
            image = QImage(bmpstr, bmpinfo['bmWidth'], bmpinfo['bmHeight'], QImage.Format.Format_ARGB32)
            pixmap = QPixmap.fromImage(image)

            if cropLeft > 0 or cropTop > 0 or cropRight > 0 or cropBottom > 0:
                cropW = width - cropLeft - cropRight
                cropH = height - cropTop - cropBottom
                if cropW > 0 and cropH > 0:
                    pixmap = pixmap.copy(cropLeft, cropTop, cropW, cropH)

            return pixmap
        return None
    except:
        pass
    finally:
        if hbmp:
            try:
                win32gui.DeleteObject(hbmp.GetHandle())
            except:
                pass
        if hdcMemory:
            try:
                hdcMemory.DeleteDC()
            except:
                pass
        if hdcWindow:
            try:
                win32gui.ReleaseDC(hwnd, hdcWindow)
            except:
                pass
