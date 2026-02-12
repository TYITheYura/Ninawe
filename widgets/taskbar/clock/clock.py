from PyQt6.QtWidgets import QLabel, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QTime, QTimer
from PyQt6.QtGui import QColor
from core.config import config as selectedThemeConfig
from core.utils import LoadFont, MakeBlur
from core.config import ConfigWrapper
import os

class Clock(QLabel):
	def __init__(self, parent = None):
		super().__init__(parent)
		self.setObjectName("ClockWidget")
		self.defaultSection = "Taskbar.Clock"
		self.clockConfig = ConfigWrapper()
		
		# Panel w/h info
		self.panelWidth = parent.panelWidth
		self.panelHeight = parent.panelHeight

		# Fonts
		self.fontFamily = self.fontSize = self.fontColor = self.fontShadow = None
		# Props
		self.clockWidth = self.clockPosition = self.clockLeftMargin = self.clockRightMargin = self.clockAlign = None
		# Used config
		self.selectedConfig = None
		# Config path
		self.widgetPath = os.path.dirname(os.path.abspath(__file__))
		self.configPath = os.path.join(self.widgetPath, "config.ini")

		# Align clock
		self.setAlignment(Qt.AlignmentFlag.AlignCenter)
		
		# Connecting to config updating state
		selectedThemeConfig.themeUpdated.connect(self.Updater)
		
		#  [> Clock timer
		self.timer = QTimer(self)
		self.timer.timeout.connect(self.UpdateTime)
		self.timer.start(1000)

	def Updater(self):
		self.clockConfig.parser.read(self.configPath)

		# Config switcher
		if selectedThemeConfig.theme.GetSectionStatus(self.defaultSection) == True: # themeconfig.ini
			self.selectedConfig = selectedThemeConfig.theme

		else: # build-in widget config
			self.selectedConfig = self.clockConfig
		
		# forced clock text update
		self.UpdateTime()

		# Enable/disable clock switch
		if self.selectedConfig.GetBool(self.defaultSection, "visible", fallback = True):
			self.show()
			if not self.timer.isActive():
				self.timer.start(1000)
		else:
			self.hide()
			self.timer.stop()
			return

		# font data
		self.fontFamily = self.selectedConfig.Get(self.defaultSection, "font_family", fallback = selectedThemeConfig.theme.globals.fontFamily)
		self.fontFamily = LoadFont(self.fontFamily, self.widgetPath)
		self.fontSize = self.selectedConfig.GetInt(self.defaultSection, "font_size", fallback = selectedThemeConfig.theme.globals.fontSize)
		self.fontColor = self.selectedConfig.Get(self.defaultSection, "font_color", fallback = selectedThemeConfig.theme.globals.fontColor)
		self.fontShadow = self.selectedConfig.Get(self.defaultSection, "font_shadow", fallback = selectedThemeConfig.theme.globals.fontShadow)
		
		# clock data
		self.clockWidth = self.selectedConfig.GetInt(self.defaultSection, "width", fallback = 50)
		self.clockPosition = self.selectedConfig.GetInt(self.defaultSection, "position", fallback = 50)
		self.clockLeftMargin = self.selectedConfig.GetInt(self.defaultSection, "margin_left", fallback = 10)
		self.clockRightMargin = self.selectedConfig.GetInt(self.defaultSection, "margin_right", fallback = 10)
		self.clockAlign = self.selectedConfig.GetInt(self.defaultSection, "align", fallback = 50)

		self.Init()

	def UpdateTime(self):
		currentTime = QTime.currentTime()
		timeFormat = self.selectedConfig.Get(self.defaultSection, "time_format", fallback = "HH:mm")
		self.setText(currentTime.toString(timeFormat))

	def Init(self):
		# If values in taskbar constructor is not updated (for first init)
		if self.panelWidth == None or self.panelHeight == None:
			return

		self.setStyleSheet(f"""
			color: {self.fontColor};
			font-family: '{self.fontFamily}';
			font-size: {self.fontSize}pt;
			background-color: transparent;
		""")

		shadowPadding = 0
		if self.fontShadow:
			shadowPadding = 4
			shadow = QGraphicsDropShadowEffect(self)
			shadow.setBlurRadius(5)
			shadow.setXOffset(1)
			shadow.setYOffset(1)
			shadow.setColor(QColor(0, 0, 0, 150))
			self.setGraphicsEffect(shadow)
		else:
			self.setGraphicsEffect(None)

		#  [> Clock position
		clockX = round(self.panelWidth * (self.clockPosition / 100) - (self.clockWidth * (self.clockAlign / 100)) + self.clockLeftMargin - self.clockRightMargin)

		self.setGeometry(clockX, shadowPadding, self.clockWidth, self.panelHeight - (shadowPadding * 2))