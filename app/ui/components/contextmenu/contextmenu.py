import json
from PyQt6.QtWidgets import QMenu
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from core.config import config as configurator
from core.utils import MakeLog
from .config import CMConfig

class ContextMenu(QMenu):
    commandClicked = pyqtSignal(str)

    def __init__(self, sectionName, parent = None, customPath = None):
        super().__init__(parent)
        self.sectionName = sectionName
        self.customPath = customPath

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlags(
            self.windowFlags() |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.NoDropShadowWindowHint
        )

        CMConfig.Updater()
        self.setStyleSheet(CMConfig.contextMenuStyleSheet)

        self.triggered.connect(self.OnActionTriggered)
        self.LoadAndBuildMenu()

    def LoadAndBuildMenu(self):
        defaultItems = []
        customItems = []

        try:
            with open(CMConfig.contextMenuDataPath, "r", encoding = "utf-8") as f:
                menuData = json.load(f)
                defaultItems = menuData.get(self.sectionName, [])
        except Exception as e:
            MakeLog("[Log] [ContextMenu]", f"Failed to load default JSON: {e}")

        if self.customPath:
            try:
                with open(self.customPath, "r", encoding = "utf-8") as f:
                    customData = json.load(f)
                    customItems = customData.get(self.sectionName, [])
            except Exception as e:
                MakeLog("[Log] [ContextMenu]", f"Failed to load custom JSON: {e}")

        if customItems and defaultItems:
            finalItems = customItems + [{"type": "separator"}] + defaultItems
        elif customItems:
            finalItems = customItems
        else:
            finalItems = defaultItems

        self.BuildMenuFromJson(finalItems, self)

    def BuildMenuFromJson(self, menuData, parentMenu):
        for item in menuData:
            itemType = item.get("type", "action")

            if itemType == "separator":
                parentMenu.addSeparator()
            else:
                label = item.get("label", "Item")
                labelID = item.get("label_id", "")

                if labelID and "." in labelID:
                    section, key = labelID.split(".", 1)
                    label = configurator.lang.Translate(section, key, fallback = label)

                if itemType == "submenu":
                    submenu = QMenu(label, self)
                    submenu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
                    submenu.setWindowFlags(submenu.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
                    submenu.setStyleSheet(parentMenu.styleSheet())

                    self.BuildMenuFromJson(item.get("items", []), submenu)
                    parentMenu.addMenu(submenu)

                elif itemType == "action":
                    iconPath = item.get("icon", None)

                    if iconPath:
                        iconPath = configurator.theme.GetPath(iconPath)
                        action = parentMenu.addAction(QIcon(iconPath), label)
                    else:
                        action = parentMenu.addAction(label)

                    action.setData(item.get("action", "none"))

    def OnActionTriggered(self, action):
        command = action.data()
        if command and command != "none":
            self.commandClicked.emit(command)
