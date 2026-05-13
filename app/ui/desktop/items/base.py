import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QApplication,
    QGraphicsDropShadowEffect, QFrame, QGraphicsOpacityEffect
)
from PyQt6.QtGui import (
    QColor, QDrag, QFontMetrics, QFont
)
from PyQt6.QtCore import Qt, QMimeData
from core.utils import MakeLog, SHELLEXECUTEINFO, SEE_MASK_INVOKEIDLIST
import re
import ctypes
from ui.components import ContextMenu, RenameEditor
from ui.desktop.config import IConfig
import uuid

class BaseDesktopItem(QWidget):
    def __init__(self, filepath, desktop, widgetData = None):
        super().__init__(desktop)
        self.desktop = desktop
        self.filepath = filepath
        self.widgetData = widgetData
        self.filename = os.path.basename(filepath) if filepath else ""

        self.textLabel = None
        self.nameEditor = None
        self.dragStartPos = None
        self.widgetInstance = None

        self.itemID = str(uuid.uuid4())

        self.spanX = 1
        self.spanY = 1
        self.gridX = -1
        self.gridY = -1

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.SetupBaseUI()

    def SetupBaseUI(self):
        self.setFixedWidth(IConfig.itemWidth)
        self.setMinimumHeight(IConfig.itemHeight)

        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self.innerFrame = QFrame()
        self.innerFrame.setObjectName("IconFrame")
        self.innerFrame.setFixedWidth(IConfig.itemWidth - 4)
        # self.innerFrame.setMinimumHeight(round(IConfig.itemHeight / 1.5)) # same here

        frameLayout = QVBoxLayout(self.innerFrame)
        frameLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frameLayout.setContentsMargins(0, 2, 0, 2) # maybe i'll change ts in future, but not now

        self.iconLabel = QLabel()
        self.iconLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # frameLayout.addStretch() # future, maybe
        frameLayout.addWidget(self.iconLabel)

        if IConfig.iconLabelStatus:
            self.textLabel = QLabel()
            self.textLabel.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
            self.textLabel.setMaximumWidth(IConfig.itemWidth)
            self.textLabel.setStyleSheet(IConfig.labelStyleSheet)

            shadow = QGraphicsDropShadowEffect(self.textLabel)
            shadow.setBlurRadius(5)
            shadow.setXOffset(0)
            shadow.setYOffset(0)
            shadow.setColor(QColor(0, 0, 0, 255))
            self.textLabel.setGraphicsEffect(shadow)

            frameLayout.addWidget(self.textLabel)

        # frameLayout.addStretch() # same here
        mainLayout.addWidget(self.innerFrame)
        self.setStyleSheet(IConfig.iconStyleSheet)

    def SetSelected(self, isSelected):
        self.innerFrame.setProperty("selected", isSelected)
        self.innerFrame.style().unpolish(self.innerFrame)
        self.innerFrame.style().polish(self.innerFrame)

    def SetHoverDrop(self, isHovered):
        self.innerFrame.setProperty("drop_hover", isHovered)
        self.innerFrame.style().unpolish(self.innerFrame)
        self.innerFrame.style().polish(self.innerFrame)

    def SetDisplayName(self, text):
        if not self.textLabel:
            return

        font = QFont(IConfig.iconLabelFontFamily, IConfig.iconLabelFontSize)
        fm = QFontMetrics(font)
        avgCharWidth = fm.averageCharWidth() or 1
        maxChars = (IConfig.itemWidth // avgCharWidth) + IConfig.iconLabelCompensator

        parts = re.split(r'( +)', text)
        name = []
        currentLine = ""

        for part in parts:
            if part.strip() != "" and len(part) > maxChars - 3:
                part = part[:maxChars - 3] + "..."
            if len(currentLine) + len(part) <= maxChars:
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

        self.textLabel.setText("\n".join(name).strip())

    def SetCutState(self, isCut):
        if isCut:
            effect = QGraphicsOpacityEffect(self)
            effect.setOpacity(0.5)
            self.setGraphicsEffect(effect)
        else:
            self.setGraphicsEffect(None)

    def ShowWindowsProperties(self):
        sei = SHELLEXECUTEINFO()
        sei.cbSize = ctypes.sizeof(sei)
        sei.fMask = SEE_MASK_INVOKEIDLIST
        sei.lpVerb = "properties"
        sei.lpFile = os.path.normpath(self.filepath)
        sei.nShow = 1

        ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(sei))

    def StartRename(self):
        if self.textLabel:
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
        if getattr(self, 'nameEditor', None) is None:
            return

        newName = self.nameEditor.text().strip()

        self.nameEditor.hide()
        self.nameEditor.setParent(None)
        self.nameEditor.deleteLater()
        self.nameEditor = None

        if not newName or newName == self.filename:
            if self.textLabel:
                self.textLabel.show()
            return

        originalExtension = os.path.splitext(self.filepath)[1]
        if originalExtension.lower() == '.lnk' and not newName.lower().endswith('.lnk'):
            newName += originalExtension

        newPath = os.path.join(os.path.dirname(self.filepath), newName)

        if os.path.exists(newPath):
            MakeLog("[Log] [DesktopItem]", f"File with this name already exists! {newPath}")
            if self.textLabel:
                self.textLabel.show()
            return

        self.desktop.pendingDropPositions[newPath] = [self.gridX, self.gridY]

        try:
            os.rename(self.filepath, newPath)
            MakeLog("[Log] [DesktopItem]", f"Renamed: {self.filepath} -> {newPath}")
        except Exception as e:
            MakeLog("[Log] [DesktopItem]", f"Rename error: {e}")

        if self.textLabel:
            self.textLabel.show()

    def mousePressEvent(self, event):
        self.setFocus()
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragStartPos = event.pos()
            self.raise_()

            ctrlButtonPressedStatus = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)

            self.desktop.ItemClicked(self, ctrlButtonPressedStatus)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and self.dragStartPos:
            if (event.pos() - self.dragStartPos).manhattanLength() > QApplication.startDragDistance():
                drag = QDrag(self)
                mimeData = QMimeData()

                mimeData.setData("application/x-ninawe-item-move", self.itemID.encode('utf-8'))

                hotspotX = self.dragStartPos.x()
                hotspotY = self.dragStartPos.y()
                mimeData.setData("application/x-ninawe-offset", f"{hotspotX}:{hotspotY}".encode('utf-8'))

                self.AddExternalMimeData(mimeData)

                drag.setMimeData(mimeData)

                pixmap = self.innerFrame.grab()
                drag.setPixmap(pixmap)

                hotspot = event.pos() - self.innerFrame.pos()
                drag.setHotSpot(hotspot)

                action = drag.exec(Qt.DropAction.MoveAction | Qt.DropAction.CopyAction)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.ExecuteDoubleClick()

    def contextMenuEvent(self, event):
        if not self.innerFrame.property("selected"):
            self.desktop.ClearSelection()
            self.SetSelected(True)
            if self not in self.desktop.selectedItems:
                self.desktop.selectedItems.append(self)

        self.ExecuteContextMenu(event)

    def GetMenuConfig(self):
        return "item", None

    def ExecuteContextMenu(self, event):
        section, customPath = self.GetMenuConfig()

        menu = ContextMenu(section, self, customPath=customPath)
        if menu.isEmpty():
            return

        menu.commandClicked.connect(self.ExecuteItemCommand)
        menu.exec(event.globalPos())

    def ExecuteItemCommand(self, command):
        pass

    def AddExternalMimeData(self, mimeData):
        pass

    def ExecuteDoubleClick(self):
        pass
