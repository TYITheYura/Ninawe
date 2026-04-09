from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QFrame,
    QScrollArea, QPushButton, QApplication
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from ui.powermenu import PMConfig
from core.config import config as configurator
import json
import os
import subprocess
from core.utils import MakeLog

class PowerButton(QFrame):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.isExpanded = False
        self.setFixedHeight(50)
        self.setFixedWidth(50)

        self.setStyleSheet("""
            PowerButton {
                background-color: rgba(43, 43, 43, 220);
                border-radius: 25px;
            }
        """)

        self.userPreferencesData = {}

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("""
            background: transparent;
            border: none;
        """)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.content = QWidget()
        self.content.setStyleSheet("background: transparent;")
        self.buttonsLayout = QHBoxLayout(self.content)
        self.buttonsLayout.setContentsMargins(0, 0, 0, 0)
        self.buttonsLayout.setSpacing(5)
        self.scroll.setWidget(self.content)

        self.scroll.hide()

        self.mainBtn = QPushButton()
        self.mainBtn.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.mainBtn.setIcon(QIcon(configurator.theme.GetPath(f"app\\ui\\components\\powerbutton\\resources\\icon\\icon.svg")))
        self.mainBtn.setFixedSize(50, 50)
        self.mainBtn.setStyleSheet("""
            QPushButton {
                background-color: #22000000;
                color: white;
                border-radius: 25px;
                font-size: 20px;
                border: none;
                text-align: center;
                outline: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 100, 100, 150);
            }
            QPushButton:focus {
                background-color: rgba(255, 100, 100, 150);
            }
            QPushButton:pressed {
                background-color: rgba(255, 100, 100, 200);
                border: none;
            }
        """)
        self.mainBtn.clicked.connect(self.ToggleMenu)

        self.layout.addWidget(self.scroll)
        self.layout.addWidget(self.mainBtn)

        QApplication.instance().focusChanged.connect(self.OnGlobalFocusChanged)

        self.LoadUserPreferences()
        self.LoadItems()

        self.mainBtn.installEventFilter(self)

    def LoadItems(self):
        for i in reversed(range(self.buttonsLayout.count())): 
            self.buttonsLayout.itemAt(i).widget().setParent(None)

        for buttonPreference in self.userPreferencesData.get("buttons"):
            if buttonPreference.get("action") == "close":
                continue
            button = QPushButton()
            button.setFocusPolicy(Qt.FocusPolicy.TabFocus)
            buttonID = buttonPreference.get("id")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setFixedSize(30, 30)

            button.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 20);
                    color: white;
                    border-radius: 15px;
                    font-size: 10px;
                    outline: none;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 50);
                }
                QPushButton:focus {
                    background-color: rgba(255, 255, 255, 50);
                    border: none;
                }
            """)

            button.clicked.connect(
                lambda required_variable_because_without_it_clicked_method_overriding_type_variable,
                type = buttonPreference.get("type"),
                act = buttonPreference.get("action"):
                    self.ExecuteCommand(type, act)
            )

            icon = buttonPreference.get("icon")

            if icon == "default":
                icon = configurator.theme.GetPath(f"app\\assets\\powermenuicons\\{buttonID}.svg")
            else:
                icon = configurator.theme.GetPath(f"{PMConfig.iconsDir}\\{buttonID}.svg")

            if os.path.exists(icon):
                iconSize = round(button.width() // 1.5)
                button.setIcon(QIcon(icon))
                button.setIconSize(QSize(iconSize, iconSize))
            else:
                button.setText(buttonID[0].upper())

            self.buttonsLayout.addWidget(button)

            button.installEventFilter(self)

    def ToggleMenu(self):
        if self.isExpanded:
            self.scroll.hide()
            self.setFixedWidth(50)
            self.isExpanded = False
            self.mainBtn.clearFocus()
        else:
            itemsCount = self.buttonsLayout.count()
            targetWidth = min(250, 45 + (itemsCount * 40) + 15)

            self.setFixedWidth(targetWidth)
            self.scroll.show()
            self.isExpanded = True

    def ExecuteCommand(self, type, action):
        # Console commands
        if type == "console":
            try:
                os.system(action)
                self.close()
            except Exception as e:
                MakeLog(f"[Log] [PowerButton] [ExecuteCommand] | CMD failed: {e}")

        # Programs
        elif type == "program":
            try:
                subprocess.Popen(action, shell=True)
                self.close()
            except Exception as e:
                MakeLog(f"[Log] [PowerButton] [ExecuteCommand] | Exec failed: {e}")

        self.ToggleMenu()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            self.ToggleMenu()

    def LoadUserPreferences(self):
        with open(PMConfig.userPreferencesPath, "r") as preferences:
            self.userPreferencesData = json.load(preferences)

    def eventFilter(self, obj, event):
        if event.type() == event.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Right):
                buttonsList = []
                for i in range(self.buttonsLayout.count()):
                    widget = self.buttonsLayout.itemAt(i).widget()
                    if widget:
                        buttonsList.append(widget)
                buttonsList.append(self.mainBtn)

                if obj not in buttonsList:
                    return super().eventFilter(obj, event)

                currentIDX = buttonsList.index(obj)

                if event.key() == Qt.Key.Key_Left:
                    if obj == self.mainBtn and not self.isExpanded:
                        self.ToggleMenu()
                        if len(buttonsList) > 1:
                            target = buttonsList[-2]
                            target.setFocus()
                            self.scroll.ensureWidgetVisible(target, 0, 0)
                        return True

                    if currentIDX > 0:
                        target = buttonsList[currentIDX - 1]
                        target.setFocus()
                        if target != self.mainBtn:
                            self.scroll.ensureWidgetVisible(target, 0, 0)
                    return True

                elif event.key() == Qt.Key.Key_Right:
                    if currentIDX < len(buttonsList) - 1:
                        target = buttonsList[currentIDX + 1]
                        target.setFocus()
                        if target != self.mainBtn:
                            self.scroll.ensureWidgetVisible(target, 0, 0)
                    return True

        return super().eventFilter(obj, event)

    def OnGlobalFocusChanged(self, oldWidgetThatIsNotUsedThere, newWidget):
        if self.isExpanded:
            if not self.isAncestorOf(newWidget) and newWidget != self.mainBtn:
                self.ToggleMenu()
