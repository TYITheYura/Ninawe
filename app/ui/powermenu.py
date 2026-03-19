from PyQt6.QtWidgets import QWidget, QBoxLayout, QPushButton, QApplication, QFrame
from PyQt6.QtCore import Qt, QSize, QFileSystemWatcher, QRectF
from PyQt6.QtGui import QColor, QAction, QIcon, QPainter, QBrush
from core.config import config as configurator
from core.utils import MakeBlur, MakeLog
import subprocess
import json
import sys
import os

class PowerMenuConfig:
    def __init__(self):
        self.userPreferencesPath = configurator.theme.GetPath("userdata\\preferences\\user\\powermenudata.json")
        self.iconsDir = ""

        self.screen = None
        self.spacing = 0
        self.buttonSize = 0
        self.radius = 0
        self.blurEnabled = False
        self.blurMode = 0
        self.buttonColor = ""
        self.hoverColor = ""
        self.pressedColor = ""
        self.isFullscreen = False
        self.bgColor = ""
        self.containerColor = ""
        self.containerWidth = 0
        self.containerHeight = 0
        self.containerHeightMax = 0
        self.containerWidthMax = 0
        self.containerMargins = 0
        self.themeUpdatedState = True
        self.borderWidth = 0
        self.borderColor = 0
        self.buttonBorderWidth = 0
        self.doubleContainerBackground = False
        self.doubleContainerBackgroundAccent = "bg"
        self.doubleContainerColor = ""
        self.fullscreenColor = ""
        self.useBGColor = False
        self.menuLayout = "horizontal"
        self.containerPaddings = 0
        self.buttonStyle = ""
        self.section = "PowerMenu"

    def Updater(self):
        self.screen = QApplication.primaryScreen().geometry()
        self.buttonSize = configurator.theme.GetInt(self.section, "button_size", fallback = 80)
        self.hoverColor = configurator.theme.Get(self.section, "hover_color", fallback = "#FFFFFF20")
        self.pressedColor = configurator.theme.Get(self.section, "pressed_color", fallback = "#FFFFFF40")
        self.spacing = configurator.theme.GetInt(self.section, "spacing", fallback = 50)
        self.buttonColor = configurator.theme.Get(self.section, "button_color", fallback = "transparent")
        self.isFullscreen = configurator.theme.GetBool(self.section, "fullscreen", fallback = True)
        self.blurEnabled = configurator.theme.GetBool(self.section, "blur_enabled", fallback = True)
        self.blurMode = configurator.theme.GetInt(self.section, "blur_mode", fallback = 0)
        self.radius = 0 if self.blurEnabled and self.isFullscreen is False else configurator.theme.GetInt(self.section, "border_radius", fallback = 10)
        self.bgColor = configurator.theme.Get(self.section, "argb_background_color", fallback = "#00000080")
        self.containerColor = configurator.theme.Get(self.section, "argb_container_color", fallback = "#00000080")
        self.borderWidth = configurator.theme.GetInt(self.section, "border_width_px", fallback = 1)
        self.borderColor = configurator.theme.Get(self.section, "argb_border_color", fallback = "#00000080")
        self.buttonBorderWidth = configurator.theme.GetInt(self.section, "button_border_width", fallback = 0)
        self.buttonBorderColor = configurator.theme.Get(self.section, "button_border_color", fallback = "#FFFFFFFF")
        self.containerWidth = configurator.theme.GetInt(self.section, "width", fallback = 600)
        self.containerHeight = configurator.theme.GetInt(self.section, "height", fallback = 200)
        self.containerMargins = configurator.theme.GetInt(self.section, "margins", fallback = 0)
        self.doubleContainerBackground = configurator.theme.GetBool(self.section, "double_container_bg", fallback = False)
        self.doubleContainerBackgroundAccent = configurator.theme.Get(self.section, "double_container_bg_accent", fallback = "bg")
        self.iconsDir = configurator.theme.Get(self.section, "icons_dir", fallback = "")
        self.useBGColor = configurator.theme.GetBool(self.section, "use_bg_color", fallback = False)
        self.containerPaddings = configurator.theme.GetInt(self.section, "paddings", fallback = 10)

        self.buttonStyle = f"""
            QPushButton {{
                background-color: {self.buttonColor};
                border: {self.buttonBorderWidth}px solid {self.buttonBorderColor};
                border-radius: {self.radius}px;
                color: white;
                font-size: 20px;
                font-family: "Arial";
                font-weight: bold;
                margin: 0;
            }}
            QPushButton:hover {{ background-color: {self.hoverColor}; }}
            QPushButton:pressed {{ background-color: {self.pressedColor}; }}
        """

