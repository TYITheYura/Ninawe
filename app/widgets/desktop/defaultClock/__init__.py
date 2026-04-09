from PyQt6.QtWidgets import QLabel, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QTime, QTimer
from PyQt6.QtGui import QColor

class Widget(QLabel):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setObjectName("defaultClock")

        self.minWidth = 350
        self.minHeight = 100

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            color: white;
            font-family: 'Segoe UI', sans-serif;
            font-size: 64px;
            font-weight: bold;
            background-color: transparent;
            border-radius: 15px;
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setXOffset(2)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 180))
        self.setGraphicsEffect(shadow)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.UpdateTime)
        self.timer.start(1000)

        self.UpdateTime()

    def UpdateTime(self):
        currentTime = QTime.currentTime()
        self.setText(currentTime.toString("HH:mm:ss"))
