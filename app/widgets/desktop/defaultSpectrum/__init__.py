import os
import sys
import numpy as np
import soundcard as sc
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QRectF, QFileSystemWatcher
from PyQt6.QtGui import QPainter, QColor, QBrush
from core.config import ConfigWrapper
from core.config import config as selectedThemeConfig
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
import warnings
from core.utils import MakeLog

warnings.filterwarnings("ignore", message="data discontinuity in recording")

class WidgetConfig:
    def __init__(self):
        self.WConfig = ConfigWrapper()

        self.widgetPath = os.path.dirname(os.path.abspath(__file__))
        self.configPath = os.path.join(self.widgetPath, "config.ini")

        self.selectedConfig = None

        self.propsSection = "Spectrum.Preferences"
        self.styleSection = "Spectrum.Style"

        # Important sh#t 🥀
        self.SAMPLE_RATE = 44100
        self.CHUNK_SIZE = 2048
        self.BANDS = 150
        self.MIN_FREQ = 40
        self.MAX_FREQ = 20000

        self.sensitivity = 3
        self.smoothing = 10
        self.refreshRateTimer = 33.3
        self.scale = "log"
        self.attackCoefficient = 0.5
        self.rollOffCoefficient = 0.5
        self.EQStartCoef = 1.5
        self.EQEndCoef = 1
        self.peakHoldsEnabled = False

        self.peakHoldsColor = "#FFFFFFFF"
        self.peakHoldsFalloff = 0.5
        self.peakHoldsHeight = 2
        self.paddings = 2
        self.color = "#FFFFFFFF"
        self.bandMinHeight = 1

        self.running = True

        self.Updater()

    def Updater(self):
        self.WConfig.parser.read(self.configPath)

        # Config switcher
        if selectedThemeConfig.theme.GetSectionStatus(self.propsSection) and selectedThemeConfig.theme.GetSectionStatus(self.styleSection):
            self.selectedConfig = selectedThemeConfig.theme
        else:
            self.selectedConfig = self.WConfig

        self.SAMPLE_RATE = self.selectedConfig.GetInt(self.propsSection, "sample_rate", fallback = 44100)
        self.CHUNK_SIZE = self.selectedConfig.GetInt(self.propsSection, "chunk_size", fallback = 2048)
        self.BANDS = self.selectedConfig.GetInt(self.propsSection, "bands", fallback = 64)
        self.MIN_FREQ = self.selectedConfig.GetInt(self.propsSection, "min_freq", fallback = 40)
        self.MAX_FREQ = self.selectedConfig.GetInt(self.propsSection, "max_freq", fallback = 20000)
        self.sensitivity = self.selectedConfig.GetFloat(self.propsSection, "sensitivity", fallback = 3)
        self.smoothing = self.selectedConfig.GetInt(self.propsSection, "smoothing", fallback = 10)
        self.refreshRateTimer = round(1000 / self.selectedConfig.GetInt(self.propsSection, "refresh_rate", fallback = 30))
        self.scale = self.selectedConfig.Get(self.propsSection, "scale", fallback = "log").lower()
        self.attackCoefficient = self.selectedConfig.GetFloat(self.propsSection, "attack", fallback = 0.5)
        self.rollOffCoefficient = self.selectedConfig.GetFloat(self.propsSection, "roll_off", fallback = 0.5)
        self.EQStartCoef = self.selectedConfig.GetFloat(self.propsSection, "eq_start_coef", fallback = 1.0)
        self.EQEndCoef = self.selectedConfig.GetFloat(self.propsSection, "eq_end_coef", fallback = 1.5)
        self.peakHoldsEnabled = self.selectedConfig.GetBool(self.propsSection, "peak_holds_enabled", fallback = True)

        self.peakHoldsColor = self.selectedConfig.Get(self.styleSection, "peak_holds_color", fallback = "#FFFFFFFF")
        self.peakHoldsFalloff = self.selectedConfig.GetFloat(self.styleSection, "peak_holds_falloff", fallback = 0.5)
        self.peakHoldsHeight = self.selectedConfig.GetInt(self.styleSection, "peak_holds_height", fallback = 2)
        self.paddings = self.selectedConfig.GetInt(self.styleSection, "paddings", fallback = 2)
        self.color = self.selectedConfig.Get(self.styleSection, "color", fallback = "#FFFFFFFF")
        self.bandMinHeight = self.selectedConfig.GetFloat(self.styleSection, "band_min_height", fallback = 1)


