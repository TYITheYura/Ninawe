#                  NI   E
#                  N N  E
#                  N  A E i n a w e
#                  N   WE ---------
#                 Version: Rare v0.4
# And remember guys: Ninawe is not a windows explorer

import sys
from PyQt6.QtWidgets import QApplication
from ui.desktop import DesktopWindow
from ui.taskbar import Taskbar
from ui.powermenu import PowerMenu
from core.config import config as cfg

class NinaweShell:
    def __init__(self):
        self.app = QApplication(sys.argv)
        
        # Links to the windows
        self.desktop = None
        self.taskbar = None
        self.powerMenu = None

    def start(self):
        print(
            '''
                      ::::    ::: ::::::::::: ::::    :::     :::     :::       ::: ::::::::::    
                     :+:+:   :+:     :+:     :+:+:   :+:   :+: :+:   :+:       :+: :+:            
                    :+:+:+  +:+     +:+     :+:+:+  +:+  +:+   +:+  +:+       +:+ +:+             
                   +#+ +:+ +#+     +#+     +#+ +:+ +#+ +#++:++#++: +#+  +:+  +#+ +#++:++#         
                  +#+  +#+#+#     +#+     +#+  +#+#+# +#+     +#+ +#+ +#+#+ +#+ +#+               
                 #+#   #+#+#     #+#     #+#   #+#+# #+#     #+#  #+#+# #+#+#  #+#                
                ###    #### ########### ###    #### ###     ###   ###   ###   ##########          

            ''')
        
        # self.desktop = DesktopWindow()
        # self.desktop.show()
        
        # self.taskbar = Taskbar()
        # self.taskbar.show()

        self.powerMenu = PowerMenu()
        self.powerMenu.show()

        sys.exit(self.app.exec())

if __name__ == "__main__":
    shell = NinaweShell()
    shell.start()