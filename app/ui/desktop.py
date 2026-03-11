import os
import random
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QFileIconProvider, QGraphicsDropShadowEffect, QFrame
from PyQt6.QtGui import QPainter, QPixmap, QColor, QIcon, QPen, QBrush
from PyQt6.QtCore import Qt, QTimer, QVariantAnimation, QFileInfo, QRect
from core.config import config as themeConfig
import win32com.client
import json

class DesktopWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.backgroundBitmap = None 
        self.nextBackgroundBitmap = None
        self.fadeAlpha = 0.0
        
        self.wallpaperMode = None
        self.wallpaperList = []
        self.currentWallpaperIndex = 0

        # Carousel timer
        self.carouselTimer = QTimer(self)
        self.carouselTimer.timeout.connect(self.StartTransition)

        # Fade animation
        self.fadeAnimation = QVariantAnimation(self)
        self.fadeAnimation.valueChanged.connect(self.UpdateFade)
        self.fadeAnimation.finished.connect(self.EndTransition)

        # ahhhhh I'm too lazy to comment all the code :(
        # i think I'll do it next time
        self.Init()

    def Init(self):
        self.setWindowTitle("Ninawe Desktop")
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnBottomHint
        )
        
        # screen resolution
        screen = self.screen().geometry()
        self.setGeometry(screen)

        self.wallpaperMode = themeConfig.theme.Get("Desktop", "wallpaper_mode", fallback="cover")
        backgroundPath = themeConfig.theme.GetResource(themeConfig.theme.Get("Desktop", "wallpaper_path"))
        
        isCarousel = themeConfig.theme.GetBool("Desktop", "wallpaper_carousel", fallback=True)
        intervalMin = themeConfig.theme.GetFloat("Desktop", "carousel_interval_min", fallback=15)
        self.shuffle = themeConfig.theme.GetBool("Desktop", "carousel_shuffle", fallback=False)
        transitionMs = themeConfig.theme.GetInt("Desktop", "wallpaper_transition_ms", fallback=500)

        self.fadeAnimation.setDuration(transitionMs)
        self.fadeAnimation.setStartValue(0.0)
        self.fadeAnimation.setEndValue(1.0)

        print(f"[Log] [Desktop] | Loading wallpaper: {backgroundPath} (Mode: {self.wallpaperMode})")

        self.LoadWallpaper(backgroundPath, isCarousel, intervalMin)

        self.desktop_items = []
        self.selected_items = []

        self.is_selecting = False
        self.selection_start = None
        self.previously_selected = [] 

        self.selection_box = QWidget(self)
        self.selection_box.setStyleSheet("""
            background-color: rgba(0, 120, 215, 60);
            border: 1px solid rgba(0, 120, 215, 255);
        """)
        self.selection_box.hide()

        self.ScanDesktop()

    def ScanDesktop(self):
        desktop_path = os.path.expanduser("~/Desktop")
        json_path = themeConfig.theme.GetPath("userdata\\preferences\\user\\desktopdata.json")

        desktop_data = {"desktop": []}
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    desktop_data = json.load(f)
            except Exception as e:
                print(f"[Log] [Desktop] | Failed to read JSON: {e}")

        saved_items = {item["path"]: item for item in desktop_data.get("desktop", []) if "path" in item}

        if not os.path.exists(desktop_path):
            print("[Log] [Desktop] | Desktop folder not found!")
            return

        itemHeight = 110
        windowMarginY = 50
        spacingY = 10
        max_rows = max(1, (self.height() - windowMarginY * 2) // (itemHeight + spacingY))

        occupied_positions = set()
        for item in saved_items.values():
            pos = item.get("position", [0, 0])
            occupied_positions.add((pos[0], pos[1]))

        valid_filepaths = []
        for filename in os.listdir(desktop_path):
            if filename.startswith('.') or filename.lower() == 'desktop.ini':
                continue
            valid_filepaths.append(os.path.join(desktop_path, filename))

        updated_desktop_data = []
        
        for filepath in valid_filepaths:
            if filepath in saved_items:
                updated_desktop_data.append(saved_items[filepath])
            else:
                new_pos = self.GetFirstFreePosition(occupied_positions, max_rows)
                
                occupied_positions.add(tuple(new_pos)) 
                
                new_item = {
                    "type": "file",
                    "name": os.path.basename(filepath),
                    "path": filepath,
                    "icon": "default",
                    "position": new_pos 
                }
                updated_desktop_data.append(new_item)

        desktop_data["desktop"] = updated_desktop_data
        
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(desktop_data, f, indent=4, ensure_ascii=False)

        self.RenderGrid(updated_desktop_data)

    def RenderGrid(self, items_data):
        itemWidth = 86
        itemHeight = 110
        windowMarginX = 50
        windowMarginY = 50
        spacingX = 10
        spacingY = 10

        for item in self.desktop_items:
            item.deleteLater()
        self.desktop_items.clear()
        self.selected_items.clear()

        for data in items_data:
            if data.get("type") == "widget":
                continue
                
            filepath = data.get("path")
            grid_x, grid_y = data.get("position", [0, 0])
            
            item = DesktopItem(filepath, parent=self)

            positionX = windowMarginX + grid_x * (itemWidth + spacingX)
            positionY = windowMarginY + grid_y * (itemHeight + spacingY)

            item.grid_x = grid_x
            item.grid_y = grid_y
            
            item.move(positionX, positionY)
            item.show()
            
            self.desktop_items.append(item)

    def LoadWallpaper(self, path, isCarousel, intervalMin):
        if os.path.isdir(path):
            valid_exts = ('.png', '.jpg', '.jpeg', '.bmp')
            self.wallpaperList = [os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith(valid_exts)]
            
            if self.shuffle:
                random.shuffle(self.wallpaperList)
            else:
                self.wallpaperList.sort()
            
        elif os.path.isfile(path):
            self.wallpaperList = [path]

        if not self.wallpaperList:
            print(f"[Log] [Desktop] [DesktopWindow] [LoadWallpaper] | No valid images found at {path}")
            self.backgroundBitmap = QPixmap(1, 1)
            self.backgroundBitmap.fill(QColor("#2E2E2E"))
            self.update()
            return

        self.currentWallpaperIndex = 0
        self.backgroundBitmap = self.GetScaledPixmap(self.wallpaperList[self.currentWallpaperIndex])

        if isCarousel and len(self.wallpaperList) > 1:
            self.carouselTimer.start(round(intervalMin * 60 * 1000)) # to minutes

        self.update()

    def GetScaledPixmap(self, path):
        pixmap = QPixmap(path)
        if pixmap.isNull():
            return pixmap

        if self.wallpaperMode == "cover":
            return pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        elif self.wallpaperMode == "contain":
            return pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        else:
            return pixmap.scaled(self.size(), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)

    def StartTransition(self):
        self.currentWallpaperIndex = (self.currentWallpaperIndex + 1) % len(self.wallpaperList)
        self.nextBackgroundBitmap = self.GetScaledPixmap(self.wallpaperList[self.currentWallpaperIndex])
        self.fadeAnimation.start()

    def UpdateFade(self, value):
        self.fadeAlpha = value
        self.update()

    def EndTransition(self):
        self.backgroundBitmap = self.nextBackgroundBitmap
        self.nextBackgroundBitmap = None
        self.fadeAlpha = 0.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        painter.fillRect(self.rect(), QColor("black"))

        if self.backgroundBitmap and not self.backgroundBitmap.isNull():
            self.DrawCenteredPixmap(painter, self.backgroundBitmap, 1.0)

        if self.nextBackgroundBitmap and not self.nextBackgroundBitmap.isNull() and self.fadeAlpha > 0:
            self.DrawCenteredPixmap(painter, self.nextBackgroundBitmap, self.fadeAlpha)

    def DrawCenteredPixmap(self, painter, pixmap, opacity):
        painter.setOpacity(opacity)
        
        x = (self.width() - pixmap.width()) // 2
        y = (self.height() - pixmap.height()) // 2
        
        painter.drawPixmap(x, y, pixmap)
        painter.setOpacity(1.0)

    def ItemClicked(self, item, ctrl_pressed):
        if ctrl_pressed:
            if item in self.selected_items:
                item.SetSelected(False)
                self.selected_items.remove(item)
            else:
                item.SetSelected(True)
                self.selected_items.append(item)
        else:
            if item not in self.selected_items or len(self.selected_items) > 1:
                self.ClearSelection()
                item.SetSelected(True)
                self.selected_items.append(item)

    def ClearSelection(self):
        for item in self.selected_items:
            item.SetSelected(False)
        self.selected_items.clear()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            ctrl_pressed = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)

            if not ctrl_pressed:
                self.ClearSelection()
                self.previously_selected = []
            else:
                self.previously_selected = self.selected_items.copy()

            self.is_selecting = True
            self.selection_start = event.pos()
            
            self.selection_box.setGeometry(QRect(self.selection_start, self.selection_start))
            self.selection_box.show()

    def mouseMoveEvent(self, event):
        if self.is_selecting:
            draw_rect = QRect(self.selection_start, event.pos()).normalized()
            self.selection_box.setGeometry(draw_rect)
            self.ProcessSelection(draw_rect)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_selecting:
            self.is_selecting = False
            self.selection_box.hide()

    def ProcessSelection(self, selection_rect):
        for item in self.desktop_items:
            if selection_rect.intersects(item.geometry()):
                if item not in self.selected_items:
                    item.SetSelected(True)
                    self.selected_items.append(item)
            else:
                if item in self.selected_items and item not in self.previously_selected:
                    item.SetSelected(False)
                    self.selected_items.remove(item)

    def GetFirstFreePosition(self, occupied_positions, max_rows):
        col = 0
        while True:
            for row in range(max_rows):
                if (col, row) not in occupied_positions:
                    return [col, row]
            col += 1

    def SnapItemToGrid(self, item):
        itemWidth = 86   
        itemHeight = 110
        windowMarginX = 50
        windowMarginY = 50
        spacingX = 10
        spacingY = 10

        target_grid_x = round((item.x() - windowMarginX) / (itemWidth + spacingX))
        target_grid_y = round((item.y() - windowMarginY) / (itemHeight + spacingY))

        target_grid_x = max(0, target_grid_x)
        target_grid_y = max(0, target_grid_y)

        is_occupied = False
        for other_item in self.desktop_items:
            if other_item != item and getattr(other_item, 'grid_x', -1) == target_grid_x and getattr(other_item, 'grid_y', -1) == target_grid_y:
                is_occupied = True
                break

        if is_occupied:
            target_grid_x = item.grid_x
            target_grid_y = item.grid_y
        else:
            item.grid_x = target_grid_x
            item.grid_y = target_grid_y
            self.UpdateItemPositionInJSON(item.filepath, target_grid_x, target_grid_y)

        final_x = windowMarginX + target_grid_x * (itemWidth + spacingX)
        final_y = windowMarginY + target_grid_y * (itemHeight + spacingY)
        
        item.move(final_x, final_y)

    def UpdateItemPositionInJSON(self, filepath, grid_x, grid_y):
        import json
        json_path = themeConfig.theme.GetPath("userdata\\preferences\\user\\desktopdata.json")
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                desktop_data = json.load(f)

            for data in desktop_data.get("desktop", []):
                if data.get("path") == filepath:
                    data["position"] = [grid_x, grid_y]
                    break
                    
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(desktop_data, f, indent=4, ensure_ascii=False)
                
        except Exception as e:
            print(f"[Log] [Desktop] | Failed to save new position for {filepath}: {e}")

