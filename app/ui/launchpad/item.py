import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QApplication)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
import win32com.client
from core.workers import ThumbnailLoaderThread
from ui.components import ContextMenu
from PyQt6.QtGui import QDrag
from PyQt6.QtCore import QMimeData
from .config import IConfig
from PyQt6.QtGui import QPixmap

class LaunchpadItem(QWidget):
    def __init__(self, parent, name, path, iconPath = None):
        super().__init__()
        self.name = name
        self.path = path
        self.parent = parent

        self.Init()

    def Init(self):
        IConfig.configUpdated.connect(self.UpdateStyles)
        self.setFixedSize(IConfig.containerWidth, IConfig.containerHeight)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(IConfig.containerStyle)

        self.WSHELL = win32com.client.Dispatch("WScript.Shell")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)

        self.iconLabel = QLabel()
        self.iconLabel.setObjectName("IconLabel")
        self.iconLabel.setFixedSize(IConfig.iconSize + IConfig.iconPadding, IConfig.iconSize + IConfig.iconPadding)

        self.iconLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.iconLabel.setStyleSheet(IConfig.iconStyle)

        self.textLabel = QLabel(self.name)
        self.textLabel.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.textLabel.setWordWrap(True)
        self.textLabel.setStyleSheet("color: white; font-size: 12px; background: transparent;")

        layout.addStretch()
        layout.addWidget(self.iconLabel, alignment = Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        layout.addWidget(self.textLabel, alignment = Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()

        self.thumbnailThread = ThumbnailLoaderThread(self.path, IConfig.iconSize, self)
        self.thumbnailThread.loadedSignal.connect(self.ApplyThumbnail)
        self.thumbnailThread.finished.connect(self.thumbnailThread.deleteLater)
        self.thumbnailThread.start()

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.ShowContextMenu)

    def UpdateStyles(self, source = None, changedSections = None):
        self.setFixedSize(IConfig.containerWidth, IConfig.containerHeight)
        self.setStyleSheet(IConfig.containerStyle)

        self.iconLabel.setFixedSize(
            IConfig.iconSize + IConfig.iconPadding,
            IConfig.iconSize + IConfig.iconPadding
        )

        self.iconLabel.setStyleSheet(IConfig.iconStyle)

        self.thumbnailThread = ThumbnailLoaderThread(self.path, IConfig.iconSize, self)
        self.thumbnailThread.loadedSignal.connect(self.ApplyThumbnail)
        self.thumbnailThread.finished.connect(self.thumbnailThread.deleteLater)
        self.thumbnailThread.start()

    def deleteLater(self):
        if self.thumbnailThread:
            try:
                self.thumbnailThread.loadedSignal.disconnect()
                self.thumbnailThread.requestInterruption()
                self.thumbnailThread.quit()
                self.thumbnailThread.wait()
            except Exception:
                pass

        super().deleteLater()

    def ApplyThumbnail(self, image):
        pixmap = QPixmap.fromImage(image)
        scaledPixmap = pixmap.scaled(
            IConfig.iconSize, IConfig.iconSize,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.iconLabel.setPixmap(scaledPixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragStartPosition = event.pos()
            self.setProperty("isPressed", True)
            self.style().unpolish(self)
            self.style().polish(self)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setProperty("isPressed", False)
        self.style().unpolish(self)
        self.style().polish(self)

        if event.button() == Qt.MouseButton.LeftButton:
            if (event.pos() - self.dragStartPosition).manhattanLength() < QApplication.startDragDistance():
                self.parent.close()
                try:
                    os.startfile(self.path)
                except OSError:
                    pass
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return

        if (event.pos() - self.dragStartPosition).manhattanLength() < QApplication.startDragDistance():
            return

        if self.path not in self.parent.manager.state["launchpad"]:
            return

        self.setProperty("isPressed", False)
        self.style().unpolish(self)
        self.style().polish(self)

        drag = QDrag(self)
        mimeData = QMimeData()
        mimeData.setText(self.path)
        drag.setMimeData(mimeData)

        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())

        self.iconLabel.setHidden(True)
        self.textLabel.setHidden(True)

        drag.exec(Qt.DropAction.MoveAction)

        self.iconLabel.setVisible(True)
        self.textLabel.setVisible(True)

    def ShowContextMenu(self, pos):
        isPinned = self.path in self.parent.manager.state["launchpad"]
        section = "launchpad.pinned" if isPinned else "launchpad.unpinned"

        menu = ContextMenu(section, self)
        menu.commandClicked.connect(self.ExecuteCommand)

        menu.exec(self.mapToGlobal(pos))

    def ExecuteCommand(self, command):
        if command == "pin":
            self.parent.PinItem(self.path)
        elif command == "unpin":
            self.parent.UnpinItem(self.path)

        self.parent.RefreshGrids()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            self.parent.close()
            try:
                os.startfile(self.path)
            except OSError:
                pass

        elif event.key() == Qt.Key.Key_Right:
            self.parent.MoveFocus(self, "right")
        elif event.key() == Qt.Key.Key_Left:
            self.parent.MoveFocus(self, "left")
        elif event.key() == Qt.Key.Key_Down:
            self.parent.MoveFocus(self, "down")
        elif event.key() == Qt.Key.Key_Up:
            self.parent.MoveFocus(self, "up")
        else:
            super().keyPressEvent(event)
