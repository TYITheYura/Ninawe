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

    def UpdateStyles(self, source, changedSections = None):
        # Reloading widgets if full update
        if "ALL" in changedSections:
            self.widgetsManager.LoadWidgets()

        # Updating widget styles
        if self.widgetsManager.widgets:
            self.widgetsManager.ReloadStyles(changedSections)

        self.setGeometry(TBConfig.panelX, TBConfig.panelY, TBConfig.panelWidth, TBConfig.panelHeight)

        # Flag for blur redrawing
        TBConfig.themeUpdatedState = True

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
