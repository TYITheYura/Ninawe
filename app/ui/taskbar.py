from PyQt6.QtWidgets import QWidget, QApplication, QLabel, QHBoxLayout, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QRect, QTime, QTimer, QRectF
from PyQt6.QtGui import QPainter, QColor, QBrush, QFont
from core.config import config as themeConfig
from core.utils import LoadFont, MakeBlur, MakeLog
from core.widgetManager import WidgetManager

# TODO: fix widget position after changing taskbar width/height

class TaskbarConfig:
    def __init__(self):
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

    def Updater(self):
        self.enableBlur = themeConfig.theme.GetBool("Taskbar", "blur_enabled", fallback = False)
        self.blurMode = themeConfig.theme.GetInt("Taskbar", "blur_mode", fallback = 4)
        self.rawPanelWidthData = themeConfig.theme.Get("Taskbar", "width", fallback = 90)
        self.rawPanelHeightData = themeConfig.theme.Get("Taskbar", "height", fallback = 30)
        self.anchorX = themeConfig.theme.GetInt("Taskbar", "anchor_x", fallback = 50)
        self.anchorY = themeConfig.theme.GetInt("Taskbar", "anchor_y", fallback = 100)
        self.rawPanelXPositionData = themeConfig.theme.GetInt("Taskbar", "position_x", fallback = 98)
        self.rawPanelYPositionData = themeConfig.theme.GetInt("Taskbar", "position_y", fallback = 2)
        self.radius = 0 if self.enableBlur else themeConfig.theme.GetInt("Taskbar", "border_radius_px", fallback = 10)
        self.borderColor = themeConfig.theme.Get("Taskbar", "argb_border_color", fallback = "#FFFFFF33")
        self.borderWidth = themeConfig.theme.GetInt("Taskbar", "border_width_px", fallback = 1)

        rawBGColor = themeConfig.theme.Get("Taskbar", "argb_color", fallback = "#000000")

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

class Taskbar(QWidget):
    def __init__(self):
        super().__init__()

        self.TBConfig = TaskbarConfig()

        # =[> Connecting to theme config update event
        themeConfig.configUpdated.connect(self.UpdateStyles)

        self.widgetsManager = WidgetManager(self, "taskbar")

        self.UpdateStyles("init", ["ALL"])

        # =[> Window flags
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |  # No borders
            Qt.WindowType.Tool |                 # No alt+tab
            Qt.WindowType.WindowStaysOnTopHint   # always on top
        )
        #  [> Transperent bg attribute
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # =[> First init
        self.InitPanelComponents()

    def UpdateStyles(self, source, changedSections = None):
        # If initial run or data update required
        if "ALL" in changedSections or "Init" in source:
            pass
        # If section is changed
        elif "Taskbar" in changedSections:
            pass
        # if update for taskbar not required
        else:
            if self.widgetsManager.widgets:
                self.widgetsManager.ReloadStyles(changedSections)
            return

        self.TBConfig.Updater()

        # =[> Panel width
        try:
            if "%" in str(self.TBConfig.rawPanelWidthData):
                value = int(str(self.TBConfig.rawPanelWidthData).replace("%", ""))
                self.TBConfig.panelWidth = round(self.TBConfig.sw * (value / 100))
            else:
                self.TBConfig.panelWidth = int(str(self.TBConfig.rawPanelWidthData).replace("px", ""))
        except ValueError:
            self.TBConfig.panelWidth = self.TBConfig.sw

        # =[> Panel height
        try:
            if "%" in str(self.TBConfig.rawPanelHeightData):
                value = int(str(self.TBConfig.rawPanelHeightData).replace("%", ""))
                self.TBConfig.panelHeight = round(self.TBConfig.sh * (value / 100))
            else:
                self.TBConfig.panelHeight = int(str(self.TBConfig.rawPanelHeightData).replace("px", ""))
        except ValueError:
            self.TBConfig.panelHeight = round(self.TBConfig.sh * (2 / 100))

        # Reloading widgets if full update
        if "ALL" in changedSections:
            self.widgetsManager.LoadWidgets()

        # Updating widget styles
        if self.widgetsManager.widgets:
            self.widgetsManager.ReloadStyles(changedSections)

        # Flag for blur redrawing
        self.TBConfig.themeUpdatedState = True

        # "configOnly" flag
        if source != "init":
            self.InitPanelComponents()

    def Init(self):
        # Panel position
        panelXPosition = int(self.TBConfig.sw * (self.TBConfig.rawPanelXPositionData / 100))
        panelYPosition = int(self.TBConfig.sh * (self.TBConfig.rawPanelYPositionData / 100))

        # =[> Panel offset
        offsetX = int(self.TBConfig.panelWidth * (self.TBConfig.anchorX / 100))
        offsetY = int(self.TBConfig.panelHeight * (self.TBConfig.anchorY / 100))

        # Panel position with offset
        panelX = panelXPosition - offsetX
        panelY = panelYPosition - offsetY

        self.setGeometry(panelX, panelY, self.TBConfig.panelWidth, self.TBConfig.panelHeight)

    def InitPanelComponents(self):
        # Updating state
        self.TBConfig.themeUpdatedState = True
        # Self init
        self.Init()
        # Panel update
        self.update()

    # qwidget automatically call this btw
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # =[> Blur apply (the first and last update of the blur if the config is not updated in the future)
        if self.TBConfig.themeUpdatedState:
            if self.TBConfig.enableBlur:
                MakeBlur(self.winId(), True, self.TBConfig.blurMode, self.TBConfig.winBlurColor)
            else:
                MakeBlur(self.winId(), False)
            self.TBConfig.themeUpdatedState = False

        rect = QRectF(self.rect())  # Base

        # Border maker 2000
        if self.TBConfig.borderWidth > 0:
            pen = painter.pen()
            pen.setColor(QColor(self.TBConfig.borderColor))
            pen.setWidth(self.TBConfig.borderWidth)
            pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
            painter.setPen(pen)

            halfWidth = self.TBConfig.borderWidth / 2
            drawRect = rect.adjusted(halfWidth, halfWidth, -halfWidth, -halfWidth)
        else:
            painter.setPen(Qt.PenStyle.NoPen)
            drawRect = rect

        # Drawing background & border
        painter.setBrush(QBrush(self.TBConfig.qtBgColor))
        painter.drawRoundedRect(drawRect, self.TBConfig.radius, self.TBConfig.radius)
