import os
import random
from PyQt6.QtCore import Qt, QTimer, QVariantAnimation
from PyQt6.QtGui import QPixmap, QColor
from core.utils import MakeLog

class WallpaperManager:
    def __init__(self, desktop, desktopConfig):
        self.desktop = desktop
        self.DConfig = desktopConfig

        self.backgroundBitmap = None
        self.nextBackgroundBitmap = None
        self.fadeAlpha = 0.0
        self.currentWallpaperIndex = 0

        # Carousel timer
        self.carouselTimer = QTimer(self.desktop)
        self.carouselTimer.timeout.connect(self.StartTransition)

        # Fade animation
        self.fadeAnimation = QVariantAnimation(self.desktop)
        self.fadeAnimation.valueChanged.connect(self.UpdateFade)
        self.fadeAnimation.finished.connect(self.EndTransition)

        self.fadeAnimation.setDuration(self.DConfig.transitionMs)
        self.fadeAnimation.setStartValue(0.0)
        self.fadeAnimation.setEndValue(1.0)

    def LoadWallpaper(self):
        MakeLog("[Log] [WallpaperManager]", f"Loading wallpaper: {self.DConfig.backgroundPath} (Mode: {self.DConfig.wallpaperMode})")

        if os.path.isdir(self.DConfig.backgroundPath):
            self.DConfig.wallpaperList = [
                os.path.join(self.DConfig.backgroundPath, file)
                for file in os.listdir(self.DConfig.backgroundPath)
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))
            ]

            if self.DConfig.shuffle:
                random.shuffle(self.DConfig.wallpaperList)
            else:
                self.DConfig.wallpaperList.sort()

        elif os.path.isfile(self.DConfig.backgroundPath):
            self.DConfig.wallpaperList = [self.DConfig.backgroundPath]

        if not self.DConfig.wallpaperList:
            MakeLog("[Log] [WallpaperManager]", f"No valid images found at {self.DConfig.backgroundPath}")
            self.backgroundBitmap = QPixmap(1, 1)
            self.backgroundBitmap.fill(QColor("#2E2E2E"))
            self.desktop.update()
            return

        self.currentWallpaperIndex = 0
        self.backgroundBitmap = self.GetScaledPixmap(self.DConfig.wallpaperList[self.currentWallpaperIndex])

        if self.DConfig.isCarousel and len(self.DConfig.wallpaperList) > 1:
            self.carouselTimer.start(round(self.DConfig.intervalInMin * 60 * 1000))
            self.fadeAnimation.setDuration(self.DConfig.transitionMs)
        else:
            self.carouselTimer.stop()

        self.desktop.update()

    def GetScaledPixmap(self, path):
        pixmap = QPixmap(path)
        if pixmap.isNull():
            return pixmap

        if self.DConfig.wallpaperMode == "cover":
            return pixmap.scaled(self.desktop.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        elif self.DConfig.wallpaperMode == "contain":
            return pixmap.scaled(self.desktop.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        else:
            return pixmap.scaled(self.desktop.size(), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)

    def DrawCenteredPixmap(self, painter, pixmap, opacity):
        painter.setOpacity(opacity)
        x = (self.desktop.width() - pixmap.width()) // 2
        y = (self.desktop.height() - pixmap.height()) // 2
        painter.drawPixmap(x, y, pixmap)
        painter.setOpacity(1.0)

    def StartTransition(self):
        self.currentWallpaperIndex = (self.currentWallpaperIndex + 1) % len(self.DConfig.wallpaperList)
        self.nextBackgroundBitmap = self.GetScaledPixmap(self.DConfig.wallpaperList[self.currentWallpaperIndex])
        self.fadeAnimation.start()

    def UpdateFade(self, value):
        self.fadeAlpha = value
        self.desktop.update()

    def EndTransition(self):
        self.backgroundBitmap = self.nextBackgroundBitmap
        self.nextBackgroundBitmap = None
        self.fadeAlpha = 0.0
        self.desktop.update()

    def Draw(self, painter):
        if self.backgroundBitmap and not self.backgroundBitmap.isNull():
            self.DrawCenteredPixmap(painter, self.backgroundBitmap, 1.0)

        if self.nextBackgroundBitmap and not self.nextBackgroundBitmap.isNull() and self.fadeAlpha > 0:
            self.DrawCenteredPixmap(painter, self.nextBackgroundBitmap, self.fadeAlpha)
