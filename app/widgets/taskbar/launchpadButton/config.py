import os
from core.config import ConfigWrapper, ConfigUpdateChecker
from core.config import config as selectedThemeConfig
from core.utils import RAWToPerOrPix
from ui.taskbar import TBConfig
from PyQt6.QtCore import QFileSystemWatcher
from PyQt6.QtGui import QPixmap

class WidgetConfig(ConfigUpdateChecker):
    def __init__(self):
        self.section = "Taskbar.LaunchpadButton"

        super().__init__([self.section])

        self.buildInConfig = ConfigWrapper()
        self.selectedConfig = ""

        self.widgetPath = os.path.dirname(os.path.abspath(__file__))
        self.configPath = os.path.join(self.widgetPath, "config.ini")

        self.pixNormal = ""
        self.pixHover = ""
        self.pixPressed = ""

        self.padding = 0
        self.align = 0

        self.buildInWidgetConfigWatcher = QFileSystemWatcher()
        if os.path.exists(self.configPath):
            self.buildInWidgetConfigWatcher.addPath(self.configPath)
            self.buildInWidgetConfigWatcher.fileChanged.connect(self.BuildInConfigFileChanged)

        self.Updater()

    def Updater(self):
        if selectedThemeConfig.theme.GetSectionStatus(self.section):
            self.selectedConfig = selectedThemeConfig.theme
        else:
            self.buildInConfig.parser.read(self.configPath)
            self.selectedConfig = self.buildInConfig

        self.visibility = self.selectedConfig.GetBool(self.section, "visible", fallback = True)

        positionRAW = self.selectedConfig.Get(self.section, "position", fallback = 10)
        self.position = RAWToPerOrPix(positionRAW, TBConfig.panelWidth, fallback = 0)

        defaultIcon = self.selectedConfig.Get(self.section, "default", fallback = "")
        hoverIcon = self.selectedConfig.Get(self.section, "hover", fallback = "")
        activeIcon = self.selectedConfig.Get(self.section, "active", fallback = "")

        self.pixNormal = QPixmap(os.path.join(self.widgetPath, defaultIcon))
        self.pixHover = QPixmap(os.path.join(self.widgetPath, hoverIcon))
        self.pixPressed = QPixmap(os.path.join(self.widgetPath, activeIcon))

        self.padding = self.selectedConfig.GetInt(self.section, "padding", fallback = 2)
        self.align = self.selectedConfig.GetInt(self.section, "align", fallback = 0)

    def BuildInConfigFileChanged(self, path):
        print(f"[Log] [{self.section}] | Local config changed: {path}.")

        if path not in self.buildInWidgetConfigWatcher.files() and os.path.exists(path):
            self.buildInWidgetConfigWatcher.addPath(path)

        self.Updater()

        self.configUpdated.emit("local", [self.section])


WConfig = WidgetConfig()
