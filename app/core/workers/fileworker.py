from PyQt6.QtCore import QThread, pyqtSignal
from core.utils import MakeLog, WindowsFileOperation
import ctypes

class FileOperationThread(QThread):
    finishedSignal = pyqtSignal()

    def __init__(self, winHandle, operation, filepaths, targetPath, flags, parent = None):
        super().__init__(parent)
        self.winHandle = winHandle
        self.operation = operation
        self.filepaths = filepaths
        self.targetPath = targetPath
        self.flags = flags

    def run(self):
        try:
            WindowsFileOperation(self.winHandle, self.operation, self.filepaths, self.targetPath, self.flags)
        except Exception as e:
            MakeLog("[Log] [FileOperationThread]", f"Operation Error: {e}")

        self.finishedSignal.emit()


class EmptyBinThread(QThread):
    finishedSignal = pyqtSignal()

    def __init__(self, winHandle, parent = None):
        super().__init__(parent)
        self.winHandle = winHandle

    def run(self):
        try:
            ctypes.windll.shell32.SHEmptyRecycleBinW(self.winHandle, None, 0)
        except Exception as e:
            MakeLog("[Log] [EmptyBinThread]", f"Failed to empty bin: {e}")

        self.finishedSignal.emit()
