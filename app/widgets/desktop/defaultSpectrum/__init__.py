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

    def __init__(self, parent=None):
        super().__init__(parent)
        self.needsReinit = True
        self.isRunning = True

    def TriggerReinit(self):
        self.needsReinit = True

    def BuildMatrices(self):
        if WConfig.scale == "linear":
            edges = np.linspace(WConfig.MIN_FREQ, WConfig.MAX_FREQ, WConfig.BANDS + 1)
            self.bandFreqs = np.linspace(WConfig.MIN_FREQ, WConfig.MAX_FREQ, WConfig.BANDS)
        else:
            edges = np.logspace(np.log10(WConfig.MIN_FREQ), np.log10(WConfig.MAX_FREQ), WConfig.BANDS + 1)
            self.bandFreqs = np.logspace(np.log10(WConfig.MIN_FREQ), np.log10(WConfig.MAX_FREQ), WConfig.BANDS)

        self.FFTFreqs = np.fft.rfftfreq(WConfig.CHUNK_SIZE, 1.0 / WConfig.SAMPLE_RATE)
        self.bandIndices = [np.searchsorted(self.FFTFreqs, edge) for edge in edges]
        self.EQCurve = np.linspace(
            WConfig.EQStartCoef,
            WConfig.EQEndCoef,
            WConfig.BANDS,
            dtype = np.float32
        )

        self.weightMatrix = np.zeros((WConfig.BANDS, len(self.FFTFreqs)), dtype = np.float32)
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

        self.zeroArray = np.zeros(WConfig.BANDS, dtype = np.float32)

        self.audioWindow = np.hanning(WConfig.CHUNK_SIZE).astype(np.float32)

        self.doSmoothing = (WConfig.smoothing > 0)
        self.postLeftPad = 0
        self.postRightPad = 0
        self.postKernel = None

        if self.doSmoothing:
            kernelSize = WConfig.smoothing + 2
            self.postKernel = np.hanning(kernelSize).astype(np.float32)
            self.postKernel /= np.sum(self.postKernel)
            self.postLeftPad = len(self.postKernel) // 2
            self.postRightPad = len(self.postKernel) - 1 - self.postLeftPad

            self.paddedBands = np.empty(WConfig.BANDS + self.postLeftPad + self.postRightPad, dtype = np.float32)

        self.needsReinit = False

    def run(self):
        while self.isRunning:
            try:
                defaultSpeaker = sc.default_speaker()
                mics = sc.all_microphones(include_loopback = True)
                mic = next((m for m in mics if defaultSpeaker.name in m.name), mics[0])

                MakeLog(f"[Log] [SpectrumAudioThread] | Connected: {mic.name}")

                if self.needsReinit:
                    self.BuildMatrices()

                with mic.recorder(samplerate = WConfig.SAMPLE_RATE, channels = 1, blocksize = WConfig.CHUNK_SIZE) as recorder:
                    while self.isRunning:
                        if self.needsReinit:
                            break

                        data = recorder.record(numframes = WConfig.CHUNK_SIZE)[:, 0]

                        if not data.any():
                            self.dataReadySignal.emit(self.zeroArray)
                            continue

                        data *= self.audioWindow
                        FFTData = np.abs(np.fft.rfft(data))

                        bandValues = self.weightMatrix.dot(FFTData)
                        np.maximum(bandValues, 0, out=bandValues)
                        np.sqrt(bandValues, out=bandValues)
                        bandValues *= self.EQCurve

                        if self.doSmoothing:
                            if self.postRightPad > 0:
                                self.paddedBands[self.postLeftPad:-self.postRightPad] = bandValues
                            else:
                                self.paddedBands[self.postLeftPad:] = bandValues
                            self.paddedBands[:self.postLeftPad] = bandValues[0]
                            self.paddedBands[-self.postRightPad:] = bandValues[-1]
                            smoothed = np.convolve(self.paddedBands, self.postKernel, mode = 'valid')
                        else:
                            smoothed = bandValues

                        if smoothed.max() < 0.01:
                            smoothed = self.zeroArray

                        self.dataReadySignal.emit(smoothed)

            except Exception as e:
                MakeLog(f"[SpectrumAudioThread] | Audio stream died: {e}\n[SpectrumAudioThread] Reconnecting in 2 seconds...")
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

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        
        self.isGL = WConfig.HARDWARE_ACCELERATION
        self.renderer = None

        self.audioThreadObj = AudioThread(self)
        self.audioThreadObj.start()

        self.SetupEngine()

        selectedThemeConfig.configUpdated.connect(self.OnGlobalConfigChanged)

        self.localWatcher = QFileSystemWatcher()
        if os.path.exists(WConfig.configPath):
            self.localWatcher.addPath(WConfig.configPath)
        self.localWatcher.fileChanged.connect(self.OnLocalConfigChanged)


    def SetupEngine(self):
        if self.renderer:
            self.audioThreadObj.dataReadySignal.disconnect(self.renderer.UpdateData)
            self.renderer.renderTimer.stop()
            self.mainLayout.removeWidget(self.renderer)
            self.renderer.setParent(None)
            self.renderer.deleteLater()

        if self.isGL:
            from .rendererGL import SpectrumRendererGLEngine
            self.renderer = SpectrumRendererGLEngine(self)
            MakeLog("[Log] [SpectrumWidget]", "Started with GPU (OpenGL) Engine")
        else:
            from .rendererDefault import SpectrumRendererEngine
            self.renderer = SpectrumRendererEngine(self)
            MakeLog("[Log] [SpectrumWidget]", "Started with CPU (QPainter) Engine")

        self.mainLayout.addWidget(self.renderer)
        self.audioThreadObj.dataReadySignal.connect(self.renderer.UpdateData)


    def OnGlobalConfigChanged(self, source, changedSections):
        isThemeUpdate = (source == "theme" and ("ALL" in changedSections or WConfig.propsSection in changedSections or WConfig.styleSection in changedSections))
        isAppUpdate = (source == "app" and ("ALL" in changedSections or "Performance" in changedSections))

        if not (isThemeUpdate or isAppUpdate):
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
        
        if self.isGL != WConfig.HARDWARE_ACCELERATION:
            MakeLog("[Log] [Desktop.Spectrum]", "Swapping rendering engine...")
            self.isGL = WConfig.HARDWARE_ACCELERATION
            self.SetupEngine()

        self.renderer.renderTimer.stop()
        self.renderer.ReinitArrays()
        self.audioThreadObj.TriggerReinit()
        self.renderer.renderTimer.start(WConfig.refreshRateTimer)

    def deleteLater(self):
        if hasattr(self, 'audioThreadObj'):
            self.audioThreadObj.stop()
        super().deleteLater()
