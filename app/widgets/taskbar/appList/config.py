import os
from core.config import ConfigWrapper, ConfigUpdateChecker
from core.config import config as selectedThemeConfig
from core.utils import RAWToPerOrPix
from PyQt6.QtCore import QFileSystemWatcher
from ui.taskbar import TBConfig
from core.utils import MakeLog

class WidgetConfig(ConfigUpdateChecker):
    def __init__(self):
        self.section = "Taskbar.AppList"
        super().__init__([self.section, "Taskbar.Geometry"])

        self.buildInConfig = ConfigWrapper()
        self.selectedConfig = ""
        self.widgetPath = os.path.dirname(os.path.abspath(__file__))
        self.configPath = os.path.join(self.widgetPath, "config.ini")

        self.visibility = True
        self.position = 0
        self.iconSize = 0
        self.paddings = 0
        self.spacing = 0
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

        positionRAW = self.selectedConfig.Get(self.section, "position", fallback = 50)
        self.position = RAWToPerOrPix(positionRAW, TBConfig.panelWidth, fallback = 0)

        self.iconSize = self.selectedConfig.GetInt(self.section, "icon_size", fallback = 20)
        self.paddings = self.selectedConfig.GetInt(self.section, "paddings", fallback = 5)
        self.spacing = self.selectedConfig.GetInt(self.section, "spacing", fallback = 10)
        self.align = self.selectedConfig.GetInt(self.section, "align", fallback = 100)

    def BuildInConfigFileChanged(self, path):
        MakeLog(f"[Log] [{self.section}]", f"Local config changed: {path}.")

        if path not in self.buildInWidgetConfigWatcher.files() and os.path.exists(path):
            self.buildInWidgetConfigWatcher.addPath(path)
        self.Updater()
        self.configUpdated.emit("local", [self.section])


WConfig = WidgetConfig()
