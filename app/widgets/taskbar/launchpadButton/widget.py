from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt
from core.managers import shellSignals
from .config import WConfig
from ui.taskbar import TBConfig

class Widget(QLabel):
	def __init__(self, parent = None):
		super().__init__(parent)
		self.setObjectName("launchpadButtonWidget")
		self.defaultSection = "Taskbar.LaunchpadButton"

		WConfig.configUpdated.connect(self.UpdateStyles)

		self.setPixmap(WConfig.pixNormal)
		self.setScaledContents(True)

		self.setAlignment(Qt.AlignmentFlag.AlignCenter)

	def UpdateStyles(self, source = None, changedSections = None):
		if WConfig.visibility:
			self.show()
		else:
			self.hide()
			return

		self.setStyleSheet("background-color: transparent;")

		size = TBConfig.panelHeight - (WConfig.padding * 2)
		self.setFixedSize(size, size)

		positionX = round(WConfig.position - (self.width() * (WConfig.align / 100)))

		self.setGeometry(positionX, WConfig.padding, size, size)

	def enterEvent(self, event):
		self.setPixmap(WConfig.pixHover)
		super().enterEvent(event)

	def leaveEvent(self, event):
		self.setPixmap(WConfig.pixNormal)
		super().leaveEvent(event)

	def mousePressEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton:
			self.setPixmap(WConfig.pixPressed)
		super().mousePressEvent(event)

	def mouseReleaseEvent(self, event):
		if event.button() == Qt.MouseButton.LeftButton:
			self.setPixmap(WConfig.pixHover)
			shellSignals.toggleLaunchpad.emit()
		super().mouseReleaseEvent(event)
