#                  NI   E
#                  N N  E
#                  N  A E i n a w e
#                  N   WE ---------
#               Version: Blue Rare 0.4
# And remember guys: Ninawe is not a windows explorer

import sys
from PyQt6.QtWidgets import QApplication
from ui.desktop import DesktopWindow
from ui.taskbar import Taskbar
from core.config import config as cfg

class NinaweShell:
    def __init__(self):
        self.app = QApplication(sys.argv)
        
        # Links to the windows
        self.desktop = None
        self.taskbar = None

    def start(self):
        print(f"[Log] Starting Ninawe Shell...")
        
        self.desktop = DesktopWindow()
        self.desktop.show()
        
        self.taskbar = Taskbar()
        self.taskbar.show()

        sys.exit(self.app.exec())

if __name__ == "__main__":
    shell = NinaweShell()
    shell.start()