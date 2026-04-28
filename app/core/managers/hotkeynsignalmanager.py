from PyQt6.QtCore import QObject, pyqtSignal
import keyboard
from core.utils import MakeLog

class HotkeyManager:
    def __init__(self):
        # {"key_name": {"pressed": False, "combo": False, "callback": func}}
        self.soloKeysState = {}

        self.RegisterHotkeys()

    def AddCombo(self, hotkeyString, callback):
        keyboard.add_hotkey(hotkeyString, callback)
        MakeLog("[Log] [Hotkeys]", f"Registered Combo: {hotkeyString}")

    def AddSolo(self, keyNames, callback):
        if isinstance(keyNames, str):
            keyNames = [keyNames]

        for key in keyNames:
            self.soloKeysState[key] = {
                "pressed": False,
                "combo": False,
                "callback": callback
            }
        MakeLog("[Log] [Hotkeys]", f"Registered Solo key: {keyNames}")

    def RegisterHotkeys(self):
        MakeLog("[Log] [Hotkeys]", "Initializing hotkeys...")

        self.AddSolo(["windows", "left windows", "right windows"], shellSignals.toggleLaunchpad.emit)
        self.AddCombo("win+q", shellSignals.togglePowerMenu.emit)

        keyboard.hook(self.UniversalHook)

    def UniversalHook(self, event):
        isSoloKey = event.name in self.soloKeysState

        if event.event_type == keyboard.KEY_DOWN:
            if isSoloKey:
                self.soloKeysState[event.name]["pressed"] = True
                self.soloKeysState[event.name]["combo"] = False
            else:
                for key, state in self.soloKeysState.items():
                    if state["pressed"]:
                        state["combo"] = True

        elif event.event_type == keyboard.KEY_UP:
            if isSoloKey:
                state = self.soloKeysState[event.name]

                if state["pressed"] and not state["combo"]:
                    state["callback"]()

                state["pressed"] = False


class UISignalManager(QObject):
    toggleLaunchpad = pyqtSignal()
    togglePowerMenu = pyqtSignal()


shellSignals = UISignalManager()
