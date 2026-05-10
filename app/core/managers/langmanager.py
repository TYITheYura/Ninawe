import os
import configparser
from core.config import ConfigWrapper, BASE_DIR
from core.utils import MakeLog

class LangManager(ConfigWrapper):
    def __init__(self, appСonfig):
        super().__init__()
        self.app = appСonfig
        self.currentLang = self.app.Get("App", "language", fallback = "uk")
        self.Load(self.currentLang)

    def GetAllLangPaths(self, langCode):
        paths = []

        userLangPath = os.path.join(BASE_DIR, "userdata", "lang", f"{langCode}.ini")
        appLangPath = os.path.join(BASE_DIR, "app", "lang", f"{langCode}.ini")

        if os.path.exists(userLangPath):
            paths.append(userLangPath)
            MakeLog("[Log] [LangManager]", f"Found primary user language: {langCode}")
        elif os.path.exists(appLangPath):
            paths.append(appLangPath)
            MakeLog("[Log] [LangManager]", f"Found primary system language: {langCode}")
        else:
            MakeLog("[Log] [LangManager]", f"Primary language file not found for: {langCode}. Fallback to keys.")
            return []

        for basePath in ["app/widgets", "userdata/widgets"]:
            fullBasePath = os.path.join(BASE_DIR, basePath)
            if not os.path.exists(fullBasePath):
                continue

            for wType in ["desktop", "taskbar"]:
                typePath = os.path.join(fullBasePath, wType)
                if not os.path.exists(typePath):
                    continue

                for wName in os.listdir(typePath):
                    wDir = os.path.join(typePath, wName)
                    wLangFile = os.path.join(wDir, "lang", f"{langCode}.ini")

                    if os.path.isdir(wDir) and os.path.exists(wLangFile):
                        paths.append(wLangFile)

        return paths

    def Load(self, langCode):
        allPaths = self.GetAllLangPaths(langCode)

        if not allPaths:
            return

        self.parser.clear()

        self.parser.read(allPaths, encoding = "utf-8")
        self.currentLang = langCode

        MakeLog("[Log] [LangManager]", f"Loaded translation from {len(allPaths)} files (System + Widgets).")

    def Translate(self, section, key, fallback = ""):
        return self.Get(section, key, fallback = fallback)

    def GetLangFromCode(self, langCode, section, key, fallback = ""):
        allPaths = self.GetAllLangPaths(langCode)
        if not allPaths:
            return fallback

        tempParser = configparser.ConfigParser()
        tempParser.read(allPaths, encoding = "utf-8")

        try:
            return tempParser.get(section, key)
        except Exception:
            return fallback
