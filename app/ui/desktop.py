import os
import random
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QApplication, QLineEdit,
    QFileIconProvider, QGraphicsDropShadowEffect, QFrame, QGraphicsOpacityEffect
)
from PyQt6.QtGui import (
    QPainter, QPixmap, QColor, QIcon, QCursor,
    QPen, QBrush, QDrag, QFontMetrics, QFont
)
from PyQt6.QtCore import (
    Qt, QTimer, QVariantAnimation, QFileInfo,
    QRect, QMimeData, QUrl, QFileSystemWatcher
)
from core.config import config as configurator
import win32com.client
import json
import shutil
import subprocess
from core.utils import MakeLog, LoadFont, ShellExecuteInfo, SEE_MASK_INVOKEIDLIST
import re
from easydict import EasyDict as easyDict
import ctypes
import ctypes.wintypes
from ui.components.contextmenu import ContextMenu
from ui.powermenu import PowerMenu
from core.widgetManager import WidgetManager
import math
import uuid

class IconConfig:
    def __init__(self):
        self.itemWidth = 0
        self.itemHeight = 0
        self.spacingX = 0
        self.spacingY = 0
        self.bitmapSize = 0
        self.containerBorderRadius = 0
        self.containerBorder = 0
        self.iconLabelFontFamily = None

        self.iconColors = easyDict(
            {
                "hover": {},
                "selected": {},
                "hoverOnSelected": {},
                "drop": {}
            }
        )

        self.iconLabelStatus = True
        self.iconStyleSheet = ""
        self.labelStyleSheet = ""

    def Updater(self):
        self.iconLabelStatus = configurator.theme.GetBool("Desktop.Icon", "icon_label_status", fallback = True)
        self.iconLabelFontSize = configurator.theme.GetInt("Desktop.Icon", "icon_label_font_size", fallback = 11)
        self.itemWidth = configurator.theme.GetInt("Desktop.Icon", "item_width", fallback = 85)
        self.itemHeight = configurator.theme.GetInt("Desktop.Icon", "item_height", fallback = 110)
        self.spacingX = configurator.theme.GetInt("Desktop.Icon", "spacing_x", fallback = 0)
        self.spacingY = configurator.theme.GetInt("Desktop.Icon", "spacing_y", fallback = 0)
        self.bitmapSize = configurator.theme.GetInt("Desktop.Icon", "bitmap_size", fallback = 48)
        self.iconLabelCompensator = configurator.theme.GetInt("Desktop.Icon", "icon_label_compensator", fallback = 0)
        self.containerBorderRadius = configurator.theme.GetInt("Desktop.Icon", "icon_container_border_radius", fallback = 0)
        self.containerBorder = configurator.theme.GetInt("Desktop.Icon", "icon_container_border", fallback = 0)

        self.iconColors.hover.background = configurator.theme.Get("Desktop.Icon", "icon_hover_background", fallback = "#44FFFFFF")
        self.iconColors.hover.border = configurator.theme.Get("Desktop.Icon", "icon_hover_border", fallback = "#55FFFFFF")

        self.iconColors.selected.background = configurator.theme.Get("Desktop.Icon", "icon_selected_background", fallback = "#55FFFFFF")
        self.iconColors.selected.border = configurator.theme.Get("Desktop.Icon", "icon_selected_border", fallback = "#66FFFFFF")

        self.iconColors.hoverOnSelected.background = configurator.theme.Get("Desktop.Icon", "icon_hover_on_selected_background", fallback = "#66FFFFFF")
        self.iconColors.hoverOnSelected.border = configurator.theme.Get("Desktop.Icon", "icon_hover_on_selected_border", fallback = "#77FFFFFF")

        self.iconColors.drop.background = configurator.theme.Get("Desktop.Icon", "icon_drop_background", fallback = "#77FFFFFF")
        self.iconColors.drop.border = configurator.theme.Get("Desktop.Icon", "icon_drop_border", fallback = "#88FFFFFF")

        rawFont = configurator.theme.Get("Desktop.Icon", "icon_label_font_family", fallback = "Segoe UI")

        if rawFont == "default":
            rawFont = configurator.theme.globals.fontFamily

        themePath = configurator.theme.GetThemePath(
            configurator.app.Get("Theme", "current_theme", fallback = "default")
        )

        self.iconLabelFontFamily = LoadFont(rawFont, themePath)

        self.iconStyleSheet = f"""
            QFrame#IconFrame {{
                background: transparent;
                border: {self.containerBorder}px solid transparent;
                border-radius: {self.containerBorderRadius}px;
            }}
            QFrame#IconFrame:hover {{
                background: {self.iconColors.hover.background};
                border: {self.containerBorder}px solid {self.iconColors.hover.border};
            }}
            QFrame#IconFrame[selected = "true"] {{
                background: {self.iconColors.selected.background};
                border: {self.containerBorder}px solid {self.iconColors.selected.border};
            }}
            QFrame#IconFrame[selected = "true"]:hover {{
                background: {self.iconColors.hoverOnSelected.background};
                border: {self.containerBorder}px solid {self.iconColors.hoverOnSelected.border};
            }}
            QFrame#IconFrame[drop_hover = "true"] {{
                background: {self.iconColors.drop.background};
                border: {self.containerBorder}px solid {self.iconColors.drop.border};
            }}
            QFrame#WidgetFrame {{
                background: transparent;
            }}
        """

        self.labelStyleSheet = f"""
            color: white;
            font-size: {self.iconLabelFontSize}px;
            font-family: "{self.iconLabelFontFamily}";
            background: transparent;
        """

