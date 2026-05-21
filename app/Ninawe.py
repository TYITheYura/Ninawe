#                  NI   E
#                  N N  E
#                  N  A E i n a w e
#                  N   WE ---------
#               Version: Well Done v1.1
# And remember guys: Ninawe is not a windows explorer

import os
import subprocess
import ctypes
import sys

system32Path = "C:\\Windows\\System32"
if system32Path.lower() not in os.environ.get("PATH", "").lower():
    os.environ["PATH"] = system32Path + os.pathsep + os.environ.get("PATH", "")

ctypes.windll.kernel32.SetConsoleTitleW("Ninawe Is Not A Windows Explorer - Shell Debugger")

from PyQt6.QtWidgets import QApplication

app = QApplication(sys.argv)

from core.config import config
from core.managers import HotkeyManager
from ui.desktop import DesktopWindow
from ui.taskbar import Taskbar
from ui.powermenu import PowerMenu
from ui.launchpad import Launchpad
from ui.settings import SettingsWindow
from core.utils import WorkAreaSetter, SetShellWindow, MakeLog
from core.workers import SystemWindowManager, ExplorerGlobalWatcher

#
#   Take me back, back home
#   Đường về cũng chẳng có xa
#   Đêm khuya rồi sao không có ai
#   Đưa em đi về nhà?
#

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
        self.settings = SettingsWindow()

        # Set desktop as a shell window
        SetShellWindow(self.desktop.winId())

    def Start(self):

        MakeLog("[Log] [Starter] [0xCAFEBABE]", "We are moving into space...")

        self.desktop.show()
        self.taskbar.show()

        sys.exit(app.exec())


if __name__ == "__main__":
    shell = NinaweShell()
    shell.Start()
