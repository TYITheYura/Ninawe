from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QApplication, QFrame
from PyQt6.QtCore import Qt, QSize, QFileSystemWatcher, QRectF
from PyQt6.QtGui import QColor, QAction, QIcon, QPainter, QBrush
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
        self.isFullscreen = self.bgColor = self.containerColor = None
        self.containerWidth = self.containerHeight = None
        self.themeUpdatedState = True

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.Tool | 
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.section = "PowerMenu"

        # Button container
        self.container = QFrame(self)
        self.container.setObjectName("PowerMenuContainer")
        self.containerLayoutForButtons = QHBoxLayout(self.container)
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

        while self.containerLayoutForButtons.count():
            item = self.containerLayoutForButtons.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self.screen = QApplication.primaryScreen().geometry()
        self.buttonSize = configurator.theme.GetInt(self.section, "button_size", fallback = 80)
        self.hoverColor = configurator.theme.Get(self.section, "hover_color", fallback = "#FFFFFF20")
        self.pressedColor = configurator.theme.Get(self.section, "pressed_color", fallback = "#FFFFFF40")
        self.spacing = configurator.theme.GetInt(self.section, "spacing", fallback = 50)
        self.buttonColor = configurator.theme.Get(self.section, "button_color", fallback = "transparent")
        self.isFullscreen = configurator.theme.GetBool(self.section, "fullscreen", fallback = True)
        self.blurEnabled = configurator.theme.GetBool(self.section, "blur_enabled", fallback = True)
        self.blurMode = configurator.theme.GetInt(self.section, "blur_mode", fallback = 4)
        self.radius = 0 if self.blurEnabled else configurator.theme.GetInt("PowerMenu", "border_radius_px", fallback = 10)
        self.bgColor = configurator.theme.Get(self.section, "argb_background_color", fallback = "#00000080")
        self.containerColor = configurator.theme.Get(self.section, "argb_container_color", fallback = "#00000080")
        self.borderWidth = configurator.theme.GetInt(self.section, "border_width_px", fallback = 1)
        self.borderColor = configurator.theme.Get(self.section, "argb_border_color", fallback = "#00000080")
        self.buttonBorder = configurator.theme.GetInt(self.section, "button_border", fallback = 0)
        self.containerWidth = configurator.theme.GetInt(self.section, "width", fallback = 600)
        self.containerHeight = configurator.theme.GetInt(self.section, "height", fallback = 200)
        self.containerMargins = configurator.theme.GetInt(self.section, "margins", fallback = 0)
        self.doubleContainerBackground = configurator.theme.GetBool(self.section, "double_container_bg", fallback = False)
        self.doubleContainerBackgroundAccent = configurator.theme.Get(self.section, "double_container_bg_accent", fallback = "bg")
        self.iconsDir = configurator.theme.Get(self.section, "icons_dir", fallback = "")

        # =[> Panel color
        if self.blurEnabled and self.blurMode == 1:
            # config blur mode: 1 (4 - acrylic)
            self.qtBgColor = QColor(0, 0, 0, 0)
            self.winBlurColor = self.bgColor
        else:
            # config blur mode: 0 (3 - default) / enable_blur = False
            self.qtBgColor = QColor(self.bgColor)
            self.winBlurColor = "#00000000"

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
            self.containerLayoutForButtons.addWidget(button)
            self.buttons[buttonPreference.get("id")] = button
            buttonStyle = f"""
                QPushButton {{
                    background-color: {self.buttonColor};
                    border: {self.buttonBorder}px solid white;
                    border-radius: {self.radius}px;
                    color: white;
                    font-size: 50px;
                    font-family: "Visitor TT2 BRK";
                    font-weight: bold;
                    margin: 0;

                }}
                QPushButton:hover {{ background-color: {self.hoverColor}; }}
                QPushButton:pressed {{ background-color: {self.pressedColor}; }}
            """ + buttonPreference.get("overrideStyles", "")
            button.setStyleSheet(buttonStyle)

        self.container.setStyleSheet(f"""
            QFrame#PowerMenuContainer {{
                background-color: {self.containerColor if self.doubleContainerBackground else "transparent"};
                border-radius: {self.radius}px;
                margin: {self.containerMargins if self.doubleContainerBackground else 0}px;
            }}
        """)

        # Pasting buttons
        for buttonID, button in self.buttons.items():
            button.setFixedSize(self.buttonSize, self.buttonSize)
            icon = buttonPreference.get("icon")
            if icon == "default":
                icon = configurator.theme.GetPath(f"app\\assets\\powermenuicons\\{buttonID}.svg")
            else:
                icon = configurator.theme.GetPath(f"{self.iconsDir}\\{buttonID}.svg")
            
            if os.path.exists(icon):
                iconSize = self.buttonSize // 2
                button.setIcon(QIcon(icon))
                button.setIconSize(QSize(iconSize, iconSize))
            else:
                button.setText(buttonID[0].upper())

        self.containerLayoutForButtons.setSpacing(self.spacing)
        self.containerLayoutForButtons.setAlignment(Qt.AlignmentFlag.AlignCenter)

        QApplication.processEvents()

        # Reset the sizes that were previously in setFixedSize
        self.container.setMinimumSize(0, 0)
        self.container.setMaximumSize(16777215, 16777215)

        # Reseting old sizes & correction of the width if the container size is larger than the size specified in the config
        self.container.resize(1, 1)
        self.container.adjustSize()
        self.adjustSize()

        containerRealWidth = self.container.width()
        containerRealHeight = self.container.height()
        self.containerWidthMax = max(containerRealWidth, self.containerWidth)
        self.containerHeightMax = max(containerRealHeight, self.containerHeight)

        if self.isFullscreen:
            self.setGeometry(self.screen)
        else:
            x = (self.screen.width() - self.containerWidthMax) // 2
            y = (self.screen.height() - self.containerHeightMax) // 2
            self.setGeometry(x, y, self.containerWidthMax, self.containerHeightMax)
            self.setStyleSheet(f"background-color: transparent;")
        
        self.container.setFixedSize(self.containerWidthMax, self.containerHeightMax)

        self.themeUpdatedState = True
        self.update()

    def ColorPicker(self):
        if self.doubleContainerBackground == True:
            if self.doubleContainerBackgroundAccent == "container":
                return self.containerColor
            else:
                return self.bgColor
        else:
            return self.containerColor

    def LoadUserPreferences(self):
        print("[Log] [PowerMenu] [UserPreferences] | Changes detected. Reloading.")
        # Deleting buttons 
        self.buttons.clear()

        # Opening powermenudata.json (user preferences)
        with open(self.userPreferencesPath, "r") as preferences:
            self.userPreferencesData = json.load(preferences)

        self.UpdateStyles("manual", ["ALL"])

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # =[> Blur apply (the first and last update of the blur if the config is not updated in the future)
        if self.themeUpdatedState:
            if self.blurEnabled:
                MakeBlur(self.winId(), True, self.blurMode, self.bgColor)
            else:
                MakeBlur(self.winId(), False)
            self.themeUpdatedState = False

        if self.isFullscreen and not self.blurEnabled:
            painter.setBrush(QColor(self.bgColor)) 
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(self.rect())

        # Border only to container
        rect = QRectF(self.container.geometry())
        
        # Border maker 2000
        if self.borderWidth > 0:
            pen = painter.pen()
            pen.setColor(QColor(self.borderColor))
            pen.setWidth(self.borderWidth)
            pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
            painter.setPen(pen)

            halfWidth = self.borderWidth / 2
            drawRect = rect.adjusted(halfWidth, halfWidth, -halfWidth, -halfWidth)
        else:
            painter.setPen(Qt.PenStyle.NoPen)
            drawRect = rect
        
        # Drawing background
        painter.setBrush(QBrush(QColor(self.ColorPicker())))

        # Drawing border
        painter.drawRoundedRect(drawRect, self.radius, self.radius)

    def showEvent(self, event):
        super().showEvent(event)
        self.activateWindow()
        self.setFocus()

    # Closing with ESC
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    def mousePressEvent(self, event):
        # Working only when background not transperent sadly.
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
                print(f"[Log] [PowerMenu] [RunCommand] | CMD failed: {e}")

        # Programs
        elif type == "program":
            try:
                subprocess.Popen(action, shell=True)
                self.close()
            except Exception as e:
                print(f"[Log] [PowerMenu] [RunCommand] | Exec failed: {e}")