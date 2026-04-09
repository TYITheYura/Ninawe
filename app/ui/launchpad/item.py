import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QApplication)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
import win32com.client
from core.workers import ThumbnailLoaderThread
from ui.components import ContextMenu
from PyQt6.QtGui import QDrag
from PyQt6.QtCore import QMimeData

class LaunchpadItem(QWidget):
    def __init__(self, parent, name, path, iconPath = None):
        super().__init__()
        self.name = name
        self.path = path
        self.parent = parent
        self.setFixedSize(100, 140)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("""
            LaunchpadItem {
                background-color: transparent;
                border-radius: 15px;
            }
            LaunchpadItem:hover {
                background-color: rgba(255, 255, 255, 30);
                border: 1px solid rgba(255, 255, 255, 50);
            }
            LaunchpadItem:focus {
                background-color: rgba(255, 255, 255, 30);
                border: 1px solid rgba(255, 255, 255, 50);
            }
        """)

        self.WSHELL = win32com.client.Dispatch("WScript.Shell")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)

        self.iconLabel = QLabel()
        self.iconLabel.setFixedSize(64, 64)

        self.iconLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.iconLabel.setStyleSheet("""background-color: rgba(255, 255, 255, 0.1); border-radius: 15px;""")

        self.textLabel = QLabel(self.name)
        self.textLabel.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.textLabel.setWordWrap(True)
        self.textLabel.setStyleSheet("color: white; font-size: 12px; background: transparent;")

        layout.addStretch()
        layout.addWidget(self.iconLabel, alignment = Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        layout.addWidget(self.textLabel, alignment = Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()

        self.thumbnailThread = ThumbnailLoaderThread(self.path, 48, self)
        self.thumbnailThread.loadedSignal.connect(self.ApplyThumbnail)
        self.thumbnailThread.finished.connect(self.thumbnailThread.deleteLater)
        self.thumbnailThread.start()

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.ShowContextMenu)

    def ApplyThumbnail(self, pixmap):
        scaledPixmap = pixmap.scaled(
            48, 48,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.iconLabel.setPixmap(scaledPixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragStartPosition = event.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
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
        is_pinned = self.path in self.parent.manager.state["launchpad"]
        section = "launchpad.pinned" if is_pinned else "launchpad.unpinned"

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
