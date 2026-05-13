from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, QSize, QPoint
from .config import WConfig

class TaskbarButton(QPushButton):
    def __init__(self, groupKey, parent = None):
        super().__init__(parent)
        self.groupKey = groupKey
        self.dragStartPosition = QPoint()
        self.isDragging = False

        self.setProperty("isHovered", "false")
        self.setProperty("isPressed", "false")
        self.setProperty("isOpen", "false")
        self.setProperty("isActive", "false")
        self.setProperty("isMinimized", "false")
        self.setProperty("isGroup", "false")

        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFixedSize(WConfig.iconSize + WConfig.paddings, WConfig.iconSize + WConfig.paddings)
        self.setIconSize(QSize(WConfig.iconSize, WConfig.iconSize))

    def UpdateState(self, isOpen: bool, isActive: bool, isMinimized: bool, isGroup: bool):
        openState = "true" if isOpen else "false"
        activeState = "true" if isActive else "false"
        minState = "true" if isMinimized else "false"
        groupState = "true" if isGroup else "false"

        changed = False
        if self.property("isOpen") != openState:
            self.setProperty("isOpen", openState)
            changed = True
        if self.property("isActive") != activeState:
            self.setProperty("isActive", activeState)
            changed = True
        if self.property("isMinimized") != minState:
            self.setProperty("isMinimized", minState)
            changed = True
        if self.property("isGroup") != groupState:
            self.setProperty("isGroup", groupState)
            changed = True

        if changed:
            self.style().unpolish(self)
            self.style().polish(self)

    def enterEvent(self, event):
        self.setProperty("isHovered", "true")
        self.style().unpolish(self)
        self.style().polish(self)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setProperty("isHovered", "false")
        self.style().unpolish(self)
        self.style().polish(self)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setProperty("isPressed", "true")
            self.style().unpolish(self)
            self.style().polish(self)

            self.dragStartPosition = event.pos()
            self.isDragging = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return

        if (event.pos() - self.dragStartPosition).manhattanLength() > 5:
            self.isDragging = True
            taskbar = self.parentWidget()
            if hasattr(taskbar, 'HandleButtonDrag'):
                taskbar.HandleButtonDrag(self, event.globalPosition().toPoint())

    def mouseReleaseEvent(self, event):
        if self.property("isPressed") == "true":
            self.setProperty("isPressed", "false")
            self.style().unpolish(self)
            self.style().polish(self)

        if event.button() == Qt.MouseButton.RightButton:
            taskbar = self.parentWidget()
            if hasattr(taskbar, 'ShowContextMenu'):
                taskbar.ShowContextMenu(self, event.globalPosition().toPoint())
            return

        if getattr(self, 'isDragging', False):
            self.isDragging = False
            taskbar = self.parentWidget()
            if hasattr(taskbar, 'HandleDragFinished'):
                taskbar.HandleDragFinished(self)
            return

        super().mouseReleaseEvent(event)
