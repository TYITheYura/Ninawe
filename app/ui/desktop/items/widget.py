import os
from PyQt6.QtCore import Qt
from core.config import config as configurator
from core.utils import MakeLog
from core.managers import WidgetManager
from ui.desktop.config import IConfig
from .base import BaseDesktopItem

class WidgetItem(BaseDesktopItem):
    def __init__(self, filepath, desktop, widgetData = None):
        super().__init__(filepath, desktop, widgetData)
        self.itemType = "widget"

        self.spanX = self.widgetData.get("spanX", 1) if self.widgetData else 1
        self.spanY = self.widgetData.get("spanY", 1) if self.widgetData else 1

        pixelWidth = (self.spanX * IConfig.itemWidth) + ((self.spanX - 1) * IConfig.spacingX)
        pixelHeight = (self.spanY * IConfig.itemHeight) + ((self.spanY - 1) * IConfig.spacingY)

        self.setFixedSize(pixelWidth, pixelHeight)
        self.innerFrame.setFixedSize(pixelWidth, pixelHeight)

        self.iconLabel.hide()
        if self.textLabel:
            self.textLabel.hide()

        self.innerFrame.setObjectName("WidgetFrame")

        widgetName = self.widgetData.get("name", "")

        try:
            widgetClass = WidgetManager.GetWidgetClass("desktop", widgetName)
            if widgetClass:
                self.widgetInstance = widgetClass(self)
                self.innerFrame.layout().addWidget(self.widgetInstance)

        except Exception as e:
            MakeLog("[Log] [WidgetItem]", f"Failed to load widget '{widgetName}': {e}")

    def SetSelected(self, isSelected):
        pass

    def SetHoverDrop(self, isHovered):
        pass

    def mousePressEvent(self, event):
        self.setFocus()
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragStartPos = event.pos()
            self.raise_()

    def contextMenuEvent(self, event):
        self.ExecuteContextMenu(event)

    def deleteLater(self):
        if self.widgetInstance and hasattr(self.widgetInstance, 'deleteLater'):
            self.widgetInstance.deleteLater()
        super().deleteLater()

    def GetMenuConfig(self):
        widgetName = self.widgetData.get("name", "")
        userPath = configurator.theme.GetPath(f"userdata\\widgets\\desktop\\{widgetName}\\contextmenu.json")
        appPath = configurator.theme.GetPath(f"app\\widgets\\desktop\\{widgetName}\\contextmenu.json")
        customPath = userPath if os.path.exists(userPath) else appPath

        return "widget", customPath

    def ExecuteItemCommand(self, command):
        if command == "delete":
            widgetId = self.widgetData.get("id")
            self.desktop.stateManager.RemoveItem(widgetId, isWidget=True)
            if self in self.desktop.desktopItems:
                self.desktop.desktopItems.remove(self)
            self.desktop.ClearSelection()
            self.deleteLater()
            MakeLog("[Log] [WidgetItem]", f"Deleted widget: {widgetId}")
