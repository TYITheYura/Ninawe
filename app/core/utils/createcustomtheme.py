from . import MakeLog
import shutil
import os

def CreateCustomTheme(baseThemeName):
    from core.config import BASE_DIR, config, ConfigWrapper

    if baseThemeName == "custom":
        return True

    MakeLog("[Log] [ThemeManager]", f"Forking theme '{baseThemeName}' into \"custom\"...")

    appThemePath = os.path.join(BASE_DIR, "app", "themes", baseThemeName)
    userThemePath = os.path.join(BASE_DIR, "userdata", "themes", baseThemeName)

    sourcePath = userThemePath if os.path.exists(userThemePath) else appThemePath

    if not os.path.exists(sourcePath):
        MakeLog("[Error] [ThemeManager]", "Source theme not found!")
        return False

    customThemeDir = os.path.join(BASE_DIR, "userdata", "themes", "custom")

    if os.path.exists(customThemeDir):
        shutil.rmtree(customThemeDir)

    try:
        shutil.copytree(sourcePath, customThemeDir)

        customThemeIni = os.path.join(customThemeDir, "themeconfig.ini")
        tempParser = ConfigWrapper()
        tempParser.parser.read(customThemeIni, encoding = "utf-8")
        tempParser.Set("Theme", "name", "Custom Theme")
        tempParser.Save(customThemeIni)

        config.app.Set("Theme", "current_theme", "custom")
        config.app.Save()

        MakeLog("[Log] [ThemeManager]", "Custom theme successfully created and applied.")
        return True
    except Exception as e:
        MakeLog("[Error] [ThemeManager]", f"Failed to fork theme: {e}")
        return False