class DesktopConfig:
    def __init__(self):
        self.desktopInfoFile = configurator.theme.GetPath("userdata\\preferences\\user\\desktopdata.json")
        self.desktopPath = os.path.normpath(os.path.expanduser("~/Desktop"))
        self.wallpaperList = []
        self.groupSelectionColors = {}
        self.wallpaperMode = None
        self.windowMarginX = 0
        self.windowMarginY = 0
        self.isCarousel = None
        self.intervalInMin = None
        self.shuffle = None
        self.backgroundPath = None
        self.transitionMs = 0
        self.groupSelectionBorderRadius = 0
        self.groupSelectionBorderWidth = 0
        self.selectionStyleSheet = ""

    def Updater(self):
        self.wallpaperMode = configurator.theme.Get("Desktop", "wallpaper_mode", fallback = "cover")
        self.isCarousel = configurator.theme.GetBool("Desktop", "wallpaper_carousel", fallback = True)
        self.intervalInMin = configurator.theme.GetFloat("Desktop", "carousel_interval_min", fallback = 10)
        self.shuffle = configurator.theme.GetBool("Desktop", "carousel_shuffle", fallback = False)
        self.backgroundPath = configurator.theme.GetResource(configurator.theme.Get("Desktop", "wallpaper_path"))
        self.transitionMs = configurator.theme.GetInt("Desktop", "wallpaper_transition_ms", fallback = 500)
        self.windowMarginX = configurator.theme.GetInt("Desktop", "window_margin_x", fallback = 0)
        self.windowMarginY = configurator.theme.GetInt("Desktop", "window_margin_y", fallback = 0)
        self.groupSelectionBorderRadius = configurator.theme.GetInt("Desktop", "group_selection_border_radius", fallback = 0)
        self.groupSelectionBorderWidth = configurator.theme.GetInt("Desktop", "group_selection_border_width", fallback = 0)
        self.groupSelectionColors["background"] = configurator.theme.Get("Desktop", "group_selection_background", fallback = "#55FFFFFF")
        self.groupSelectionColors["border"] = configurator.theme.Get("Desktop", "group_selection_border", fallback = "#66FFFFFF")

        self.selectionStyleSheet = f"""
            background-color: {self.groupSelectionColors.get("background")};
            border: {self.groupSelectionBorderWidth}px solid {self.groupSelectionColors.get("border")};
            border-radius: {self.groupSelectionBorderRadius}px;
        """

class GridHintWidget(QFrame):
    def __init__(self, parent = None, desktopConfig = None):
        super().__init__(parent)
        self.setObjectName("GridHint")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        self.setStyleSheet(f"""
            QFrame#GridHint {{
                background-color: {desktopConfig.groupSelectionColors.get("background")};
                border: 2px dashed {desktopConfig.groupSelectionColors.get("border")};
                border-radius: {desktopConfig.groupSelectionBorderRadius}px;
            }}
        """)
        self.hide()

class RenameEditor(QLineEdit):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.originalText = text
        self.finishCallback = None

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        if self.finishCallback:
            QTimer.singleShot(0, self.finishCallback)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.setText(self.originalText)
            self.clearFocus()
        else:
            super().keyPressEvent(event)

class DesktopWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.WSHELL = win32com.client.Dispatch("WScript.Shell")
        self.desktopConfig = DesktopConfig()
        self.iconConfig = IconConfig()
        self.iconConfig.Updater()
        self.desktopConfig.Updater()

        self.backgroundBitmap = None
        self.nextBackgroundBitmap = None

        self.fadeAlpha = 0.0
        self.currentWallpaperIndex = 0

        # Carousel timer
        self.carouselTimer = QTimer(self)
        self.carouselTimer.timeout.connect(self.StartTransition)

        # Fade animation
        self.fadeAnimation = QVariantAnimation(self)
        self.fadeAnimation.valueChanged.connect(self.UpdateFade)
        self.fadeAnimation.finished.connect(self.EndTransition)

        # Desktop dir watcher btw
        self.dirWatcher = QFileSystemWatcher(self)
        if os.path.exists(self.desktopConfig.desktopPath):
            self.dirWatcher.addPath(self.desktopConfig.desktopPath)
        self.dirWatcher.directoryChanged.connect(self.OnDirectoryChanged)

        configurator.configUpdated.connect(self.UpdateStyles)

        self.cutItems = []
        self.desktopItems = []
        self.selectedItems = []
        self.previouslySelectedItems = []
        self.pendingDropPositions = {}

        self.isSelectingStatus = False
        self.selectionStart = None
        self.hoveredDropTarget = None

        # ahhhhh I'm too lazy to comment all the code :(
        # i think I'll do it next time
        self.Init()

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Main

    def Init(self):
        self.setWindowTitle("Ninawe Desktop")
        self.setAcceptDrops(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.gridHint = GridHintWidget(self, desktopConfig = self.desktopConfig)
        self.gridHint.lower()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnBottomHint
        )

        self.setGeometry(self.screen().geometry())

        self.fadeAnimation.setDuration(self.desktopConfig.transitionMs)
        self.fadeAnimation.setStartValue(0.0)
        self.fadeAnimation.setEndValue(1.0)

        MakeLog(f"[Log] [Desktop]", f"Loading wallpaper: {self.desktopConfig.backgroundPath} (Mode: {self.desktopConfig.wallpaperMode})")

        self.LoadWallpaper()

        self.selectionBox = QWidget(self)
        self.selectionBox.setStyleSheet(self.desktopConfig.selectionStyleSheet)
        self.selectionBox.hide()

        self.ScanDesktop()

    def ScanDesktop(self):
        desktopData = {"desktop": []}
        if os.path.exists(self.desktopConfig.desktopInfoFile):
            try:
                desktopData = self.LoadJSONData()
            except Exception as e:
                MakeLog(f"[Log] [Desktop]", f"Failed to read JSON: {e}")

        savedItems = {os.path.normpath(item["path"]): item for item in desktopData.get("desktop", []) if "path" in item and item.get("type") != "widget"}

        savedWidgets = [item for item in desktopData.get("desktop", []) if item.get("type") == "widget"]

        if not os.path.exists(self.desktopConfig.desktopPath):
            MakeLog("[Log] [Desktop]", f"Desktop folder not found!")
            return

        maxRows = max(1, (self.height() - self.desktopConfig.windowMarginY * 2) // (self.iconConfig.itemHeight + self.iconConfig.spacingY))

        occupiedPositions = set()

        for item in savedItems.values():
            pos = item.get("position", [0, 0])
            occupiedPositions.add((pos[0], pos[1]))

        for widget in savedWidgets:
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

            spanX = math.ceil(minWidth / (self.iconConfig.itemWidth + self.iconConfig.spacingX))
            spanY = math.ceil(minHeight / (self.iconConfig.itemHeight + self.iconConfig.spacingY))

            widget["spanX"] = spanX
            widget["spanY"] = spanY

            for x in range(spanX):
                for y in range(spanY):
                    occupiedPositions.add((pos[0] + x, pos[1] + y))

        validFilepaths = []
        for filename in os.listdir(self.desktopConfig.desktopPath):
            if filename.startswith('.') or filename.lower() == 'desktop.ini':
                continue
            filepath = os.path.normpath(os.path.join(self.desktopConfig.desktopPath, filename))
            validFilepaths.append(filepath)

        updatedDesktopData = []

        for filepath in validFilepaths:
            if hasattr(self, 'pendingDropPositions') and filepath in self.pendingDropPositions:
                desiredPosition = self.pendingDropPositions.pop(filepath)

                if tuple(desiredPosition) not in occupiedPositions and desiredPosition[1] < maxRows:
                    newPosition = desiredPosition
                else:
                    newPosition = self.GetFirstFreePosition(occupiedPositions, maxRows)

                occupiedPositions.add(tuple(newPosition))

                if filepath in savedItems:
                    itemData = savedItems[filepath]
                    itemData["position"] = newPosition
                    updatedDesktopData.append(itemData)
                    continue

            elif filepath in savedItems:
                updatedDesktopData.append(savedItems[filepath])
                continue
            else:
                newPosition = self.GetFirstFreePosition(occupiedPositions, maxRows)
                occupiedPositions.add(tuple(newPosition))

            actualPath = self.GetRealTargetPath(filepath)
            itemType = "file"

            if os.path.isdir(actualPath):
                itemType = "folder_shortcut" if filepath.lower().endswith('.lnk') else "folder"
            elif actualPath.lower().endswith('.exe'):
                itemType = "exe_shortcut" if filepath.lower().endswith('.lnk') else "executable"
            elif filepath.lower().endswith('.lnk'):
                itemType = "shortcut"

            newItem = {
                "type": itemType,
                "name": os.path.basename(filepath),
                "path": filepath,
                "icon": "default",
                "position": newPosition
            }
            updatedDesktopData.append(newItem)

        for widget in savedWidgets:
            updatedDesktopData.append(widget)

        desktopData["desktop"] = updatedDesktopData

        os.makedirs(os.path.dirname(self.desktopConfig.desktopInfoFile), exist_ok = True)

        self.SaveJSONData(desktopData)

        self.RenderGrid(updatedDesktopData)

    def OnDirectoryChanged(self, path):
        actualFiles = set()
        for filename in os.listdir(self.desktopConfig.desktopPath):
            if filename.startswith('.') or filename.lower() == 'desktop.ini':
                continue
            actualFiles.add(os.path.normpath(os.path.join(self.desktopConfig.desktopPath, filename)))

        trackedFiles = {os.path.normpath(item.filepath): item for item in self.desktopItems if item.itemType != "widget"}

        for filepath in list(trackedFiles.keys()):
            if filepath not in actualFiles:
                MakeLog("[Log] [Desktop] [OnDirectoryChanged]", f"File removed externally: {filepath}")
                self.RemoveItemByPath(filepath)

        desktopData = None
        newItemsAdded = False

        for filepath in actualFiles:
            if filepath not in trackedFiles:
                MakeLog("[Log] [Desktop] [OnDirectoryChanged]", f"New file detected: {filepath}")

                if desktopData is None:
                    desktopData = self.LoadJSONData()

                occupiedPositions = set()
                for item in desktopData.get("desktop", []):
                    pos = item.get("position", [0, 0])
                    occupiedPositions.add((pos[0], pos[1]))

                maxRows = max(1, (self.height() - self.desktopConfig.windowMarginY * 2) // (self.iconConfig.itemHeight + self.iconConfig.spacingY))

                if hasattr(self, 'pendingDropPositions') and filepath in self.pendingDropPositions:
                    newPosition = self.pendingDropPositions.pop(filepath)
                    if tuple(newPosition) in occupiedPositions or newPosition[1] >= maxRows:
                        newPosition = self.GetFirstFreePosition(occupiedPositions, maxRows)
                else:
                    newPosition = self.GetFirstFreePosition(occupiedPositions, maxRows)

                occupiedPositions.add(tuple(newPosition))

                actualPath = self.GetRealTargetPath(filepath)
                itemType = "file"
                if os.path.isdir(actualPath):
                    itemType = "folder_shortcut" if filepath.lower().endswith('.lnk') else "folder"
                elif actualPath.lower().endswith('.exe'):
                    itemType = "exe_shortcut" if filepath.lower().endswith('.lnk') else "executable"
                elif filepath.lower().endswith('.lnk'):
                    itemType = "shortcut"

                newItemData = {
                    "type": itemType,
                    "name": os.path.basename(filepath),
                    "path": filepath,
                    "icon": "default",
                    "position": newPosition
                }
                desktopData.setdefault("desktop", []).append(newItemData)
                newItemsAdded = True

                item = DesktopItem(filepath, itemType, parent = self)
                positionX = self.desktopConfig.windowMarginX + newPosition[0] * (self.iconConfig.itemWidth + self.iconConfig.spacingX)
                positionY = self.desktopConfig.windowMarginY + newPosition[1] * (self.iconConfig.itemHeight + self.iconConfig.spacingY)

                item.grid_x = newPosition[0]
                item.grid_y = newPosition[1]
                item.move(positionX, positionY)
                item.show()
                self.desktopItems.append(item)

        if newItemsAdded:
            self.SaveJSONData(desktopData)

    def UpdateStyles(self, source = None, changedSections = None):
        if not changedSections:
            return

        needsUpdate = False

        if "ALL" in changedSections or source == "init":
            needsUpdate = True
        elif "Desktop" in changedSections or "Desktop.Icon" in changedSections:
            needsUpdate = True

        if not needsUpdate:
            return

        MakeLog("[Log] [Desktop]", "Live config update detected. Reloading desktop...")

        if "ALL" in changedSections or "Desktop" in changedSections or source == "init":
            self.desktopConfig.Updater()
            self.LoadWallpaper()
            self.selectionBox.setStyleSheet(self.desktopConfig.selectionStyleSheet)

        if "ALL" in changedSections or "Desktop.Icon" in changedSections or source == "init":
            self.iconConfig.Updater()

        self.ScanDesktop()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        painter.fillRect(self.rect(), QColor("black"))

        if self.backgroundBitmap and not self.backgroundBitmap.isNull():
            self.DrawCenteredPixmap(painter, self.backgroundBitmap, 1.0)

        if self.nextBackgroundBitmap and not self.nextBackgroundBitmap.isNull() and self.fadeAlpha > 0:
            self.DrawCenteredPixmap(painter, self.nextBackgroundBitmap, self.fadeAlpha)

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Window Events

    def closeEvent(self, event):
        event.ignore()

        if not hasattr(self, 'powerMenuWindow'):
            from ui.powermenu import PowerMenu
            self.powerMenuWindow = PowerMenu()

        if not self.powerMenuWindow.isVisible():
            self.powerMenuWindow.show()

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> BG Utils

    def GetScaledPixmap(self, path):
        pixmap = QPixmap(path)
        if pixmap.isNull():
            return pixmap

        if self.desktopConfig.wallpaperMode == "cover":
            return pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        elif self.desktopConfig.wallpaperMode == "contain":
            return pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        else:
            return pixmap.scaled(self.size(), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)

    def DrawCenteredPixmap(self, painter, pixmap, opacity):
        painter.setOpacity(opacity)

        x = (self.width() - pixmap.width()) // 2
        y = (self.height() - pixmap.height()) // 2

        painter.drawPixmap(x, y, pixmap)
        painter.setOpacity(1.0)

    def LoadWallpaper(self):
        if os.path.isdir(self.desktopConfig.backgroundPath):
            self.desktopConfig.wallpaperList = [
                os.path.join(
                    self.desktopConfig.backgroundPath, file
                ) for file in os.listdir(
                    self.desktopConfig.backgroundPath
                ) if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))
            ]

            if self.desktopConfig.shuffle:
                random.shuffle(self.desktopConfig.wallpaperList)
            else:
                self.desktopConfig.wallpaperList.sort()

        elif os.path.isfile(self.desktopConfig.backgroundPath):
            self.desktopConfig.wallpaperList = [self.desktopConfig.backgroundPath]

        if not self.desktopConfig.wallpaperList:
            MakeLog(f"[Log] [Desktop] [DesktopWindow] [LoadWallpaper]", f"No valid images found at {self.desktopConfig.backgroundPath}")
            self.backgroundBitmap = QPixmap(1, 1)
            self.backgroundBitmap.fill(QColor("#2E2E2E"))
            self.update()
            return

        self.currentWallpaperIndex = 0
        self.backgroundBitmap = self.GetScaledPixmap(self.desktopConfig.wallpaperList[self.currentWallpaperIndex])

        if self.desktopConfig.isCarousel and len(self.desktopConfig.wallpaperList) > 1:
            self.carouselTimer.start(round(self.desktopConfig.intervalInMin * 60 * 1000))  # to minutes

        self.update()

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Transition

    def StartTransition(self):
        self.currentWallpaperIndex = (self.currentWallpaperIndex + 1) % len(self.desktopConfig.wallpaperList)
        self.nextBackgroundBitmap = self.GetScaledPixmap(self.desktopConfig.wallpaperList[self.currentWallpaperIndex])
        self.fadeAnimation.start()

    def UpdateFade(self, value):
        self.fadeAlpha = value
        self.update()

    def EndTransition(self):
        self.backgroundBitmap = self.nextBackgroundBitmap
        self.nextBackgroundBitmap = None
        self.fadeAlpha = 0.0
        self.update()

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

    def IsPositionFree(self, startX, startY, spanX, spanY, occupiedPositions, maxRows):
        if startY + spanY > maxRows:
            return False

        for x in range(startX, startX + spanX):
            for y in range(startY, startY + spanY):
                if (x, y) in occupiedPositions:
                    return False
        return True

    def GetFirstFreePosition(self, occupiedPositions, maxRows, spanX = 1, spanY = 1):
        col = 0
        while True:
            for row in range(maxRows - spanY + 1):
                if self.IsPositionFree(col, row, spanX, spanY, occupiedPositions, maxRows):
                    return [col, row]
            col += 1

    def SnapItemToGrid(self, item, dropPosition = None, forceGridPosition = None):
        if forceGridPosition:
            targetGridX, targetGridY = forceGridPosition
        elif dropPosition:
            targetGridX = round((dropPosition.x() - self.desktopConfig.windowMarginX) / (self.iconConfig.itemWidth + self.iconConfig.spacingX))
            targetGridY = round((dropPosition.y() - self.desktopConfig.windowMarginY) / (self.iconConfig.itemHeight + self.iconConfig.spacingY))
        else:
            targetGridX = round((item.x() - self.desktopConfig.windowMarginX) / (self.iconConfig.itemWidth + self.iconConfig.spacingX))
            targetGridY = round((item.y() - self.desktopConfig.windowMarginY) / (self.iconConfig.itemHeight + self.iconConfig.spacingY))

        targetGridX = max(0, targetGridX)
        targetGridY = max(0, targetGridY)

        itemSpanX = item.widgetData.get("spanX", 1) if item.itemType == "widget" else 1
        itemSpanY = item.widgetData.get("spanY", 1) if item.itemType == "widget" else 1

        isOccupied = False
        for otherItem in self.desktopItems:
            if otherItem == item:
                continue

            otherX = getattr(otherItem, 'grid_x', -1)
            otherY = getattr(otherItem, 'grid_y', -1)
            if otherX == -1 or otherY == -1:
                continue

            otherSpanX = otherItem.widgetData.get("spanX", 1) if otherItem.itemType == "widget" else 1
            otherSpanY = otherItem.widgetData.get("spanY", 1) if otherItem.itemType == "widget" else 1

            if (
                targetGridX < otherX + otherSpanX and
                targetGridX + itemSpanX > otherX and
                targetGridY < otherY + otherSpanY and
                targetGridY + itemSpanY > otherY
            ):
                isOccupied = True
                break

        if isOccupied:
            targetGridX = item.grid_x
            targetGridY = item.grid_y
        else:
            item.grid_x = targetGridX
            item.grid_y = targetGridY

            if item.itemType == "widget":
                self.UpdateItemPositionInJSON(item.widgetData.get("id"), targetGridX, targetGridY, isWidget = True)
            else:
                self.UpdateItemPositionInJSON(item.filepath, targetGridX, targetGridY, isWidget = False)

        finalX = self.desktopConfig.windowMarginX + targetGridX * (self.iconConfig.itemWidth + self.iconConfig.spacingX)
        finalY = self.desktopConfig.windowMarginY + targetGridY * (self.iconConfig.itemHeight + self.iconConfig.spacingY)

        item.move(finalX, finalY)

    def CalculateHintGeometry(self, gridX, gridY, spanX, spanY):
        pixelWidth = (spanX * self.iconConfig.itemWidth) + ((spanX - 1) * self.iconConfig.spacingX)
        pixelHeight = (spanY * self.iconConfig.itemHeight) + ((spanY - 1) * self.iconConfig.spacingY)

        posX = self.desktopConfig.windowMarginX + (gridX * (self.iconConfig.itemWidth + self.iconConfig.spacingX))
        posY = self.desktopConfig.windowMarginY + (gridY * (self.iconConfig.itemHeight + self.iconConfig.spacingY))

        return QRect(int(posX), int(posY), int(pixelWidth), int(pixelHeight))

    def RenderGrid(self, itemsData):
        for item in self.desktopItems:
            item.deleteLater()
        self.desktopItems.clear()
        self.selectedItems.clear()

        for data in itemsData:
            filepath = data.get("path", "")
            itemType = data.get("type", "file")
            gridX, gridY = data.get("position", [0, 0])

            item = DesktopItem(filepath, itemType, parent = self, widgetData = data)

            positionX = self.desktopConfig.windowMarginX + gridX * (self.iconConfig.itemWidth + self.iconConfig.spacingX)
            positionY = self.desktopConfig.windowMarginY + gridY * (self.iconConfig.itemHeight + self.iconConfig.spacingY)

            item.grid_x = gridX
            item.grid_y = gridY

            item.move(positionX, positionY)
            item.show()

            self.desktopItems.append(item)

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

        gridX = round((event.pos().x() - self.desktopConfig.windowMarginX) / (self.iconConfig.itemWidth + self.iconConfig.spacingX))
        gridY = round((event.pos().y() - self.desktopConfig.windowMarginY) / (self.iconConfig.itemHeight + self.iconConfig.spacingY))
        self.lastContextMenuGridPos = [max(0, gridX), max(0, gridY)]

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
            self.CreateDesktopItem("New folder", isFolder = True)
        elif command == "create_text":
            self.CreateDesktopItem("New text document.txt")
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
                subprocess.Popen(target, shell=True)
            except Exception as e:
                MakeLog("[Log] [DesktopMenu] [ExecuteMenuCommand]", f"Failed to run {target}: {e}")

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> CME Commands (Misc)

    def CreateDesktopItem(self, defaultName, isFolder = False):
        basePath = os.path.join(self.desktopConfig.desktopPath, defaultName)
        path = basePath
        counter = 2

        if isFolder:
            while os.path.exists(path):
                path = f"{basePath} ({counter})"
                counter += 1
        else:
            namePart, extPart = os.path.splitext(defaultName)
            while os.path.exists(path):
                path = os.path.join(self.desktopConfig.desktopPath, f"{namePart} ({counter}){extPart}")
                counter += 1

        try:
            if hasattr(self, 'lastContextMenuGridPos'):
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

            for url in mimeData.urls():
                sourcePath = os.path.normpath(url.toLocalFile())
                if not os.path.exists(sourcePath):
                    continue

                filename = os.path.basename(sourcePath)
                targetPath = os.path.join(self.desktopConfig.desktopPath, filename)

                counter = 2
                baseName, ext = os.path.splitext(filename)
                while os.path.exists(targetPath):
                    targetPath = os.path.join(self.desktopConfig.desktopPath, f"{baseName} ({counter}){ext}")
                    counter += 1

                try:
                    if isCut:
                        MakeLog("[Log] [Desktop]", f"Moving (Cut) file: {sourcePath} to {targetPath}")
                        shutil.move(sourcePath, targetPath)
                    else:
                        MakeLog("[Log] [Desktop]", f"Copying file: {sourcePath} to {targetPath}")
                        if os.path.isdir(sourcePath):
                            shutil.copytree(sourcePath, targetPath)
                        else:
                            shutil.copy2(sourcePath, targetPath)
                except Exception as e:
                    MakeLog("[Log] [Desktop]", f"Paste error: {e}")

            if isCut:
                clipboard.clear()

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Drag & drop events

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasFormat("application/x-ninawe-widget"):

            self.draggedItemSpanX = 1
            self.draggedItemSpanY = 1

            if event.mimeData().hasFormat("application/x-ninawe-widget"):
                try:
                    data = event.mimeData().data("application/x-ninawe-widget").data().decode('utf-8')
                    parts = data.split(":")
                    if len(parts) == 3:
                        self.draggedItemSpanX = int(parts[1])
                        self.draggedItemSpanY = int(parts[2])
                except Exception:
                    pass

            self.gridHint.show()
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasFormat("application/x-ninawe-widget"):
            if not self.gridHint.isVisible():
                self.gridHint.show()

            offsetX, offsetY = 0, 0
            if event.mimeData().hasFormat("application/x-ninawe-offset"):
                try:
                    parts = event.mimeData().data("application/x-ninawe-offset").data().decode('utf-8').split(':')
                    offsetX, offsetY = int(parts[0]), int(parts[1])
                except Exception:
                    pass

            visualX = event.position().x() - offsetX
            visualY = event.position().y() - offsetY

            targetGridX = round((visualX - self.desktopConfig.windowMarginX) / (self.iconConfig.itemWidth + self.iconConfig.spacingX))
            targetGridY = round((visualY - self.desktopConfig.windowMarginY) / (self.iconConfig.itemHeight + self.iconConfig.spacingY))

            targetGridX = max(0, targetGridX)
            targetGridY = max(0, targetGridY)

            hintGeometry = self.CalculateHintGeometry(targetGridX, targetGridY, self.draggedItemSpanX, self.draggedItemSpanY)
            self.gridHint.setGeometry(hintGeometry)

            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()

    def dropEvent(self, event):
        offsetX, offsetY = 0, 0
        if event.mimeData().hasFormat("application/x-ninawe-offset"):
            try:
                parts = event.mimeData().data("application/x-ninawe-offset").data().decode('utf-8').split(':')
                offsetX, offsetY = int(parts[0]), int(parts[1])
            except Exception:
                pass

        visualX = event.position().x() - offsetX
        visualY = event.position().y() - offsetY

        targetGridX = round((visualX - self.desktopConfig.windowMarginX) / (self.iconConfig.itemWidth + self.iconConfig.spacingX))
        targetGridY = round((visualY - self.desktopConfig.windowMarginY) / (self.iconConfig.itemHeight + self.iconConfig.spacingY))
        targetGridX = max(0, targetGridX)
        targetGridY = max(0, targetGridY)

        if event.mimeData().hasFormat("application/x-ninawe-widget"):
            self.gridHint.hide()
            rawData = event.mimeData().data("application/x-ninawe-widget").data().decode('utf-8')
            parts = rawData.split(":")
            if len(parts) >= 1:
                widgetID = parts[0]
                widgetItem = next((i for i in self.desktopItems if i.itemType == "widget" and i.widgetData.get("id") == widgetID), None)

                if widgetItem:
                    self.SnapItemToGrid(widgetItem, forceGridPosition = (targetGridX, targetGridY))

            event.acceptProposedAction()
            return

        urls = event.mimeData().urls()
        if not urls:
            return

        self.gridHint.hide()
        newFilesAdded = False

        internalMoves = []
        action = event.dropAction()

        externalFilesCount = 0

        for url in urls:
            filepath = os.path.normpath(url.toLocalFile())
            if not filepath or not os.path.exists(filepath):
                continue

            if os.path.normpath(os.path.dirname(filepath)) != self.desktopConfig.desktopPath:
                try:
                    targetPath = os.path.join(self.desktopConfig.desktopPath, os.path.basename(filepath))
                    if not os.path.exists(targetPath):
                        if action == Qt.DropAction.CopyAction:
                            if os.path.isdir(filepath):
                                shutil.copytree(filepath, targetPath)
                            else:
                                shutil.copy2(filepath, targetPath)
                        else:
                            shutil.move(filepath, targetPath)

                        self.pendingDropPositions[targetPath] = [targetGridX, targetGridY + externalFilesCount]
                        externalFilesCount += 1

                        newFilesAdded = True
                except Exception as e:
                    MakeLog(f"[Log] [Desktop]", f"File operation error: {e}")

            else:
                internalMoves.append(filepath)

        if internalMoves:
            primaryFilepath = internalMoves[0]
            primaryItem = next((i for i in self.desktopItems if os.path.normpath(i.filepath) == primaryFilepath), None)

            if primaryItem:
                deltaX = targetGridX - primaryItem.grid_x
                deltaY = targetGridY - primaryItem.grid_y

                for filepath in internalMoves:
                    item = next((i for i in self.desktopItems if os.path.normpath(i.filepath) == filepath), None)
                    if item:
                        newX = item.grid_x + deltaX
                        newY = item.grid_y + deltaY
                        self.SnapItemToGrid(item, forceGridPosition = (newX, newY))

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

            if hasattr(self, 'cutItems') and itemToRemove in self.cutItems:
                self.cutItems.remove(itemToRemove)

            self.RemoveItemFromJSON(itemToRemove.filepath)
            itemToRemove.deleteLater()

    def GetRealTargetPath(self, filepath):
        if filepath.lower().endswith('.lnk'):
            try:
                shortcut = self.WSHELL.CreateShortCut(filepath)
                target = shortcut.Targetpath
                if target and os.path.exists(target):
                    return target
            except Exception as e:
                MakeLog(f"[Log] [Desktop]", f"Failed to resolve shortcut {filepath}: {e}")
        return filepath

    def UpdateItemPositionInJSON(self, identifier, gridX, gridY, isWidget = False):
        try:
            desktopData = self.LoadJSONData()

            for data in desktopData.get("desktop", []):
                if isWidget and data.get("type") == "widget":
                    if data.get("id") == identifier:
                        data["position"] = [gridX, gridY]
                        break
                elif not isWidget and data.get("type") != "widget":
                    if data.get("path") == identifier:
                        data["position"] = [gridX, gridY]
                        break

            self.SaveJSONData(desktopData)

        except Exception as e:
            MakeLog(f"[Log] [Desktop]", f"Failed to save new position for {identifier}: {e}")

    def RemoveItemFromJSON(self, identifier, isWidget = False):
        try:
            desktopData = self.LoadJSONData()

            if isWidget:
                desktopData["desktop"] = [item for item in desktopData.get("desktop", []) if not (item.get("type") == "widget" and item.get("id") == identifier)]
            else:
                desktopData["desktop"] = [item for item in desktopData.get("desktop", []) if item.get("path") != identifier]

            self.SaveJSONData(desktopData)

        except Exception as e:
            MakeLog(f"[Log] [Desktop]", f"Failed to remove item {identifier} from JSON: {e}")

    def LoadJSONData(self):
        with open(self.desktopConfig.desktopInfoFile, "r", encoding = "utf-8") as f:
            desktopData = json.load(f)

        return desktopData

    def SaveJSONData(self, data):
        with open(self.desktopConfig.desktopInfoFile, "w", encoding="utf-8") as JSONFile:
            json.dump(data, JSONFile, indent = 4, ensure_ascii = False)

