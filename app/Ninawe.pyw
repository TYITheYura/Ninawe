#                  NI   E
#                  N N  E
#                  N  A E i n a w e
#                  N   WE ---------
#               Version: Well Done v2.1
# And remember guys: Ninawe is not a windows explorer

import os
import sys
import ctypes
import time
import traceback
import importlib.util
import subprocess
import mmap

def CheckDependencies():
    requiredPackages = {
        "PyQt6": "PyQt6",
        "win32gui": "pywin32",
        "win32con": "pywin32",
        "win32com": "pywin32",
        "pythoncom": "pywin32",
        "easydict": "easydict",
        "keyboard": "keyboard",
        "OpenGL": "pyopengl",
        "numpy": "numpy",
        "soundcard": "soundcard"
    }

    missing = []
    for module, pipName in requiredPackages.items():
        if importlib.util.find_spec(module) is None:
            if pipName not in missing:
                missing.append(pipName)

    if missing:
        msg = f"The Ninawe shell is missing important libraries:\n\n{', '.join(missing)}\n\nInstall them automatically via pip right now?"
        # 0x34 = MB_YESNO (4) | MB_ICONQUESTION (0x30)
        result = ctypes.windll.user32.MessageBoxW(0, msg, "Ninawe | Installing Components", 0x34)

        if result == 6:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
                os.execv(sys.executable, ['python'] + sys.argv)
            except subprocess.CalledProcessError:
                ctypes.windll.user32.MessageBoxW(
                    0, "Failed to install libraries. Check the internet or install manually.", "Ninawe | Error", 0x10)
                sys.exit(1)
        else:
            sys.exit(1)

CheckDependencies()

system32Path = "C:\\Windows\\System32"
if system32Path.lower() not in os.environ.get("PATH", "").lower():
    os.environ["PATH"] = system32Path + os.pathsep + os.environ.get("PATH", "")

ctypes.windll.kernel32.SetConsoleTitleW("Ninawe Is Not A Windows Explorer - Shell Debugger")

CRASH_TRACKER_FILE = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "userdata", "logs", "ninawecrashtracker.txt"
    )
)
CRASH_LOG_FILE = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "userdata", "logs", "ninawecrashes.log"
    )
)

SHMEM_TAG = "NinaweHandlerMem"
SHMEM_SIZE = 32

if "--worker" not in sys.argv:
    shmem = mmap.mmap(-1, SHMEM_SIZE, tagname = SHMEM_TAG)
    user32 = ctypes.windll.user32

    user32.IsHungAppWindow.argtypes = [ctypes.c_void_p]
    user32.IsHungAppWindow.restype = ctypes.c_bool

    while True:
        shmem.seek(0)
        shmem.write(b'\x00' * SHMEM_SIZE)

        workerProcess = subprocess.Popen([sys.executable, __file__, "--worker"])
        startTime = time.time()

        while workerProcess.poll() is None:
            time.sleep(2)
            try:
                shmem.seek(0)
                rawData = shmem.read(SHMEM_SIZE).decode('utf-8').strip('\x00').strip('.')

                if not rawData:
                    if time.time() - startTime > 60:
                        workerProcess.kill()
                        break
                else:
                    hwnd = int(rawData)

                    isHung = user32.IsHungAppWindow(hwnd)

                    if isHung:
                        with open(CRASH_LOG_FILE, "a", encoding = "utf-8") as f:
                            f.write(f"\n[Log] [{time.ctime()}] | Killed by CrashHandler")

                        workerProcess.kill()
                        break
            except Exception:
                pass

        exitCode = workerProcess.returncode
        if exitCode == 0:
            shmem.close()
            sys.exit(0)

        now = time.time()
        crashes = []
        if os.path.exists(CRASH_TRACKER_FILE):
            try:
                with open(CRASH_TRACKER_FILE, "r") as f:
                    crashes = [float(line.strip()) for line in f if line.strip()]
            except Exception:
                pass

        crashes = [t for t in crashes if now - t < 60]
        crashes.append(now)

        with open(CRASH_TRACKER_FILE, "w") as f:
            for t in crashes:
                f.write(f"{t}\n")

        if len(crashes) >= 3:
            msg = (
                "Ninawe Shell crashed 3 times in one minute.\n"+
                "To avoid system freezes, the standard Explorer will be launched.\n\nError log: ninawecrashes.log"
            )
            ctypes.windll.user32.MessageBoxW(0, msg, "Ninawe | Fatal Error", 0x10)
            os.system("start explorer.exe")
            shmem.close()
            os._exit(1)
        else:
            pass

else:
    def GlobalExceptionHandler(excType, excValue, excTB):
        if issubclass(excType, KeyboardInterrupt):
            sys.__excepthook__(excType, excValue, excTB)
            return
        tracebackStr = "".join(traceback.format_exception(excType, excValue, excTB))
        with open(CRASH_LOG_FILE, "a", encoding = "utf-8") as f:
            f.write(f"\n[Log] [{time.ctime()}] | Crashed:\n{tracebackStr}\n")
        os._exit(1)

    sys.excepthook = GlobalExceptionHandler

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

            hwnd = int(self.desktop.winId())

            # Set desktop as a shell window
            SetShellWindow(hwnd)

            try:
                self.shmem = mmap.mmap(-1, SHMEM_SIZE, tagname=SHMEM_TAG)
                self.shmem.seek(0)
                hwnd_str = str(hwnd)
                self.shmem.write(f"{hwnd_str:.<32}".encode('utf-8'))
            except Exception as e:
                pass

        def Start(self):
            MakeLog("[Log] [Starter] [0xD15EA5E]", "We are moving into space...")
            self.desktop.show()
            self.taskbar.show()
            sys.exit(app.exec())

    if __name__ == "__main__":
        shell = NinaweShell()
        shell.Start()