class PowerMenu(QWidget):
    def __init__(self):
        super().__init__()

        self.PMData = PowerMenuConfig()

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
        self.userPreferencesData = {}

        # Buttons object dict
        self.buttons = {}

        # File changed events
        self.powerMenuUserPropertiesWatcher = QFileSystemWatcher()
        if os.path.exists(self.PMData.userPreferencesPath):
            self.powerMenuUserPropertiesWatcher.addPath(self.PMData.userPreferencesPath)
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

        self.PMData.Updater()

        while self.containerLayoutForButtons.count():
            item = self.containerLayoutForButtons.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

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

            buttonStyle = self.PMData.buttonStyle + buttonPreference.get("overrideStyles", "")

            button.setStyleSheet(buttonStyle)
            button.setFixedSize(self.PMData.buttonSize, self.PMData.buttonSize)

            icon = buttonPreference.get("icon")

            if icon == "default":
                icon = configurator.theme.GetPath(f"app\\assets\\powermenuicons\\{buttonID}.svg")
            else:
                icon = configurator.theme.GetPath(f"{self.PMData.iconsDir}\\{buttonID}.svg")

            if os.path.exists(icon):
                iconSize = self.PMData.buttonSize // 2
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
        self.containerLayoutForButtons.setSpacing(self.PMData.spacing)
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

        self.PMData.containerWidthMax = max(containerRealWidth, self.PMData.containerWidth) + self.PMData.containerPaddings * 2 + self.PMData.borderWidth * 2
        self.PMData.containerHeightMax = max(containerRealHeight, self.PMData.containerHeight) + self.PMData.containerPaddings * 2 + self.PMData.borderWidth * 2

        self.PMData.containerWidthMax = self.PMData.containerWidthMax + self.PMData.containerMargins * 2 if self.PMData.doubleContainerBackground else self.PMData.containerWidthMax
        self.PMData.containerHeightMax = self.PMData.containerHeightMax + self.PMData.containerMargins * 2 if self.PMData.doubleContainerBackground else self.PMData.containerHeightMax

        if self.PMData.isFullscreen:
            self.setGeometry(self.PMData.screen)
        else:
            x = (self.PMData.screen.width() - self.PMData.containerWidthMax) // 2
            y = (self.PMData.screen.height() - self.PMData.containerHeightMax) // 2
            self.setGeometry(x, y, self.PMData.containerWidthMax, self.PMData.containerHeightMax)
            self.setStyleSheet(f"background-color: transparent;")

        self.container.setFixedSize(self.PMData.containerWidthMax, self.PMData.containerHeightMax)

        self.PMData.themeUpdatedState = True

        self.update()

    def LayoutPicker(self):
        configLayout = configurator.theme.Get(self.PMData.section, "menu_layout", fallback = "horizontal")

        if configLayout != self.PMData.menuLayout:
            # v/h orientation picker 2000
            if configLayout == "vertical":
                direction = QBoxLayout.Direction.TopToBottom
            elif configLayout == "horizontal":
                direction = QBoxLayout.Direction.LeftToRight
            else:
                return

            # set orientation to layouts
            self.PMData.menuLayout = configLayout
            self.layout.setDirection(direction)
            self.containerLayoutForButtons.setDirection(direction)

    def ColorPicker(self, updateToBG = False):
        if updateToBG:  # what the fuck.
            if self.PMData.isFullscreen:
                if self.PMData.useBGColor:
                    self.PMData.fullscreenColor = self.PMData.bgColor
                    self.PMData.doubleContainerColor = "#00000000"
                elif not self.PMData.useBGColor:
                    self.PMData.fullscreenColor = "#01000000"
                    self.PMData.doubleContainerColor = self.PMData.bgColor
            elif not self.PMData.isFullscreen:
                self.PMData.doubleContainerColor = self.ColorPicker()
                self.PMData.fullscreenColor = self.PMData.bgColor
            return

        if self.PMData.doubleContainerBackground is True:
            if self.PMData.doubleContainerBackgroundAccent == "container":
                return self.PMData.containerColor
            else:
                return self.PMData.bgColor
        else:
            return self.PMData.containerColor

    def LoadUserPreferences(self):
        MakeLog("[Log] [PowerMenu] [UserPreferences] | Changes detected. Reloading.")
        # Deleting buttons
        self.buttons.clear()

        # Opening PMData.json (user preferences)
        with open(self.PMData.userPreferencesPath, "r") as preferences:
            self.userPreferencesData = json.load(preferences)

        self.UpdateStyles("manual", ["ALL"])

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Blur
        if self.PMData.themeUpdatedState:
            if self.PMData.blurEnabled:
                MakeBlur(self.winId(), True, self.PMData.blurMode, self.PMData.fullscreenColor)
            else:
                MakeBlur(self.winId(), False)
            self.PMData.themeUpdatedState = False

        if self.PMData.isFullscreen and (not self.PMData.blurEnabled or self.PMData.blurMode != 1):
            painter.setBrush(QColor(self.PMData.fullscreenColor))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(self.rect())

        buttonLen = len(self.buttons)
        if buttonLen == 0:
            MakeLog("[Log] [PowerMenu] | Seems like list of buttons is empty.")
            return

        currentMargins = self.PMData.containerMargins * 2 if self.PMData.doubleContainerBackground else 0

        layoutWidth = self.PMData.containerWidthMax - self.PMData.borderWidth * 2 - self.PMData.containerPaddings * 2 - currentMargins
        layoutHeight = self.PMData.containerHeightMax - self.PMData.borderWidth * 2 - self.PMData.containerPaddings * 2 - currentMargins

        painter.setPen(Qt.PenStyle.NoPen)

        # Inner container w/h
        innerW = layoutWidth + self.PMData.containerPaddings * 2
        innerH = layoutHeight + self.PMData.containerPaddings * 2

        # Outer container w/h
        outerW = innerW + self.PMData.containerMargins * 2
        outerH = innerH + self.PMData.containerMargins * 2

        # border & background maker 3000
        outerColor = self.PMData.doubleContainerColor if (not self.PMData.blurEnabled or self.PMData.blurMode == 0) else "#01000000"
        painter.setBrush(QBrush(QColor(outerColor)))

        borderRect = QRectF(
            (self.width() - outerW) / 2, (self.height() - outerH) / 2, outerW, outerH
        ) if self.PMData.doubleContainerBackground else QRectF(
            (self.width() - innerW) / 2, (self.height() - innerH) / 2, innerW, innerH
        )

        if self.PMData.borderWidth > 0:
            pen = painter.pen()
            pen.setStyle(Qt.PenStyle.SolidLine)
            pen.setColor(QColor(self.PMData.borderColor))
            pen.setWidth(self.PMData.borderWidth)
            pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
            painter.setPen(pen)

            halfWidth = self.PMData.borderWidth / 2
            borderRect = borderRect.adjusted(-halfWidth, -halfWidth, halfWidth, halfWidth)
        else:
            painter.setPen(Qt.PenStyle.NoPen)

        painter.drawRoundedRect(borderRect, self.RadiusSelector("border"), self.RadiusSelector("border"))

        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(Qt.PenStyle.NoPen)

        # Inner "container"
        innerRect = QRectF((self.width() - innerW) / 2, (self.height() - innerH) / 2, innerW, innerH)
        painter.setBrush(QBrush(QColor(self.PMData.containerColor)))
        painter.drawRoundedRect(innerRect, self.RadiusSelector("inner"), self.RadiusSelector("inner"))

    def RadiusSelector(self, type):
        menuSize = self.PMData.containerHeightMax if self.PMData.menuLayout == "horizontal" else self.PMData.containerWidthMax
        if type == "inner":
            margin = self.PMData.containerMargins if self.PMData.doubleContainerBackground else 0
            return self.PMData.radius * ((menuSize - margin * 2 - self.PMData.borderWidth * 2) / self.PMData.buttonSize)
        if type == "border":
            return self.PMData.radius * ((menuSize - self.PMData.borderWidth) / self.PMData.buttonSize)

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
                MakeLog(f"[Log] [PowerMenu] [RunCommand] | CMD failed: {e}")

        # Programs
        elif type == "program":
            try:
                subprocess.Popen(action, shell=True)
                self.close()
            except Exception as e:
                MakeLog(f"[Log] [PowerMenu] [RunCommand] | Exec failed: {e}")
