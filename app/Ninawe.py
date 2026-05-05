#                  NI   E
#                  N N  E
#                  N  A E i n a w e
#                  N   WE ---------
#              Version: Medium Well v2.0
# And remember guys: Ninawe is not a windows explorer

import os
import subprocess
import ctypes
import sys

system32Path = "C:\\Windows\\System32"
if system32Path.lower() not in os.environ.get("PATH", "").lower():
    os.environ["PATH"] = system32Path + os.pathsep + os.environ.get("PATH", "")

os.system("mode con cols=128 lines=30")
ctypes.windll.kernel32.SetConsoleTitleW("Ninawe Is Not A Windows Explorer - Shell")

from PyQt6.QtWidgets import QApplication

app = QApplication(sys.argv)

from core.config import config
from core.managers import HotkeyManager
from ui.desktop import DesktopWindow
from ui.taskbar import Taskbar
from ui.powermenu import PowerMenu
from ui.launchpad import Launchpad
from core.utils import SetGlobalAnimations, WorkAreaSetter, SetShellWindow, MakeLog
from core.workers import SystemWindowManager, ExplorerGlobalWatcher

class NinaweShell:
    def __init__(self):

        MakeLog('''
                                                                                             ---:::+++#####+++:::---
                      ::: :: :  ::::    ::: ::::::::::: ::::    :::     :::     :::       ::: ::::::::::
                     :+: :: :  :+:+:   :+:     :+:     :+:+:   :+:   :+: :+:   :+:       :+: :+:
                    :+: :+ :  :+:+:+  +:+     +:+     :+:+:+  +:+  +:+   +:+  +:+       +:+ +:+
                   +#+ #+ +  +#+ +:+ +#+     +#+     +#+ +:+ +#+ +#++:++#++: +#+  +:+  +#+ +#++:++#
                  +#+ +# +  +#+  +#+#+#     +#+     +#+  +#+#+# +#+     +#+ +#+ +#+#+ +#+ +#+
                 #+# ## #  #+#   #+#+#     #+#     #+#   #+#+# #+#     #+#  #+#+# #+#+#  #+#
                ### ## #  ###    #### ########### ###    #### ###     ###   ###   ###   ##########
    ---:::+++#####+++:::---
''')

        os.system("taskkill /f /im explorer.exe")

        # Admin pipe for commands, that working only with admin previlegies
        adminPipeWorkerPath = os.path.abspath(os.path.join(os.path.dirname(__file__), "core", "workers", "adminpipeworker.py"))
        subprocess.Popen([sys.executable, adminPipeWorkerPath])

        # Recalculating the available area on the screen
        self.workArea = WorkAreaSetter()

        # Enabling minimize/maximize animations
        SetGlobalAnimations(True)

        # Window hook
        app.windowManager = SystemWindowManager()
        app.windowManager.start()

        # Explorer watcher
        self.globalWatcher = ExplorerGlobalWatcher()

        # What a great manager, I'm proud of him ngl
        self.hotkeyManager = HotkeyManager()

        # Links to the windows
        self.desktop = DesktopWindow()
        self.taskbar = Taskbar()
        self.powerMenu = PowerMenu()
        self.launchpad = Launchpad()

        # Set desktop as a shell window
        SetShellWindow(self.desktop.winId())

    def Start(self):

        MakeLog("[Log] [Starter]", "We are moving into space...")

        self.desktop.show()
        self.taskbar.show()

        sys.exit(app.exec())


if __name__ == "__main__":
    shell = NinaweShell()
    shell.Start()