WConfig = WidgetConfig()

class AudioThread(QThread):
    dataReadySignal = pyqtSignal(list)

    def __init__(self, parent = None):
        super().__init__(parent)
        self.needsReinit = True

    def TriggerReinit(self):
        self.needsReinit = True

    def run(self):
        while WConfig.running:
            try:
                defaultSpeaker = sc.default_speaker()
                mics = sc.all_microphones(include_loopback = True)
                mic = next((m for m in mics if defaultSpeaker.name in m.name), mics[0])

                MakeLog(f"[SpectrumWidget] Connected: {mic.name}")

                if self.needsReinit:
                    if WConfig.scale == "linear":
                        edges = np.linspace(WConfig.MIN_FREQ, WConfig.MAX_FREQ, WConfig.BANDS + 1)
                        self.bandFreqs = np.linspace(WConfig.MIN_FREQ, WConfig.MAX_FREQ, WConfig.BANDS)
                    else:
                        edges = np.logspace(np.log10(WConfig.MIN_FREQ), np.log10(WConfig.MAX_FREQ), WConfig.BANDS + 1)
                        self.bandFreqs = np.logspace(np.log10(WConfig.MIN_FREQ), np.log10(WConfig.MAX_FREQ), WConfig.BANDS)

                    self.FFTFreqs = np.fft.rfftfreq(WConfig.CHUNK_SIZE, 1.0 / WConfig.SAMPLE_RATE)
                    self.bandIndices = [np.searchsorted(self.FFTFreqs, edge) for edge in edges]
                    self.EQCurve = np.array([WConfig.EQStartCoef + (i / WConfig.BANDS) * WConfig.EQEndCoef for i in range(WConfig.BANDS)])
                    self.needsReinit = False

                with mic.recorder(samplerate=WConfig.SAMPLE_RATE, channels=1, blocksize=WConfig.CHUNK_SIZE) as recorder:
                    while WConfig.running:
                        if self.needsReinit:
                            break

                        data = recorder.record(numframes=WConfig.CHUNK_SIZE)[:, 0]
                        windowed = data * np.hanning(WConfig.CHUNK_SIZE)
                        FFTData = np.abs(np.fft.rfft(windowed))

                        if WConfig.smoothing > 0:
                            pre_kernel = np.hanning(3)
                            pre_kernel = pre_kernel / np.sum(pre_kernel)
                            pad_pre = len(pre_kernel) // 2
                            padded_FFT = np.pad(FFTData, (pad_pre, pad_pre), mode = 'edge')
                            FFTData = np.convolve(padded_FFT, pre_kernel, mode = 'valid')

                        bandValues = []
                        for i in range(WConfig.BANDS):
                            startIDx = self.bandIndices[i]
                            endIDx = self.bandIndices[i + 1]

                            if endIDx > startIDx + 1:
                                bandValue = np.mean(FFTData[startIDx:endIDx])
                            else:
                                bandValue = np.interp(self.bandFreqs[i], self.FFTFreqs, FFTData)

                            bandValues.append(np.sqrt(bandValue))

                        bandValues = np.array(bandValues) * self.EQCurve

                        if WConfig.smoothing > 2:
                            kernel = np.hanning(WConfig.smoothing)
                            kernel = kernel / np.sum(kernel)

                            pad_k = len(kernel) // 2
                            pad_rem = len(kernel) - 1 - pad_k
                            padded_bands = np.pad(bandValues, (pad_k, pad_rem), mode = 'edge')
                            smoothed = np.convolve(padded_bands, kernel, mode = 'valid')
                        else:
                            smoothed = bandValues

                        if np.max(smoothed) < 0.01:
                            smoothed = np.zeros(WConfig.BANDS)

                        self.dataReadySignal.emit(list(smoothed))

            except Exception as e:
                MakeLog(f"[Spectrum] Audio stream died: {e}")
                MakeLog("[Spectrum] Reconnecting in 2 seconds...")
                self.needsReinit = True
                self.msleep(2000)

    def stop(self):
        WConfig.running = False
        self.wait()

