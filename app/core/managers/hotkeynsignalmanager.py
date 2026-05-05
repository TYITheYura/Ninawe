from PyQt6.QtCore import QObject, pyqtSignal, QAbstractNativeEventFilter, QCoreApplication
from core.utils import MakeLog, MOD_NOREPEAT
import keyboard
import subprocess
import ctypes
import ctypes.wintypes
import win32con
import os

#
#   Honestly, everything in this file is something I absolutely love, and I'm proud of this part of the program.
#   It's wonderful and probably has the fewest bugs.
#

class NativeComboFilter(QAbstractNativeEventFilter):
    #
    #   System event filter. Filters hotkeys from all system events,
    #   and if any of them are defined in the dictionary, calls a function from nativeCombos.
    #
    def __init__(self, manager):
        super().__init__()
        self.manager = manager

    def nativeEventFilter(self, eventType, message):
        try:
            msg = ctypes.wintypes.MSG.from_address(int(message))

            if msg.message == win32con.WM_HOTKEY:
                hotkeyID = msg.wParam
                if hotkeyID in self.manager.nativeCombos:
                    self.manager.nativeCombos[hotkeyID]()

                    return True, 0
        except Exception as e:
            MakeLog("[Error] [Hotkeys]", f"Native event error: {e}")

        return False, 0

class HotkeyManager:
    #
    #   The basic hotkey manager. Does everything it can and doesn't do what it can't :)
    #   Collects, records, monitors, sets and executes hotkeys.
    #
    def __init__(self):
        from core.config import ConfigUpdateChecker
        from core.utils import RunDialog, DesktopToggler

        self.configChecker = ConfigUpdateChecker(["Hotkeys.Custom", "Hotkeys.Ninawe"])
        self.configChecker.configUpdated.connect(self.Reload)
        self.desktopToggler = DesktopToggler()

        self.soloKeysState = {}
        self.nativeCombos = {}
        self.currentHotkeyId = 1

        self.nativeFilter = NativeComboFilter(self)
        QCoreApplication.instance().installNativeEventFilter(self.nativeFilter)

        self.internalCommands = {
            "launcher_toggle": shellSignals.toggleLaunchpad.emit,
            "powermenu_toggle": shellSignals.togglePowerMenu.emit,
            "toggle_desktop": self.desktopToggler.ToggleDesktop,
            "run": RunDialog
        }

        self.Reload()

    def Clear(self):
        # Solo clear
        keyboard.unhook_all()
        self.soloKeysState.clear()

        # Combo clear
        for hotkeyID in self.nativeCombos.keys():
            ctypes.windll.user32.UnregisterHotKey(0, hotkeyID)

        self.nativeCombos.clear()
        self.currentHotkeyId = 1

        MakeLog("[Log] [Hotkeys]", "Cleared all hotkeys.")

    def Reload(self):
        from core.config import config as configurator

        self.Clear()
        MakeLog("[Log] [Hotkeys]", "Loading hotkeys from config...")

        # Build-in shell
        for cmdName, callback in self.internalCommands.items():
            hotkeyStr = configurator.app.Get("Hotkeys.Ninawe", cmdName, fallback = "")
            if hotkeyStr:
                self.BindKey(hotkeyStr, callback)

        # Customs
        customs = configurator.app.GetList("Hotkeys.Custom", "customs", fallback = [])
        for line in customs:
            if "," in line:
                hotkeyStr, command = line.split(",", 1)

                callback = self.CreateCustomRunner(command.strip())
                self.BindKey(hotkeyStr.strip(), callback)

        keyboard.hook(self.UniversalHook)

    def CreateCustomRunner(self, command):
        #
        #   Creates and returns a function for custom hotkeys.
        #
        def Runner():
            try:
                expandedCMD = os.path.expandvars(command)

                ctypes.windll.user32.AllowSetForegroundWindow(-1)

                subprocess.Popen(
                    expandedCMD,
                    shell = False,
                    creationflags = win32con.CREATE_NEW_CONSOLE
                )

                MakeLog("[Log] [Hotkeys]", f"Executed custom: {command}")
            except Exception as e:
                MakeLog("[Log] [Hotkeys]", f"Failed to run '{command}': {e}")
        return Runner

    def BindKey(self, hotkeyStr, callback):
        hotkeyStr = hotkeyStr.lower().strip()

        # Combos
        if "+" in hotkeyStr:
            self.AddCombo(hotkeyStr, callback)
        # Solos
        else:
            keys = [hotkeyStr]
            if hotkeyStr == "win":
                keys = ["windows", "left windows", "right windows"]
            elif hotkeyStr == "alt":
                keys = ["alt", "left alt", "right alt"]

            self.AddSolo(keys, callback)

    def AddCombo(self, hotkeyString, callback):
        mods = 0
        virtualKey = 0
        parts = hotkeyString.lower().replace(' ', '').split('+')

        for p in parts[:-1]:
            if p in ('win', 'windows'):
                mods |= win32con.MOD_WIN
            elif p in ('ctrl', 'control'):
                mods |= win32con.MOD_CONTROL
            elif p in ('alt',):
                mods |= win32con.MOD_ALT
            elif p in ('shift',):
                mods |= win32con.MOD_SHIFT

        key = parts[-1]

        virtualKeysMap = {
            'enter': win32con.VK_RETURN, 'space': win32con.VK_SPACE,
            'tab': win32con.VK_TAB, 'esc': win32con.VK_ESCAPE,
            'up': win32con.VK_UP, 'down': win32con.VK_DOWN,
            'left': win32con.VK_LEFT, 'right': win32con.VK_RIGHT
        }

        if key in virtualKeysMap:
            virtualKey = virtualKeysMap[key]
        elif len(key) == 1:
            virtualKey = ord(key.upper())

        success = ctypes.windll.user32.RegisterHotKey(0, self.currentHotkeyId, mods | MOD_NOREPEAT, virtualKey)

        if success:
            self.nativeCombos[self.currentHotkeyId] = callback
            MakeLog("[Log] [Hotkeys]", f"Registered native combo: {hotkeyString} (ID: {self.currentHotkeyId})")
            self.currentHotkeyId += 1
        else:
            MakeLog("[Log] [Hotkeys]", f"Failed to register native Combo: {hotkeyString}")

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
    toggleRunDialog = pyqtSignal()


shellSignals = UISignalManager()
