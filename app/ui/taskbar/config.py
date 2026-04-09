from core.config import config as themeConfig
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication
from core.config import ConfigUpdateChecker

class TaskbarConfig(ConfigUpdateChecker):
    def __init__(self):
        self.section = "Taskbar"

        super().__init__([self.section])

        self.enableBlur = None
        self.radius = None
        self.borderColor = None
        self.borderWidth = None
        self.blurMode = None
        self.sw = None
        self.sh = None
        self.anchorX = None
        self.anchorY = None
        self.panelWidth = None
        self.panelHeight = None
        self.rawPanelXPositionData = None
        self.rawPanelYPositionData = None
        self.themeUpdatedState = True
        self.qtBgColor = None
        self.winBlurColor = None
        self.rawPanelWidthData = None
        self.rawPanelHeightData = None

        self.Updater()

    def Updater(self):
        self.enableBlur = themeConfig.theme.GetBool(self.section, "blur_enabled", fallback = False)
        self.blurMode = themeConfig.theme.GetInt(self.section, "blur_mode", fallback = 4)
        self.rawPanelWidthData = themeConfig.theme.Get(self.section, "width", fallback = 90)
        self.rawPanelHeightData = themeConfig.theme.Get(self.section, "height", fallback = 30)
        self.anchorX = themeConfig.theme.GetInt(self.section, "anchor_x", fallback = 50)
        self.anchorY = themeConfig.theme.GetInt(self.section, "anchor_y", fallback = 100)
        self.rawPanelXPositionData = themeConfig.theme.GetInt(self.section, "position_x", fallback = 98)
        self.rawPanelYPositionData = themeConfig.theme.GetInt(self.section, "position_y", fallback = 2)
        self.radius = 0 if self.enableBlur else themeConfig.theme.GetInt(self.section, "border_radius_px", fallback = 10)
        self.borderColor = themeConfig.theme.Get(self.section, "argb_border_color", fallback = "#FFFFFF33")
        self.borderWidth = themeConfig.theme.GetInt(self.section, "border_width_px", fallback = 1)

        rawBGColor = themeConfig.theme.Get(self.section, "argb_color", fallback = "#000000")

        # =[> Panel color
        if self.enableBlur and self.blurMode == 1:
            # config blur mode: 1 (4 - acrylic)
            self.qtBgColor = QColor(0, 0, 0, 0)
            self.winBlurColor = rawBGColor
        else:
            # config blur mode: 0 (3 - default) / enable_blur = False
            self.qtBgColor = QColor(rawBGColor)
            self.winBlurColor = "#00000000"

        screen = QApplication.primaryScreen().geometry()
        self.sw, self.sh = screen.width(), screen.height()


TBConfig = TaskbarConfig()
