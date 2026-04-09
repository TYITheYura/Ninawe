from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QBrush
from core.utils import MakeBlur
from core.managers import WidgetManager
from .config import TBConfig

class Taskbar(QWidget):
    def __init__(self):
        super().__init__()

        # =[> Connecting to theme config update event
        self.widgetsManager = WidgetManager(self, "taskbar")

        TBConfig.configUpdated.connect(self.UpdateStyles)
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
        # =[> Panel width
        try:
            if "%" in str(TBConfig.rawPanelWidthData):
                value = int(str(TBConfig.rawPanelWidthData).replace("%", ""))
                TBConfig.panelWidth = round(TBConfig.sw * (value / 100))
            else:
                TBConfig.panelWidth = int(str(TBConfig.rawPanelWidthData).replace("px", ""))
        except ValueError:
            TBConfig.panelWidth = TBConfig.sw

        # =[> Panel height
        try:
            if "%" in str(TBConfig.rawPanelHeightData):
                value = int(str(TBConfig.rawPanelHeightData).replace("%", ""))
                TBConfig.panelHeight = round(TBConfig.sh * (value / 100))
            else:
                TBConfig.panelHeight = int(str(TBConfig.rawPanelHeightData).replace("px", ""))
        except ValueError:
            TBConfig.panelHeight = round(TBConfig.sh * (2 / 100))

        # Reloading widgets if full update
        if "ALL" in changedSections:
            self.widgetsManager.LoadWidgets()

        # Updating widget styles
        if self.widgetsManager.widgets:
            self.widgetsManager.ReloadStyles(changedSections)

        # Flag for blur redrawing
        TBConfig.themeUpdatedState = True

        # "configOnly" flag
        if source != "init":
            self.InitPanelComponents()

    def Init(self):
        # Panel position
        panelXPosition = int(TBConfig.sw * (TBConfig.rawPanelXPositionData / 100))
        panelYPosition = int(TBConfig.sh * (TBConfig.rawPanelYPositionData / 100))

        # =[> Panel offset
        offsetX = int(TBConfig.panelWidth * (TBConfig.anchorX / 100))
        offsetY = int(TBConfig.panelHeight * (TBConfig.anchorY / 100))

        # Panel position with offset
        panelX = panelXPosition - offsetX
        panelY = panelYPosition - offsetY

        self.setGeometry(panelX, panelY, TBConfig.panelWidth, TBConfig.panelHeight)

    def InitPanelComponents(self):
        # Updating state
        TBConfig.themeUpdatedState = True
        # Self init
        self.Init()
        # Panel update
        self.update()

    # qwidget automatically call this btw
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # =[> Blur apply (the first and last update of the blur if the config is not updated in the future)
        if TBConfig.themeUpdatedState:
            if TBConfig.enableBlur:
                MakeBlur(self.winId(), True, TBConfig.blurMode, TBConfig.winBlurColor)
            else:
                MakeBlur(self.winId(), False)
            TBConfig.themeUpdatedState = False

        rect = QRectF(self.rect())  # Base

        # Border maker 2000
        if TBConfig.borderWidth > 0:
            pen = painter.pen()
            pen.setColor(QColor(TBConfig.borderColor))
            pen.setWidth(TBConfig.borderWidth)
            pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
            painter.setPen(pen)

            halfWidth = TBConfig.borderWidth / 2
            drawRect = rect.adjusted(halfWidth, halfWidth, -halfWidth, -halfWidth)
        else:
            painter.setPen(Qt.PenStyle.NoPen)
            drawRect = rect

        # Drawing background & border
        painter.setBrush(QBrush(TBConfig.qtBgColor))
        painter.drawRoundedRect(drawRect, TBConfig.radius, TBConfig.radius)

    def closeEvent(self, event):
        event.ignore()
