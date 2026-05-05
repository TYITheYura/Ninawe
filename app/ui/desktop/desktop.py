import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QApplication,
)
from PyQt6.QtGui import (
    QPainter, QColor, QCursor,
)
from PyQt6.QtCore import (
    Qt, QRect, QFileSystemWatcher, pyqtSignal, QTimer
)
import subprocess
from core.utils import MakeLog
from ui.components import ContextMenu, GridHintWidget
from .config import DConfig, IConfig, DAConfig
from .items import SystemItem, FileItem, WidgetItem
from core.config import config as configurator
from core.utils import FO_COPY, FO_MOVE, FOF_NOCONFIRMATION, GetRealTargetPath
from core.managers import GridManager, DesktopStateManager, WallpaperManager, WidgetManager
from core.workers import FileOperationThread, DesktopWatcher
import math
import uuid

class DesktopWindow(QMainWindow):
    globalFolderUpdated = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.VIRTUAL_TYPES = ["widget", "system_icon"]

        # Desktop dir watcher btw
        self.dirWatcher = QFileSystemWatcher(self)
        if os.path.exists(DConfig.desktopPath):
            self.dirWatcher.addPath(DConfig.desktopPath)
        self.dirWatcher.directoryChanged.connect(self.OnDirectoryChanged)

        IConfig.configUpdated.connect(self.UpdateStyles)
        DConfig.configUpdated.connect(self.UpdateStyles)
        DAConfig.configUpdated.connect(self.ScanDesktop)

        self.cutItems = []
        self.desktopItems = []
        self.selectedItems = []
        self.previouslySelectedItems = []
        self.pendingDropPositions = {}

        self.isSelectingStatus = False
        self.selectionStart = None
        self.hoveredDropTarget = None
        self.powerMenuWindow = None
        self.lastContextMenuGridPos = None

        # ahhhhh I'm too lazy to comment all the code :(
        # i think I'll do it next time

        self.recursiveWatcher = DesktopWatcher(DConfig.desktopPath)
        self.recursiveWatcher.systemChanged.connect(self.OnFolderActivity)
        self.recursiveWatcher.start()

        self.folderUpdateTimer = QTimer()
        self.folderUpdateTimer.setSingleShot(True)
        self.folderUpdateTimer.timeout.connect(self.globalFolderUpdated.emit)

        self.Init()

    def OnFolderActivity(self):
        self.folderUpdateTimer.start(250)

    def __del__(self):
        if hasattr(self, 'recursiveWatcher'):
            self.recursiveWatcher.stop()

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Main

    def Init(self):
        self.setWindowTitle("Ninawe Desktop")
        self.setAcceptDrops(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.gridHint = GridHintWidget(self, DConfig)
        self.gridHint.lower()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnBottomHint
        )

        self.setGeometry(self.screen().geometry())

        self.stateManager = DesktopStateManager(DConfig.desktopInfoFile)

        self.wallpaperManager = WallpaperManager(self, DConfig)
        self.wallpaperManager.LoadWallpaper()

        self.selectionBox = QWidget(self)
        self.selectionBox.setStyleSheet(DConfig.selectionStyleSheet)
        self.selectionBox.hide()

        self.ScanDesktop()

    def ScanDesktop(self, softUpdate = False):
        self.stateManager.Load()

        savedItems = {os.path.normpath(item["path"]): item for item in self.stateManager.state.get("desktop", []) if item.get("type") not in self.VIRTUAL_TYPES}
        virtualItems = [item for item in self.stateManager.state.get("desktop", []) if item.get("type") in self.VIRTUAL_TYPES]

        if not os.path.exists(DConfig.desktopPath):
            MakeLog("[Log] [Desktop]", "Desktop folder not found")
            return

        maxRows = max(1, (self.height() - DConfig.windowMarginY * 2) // (IConfig.itemHeight + IConfig.spacingY))

        occupiedPositions = set()

        for item in savedItems.values():
            pos = item.get("position", [0, 0])
            occupiedPositions.add((pos[0], pos[1]))

        for widget in virtualItems:
            if widget.get("type") != "widget":
                pos = widget.get("position", [0, 0])
                occupiedPositions.add((pos[0], pos[1]))
                continue

            if "id" not in widget or not widget["id"]:
                widget["id"] = str(uuid.uuid4())
                MakeLog("[Log] [Desktop]", f"Generated new ID for widget '{widget.get('name')}': {widget['id']}")

            pos = widget.get("position", [0, 0])
            widgetName = widget.get("name", "")

            if "minWidth" not in widget or "minHeight" not in widget:
                BIWidgetConfig = WidgetManager.GetWidgetConfig("desktop", widgetName)
                widget["minWidth"] = BIWidgetConfig["minWidth"]
                widget["minHeight"] = BIWidgetConfig["minHeight"]

            minWidth = widget.get("minWidth", 200)
            minHeight = widget.get("minHeight", 200)

            spanX = math.ceil(minWidth / (IConfig.itemWidth + IConfig.spacingX))
            spanY = math.ceil(minHeight / (IConfig.itemHeight + IConfig.spacingY))

            widget["spanX"] = spanX
            widget["spanY"] = spanY

            for x in range(spanX):
                for y in range(spanY):
                    occupiedPositions.add((pos[0] + x, pos[1] + y))

        validFilepaths = []

        for filename in os.listdir(DConfig.desktopPath):
            if filename.startswith('.') or filename.lower() == 'desktop.ini':
                continue

            validFilepaths.append(os.path.normpath(os.path.join(DConfig.desktopPath, filename)))

        updatedDesktopData = []

        for filepath in validFilepaths:
            if filepath in savedItems:
                itemData = savedItems[filepath]

                if self.pendingDropPositions and filepath in self.pendingDropPositions:
                    desiredPos = self.pendingDropPositions.pop(filepath)

                    if tuple(desiredPos) not in occupiedPositions and desiredPos[1] < maxRows:
                        itemData["position"] = desiredPos
                    else:
                        itemData["position"] = GridManager.GetFirstFreePosition(occupiedPositions, maxRows)

                    occupiedPositions.add(tuple(itemData["position"]))

                updatedDesktopData.append(itemData)
            else:
                newItemData = self.AddNewItemToGrid(filepath, occupiedPositions, maxRows, renderInstantly=False)
                updatedDesktopData.append(newItemData)

        for vItem in virtualItems:
            updatedDesktopData.append(vItem)

        self.stateManager.UpdateEntireDesktop(updatedDesktopData)

        os.makedirs(os.path.dirname(DConfig.desktopInfoFile), exist_ok = True)

        self.RenderGrid(updatedDesktopData, softUpdate)

    def OnDirectoryChanged(self, path):
        actualFiles = set()
        for filename in os.listdir(DConfig.desktopPath):
            if filename.startswith('.') or filename.lower() == 'desktop.ini':
                continue
            actualFiles.add(os.path.normpath(os.path.join(DConfig.desktopPath, filename)))

        trackedFiles = {os.path.normpath(item.filepath): item for item in self.desktopItems if item.itemType not in self.VIRTUAL_TYPES}

        fileRemoved = False

        for filepath in list(trackedFiles.keys()):
            if filepath not in actualFiles:
                MakeLog("[Log] [Desktop] [OnDirectoryChanged]", f"File removed externally: {filepath}")
                self.RemoveItemByPath(filepath)
                fileRemoved = True

        if fileRemoved:
            self.UpdateRecycleBinIcon()

        desktopData = None
        newItemsAdded = False

        for filepath in actualFiles:
            if filepath not in trackedFiles:
                MakeLog("[Log] [Desktop] [OnDirectoryChanged]", f"New file detected: {filepath}")

                if desktopData is None:
                    desktopData = self.stateManager.Load()

                occupiedPositions = set()
                for item in self.desktopItems:
                    for x in range(getattr(item, 'spanX', 1)):
                        for y in range(getattr(item, 'spanY', 1)):
                            occupiedPositions.add((item.gridX + x, item.gridY + y))

                maxRows = max(1, (self.height() - DConfig.windowMarginY * 2) // (IConfig.itemHeight + IConfig.spacingY))

                newItemData, _ = self.AddNewItemToGrid(filepath, occupiedPositions, maxRows, renderInstantly = True)

                desktopData.setdefault("desktop", []).append(newItemData)
                newItemsAdded = True

        if newItemsAdded:
            self.stateManager.Save()

    def AddNewItemToGrid(self, filepath, occupiedPositions, maxRows, renderInstantly = False):
        if self.pendingDropPositions and filepath in self.pendingDropPositions:
            desiredPosition = self.pendingDropPositions.pop(filepath)
            if tuple(desiredPosition) not in occupiedPositions and desiredPosition[1] < maxRows:
                newPosition = desiredPosition
            else:
                newPosition = GridManager.GetFirstFreePosition(occupiedPositions, maxRows)
        else:
            newPosition = GridManager.GetFirstFreePosition(occupiedPositions, maxRows)

        occupiedPositions.add(tuple(newPosition))
        itemType = self.ResolveItemType(filepath)

        itemData = {
            "type": itemType,
            "name": os.path.basename(filepath),
            "path": filepath,
            "icon": "default",
            "position": newPosition
        }

        if renderInstantly:
            item = self.CreateItemNode(filepath, itemType, widgetData=itemData)
            item.gridX = newPosition[0]
            item.gridY = newPosition[1]

            positionX = DConfig.windowMarginX + newPosition[0] * (IConfig.itemWidth + IConfig.spacingX)
            positionY = DConfig.windowMarginY + newPosition[1] * (IConfig.itemHeight + IConfig.spacingY)

            item.move(positionX, positionY)
            item.show()
            self.desktopItems.append(item)
            return itemData, item

        return itemData

    def UpdateStyles(self, source = None, changedSections = None):
        if "ALL" in changedSections or "Desktop" in changedSections or source == "init":
            MakeLog("[Log] [Desktop]", "Config update detected. Applying.")
            self.wallpaperManager.LoadWallpaper()
            self.selectionBox.setStyleSheet(DConfig.selectionStyleSheet)
        elif "ALL" in changedSections or "Desktop.Icon" in changedSections or source == "init":
            MakeLog("[Log] [Desktop.Icon]", "Config update detected. Applying.")
        else:
            return

        self.ScanDesktop(True)
        self.update()

    def CreateItemNode(self, filepath, itemType, widgetData = None):
        if itemType == "system_icon":
            return SystemItem(filepath, self, widgetData)
        elif itemType == "widget":
            return WidgetItem(filepath, self, widgetData)
        else:
            return FileItem(filepath, itemType, self)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        painter.fillRect(self.rect(), QColor("black"))

        self.wallpaperManager.Draw(painter)

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Window Events

    def closeEvent(self, event):
        event.ignore()

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Selection

    def ClearSelection(self):
        for item in self.selectedItems:
            item.SetSelected(False)
        self.selectedItems.clear()

    def ProcessSelection(self, selectionRect):
        for item in self.desktopItems:
            if selectionRect.intersects(item.geometry()):
                if item not in self.selectedItems:
                    item.SetSelected(True)
                    self.selectedItems.append(item)
            else:
                if item in self.selectedItems and item not in self.previouslySelectedItems:
                    item.SetSelected(False)
                    self.selectedItems.remove(item)

    def ItemClicked(self, item, ctrlButtonPressedStatus):
        if ctrlButtonPressedStatus:
            if item in self.selectedItems:
                item.SetSelected(False)
                self.selectedItems.remove(item)
            else:
                item.SetSelected(True)
                self.selectedItems.append(item)
        else:
            if item not in self.selectedItems:
                self.ClearSelection()
                item.SetSelected(True)
                self.selectedItems.append(item)

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Grid utils

    def SnapItemToGrid(self, item, dropPosition = None, forceGridPosition = None, ignoreItems = None, bypassChecks = False):
        if ignoreItems is None:
            ignoreItems = []

        if forceGridPosition:
            targetGridX, targetGridY = forceGridPosition
        elif dropPosition:
            targetGridX, targetGridY = GridManager.PixelsToGrid(dropPosition.x(), dropPosition.y(), DConfig, IConfig)
        else:
            targetGridX, targetGridY = GridManager.PixelsToGrid(item.x(), item.y(), DConfig, IConfig)

        if not bypassChecks and not GridManager.IsPositionValid(
            targetGridX, targetGridY,
            item.spanX, item.spanY,
            ignoreItems,
            self.desktopItems,
            self.width(), self.height()
        ):
            targetGridX = item.gridX
            targetGridY = item.gridY

        item.gridX = targetGridX
        item.gridY = targetGridY

        if item.itemType == "widget":
            self.stateManager.UpdatePosition(item.widgetData.get("id"), targetGridX, targetGridY, isWidget = True)
        else:
            self.stateManager.UpdatePosition(item.filepath, targetGridX, targetGridY, isWidget = False)

        finalX = DConfig.windowMarginX + targetGridX * (IConfig.itemWidth + IConfig.spacingX)
        finalY = DConfig.windowMarginY + targetGridY * (IConfig.itemHeight + IConfig.spacingY)

        item.move(finalX, finalY)

    def RenderGrid(self, itemsData, softUpdate = False):
        savedVirtualItems = {}

        if softUpdate:
            for item in self.desktopItems:
                if item.itemType in self.VIRTUAL_TYPES and item.itemType != "system_icon":
                    key = item.widgetData.get("id") if item.itemType == "widget" else item.filepath
                    savedVirtualItems[key] = item
                else:
                    item.deleteLater()
        else:
            for item in self.desktopItems:
                item.deleteLater()

        self.desktopItems.clear()
        self.selectedItems.clear()

        for data in itemsData:
            filepath = data.get("path", "")
            itemType = data.get("type", "file")
            gridX, gridY = data.get("position", [0, 0])

            positionX = DConfig.windowMarginX + gridX * (IConfig.itemWidth + IConfig.spacingX)
            positionY = DConfig.windowMarginY + gridY * (IConfig.itemHeight + IConfig.spacingY)

            key = data.get("id") if itemType == "widget" else filepath

            if softUpdate and itemType in self.VIRTUAL_TYPES and key in savedVirtualItems:
                item = savedVirtualItems[key]
                item.gridX = gridX
                item.gridY = gridY
                item.move(positionX, positionY)
            else:
                item = self.CreateItemNode(filepath, itemType, widgetData = data)
                item.gridX = gridX
                item.gridY = gridY
                item.move(positionX, positionY)
                item.show()

            self.desktopItems.append(item)

    def GetGridPosWithOffset(self, event):
        offsetX, offsetY = 0, 0
        if event.mimeData().hasFormat("application/x-ninawe-offset"):
            try:
                parts = event.mimeData().data("application/x-ninawe-offset").data().decode('utf-8').split(':')
                offsetX, offsetY = int(parts[0]), int(parts[1])
            except Exception:
                pass

        visualX = event.position().x() - offsetX
        visualY = event.position().y() - offsetY

        return GridManager.PixelsToGrid(visualX, visualY, DConfig, IConfig)

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Mouse events

    def mousePressEvent(self, event):
        self.setFocus()

        if event.button() == Qt.MouseButton.LeftButton:
            ctrlButtonPressedStatus = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)

            if not ctrlButtonPressedStatus:
                self.ClearSelection()
                self.previouslySelectedItems = []
            else:
                self.previouslySelectedItems = self.selectedItems.copy()

            self.isSelectingStatus = True
            self.selectionStart = event.pos()

            self.selectionBox.setGeometry(QRect(self.selectionStart, self.selectionStart))
            self.selectionBox.show()

    def mouseMoveEvent(self, event):
        if self.isSelectingStatus:
            drawRect = QRect(self.selectionStart, event.pos()).normalized()
            self.selectionBox.setGeometry(drawRect)
            self.ProcessSelection(drawRect)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.isSelectingStatus:
            self.isSelectingStatus = False
            self.selectionBox.hide()

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Context Menu

    def contextMenuEvent(self, event):
        if self.childAt(event.pos()) and self.childAt(event.pos()) != self.selectionBox:
            return

        self.lastContextMenuGridPos = list(GridManager.PixelsToGrid(event.pos().x(), event.pos().y(), DConfig, IConfig))

        menu = ContextMenu("desktop", self)

        if menu.isEmpty():
            return

        menu.commandClicked.connect(self.ExecuteMenuCommand)

        menu.exec(QCursor.pos())

    def ExecuteMenuCommand(self, command):
        if not command or command == "none":
            return

        MakeLog("[Log] [DesktopMenu] [ExecuteMenuCommand]", f"Executing command: {command}")

        if command == "refresh":
            self.ScanDesktop()
        elif command == "create_folder":
            self.CreateDesktopItem(configurator.lang.Translate("DefaultItems", "new_folder", fallback = "New folder"), isFolder = True)
        elif command == "create_text":
            self.CreateDesktopItem(configurator.lang.Translate("DefaultItems", "new_text_document", fallback = "New text document") + ".txt")
        elif command == "paste":
            self.PasteCommand()
        elif command.startswith("create:"):
            target = command.split("create:")[1]
            self.CreateDesktopItem(target)
        elif command.startswith("cmd:"):
            target = command.split("cmd:")[1]
            os.system(f"start {target}")
        elif command.startswith("run:"):
            target = command.split("run:")[1]
            try:
                subprocess.Popen(target, shell = True)
            except Exception as e:
                MakeLog("[Log] [DesktopMenu] [ExecuteMenuCommand]", f"Failed to run {target}: {e}")

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> CME Commands (Misc)

    def CreateDesktopItem(self, defaultName, isFolder = False):
        path = self.GetUniqueFilepath(os.path.join(DConfig.desktopPath, defaultName), isFolder)

        try:
            if self.lastContextMenuGridPos:
                self.pendingDropPositions[path] = self.lastContextMenuGridPos

            if isFolder:
                os.makedirs(path)
            else:
                with open(path, 'w') as f:
                    pass

            MakeLog("[Log] [Desktop]", f"Created item: {path}")
        except Exception as e:
            MakeLog("[Log] [Desktop]", f"Failed to create item {path}: {e}")

    def PasteCommand(self):
        clipboard = QApplication.clipboard()
        mimeData = clipboard.mimeData()

        if mimeData.hasUrls():
            isCut = False
            for fmt in mimeData.formats():
                if "Preferred DropEffect" in fmt:
                    effectData = mimeData.data(fmt)
                    bytesData = bytes(effectData)
                    if len(bytesData) >= 1 and bytesData[0] == 2:
                        isCut = True
                    break

            winHandle = int(self.winId())
            pasteOffset = 0

            for url in mimeData.urls():
                sourcePath = os.path.normpath(url.toLocalFile())
                if not os.path.exists(sourcePath):
                    continue

                filename = os.path.basename(sourcePath)
                targetPath = self.GetUniqueFilepath(os.path.join(DConfig.desktopPath, filename), os.path.isdir(sourcePath))

                if self.lastContextMenuGridPos:
                    self.pendingDropPositions[targetPath] = [self.lastContextMenuGridPos[0], self.lastContextMenuGridPos[1] + pasteOffset]
                    pasteOffset += 1

                try:
                    if isCut:
                        MakeLog("[Log] [Desktop]", f"Cut file {sourcePath} to {targetPath}")
                        self.dropOpThread = FileOperationThread(winHandle, FO_MOVE, [sourcePath], DConfig.desktopPath, 0, self)
                    else:
                        MakeLog("[Log] [Desktop]", f"Copying file {sourcePath} to {targetPath}")
                        self.dropOpThread = FileOperationThread(winHandle, FO_COPY, [sourcePath], DConfig.desktopPath, 0, self)

                    self.dropOpThread.finished.connect(self.dropOpThread.deleteLater)
                    self.dropOpThread.start()

                except Exception as e:
                    MakeLog("[Log] [Desktop]", f"Paste error: {e}")

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Drag & drop events

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasFormat("application/x-ninawe-item-move"):
            self.draggedItemSpanX = 1
            self.draggedItemSpanY = 1

            if event.mimeData().hasFormat("application/x-ninawe-item-move"):
                itemID = event.mimeData().data("application/x-ninawe-item-move").data().decode('utf-8')

                itemToMove = next((i for i in self.desktopItems if i.itemID == itemID), None)
                if itemToMove:
                    self.draggedItemSpanX = itemToMove.spanX
                    self.draggedItemSpanY = itemToMove.spanY

            self.gridHint.show()
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasFormat("application/x-ninawe-widget") or event.mimeData().hasFormat("application/x-ninawe-item-move"):
            if not self.gridHint.isVisible():
                self.gridHint.show()

            targetGridX, targetGridY = self.GetGridPosWithOffset(event)

            hintGeometry = GridManager.CalculateHintGeometry(targetGridX, targetGridY, self.draggedItemSpanX, self.draggedItemSpanY, DConfig, IConfig)
            self.gridHint.setGeometry(hintGeometry)

            event.acceptProposedAction()

    def dropEvent(self, event):
        targetGridX, targetGridY = self.GetGridPosWithOffset(event)

        if event.mimeData().hasFormat("application/x-ninawe-item-move"):
            self.gridHint.hide()
            itemID = event.mimeData().data("application/x-ninawe-item-move").data().decode('utf-8')

            primaryItem = next((i for i in self.desktopItems if i.itemID == itemID), None)

            if primaryItem:
                deltaX = targetGridX - primaryItem.gridX
                deltaY = targetGridY - primaryItem.gridY

                itemsToMove = self.selectedItems if primaryItem in self.selectedItems else [primaryItem]

                canMoveGroup = True
                for item in itemsToMove:
                    if not GridManager.IsPositionValid(
                        item.gridX + deltaX, item.gridY + deltaY,
                        item.spanX, item.spanY,
                        itemsToMove,
                        self.desktopItems,
                        self.width(), self.height(),
                        DConfig, IConfig
                    ):
                        canMoveGroup = False
                        break

                if canMoveGroup:
                    for item in itemsToMove:
                        newX = item.gridX + deltaX
                        newY = item.gridY + deltaY
                        self.SnapItemToGrid(item, forceGridPosition = (newX, newY), bypassChecks=True)

            event.acceptProposedAction()
            return

        urls = event.mimeData().urls()
        if not urls:
            return

        self.gridHint.hide()

        internalMoves = []

        event.dropAction()

        externalFilesCount = 0
        externalPaths = []

        for url in urls:
            filepath = os.path.normpath(url.toLocalFile())
            if not filepath or not os.path.exists(filepath):
                continue

            if os.path.normpath(os.path.dirname(filepath)) != DConfig.desktopPath:
                targetPath = os.path.join(DConfig.desktopPath, os.path.basename(filepath))
                externalPaths.append(filepath)
                self.pendingDropPositions[targetPath] = [targetGridX, targetGridY + externalFilesCount]
                externalFilesCount += 1
            else:
                internalMoves.append(filepath)

        if externalPaths:
            winHandle = int(self.winId())

            modifiers = event.modifiers()

            if modifiers & Qt.KeyboardModifier.ControlModifier:
                operation = FO_COPY
            elif modifiers & Qt.KeyboardModifier.ShiftModifier:
                operation = FO_MOVE
            else:

                sourceDrive = os.path.splitdrive(externalPaths[0])[0].upper()
                desktopDrive = os.path.splitdrive(DConfig.desktopPath)[0].upper()
                operation = FO_MOVE if sourceDrive == desktopDrive else FO_COPY

            flags = 0
            if any('$recycle.bin' in p.lower() for p in externalPaths):
                flags = FOF_NOCONFIRMATION

            self.dropOpThread = FileOperationThread(winHandle, operation, externalPaths, DConfig.desktopPath, flags, self)
            self.dropOpThread.finished.connect(self.dropOpThread.deleteLater)
            self.dropOpThread.start()

        if internalMoves:
            primaryFilepath = internalMoves[0]
            primaryItem = next((i for i in self.desktopItems if os.path.normpath(i.filepath) == primaryFilepath), None)

            if primaryItem:
                deltaX = targetGridX - primaryItem.gridX
                deltaY = targetGridY - primaryItem.gridY

                for filepath in internalMoves:
                    item = next((i for i in self.desktopItems if os.path.normpath(i.filepath) == filepath), None)
                    if item:
                        newX = item.gridX + deltaX
                        newY = item.gridY + deltaY
                        self.SnapItemToGrid(item, forceGridPosition = (newX, newY))

            if externalPaths:
                event.setDropAction(Qt.DropAction.CopyAction)
            else:
                event.setDropAction(Qt.DropAction.MoveAction)

        event.accept()

    def dragLeaveEvent(self, event):
        self.gridHint.hide()
        event.accept()

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> File utils

    def RemoveItemByPath(self, filepath):
        filepath = os.path.normpath(filepath)

        itemToRemove = next((item for item in self.desktopItems if os.path.normpath(item.filepath) == filepath), None)

        if itemToRemove:
            self.desktopItems.remove(itemToRemove)
            if itemToRemove in self.selectedItems:
                self.selectedItems.remove(itemToRemove)

            if self.cutItems and itemToRemove in self.cutItems:
                self.cutItems.remove(itemToRemove)

            itemToRemove.deleteLater()
            itemToRemove.Cleanup()
            self.stateManager.RemoveItem(itemToRemove.filepath)

    def ResolveItemType(self, filepath):
        actualPath = GetRealTargetPath(filepath)
        if os.path.isdir(actualPath):
            return "folder_shortcut" if filepath.lower().endswith('.lnk') else "folder"
        elif actualPath.lower().endswith('.exe'):
            return "exe_shortcut" if filepath.lower().endswith('.lnk') else "executable"
        elif filepath.lower().endswith('.lnk'):
            return "shortcut"
        return "file"

    def GetUniqueFilepath(self, targetPath, isFolder = False):
        if not os.path.exists(targetPath):
            return targetPath

        basePath = targetPath if isFolder else os.path.splitext(targetPath)[0]
        extPart = "" if isFolder else os.path.splitext(targetPath)[1]
        counter = 2

        newPath = f"{basePath} ({counter}){extPart}"
        while os.path.exists(newPath):
            counter += 1
            newPath = f"{basePath} ({counter}){extPart}"

        return newPath

    def UpdateRecycleBinIcon(self):
        for item in self.desktopItems:
            if item.itemType == "system_icon" and item.widgetData.get("system_type") == "recycle_bin":
                item.LoadCustomIcon()
                break

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_V:
            self.PasteCommand()
        elif event.key() == Qt.Key.Key_F5:
            self.ScanDesktop()
        else:
            super().keyPressEvent(event)
