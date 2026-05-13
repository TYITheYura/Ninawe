import os
from core.config import ConfigWrapper, ConfigUpdateChecker
from core.config import config as selectedThemeConfig
from core.utils import RAWToPerOrPix
from PyQt6.QtCore import QFileSystemWatcher
from ui.taskbar import TBConfig
from core.utils import MakeLog
from easydict import EasyDict as easyDict

class WidgetConfig(ConfigUpdateChecker):
    def __init__(self):
        self.section = "Taskbar.AppList"
        self.buttonSection = "Taskbar.AppList.Button"
        super().__init__([self.section, self.buttonSection, "Taskbar.Geometry"])

        self.buildInConfig = ConfigWrapper()
        self.selectedConfig = ""
        self.widgetPath = os.path.dirname(os.path.abspath(__file__))
        self.configPath = os.path.join(self.widgetPath, "config.ini")

        self.container = ""

        self.visibility = True
        self.position = 0
        self.iconSize = 0
        self.paddings = 0
        self.spacing = 0
        self.align = 0

        self.buttonStyleSheet = ""
        self.mainStyleSheet = ""

        self.main = easyDict(
            {
                "bgColor": {},
                "border": {
                    "color": {},
                    "width": {},
                    "radius": {
                        "topLeft": {},
                        "topRight": {},
                        "bottomRight": {},
                        "bottomLeft": {}
                    }
                }
            }
        )

        self.container = easyDict(
            {
                "default": {
                    "color": {}
                },
                "hovered": {
                    "color": {}
                },
                "pressed": {
                    "color": {}
                },
                "opened": {
                    "color": {},
                    "lineColor": {}
                },
                "focus": {
                    "color": {},
                    "lineColor": {}
                },
                "line": {
                    "width": {}
                },
                "radius": {}
            }
        )

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

        self.container.default.color = self.selectedConfig.Get(self.buttonSection, "default_state_container_color", fallback = "#01000000")
        self.container.hovered.color = self.selectedConfig.Get(self.buttonSection, "hovered_state_container_color", fallback = "#33FFFFFF")
        self.container.pressed.color = self.selectedConfig.Get(self.buttonSection, "pressed_state_container_color", fallback = "#44FFFFFF")
        self.container.opened.color = self.selectedConfig.Get(self.buttonSection, "opened_state_container_color", fallback = "#00000000")
        self.container.opened.lineColor = self.selectedConfig.Get(self.buttonSection, "opened_state_line_color", fallback = "#FF888888")
        self.container.focus.color = self.selectedConfig.Get(self.buttonSection, "focus_state_container_color", fallback = "11FFFFFF")
        self.container.focus.lineColor = self.selectedConfig.Get(self.buttonSection, "focus_state_line_color", fallback = "#FF0078D7")
        self.container.line.width = self.selectedConfig.GetInt(self.buttonSection, "line_width", fallback = 1)
        self.container.radius = self.selectedConfig.GetInt(self.buttonSection, "container_radius", fallback = 0)

        self.buttonStyleSheet = f"""
            /*
                Default
            */
            TaskbarButton {{
                background-color: {self.container.default.color};
                border-radius: {self.container.radius}px;
            }}

            /*
                Base hover
            */
            TaskbarButton[isHovered="true"] {{
                background-color: {self.container.hovered.color};
            }}

            /*
                Opened (on background) (one window)
            */
            TaskbarButton[isOpen="true"][isGroup="false"] {{
                background-color: {self.container.opened.color};
                padding-bottom: -{self.container.line.width}px;
                border-bottom: {self.container.line.width}px solid {self.container.opened.lineColor};
            }}
            TaskbarButton[isOpen="true"][isGroup="false"][isHovered="true"] {{
                background-color: {self.container.hovered.color};
            }}

            /*
                Opened (on background) (group)
            */
            TaskbarButton[isOpen="true"][isGroup="true"] {{
                background-color: {self.container.opened.color};
                padding-bottom: -{self.container.line.width + 2}px;
                border-bottom: {self.container.line.width + 2}px solid {self.container.opened.lineColor};
            }}
            TaskbarButton[isOpen="true"][isGroup="true"][isHovered="true"] {{
                background-color: {self.container.hovered.color};
            }}

            /*
                In focus (one window)
            */
            TaskbarButton[isActive="true"][isGroup="false"] {{
                padding-bottom: -{self.container.line.width}px;
                border-bottom: {self.container.line.width}px solid {self.container.focus.lineColor};
                background-color: {self.container.focus.color};
            }}
            TaskbarButton[isActive="true"][isGroup="false"][isHovered="true"] {{
                background-color: {self.container.hovered.color};
            }}

            /*
                In focus (group)
            */
            TaskbarButton[isActive="true"][isGroup="true"] {{
                padding-bottom: --{self.container.line.width + 2}px;
                border-bottom: {self.container.line.width + 2}px solid {self.container.focus.lineColor};
                background-color: {self.container.focus.color};
            }}
            TaskbarButton[isActive="true"][isGroup="true"][isHovered="true"] {{
                background-color: {self.container.hovered.color};
            }}

            /*
                Pressed
                WOOOOAH, DON'T DO THIS AGAIN PLEASE
            */
            TaskbarButton[isPressed="true"],
            TaskbarButton[isHovered="true"][isPressed="true"],
            TaskbarButton[isOpen="true"][isGroup="false"][isPressed="true"],
            TaskbarButton[isOpen="true"][isGroup="true"][isPressed="true"],
            TaskbarButton[isActive="true"][isGroup="false"][isPressed="true"],
            TaskbarButton[isActive="true"][isGroup="true"][isPressed="true"],
            TaskbarButton[isMinimized="true"][isPressed="true"],
            TaskbarButton[isOpen="true"][isGroup="false"][isHovered="true"][isPressed="true"],
            TaskbarButton[isOpen="true"][isGroup="true"][isHovered="true"][isPressed="true"],
            TaskbarButton[isActive="true"][isGroup="false"][isHovered="true"][isPressed="true"],
            TaskbarButton[isActive="true"][isGroup="true"][isHovered="true"][isPressed="true"],
            TaskbarButton[isMinimized="true"][isHovered="true"][isPressed="true"] {{
                background-color: {self.container.pressed.color};
            }}
        """

        self.main.bgColor = self.selectedConfig.Get(self.section, "background_color", fallback = 100)
        self.main.border.color = self.selectedConfig.Get(self.section, "border_color", fallback = 100)
        self.main.border.width = self.selectedConfig.GetInt(self.section, "border_width", fallback = 100)
        self.main.border.radius.topLeft = self.selectedConfig.GetInt(self.section, "radius_top_left", fallback = 100)
        self.main.border.radius.topRight = self.selectedConfig.GetInt(self.section, "radius_top_right", fallback = 100)
        self.main.border.radius.bottomRight = self.selectedConfig.GetInt(self.section, "radius_bottom_right", fallback = 100)
        self.main.border.radius.bottomLeft = self.selectedConfig.GetInt(self.section, "radius_bottom_left", fallback = 100)

        self.mainStyleSheet = f"""
            QWidget#appListWidget {{
                background-color: {self.main.bgColor};
                border-color: {self.main.border.color};
                border-width: {self.main.border.width};
                border-style: solid;
                border-top-left-radius: {self.main.border.radius.topLeft}px;
                border-top-right-radius: {self.main.border.radius.topRight}px;
                border-bottom-right-radius: {self.main.border.radius.bottomRight}px;
                border-bottom-left-radius: {self.main.border.radius.bottomLeft}px;
                padding: {self.main.border.width}px;
            }}
        """

        onFirstButtonTopLeft = max(self.main.border.radius.topLeft, self.container.radius)
        onFirstButtonBottomLeft = max(self.main.border.radius.bottomLeft, self.container.radius)
        onLastButtomTopRight = max(self.main.border.radius.topRight, self.container.radius)
        onLastButtomBottomRight = max(self.main.border.radius.bottomRight, self.container.radius)

        self.styleOnFirstButton = f"""
            TaskbarButton {{
                border-top-left-radius: {onFirstButtonTopLeft}px;
                border-bottom-left-radius: {onFirstButtonBottomLeft}px;
            }}
        """

        self.styleOnLastButton = f"""
            TaskbarButton {{
                border-top-right-radius: {onLastButtomTopRight}px;
                border-bottom-right-radius: {onLastButtomBottomRight}px;
            }}
        """

    def BuildInConfigFileChanged(self, path):
        MakeLog(f"[Log] [{self.section}]", f"Local config changed: {path}.")

        if path not in self.buildInWidgetConfigWatcher.files() and os.path.exists(path):
            self.buildInWidgetConfigWatcher.addPath(path)
        self.Updater()
        self.configUpdated.emit("local", [self.section])


WConfig = WidgetConfig()
