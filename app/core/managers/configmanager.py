import os
from PyQt6.QtCore import QObject, pyqtSignal, QFileSystemWatcher
from . import LangManager
from core.utils import MakeLog

# All-in-one config manager
class ConfigManager(QObject):
    # Signals
    configUpdated = pyqtSignal(str, list)

    def __init__(self, appConfig, themeConfig):
        super().__init__()
        self.app = appConfig
        self.theme = themeConfig
        self.lang = LangManager(self.app)

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
                MakeLog(f"[Log] [ConfigWatcher] [UpdateWatchList] | Added: {self.app.configFilePath}")

        if self.theme.themeInitFile and self.theme.themeInitFile not in files:
            if os.path.exists(self.theme.themeInitFile):
                self.watcher.addPath(self.theme.themeInitFile)
                MakeLog(f"[Log] [ConfigWatcher] [UpdateWatchList] | Added: {self.theme.themeInitFile}")

    # One updater for config/themeconfig
    def OnFileChanged(self, path):
        if path == self.app.configFilePath:
            MakeLog("[Log] [ConfigManager] [Config] | App config changes detected.")
            changes = self.app.Load()
            newTheme = self.app.Get("Theme", "current_theme", fallback = "default")
            newLang = self.app.Get("App", "language", fallback = "uk")

            # If theme in config.ini switched
            if self.currentTheme != newTheme:
                MakeLog(f"[Log] [ConfigManager] [Config] | Theme switch detected: {self.currentTheme} -> {newTheme}")
                if self.theme.themeInitFile in self.watcher.files():
                    self.watcher.removePath(self.theme.themeInitFile)

                self.theme.Load(newTheme)
                self.currentTheme = newTheme
                self.UpdateWatchList()

                self.configUpdated.emit("theme", ["ALL"])
            # If other props is changed
            elif self.lang.currentLang != newLang:
                self.lang.Load(newLang)

            self.configUpdated.emit("app", changes)

        elif path == self.theme.themeInitFile:
            changes = self.theme.Load(self.app.Get("Theme", "current_theme"))
            if changes:
                MakeLog("[Log] [ConfigManager] [Config] | Theme config changes detected.")
                self.configUpdated.emit("theme", changes)

        self.UpdateWatchList()