class DesktopItem(QWidget):
    def __init__(self, filepath, parent = None):
        super().__init__(parent)
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        
        if self.filename.lower().endswith('.lnk'):
            self.filename = self.filename[:-4]
            
        self.Init()

    def Init(self):
        self.setFixedSize(85, 110)
        
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self.innerFrame = QFrame()
        self.innerFrame.setObjectName("IconFrame")
        
        frameLayout = QVBoxLayout(self.innerFrame)
        frameLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        actualIconPath = self.filepath
        
        if self.filepath.lower().endswith('.lnk'):
            try:
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(self.filepath)
                target = shortcut.Targetpath
                
                if target and os.path.exists(target):
                    actualIconPath = target
            except Exception as exc:
                print(f"[Log] [Desktop] [DesktopItem] [Init] | Failed to resolve shortcut {self.filepath}: {exc}")

        provider = QFileIconProvider()
        fileInfo = QFileInfo(actualIconPath)
        icon = provider.icon(fileInfo)
        
        self.iconLabel = QLabel()
        self.iconLabel.setPixmap(icon.pixmap(48, 48)) 
        self.iconLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.textLabel = QLabel(self.filename)
        self.textLabel.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.textLabel.setWordWrap(True)
        self.textLabel.setMaximumWidth(85) 
        self.textLabel.setStyleSheet("""
            color: white; 
            font-size: 11px;
            font-family: 'Segoe UI', Arial;
            background: transparent;
        """)

        shadow = QGraphicsDropShadowEffect(self.textLabel)
        shadow.setBlurRadius(5)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 255))
        self.textLabel.setGraphicsEffect(shadow)

        frameLayout.addWidget(self.iconLabel)
        frameLayout.addWidget(self.textLabel)
        mainLayout.addWidget(self.innerFrame)

        self.setStyleSheet("""
            QFrame#IconFrame {
                background: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
            }
            QFrame#IconFrame:hover {
                background: rgba(255, 255, 255, 30);
                border: 1px solid rgba(255, 255, 255, 60);
            }
            QFrame#IconFrame[selected = "true"] {
                background: rgba(255, 255, 255, 60);
                border: 1px solid rgba(255, 255, 255, 100);
            }
            QFrame#IconFrame[selected = "true"]:hover {
                background: rgba(255, 255, 255, 80);
                border: 1px solid rgba(255, 255, 255, 120);
            }
        """)

    def SetSelected(self, is_selected):
        self.innerFrame.setProperty("selected", is_selected)
        self.innerFrame.style().unpolish(self.innerFrame)
        self.innerFrame.style().polish(self.innerFrame)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = event.pos() 
            self.is_dragging = False

            self.raise_()

            ctrl_pressed = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
            if self.parent():
                self.parent().ItemClicked(self, ctrl_pressed)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            if hasattr(self, 'drag_start_pos') and self.drag_start_pos:
                if (event.pos() - self.drag_start_pos).manhattanLength() > 5:
                    self.is_dragging = True
                    
                if self.is_dragging:
                    new_pos = self.mapToParent(event.pos()) - self.drag_start_pos
                    self.move(new_pos)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = None
            if getattr(self, 'is_dragging', False):
                self.is_dragging = False
                if self.parent():
                    self.parent().SnapItemToGrid(self)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            try:
                if self.parent():
                    self.parent().ClearSelection()
                os.startfile(self.filepath)
            except Exception as e:
                print(f"[Log] [DesktopItem] | Failed to start {self.filepath}: {e}")