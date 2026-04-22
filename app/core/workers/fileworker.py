from PyQt6.QtCore import QThread, pyqtSignal
from core.utils import MakeLog, WindowsFileOperation
import ctypes
import os

class FileOperationThread(QThread):
    #
    #   Delete/copy/cut/etc operations thread for file
    #
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
    #
    #   Designed to clean the trash bin in a separate thread
    #
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

class StartFileThread(QThread):
    #
    #   Designed to run files in a separate thread
    #
    finishedSignal = pyqtSignal()

    def __init__(self, filepath, parent = None):
        super().__init__(parent)
        self.filepath = filepath

    def run(self):
        try:
            os.startfile(self.filepath)
        except Exception as e:
            MakeLog("[Log] [StartFileThread]", f"Failed to start file: {e}")

        self.finishedSignal.emit()
