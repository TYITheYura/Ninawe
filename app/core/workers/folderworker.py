import win32file
import win32event
import win32con
from PyQt6.QtCore import QThread, pyqtSignal

class DesktopWatcher(QThread):
    #
    #   Monitors changes in folders located on the desktop.
    #   If any are detected, it sends a signal.
    #
    systemChanged = pyqtSignal()

    def __init__(self, desktopPath):
        super().__init__()
        self.desktopPath = desktopPath
        self.isRunning = True

    def run(self):
        flags = (
            win32con.FILE_NOTIFY_CHANGE_FILE_NAME |
            win32con.FILE_NOTIFY_CHANGE_DIR_NAME |
            win32con.FILE_NOTIFY_CHANGE_LAST_WRITE
        )

        changeHandle = win32file.FindFirstChangeNotification(
            self.desktopPath,
            True,
            flags
        )

        if changeHandle == win32file.INVALID_HANDLE_VALUE:
            return

        try:
            while self.isRunning:
                result = win32event.WaitForSingleObject(changeHandle, 500)

                if result == win32event.WAIT_OBJECT_0:
                    self.systemChanged.emit()
                    win32file.FindNextChangeNotification(changeHandle)
        finally:
            win32file.FindCloseChangeNotification(changeHandle)

    def stop(self):
        self.isRunning = False
        self.wait()
