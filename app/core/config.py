from PyQt6.QtCore import QObject, pyqtSignal, QFileSystemWatcher
import configparser
import os
import sys
import hashlib

# Absolute path to files
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # from config.py to default directory (.. x 3)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print(f"[Log] [Config] | Default path: {BASE_DIR}")

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

    def GetPath(self, path = ""):
        return os.path.join(BASE_DIR, path)

    # I'm too dumb to do this properly, so the hash variable must be called "hashes" in any case
    def SectionHashCheck(self, dataClaimer = None):
        if dataClaimer == None:
            print("[Log] [ConfigWrapper] [SectionHashCheck] | Data not set")
            return

        changedSections = []
        allSections = dataClaimer.parser.sections()

        for section in allSections:
            items = sorted(dataClaimer.parser.items(section))
            rawData = str(items).encode("utf-8")
            currentHash = hashlib.md5(rawData).hexdigest()
            oldHash = dataClaimer.hashes.get(section)

            if currentHash != oldHash:
                dataClaimer.hashes[section] = currentHash
                changedSections.append(section)

        return changedSections

# Theme [Global] properties (and defaults)
class GlobalThemeConfigData:
    def __init__(self):
        self.fontFamily = "Arial"
        self.fontSize = 12
        self.fontColor = "#FFFFFF"
        self.fontShadow = True

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
                print(f"[Log] [ThemeConfig] | No theme with name {themeName} detected. Rolling back to default.")
                self.currentThemePath = self.GetThemePath("default")
                self.themeInitFile = os.path.join(self.currentThemePath, "themeconfig.ini")
        
        self.parser.clear()
        self.parser.read(self.themeInitFile)

        changedSections = self.SectionHashCheck(self)

        self.ParseGlobals()

        print(f"[Log] [ThemeConfig] | Theme loaded: {themeName}")

        return changedSections

    def ParseGlobals(self):
        print("[Log] [ThemeConfig] | Caching theme global properties...")
        rawFont = self.Get("Global", "font_family", fallback =  "Segoe UI")
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
        print(userPath)
        print(appPath)
        
        # User theme (high priority)
        if os.path.exists(os.path.join(userPath, "themeconfig.ini")):
            print(f"[Log] [ThemeConfig] | Loading user theme: \"{themeName}\"")
            return userPath

        # Default build-in theme
        if os.path.exists(os.path.join(appPath, "themeconfig.ini")):
            print(f"[Log] [ThemeConfig] | Loading system theme: \"{themeName}\"")
            return appPath

        # Not found anything
        print(f"[Log] [ThemeConfig] | Theme \"{themeName}\" not found! Fallback to default.")
        return os.path.join(appPath, "default")

    def GetResource(self, relativePath):
        if os.path.isabs(relativePath):
            return relativePath
        return os.path.join(self.currentThemePath, relativePath)

# This class covers everything related to the program properties
class AppConfig(ConfigWrapper):
    def __init__(self):
        super().__init__()
        self.configFilePath = os.path.join(BASE_DIR, "userdata", "preferences",  "program", "config.ini")
        self.hashes = {}
        self.Load()

    def Load(self):
        if not os.path.exists(self.configFilePath):
            print(f"[Log] [AppConfig] | Config file on directory {self.configFilePath} not found.")
            return []

        self.parser.read(self.configFilePath)
        changedSections = self.SectionHashCheck(self)
        print(f"[Log] [AppConfig] | {self.configFilePath} loaded.")
        return changedSections

# All-in-one config manager
class ConfigManager(QObject):
    # Signals
    configUpdated = pyqtSignal(str, list)

    def __init__(self):
        super().__init__()
        self.app = AppConfig()
        self.theme = ThemeConfig()

        self.currentTheme = self.app.Get("Theme", "current_theme", fallback = "default")
        self.theme.Load(self.currentTheme)

        self.watcher = QFileSystemWatcher()
        self.watcher.fileChanged.connect(self.OnFileChanged)
        self.UpdateWatchList()

    # Updating watching files list
    def UpdateWatchList(self):
        files = self.watcher.files()

        if self.app.configFilePath and self.app.configFilePath not in files:
            if os.path.exists(self.app.configFilePath):
                self.watcher.addPath(self.app.configFilePath)
                print(f"[Log] [ConfigWatcher] [UpdateWatchList] | Added: {self.app.configFilePath}")

        if self.theme.themeInitFile and self.theme.themeInitFile not in files:
            if os.path.exists(self.theme.themeInitFile):
                self.watcher.addPath(self.theme.themeInitFile)
                print(f"[Log] [ConfigWatcher] [UpdateWatchList] | Added: {self.theme.themeInitFile}")

    # One updater for config/themeconfig
    def OnFileChanged(self, path):
        if path == self.app.configFilePath:
            print("[Log] [ConfigManager] [Config] | App config changes detected.")
            changes = self.app.Load()
            newTheme = self.app.Get("Theme", "current_theme", fallback = "default")
            
            # If theme in config.ini switched
            if self.currentTheme != newTheme:
                print(f"[Log] [ConfigManager] [Config] | Theme switch detected: {self.currentTheme} -> {newTheme}")
                if self.theme.themeInitFile in self.watcher.files():
                    self.watcher.removePath(self.theme.themeInitFile)
                
                self.theme.Load(newTheme)
                self.currentTheme = newTheme
                self.UpdateWatchList()
                
                self.configUpdated.emit("theme", ["ALL"]) 
            # If other props is changed
            else:
                self.configUpdated.emit("app", changes)

        elif path == self.theme.themeInitFile:
            print("[Log] [ConfigManager] [Config] | Theme config changes detected.")
            changes = self.theme.Load(self.app.Get("Theme", "current_theme"))
            if changes:
                self.configUpdated.emit("theme", changes)
        
        self.UpdateWatchList()

    def Reload(self):
        self.app.Load()
        self.theme.Load()
        self.UpdateWatchList()

config = ConfigManager()