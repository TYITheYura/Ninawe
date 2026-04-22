import ctypes
import ctypes.wintypes
from PyQt6.QtCore import QThread, pyqtSignal, QTimer

user32 = ctypes.windll.user32
ole32 = ctypes.windll.ole32

EVENT_OBJECT_CREATE = 0x8000
EVENT_OBJECT_DESTROY = 0x8001
EVENT_SYSTEM_MINIMIZESTART = 0x0016
EVENT_SYSTEM_MINIMIZEEND = 0x0017
EVENT_SYSTEM_FOREGROUND = 0x0003
EVENT_OBJECT_NAMECHANGE = 0x800C
OBJID_WINDOW = 0
CHILDID_SELF = 0

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

        flags = 0   # WINEVENT_OUTOFCONTEXT
        events_to_hook = [
            EVENT_OBJECT_CREATE, EVENT_OBJECT_DESTROY,
            EVENT_SYSTEM_MINIMIZESTART, EVENT_SYSTEM_MINIMIZEEND,
            EVENT_SYSTEM_FOREGROUND, EVENT_OBJECT_NAMECHANGE
        ]

        for event in events_to_hook:
            hook = user32.SetWinEventHook(event, event, 0, self.callback, 0, 0, flags)
            self.hooks.append(hook)

        self.exec()

        for hook in self.hooks:
            user32.UnhookWinEvent(hook)
        ole32.CoUninitialize()

    def EventCallback(self, hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
        if idObject == OBJID_WINDOW and idChild == CHILDID_SELF:
            if event in [EVENT_OBJECT_CREATE, EVENT_OBJECT_DESTROY]:
                self.structureEventCount += 1

                if self.structureEventCount > 25:
                    self.structureTimer.start(500)

                else:
                    self.structureTimer.start(15)

            elif event in [EVENT_SYSTEM_FOREGROUND, EVENT_SYSTEM_MINIMIZESTART, EVENT_SYSTEM_MINIMIZEEND, EVENT_OBJECT_NAMECHANGE]:
                self.stateTimer.start(10)

    def OnStructureTimeout(self):
        self.structureEventCount = 0
        self.windowsStructureChanged.emit()

    def stop(self):
        self.quit()
        self.wait()
