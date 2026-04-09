import os
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from core.config import config as configurator
from core.utils import MakeLog, FOF_ALLOWUNDO, FO_DELETE, IsRecycleBinEmpty
from ui.desktop.config import IConfig
from core.workers import FileOperationThread, EmptyBinThread
from .base import BaseDesktopItem

class SystemItem(BaseDesktopItem):
    def __init__(self, filepath, desktop, widgetData = None):
        super().__init__(filepath, desktop, widgetData)
        self.itemType = "system_icon"

        systemType = self.widgetData.get("system_type", "") if self.widgetData else ""

        if systemType == "recycle_bin":
            self.setAcceptDrops(True)

        if self.widgetData:
            self.filename = self.widgetData.get("name", self.filename)

        self.LoadCustomIcon()
        self.SetDisplayName(self.filename)

    def LoadCustomIcon(self):
        systemType = self.widgetData.get("system_type", "") if self.widgetData else ""
        iconName = "default"

        if systemType == "computer":
            iconName = "my_pc"
        elif systemType == "recycle_bin":
            if IsRecycleBinEmpty():
                iconName = "bin_empty"
            else:
                iconName = "bin_full"

        finalIconPath = configurator.theme.GetPath(f"app\\assets\\desktopicons\\{iconName}.ico")

        self.iconLabel.setPixmap(QPixmap(finalIconPath).scaled(
            IConfig.bitmapSize, IConfig.bitmapSize,
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        ))

    def ExecuteDoubleClick(self):
        os.startfile(self.filepath)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
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

        filepaths = [os.path.normpath(url.toLocalFile()) for url in urls]

        winHandle = int(self.desktop.winId()) if self.desktop.winId else 0

        operationThread = FileOperationThread(winHandle, FO_DELETE, filepaths, None, FOF_ALLOWUNDO, self.desktop)
        operationThread.finishedSignal.connect(self.desktop.UpdateRecycleBinIcon)
        operationThread.finished.connect(operationThread.deleteLater)
        operationThread.start()

        event.acceptProposedAction()

    def GetMenuConfig(self):
        systemType = self.widgetData.get("system_type", "default")
        return f"system.{systemType}", None

    def ExecuteItemCommand(self, command):
        if command == "open":
            self.ExecuteDoubleClick()

        elif command == "empty_bin" and self.widgetData.get("system_type") == "recycle_bin":
            winHandle = int(self.desktop.winId())

            emptyThread = EmptyBinThread(winHandle, self.desktop)
            emptyThread.finishedSignal.connect(self.desktop.UpdateRecycleBinIcon)
            emptyThread.finished.connect(emptyThread.deleteLater)
            emptyThread.start()
            MakeLog("[Log] [SystemItem]", "Started async recycle bin cleanup")

        elif command == "properties":
            self.ShowWindowsProperties()
