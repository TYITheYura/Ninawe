# core/managers/hotkeys.py
from PyQt6.QtCore import QObject, pyqtSignal
import keyboard
from core.utils import MakeLog

class HotkeyManager:
    def __init__(self):
        self.RegisterHotkeys()

    def RegisterHotkeys(self):
        MakeLog("[Log] [Hotkeys]", "Registering global hotkeys...")

        # Launchpad
        keyboard.add_hotkey('f10', shellSignals.toggleLaunchpad.emit)

class UISignalManager(QObject):
    toggleLaunchpad = pyqtSignal()
    togglePowerMenu = pyqtSignal()


shellSignals = UISignalManager()
