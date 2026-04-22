from core.utils import GetWindowSnapshot, GetWindowIcon, LIVE_THUMBNAIL_CACHE, MakeBlur, InternalWindowFader
from PyQt6.QtWidgets import QWidget, QApplication, QGridLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPixmap
from .card import ThumbnailCard
import win32gui
import math

class AppExposeWidget(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setObjectName("AppExpose")

        self.internalWindowFader = InternalWindowFader(self)

        self.setWindowFlags(
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        screenGeometry = QApplication.primaryScreen().geometry()
        self.setGeometry(screenGeometry)

        self.layout = QGridLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.setSpacing(40)

        MakeBlur(self.winId(), True, 1, "#22FFFFFF")

    def ShowGroup(self, windowsList):
        cols = math.ceil(math.sqrt(len(windowsList)))
        if cols == 0:
            cols = 1

        row, col = 0, 0

        for w in windowsList:
            hwnd = w["hwnd"]
            title = w["title"]
            isMinimized = win32gui.IsIconic(hwnd)
            isMinimizedVisual = False
            pixmap = None

            if hwnd in LIVE_THUMBNAIL_CACHE:
                pixmap = LIVE_THUMBNAIL_CACHE[hwnd]
            elif isMinimized:
                pixmap = GetWindowIcon(hwnd)
                isMinimizedVisual = True
            else:
                rawPixmap = GetWindowSnapshot(hwnd)
                if rawPixmap and not rawPixmap.isNull():
                    pixmap = rawPixmap.scaledToWidth(360, Qt.TransformationMode.SmoothTransformation)
                    LIVE_THUMBNAIL_CACHE[hwnd] = pixmap
                else:
                    pixmap = GetWindowIcon(hwnd)
                    isMinimizedVisual = True

            if not pixmap or pixmap.isNull():
                pixmap = QPixmap(360, 240)
                pixmap.fill(QColor("#333333"))
                isMinimizedVisual = True

            appIconPixmap = GetWindowIcon(hwnd)

            card = ThumbnailCard(hwnd, title, pixmap, isMinimizedVisual, appIconPixmap, self)
            self.layout.addWidget(card, row, col)

            col += 1
            if col >= cols:
                col = 0
                row += 1

        self.show()
        self.setFocus()
        self.internalWindowFader.FadeIn()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#01000000"))
        painter.drawRect(self.rect())

    def mousePressEvent(self, event):
        event.accept()
        self.CloseExpose()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.CloseExpose()
        super().keyPressEvent(event)

    def CloseExpose(self):
        self.internalWindowFader.FadeOut(onFinished = self.deleteLater)
