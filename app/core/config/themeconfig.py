import os
from . import ConfigWrapper
from . import GlobalThemeConfigData
from core.utils import MakeLog

# This class covers everything related to the themes
class ThemeConfig(ConfigWrapper):
    def __init__(self):
        super().__init__()
        self.currentThemePath = ""
        self.themeInitFile = ""

        self.hashes = {}
        self.globals = GlobalThemeConfigData()

    def Load(self, themeName):
        # Getting theme by name
        self.currentThemePath = self.GetThemePath(themeName)
        self.themeInitFile = os.path.join(self.currentThemePath, "themeconfig.ini")

        # Checking if theme in folder is exists
        if not os.path.exists(self.themeInitFile):
            if themeName != "default":
                # fallback to default theme
                MakeLog(f"[Log] [ThemeConfig] | No theme with name {themeName} detected. Rolling back to default.")
                self.currentThemePath = self.GetThemePath("default")
                self.themeInitFile = os.path.join(self.currentThemePath, "themeconfig.ini")

        self.parser.clear()
        self.parser.read(self.themeInitFile)

        changedSections = self.SectionHashCheck(self)

        self.ParseGlobals()

        MakeLog(f"[Log] [ThemeConfig] | Theme loaded: {themeName}")

        return changedSections

    def ParseGlobals(self):
        MakeLog("[Log] [ThemeConfig] | Caching theme global properties...")
        rawFont = self.Get("Global", "font_family", fallback = "Segoe UI")
        if rawFont.lower().endswith((".ttf", ".otf")):
            self.globals.fontFamily = self.GetResource(rawFont)
        else:
            self.globals.fontFamily = rawFont
        self.globals.fontSize = self.GetInt("Global", "font_size", fallback = 12)
        self.globals.fontColor = self.Get("Global", "font_color", fallback = "#FFFFFF")
        self.globals.fontShadow = self.GetBool("Global", "font_shadow", fallback = True)

    def GetThemePath(self, themeName):
        # Theme folder paths
        userPath = os.path.join(self.GetPath(f"userdata\\themes\\{themeName}"))
        appPath = os.path.join(self.GetPath(f"app\\themes\\{themeName}"))

        # User theme (high priority)
        if os.path.exists(os.path.join(userPath, "themeconfig.ini")):
            # MakeLog(f"[Log] [ThemeConfig] | Loading user theme: \"{themeName}\"") # Commented because flood
            return userPath

        # Default build-in theme
        if os.path.exists(os.path.join(appPath, "themeconfig.ini")):
            # MakeLog(f"[Log] [ThemeConfig] | Loading system theme: \"{themeName}\"") # Commented because flood
            return appPath

        # Not found anything
        MakeLog(f"[Log] [ThemeConfig] | Theme \"{themeName}\" not found! Fallback to default.")
        return os.path.join(appPath, "default")

    def GetResource(self, relativePath):
        if os.path.isabs(relativePath):
            return relativePath
        return os.path.join(self.currentThemePath, relativePath)
