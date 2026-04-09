import os
import numpy as np
import soundcard as sc
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import QThread, pyqtSignal, QFileSystemWatcher
from core.config import config as selectedThemeConfig
import warnings
from core.utils import MakeLog
from .config import WConfig

warnings.filterwarnings("ignore", message = "data discontinuity in recording")

class AudioThread(QThread):
    dataReadySignal = pyqtSignal(object)

    def __init__(self, parent = None):
        super().__init__(parent)
        self.needsReinit = True
        self.isRunning = True

    def TriggerReinit(self):
        self.needsReinit = True

    def run(self):
        # From this point on, a lot of incomprehensible code begins. Be careful.
        while self.isRunning:
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

                    self.weightMatrix = np.zeros((WConfig.BANDS, len(self.FFTFreqs)))

                    for i in range(WConfig.BANDS):
                        startIDx = self.bandIndices[i]
                        endIDx = self.bandIndices[i + 1]

                        if endIDx > startIDx + 1:
                            self.weightMatrix[i, startIDx:endIDx] = 1.0 / (endIDx - startIDx)
                        else:
                            targetFrequency = self.bandFreqs[i]
                            idx = np.searchsorted(self.FFTFreqs, targetFrequency)

                            if idx == 0:
                                self.weightMatrix[i, 0] = 1.0
                            elif idx >= len(self.FFTFreqs):
                                self.weightMatrix[i, -1] = 1.0
                            else:
                                x0, x1 = self.FFTFreqs[idx - 1], self.FFTFreqs[idx]
                                dx = x1 - x0

                                if dx > 0:
                                    w1 = (targetFrequency - x0) / dx
                                    self.weightMatrix[i, idx - 1] = 1.0 - w1
                                    self.weightMatrix[i, idx] = w1
                                else:
                                    self.weightMatrix[i, idx] = 1.0

                    self.needsReinit = False

                with mic.recorder(samplerate = WConfig.SAMPLE_RATE, channels = 1, blocksize = WConfig.CHUNK_SIZE) as recorder:
                    while self.isRunning:
                        if self.needsReinit:
                            break

                        data = recorder.record(numframes = WConfig.CHUNK_SIZE)[:, 0]

                        if np.max(np.abs(data)) == 0:
                            self.dataReadySignal.emit(np.zeros(WConfig.BANDS))
                            continue

                        windowed = data * np.hanning(WConfig.CHUNK_SIZE)
                        FFTData = np.abs(np.fft.rfft(windowed))

                        if WConfig.smoothing > 0:
                            preKernel = np.hanning(3)
                            preKernel = preKernel / np.sum(preKernel)
                            prePadding = len(preKernel) // 2
                            paddedFFT = np.pad(FFTData, (prePadding, prePadding), mode = 'edge')
                            FFTData = np.convolve(paddedFFT, preKernel, mode = 'valid')

                        bandValues = self.weightMatrix.dot(FFTData)
                        bandValues = np.sqrt(bandValues) * self.EQCurve

                        if WConfig.smoothing > 2:
                            kernel = np.hanning(WConfig.smoothing)
                            kernel = kernel / np.sum(kernel)

                            paddingLeft = len(kernel) // 2
                            paddingRight = len(kernel) - 1 - paddingLeft
                            paddedBands = np.pad(bandValues, (paddingLeft, paddingRight), mode = 'edge')
                            smoothed = np.convolve(paddedBands, kernel, mode = 'valid')
                        else:
                            smoothed = bandValues

                        if np.max(smoothed) < 0.01:
                            smoothed = np.zeros(WConfig.BANDS)

                        self.dataReadySignal.emit(smoothed)

            except Exception as e:
                MakeLog(f"[Spectrum] Audio stream died: {e}\n[Spectrum] Reconnecting in 2 seconds...")
                self.needsReinit = True
                self.msleep(2000)

    def stop(self):
        self.isRunning = False
        self.wait()

class Widget(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setObjectName("SpectrumWidget")

        self.setStyleSheet("""
            QWidget#SpectrumWidget {
                background-color: transparent;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if WConfig.HARDWARE_ACCELERATION:
            from .rendererGL import SpectrumRendererGLEngine
            self.renderer = SpectrumRendererGLEngine(self)
            MakeLog("[Spectrum] Started with GPU (OpenGL) Engine")
        else:
            from .rendererDefault import SpectrumRendererEngine
            self.renderer = SpectrumRendererEngine(self)
            MakeLog("[Spectrum] Started with CPU (QPainter) Engine")

        layout.addWidget(self.renderer)

        selectedThemeConfig.configUpdated.connect(self.OnGlobalConfigChanged)

        self.localWatcher = QFileSystemWatcher()

        if os.path.exists(WConfig.configPath):
            self.localWatcher.addPath(WConfig.configPath)

        self.localWatcher.fileChanged.connect(self.OnLocalConfigChanged)

        self.audioThreadObj = AudioThread(self)
        self.audioThreadObj.dataReadySignal.connect(self.renderer.UpdateData)
        self.audioThreadObj.start()

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
        self.renderer.renderTimer.stop()
        self.renderer.ReinitArrays()
        self.audioThreadObj.TriggerReinit()
        self.renderer.renderTimer.start(WConfig.refreshRateTimer)

    def deleteLater(self):
        if hasattr(self, 'audioThreadObj'):
            self.audioThreadObj.stop()
        super().deleteLater()
