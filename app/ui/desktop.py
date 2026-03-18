import os
import random
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QFileIconProvider, QGraphicsDropShadowEffect, QFrame
from PyQt6.QtGui import QPainter, QPixmap, QColor, QIcon, QPen, QBrush, QDrag, QFontMetrics, QFont
from PyQt6.QtCore import Qt, QTimer, QVariantAnimation, QFileInfo, QRect, QMimeData, QUrl
from core.config import config as configurator
import win32com.client
import json
import shutil
import subprocess
from core.utils import MakeLog, LoadFont
import re

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

        self.iconHoverColors = {}
        self.iconSelectedColors = {}
        self.iconHoverOnSelectedColors = {}
        self.iconDropColors = {}

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

        self.iconHoverColors["background"] = configurator.theme.Get("Desktop.Icon", "icon_hover_background", fallback = "#44FFFFFF")
        self.iconHoverColors["border"] = configurator.theme.Get("Desktop.Icon", "icon_hover_border", fallback = "#55FFFFFF")

        self.iconSelectedColors["background"] = configurator.theme.Get("Desktop.Icon", "icon_selected_background", fallback = "#55FFFFFF")
        self.iconSelectedColors["border"] = configurator.theme.Get("Desktop.Icon", "icon_selected_border", fallback = "#66FFFFFF")

        self.iconHoverOnSelectedColors["background"] = configurator.theme.Get("Desktop.Icon", "icon_hover_on_selected_background", fallback = "#66FFFFFF")
        self.iconHoverOnSelectedColors["border"] = configurator.theme.Get("Desktop.Icon", "icon_hover_on_selected_border", fallback = "#77FFFFFF")

        self.iconDropColors["background"] = configurator.theme.Get("Desktop.Icon", "icon_drop_background", fallback = "#77FFFFFF")
        self.iconDropColors["border"] = configurator.theme.Get("Desktop.Icon", "icon_drop_border", fallback = "#88FFFFFF")

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
                background: {self.iconHoverColors.get("background")};
                border: {self.containerBorder}px solid {self.iconHoverColors.get("border")};
            }}
            QFrame#IconFrame[selected = "true"] {{
                background: {self.iconSelectedColors.get("background")};
                border: {self.containerBorder}px solid {self.iconSelectedColors.get("border")};
            }}
            QFrame#IconFrame[selected = "true"]:hover {{
                background: {self.iconHoverOnSelectedColors.get("background")};
                border: {self.containerBorder}px solid {self.iconHoverOnSelectedColors.get("border")};
            }}
            QFrame#IconFrame[drop_hover = "true"] {{
                background: {self.iconDropColors.get("background")};
                border: {self.containerBorder}px solid {self.iconDropColors.get("border")};
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
        self.groudSelectionColors = {}
        self.wallpaperMode = None
        self.windowMarginX = 0
        self.windowMarginY = 0
        self.isCarousel = None
        self.intervalInMin = None
        self.shuffle = None
        self.backgroundPath = None
        self.transitionMs = 0
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
        self.groudSelectionBorderRadius = configurator.theme.GetInt("Desktop", "group_selection_border_radius", fallback = 0)
        self.groudSelectionBorderWidth = configurator.theme.GetInt("Desktop", "group_selection_border_width", fallback = 0)
        self.groudSelectionColors["background"] = configurator.theme.Get("Desktop", "group_selection_background", fallback = "#55FFFFFF")
        self.groudSelectionColors["border"] = configurator.theme.Get("Desktop", "group_selection_background", fallback = "#66FFFFFF")
        self.selectionStyleSheet = f"""
            background-color: {self.groudSelectionColors.get("background")};
            border: {self.groudSelectionBorderWidth}px solid {self.groudSelectionColors.get("border")};
            border-radius: {self.groudSelectionBorderRadius}px;
        """

