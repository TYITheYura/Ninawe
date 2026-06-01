import ctypes
import ctypes.wintypes
import win32con
import win32gui
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
    explorerSyncRequested = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.hooks = []
        self.callback = WinEventProcType(self.EventCallback)
        self.lastExplorerHwnd = 0

    def run(self):
        ole32.CoInitialize(0)

        self.structureTimer = QTimer()
        self.structureTimer.setSingleShot(True)
        self.structureTimer.timeout.connect(self.windowsStructureChanged.emit)

        self.stateTimer = QTimer()
        self.stateTimer.setSingleShot(True)
        self.stateTimer.timeout.connect(self.windowsStateChanged.emit)

        self.explorerTimer = QTimer()
        self.explorerTimer.setSingleShot(True)
        self.explorerTimer.timeout.connect(self.EmitExplorerSync)

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

    def EmitExplorerSync(self):
        self.explorerSyncRequested.emit(self.lastExplorerHwnd)

    def EventCallback(self, hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
        #
        #   I wanna kill myself.
        #
        if hwnd == 0:
            return

        if idObject != win32con.OBJID_WINDOW or idChild != win32con.CHILDID_SELF:
            return

        try:
            if win32gui.GetParent(hwnd) != 0:
                return

            if event not in (win32con.EVENT_OBJECT_CREATE, win32con.EVENT_OBJECT_DESTROY):
                if not win32gui.IsWindowVisible(hwnd):
                    return

        except Exception:
            return

        try:
            className = win32gui.GetClassName(hwnd)
        except Exception:
            className = ""

        isExplorer = className in ("CabinetWClass", "ExploreWClass")

        if event in (win32con.EVENT_OBJECT_CREATE, win32con.EVENT_OBJECT_DESTROY):
            self.structureTimer.start(50)
            if isExplorer:
                self.lastExplorerHwnd = hwnd
                self.explorerTimer.start(400)

        elif event in (win32con.EVENT_SYSTEM_FOREGROUND, win32con.EVENT_SYSTEM_MINIMIZESTART, win32con.EVENT_SYSTEM_MINIMIZEEND):
            self.stateTimer.start(20)
            if isExplorer and event == win32con.EVENT_SYSTEM_FOREGROUND:
                self.lastExplorerHwnd = hwnd
                self.explorerTimer.start(400)

        elif event == win32con.EVENT_OBJECT_NAMECHANGE:
            self.structureTimer.start(50)
            if isExplorer:
                self.lastExplorerHwnd = hwnd
                self.explorerTimer.start(400)

    def stop(self):
        self.quit()
        self.wait()
