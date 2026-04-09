from PyQt6.QtGui import QFontDatabase
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
                print(f"[Log] [FontLoader] Could not load font from file: {fontFullPath}")
        else:
            print(f"[Log] [FontLoader] Font file not found: {fontFullPath}")
    return fontStr
