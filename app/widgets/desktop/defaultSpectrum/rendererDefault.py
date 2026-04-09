import numpy as np
from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtCore import Qt, QRectF, QTimer, QElapsedTimer
from PyQt6.QtGui import QPainter, QColor, QBrush
from .config import WConfig

class SpectrumRendererEngine(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.currentHeights = np.zeros(WConfig.BANDS)
        self.targetHeights = np.zeros(WConfig.BANDS)
        self.peakHeights = np.zeros(WConfig.BANDS)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.renderTimer = QTimer(self)
        self.renderTimer.timeout.connect(self.update)

        self.timeTracker = QElapsedTimer()
        self.timeTracker.start()

    def ReinitArrays(self):
        self.currentHeights = np.zeros(WConfig.BANDS)
        self.targetHeights = np.zeros(WConfig.BANDS)
        self.peakHeights = np.zeros(WConfig.BANDS)

    def UpdateData(self, newData):
        if len(newData) != len(self.targetHeights):
            return

        self.targetHeights = np.clip(np.array(newData) * WConfig.sensitivity, 0, 100)

        if np.max(self.targetHeights) > 0 and not self.renderTimer.isActive():
            self.renderTimer.start(WConfig.refreshRateTimer)

    def paintEvent(self, event):
        w = self.width()
        h = self.height()

        if w <= 0 or h <= 0:
            return

        painter = QPainter(self)
        # painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        deltaTime = self.timeTracker.restart()
        timeScale = min(deltaTime / WConfig.physicsRefreshRateTimer, 3.0)

        diff = self.targetHeights - self.currentHeights

        attack = min(WConfig.attackCoefficient * timeScale, 1.0)
        decay = min(WConfig.rollOffCoefficient * timeScale, 1.0)

        rates = np.where(diff > 0, attack, decay)

        self.currentHeights += diff * rates

        if WConfig.peakHoldsEnabled:
            self.peakHeights -= (WConfig.peakHoldsFalloff * timeScale)
            self.peakHeights = np.maximum(self.peakHeights, self.currentHeights)
            self.peakHeights = np.clip(self.peakHeights, 0, 100)

        canSleep = np.max(self.targetHeights) == 0 and np.max(self.currentHeights) < 0.1
        if WConfig.peakHoldsEnabled:
            canSleep = canSleep and np.max(self.peakHeights) < 0.1

        if canSleep:
            self.currentHeights.fill(0)
            if WConfig.peakHoldsEnabled:
                self.peakHeights.fill(0)

            if self.renderTimer.isActive():
                self.renderTimer.stop()

        barWidth = w / WConfig.BANDS
        rectWidth = barWidth - WConfig.paddings
        XCoords = np.arange(WConfig.BANDS) * barWidth + (WConfig.paddings / 2)

        barHeightsPx = (self.currentHeights / 100) * h
        barHeightsPx = np.clip(barHeightsPx, WConfig.bandMinHeight, None)
        YCoordsBars = h - barHeightsPx

        rects = [QRectF(x, y, rectWidth, bh) for x, y, bh in zip(XCoords, YCoordsBars, barHeightsPx)]

        painter.setBrush(QBrush(QColor(WConfig.color)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRects(rects)

        if WConfig.peakHoldsEnabled:
            peakHeightsPx = (self.peakHeights / 100) * h
            peakHeightsPx = np.clip(peakHeightsPx, WConfig.bandMinHeight, None)

            YCoordsPeaks = h - peakHeightsPx - WConfig.peakHoldsHeight

            peakRects = [QRectF(x, y, rectWidth, WConfig.peakHoldsHeight) for x, y in zip(XCoords, YCoordsPeaks)]

            painter.setBrush(QBrush(QColor(WConfig.peakHoldsColor)))
            painter.drawRects(peakRects)
