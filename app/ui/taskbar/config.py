from core.config import config as themeConfig
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication
from core.config import ConfigUpdateChecker
from core.utils import RAWToPerOrPix

class TaskbarConfig(ConfigUpdateChecker):
    def __init__(self):
        self.section = "Taskbar"
        self.geometrySection = "Taskbar.Geometry"
        self.activeWidgetsSection = "Taskbar.ActiveWidgets"
        self.positionSection = "Taskbar.Position"

        super().__init__([self.section, self.geometrySection, self.activeWidgetsSection, self.positionSection])

        self.enableBlur = False
        self.radius = 0
        self.borderColor = ""
        self.borderWidth = 0
        self.blurMode = 0
        self.sw = 0
        self.sh = 0
        self.panelWidth = 0
        self.panelHeight = 0
        self.panelX = 0
        self.panelY = 0
        self.themeUpdatedState = True
        self.qtBgColor = ""
        self.winBlurColor = ""

        self.Updater()

    def Updater(self):

        screen = QApplication.primaryScreen().geometry()
        self.sw, self.sh = screen.width(), screen.height()

        self.enableBlur = themeConfig.theme.GetBool(self.section, "blur_enabled", fallback = False)
        self.blurMode = themeConfig.theme.GetInt(self.section, "blur_mode", fallback = 4)

        # Panel width/height

        rawPanelWidthData = themeConfig.theme.Get(self.geometrySection, "width", fallback = 90)
        rawPanelHeightData = themeConfig.theme.Get(self.geometrySection, "height", fallback = 30)

        self.panelWidth = round(RAWToPerOrPix(rawPanelWidthData, self.sw, fallback = self.sw))
        self.panelHeight = round(RAWToPerOrPix(rawPanelHeightData, self.sh, fallback = self.sh * (2 / 100)))

        anchorX = themeConfig.theme.Get(self.positionSection, "anchor_x", fallback = 50)
        anchorY = themeConfig.theme.Get(self.positionSection, "anchor_y", fallback = 100)

        # End.

        # Panel position

        rawPanelXPositionData = themeConfig.theme.Get(self.positionSection, "position_x", fallback = 98)
        rawPanelYPositionData = themeConfig.theme.Get(self.positionSection, "position_y", fallback = 2)

        panelXPosition = RAWToPerOrPix(rawPanelXPositionData, self.sw)
        panelYPosition = RAWToPerOrPix(rawPanelYPositionData, self.sh)

        offsetX = RAWToPerOrPix(anchorX, self.panelWidth)
        offsetY = RAWToPerOrPix(anchorY, self.panelHeight)

        self.panelX = round(panelXPosition - offsetX)
        self.panelY = round(panelYPosition - offsetY)

        # End.

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


TBConfig = TaskbarConfig()
