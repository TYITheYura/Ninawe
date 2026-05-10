from PyQt6.QtCore import QObject, QPropertyAnimation, QEasingCurve

class InternalWindowFader(QObject):
    #
    #   A universal transparency controller for any in-program window.
    #   Creates beautiful fade-in and fade-out effects.
    #
    def __init__(self, targetWidget, durationIn = 250, durationOut = 250):
        super().__init__(targetWidget)

        self.target = targetWidget
        self.durationIn = durationIn
        self.durationOut = durationOut

        self.target.setWindowOpacity(0.0)

    def FadeIn(self):
        from core.config import config

        self.target.show()

        if config.app.GetBool("Performance", "animations_enabled", fallback = False):
            self.animationIn = QPropertyAnimation(self.target, b"windowOpacity")
            self.animationIn.setDuration(self.durationIn)
            self.animationIn.setStartValue(self.target.windowOpacity())
            self.animationIn.setEndValue(1.0)
            self.animationIn.setEasingCurve(QEasingCurve.Type.OutCirc)
            self.animationIn.start()
        else:
            self.target.setWindowOpacity(1.0)

    def FadeOut(self, onFinished = None):
        from core.config import config

        if config.app.GetBool("Performance", "animations_enabled", fallback = False):
            self.animationOut = QPropertyAnimation(self.target, b"windowOpacity")
            self.animationOut.setDuration(self.durationOut)
            self.animationOut.setStartValue(self.target.windowOpacity())
            self.animationOut.setEndValue(0.0)
            self.animationOut.setEasingCurve(QEasingCurve.Type.OutCirc)

            if onFinished:
                self.animationOut.finished.connect(onFinished)

            self.animationOut.start()
        else:
            self.target.setWindowOpacity(0.0)
            onFinished()
