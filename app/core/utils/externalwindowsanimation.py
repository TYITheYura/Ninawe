from PyQt6.QtCore import QObject, QPropertyAnimation, QEasingCurve, pyqtProperty
import ctypes
import win32gui
import win32con

ACTIVE_ANIMATIONS = {}

class HwndProxy(QObject):
    def __init__(self, hwnd, parent=None):
        super().__init__(parent)
        self.hwnd = hwnd
        self._opacity = 1.0

    @pyqtProperty(float)
    def windowOpacity(self):
        return self._opacity

    @windowOpacity.setter
    def windowOpacity(self, value):
        self._opacity = value
        alpha = int(255 * value)
        ctypes.windll.user32.SetLayeredWindowAttributes(self.hwnd, 0, alpha, win32con.LWA_ALPHA)


class ExternalWindowFader(QObject):
    #
    #   Animator for system windows HWND. Used once, no longer in use...
    #   Sets alpha from 0 to 1 and from 1 to 0, depending on the function called.
    #
    def __init__(self, hwnd, durationIn=200, durationOut=150):
        super().__init__()
        self.hwnd = hwnd
        self.proxy = HwndProxy(hwnd)

        self.durationIn = durationIn
        self.durationOut = durationOut

        self.animation = QPropertyAnimation(self.proxy, b"windowOpacity")

        if hwnd in ACTIVE_ANIMATIONS:
            ACTIVE_ANIMATIONS[hwnd].animation.stop()
        ACTIVE_ANIMATIONS[hwnd] = self

    def FadeIn(self, onFinished = None):
        self.animation.setDuration(self.durationIn)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCirc)

        def Finish():
            if onFinished:
                onFinished()
            self.RemoveLayeredFlag()
            if self.hwnd in ACTIVE_ANIMATIONS:
                del ACTIVE_ANIMATIONS[self.hwnd]

        self.animation.finished.connect(Finish)
        self.animation.start()

    def FadeOut(self, onFinished = None):
        self.AddLayeredFlag()

        self.animation.setDuration(self.durationOut)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.01)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCirc)

        def Finish():
            if onFinished:
                onFinished()
            if self.hwnd in ACTIVE_ANIMATIONS:
                del ACTIVE_ANIMATIONS[self.hwnd]

        self.animation.finished.connect(Finish)
        self.animation.start()

    def AddLayeredFlag(self):
        try:
            exStyle = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
            if not (exStyle & win32con.WS_EX_LAYERED):
                win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, exStyle | win32con.WS_EX_LAYERED)
        except Exception:
            pass

    def RemoveLayeredFlag(self):
        try:
            exStyle = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
            if exStyle & win32con.WS_EX_LAYERED:
                win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, exStyle & ~win32con.WS_EX_LAYERED)
                win32gui.SetWindowPos(
                    self.hwnd, 0, 0, 0, 0, 0,
                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE |
                    win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED
                )
        except Exception:
            pass
