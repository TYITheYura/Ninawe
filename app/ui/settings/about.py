import os
import time
import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsDropShadowEffect
from PyQt6.QtGui import QPainter, QColor, QPen, QPolygonF, QPixmap
from PyQt6.QtCore import Qt, QTimer, QPointF
from core.config import BASE_DIR, config as configurator

class WaveBackground(QWidget):
    def __init__(self, parent = None, cols = 40, rows = 20):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.mouseX = -1000
        self.mouseY = -1000
        self.startTime = time.perf_counter()
        self.cols = cols
        self.rows = rows
        self.numPoints = cols * rows

        nx = np.linspace(0, 1, cols)
        ny = np.linspace(0, 1, rows)
        NX, NY = np.meshgrid(nx, ny)

        self.baseNX = NX.flatten()
        self.baseNY = NY.flatten()
        self.phaseOffsets = self.baseNX * 12.0
        self.lastW = 0
        self.lastH = 0

        self.cacheBaseX = np.zeros(self.numPoints)
        self.cacheBaseY = np.zeros(self.numPoints)
        self.waveY = np.zeros(self.numPoints)
        self.finalX = np.zeros(self.numPoints)
        self.finalY = np.zeros(self.numPoints)
        self.dx = np.zeros(self.numPoints)
        self.dy = np.zeros(self.numPoints)
        self.distSQ = np.zeros(self.numPoints)

        self.tempBuffer = np.zeros(self.numPoints)

        self.dotColor = QColor(127, 127, 127, 127)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.OnTick)

    def SetTheme(self, themeMode):
        if themeMode == "white":
            self.dotColor = QColor(0, 0, 0, 63)
        else:
            self.dotColor = QColor(255, 255, 255, 63)
        self.update()

    def showEvent(self, e):
        self.timer.start(25)
        super().showEvent(e)

    def hideEvent(self, e):
        self.timer.stop()
        super().hideEvent(e)

    def mouseMoveEvent(self, e):
        self.mouseX, self.mouseY = e.pos().x(), e.pos().y()

    def leaveEvent(self, e):
        self.mouseX = -1000

    def OnTick(self):
        self.update()

    def paintEvent(self, event):
        w, h = self.width(), self.height()
        if w == 0:
            return

        if w != self.lastW or h != self.lastH:
            np.multiply(self.baseNX, w, out = self.cacheBaseX)
            np.multiply(self.baseNY, h, out = self.cacheBaseY)
            self.lastW = w
            self.lastH = h

        currentTime = time.perf_counter() - self.startTime
        waveTime = currentTime * 1.5

        np.add(self.phaseOffsets, waveTime, out = self.waveY)
        np.sin(self.waveY, out = self.waveY)
        np.multiply(self.waveY, 15.0, out = self.waveY)
        np.add(self.cacheBaseY, self.waveY, out = self.waveY)

        np.copyto(self.finalX, self.cacheBaseX)
        np.copyto(self.finalY, self.waveY)

        np.subtract(self.cacheBaseX, self.mouseX, out = self.dx)
        np.subtract(self.waveY, self.mouseY, out = self.dy)

        np.square(self.dx, out = self.distSQ)
        np.square(self.dy, out = self.tempBuffer)
        np.add(self.distSQ, self.tempBuffer, out = self.distSQ)

        mask = self.distSQ < 120000.0
        if np.any(mask):
            distNear = np.sqrt(self.distSQ[mask])
            np.maximum(distNear, 0.1, out = distNear)

            factor = (np.exp(self.distSQ[mask] * -0.00004545) * 90.0) / distNear
            self.finalX[mask] += self.dx[mask] * factor
            self.finalY[mask] += self.dy[mask] * factor

        poly = QPolygonF(map(QPointF, self.finalX, self.finalY))
        painter = QPainter(self)
        pen = QPen(self.dotColor)
        pen.setWidth(5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawPoints(poly)


class AboutTab(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.uiLayout = QVBoxLayout(self)
        self.uiLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.uiLayout.setSpacing(0)

        self.logoLabel = QLabel()
        self.logoLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logoLabel.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        imagePath = os.path.join(BASE_DIR, "app", "assets", "logo", "logo.png")
        if os.path.exists(imagePath):
            pixmap = QPixmap(imagePath)
            scaledPixmap = pixmap.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.logoLabel.setPixmap(scaledPixmap)
        else:
            self.logoLabel.setText("Ninawe")

        self.subtitle = QLabel(
            "Ninawe Is Not A Windows Shell\nVersion: Well Done 1.2"
        )
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        self.logoShadow = QGraphicsDropShadowEffect(self.logoLabel)
        self.logoShadow.setBlurRadius(30)
        self.logoShadow.setXOffset(0)
        self.logoShadow.setYOffset(0)
        self.logoLabel.setGraphicsEffect(self.logoShadow)

        self.subtitleShadow = QGraphicsDropShadowEffect(self.subtitle)
        self.subtitleShadow.setBlurRadius(5)
        self.subtitleShadow.setXOffset(0)
        self.subtitleShadow.setYOffset(0)
        self.subtitle.setGraphicsEffect(self.subtitleShadow)

        self.uiLayout.addWidget(self.logoLabel)
        self.uiLayout.addWidget(self.subtitle)

        self.waveEngine = WaveBackground(self)
        self.waveEngine.resize(self.size())

        self.waveEngine.lower()
        self.waveEngine.show()

        self.ApplyTheme()
        configurator.configUpdated.connect(self.OnGlobalConfigChanged)

    def ApplyTheme(self):

        themeMode = configurator.app.Get("Theme", "settings_theme", fallback="black")

        if themeMode == "white":
            textColor = "#333333"
            subColor = "#555555"
            shadowColor = QColor(0, 0, 0, 127)
        else:
            textColor = "#BBBBBB"
            subColor = "#AAAAAA"
            shadowColor = QColor(255, 255, 255, 127)

        if self.logoLabel.text():
            self.logoLabel.setStyleSheet(f"font-size: 42px; font-weight: bold; color: {textColor};")
        self.subtitle.setStyleSheet(f"font-size: 14px; color: {subColor};")

        self.logoShadow.setColor(shadowColor)
        self.subtitleShadow.setColor(shadowColor)

        if hasattr(self, 'waveEngine'):
            self.waveEngine.SetTheme(themeMode)

    def OnGlobalConfigChanged(self, source, changedSections):
        if source == "app" and ("ALL" in changedSections or "Theme" in changedSections):
            self.ApplyTheme()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'waveEngine'):
            self.waveEngine.resize(self.size())
