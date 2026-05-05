from PyQt6.QtGui import QFontDatabase
from . import MakeLog
import os

def LoadFont(fontFromConfig, path=""):
    fontStr = str(fontFromConfig)
    if fontStr.lower().endswith((".ttf", ".otf")):
        if os.path.isabs(fontStr):
            fontFullPath = fontStr
        else:
            fontFullPath = os.path.join(path, fontStr)
        if os.path.exists(fontFullPath):
            fontID = QFontDatabase.addApplicationFont(fontFullPath)
            if fontID != -1:
                families = QFontDatabase.applicationFontFamilies(fontID)
                if families:
                    return families[0]
            else:
                MakeLog("[Log] [FontLoader]", f"Could not load font from file: {fontFullPath}")
        else:
            MakeLog("[Log] [FontLoader]", f"Font file not found: {fontFullPath}")
    return fontStr

def GetRealTargetPath(filepath):
    if filepath.lower().endswith('.lnk'):
        try:
            from . import WSHELL
            shortcut = WSHELL.CreateShortCut(filepath)
            target = shortcut.Targetpath
            if target and os.path.exists(target):
                return target
        except Exception as e:
            MakeLog("[Log] [GetRealTargetPath]", f"Failed to resolve shortcut {filepath}: {e}")
    return filepath