class DesktopWindow(QMainWindow):
    def __init__(self):
        super().__init__()

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

        configurator.configUpdated.connect(self.UpdateStyles)

        # ahhhhh I'm too lazy to comment all the code :(
        # i think I'll do it next time
        self.Init()

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Main

    def Init(self):
        self.setWindowTitle("Ninawe Desktop")
        self.setAcceptDrops(True)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnBottomHint
        )

        # screen resolution
        screen = self.screen().geometry()
        self.setGeometry(screen)

        self.fadeAnimation.setDuration(self.desktopConfig.transitionMs)
        self.fadeAnimation.setStartValue(0.0)
        self.fadeAnimation.setEndValue(1.0)

        MakeLog(f"[Log] [Desktop]", f"Loading wallpaper: {self.desktopConfig.backgroundPath} (Mode: {self.desktopConfig.wallpaperMode})")

        self.LoadWallpaper()

        self.desktopItems = []
        self.selectedItems = []

        self.isSelectingStatus = False
        self.selectionStart = None
        self.previouslySelectedItems = []

        self.selectionBox = QWidget(self)
        self.selectionBox.setStyleSheet(self.desktopConfig.selectionStyleSheet)
        self.selectionBox.hide()
        self.hoveredDropTarget = None

        self.pendingDropPositions = {}

        self.ScanDesktop()

    def ScanDesktop(self):
        desktopData = {"desktop": []}
        if os.path.exists(self.desktopConfig.desktopInfoFile):
            try:
                desktopData = self.LoadJSONData()
            except Exception as e:
                MakeLog(f"[Log] [Desktop]", f"Failed to read JSON: {e}")

        savedItems = {os.path.normpath(item["path"]): item for item in desktopData.get("desktop", []) if "path" in item}

        if not os.path.exists(self.desktopConfig.desktopPath):
            MakeLog("[Log] [Desktop]", f"Desktop folder not found!")
            return

        maxRows = max(1, (self.height() - self.desktopConfig.windowMarginY * 2) // (self.iconConfig.itemHeight + self.iconConfig.spacingY))

        occupiedPositions = set()
        for item in savedItems.values():
            pos = item.get("position", [0, 0])
            occupiedPositions.add((pos[0], pos[1]))

        valid_filepaths = []
        for filename in os.listdir(self.desktopConfig.desktopPath):
            if filename.startswith('.') or filename.lower() == 'desktop.ini':
                continue
            filepath = os.path.normpath(os.path.join(self.desktopConfig.desktopPath, filename))
            valid_filepaths.append(filepath)

        updatedDesktopData = []

        for filepath in valid_filepaths:
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

        desktopData["desktop"] = updatedDesktopData

        os.makedirs(os.path.dirname(self.desktopConfig.desktopInfoFile), exist_ok = True)

        self.SaveJSONData(desktopData)

        self.RenderGrid(updatedDesktopData)

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
            MakeLog(f"[Log] [Desktop] [DesktopWindow] [LoadWallpaper]", f"No valid images found at {path}")
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

    def GetFirstFreePosition(self, occupiedPositions, maxRows):
        col = 0
        while True:
            for row in range(maxRows):
                if (col, row) not in occupiedPositions:
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

        isOccupied = False
        for otherItem in self.desktopItems:
            if otherItem != item and getattr(otherItem, 'grid_x', -1) == targetGridX and getattr(otherItem, 'grid_y', -1) == targetGridY:
                isOccupied = True
                break

        if isOccupied:
            targetGridX = item.grid_x
            targetGridY = item.grid_y
        else:
            item.grid_x = targetGridX
            item.grid_y = targetGridY
            self.UpdateItemPositionInJSON(item.filepath, targetGridX, targetGridY)

        finalX = self.desktopConfig.windowMarginX + targetGridX * (self.iconConfig.itemWidth + self.iconConfig.spacingX)
        finalY = self.desktopConfig.windowMarginY + targetGridY * (self.iconConfig.itemHeight + self.iconConfig.spacingY)

        item.move(finalX, finalY)

    def RenderGrid(self, itemsData):
        for item in self.desktopItems:
            item.deleteLater()
        self.desktopItems.clear()
        self.selectedItems.clear()

        for data in itemsData:
            if data.get("type") == "widget":
                continue

            filepath = data.get("path")
            itemType = data.get("type", "file")
            gridX, gridY = data.get("position", [0, 0])

            item = DesktopItem(filepath, itemType, parent = self)

            positionX = self.desktopConfig.windowMarginX + gridX * (self.iconConfig.itemWidth + self.iconConfig.spacingX)
            positionY = self.desktopConfig.windowMarginY + gridY * (self.iconConfig.itemHeight + self.iconConfig.spacingY)

            item.grid_x = gridX
            item.grid_y = gridY

            item.move(positionX, positionY)
            item.show()

            self.desktopItems.append(item)

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Mouse events

    def mousePressEvent(self, event):
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

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Drag & drop events

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            return

        newFilesAdded = False
        dropPosition = event.position().toPoint()

        internalMoves = []
        action = event.dropAction()

        targetGridX = round((dropPosition.x() - self.desktopConfig.windowMarginX) / (self.iconConfig.itemWidth + self.iconConfig.spacingX))
        targetGridY = round((dropPosition.y() - self.desktopConfig.windowMarginY) / (self.iconConfig.itemHeight + self.iconConfig.spacingY))
        targetGridX = max(0, targetGridX)
        targetGridY = max(0, targetGridY)

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

        if newFilesAdded:
            self.ScanDesktop()

        if internalMoves:
            primary_filepath = internalMoves[0]
            primaryItem = next((i for i in self.desktopItems if os.path.normpath(i.filepath) == primary_filepath), None)

            if primaryItem:
                targetGridX = round((dropPosition.x() - self.desktopConfig.windowMarginX) / (self.iconConfig.itemWidth + self.iconConfig.spacingX))
                targetGridY = round((dropPosition.y() - self.desktopConfig.windowMarginY) / (self.iconConfig.itemHeight + self.iconConfig.spacingY))

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

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> File utils

    def RemoveItemByPath(self, filepath):
        filepath = os.path.normpath(filepath)

        itemToRemove = next((item for item in self.desktopItems if os.path.normpath(item.filepath) == filepath), None)

        if itemToRemove:
            self.desktopItems.remove(itemToRemove)
            if itemToRemove in self.selectedItems:
                self.selectedItems.remove(itemToRemove)

            self.RemoveItemFromJSON(itemToRemove.filepath)
            itemToRemove.deleteLater()

    def GetRealTargetPath(self, filepath):
        if filepath.lower().endswith('.lnk'):
            try:
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(filepath)
                target = shortcut.Targetpath
                if target and os.path.exists(target):
                    return target
            except Exception as e:
                MakeLog(f"[Log] [Desktop]", f"Failed to resolve shortcut {filepath}: {e}")
        return filepath

    def UpdateItemPositionInJSON(self, filepath, gridX, gridY):
        try:
            desktopData = self.LoadJSONData()

            for data in desktopData.get("desktop", []):
                if data.get("path") == filepath:
                    data["position"] = [gridX, gridY]
                    break

            self.SaveJSONData(desktopData)

        except Exception as e:
            MakeLog(f"[Log] [Desktop]", f"Failed to save new position for {filepath}: {e}")

    def RemoveItemFromJSON(self, filepath):
        try:
            desktopData = self.LoadJSONData()

            desktopData["desktop"] = [item for item in desktopData.get("desktop", []) if item.get("path") != filepath]

            self.SaveJSONData(desktopData)

        except Exception as e:
            MakeLog(f"[Log] [Desktop]", f"Failed to remove item {filepath} from JSON: {e}")

    def LoadJSONData(self):
        with open(self.desktopConfig.desktopInfoFile, "r", encoding = "utf-8") as f:
            desktopData = json.load(f)

        return desktopData

    def SaveJSONData(self, data):
        with open(self.desktopConfig.desktopInfoFile, "w", encoding="utf-8") as JSONFile:
            json.dump(data, JSONFile, indent = 4, ensure_ascii = False)

class DesktopItem(QWidget):
    def __init__(self, filepath, itemType = "file", parent = None):
        super().__init__(parent)
        self.filepath = filepath
        self.itemType = itemType
        self.filename = os.path.basename(filepath)
        self.iconConfig = parent.iconConfig if parent else IconConfig()

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        if self.itemType in ["folder", "folder_shortcut", "executable", "exe_shortcut"]:
            self.setAcceptDrops(True)

        if self.filename.lower().endswith('.lnk'):
            self.filename = self.filename[:-4]

        self.Init()

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Main

    def Init(self):
        self.setFixedWidth(self.iconConfig.itemWidth)
        self.setMinimumHeight(self.iconConfig.itemHeight)

        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self.innerFrame = QFrame()
        self.innerFrame.setObjectName("IconFrame")

        self.innerFrame.setFixedWidth(self.iconConfig.itemWidth - 4)

        frameLayout = QVBoxLayout(self.innerFrame)
        frameLayout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        frameLayout.setContentsMargins(0, 2, 0, 2)
        actualIconPath = self.filepath

        if self.filepath.lower().endswith('.lnk'):
            try:
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(self.filepath)
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

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Mouse events

    def mousePressEvent(self, event):
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
                    parent = self.parent()

                    if parent and hasattr(parent, 'selectedItems') and self in parent.selectedItems:
                        urls.append(QUrl.fromLocalFile(self.filepath))

                        for item in parent.selectedItems:
                            if item != self:
                                urls.append(QUrl.fromLocalFile(item.filepath))
                    else:
                        urls.append(QUrl.fromLocalFile(self.filepath))

                    mimeData.setUrls(urls)
                    drag.setMimeData(mimeData)

                    self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

                    was_selected = self.innerFrame.property("selected")
                    if was_selected:
                        self.SetSelected(False)

                    pixmap = self.innerFrame.grab()
                    drag.setPixmap(pixmap)

                    if was_selected:
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
            try:
                if self.parent():
                    self.parent().ClearSelection()
                os.startfile(self.filepath)
            except Exception as e:
                MakeLog("[Log] [DesktopItem]", f"Failed to start {self.filepath}: {e}")

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
                new_filepath = os.path.join(targetRealPath, os.path.basename(path))
                if os.path.exists(new_filepath):
                    continue
                try:
                    shutil.move(path, new_filepath)
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
