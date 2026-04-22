from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtCore import Qt
from core.utils import ToggleWindow
import win32gui
import win32con

class ThumbnailCard(QWidget):
    def __init__(self, hwnd, title, pixmap, isMinimizedVisual, appIconPixmap, parent = None):
        super().__init__(parent)
        self.hwnd = hwnd
        self.exposeParent = parent

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setProperty("isHovered", "false")

        cardWidth = 360
        cardHeight = 240
        self.setFixedSize(cardWidth, cardHeight)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.imageLabel = QLabel()
        self.imageLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if isMinimizedVisual:
            scaledPixmap = pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        else:
            scaledPixmap = pixmap.scaled(cardWidth - 20, cardHeight - 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        self.imageLabel.setPixmap(scaledPixmap)

        bottomLayout = QHBoxLayout()
        bottomLayout.setContentsMargins(0, 0, 0, 0)
        bottomLayout.setSpacing(8)
        bottomLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.iconLabel = QLabel()
        self.iconLabel.setFixedSize(18, 18)
        if appIconPixmap and not appIconPixmap.isNull():
            self.iconLabel.setPixmap(appIconPixmap.scaled(18, 18, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

        self.titleLabel = QLabel()
        metrics = QFontMetrics(self.titleLabel.font())
        elidedTitle = metrics.elidedText(title, Qt.TextElideMode.ElideRight, cardWidth - 60)
        self.titleLabel.setText(elidedTitle)

        bottomLayout.addStretch()
        bottomLayout.addWidget(self.iconLabel)
        bottomLayout.addWidget(self.titleLabel)
        bottomLayout.addStretch()

        layout.addWidget(self.imageLabel)
        layout.addLayout(bottomLayout)

        self.closeBtn = QPushButton("×", self)
        self.closeBtn.setObjectName("ExposeCloseBtn")
        self.closeBtn.setFixedSize(24, 24)
        self.closeBtn.move(cardWidth - 34, 10)
        self.closeBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.closeBtn.clicked.connect(self.CloseWindow)

        self.closeBtn.hide()

        self.setStyleSheet("""
            ThumbnailCard {
                background-color: #33000000;
                border-radius: 10px;
                border: 1px solid transparent;
            }
            ThumbnailCard[isHovered="true"] {
                background-color: #55FFFFFF;
                border: 1px solid #88FFFFFF;
            }
            QLabel {
                color: white;
                font-size: 14px;
                background-color: transparent;
            }
            QPushButton#ExposeCloseBtn {
                background-color: #66000000;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                padding-bottom: 2px;
            }
            QPushButton#ExposeCloseBtn:hover {
                background-color: #FF4444;
            }
        """)

    def enterEvent(self, event):
        self.setProperty("isHovered", "true")
        self.closeBtn.show()
        self.style().unpolish(self)
        self.style().polish(self)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setProperty("isHovered", "false")
        self.closeBtn.hide()
        self.style().unpolish(self)
        self.style().polish(self)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            event.accept()
            self.exposeParent.CloseExpose()
            ToggleWindow(self.hwnd)

    def CloseWindow(self):
        win32gui.PostMessage(self.hwnd, win32con.WM_CLOSE, 0, 0)

        self.close()

        visibleCards = 0
        for i in range(self.exposeParent.layout.count()):
            item = self.exposeParent.layout.itemAt(i)
            if item and item.widget() and item.widget().isVisible():
                visibleCards += 1
        if visibleCards == 0:
            self.exposeParent.CloseExpose()
