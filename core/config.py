from PyQt6.QtCore import QObject, pyqtSignal, QFileSystemWatcher
import configparser
import os
import sys

# Absolute path to files
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Base class for convenient data retrieval
class ConfigWrapper:
    def __init__(self):
        self.parser = configparser.ConfigParser(interpolation = None)

    def Get(self, section, option, fallback = None):
        try:
            return self.parser.get(section, option, fallback = fallback)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback

    def GetBool(self, section, option, fallback = False):
        try:
            return self.parser.getboolean(section, option, fallback = fallback)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback

    def GetInt(self, section, option, fallback = 0):
        try:
            return self.parser.getint(section, option)
        except ValueError:
            # Attempt to read only numeric data if it exists
            rawData = self.parser.get(section, option)
            numData = rawData.replace("px", "").replace("%", "").strip()
            return int(numData)
        except:
            return fallback

    def GetFloat(self, section, option, fallback = 0.00):
        try:
            return self.parser.getfloat(section, option)
        except ValueError:
            # Attempt to read only numeric data if it exists
            rawData = self.parser.get(section, option)
            numData = rawData.replace("px", "").replace("%", "").strip()
            return int(numData)
        except:
            return fallback

    def GetSectionStatus(self, section):
        return self.parser.has_section(section)

# Theme [Global] properties (and defaults)
class GlobalThemeConfigData:
    def __init__(self):
        self.fontFamily = "Arial"
        self.fontSize = 12
        self.fontColor = "#FFFFFF"
        self.fontShadow = True

# This class covers everything related to the themes
class ThemeConfig(ConfigWrapper):
    def __init__(self, configManager):
        super().__init__()
        self.configManager = configManager
        self.currentThemePath = ""
        self.themeInitFile = ""

        self.globals = GlobalThemeConfigData()

        self.Load()

    def Load(self):
        # Getting theme from config.ini file
        themeName = self.configManager.app.Get("Theme", "current_theme", fallback = "default")
        self.currentThemePath = os.path.join(BASE_DIR, "themes", themeName)
        self.themeInitFile = os.path.join(self.currentThemePath, "themeconfig.ini")

        # Checking if theme in folder is exists
        if not os.path.exists(self.themeInitFile):
            if themeName != "default":
                # fallback to default theme
                self.currentThemePath = os.path.join(BASE_DIR, "themes", "default")
                self.themeInitFile = os.path.join(self.currentThemePath, "themeconfig.ini")
        
        self.parser.clear()
        self.parser.read(self.themeInitFile)
        print("[Log] [ThemeConfig] | Caching theme global properties...")
        rawFont = self.Get("Global", "font_family", fallback="Segoe UI")
        if rawFont.lower().endswith((".ttf", ".otf")):
             self.globals.fontFamily = self.GetResource(rawFont)
        else:
             self.globals.fontFamily = rawFont
        self.globals.fontSize = self.GetInt("Global", "font_size", fallback = 12)
        self.globals.fontColor = self.Get("Global", "font_color", fallback = "#FFFFFF")
        self.globals.fontShadow = self.GetBool("Global", "font_shadow", fallback = True)

        print(f"[Log] [Info] [ThemeConfig] | Theme loaded: {themeName}")

    def GetResource(self, relativePath):
        if os.path.isabs(relativePath):
            return relativePath
        return os.path.join(self.currentThemePath, relativePath)

# This class covers everything related to the program properties
class AppConfig(ConfigWrapper):
    def __init__(self, configManager):
        super().__init__()
        self.configManager = configManager
        self.configFilePath = os.path.join(BASE_DIR, "preferences", "config.ini")
        self.Load()

    def Load(self):
        if not os.path.exists(self.configFilePath):
            print(f"[Log] [Critical] [AppConfig] | Config file on directory {self.configFilePath} not found.")
            return
        self.parser.read(self.configFilePath)

# All-in-one config manager
class ConfigManager(QObject):
    # Signals
    themeUpdated = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.app = AppConfig(self)
        self.theme = ThemeConfig(self)

        self.watcher = QFileSystemWatcher()
        self.watcher.fileChanged.connect(self.OnFileChanged)
        self.UpdateWatchList()

    # Updating watching files list
    def UpdateWatchList(self):
        # Clearing old paths if it exists
        if self.watcher.files():
            self.watcher.removePaths(self.watcher.files())

        path = self.theme.themeInitFile
        if path and os.path.exists(path):
            self.watcher.addPath(path)
            print(f"[Log] [ConfigWatcher] | Now watching {path}")

    # Triggered by system if file are changed
    def OnFileChanged(self):
        print("[Log] [ConfigWatcher] | Changes in config files are detected. Trying to load...")
        self.theme.Load()
        self.UpdateWatchList()
        self.themeUpdated.emit()

    def Reload(self):
        self.app.load()
        self.theme.load()
        self.UpdateWatchList()
        self.themeUpdated.emit()

config = ConfigManager()