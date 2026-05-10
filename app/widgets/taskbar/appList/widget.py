from PyQt6.QtWidgets import QWidget, QHBoxLayout, QApplication
from PyQt6.QtCore import Qt, QSize, QPoint, QTimer
from PyQt6.QtGui import QIcon, QImage
from core.utils import (
    GetRealTargetPath, GetOpenWindows, GetWindowIcon, GetIconFromFile, PickWindowOpacity,
    IsPixmapEmpty, ToggleWindow, MakeLog, GetWindowSnapshot, LIVE_THUMBNAIL_CACHE
)
from core.config import config as configurator
from ui.components import ContextMenu
from .config import WConfig
from ui.taskbar import TBConfig
from ui.desktop import WAConfig
from core.workers import CallInPipe
from .manager import Manager
from .expose import AppExposeWidget
from .button import TaskbarButton
import os
import subprocess
import win32gui
import win32con

# please kill me :(

class Widget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("appListWidget")

        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowDoesNotAcceptFocus)

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.buttons = {}
        self.iconHashes = {}
        self.sessionOrder = []
        self.pinnedPaths = {}
        self.currentGroups = {}

        self.launchpadInfoFile = configurator.theme.GetPath("userdata\\preferences\\user\\applistdata.json")
        self.appListManager = Manager(self.launchpadInfoFile)

        app = QApplication.instance()
        app.windowManager.windowsStructureChanged.connect(self.RefreshWindows)
        app.windowManager.windowsStateChanged.connect(self.UpdateOnlyStates)
        app.windowManager.windowsStateChanged.connect(self.TakeActiveWindowSnapshot)

        WConfig.configUpdated.connect(self.UpdateStyles)

        self.UpdateStyles()

    def UpdateStyles(self, source = None, changedSections = None):
        if WConfig.visibility:
            self.show()
        else:
            self.hide()
            return

        self.layout.setSpacing(WConfig.spacing)
        self.setFixedHeight(TBConfig.panelHeight)

        for iconButton in self.buttons.values():
            iconButton.setFixedSize(WConfig.iconSize + WConfig.paddings, WConfig.iconSize + WConfig.paddings)
            iconButton.setIconSize(QSize(WConfig.iconSize, WConfig.iconSize))

        self.RefreshWindows()

    def UpdateGeometry(self):
        self.adjustSize()
        positionX = round(WConfig.position - (self.width() * (WConfig.align / 100)))
        self.setGeometry(positionX, 0, self.width(), TBConfig.panelHeight)

    def SyncDataModel(self):
        self.currentGroups = GetOpenWindows()
        openKeys = list(self.currentGroups.keys())

        rawPinnedKeys = self.appListManager.state.get("applist", [])
        self.pinnedPaths = {}
        pinnedKeys = []

        for pinPath in rawPinnedKeys:
            resolvedKey = self.ResolvePinnedKey(pinPath, openKeys)
            if resolvedKey not in pinnedKeys:
                pinnedKeys.append(resolvedKey)
                self.pinnedPaths[resolvedKey] = pinPath

        currentValid = set(pinnedKeys + openKeys)
        if not hasattr(self, "sessionOrder"):
            self.sessionOrder = []

        self.sessionOrder = [k for k in self.sessionOrder if k in currentValid]

        for pk in reversed(pinnedKeys):
            if pk not in self.sessionOrder:
                self.sessionOrder.insert(0, pk)

        for ok in openKeys:
            if ok not in self.sessionOrder:
                self.sessionOrder.append(ok)

        return self.sessionOrder.copy(), pinnedKeys, openKeys

    def ResolvePinnedKey(self, pinPath, openKeys):
        realTarget = os.path.normpath(GetRealTargetPath(pinPath)).lower()
        if realTarget in openKeys:
            return realTarget

        pinBase = os.path.basename(realTarget)
        for ok in openKeys:
            if os.path.basename(ok) == pinBase:
                return ok

        return realTarget

    def RefreshWindows(self):
        if not WConfig.visibility:
            return

        unifiedKeys, pinnedKeys, openKeys = self.SyncDataModel()
        fgHWND = win32gui.GetForegroundWindow()

        for groupKey in list(self.buttons.keys()):
            if groupKey not in unifiedKeys:
                button = self.buttons.pop(groupKey)
                self.layout.removeWidget(button)
                button.deleteLater()
                if groupKey in self.iconHashes:
                    del self.iconHashes[groupKey]

        for index, groupKey in enumerate(unifiedKeys):
            isOpen = groupKey in openKeys
            isActive = False
            isMinimized = False
            isGroup = False
            firstHWND = None

            if groupKey not in self.buttons:
                button = TaskbarButton(groupKey)
                button.setStyleSheet("""
                    TaskbarButton {
                        background-color: transparent;
                        border-radius: 4px;
                    }

                    /* Base hover */
                    TaskbarButton[isHovered="true"] { background-color: #33FFFFFF; }

                    /* Opened (on background) (one window) */
                    TaskbarButton[isOpen="true"][isGroup="false"] { padding-bottom: -1px; border-bottom: 1px solid #888888; }
                    TaskbarButton[isOpen="true"][isGroup="false"][isHovered="true"] { background-color: #33FFFFFF; }

                    /* Opened (on background) (group) */
                    TaskbarButton[isOpen="true"][isGroup="true"] { padding-bottom: -3px; border-bottom: 3px double #888888; }
                    TaskbarButton[isOpen="true"][isGroup="true"][isHovered="true"] { background-color: #33FFFFFF; }

                    /* In focus (one window) */
                    TaskbarButton[isActive="true"][isGroup="false"] { padding-bottom: -1px; border-bottom: 1px solid #0078D7; background-color: #11FFFFFF; }
                    TaskbarButton[isActive="true"][isGroup="false"][isHovered="true"] { background-color: #33FFFFFF; }

                    /* In focus (group) */
                    TaskbarButton[isActive="true"][isGroup="true"] { padding-bottom: -3px; border-bottom: 3px double #0078D7; background-color: #11FFFFFF; }
                    TaskbarButton[isActive="true"][isGroup="true"][isHovered="true"] { background-color: #33FFFFFF; }

                    /* Minimized */
                    TaskbarButton[isMinimized="true"] { padding-bottom: -3px; background-color: transparent; border-bottom: 3px solid transparent; }
                    TaskbarButton[isMinimized="true"][isHovered="true"] { background-color: #33FFFFFF; }
                """)
                button.clicked.connect(lambda checked, gk = groupKey: self.OnGroupClicked(gk))

                self.buttons[groupKey] = button

            button = self.buttons[groupKey]

            if isOpen:
                windowsList = self.currentGroups[groupKey]
                firstHWND = windowsList[0]["hwnd"]

                isMinimized = win32gui.IsIconic(firstHWND)

                PickWindowOpacity(firstHWND, isMinimized)

                isGroup = len(windowsList) > 1
                isActive = any(w["hwnd"] == fgHWND for w in windowsList) and not isMinimized

            button.UpdateState(isOpen, isActive, isMinimized, isGroup)

            freshPixmap = None
            if isOpen:
                freshPixmap = GetWindowIcon(firstHWND)
                if IsPixmapEmpty(freshPixmap):
                    freshPixmap = GetIconFromFile(groupKey)
            else:
                freshPixmap = GetIconFromFile(groupKey)
                button.setToolTip(os.path.basename(groupKey))

            if freshPixmap:
                freshHash = self.GetPixmapHash(freshPixmap)
                if self.iconHashes.get(groupKey) != freshHash:
                    button.setIcon(QIcon(freshPixmap))
                    self.iconHashes[groupKey] = freshHash

            self.layout.insertWidget(index, button)

        QTimer.singleShot(0, self.UpdateGeometry)

    def GetPixmapHash(self, pixmap):
        if not pixmap or pixmap.isNull():
            return 0

        img = pixmap.toImage().convertToFormat(QImage.Format.Format_ARGB32)

        pointer = img.constBits()
        pointer.setsize(img.sizeInBytes())

        return hash(bytes(pointer))

    def OnGroupClicked(self, groupKey):
        windowsList = self.currentGroups.get(groupKey, [])

        if not windowsList:
            try:
                pinPath = self.pinnedPaths.get(groupKey, groupKey)

                if "explorer.exe" in pinPath.lower():
                    MakeLog("[Log] [Taskbar]", "Intercepted explorer.exe. Forcing File Browser mode.")

                    # /n - Open new window
                    # /e - Use file explorer
                    # ::{20D04FE0-3AEA-1069-A2D8-08002B30309D} - System CLSID for "This computer"
                    subprocess.Popen(
                        ['explorer.exe', '/n,', '/e,', '::{20D04FE0-3AEA-1069-A2D8-08002B30309D}'],
                        creationflags = 0x00000008,
                        close_fds = True
                    )
                    return

                MakeLog("[Log] [Taskbar]", f"Starting pinned app: {pinPath}")
                subprocess.Popen([pinPath], creationflags = 0x00000008, close_fds = True, shell = True)
            except Exception as e:
                MakeLog("[Log] [Taskbar]", f"Popen failed, using startfile. Error: {e}")
                os.startfile(pinPath)
            return

        if hasattr(self, 'exposeWindow') and self.exposeWindow is not None:
            try:
                if self.exposeWindow.isVisible():
                    self.exposeWindow.close()
                    self.exposeWindow = None
                    return
            except Exception:
                self.exposeWindow = None

        targetX, targetY = 0, 0
        button = self.buttons.get(groupKey)
        if button:
            globalPosition = button.mapToGlobal(QPoint(button.width() // 2, button.height() // 2))
            targetX = globalPosition.x()
            targetY = globalPosition.y()

        if len(windowsList) == 1:
            ToggleWindow(windowsList[0]["hwnd"], targetX, targetY, True, WAConfig.minimizeVerticalPosition)
        else:
            self.exposeWindow = AppExposeWidget()
            self.exposeWindow.ShowGroup(windowsList)

    def HandleButtonDrag(self, draggedButton, globalPosition):
        localPosition = self.mapFromGlobal(globalPosition)
        targetWidget = self.childAt(localPosition)

        while targetWidget and not hasattr(targetWidget, 'groupKey'):
            targetWidget = targetWidget.parent()

        if targetWidget and hasattr(targetWidget, 'groupKey') and targetWidget != draggedButton:
            newIndex = self.layout.indexOf(targetWidget)
            self.layout.insertWidget(newIndex, draggedButton)

    def HandleDragFinished(self, draggedButton):
        newSessionOrder = []
        newPinnedList = []

        for i in range(self.layout.count()):
            item = self.layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if hasattr(widget, 'groupKey'):
                    gk = widget.groupKey

                    newSessionOrder.append(gk)

                    if gk in self.pinnedPaths:
                        newPinnedList.append(self.pinnedPaths[gk])

        self.sessionOrder = newSessionOrder

        self.appListManager.UpdatePinnedOrder(newPinnedList)

    def UpdateOnlyStates(self):
        if not WConfig.visibility:
            return

        self.currentGroups = GetOpenWindows()
        openKeys = list(self.currentGroups.keys())
        fgHWND = win32gui.GetForegroundWindow()

        for groupKey, button in self.buttons.items():
            isOpen = groupKey in openKeys
            isActive = False
            isMinimized = False
            isGroup = False

            if isOpen:
                windowsList = self.currentGroups[groupKey]
                isGroup = len(windowsList) > 1

                allMinimized = True
                for w in windowsList:
                    hwnd = w["hwnd"]
                    minimized = win32gui.IsIconic(hwnd)
                    PickWindowOpacity(hwnd, minimized)
                    if not minimized:
                        allMinimized = False

                isMinimized = allMinimized

                fgHWND = win32gui.GetForegroundWindow()
                isActive = any(w["hwnd"] == fgHWND for w in windowsList) and not isMinimized

                firstHWND = windowsList[0]["hwnd"]
                freshPixmap = GetWindowIcon(firstHWND)

                if IsPixmapEmpty(freshPixmap):
                    freshPixmap = GetIconFromFile(groupKey)
                if freshPixmap:
                    freshHash = self.GetPixmapHash(freshPixmap)
                    if self.iconHashes.get(groupKey) != freshHash:
                        button.setIcon(QIcon(freshPixmap))
                        self.iconHashes[groupKey] = freshHash

            button.UpdateState(isOpen, isActive, isMinimized, isGroup)

    def TakeActiveWindowSnapshot(self):
        if not WConfig.visibility:
            return

        hwnd = win32gui.GetForegroundWindow()

        if not hwnd or win32gui.IsIconic(hwnd):
            return

        isTracked = False
        if hasattr(self, 'currentGroups'):
            for windowsList in self.currentGroups.values():
                if any(w["hwnd"] == hwnd for w in windowsList):
                    isTracked = True
                    break

        if isTracked:
            pixmap = GetWindowSnapshot(hwnd)

            if pixmap and not pixmap.isNull():
                scaledPixmap = pixmap.scaledToWidth(360, Qt.TransformationMode.SmoothTransformation)
                LIVE_THUMBNAIL_CACHE[hwnd] = scaledPixmap

    def ShowContextMenu(self, button, globalPosition):
        menu = ContextMenu("taskbar.applist.icon", None)

        isPinned = button.groupKey in getattr(self, 'pinnedPaths', {})
        isOpen = button.property("isOpen") == "true"

        if isPinned:
            action = menu.addAction(configurator.lang.Translate("ContextMenu", "unpin", fallback = "Unpin"))
            action.setData("unpin")
        else:
            action = menu.addAction(configurator.lang.Translate("ContextMenu", "pin", fallback = "Pin"))
            action.setData("pin")

        if isOpen:
            menu.addSeparator()
            closeAction = menu.addAction(configurator.lang.Translate("ContextMenu", "close", fallback = "Close"))
            closeAction.setData("close")

        menu.commandClicked.connect(lambda cmd: self.HandleMenuCommand(cmd, button.groupKey))

        menu.exec(globalPosition)

    def HandleMenuCommand(self, command, groupKey):
        if command == "pin":
            self.appListManager.PinApp(groupKey)
            self.RefreshWindows()

        elif command == "unpin":
            pinPath = self.pinnedPaths.get(groupKey, groupKey)
            self.appListManager.UnpinApp(pinPath)
            self.sessionOrder = []
            self.RefreshWindows()

        elif command == "close":
            windowsList = self.currentGroups.get(groupKey, [])
            for w in windowsList:
                try:
                    win32gui.PostMessage(w["hwnd"], win32con.WM_CLOSE, 0, 0)
                except Exception:
                    CallInPipe("win32gui", "PostMessage", w["hwnd"], win32con.WM_CLOSE, 0, 0)