class SpectrumRenderer(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.currentHeights = np.zeros(WConfig.BANDS)
        self.targetHeights = np.zeros(WConfig.BANDS)
        self.peakHeights = np.zeros(WConfig.BANDS)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def ReinitArrays(self):
        self.currentHeights = np.zeros(WConfig.BANDS)
        self.targetHeights = np.zeros(WConfig.BANDS)
        self.peakHeights = np.zeros(WConfig.BANDS)

    def UpdateData(self, newData):
        if len(newData) != len(self.targetHeights):
            return

        self.targetHeights = np.clip(np.array(newData) * WConfig.sensitivity, 0, 100)

        if np.max(self.targetHeights) > 0 and not self.parent().renderTimer.isActive():
            self.parent().renderTimer.start(WConfig.refreshRateTimer)

    def paintEvent(self, event):
        w = self.width()
        h = self.height()

        if w <= 0 or h <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        diff = self.targetHeights - self.currentHeights
        rates = np.where(diff > 0, WConfig.attackCoefficient, WConfig.rollOffCoefficient)
        self.currentHeights += diff * rates

        if WConfig.peakHoldsEnabled:
            self.peakHeights = np.maximum(self.peakHeights, self.currentHeights)
            self.peakHeights -= WConfig.peakHoldsFalloff
            self.peakHeights = np.clip(self.peakHeights, 0, 100)

        canSleep = np.max(self.targetHeights) == 0 and np.max(self.currentHeights) < 0.1
        if WConfig.peakHoldsEnabled:
            canSleep = canSleep and np.max(self.peakHeights) < 0.1

        if canSleep:
            self.currentHeights.fill(0)
            if WConfig.peakHoldsEnabled:
                self.peakHeights.fill(0)

            if self.parent().renderTimer.isActive():
                self.parent().renderTimer.stop()

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

class Widget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SpectrumWidget")

        self.setStyleSheet("""
            QWidget#SpectrumWidget {
                background-color: rgba(0, 0, 0, 100);
                border-radius: 10px;
            }
        """)

        layout = QVBoxLayout(self)

        self.renderer = SpectrumRenderer(self)
        layout.addWidget(self.renderer)

        selectedThemeConfig.configUpdated.connect(self.OnGlobalConfigChanged)

        self.localWatcher = QFileSystemWatcher()
        if os.path.exists(WConfig.configPath):
            self.localWatcher.addPath(WConfig.configPath)
        self.localWatcher.fileChanged.connect(self.OnLocalConfigChanged)

        self.audioThreadObj = AudioThread(self)
        self.audioThreadObj.dataReadySignal.connect(self.renderer.UpdateData)
        self.audioThreadObj.start()

        self.renderTimer = QTimer(self)
        self.renderTimer.timeout.connect(self.renderer.update)
        self.renderTimer.start(WConfig.refreshRateTimer)

    def OnGlobalConfigChanged(self, source, changedSections):
        if "ALL" not in changedSections and WConfig.propsSection not in changedSections and WConfig.styleSection not in changedSections:
            return

        MakeLog("[Log] [Desktop.Spectrum] | Global config changed. Applying.")
        self.ApplyNewConfig()

    def OnLocalConfigChanged(self, path):
        if path not in self.localWatcher.files() and os.path.exists(path):
            self.localWatcher.addPath(path)

        MakeLog(f"[Log] [Desktop.Spectrum] | LC changed: {path}")
        self.ApplyNewConfig()

    def ApplyNewConfig(self):
        WConfig.Updater()
        self.renderTimer.stop()
        self.renderTimer.start(WConfig.refreshRateTimer)
        self.renderer.ReinitArrays()
        self.audioThreadObj.TriggerReinit()

    def deleteLater(self):
        if hasattr(self, 'audioThreadObj'):
            self.audioThreadObj.stop()
        super().deleteLater()
