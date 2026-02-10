from PyQt6.QtWidgets import QWidget, QApplication, QLabel, QHBoxLayout, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QRect, QTime, QTimer, QRectF
from PyQt6.QtGui import QPainter, QColor, QBrush, QFont
from core.config import config as themeConfig
from core.utils import LoadFont, MakeBlur

class Taskbar(QWidget):
    def __init__(self):
        super().__init__()
        # =[> Connecting to theme config update event
        themeConfig.themeUpdated.connect(self.UpdateStyles)
        self.panelBackgroundColor = self.enableBlur = self.radius = self.borderColor = self.borderWidth = self.enableBlur = self.blurMode = None
        self.themeUpdatedState = True
        self.UpdateStyles(True)
        
        # =[> Window flags
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |  # No borders
            Qt.WindowType.Tool |                 # No alt+tab
            Qt.WindowType.WindowStaysOnTopHint   # always on top
        )
        #  [> Transperent bg attribute
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # =[> Clock
        self.clockLabel = QLabel(self)
        self.clockLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        #  [> Clock timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.UpdateTime)
        self.timer.start(1000)

        # =[> First init
        self.UpdateTime()
        self.init_ui()

    def UpdateStyles(self, configOnly = False):
        # =[> Data from config
        self.panelBackgroundColor = themeConfig.theme.Get("Taskbar", "argb_color", fallback = "#000000")
        self.enableBlur = themeConfig.theme.GetBool("Taskbar", "blur_enabled", fallback = False)
        self.radius = 0 if self.enableBlur == True else themeConfig.theme.GetInt("Taskbar", "border_radius_px", fallback = 10)
        self.borderColor = themeConfig.theme.Get("Taskbar", "argb_border_color", fallback="#FFFFFF33")
        self.borderWidth = themeConfig.theme.GetInt("Taskbar", "border_width_px", fallback = 1)
        if self.enableBlur:
            self.blurMode = themeConfig.theme.GetInt("Taskbar", "blur_mode", fallback = 4)

        if configOnly:
            return

        self.themeUpdatedState = True
        self.init_ui()
        self.update()

    def UpdateTime(self):
        currentTime = QTime.currentTime()
        timeFormat = themeConfig.theme.Get("Taskbar.Clock", "time_format", fallback = "HH:mm")
        self.clockLabel.setText(currentTime.toString(timeFormat))

    def init_ui(self):
        screen = QApplication.primaryScreen().geometry()
        sw, sh = screen.width(), screen.height()

        # =[> Panel width
        rawPanelWidthData = themeConfig.theme.Get("Taskbar", "width", fallback = 90)
        panelWidth = 0
        try:
            if "%" in str(rawPanelWidthData):
                value = int(str(rawPanelWidthData).replace("%", ""))
                panelWidth = round(sw * (value / 100))
            else:
                panelWidth = int(str(rawPanelWidthData).replace("px", ""))
        except ValueError:
            panelWidth = sw

        # =[> Panel height
        rawPanelHeightData = themeConfig.theme.Get("Taskbar", "height", fallback = 30)
        panelHeight = 0
        try:
            if "%" in str(rawPanelHeightData):
                value = int(str(rawPanelHeightData).replace("%", ""))
                panelHeight = round(sh * (value / 100))
            else:
                panelHeight = int(str(rawPanelHeightData).replace("px", ""))
        except ValueError:
            panelHeight = round(sh * (2 / 100))
        
        # =[> Anchors getting
        anchorX = themeConfig.theme.GetInt("Taskbar", "anchor_x", fallback = 50)
        anchorY = themeConfig.theme.GetInt("Taskbar", "anchor_y", fallback = 100)

        # =[> Panel position
        #  [> X
        rawPanelXPositionData = themeConfig.theme.GetInt("Taskbar", "position_x", fallback = 98)
        panelXPosition = int(sw * (rawPanelXPositionData / 100))

        #  [> Y
        rawPanelYPositionData = themeConfig.theme.GetInt("Taskbar", "position_y", fallback = 2)
        panelYPosition = int(sh * (rawPanelYPositionData / 100))

        # =[> Panel offset
        #  [> X
        offsetX = int(panelWidth * (anchorX / 100))
        offsetY = int(panelHeight * (anchorY / 100))

        panelX = panelXPosition - offsetX
        panelY = panelYPosition - offsetY

        self.setGeometry(panelX, panelY, panelWidth, panelHeight)

        if themeConfig.theme.GetBool("Taskbar.Clock", "visible", fallback = True):
            self.clockLabel.show()
            if not self.timer.isActive():
                self.timer.start(1000)
                self.UpdateTime()
        
            # =[> Clock styles
            fontFamily = themeConfig.theme.Get("Taskbar.Clock", "font_family", fallback = themeConfig.theme.globals.fontFamily)
            fontFamily = LoadFont(fontFamily)
            fontSize = themeConfig.theme.GetInt("Taskbar.Clock", "font_size", fallback = themeConfig.theme.globals.fontSize)
            fontColor = themeConfig.theme.Get("Taskbar.Clock", "font_color", fallback = themeConfig.theme.globals.fontColor)
            fontShadow = themeConfig.theme.Get("Taskbar.Clock", "font_shadow", fallback = themeConfig.theme.globals.fontShadow)

            self.clockLabel.setStyleSheet(f"""
                color: {fontColor};
                font-family: '{fontFamily}';
                font-size: {fontSize}pt;
                background-color: transparent;
            """)

            shadowPadding = 0
            if fontShadow:
                shadowPadding = 4
                shadow = QGraphicsDropShadowEffect(self)
                shadow.setBlurRadius(5)
                shadow.setXOffset(1)
                shadow.setYOffset(1)
                shadow.setColor(QColor(0, 0, 0, 150))
                self.clockLabel.setGraphicsEffect(shadow)
            else:
                self.clockLabel.setGraphicsEffect(None)

            #  [> Clock position
            clockWidth = themeConfig.theme.GetInt("Taskbar.Clock", "width", fallback = 50)
            clockPosition = themeConfig.theme.GetInt("Taskbar.Clock", "position", fallback = 50)
            clockLeftMargin = themeConfig.theme.GetInt("Taskbar.Clock", "margin_left", fallback = 10)
            clockRightMargin = themeConfig.theme.GetInt("Taskbar.Clock", "margin_right", fallback = 10)
            clockAlign = themeConfig.theme.GetInt("Taskbar.Clock", "align", fallback = 50)
            clockX = round(panelWidth * (clockPosition / 100) - (clockWidth * (clockAlign / 100)) + clockLeftMargin - clockRightMargin)

            self.clockLabel.setGeometry(clockX, shadowPadding, clockWidth, panelHeight - (shadowPadding * 2))
        else:
            self.clockLabel.hide()
            self.timer.stop() 

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing) # Aliasing btw
        
        # Border maker 2000
        if self.borderWidth > 0:
            pen = painter.pen()
            pen.setColor(QColor(self.borderColor))
            pen.setWidth(self.borderWidth)
            pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin) 
            painter.setPen(pen)

            halfWidth = self.borderWidth / 2
            borderPen = QRectF(self.rect()).adjusted(halfWidth, halfWidth, -halfWidth, -halfWidth)
        else:
            painter.setPen(Qt.PenStyle.NoPen)

        if self.themeUpdatedState:
            # =[> Panel blur
            #  [> not working with border_radius sadly :(
            MakeBlur(self.winId(), self.enableBlur, self.blurMode, self.panelBackgroundColor)
            self.themeUpdatedState = False

        if self.enableBlur:
            self.panelBackgroundColor = QColor(0, 0, 0, 0)
        else:
            MakeBlur(self.winId(), self.enableBlur)

        # Drawing background
        painter.setBrush(QBrush(QColor(self.panelBackgroundColor)))
        
        # Drawing border
        painter.drawRoundedRect(borderPen, self.radius, self.radius)