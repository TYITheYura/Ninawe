from core.config import config as configurator
from core.config import ConfigUpdateChecker
from PyQt6.QtWidgets import QApplication

class PowerMenuConfig(ConfigUpdateChecker):
    def __init__(self):
        self.section = "PowerMenu"

        super().__init__([self.section])

        self.userPreferencesPath = configurator.theme.GetPath("userdata\\preferences\\user\\powermenudata.json")
        self.iconsDir = ""

        self.screen = None
        self.spacing = 0
        self.buttonSize = 0
        self.radius = 0
        self.blurEnabled = False
        self.blurMode = 0
        self.buttonColor = ""
        self.hoverColor = ""
        self.pressedColor = ""
        self.isFullscreen = False
        self.bgColor = ""
        self.containerColor = ""
        self.containerWidth = 0
        self.containerHeight = 0
        self.containerHeightMax = 0
        self.containerWidthMax = 0
        self.containerMargins = 0
        self.borderWidth = 0
        self.borderColor = 0
        self.buttonBorderWidth = 0
        self.doubleContainerBackground = False
        self.doubleContainerBackgroundAccent = "bg"
        self.doubleContainerColor = ""
        self.fullscreenColor = ""
        self.useBGColor = False
        self.menuLayout = "horizontal"
        self.containerPaddings = 0
        self.buttonStyle = ""

        self.Updater()

    def Updater(self):
        self.screen = QApplication.primaryScreen().geometry()
        self.buttonSize = configurator.theme.GetInt(self.section, "button_size", fallback = 80)
        self.hoverColor = configurator.theme.Get(self.section, "hover_color", fallback = "#FFFFFF20")
        self.pressedColor = configurator.theme.Get(self.section, "pressed_color", fallback = "#FFFFFF40")
        self.spacing = configurator.theme.GetInt(self.section, "spacing", fallback = 50)
        self.buttonColor = configurator.theme.Get(self.section, "button_color", fallback = "transparent")
        self.isFullscreen = configurator.theme.GetBool(self.section, "fullscreen", fallback = True)
        self.blurEnabled = configurator.theme.GetBool(self.section, "blur_enabled", fallback = True)
        self.blurMode = configurator.theme.GetInt(self.section, "blur_mode", fallback = 0)
        self.radius = 0 if self.blurEnabled and self.isFullscreen is False else configurator.theme.GetInt(self.section, "border_radius", fallback = 10)
        self.bgColor = configurator.theme.Get(self.section, "argb_background_color", fallback = "#00000080")
        self.containerColor = configurator.theme.Get(self.section, "argb_container_color", fallback = "#00000080")
        self.borderWidth = configurator.theme.GetInt(self.section, "border_width_px", fallback = 1)
        self.borderColor = configurator.theme.Get(self.section, "argb_border_color", fallback = "#00000080")
        self.buttonBorderWidth = configurator.theme.GetInt(self.section, "button_border_width", fallback = 0)
        self.buttonBorderColor = configurator.theme.Get(self.section, "button_border_color", fallback = "#FFFFFFFF")
        self.containerWidth = configurator.theme.GetInt(self.section, "width", fallback = 600)
        self.containerHeight = configurator.theme.GetInt(self.section, "height", fallback = 200)
        self.containerMargins = configurator.theme.GetInt(self.section, "margins", fallback = 0)
        self.doubleContainerBackground = configurator.theme.GetBool(self.section, "double_container_bg", fallback = False)
        self.doubleContainerBackgroundAccent = configurator.theme.Get(self.section, "double_container_bg_accent", fallback = "bg")
        self.iconsDir = configurator.theme.Get(self.section, "icons_dir", fallback = "")
        self.useBGColor = configurator.theme.GetBool(self.section, "use_bg_color", fallback = False)
        self.containerPaddings = configurator.theme.GetInt(self.section, "paddings", fallback = 10)

        self.buttonStyle = f"""
            QPushButton {{
                background-color: {self.buttonColor};
                border: {self.buttonBorderWidth}px solid {self.buttonBorderColor};
                border-radius: {self.radius}px;
                color: white;
                font-size: 20px;
                font-family: "Arial";
                font-weight: bold;
                margin: 0;
            }}
            QPushButton:hover {{ background-color: {self.hoverColor}; }}
            QPushButton:pressed {{ background-color: {self.pressedColor}; }}
        """


PMConfig = PowerMenuConfig()
