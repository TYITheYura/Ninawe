from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt
from core.config import config
from core.utils import InternalWindowFader

class TitleBar(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.parentWindow = parent
        self.startPos = None
        self.internalWindowFader = InternalWindowFader(self)
        self.InitUI()

    def InitUI(self):
        self.setFixedHeight(40)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(15, 0, 0, 0)
        self.layout.setSpacing(0)

        self.titleLabel = QLabel("Window title")
        self.layout.addWidget(self.titleLabel)

        self.layout.addStretch()

        self.closeBtn = QPushButton("✕")
        self.closeBtn.setObjectName("CloseButton")
        self.closeBtn.setFixedSize(40, 40)
        self.closeBtn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.closeBtn.clicked.connect(self.window().close)
        self.layout.addWidget(self.closeBtn)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.startPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.startPos is not None:
            delta = event.globalPosition().toPoint() - self.startPos
            mainWindow = self.window()
            mainWindow.move(mainWindow.pos() + delta)
            self.startPos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.startPos = None
