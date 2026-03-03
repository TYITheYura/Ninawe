import os
import random
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QFileIconProvider, QGraphicsDropShadowEffect, QFrame
from PyQt6.QtGui import QPainter, QPixmap, QColor, QIcon
from PyQt6.QtCore import Qt, QTimer, QVariantAnimation, QFileInfo
from core.config import config as themeConfig
import win32com.client

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
        
        self.ScanDesktop()

    def ScanDesktop(self):
        desktop_path = os.path.expanduser("~/Desktop")
        if not os.path.exists(desktop_path):
            print("[Log] [Desktop] [DesktopWindow] [Scan] | ummmm where is desktop folder???")
            return

        valid_filepaths = []
        for filename in os.listdir(desktop_path):
            if filename.startswith('.') or filename.lower() == 'desktop.ini':
                continue
            
            filepath = os.path.join(desktop_path, filename)
            valid_filepaths.append(filepath)

        self.RenderGrid(valid_filepaths)

    def RenderGrid(self, filepaths):
        itemWidth = 85
        itemHeight = 110
        windowMarginX = 50
        windowMarginY = 50
        spacingX = 10
        spacingY = 10

        currentRow = 0
        currentColumn = 0
        
        maxRowsCount = (self.height() - windowMarginY * 2) // (itemHeight + spacingY)

        for filepath in filepaths:
            item = DesktopItem(filepath, parent = self)
            
            positionX = windowMarginX + currentColumn * (itemWidth + spacingX)
            positionY = windowMarginY + currentRow * (itemHeight + spacingY)
            
            item.move(positionX, positionY)
            item.show()
            
            self.desktop_items.append(item)

            currentRow += 1
            
            if currentRow >= maxRowsCount:
                currentRow = 0
                currentColumn += 1

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
            }
            QFrame#IconFrame:hover {
                background: rgba(0, 191, 255, 50);
                border: 1px solid rgba(0, 191, 255, 100);
            }
            QFrame#IconFrame[pressed = "true"] {
                background: rgba(0, 191, 255, 100);
                border: 1px solid rgba(0, 191, 255, 150);
            }
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.innerFrame.setProperty("pressed", True)
            self.innerFrame.style().unpolish(self.innerFrame)
            self.innerFrame.style().polish(self.innerFrame)
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.innerFrame.setProperty("pressed", False)
            self.innerFrame.style().unpolish(self.innerFrame)
            self.innerFrame.style().polish(self.innerFrame)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            try:
                os.startfile(self.filepath)
            except Exception as exc:
                print(f"[Log] [Desktop] [DesktopItem] [DoubleClick] | Failed to start {self.filepath}: {exc}")