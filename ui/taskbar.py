from PyQt6.QtWidgets import QWidget, QApplication, QLabel, QHBoxLayout, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QRect, QTime, QTimer, QRectF
from PyQt6.QtGui import QPainter, QColor, QBrush, QFont
from core.config import config as themeConfig
from core.utils import LoadFont, MakeBlur
from core.widgetManager import WidgetManager
class Taskbar(QWidget):
    def __init__(self):
        super().__init__()
        # =[> Connecting to theme config update event
        themeConfig.themeUpdated.connect(self.UpdateStyles)
        self.panelBackgroundColor = self.enableBlur = self.radius = self.borderColor = self.borderWidth = self.blurMode = None
        self.sw = self.sh = None
        self.anchorX = self.anchorY = None
        self.panelWidth = self.panelHeight = None
        self.rawPanelXPositionData = self.rawPanelYPositionData = None
        self.themeUpdatedState = True

        self.widgetsManager = WidgetManager(self, "taskbar")

        self.UpdateStyles(configOnly = True)
        
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

    def UpdateStyles(self, changedSections = None, configOnly = False):
        if changedSections != None and len(changedSections) > 0:
            if "Taskbar" not in changedSections:
                return

        # =[> Data from config
        rawBGColor = themeConfig.theme.Get("Taskbar", "argb_color", fallback = "#000000")
        self.enableBlur = themeConfig.theme.GetBool("Taskbar", "blur_enabled", fallback = False)
        self.blurMode = themeConfig.theme.GetInt("Taskbar", "blur_mode", fallback = 4)
        
        # =[> Panel color
        if self.enableBlur and self.blurMode == 1:
            # config blur mode: 1 (4 - acrylic)
            self.qtBgColor = QColor(0, 0, 0, 0)
            self.winBlurColor = rawBGColor
        else:
            # config blur mode: 0 (3 - default) / enable_blur = False
            self.qtBgColor = QColor(rawBGColor)
            self.winBlurColor = "#00000000"

        # Calculation the width and height of the panel
        screen = QApplication.primaryScreen().geometry()
        self.sw, self.sh = screen.width(), screen.height()

        # =[> Panel width
        rawPanelWidthData = themeConfig.theme.Get("Taskbar", "width", fallback = 90)
        try:
            if "%" in str(rawPanelWidthData):
                value = int(str(rawPanelWidthData).replace("%", ""))
                self.panelWidth = round(self.sw * (value / 100))
            else:
                self.panelWidth = int(str(rawPanelWidthData).replace("px", ""))
        except ValueError:
            self.panelWidth = self.sw

        # =[> Panel height
        rawPanelHeightData = themeConfig.theme.Get("Taskbar", "height", fallback = 30)
        try:
            if "%" in str(rawPanelHeightData):
                value = int(str(rawPanelHeightData).replace("%", ""))
                self.panelHeight = round(self.sh * (value / 100))
            else:
                self.panelHeight = int(str(rawPanelHeightData).replace("px", ""))
        except ValueError:
            self.panelHeight = round(self.sh * (2 / 100))

        # =[> Anchors getting
        self.anchorX = themeConfig.theme.GetInt("Taskbar", "anchor_x", fallback = 50)
        self.anchorY = themeConfig.theme.GetInt("Taskbar", "anchor_y", fallback = 100)

        # =[> Panel position
        self.rawPanelXPositionData = themeConfig.theme.GetInt("Taskbar", "position_x", fallback = 98)
        self.rawPanelYPositionData = themeConfig.theme.GetInt("Taskbar", "position_y", fallback = 2)

        # =[> Other props
        self.radius = 0 if self.enableBlur else themeConfig.theme.GetInt("Taskbar", "border_radius_px", fallback = 10)
        self.borderColor = themeConfig.theme.Get("Taskbar", "argb_border_color", fallback = "#FFFFFF33")
        self.borderWidth = themeConfig.theme.GetInt("Taskbar", "border_width_px", fallback = 1)
        self.widgetsManager.LoadWidgets()

        if self.widgetsManager.widgets:
            self.widgetsManager.panelWidth = self.panelWidth
            self.widgetsManager.panelHeight = self.panelHeight
            self.widgetsManager.ReloadStyles()

        if not configOnly:
            self.InitPanelComponents()

    def Init(self):
        # Panel position
        panelXPosition = int(self.sw * (self.rawPanelXPositionData / 100))
        panelYPosition = int(self.sh * (self.rawPanelYPositionData / 100))

        # =[> Panel offset
        offsetX = int(self.panelWidth * (self.anchorX / 100))
        offsetY = int(self.panelHeight * (self.anchorY / 100))

        # Panel position with offset
        panelX = panelXPosition - offsetX
        panelY = panelYPosition - offsetY

        self.setGeometry(panelX, panelY, self.panelWidth, self.panelHeight)

    def InitPanelComponents(self):
        # Updating state
        self.themeUpdatedState = True
        # Self init
        self.Init()
        # Panel update
        self.update()

    # qwidget automatically call this btw
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # =[> Blur apply (the first and last update of the blur if the config is not updated in the future)
        if self.themeUpdatedState:
            if self.enableBlur:
                MakeBlur(self.winId(), True, self.blurMode, self.winBlurColor)
            else:
                MakeBlur(self.winId(), False)
            self.themeUpdatedState = False

        rect = QRectF(self.rect()) # Base
        
        # Border maker 2000
        if self.borderWidth > 0:
            pen = painter.pen()
            pen.setColor(QColor(self.borderColor))
            pen.setWidth(self.borderWidth)
            pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
            painter.setPen(pen)

            halfWidth = self.borderWidth / 2
            drawRect = rect.adjusted(halfWidth, halfWidth, -halfWidth, -halfWidth)
        else:
            painter.setPen(Qt.PenStyle.NoPen)
            drawRect = rect

        # Drawing background
        painter.setBrush(QBrush(self.qtBgColor))
        
        # Drawing border
        painter.drawRoundedRect(drawRect, self.radius, self.radius)