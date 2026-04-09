import os
from core.config import ConfigWrapper, BASE_DIR
from core.utils import MakeLog

class LangManager(ConfigWrapper):
    def __init__(self, appСonfig):
        super().__init__()
        self.app = appСonfig
        self.currentLang = self.app.Get("App", "language", fallback = "uk")
        self.Load(self.currentLang)

    def Load(self, langCode):
        userLangPath = os.path.join(BASE_DIR, "userdata", "lang", f"{langCode}.ini")
        appLangPath = os.path.join(BASE_DIR, "app", "lang", f"{langCode}.ini")

        if os.path.exists(userLangPath):
            targetPath = userLangPath
            MakeLog("[Log] [LangManager]", f"Loading user language: {langCode}")
        elif os.path.exists(appLangPath):
            targetPath = appLangPath
            MakeLog("[Log] [LangManager]", f"Loading system language: {langCode}")
        else:
            MakeLog("[Log] [LangManager]", f"Language file not found for: {langCode}. Fallback to keys.")
            return

        self.parser.clear()
        self.parser.read(targetPath, encoding = "utf-8")
        self.currentLang = langCode

    def Translate(self, section, key, fallback = ""):
        return self.Get(section, key, fallback = fallback)
