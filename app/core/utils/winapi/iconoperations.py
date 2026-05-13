import ctypes
import ctypes.wintypes as wintypes
import win32gui
import win32ui
import win32con
import win32process
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
import os
from .. import MakeLog
from .consts import SHGFI_ICON, SHGFI_LARGEICON

class SHFILEINFO(ctypes.Structure):
    _fields_ = [
        ("hIcon", wintypes.HICON),
        ("iIcon", ctypes.c_int),
        ("dwAttributes", wintypes.DWORD),
        ("szDisplayName", wintypes.WCHAR * 260),
        ("szTypeName", wintypes.WCHAR * 80)
    ]

def IsPixmapEmpty(pixmap):
    #
    #   Checks if pixmap is empty. True if yes, otherwise False
    #
    if not pixmap or pixmap.isNull():
        return True

    image = pixmap.toImage().convertToFormat(QImage.Format.Format_ARGB32)

    pointer = image.constBits()
    pointer.setsize(image.sizeInBytes())
    data = bytes(pointer)

    if not data:
        return True

    alphaChannel = data[3::4]

    if max(alphaChannel) == 0:
        return True

    return False

def HiconToPixmap(hicon):
    #
    #   Converts the passed hicon into a pixmap
    #
    if not hicon:
        return None

    hdc = None
    hbmp = None
    hdcScreen = None
    hdcMemory = None

    try:
        hdcScreen = win32gui.GetDC(0)
        hdc = win32ui.CreateDCFromHandle(hdcScreen)
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(hdc, 32, 32)

        hdcMemory = hdc.CreateCompatibleDC()
        hdcMemory.SelectObject(hbmp)
        hdcMemory.DrawIcon((0, 0), hicon)

        bmpinfo = hbmp.GetInfo()
        bmpstr = hbmp.GetBitmapBits(True)
        image = QImage(bmpstr, bmpinfo['bmWidth'], bmpinfo['bmHeight'], QImage.Format.Format_ARGB32)

        return QPixmap.fromImage(image)
    except Exception as e:
        MakeLog("[Log] [HiconToPixmap]", f"HiconToPixmap error: {e}")
        return None
    finally:
        if hbmp:
            try:
                win32gui.DeleteObject(hbmp.GetHandle())
            except Exception:
                pass

        if hdcMemory:
            try:
                hdcMemory.DeleteDC()
            except Exception:
                pass

        if hdc:
            try:
                hdc.DeleteDC()
            except Exception:
                pass

        if hdcScreen:
            try:
                win32gui.ReleaseDC(0, hdcScreen)
            except Exception:
                pass

def GetWindowIcon(hwnd, iconType = None):
    #
    #   Tries to get an icon from a window
    #   Returns window icon
    #

    # Switch to a UWP window if one exists
    try:
        if win32gui.GetClassName(hwnd) == "ApplicationFrameWindow":
            realHWND = [0]

            def EnumChild(childHWND, ctx):
                if win32gui.GetClassName(childHWND) == "Windows.UI.Core.CoreWindow":
                    realHWND[0] = childHWND
                return True

            win32gui.EnumChildWindows(hwnd, EnumChild, None)

            if realHWND[0]:
                hwnd = realHWND[0]
    except Exception:
        pass

    # Icon from window
    hicon = 0
    try:
        if iconType == "SMALL":
            hicon = win32gui.SendMessageTimeout(hwnd, win32con.WM_GETICON, win32con.ICON_SMALL, 0, win32con.SMTO_ABORTIFHUNG, 50)[1]
        else:
            hicon = win32gui.SendMessageTimeout(hwnd, win32con.WM_GETICON, win32con.ICON_SMALL2, 0, win32con.SMTO_ABORTIFHUNG, 50)[1]

        if not hicon:
            hicon = win32gui.GetClassLong(hwnd, win32con.GCL_HICONSM)
    except Exception:
        pass

    if hicon:
        pixmap = HiconToPixmap(hicon)
        if pixmap and not IsPixmapEmpty(pixmap):
            return pixmap

    # Icon from class
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        handle = ctypes.windll.kernel32.OpenProcess(win32con.PROCESS_QUERY_LIMITED_INFORMATION, False, pid)

        if handle:
            buffer = ctypes.create_unicode_buffer(260)
            size = wintypes.DWORD(260)

            if ctypes.windll.kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
                shfi = SHFILEINFO()
                if ctypes.windll.shell32.SHGetFileInfoW(buffer.value, 0, ctypes.byref(shfi), ctypes.sizeof(shfi), SHGFI_ICON | SHGFI_LARGEICON):
                    pixmap = HiconToPixmap(shfi.hIcon)
                    win32gui.DestroyIcon(shfi.hIcon)

                    if pixmap and not IsPixmapEmpty(pixmap):
                        ctypes.windll.kernel32.CloseHandle(handle)
                        return pixmap

            ctypes.windll.kernel32.CloseHandle(handle)
    except Exception:
        pass

    try:
        hiconDefault = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
        return HiconToPixmap(hiconDefault)
    except Exception:
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        return pixmap

def GetIconFromFile(filepath):
    #
    #   Extracts an icon directly from an .exe or .lnk file
    #   Returns file icon
    #
    targetPath = filepath
    if filepath.lower().endswith('.lnk'):
        try:
            from core.utils import WSHELL
            shortcut = WSHELL.CreateShortCut(filepath)
            if shortcut.Targetpath and os.path.exists(shortcut.Targetpath):
                targetPath = shortcut.Targetpath
        except Exception:
            pass

    try:
        shfi = SHFILEINFO()
        if ctypes.windll.shell32.SHGetFileInfoW(targetPath, 0, ctypes.byref(shfi), ctypes.sizeof(shfi), SHGFI_ICON | SHGFI_LARGEICON):
            pixmap = HiconToPixmap(shfi.hIcon)
            win32gui.DestroyIcon(shfi.hIcon)
            if pixmap and not IsPixmapEmpty(pixmap):
                return pixmap
    except Exception as e:
        MakeLog("[Log] [GetIconFromFile]", f"GetIconFromFile error: {e}")

    # Fallback to empty
    empty = QPixmap(32, 32)
    empty.fill(Qt.GlobalColor.transparent)
    return empty