class DesktopItem(QWidget):
    def __init__(self, filepath, itemType = "file", parent = None, widgetData = None):
        super().__init__(parent)
        self.filepath = filepath
        self.itemType = itemType
        self.widgetData = widgetData
        self.filename = os.path.basename(filepath) if filepath else ""
        self.iconConfig = parent.iconConfig if parent else IconConfig()
        self.WSHELL = parent.WSHELL if parent else win32com.client.Dispatch("WScript.Shell")

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        if self.itemType in ["folder", "folder_shortcut", "executable", "exe_shortcut"]:
            self.setAcceptDrops(True)

        if self.filename.lower().endswith('.lnk'):
            self.filename = self.filename[:-4]

        self.Init()

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Main

    def Init(self):
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self.innerFrame = QFrame()
        self.innerFrame.setObjectName("IconFrame")
        frameLayout = QVBoxLayout(self.innerFrame)
        frameLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frameLayout.setContentsMargins(0, 0, 0, 0)

        if self.itemType == "widget" and self.widgetData:
            self.innerFrame.setObjectName("WidgetFrame")

            spanX = self.widgetData.get("spanX", 1)
            spanY = self.widgetData.get("spanY", 1)

            pixelWidth = (spanX * self.iconConfig.itemWidth) + ((spanX - 1) * self.iconConfig.spacingX)
            pixelHeight = (spanY * self.iconConfig.itemHeight) + ((spanY - 1) * self.iconConfig.spacingY)

            self.setFixedSize(pixelWidth, pixelHeight)
            self.innerFrame.setFixedSize(pixelWidth, pixelHeight)

            widgetName = self.widgetData.get("name", "")

            try:
                widgetClass = WidgetManager.GetWidgetClass("desktop", widgetName)
                if widgetClass:
                    widgetInstance = widgetClass(self)

                    self.widgetInstance = widgetInstance

                    frameLayout.addWidget(widgetInstance)
            except Exception as e:
                MakeLog("[Log] [DesktopItem]", f"Failed to load widget '{widgetName}': {e}")

        else:
            self.setFixedWidth(self.iconConfig.itemWidth)
            self.setMinimumHeight(self.iconConfig.itemHeight)
            self.innerFrame.setFixedWidth(self.iconConfig.itemWidth - 4)
            frameLayout.setContentsMargins(0, 2, 0, 2)

            actualIconPath = self.filepath
            if self.filepath and self.filepath.lower().endswith('.lnk'):
                try:
                    shortcut = self.WSHELL.CreateShortCut(self.filepath)
                    target = shortcut.Targetpath
                    if target and os.path.exists(target):
                        actualIconPath = target
                except Exception as exc:
                    MakeLog(f"[Log] [DesktopItem]", f"Failed to resolve shortcut {self.filepath}: {exc}")

            provider = QFileIconProvider()
            fileInfo = QFileInfo(actualIconPath)
            icon = provider.icon(fileInfo)

            self.iconLabel = QLabel()
            self.iconLabel.setPixmap(icon.pixmap(self.iconConfig.bitmapSize, self.iconConfig.bitmapSize))
            self.iconLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
            frameLayout.addWidget(self.iconLabel)

            if self.iconConfig.iconLabelStatus:
                parts = re.split(r'( +)', self.filename)
                name = []
                currentLine = ""

                for part in parts:
                    if part.strip() != "" and len(part) > self.LabelSize() - 3:
                        part = part[:self.LabelSize() - 3] + "..."
                    if len(currentLine) + len(part) <= self.LabelSize():
                        currentLine += part
                    else:
                        if part.strip() == "":
                            continue
                        name.append(currentLine.rstrip())
                        currentLine = part
                        if len(name) == 2:
                            currentLine = ""
                            break

                if currentLine:
                    name.append(currentLine)

                displayName = "\n".join(name).strip()
                self.textLabel = QLabel(displayName)
                self.textLabel.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
                self.textLabel.setMaximumWidth(self.iconConfig.itemWidth)
                self.textLabel.setStyleSheet(self.iconConfig.labelStyleSheet)

                shadow = QGraphicsDropShadowEffect(self.textLabel)
                shadow.setBlurRadius(5)
                shadow.setXOffset(0)
                shadow.setYOffset(0)
                shadow.setColor(QColor(0, 0, 0, 255))
                self.textLabel.setGraphicsEffect(shadow)

                frameLayout.addWidget(self.textLabel)

        mainLayout.addWidget(self.innerFrame)
        self.setStyleSheet(self.iconConfig.iconStyleSheet)

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Misc

    def LabelSize(self):
        font = QFont(self.iconConfig.iconLabelFontFamily, self.iconConfig.iconLabelFontSize)
        fm = QFontMetrics(font)

        avgCharWidth = fm.averageCharWidth()

        return (self.iconConfig.itemWidth // avgCharWidth) + self.iconConfig.iconLabelCompensator

    def SetSelected(self, isSelected):
        self.innerFrame.setProperty("selected", isSelected)
        self.innerFrame.style().unpolish(self.innerFrame)
        self.innerFrame.style().polish(self.innerFrame)

    def SetHoverDrop(self, isHovered):
        self.innerFrame.setProperty("drop_hover", isHovered)
        self.innerFrame.style().unpolish(self.innerFrame)
        self.innerFrame.style().polish(self.innerFrame)

    def OpenFile(self):
        try:
            if self.parent():
                self.parent().ClearSelection()
            os.startfile(self.filepath)
        except Exception as e:
            MakeLog("[Log] [DesktopItem] [OpenFile]", f"Failed to start {self.filepath}: {e}")

    def SetCutState(self, isCut):
        if isCut:
            effect = QGraphicsOpacityEffect(self)
            effect.setOpacity(0.5)
            self.setGraphicsEffect(effect)
        else:
            self.setGraphicsEffect(None)

    def StartRename(self):
        if hasattr(self, 'textLabel'):
            self.textLabel.hide()

        self.nameEditor = RenameEditor(self.filename, self.innerFrame)
        self.nameEditor.finishCallback = self.FinishRename

        self.nameEditor.setStyleSheet("""
            QLineEdit {
                background: white;
                color: black;
                border: 1px solid #0078D7;
                selection-background-color: #0078D7;
                padding: 0px;
                margin: 0px 4px 0px 4px;
                border-radius: 2px;
            }
        """)
        self.nameEditor.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.innerFrame.layout().addWidget(self.nameEditor)

        self.nameEditor.show()
        self.nameEditor.setFocus()

        baseName = os.path.splitext(self.filename)[0]
        self.nameEditor.setSelection(0, len(baseName))

        self.nameEditor.returnPressed.connect(self.FinishRename)

    def FinishRename(self):
        if not hasattr(self, 'nameEditor'):
            return

        newName = self.nameEditor.text().strip()

        self.nameEditor.deleteLater()
        del self.nameEditor
        if hasattr(self, 'textLabel'):
            self.textLabel.show()

        if not newName or newName == self.filename:
            return

        originalExtension = os.path.splitext(self.filepath)[1]
        if originalExtension.lower() == '.lnk' and not newName.lower().endswith('.lnk'):
            newName += originalExtension

        newPath = os.path.join(os.path.dirname(self.filepath), newName)

        if os.path.exists(newPath):
            MakeLog("[Log] [DesktopItem]", f"File with this name already exists! {newPath}")
            return

        parent = self.parent()
        if parent:
            parent.pendingDropPositions[newPath] = [self.grid_x, self.grid_y]

        try:
            os.rename(self.filepath, newPath)
            MakeLog("[Log] [DesktopItem]", f"Renamed: {self.filepath} -> {newPath}")
        except Exception as e:
            MakeLog("[Log] [DesktopItem]", f"Rename error: {e}")

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Mouse events

    def mousePressEvent(self, event):
        self.setFocus()
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragStartPos = event.pos()
            self.raise_()

            ctrlButtonPressedStatus = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
            if self.parent():
                self.parent().ItemClicked(self, ctrlButtonPressedStatus)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            if hasattr(self, 'dragStartPos') and self.dragStartPos:
                if (event.pos() - self.dragStartPos).manhattanLength() > 5:

                    drag = QDrag(self)
                    mimeData = QMimeData()
                    urls = []

                    hotspotX = self.dragStartPos.x()
                    hotspotY = self.dragStartPos.y()
                    mimeData.setData("application/x-ninawe-offset", f"{hotspotX}:{hotspotY}".encode('utf-8'))

                    if self.itemType == "widget":
                        widgetData = f"{self.widgetData.get('id', '')}:{self.widgetData.get('spanX', 1)}:{self.widgetData.get('spanY', 1)}"

                        mimeData.setData("application/x-ninawe-widget", widgetData.encode('utf-8'))
                    else:
                        parent = self.parent()

                        if parent and hasattr(parent, 'selectedItems') and self in parent.selectedItems:
                            urls.append(QUrl.fromLocalFile(self.filepath))
                            for item in parent.selectedItems:
                                if item != self and item.itemType != "widget":
                                    urls.append(QUrl.fromLocalFile(item.filepath))
                        else:
                            urls.append(QUrl.fromLocalFile(self.filepath))

                        mimeData.setUrls(urls)

                    drag.setMimeData(mimeData)

                    self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

                    wasSelected = self.innerFrame.property("selected")
                    if wasSelected:
                        self.SetSelected(False)

                    pixmap = self.innerFrame.grab()
                    drag.setPixmap(pixmap)

                    if wasSelected:
                        self.SetSelected(True)

                    drag.setHotSpot(event.pos())

                    action = drag.exec(Qt.DropAction.MoveAction | Qt.DropAction.CopyAction)

                    self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
                    self.SetHoverDrop(False)

                    for url in urls:
                        path = os.path.normpath(url.toLocalFile())
                        if not os.path.exists(path):
                            if parent:
                                parent.RemoveItemByPath(path)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragStartPos = None

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.itemType == "widget":
                return
            self.OpenFile()

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Context Menu

    def contextMenuEvent(self, event):
        parent = self.parent()
        if not parent:
            return

        if not self.innerFrame.property("selected"):
            parent.ClearSelection()
            self.SetSelected(True)
            parent.selectedItems.append(self)

        if self.itemType == "widget":
            widgetName = self.widgetData.get("name", "")

            userPath = configurator.theme.GetPath(f"userdata\\widgets\\desktop\\{widgetName}\\contextmenu.json")
            appPath = configurator.theme.GetPath(f"app\\widgets\\desktop\\{widgetName}\\contextmenu.json")

            customPath = None
            if os.path.exists(userPath):
                customPath = userPath
            elif os.path.exists(appPath):
                customPath = appPath

            menu = ContextMenu("widget", self, customPath = customPath)
        else:
            menu = ContextMenu("item", self)

        if menu.isEmpty():
            return

        menu.commandClicked.connect(self.ExecuteItemCommand)
        menu.exec(event.globalPos())

    def ExecuteItemCommand(self, command):
        if not command or command == "none":
            return

        MakeLog("[Log] [DesktopItem]", f"Executing item command: {command} on {self.filepath}")

        if command == "open":
            self.OpenFile()
        elif command == "delete":
            parent = self.parent()

            itemsToDelete = []

            if parent and hasattr(parent, 'selectedItems') and self in parent.selectedItems:
                itemsToDelete = list(parent.selectedItems)
            else:
                itemsToDelete = [self]

            for item in itemsToDelete:
                try:
                    if parent:
                        if item in parent.selectedItems:
                            parent.selectedItems.remove(item)
                        if item in parent.previouslySelectedItems:
                            parent.previouslySelectedItems.remove(item)
                        if item in parent.cutItems:
                            parent.cutItems.remove(item)

                    if item.itemType == "widget":
                        widgetId = item.widgetData.get("id")
                        if parent:
                            parent.RemoveItemFromJSON(widgetId, isWidget = True)
                            if item in parent.desktopItems:
                                parent.desktopItems.remove(item)

                        if hasattr(item, 'widgetInstance') and hasattr(item.widgetInstance, 'deleteLater'):
                            item.widgetInstance.deleteLater()

                        item.deleteLater()
                        MakeLog("[Log] [DesktopItem]", f"Deleted widget: {widgetId}")

                    else:
                        if os.path.isdir(item.filepath):
                            shutil.rmtree(item.filepath)
                        else:
                            os.remove(item.filepath)
                        MakeLog("[Log] [DesktopItem]", f"Deleted: {item.filepath}")
                except Exception as e:
                    MakeLog("[Log] [DesktopItem]", f"Failed to delete: {e}")

            if parent and itemsToDelete != [self]:
                parent.ClearSelection()
        elif command == "properties":
            self.ShowWindowsProperties()
        elif command in ["copy", "cut"]:
            clipboard = QApplication.clipboard()
            mimeData = QMimeData()

            urls = []
            parent = self.parent()

            if parent and hasattr(parent, 'cutItems'):
                for item in parent.cutItems:
                    try:
                        item.SetCutState(False)
                    except RuntimeError:
                        pass
                parent.cutItems.clear()

            if parent and hasattr(parent, 'selectedItems') and self in parent.selectedItems:
                for item in parent.selectedItems:
                    urls.append(QUrl.fromLocalFile(item.filepath))

                    if command == "cut":
                        item.SetCutState(True)
                        parent.cutItems.append(item)
            else:
                urls.append(QUrl.fromLocalFile(self.filepath))
                if command == "cut":
                    self.SetCutState(True)
                    if parent:
                        parent.cutItems.append(self)

            mimeData.setUrls(urls)

            # x02 - cut, x05 - copy
            dropEffect = b'\x02\x00\x00\x00' if command == "cut" else b'\x05\x00\x00\x00'
            mimeData.setData("Preferred DropEffect", dropEffect)

            clipboard.setMimeData(mimeData)
            MakeLog("[Log] [DesktopItem]", f"Items {command}ed to clipboard")
        elif command == "rename":
            self.StartRename()

    def ShowWindowsProperties(self):
        sei = ShellExecuteInfo()
        sei.cbSize = ctypes.sizeof(sei)
        sei.fMask = SEE_MASK_INVOKEIDLIST
        sei.lpVerb = "properties"
        sei.lpFile = os.path.normpath(self.filepath)
        sei.nShow = 1

        ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(sei))

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Drag & drop events

    def dragEnterEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            filepaths = [url.toLocalFile() for url in urls]
            if self.filepath in filepaths:
                return

        if self.itemType in ["folder", "folder_shortcut", "executable", "exe_shortcut"] and event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
            self.SetHoverDrop(True)

            parent = self.parent()
            if parent and hasattr(parent, 'gridHint'):
                parent.gridHint.hide()

    def dragMoveEvent(self, event):
        if self.itemType in ["folder", "folder_shortcut", "executable", "exe_shortcut"] and event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()

    def dragLeaveEvent(self, event):
        self.SetHoverDrop(False)

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            return

        self.SetHoverDrop(False)
        filepaths = [url.toLocalFile() for url in urls]

        parent = self.parent()
        targetRealPath = parent.GetRealTargetPath(self.filepath) if parent else self.filepath

        if self.itemType in ["folder", "folder_shortcut"]:
            for path in filepaths:
                newFilepath = os.path.join(targetRealPath, os.path.basename(path))
                if os.path.exists(newFilepath):
                    continue
                try:
                    shutil.move(path, newFilepath)
                    if parent:
                        parent.RemoveItemByPath(path)
                except Exception as e:
                    MakeLog("[Log] [DesktopItem]", f" Move error: {e}")

        elif self.itemType in ["executable", "exe_shortcut"]:
            for path in filepaths:
                try:
                    subprocess.Popen([targetRealPath, path])
                except Exception as e:
                    MakeLog("[Log] [DesktopItem]", f"Error while opening: {e}")

        event.acceptProposedAction()


# OH MY GOD, MY HEART IS BEATING SO MUCH I'M AFRAID I MIGHT DIE BEFORE FINISHING THIS
