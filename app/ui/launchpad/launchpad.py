import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLineEdit, QScrollArea, QLabel, QGridLayout,
    QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter
from core.utils import MakeBlur, WSHELL
from ui.components import PowerButton
from .item import LaunchpadItem
from .config import LConfig
from core.managers import LaunchpadStateManager

class Launchpad(QWidget):
    def __init__(self):
        super().__init__()
        LConfig.configUpdated.connect(self.UpdateStyles)
        self.manager = LaunchpadStateManager(LConfig.launchpadInfoFile)
        self.Init()
        self.LoadApps()
        self.ApplyGeometry()

    def Init(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAcceptDrops(True)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.container = QFrame()
        self.container.setObjectName("LaunchpadContainer")
        self.container.setFixedSize(LConfig.containerWidth, LConfig.containerHeight)

        self.container.setStyleSheet(LConfig.containerStyle)

        containerLayout = QVBoxLayout(self.container)
        containerLayout.setContentsMargins(30, 30, 30, 30)
        containerLayout.setSpacing(20)

        self.searchBar = QLineEdit()
        self.searchBar.setPlaceholderText("Search...")
        self.searchBar.setFixedHeight(45)
        self.searchBar.setStyleSheet(LConfig.searchbarStyle)
        containerLayout.addWidget(self.searchBar)

        self.searchBar.installEventFilter(self)
        self.searchBar.returnPressed.connect(self.LaunchFirstApp)
        self.searchBar.textChanged.connect(self.FilterApps)

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setStyleSheet(LConfig.scrollAreaStyle)

        scrollContent = QWidget()
        scrollContent.setStyleSheet("background: transparent;")
        self.scrollLayout = QVBoxLayout(scrollContent)
        self.scrollLayout.setSpacing(20)

        labelStyle = "color: rgba(255, 255, 255, 150); font-size: 14px; font-weight: bold; margin-bottom: 5px;"

        self.pinnedLabel = QLabel("Pinned")
        self.pinnedLabel.setStyleSheet(labelStyle)
        self.pinnedGrid = QGridLayout()
        self.pinnedGrid.setSpacing(15)
        self.scrollLayout.addWidget(self.pinnedLabel)
        self.scrollLayout.addLayout(self.pinnedGrid)

        self.allAppsLabel = QLabel("All Programs")
        self.allAppsLabel.setStyleSheet(labelStyle)
        self.allAppsGrid = QGridLayout()
        self.allAppsGrid.setSpacing(15)
        self.scrollLayout.addWidget(self.allAppsLabel)
        self.scrollLayout.addLayout(self.allAppsGrid)

        self.scrollLayout.addStretch()
        self.scrollArea.setWidget(scrollContent)
        containerLayout.addWidget(self.scrollArea)

        bottomLayout = QHBoxLayout()
        self.userLabel = QLabel(os.getlogin())
        self.userLabel.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")

        self.powerMenu = PowerButton()

        bottomLayout.addWidget(self.userLabel)
        bottomLayout.addStretch()
        bottomLayout.addWidget(self.powerMenu)

        containerLayout.addLayout(bottomLayout)
        self.mainLayout.addWidget(self.container)

    def ApplyGeometry(self):
        screen = QApplication.primaryScreen().geometry()

        if LConfig.isFullscreen:
            self.setGeometry(screen)
        else:
            x = (screen.width() - LConfig.containerWidth) // 2
            y = (screen.height() - LConfig.containerHeight) // 2
            self.setGeometry(x, y, LConfig.containerWidth, LConfig.containerHeight)

        self.RefreshGrids()

    def UpdateStyles(self, source = None, changedSections = None):
        self.container.setFixedSize(LConfig.containerWidth, LConfig.containerHeight)
        self.container.setStyleSheet(LConfig.containerStyle)
        self.searchBar.setStyleSheet(LConfig.searchbarStyle)
        self.scrollArea.setStyleSheet(LConfig.scrollAreaStyle)

        self.ApplyGeometry()

    def showEvent(self, event):
        if LConfig.blurEnabled:
            MakeBlur(self.winId(), True, LConfig.blurMode, LConfig.fullscreenColor)
        else:
            MakeBlur(self.winId(), False)

        super().showEvent(event)
        self.activateWindow()
        self.raise_()
        self.searchBar.setFocus()
        self.BuildVisualGrid()

    def paintEvent(self, event):
        if LConfig.blurEnabled and LConfig.isFullscreen and LConfig.blurMode != 1:
            painter = QPainter(self)
            painter.setBrush(QColor(LConfig.fullscreenColor))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(self.rect())

    def BuildVisualGrid(self):
        self.visualGrid = []

        if self.searchBar.text():
            rowItems = []
            for item in self.appWidgets:
                if item.isVisible():
                    rowItems.append(item)
                    if len(rowItems) == LConfig.columns:
                        self.visualGrid.append(rowItems)
                        rowItems = []
            if rowItems:
                self.visualGrid.append(rowItems)
        else:
            pinnedPaths = self.manager.state.get("launchpad", [])
            pinnedRow = []
            for path in pinnedPaths:
                item = next((w for w in self.appWidgets if w.path == path), None)
                if item and item.isVisible():
                    pinnedRow.append(item)
                    if len(pinnedRow) == LConfig.columns:
                        self.visualGrid.append(pinnedRow)
                        pinnedRow = []
            if pinnedRow:
                self.visualGrid.append(pinnedRow)

            allRow = []
            for item in self.appWidgets:
                if item.path not in pinnedPaths and item.isVisible():
                    allRow.append(item)
                    if len(allRow) == LConfig.columns:
                        self.visualGrid.append(allRow)
                        allRow = []
            if allRow:
                self.visualGrid.append(allRow)

    def LoadApps(self):
        pathsToScan = [
            os.path.join(os.environ.get("ProgramData", "C:\\ProgramData"), r"Microsoft\Windows\Start Menu\Programs"),
            os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs")
        ]

        foundApps = []

        for scanPath in pathsToScan:
            if not os.path.exists(scanPath):
                continue
            for root, dirs, files in os.walk(scanPath):
                for file in files:
                    if file.lower().endswith('.lnk'):
                        if "uninstall" in file.lower() or "удалить" in file.lower():  # how tf can i except ts 😭
                            continue

                        fullPath = os.path.join(root, file)

                        try:
                            shortcut = WSHELL.CreateShortCut(fullPath)
                            targetPath = shortcut.Targetpath

                            if not targetPath.lower().endswith('.exe'):
                                continue

                        except Exception:
                            continue

                        name = os.path.splitext(file)[0]
                        foundApps.append({"name": name, "path": fullPath})

        foundApps.sort(key = lambda x: x["name"].lower())

        self.appWidgets = []

        for app in foundApps:
            item = LaunchpadItem(self, app["name"], app["path"])
            self.appWidgets.append(item)

        self.FilterApps("")

    def PinItem(self, path):
        if path not in self.manager.state["launchpad"]: 
            self.manager.state["launchpad"].append(path)
            self.manager.Save()

    def UnpinItem(self, path):
        if path in self.manager.state["launchpad"]:
            self.manager.state["launchpad"].remove(path)
            self.manager.Save()

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

            sourcePath = event.mimeData().text()
            pos = event.position().toPoint()
            widgetAtPos = self.childAt(pos)

            targetPath = None
            while widgetAtPos:
                if isinstance(widgetAtPos, LaunchpadItem):
                    targetPath = widgetAtPos.path
                    break
                widgetAtPos = widgetAtPos.parentWidget()

            if targetPath and targetPath != sourcePath:
                pinnedList = self.manager.state.get("launchpad", [])

                if sourcePath in pinnedList and targetPath in pinnedList:
                    sourceIDX = pinnedList.index(sourcePath)
                    targetIDX = pinnedList.index(targetPath)

                    pinnedList.pop(sourceIDX)
                    pinnedList.insert(targetIDX, sourcePath)

                    self.LiveUpdatePinnedGrid()

    def LiveUpdatePinnedGrid(self):
        pinnedPaths = self.manager.state.get("launchpad", [])
        pinnedRow, pinnedColumn = 0, 0

        for path in pinnedPaths:
            item = next((w for w in self.appWidgets if w.path == path), None)
            if item:
                self.pinnedGrid.addWidget(item, pinnedRow, pinnedColumn, alignment = Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
                pinnedColumn += 1
                if pinnedColumn >= LConfig.columns:
                    pinnedColumn = 0
                    pinnedRow += 1

        self.BuildVisualGrid()

    def dropEvent(self, event):
        self.manager.Save()
        event.acceptProposedAction()

    def MoveFocus(self, currentItem, direction):
        if not self.visualGrid:
            return

        currentRow, currentColumn = -1, -1
        for r, row in enumerate(self.visualGrid):
            if currentItem in row:
                currentRow = r
                currentColumn = row.index(currentItem)
                break

        if currentRow == -1:
            return

        nextRow, nextColumn = currentRow, currentColumn

        if direction == "right":
            nextColumn += 1
            if nextColumn >= len(self.visualGrid[currentRow]):
                if currentRow + 1 < len(self.visualGrid):
                    nextRow += 1
                    nextColumn = 0
                else:
                    nextColumn -= 1

        elif direction == "left":
            nextColumn -= 1
            if nextColumn < 0:
                if currentRow - 1 >= 0:
                    nextRow -= 1
                    nextColumn = len(self.visualGrid[nextRow]) - 1
                else:
                    nextColumn = 0

        elif direction == "down":
            if currentRow + 1 < len(self.visualGrid):
                nextRow += 1
                nextColumn = min(currentColumn, len(self.visualGrid[nextRow]) - 1)

        elif direction == "up":
            if currentRow - 1 >= 0:
                nextRow -= 1
                nextColumn = min(currentColumn, len(self.visualGrid[nextRow]) - 1)
            else:
                self.searchBar.setFocus()
                return

        targetWidget = self.visualGrid[nextRow][nextColumn]
        targetWidget.setFocus()
        self.scrollArea.ensureWidgetVisible(targetWidget, 0, 50)

    def RefreshGrids(self):
        self.FilterApps(self.searchBar.text())

    def FilterApps(self, query):
        query = query.lower()

        # i can delete this in future, or also make it cooler if i like this idea btw

        ENLayout = "qwertyuiop[]asdfghjkl;'zxcvbnm,./"
        RULayout = "йцукенгшщзхъфывапролджэячсмитьбю."
        UKLayout = "йцукенгшщзхїфівапролджєячсмитьбю."

        toENFromRU = str.maketrans(RULayout, ENLayout)
        toENFromUK = str.maketrans(UKLayout, ENLayout)
        toRUFromEN = str.maketrans(ENLayout, RULayout)

        searchVariants = {
            query,
            query.translate(toENFromRU),
            query.translate(toENFromUK),
            query.translate(toRUFromEN)
        }

        for item in self.appWidgets:
            self.pinnedGrid.removeWidget(item)
            self.allAppsGrid.removeWidget(item)
            item.hide()

        pinnedPaths = self.manager.state.get("launchpad", [])

        # The code is really shitty from now on. Protect your eyes.

        # search mode
        if query:
            self.pinnedLabel.hide()

            row, column = 0, 0
            for item in self.appWidgets:
                appName = item.name.lower()
                if any(variant in appName for variant in searchVariants):
                    self.allAppsGrid.addWidget(item, row, column, alignment = Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
                    item.show()

                    column += 1
                    if column >= LConfig.columns:
                        column = 0
                        row += 1
        else:
            self.pinnedLabel.show()

            # rendering pinned
            pinnedRow, pinnedColumn = 0, 0
            for path in pinnedPaths:
                item = next((w for w in self.appWidgets if w.path == path), None)
                if item:
                    self.pinnedGrid.addWidget(item, pinnedRow, pinnedColumn, alignment = Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
                    item.show()
                    pinnedColumn += 1
                    if pinnedColumn >= LConfig.columns:
                        pinnedColumn = 0
                        pinnedRow += 1

            # rendering all
            allRow, allColumn = 0, 0
            for item in self.appWidgets:
                if item.path not in pinnedPaths:
                    self.allAppsGrid.addWidget(item, allRow, allColumn, alignment = Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
                    item.show()
                    allColumn += 1
                    if allColumn >= LConfig.columns:
                        allColumn = 0
                        allRow += 1

        self.BuildVisualGrid()

    def LaunchFirstApp(self):
        for item in self.appWidgets:
            if item.isVisible():
                self.close()
                try:
                    os.startfile(self.path)
                except OSError:
                    pass

    def eventFilter(self, obj, event):
        if obj == self.searchBar and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Down:
                if hasattr(self, 'visualGrid') and self.visualGrid and self.visualGrid[0]:
                    firstItem = self.visualGrid[0][0]
                    firstItem.setFocus()
                    self.scrollArea.ensureWidgetVisible(firstItem, 0, 50)
                    return True
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        if not self.container.geometry().contains(event.pos()):
            self.close()
        else:
            self.setFocus()
        super().mousePressEvent(event)

    def changeEvent(self, event):
        if event.type() == event.Type.ActivationChange:
            if not self.isActiveWindow():
                self.close()
        super().changeEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Down:
            if self.visualGrid[0]:
                firstItem = self.visualGrid[0][0]
                firstItem.setFocus()
                self.scrollArea.ensureWidgetVisible(firstItem, 0, 50)

        elif event.key() == Qt.Key.Key_Up:
            self.searchBar.setFocus()

        elif event.key() == Qt.Key.Key_Escape or Qt.Key.Key_Control:
            self.close()

        else:
            super().keyPressEvent(event)
