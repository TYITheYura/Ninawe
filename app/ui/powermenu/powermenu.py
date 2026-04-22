from PyQt6.QtWidgets import QWidget, QBoxLayout, QPushButton, QApplication, QFrame
from PyQt6.QtCore import Qt, QSize, QFileSystemWatcher, QRectF
from PyQt6.QtGui import QColor, QIcon, QPainter, QBrush
from core.config import config as configurator
from core.utils import MakeBlur, MakeLog, InternalWindowFader
from .config import PMConfig
import subprocess
import json
import os

class PowerMenu(QWidget):
    def __init__(self):
        super().__init__()

        PMConfig.configUpdated.connect(self.UpdateStyles)

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
        if os.path.exists(PMConfig.userPreferencesPath):
            self.powerMenuUserPropertiesWatcher.addPath(PMConfig.userPreferencesPath)
            self.powerMenuUserPropertiesWatcher.fileChanged.connect(self.LoadUserPreferences)

        # Window fader
        self.internalWindowFader = InternalWindowFader(self)

        self.LoadUserPreferences()

    def UpdateStyles(self, source = None, changedSections = None):
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

            buttonStyle = PMConfig.buttonStyle + buttonPreference.get("overrideStyles", "")

            button.setStyleSheet(buttonStyle)
            button.setFixedSize(PMConfig.buttonSize, PMConfig.buttonSize)

            icon = buttonPreference.get("icon")

            if icon == "default":
                icon = configurator.theme.GetPath(f"app\\assets\\powermenuicons\\{buttonID}.svg")
            else:
                icon = configurator.theme.GetPath(f"{PMConfig.iconsDir}\\{buttonID}.svg")

            if os.path.exists(icon):
                iconSize = PMConfig.buttonSize // 2
                button.setIcon(QIcon(icon))
                button.setIconSize(QSize(iconSize, iconSize))
            else:
                button.setText(buttonID[0].upper())

            self.containerLayoutForButtons.addWidget(button)
            self.buttons[buttonID] = button

        # Container style
        self.container.setStyleSheet("""
            QFrame#PowerMenuContainer {{
                background-color: transparent;
            }}
        """)

        self.containerLayoutForButtons.setContentsMargins(0, 0, 0, 0)
        self.containerLayoutForButtons.setSpacing(PMConfig.spacing)
        self.containerLayoutForButtons.setAlignment(Qt.AlignmentFlag.AlignCenter)

        QApplication.processEvents()

        # Reset the sizes that were previously in setFixedSize
        self.container.setMinimumSize(0, 0)
        self.container.setMaximumSize(16777215, 16777215)

        # Reseting old sizes & correction of the width if the container size is larger than the size specified in the config
        self.container.resize(1, 1)
        self.container.adjustSize()
        self.adjustSize()
        # woahhh, never do this again please

        containerRealWidth = self.container.width()
        containerRealHeight = self.container.height()

        PMConfig.containerWidthMax = max(containerRealWidth, PMConfig.containerWidth) + PMConfig.containerPaddings * 2 + PMConfig.borderWidth * 2
        PMConfig.containerHeightMax = max(containerRealHeight, PMConfig.containerHeight) + PMConfig.containerPaddings * 2 + PMConfig.borderWidth * 2

        PMConfig.containerWidthMax = PMConfig.containerWidthMax + PMConfig.containerMargins * 2 if PMConfig.doubleContainerBackground else PMConfig.containerWidthMax
        PMConfig.containerHeightMax = PMConfig.containerHeightMax + PMConfig.containerMargins * 2 if PMConfig.doubleContainerBackground else PMConfig.containerHeightMax

        if PMConfig.isFullscreen:
            self.setGeometry(PMConfig.screen)
        else:
            x = (PMConfig.screen.width() - PMConfig.containerWidthMax) // 2
            y = (PMConfig.screen.height() - PMConfig.containerHeightMax) // 2
            self.setGeometry(x, y, PMConfig.containerWidthMax, PMConfig.containerHeightMax)
            self.setStyleSheet("background-color: transparent;")

        self.container.setFixedSize(PMConfig.containerWidthMax, PMConfig.containerHeightMax)

        self.update()

    def LayoutPicker(self):
        configLayout = configurator.theme.Get(PMConfig.section, "menu_layout", fallback = "horizontal")

        if configLayout != PMConfig.menuLayout:
            # v/h orientation picker 2000
            if configLayout == "vertical":
                direction = QBoxLayout.Direction.TopToBottom
            elif configLayout == "horizontal":
                direction = QBoxLayout.Direction.LeftToRight
            else:
                return

            # set orientation to layouts
            PMConfig.menuLayout = configLayout
            self.layout.setDirection(direction)
            self.containerLayoutForButtons.setDirection(direction)

    def ColorPicker(self, updateToBG = False):
        if updateToBG:  # what the fuck.
            if PMConfig.isFullscreen:
                if PMConfig.useBGColor:
                    PMConfig.fullscreenColor = PMConfig.bgColor
                    PMConfig.doubleContainerColor = "#00000000"
                elif not PMConfig.useBGColor:
                    PMConfig.fullscreenColor = "#01000000"
                    PMConfig.doubleContainerColor = PMConfig.bgColor
            elif not PMConfig.isFullscreen:
                PMConfig.doubleContainerColor = self.ColorPicker()
                PMConfig.fullscreenColor = PMConfig.bgColor
            return

        if PMConfig.doubleContainerBackground is True:
            if PMConfig.doubleContainerBackgroundAccent == "container":
                return PMConfig.containerColor
            else:
                return PMConfig.bgColor
        else:
            return PMConfig.containerColor

    def LoadUserPreferences(self):
        # Deleting buttons (legacy actually)
        self.buttons.clear()

        # Opening PMData.json (user preferences)
        with open(PMConfig.userPreferencesPath, "r") as preferences:
            self.userPreferencesData = json.load(preferences)

        self.UpdateStyles("manual", ["ALL"])

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if PMConfig.isFullscreen and (not PMConfig.blurEnabled or PMConfig.blurMode != 1):
            painter.setBrush(QColor(PMConfig.fullscreenColor))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(self.rect())

        buttonLen = len(self.buttons)
        if buttonLen == 0:
            MakeLog("[Log] [PowerMenu] | Seems like list of buttons is empty.")
            return

        currentMargins = PMConfig.containerMargins * 2 if PMConfig.doubleContainerBackground else 0

        layoutWidth = PMConfig.containerWidthMax - PMConfig.borderWidth * 2 - PMConfig.containerPaddings * 2 - currentMargins
        layoutHeight = PMConfig.containerHeightMax - PMConfig.borderWidth * 2 - PMConfig.containerPaddings * 2 - currentMargins

        painter.setPen(Qt.PenStyle.NoPen)

        # Inner container w/h
        innerW = layoutWidth + PMConfig.containerPaddings * 2
        innerH = layoutHeight + PMConfig.containerPaddings * 2

        # Outer container w/h
        outerW = innerW + PMConfig.containerMargins * 2
        outerH = innerH + PMConfig.containerMargins * 2

        # border & background maker 3000
        outerColor = PMConfig.doubleContainerColor if (not PMConfig.blurEnabled or PMConfig.blurMode == 0) else "#01000000"
        painter.setBrush(QBrush(QColor(outerColor)))

        borderRect = QRectF(
            (self.width() - outerW) / 2, (self.height() - outerH) / 2, outerW, outerH
        ) if PMConfig.doubleContainerBackground else QRectF(
            (self.width() - innerW) / 2, (self.height() - innerH) / 2, innerW, innerH
        )

        if PMConfig.borderWidth > 0:
            pen = painter.pen()
            pen.setStyle(Qt.PenStyle.SolidLine)
            pen.setColor(QColor(PMConfig.borderColor))
            pen.setWidth(PMConfig.borderWidth)
            pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
            painter.setPen(pen)

            halfWidth = PMConfig.borderWidth / 2
            borderRect = borderRect.adjusted(-halfWidth, -halfWidth, halfWidth, halfWidth)
        else:
            painter.setPen(Qt.PenStyle.NoPen)

        painter.drawRoundedRect(borderRect, self.RadiusSelector("border"), self.RadiusSelector("border"))

        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(Qt.PenStyle.NoPen)

        # Inner "container"
        innerRect = QRectF((self.width() - innerW) / 2, (self.height() - innerH) / 2, innerW, innerH)
        painter.setBrush(QBrush(QColor(PMConfig.containerColor)))
        painter.drawRoundedRect(innerRect, self.RadiusSelector("inner"), self.RadiusSelector("inner"))

    def RadiusSelector(self, type):
        menuSize = PMConfig.containerHeightMax if PMConfig.menuLayout == "horizontal" else PMConfig.containerWidthMax
        if type == "inner":
            margin = PMConfig.containerMargins if PMConfig.doubleContainerBackground else 0
            return PMConfig.radius * ((menuSize - margin * 2 - PMConfig.borderWidth * 2) / PMConfig.buttonSize)
        if type == "border":
            return PMConfig.radius * ((menuSize - PMConfig.borderWidth) / PMConfig.buttonSize)

    def showEvent(self, event):
        # Draw blur
        if PMConfig.blurEnabled:
            MakeBlur(self.winId(), True, PMConfig.blurMode, PMConfig.fullscreenColor)
        else:
            MakeBlur(self.winId(), False)

        # Draw powermenu
        self.internalWindowFader.FadeIn()
        self.activateWindow()
        self.setFocus()

    # Closing with ESC
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.internalWindowFader.FadeOut(self.close)

    def mousePressEvent(self, event):
        # Working only when background not transperent sadly.
        if self.childAt(event.pos()) is None:
            self.internalWindowFader.FadeOut(self.close)

    def RunCommand(self, type, action):
        # Build-in commands
        if type == "integrated":
            if action == "close":
                pass

        # Console commands
        elif type == "console":
            try:
                os.system(action)
            except Exception as e:
                MakeLog(f"[Log] [PowerMenu] [RunCommand] | CMD failed: {e}")

        # Programs
        elif type == "program":
            try:
                subprocess.Popen(action, shell=True)
            except Exception as e:
                MakeLog(f"[Log] [PowerMenu] [RunCommand] | Exec failed: {e}")

        self.internalWindowFader.FadeOut(self.close)