import numpy as np
from PyQt6.QtWidgets import QSizePolicy
from PyQt6.QtCore import Qt, QTimer, QElapsedTimer
from PyQt6.QtGui import QColor, QSurfaceFormat
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
import OpenGL.GL as gl
from OpenGL.GL import shaders
from .config import WConfig

class SpectrumRendererGLEngine(QOpenGLWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        sFormat = QSurfaceFormat()
        sFormat.setVersion(3, 3)
        sFormat.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
        sFormat.setAlphaBufferSize(8)
        sFormat.setSamples(0)
        self.setFormat(sFormat)

        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.ReinitArrays()
        self.shaderProgram = None
        self.vao = None
        self.vbo = None

        self.renderTimer = QTimer(self)
        self.renderTimer.timeout.connect(self.update)

        self.timeTracker = QElapsedTimer()
        self.timeTracker.start()

    def ReinitArrays(self):
        self.currentHeights = np.zeros(WConfig.BANDS, dtype=np.float32)
        self.targetHeights = np.zeros(WConfig.BANDS, dtype=np.float32)
        self.peakHeights = np.zeros(WConfig.BANDS, dtype=np.float32)
        self.needsShaderRebuild = True

    def UpdateData(self, newData):
        if len(newData) != len(self.targetHeights):
            return

        self.targetHeights = np.clip(np.array(newData) * WConfig.sensitivity, 0, 100).astype(np.float32)

        if np.max(self.targetHeights) > 0 and not self.renderTimer.isActive():
            self.renderTimer.start(WConfig.refreshRateTimer)

    def initializeGL(self):
        self.CompileShaders()

        vertices = np.array(
            [
                0.0, 1.0,
                0.0, 0.0,
                1.0, 1.0,
                1.0, 0.0
            ], dtype = np.float32
        )

        self.vao = gl.glGenVertexArrays(1)
        self.vbo = gl.glGenBuffers(1)

        gl.glBindVertexArray(self.vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW)

        position_loc = gl.glGetAttribLocation(self.shaderProgram, "position")
        gl.glEnableVertexAttribArray(position_loc)
        gl.glVertexAttribPointer(position_loc, 2, gl.GL_FLOAT, gl.GL_FALSE, 0, None)

        gl.glBindVertexArray(0)

    def CompileShaders(self):
        VERTEX_SHADER = f"""
            #version 330 core
            in vec2 position;

            uniform float heights[{WConfig.BANDS}];
            uniform float barWidth;
            uniform float screenWidth;
            uniform float screenHeight;
            uniform float padding;

            uniform bool isPeak;
            uniform float peakHeightPx;

            void main() {{
                float baseHeightPx = heights[gl_InstanceID];
                float actualHeightPx = isPeak ? peakHeightPx : baseHeightPx;

                float actualBarWidth = barWidth - padding;
                float xPixel = (gl_InstanceID * barWidth) + (position.x * actualBarWidth) + (padding / 2.0);

                float yOffset = isPeak ? baseHeightPx : 0.0;
                float yPixel = screenHeight - (position.y * actualHeightPx) - yOffset;

                float ndc_x = (xPixel / screenWidth) * 2.0 - 1.0;
                float ndc_y = (yPixel / screenHeight) * -2.0 + 1.0;

                gl_Position = vec4(ndc_x, ndc_y, 0.0, 1.0);
            }}
        """

        FRAGMENT_SHADER = """
            #version 330 core
            uniform vec4 color;
            out vec4 fragColor;

            void main() {
                fragColor = color;
            }
        """

        vs = shaders.compileShader(VERTEX_SHADER, gl.GL_VERTEX_SHADER)
        fs = shaders.compileShader(FRAGMENT_SHADER, gl.GL_FRAGMENT_SHADER)

        if self.shaderProgram:
            try:
                gl.glDeleteProgram(self.shaderProgram)
            except Exception:
                pass
        self.shaderProgram = shaders.compileProgram(vs, fs)

        self.loc_barWidth = gl.glGetUniformLocation(self.shaderProgram, "barWidth")
        self.loc_screenWidth = gl.glGetUniformLocation(self.shaderProgram, "screenWidth")
        self.loc_screenHeight = gl.glGetUniformLocation(self.shaderProgram, "screenHeight")
        self.loc_padding = gl.glGetUniformLocation(self.shaderProgram, "padding")
        self.loc_heights = gl.glGetUniformLocation(self.shaderProgram, "heights")
        self.loc_color = gl.glGetUniformLocation(self.shaderProgram, "color")
        self.loc_isPeak = gl.glGetUniformLocation(self.shaderProgram, "isPeak")
        self.loc_peakHeightPx = gl.glGetUniformLocation(self.shaderProgram, "peakHeightPx")

    def resizeGL(self, w, h):
        gl.glViewport(0, 0, w, h)

    def paintGL(self):
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return

        if getattr(self, 'needsShaderRebuild', False):
            self.CompileShaders()
            self.needsShaderRebuild = False

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

        barHeightsPx = np.clip((self.currentHeights / 100) * h, WConfig.bandMinHeight, None).astype(np.float32)

        gl.glClearColor(0.0, 0.0, 0.0, 0.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glUseProgram(self.shaderProgram)

        qCol = QColor(WConfig.color)
        baseR, baseG, baseB, baseA = qCol.redF(), qCol.greenF(), qCol.blueF(), qCol.alphaF()

        gl.glUniform1f(self.loc_barWidth, w / WConfig.BANDS)
        gl.glUniform1f(self.loc_screenWidth, float(w))
        gl.glUniform1f(self.loc_screenHeight, float(h))
        gl.glUniform1f(self.loc_padding, float(WConfig.paddings))

        gl.glBindVertexArray(self.vao)

        gl.glUniform4f(self.loc_color, baseR, baseG, baseB, baseA)
        gl.glUniform1i(self.loc_isPeak, 0)

        gl.glUniform1fv(self.loc_heights, WConfig.BANDS, barHeightsPx)
        gl.glDrawArraysInstanced(gl.GL_TRIANGLE_STRIP, 0, 4, WConfig.BANDS)

        if WConfig.peakHoldsEnabled:
            qPeakCol = QColor(WConfig.peakHoldsColor)
            peakR, peakG, peakB, peakA = qPeakCol.redF(), qPeakCol.greenF(), qPeakCol.blueF(), qPeakCol.alphaF()
            peakHeightsPx = np.clip((self.peakHeights / 100) * h, WConfig.bandMinHeight, None).astype(np.float32)

            gl.glUniform4f(self.loc_color, peakR, peakG, peakB, peakA)
            gl.glUniform1i(self.loc_isPeak, 1)
            gl.glUniform1f(self.loc_peakHeightPx, float(WConfig.peakHoldsHeight))

            gl.glUniform1fv(self.loc_heights, WConfig.BANDS, peakHeightsPx)
            gl.glDrawArraysInstanced(gl.GL_TRIANGLE_STRIP, 0, 4, WConfig.BANDS)

        gl.glBindVertexArray(0)
