from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtCore import Qt, QTimer

class RenameEditor(QLineEdit):
    def __init__(self, text, parent = None):
        super().__init__(text, parent)
        self.originalText = text
        self.finishCallback = None

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        if self.finishCallback:
            QTimer.singleShot(0, self.finishCallback)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.setText(self.originalText)
            self.clearFocus()
        else:
            super().keyPressEvent(event)