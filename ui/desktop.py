from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtGui import QPainter, QPixmap, QColor
from PyQt6.QtCore import Qt, QRect

from core.config import config as cfg

class DesktopWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.backgroundBitmap = None 
        self.backgroundMode = "cover"
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Ninawe Desktop")
        # no borders
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        # screen resolution
        screen = self.screen().geometry()
        self.setGeometry(screen)

        self.backgroundMode = cfg.theme.Get("Desktop", "wallpaper_mode", fallback="cover")
        backgroundRawPath = cfg.theme.Get("Desktop", "wallpaper_path")
        backgroundPath = cfg.theme.GetResource(backgroundRawPath)

        print(f"Loading wallpaper: {backgroundPath} (Mode: {self.backgroundMode})")
        self.load_wallpaper(backgroundPath)

    def load_wallpaper(self, path):
        self.backgroundBitmap = QPixmap(path)
        if self.backgroundBitmap.isNull():
            print(f"Error: Could not load image at {path}")
            self.backgroundBitmap = QPixmap(1, 1)
            self.backgroundBitmap.fill(QColor("#2E2E2E"))
        
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        
        if not self.backgroundBitmap:
            painter.fillRect(self.rect(), QColor("black"))
            return

        windoWidth = self.width()
        windowHeight = self.height()
        # imageWidth = self.backgroundBitmap.width()
        # imageHeight = self.backgroundBitmap.height()

        if self.backgroundMode == "cover":
            scaled = self.backgroundBitmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            
            x = (windoWidth - scaled.width()) // 2
            y = (windowHeight - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)

        elif self.backgroundMode == "contain":
            painter.fillRect(self.rect(), QColor("black"))
            scaled = self.backgroundBitmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            x = (windoWidth - scaled.width()) // 2
            y = (windowHeight - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
            
        else:
            painter.drawPixmap(self.rect(), self.backgroundBitmap)