from PyQt6.QtWidgets import QWidget, QBoxLayout, QPushButton, QApplication, QFrame
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
        self.containerWidth = self.containerHeight = self.containerMargins = None
        self.themeUpdatedState = True
        self.borderWidth = self.borderColor = None
        self.buttonBorder = None
        self.doubleContainerBackground = self.doubleContainerBackgroundAccent = None
        self.iconsDir = None
        self.doubleContainerColor = self.fullscreenColor = None
        self.useBGColor = None
        self.section = "PowerMenu"
        
        self.menuLayout = None

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.Tool | 
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Button container
        self.container = QFrame(self)
        
        # Layouts
        self.layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, self)
        self.containerLayoutForButtons = QBoxLayout(QBoxLayout.Direction.LeftToRight, self.container)
        
        # Layout props set
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Button container set
        self.container.setObjectName("PowerMenuContainer")
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
        self.blurMode = configurator.theme.GetInt(self.section, "blur_mode", fallback = 0)
        self.radius = 0 if self.blurEnabled and self.isFullscreen == False else configurator.theme.GetInt("PowerMenu", "border_radius", fallback = 10)
        self.bgColor = configurator.theme.Get(self.section, "argb_background_color", fallback = "#00000080")
        self.containerColor = configurator.theme.Get(self.section, "argb_container_color", fallback = "#00000080")
        self.borderWidth = configurator.theme.GetInt(self.section, "border_width_px", fallback = 1)
        self.borderColor = configurator.theme.Get(self.section, "argb_border_color", fallback = "#00000080")
        self.buttonBorder = configurator.theme.GetInt(self.section, "button_border", fallback = 0)
        self.containerWidth = configurator.theme.GetInt(self.section, "width", fallback = 600)
        self.containerHeight = configurator.theme.GetInt(self.section, "height", fallback = 200)
        self.containerMargins = configurator.theme.GetInt(self.section, "margins", fallback = 0)
        self.containerPaddings = configurator.theme.GetInt(self.section, "paddings", fallback = 10)
        self.doubleContainerBackground = configurator.theme.GetBool(self.section, "double_container_bg", fallback = False)
        self.doubleContainerBackgroundAccent = configurator.theme.Get(self.section, "double_container_bg_accent", fallback = "bg")
        self.iconsDir = configurator.theme.Get(self.section, "icons_dir", fallback = "")
        self.useBGColor = configurator.theme.GetBool    (self.section, "use_bg_color", fallback = False)

        self.LayoutPicker()
        self.ColorPicker(True)

        # Button maker
        for buttonPreference in self.userPreferencesData.get("buttons"):
            button = QPushButton()
            buttonID = buttonPreference.get("id")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            
            button.clicked.connect(
                lambda required_variable_because_without_it_clicked_method_overriding_type_variable,
                type = buttonPreference.get("type"),
                act = buttonPreference.get("action"): 
                    self.RunCommand(type, act)
            )
            
            buttonStyle = f"""
                QPushButton {{
                    background-color: {self.buttonColor};
                    border: {self.buttonBorder}px solid white;
                    border-radius: {self.radius}px;
                    color: white;
                    font-size: 20px;
                    font-family: "Arial";
                    font-weight: bold;
                    margin: 0;
                }}
                QPushButton:hover {{ background-color: {self.hoverColor}; }}
                QPushButton:pressed {{ background-color: {self.pressedColor}; }}
            """ + buttonPreference.get("overrideStyles", "")

            button.setStyleSheet(buttonStyle)
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

            self.containerLayoutForButtons.addWidget(button)
            self.buttons[buttonID] = button

        # Container style
        self.container.setStyleSheet(f"""
            QFrame#PowerMenuContainer {{
                background-color: transparent;
            }}
        """)

        self.containerLayoutForButtons.setContentsMargins(0, 0, 0, 0)
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

        self.containerWidthMax = max(containerRealWidth, self.containerWidth) + self.containerPaddings * 2 + self.borderWidth * 2
        self.containerHeightMax = max(containerRealHeight, self.containerHeight) + self.containerPaddings * 2 + self.borderWidth * 2

        self.containerWidthMax = self.containerWidthMax + self.containerMargins * 2 if self.doubleContainerBackground else self.containerWidthMax
        self.containerHeightMax = self.containerHeightMax + self.containerMargins * 2 if self.doubleContainerBackground else self.containerHeightMax

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

    def LayoutPicker(self):
        configLayout = configurator.theme.Get(self.section, "menu_layout", fallback = "horizontal")

        if configLayout != self.menuLayout:
            # v/h orientation picker 2000
            if configLayout == "vertical":
                direction = QBoxLayout.Direction.TopToBottom
            elif configLayout == "horizontal":
                direction = QBoxLayout.Direction.LeftToRight
            else:
                return

            # set orientation to layouts
            self.menuLayout = configLayout
            self.layout.setDirection(direction)
            self.containerLayoutForButtons.setDirection(direction)

    def ColorPicker(self, updateToBG = False):
        if updateToBG: # what the fuck.
            if self.isFullscreen:
                if self.useBGColor:
                    self.fullscreenColor = self.bgColor
                    self.doubleContainerColor = "#00000000"
                elif not self.useBGColor:
                    self.fullscreenColor = "#01000000"
                    self.doubleContainerColor = self.bgColor
            elif not self.isFullscreen:
                self.doubleContainerColor = self.ColorPicker()
                self.fullscreenColor = self.bgColor
            return

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

        # Blur
        if self.themeUpdatedState:
            if self.blurEnabled:
                MakeBlur(self.winId(), True, self.blurMode, self.fullscreenColor)
            else:
                MakeBlur(self.winId(), False)
            self.themeUpdatedState = False

        if self.isFullscreen and (not self.blurEnabled or self.blurMode != 1):
            painter.setBrush(QColor(self.fullscreenColor)) 
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(self.rect())

        buttonLen = len(self.buttons)
        if buttonLen == 0:
            print("[Log] [PowerMenu] | Seems like list of buttons is empty.")
            return

        currentMargins = self.containerMargins * 2 if self.doubleContainerBackground else 0

        layoutWidth = self.containerWidthMax - self.borderWidth * 2 - self.containerPaddings * 2 - currentMargins
        layoutHeight = self.containerHeightMax - self.borderWidth * 2 - self.containerPaddings * 2 - currentMargins

        painter.setPen(Qt.PenStyle.NoPen)
        
        # Inner container w/h
        innerW = layoutWidth + self.containerPaddings * 2
        innerH = layoutHeight + self.containerPaddings * 2
        
        # Outer container w/h
        outerW = innerW + self.containerMargins * 2
        outerH = innerH + self.containerMargins * 2

        # border & background maker 3000
        outerColor = self.doubleContainerColor if (not self.blurEnabled or self.blurMode == 0) else "#01000000"
        painter.setBrush(QBrush(QColor(outerColor)))
        
        borderRect = QRectF((self.width() - outerW) / 2, (self.height() - outerH) / 2, outerW, outerH) if self.doubleContainerBackground else QRectF((self.width() - innerW) / 2, (self.height() - innerH) / 2, innerW, innerH)

        if self.borderWidth > 0:
            pen = painter.pen()
            pen.setStyle(Qt.PenStyle.SolidLine)
            pen.setColor(QColor(self.borderColor))
            pen.setWidth(self.borderWidth)
            pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
            painter.setPen(pen)

            halfWidth = self.borderWidth / 2
            borderRect = borderRect.adjusted(-halfWidth, -halfWidth, halfWidth, halfWidth)
        else:
            painter.setPen(Qt.PenStyle.NoPen)

        painter.drawRoundedRect(borderRect, self.RadiusSelector("border"), self.RadiusSelector("border"))
        
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(Qt.PenStyle.NoPen)

        # Inner "container"
        innerRect = QRectF((self.width() - innerW) / 2, (self.height() - innerH) / 2, innerW, innerH)
        painter.setBrush(QBrush(QColor(self.containerColor)))
        painter.drawRoundedRect(innerRect, self.RadiusSelector("inner"), self.RadiusSelector("inner"))

    def RadiusSelector(self, type):
        menuSize = self.containerHeightMax if self.menuLayout == "horizontal" else self.containerWidthMax
        if type == "inner":
            margin = self.containerMargins if self.doubleContainerBackground else 0
            return self.radius * ((menuSize - margin * 2 - self.borderWidth * 2) / self.buttonSize)
        if type == "border":
            return self.radius * ((menuSize - self.borderWidth) / self.buttonSize)

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