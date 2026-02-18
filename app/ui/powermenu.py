from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QApplication, QFrame
from PyQt6.QtCore import Qt, QSize, QFileSystemWatcher
from PyQt6.QtGui import QColor, QAction, QIcon
from core.config import config as configurator
from core.utils import MakeBlur
import subprocess
import json
import sys
import os

class PowerMenu(QWidget):
    def __init__(self):
        super().__init__()

        self.screen = self.spacing = None
        self.buttonSize = self.radius = None
        self.blurEnabled = self.blurMode = None
        self.buttonColor = self.hoverColor = self.pressedColor = None
        self.isFullscreen = self.bgColor = None

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.Tool | 
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.layout = QHBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.section = "PowerMenu"

        # Button container
        self.container = QFrame(self)
        self.containerLayout = QHBoxLayout(self.container)
        self.layout.addWidget(self.container)

        # User preferences file
        self.userPreferencesPath = configurator.theme.GetPath("userdata\\preferences\\user\\powermenudata.json")
        self.userPreferencesData = {}

        # Buttons object dict
        self.buttons = {}

        # File changed events
        self.powerMenuUserPropertiesWatcher = QFileSystemWatcher()
        if os.path.exists(self.userPreferencesPath):
            self.powerMenuUserPropertiesWatcher.addPath(self.userPreferencesPath)
            self.powerMenuUserPropertiesWatcher.fileChanged.connect(self.LoadUserPreferences)
        configurator.configUpdated.connect(self.UpdateStyles)
        
        self.LoadUserPreferences()

    def UpdateStyles(self, source = None, changedSections = None):
        # If initial run or data update required
        if "ALL" in changedSections or "init" in source:
            pass
        # If section is changed
        elif "PowerMenu" in changedSections:
            pass
        # if update for PowerMenu not required
        else:
            return

        while self.containerLayout.count():
            item = self.containerLayout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self.screen = QApplication.primaryScreen().geometry()
        self.buttonSize = configurator.theme.GetInt(self.section, "button_size", fallback = 80)
        self.radius = configurator.theme.GetInt(self.section, "border_radius", fallback = 20)
        self.hoverColor = configurator.theme.Get(self.section, "hover_color", fallback = "#FFFFFF20")
        self.pressedColor = configurator.theme.Get(self.section, "pressed_color", fallback = "#FFFFFF40")
        self.spacing = configurator.theme.GetInt(self.section, "spacing", fallback = 50)
        self.buttonColor = configurator.theme.Get(self.section, "button_color", fallback = "transperent")
        self.isFullscreen = configurator.theme.GetBool(self.section, "fullscreen", fallback = True)
        self.blurEnabled = configurator.theme.GetBool(self.section, "blur_enabled", fallback = True)
        self.blurMode = configurator.theme.GetInt(self.section, "blur_mode", fallback = 4)
        self.bgColor = configurator.theme.Get(self.section, "argb_color", fallback = "#00000080")
        self.borderWidth = configurator.theme.GetInt(self.section, "border_width_px", fallback = 1)

        # Data apply
        for buttonPreference in self.userPreferencesData.get("buttons"):
            button = QPushButton()
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(
                lambda required_variable_because_without_it_clicked_method_overriding_type_variable,
                type = buttonPreference.get("type"),
                act = buttonPreference.get("action"): 
                    self.RunCommand(type, act)
            )
            self.containerLayout.addWidget(button)
            self.buttons[buttonPreference.get("id")] = button
            buttonStyle = f"""
                QPushButton {{
                    background-color: {self.buttonColor};
                    border: {self.borderWidth}px solid white;
                    border-radius: {self.radius}px;
                    color: white;
                    font-size: 50px;
                    font-family: "Visitor TT2 BRK";
                    font-weight: bold;

                }}
                QPushButton:hover {{ background-color: {self.hoverColor}; }}
                QPushButton:pressed {{ background-color: {self.pressedColor}; }}
            """ + buttonPreference.get("overrideStyles", "")
            button.setStyleSheet(buttonStyle)
        
        if self.isFullscreen:
            self.setGeometry(self.screen)
            self.setStyleSheet(f"background-color: {self.bgColor};")
        else:
            w = configurator.theme.GetInt(self.section, "width", fallback=600)
            h = configurator.theme.GetInt(self.section, "height", fallback=200)
            x = (self.screen.width() - w) // 2
            y = (self.screen.height() - h) // 2
            self.setGeometry(x, y, w, h)
            self.setStyleSheet("background-color: transparent;")

        self.container.setFixedSize(
             configurator.theme.GetInt(self.section, "width", fallback=600),
             configurator.theme.GetInt(self.section, "height", fallback=200)
        )
        self.containerLayout.setSpacing(self.spacing)
        
        for name, button in self.buttons.items():
            button.setFixedSize(self.buttonSize, self.buttonSize)
            # button.setIcon() 
            button.setText(name[0].upper())

        self.update()

    def LoadUserPreferences(self):
        print("[Log] [PowerMenu] [UserPreferences] | Changes detected. Reloading.")
        # Deleting buttons 
        self.buttons.clear()

        # Opening powermenudata.json (user preferences)
        with open(self.userPreferencesPath, "r") as preferences:
            self.userPreferencesData = json.load(preferences)

        self.UpdateStyles("manual", ["ALL"])

    def paintEvent(self, event):
        if self.blurEnabled:
            MakeBlur(self.winId(), True, self.blurMode, self.bgColor if not self.isFullscreen else "#00000000")
        else:
            MakeBlur(self.winId(), False)

    def showEvent(self, event):
        super().showEvent(event)
        self.activateWindow()
        self.setFocus()

    # Closing with ESC
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    def mousePressEvent(self, event):
        # Clicked on back (NOT WORKING IDK WHY :((((((()
        if self.childAt(event.pos()) is None:
             self.close()

    def RunCommand(self, type, action):
        # Build-in commands
        if type == "integrated":
            if action == "close":
                self.close()

        # Console commands
        elif type == "console":
            try:
                os.system(action)
                self.close()
            except Exception as e:
                print(f"[Error] CMD failed: {e}")

        # Programs
        elif type == "program":
            try:
                subprocess.Popen(action, shell=True)
                self.close()
            except Exception as e:
                print(f"[Log] [PowerMenu] [RunCommand] | Exec failed: {e}")