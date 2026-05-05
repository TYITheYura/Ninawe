import os
from PyQt6.QtWidgets import QApplication, QFileIconProvider
from PyQt6.QtCore import Qt, QFileInfo, QMimeData, QUrl
from core.utils import MakeLog, FO_MOVE, FOF_ALLOWUNDO, FO_DELETE, WSHELL, GetRealTargetPath
from ui.components import ContextMenu
from ui.desktop.config import IConfig
from core.workers import ThumbnailLoaderThread, FileOperationThread, StartFileThread
from .base import BaseDesktopItem
import subprocess
from PyQt6.QtGui import QPixmap

class FileItem(BaseDesktopItem):
    def __init__(self, filepath, itemType, desktop):
        super().__init__(filepath, desktop, None)
        self.itemType = itemType

        displayName = self.filename[:-4] if self.filename.lower().endswith('.lnk') else self.filename

        if self.itemType in ["folder", "folder_shortcut", "executable", "exe_shortcut"]:
            self.setAcceptDrops(True)

        if self.itemType in ["folder", "folder_shortcut"]:
            self.lastmTime = os.path.getmtime(self.filepath)
            self.desktop.globalFolderUpdated.connect(self.ContentChanged)

        self.LoadNativeIcon()
        self.SetDisplayName(displayName)

        self.thumbnailThread = ThumbnailLoaderThread(self.filepath, IConfig.bitmapSize, self.desktop)
        self.thumbnailThread.loadedSignal.connect(self.ApplyThumbnail)

        self.thumbnailThread.finished.connect(self.thumbnailThread.deleteLater)
        self.thumbnailThread.start()

    def ContentChanged(self):
        if getattr(self, 'isDying', False):
            return

        try:
            currentmTime = os.path.getmtime(self.filepath)
            if currentmTime != self.lastmTime:
                from core.utils import MakeLog
                MakeLog("[Log] [DesktopItem]", f"Changes in {self.filepath}")
                self.lastmTime = currentmTime
                self.ReloadThumbnail()
        except Exception:
            pass

    def ApplyThumbnail(self, image):
        pixmap = QPixmap.fromImage(image)
        scaledPixmap = pixmap.scaled(
            IConfig.bitmapSize, IConfig.bitmapSize,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.iconLabel.setPixmap(scaledPixmap)

    def LoadNativeIcon(self):
        actualIconPath = self.filepath

        if self.filepath and self.filepath.lower().endswith('.lnk'):
            try:
                shortcut = WSHELL.CreateShortCut(self.filepath)
                target = shortcut.Targetpath
                if target and os.path.exists(target):
                    actualIconPath = target
            except Exception as e:
                MakeLog("[Log] [DesktopItem]", f"Failed to resolve shortcut {self.filepath}: {e}")

        provider = QFileIconProvider()
        fileInfo = QFileInfo(actualIconPath)
        icon = provider.icon(fileInfo)

        self.iconLabel.setPixmap(icon.pixmap(IConfig.bitmapSize, IConfig.bitmapSize))

    def ReloadThumbnail(self):
        try:
            if self.thumbnailThread.isRunning():
                self.thumbnailThread.terminate()
        except RuntimeError:
            pass

        self.thumbnailThread = ThumbnailLoaderThread(self.filepath, IConfig.bitmapSize, self)
        self.thumbnailThread.loadedSignal.connect(self.ApplyThumbnail)
        self.thumbnailThread.finished.connect(self.thumbnailThread.deleteLater)
        self.thumbnailThread.start()

    def ExecuteDoubleClick(self):
        self.startThread = StartFileThread(self.filepath)
        self.startThread.finishedSignal.connect(self.startThread.deleteLater)
        self.startThread.start()

    def AddExternalMimeData(self, mimeData):
        urls = [QUrl.fromLocalFile(self.filepath)]

        if self in self.desktop.selectedItems:
            for item in self.desktop.selectedItems:
                if item != self and getattr(item, 'itemType', '') not in ["widget", "system_icon"]:
                    urls.append(QUrl.fromLocalFile(item.filepath))

        mimeData.setUrls(urls)

    def dragEnterEvent(self, event):
        if self.itemType in ["folder", "folder_shortcut", "executable", "exe_shortcut"] and event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            filepaths = [os.path.normpath(url.toLocalFile()) for url in urls]
            if os.path.normpath(self.filepath) in filepaths:
                return

            event.accept()
            self.SetHoverDrop(True)
            self.desktop.gridHint.hide()

    def dragLeaveEvent(self, event):
        self.SetHoverDrop(False)

    def dropEvent(self, event):
        self.SetHoverDrop(False)
        urls = event.mimeData().urls()

        if not urls:
            return

        filepaths = [url.toLocalFile() for url in urls]
        targetPath = GetRealTargetPath(self.filepath)

        if self.itemType in ["folder", "folder_shortcut"]:
            winHandle = int(self.desktop.winId()) if self.desktop else 0
            operationThread = FileOperationThread(winHandle, FO_MOVE, filepaths, targetPath, 0, self.desktop)
            operationThread.finished.connect(operationThread.deleteLater)
            operationThread.start()
        elif self.itemType in ["executable", "exe_shortcut"]:
            for path in filepaths:
                subprocess.Popen([targetPath, path])

        event.acceptProposedAction()

    def ExecuteContextMenu(self, event):
        menu = ContextMenu("item", self)

        if menu.isEmpty():
            return

        menu.commandClicked.connect(self.ExecuteItemCommand)
        menu.exec(event.globalPos())

    def DeleteSelf(self):
        itemsToDelete = []

        if self in self.desktop.selectedItems:
            itemsToDelete = list(self.desktop.selectedItems)
        else:
            itemsToDelete = [self]

        filepaths = [os.path.normpath(item.filepath) for item in itemsToDelete if item.filepath]

        if filepaths:
            winHandle = int(self.desktop.winId())

            for item in itemsToDelete:
                item.Cleanup()

            operationThread = FileOperationThread(winHandle, FO_DELETE, filepaths, None, FOF_ALLOWUNDO, self.desktop)
            operationThread.finishedSignal.connect(self.desktop.UpdateRecycleBinIcon)
            operationThread.finished.connect(operationThread.deleteLater)

            operationThread.start()

            MakeLog("[Log] [DesktopItem]", f"Started async delete for {len(filepaths)} items")

        self.desktop.ClearSelection()

    def MakeFileOperation(self, command):
        clipboard = QApplication.clipboard()
        mimeData = QMimeData()

        urls = []

        for item in self.desktop.cutItems:
            try:
                item.SetCutState(False)
            except RuntimeError:
                pass

        self.desktop.cutItems.clear()

        if self in self.desktop.selectedItems:
            for item in self.desktop.selectedItems:
                urls.append(QUrl.fromLocalFile(item.filepath))

                if command == "cut":
                    item.SetCutState(True)
                    self.desktop.cutItems.append(item)
        else:
            urls.append(QUrl.fromLocalFile(self.filepath))
            if command == "cut":
                self.SetCutState(True)
                self.desktop.cutItems.append(self)

        mimeData.setUrls(urls)

        # x02 (0x2) - cut, x05 (0x5) - copy
        dropEffect = b'\x02\x00\x00\x00' if command == "cut" else b'\x05\x00\x00\x00'
        mimeData.setData("Preferred DropEffect", dropEffect)

        clipboard.setMimeData(mimeData)
        MakeLog("[Log] [DesktopItem]", f"Items {command}ed to clipboard")

    def ExecuteItemCommand(self, command):
        if not command or command == "none":
            return

        MakeLog("[Log] [DesktopItem]", f"Executing item command: {command} on {self.filepath}")

        if command == "open":
            self.ExecuteDoubleClick()
        elif command == "delete":
            self.DeleteSelf()
        elif command == "properties":
            self.ShowWindowsProperties()
        elif command in ["copy", "cut"]:
            self.MakeFileOperation(command)
        elif command == "rename":
            self.StartRename()

    def Cleanup(self):
        self.isDying = True
        if self.itemType in ["folder", "folder_shortcut"]:
            try:
                self.desktop.globalFolderUpdated.disconnect(self.ContentChanged)
            except TypeError:
                pass

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F2:
            self.StartRename()
        elif event.key() == Qt.Key.Key_Delete:
            self.DeleteSelf()
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_X:
            self.MakeFileOperation("cut")
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_C:
            self.MakeFileOperation("copy")
        elif event.key() in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
            self.ExecuteDoubleClick()
        else:
            super().keyPressEvent(event)
