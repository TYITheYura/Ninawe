import ctypes
import ctypes.wintypes
import win32con
from PyQt6.QtCore import QThread, pyqtSignal, QTimer

user32 = ctypes.windll.user32
ole32 = ctypes.windll.ole32

WinEventProcType = ctypes.WINFUNCTYPE(
    None,
    ctypes.wintypes.HANDLE, ctypes.wintypes.DWORD,
    ctypes.wintypes.HWND, ctypes.wintypes.LONG,
    ctypes.wintypes.LONG, ctypes.wintypes.DWORD, ctypes.wintypes.DWORD
)

class SystemWindowManager(QThread):
    #
    #   A thread that intercepts windows events and, depending on their purpose, emits them for the entire shell.
    #
    windowsStructureChanged = pyqtSignal()
    windowsStateChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.hooks = []
        self.callback = WinEventProcType(self.EventCallback)
        self.structureEventCount = 0

    def run(self):
        ole32.CoInitialize(0)

        self.structureTimer = QTimer()
        self.structureTimer.setSingleShot(True)
        self.structureTimer.timeout.connect(self.OnStructureTimeout)

        self.stateTimer = QTimer()
        self.stateTimer.setSingleShot(True)
        self.stateTimer.timeout.connect(self.windowsStateChanged.emit)

        eventsToHook = [
            win32con.EVENT_OBJECT_CREATE, win32con.EVENT_OBJECT_DESTROY,
            win32con.EVENT_SYSTEM_MINIMIZESTART, win32con.EVENT_SYSTEM_MINIMIZEEND,
            win32con.EVENT_SYSTEM_FOREGROUND, win32con.EVENT_OBJECT_NAMECHANGE
        ]

        for event in eventsToHook:
            hook = user32.SetWinEventHook(event, event, 0, self.callback, 0, 0, win32con.WINEVENT_OUTOFCONTEXT)
            self.hooks.append(hook)

        self.exec()

        for hook in self.hooks:
            user32.UnhookWinEvent(hook)
        ole32.CoUninitialize()

    def EventCallback(self, hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
        if idObject == win32con.OBJID_WINDOW and idChild == win32con.CHILDID_SELF:
            if event in [win32con.EVENT_OBJECT_CREATE, win32con.EVENT_OBJECT_DESTROY]:
                self.structureEventCount += 1

                if self.structureEventCount > 25:
                    self.structureTimer.start(500)

                else:
                    self.structureTimer.start(15)

            elif event in [win32con.EVENT_SYSTEM_FOREGROUND, win32con.EVENT_SYSTEM_MINIMIZESTART, win32con.EVENT_SYSTEM_MINIMIZEEND, win32con.EVENT_OBJECT_NAMECHANGE]:
                self.stateTimer.start(10)

    def OnStructureTimeout(self):
        self.structureEventCount = 0
        self.windowsStructureChanged.emit()

    def stop(self):
        self.quit()
        self.wait()
