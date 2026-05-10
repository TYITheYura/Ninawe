import os
from core.config import ConfigWrapper
from core.config import config as selectedThemeConfig
from core.config import ConfigUpdateChecker
from core.utils import LoadFont
from PyQt6.QtCore import QFileSystemWatcher
from core.utils import MakeLog

class WidgetConfig(ConfigUpdateChecker):
    def __init__(self):
        self.section = "Taskbar.Clock"

        super().__init__([self.section, "Taskbar.Geometry"])

        self.buildInConfig = ConfigWrapper()
        self.selectedConfig = None

        self.widgetPath = os.path.dirname(os.path.abspath(__file__))
        self.configPath = os.path.join(self.widgetPath, "config.ini")

        self.visibility = True
        self.fontFamily = ""
        self.fontSize = 10
        self.fontColor = "#FFFFFF"
        self.fontShadow = False

        self.clockWidth = 0
        self.clockPosition = 50
        self.clockLeftMargin = 0
        self.clockRightMargin = 0
        self.clockAlign = 50
        self.timeFormat = "HH:mm"

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

        self.visibility = self.selectedConfig.GetBool(self.section, "visible", fallback=True)

        rawFontFamily = self.selectedConfig.Get(self.section, "font_family", fallback = selectedThemeConfig.theme.globals.fontFamily)
        self.fontFamily = LoadFont(rawFontFamily, self.widgetPath)

        self.fontSize = self.selectedConfig.GetInt(self.section, "font_size", fallback = selectedThemeConfig.theme.globals.fontSize)
        self.fontColor = self.selectedConfig.Get(self.section, "font_color", fallback = selectedThemeConfig.theme.globals.fontColor)
        self.fontShadow = self.selectedConfig.GetBool(self.section, "font_shadow", fallback = selectedThemeConfig.theme.globals.fontShadow)

        self.clockWidth = self.selectedConfig.GetInt(self.section, "width", fallback = 50)
        self.clockPosition = self.selectedConfig.GetInt(self.section, "position", fallback = 50)
        self.clockLeftMargin = self.selectedConfig.GetInt(self.section, "margin_left", fallback = 10)
        self.clockRightMargin = self.selectedConfig.GetInt(self.section, "margin_right", fallback = 10)
        self.clockAlign = self.selectedConfig.GetInt(self.section, "align", fallback = 50)

        self.timeFormat = self.selectedConfig.Get(self.section, "time_format", fallback = "HH:mm").replace('\\n', '\n')

    def BuildInConfigFileChanged(self, path):
        MakeLog(f"[Log] [{self.section}]", f"Local config changed: {path}.")

        if path not in self.buildInWidgetConfigWatcher.files() and os.path.exists(path):
            self.buildInWidgetConfigWatcher.addPath(path)

        self.Updater()
        self.configUpdated.emit("local", [self.section])


WConfig = WidgetConfig()