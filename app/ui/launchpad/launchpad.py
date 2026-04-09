import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLineEdit, QScrollArea, QLabel, QGridLayout,
    QApplication
)
from PyQt6.QtCore import Qt
from core.utils import MakeBlur, WSHELL
from core.managers import LaunchpadStateManager
from core.config import config as configurator
from ui.components import PowerButton
from .item import LaunchpadItem

class Launchpad(QWidget):
    def __init__(self):
        super().__init__()
        self.launchpadInfoFile = configurator.theme.GetPath("userdata\\preferences\\user\\launchpaddata.json")
        self.manager = LaunchpadStateManager(self.launchpadInfoFile)
        self.Init()
        self.LoadApps()

    def Init(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setAcceptDrops(True)

        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)

        mainLayout = QVBoxLayout(self)
        mainLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.container = QFrame()
        self.container.setObjectName("LaunchpadContainer")
        self.container.setFixedSize(int(screen.width() * 0.6), int(screen.height() * 0.7))

        self.container.setStyleSheet("""
            QFrame#LaunchpadContainer {
                background-color: rgba(43, 43, 43, 180);
                border-radius: 24px;
                border: 1px solid rgba(255, 255, 255, 25);
            }
        """)

        containerLayout = QVBoxLayout(self.container)
        containerLayout.setContentsMargins(30, 30, 30, 30)
        containerLayout.setSpacing(20)

        self.searchBar = QLineEdit()
        self.searchBar.setPlaceholderText("Search...")
        self.searchBar.setFixedHeight(45)
        self.searchBar.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 20);
                border-radius: 10px;
                padding: 0 15px;
                color: white;
                font-size: 16px;
                border: 1px solid rgba(255, 255, 255, 30);
            }
            QLineEdit:focus {
                border: 1px solid rgba(255, 255, 255, 80);
                background-color: rgba(255, 255, 255, 30);
            }
        """)
        containerLayout.addWidget(self.searchBar)

        self.searchBar.installEventFilter(self)
        self.searchBar.returnPressed.connect(self.LaunchFirstApp)
        self.searchBar.textChanged.connect(self.FilterApps)

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 50);
                min-height: 30px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 80);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                width: 0px;
                background: none;
                border: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

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
        mainLayout.addWidget(self.container)

    def showEvent(self, event):
        MakeBlur(self.winId(), True, 1, "#11FFFFFF")
        super().showEvent(event)
        self.activateWindow()
        self.raise_()
        self.searchBar.setFocus()
        self.BuildVisualGrid()

    def BuildVisualGrid(self):
        self.visualGrid = []
        columns = 6

        if self.searchBar.text():
            rowItems = []
            for item in self.appWidgets:
                if item.isVisible():
                    rowItems.append(item)
                    if len(rowItems) == columns:
                        self.visualGrid.append(rowItems)
                        rowItems = []
            if rowItems:
                self.visualGrid.append(rowItems)
        else:
            pinnedPaths = self.manager.state.get("launchpad", [])
            pRow = []
            for path in pinnedPaths:
                item = next((w for w in self.appWidgets if w.path == path), None)
                if item and item.isVisible():
                    pRow.append(item)
                    if len(pRow) == columns:
                        self.visualGrid.append(pRow)
                        pRow = []
            if pRow:
                self.visualGrid.append(pRow)

            aRow = []
            for item in self.appWidgets:
                if item.path not in pinnedPaths and item.isVisible():
                    aRow.append(item)
                    if len(aRow) == columns:
                        self.visualGrid.append(aRow)
                        aRow = []
            if aRow:
                self.visualGrid.append(aRow)

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
        pColumns = 6
        pRow, pColumn = 0, 0

        for path in pinnedPaths:
            item = next((w for w in self.appWidgets if w.path == path), None)
            if item:
                self.pinnedGrid.addWidget(item, pRow, pColumn, alignment = Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
                pColumn += 1
                if pColumn >= pColumns:
                    pColumn = 0
                    pRow += 1

        self.BuildVisualGrid()

    def dropEvent(self, event):
        self.manager.Save()
        event.acceptProposedAction()

    def MoveFocus(self, currentItem, direction):
        if not hasattr(self, 'visualGrid') or not self.visualGrid:
            return

        currRow, currColumn = -1, -1
        for r, row in enumerate(self.visualGrid):
            if currentItem in row:
                currRow = r
                currColumn = row.index(currentItem)
                break

        if currRow == -1:
            return

        nextR, nextC = currRow, currColumn

        if direction == "right":
            nextC += 1
            if nextC >= len(self.visualGrid[currRow]):
                if currRow + 1 < len(self.visualGrid):
                    nextR += 1
                    nextC = 0
                else:
                    nextC -= 1

        elif direction == "left":
            nextC -= 1
            if nextC < 0:
                if currRow - 1 >= 0:
                    nextR -= 1
                    nextC = len(self.visualGrid[nextR]) - 1
                else:
                    nextC = 0

        elif direction == "down":
            if currRow + 1 < len(self.visualGrid):
                nextR += 1
                nextC = min(currColumn, len(self.visualGrid[nextR]) - 1)

        elif direction == "up":
            if currRow - 1 >= 0:
                nextR -= 1
                nextC = min(currColumn, len(self.visualGrid[nextR]) - 1)
            else:
                self.searchBar.setFocus()
                return

        target_widget = self.visualGrid[nextR][nextC]
        target_widget.setFocus()
        self.scrollArea.ensureWidgetVisible(target_widget, 0, 50)

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

            columns = 6
            row, col = 0, 0
            for item in self.appWidgets:
                appName = item.name.lower()
                if any(variant in appName for variant in searchVariants):
                    self.allAppsGrid.addWidget(item, row, col, alignment = Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
                    item.show()

                    col += 1
                    if col >= columns:
                        col = 0
                        row += 1
        else:
            self.pinnedLabel.show()

            # rendering pinned
            pColumns = 6
            pRow, pColumn = 0, 0

            for path in pinnedPaths:
                item = next((w for w in self.appWidgets if w.path == path), None)
                if item:
                    self.pinnedGrid.addWidget(item, pRow, pColumn, alignment = Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
                    item.show()
                    pColumn += 1
                    if pColumn >= pColumns:
                        pColumn = 0
                        pRow += 1

            # rendering all
            aColumns = 6
            aRow, aColumn = 0, 0
            for item in self.appWidgets:
                if item.path not in pinnedPaths:
                    self.allAppsGrid.addWidget(item, aRow, aColumn, alignment = Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
                    item.show()
                    aColumn += 1
                    if aColumn >= aColumns:
                        aColumn = 0
                        aRow += 1

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
        self.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Down:
            if hasattr(self, 'visualGrid') and self.visualGrid and self.visualGrid[0]:
                firstItem = self.visualGrid[0][0]
                firstItem.setFocus()
                self.scrollArea.ensureWidgetVisible(firstItem, 0, 50)

        elif event.key() == Qt.Key.Key_Up:
            self.searchBar.setFocus()

        else:
            super().keyPressEvent(event)
