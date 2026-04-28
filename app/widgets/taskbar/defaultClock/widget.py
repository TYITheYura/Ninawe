from PyQt6.QtWidgets import QLabel, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QDateTime, QTimer
from PyQt6.QtGui import QColor
from .config import WConfig
from ui.taskbar import TBConfig

class Widget(QLabel):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setObjectName("ClockWidget")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        WConfig.configUpdated.connect(self.UpdateStyles)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.UpdateTime)

        self.UpdateStyles()

    def UpdateStyles(self, source = None, changedSections = None):
        if WConfig.visibility:
            self.show()
            if not self.timer.isActive():
                self.timer.start(1000)
        else:
            self.hide()
            self.timer.stop()
            return

        self.setStyleSheet(f"""
            color: {WConfig.fontColor};
            font-family: '{WConfig.fontFamily}';
            font-size: {WConfig.fontSize}pt;
            background-color: transparent;
        """)

        self.UpdateTime()
        self.adjustSize()
        currentClockWidth = max(self.width(), WConfig.clockWidth)

        shadowPadding = 0
        if WConfig.fontShadow:
            shadowPadding = 4
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(5)
            shadow.setXOffset(1)
            shadow.setYOffset(1)
            shadow.setColor(QColor(0, 0, 0, 150))
            self.setGraphicsEffect(shadow)
        else:
            self.setGraphicsEffect(None)

        clockX = round(
            TBConfig.panelWidth * (WConfig.clockPosition / 100) -
            (currentClockWidth * (WConfig.clockAlign / 100)) +
            WConfig.clockLeftMargin - WConfig.clockRightMargin
        )

        self.setGeometry(clockX, shadowPadding, currentClockWidth, TBConfig.panelHeight - (shadowPadding * 2))

    def UpdateTime(self):
        currentTime = QDateTime.currentDateTime()
        self.setText(currentTime.toString(WConfig.timeFormat))
