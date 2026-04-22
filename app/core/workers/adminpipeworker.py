import win32pipe
import win32file
import win32security
import pywintypes
import winerror
import json
import ctypes
import sys
import win32gui
import os
import time
from threading import Lock

currentDir = os.path.dirname(os.path.abspath(__file__))
appRootDir = os.path.dirname(os.path.dirname(currentDir))
if appRootDir not in sys.path:
    sys.path.insert(0, appRootDir)

from core.utils import MakeLog
import core.utils.winapi as shellWinapiModule

ALLOWED_MODULES = {
    "win32gui": win32gui,
    "winapi": shellWinapiModule
}

PIPE_NAME = r'\\.\pipe\NinaweAdminPipe'

PIPE_LOCAL_LOCK = Lock()

def CreatePipeServer():
    #
    #   Creates a console ("server") with administrator rights,
    #   into which you can send commands that do not work with normal rights
    #
    securityAttributes = pywintypes.SECURITY_ATTRIBUTES()
    securityDescriptor = win32security.SECURITY_DESCRIPTOR()
    securityDescriptor.SetSecurityDescriptorDacl(1, None, 0)
    securityAttributes.SECURITY_DESCRIPTOR = securityDescriptor

    MakeLog("[Log] [AdminPipe]", "Admin pipe started and waiting for tasks...")

    while True:
        pipe = None
        try:
            pipe = win32pipe.CreateNamedPipe(
                PIPE_NAME,
                win32pipe.PIPE_ACCESS_DUPLEX,
                win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                win32pipe.PIPE_UNLIMITED_INSTANCES,
                65536, 65536, 0,
                securityAttributes
            )

            win32pipe.ConnectNamedPipe(pipe, None)

            result, data = win32file.ReadFile(pipe, 65536)
            if result == 0 and data:
                payload = json.loads(data.decode('utf-8'))
                moduleName = payload.get("module")
                functionName = payload.get("func")
                args = payload.get("args", [])

                if moduleName == "SYSTEM" and functionName == "EXIT":
                    win32pipe.DisconnectNamedPipe(pipe)
                    win32file.CloseHandle(pipe)
                    os._exit(0)

                if moduleName in ALLOWED_MODULES:
                    targetModule = ALLOWED_MODULES[moduleName]
                    if hasattr(targetModule, functionName):
                        targetFunc = getattr(targetModule, functionName)
                        targetFunc(*args)

            win32pipe.DisconnectNamedPipe(pipe)
            win32file.CloseHandle(pipe)

        except Exception as e:
            if pipe:
                try:
                    win32pipe.DisconnectNamedPipe(pipe)
                    win32file.CloseHandle(pipe)
                except:
                    pass


def CallInPipe(moduleName, functionName, *args):
    #
    #   Directly calling available WinAPI functions under Admin via a Named Pipe.
    #   CallInPipe("win32gui", "ShowWindow", arg, another_arg)
    #
    payload = {
        "module": moduleName,
        "func": functionName,
        "args": args
    }
    data = json.dumps(payload).encode('utf-8')

    with PIPE_LOCAL_LOCK:
        while True:
            try:
                handle = win32file.CreateFile(
                    PIPE_NAME,
                    win32file.GENERIC_WRITE,
                    0, None,
                    win32file.OPEN_EXISTING,
                    0, None
                )
                break

            except pywintypes.error as e:
                if e.winerror == winerror.ERROR_PIPE_BUSY:
                    try:
                        win32pipe.WaitNamedPipe(PIPE_NAME, 5000)
                    except pywintypes.error:
                        time.sleep(0.1)
                        continue
                elif e.winerror == winerror.ERROR_FILE_NOT_FOUND:
                    time.sleep(0.01)
                    continue
                else:
                    MakeLog("[Log] [AdminPipe]", f"Critical connection error: {e}")
                    return

        try:
            win32file.WriteFile(handle, data)
        except Exception as e:
            MakeLog("[Log] [AdminPipe]", f"Error while writing task: {e}")
        finally:
            win32file.CloseHandle(handle)


def StartPipe():
    MakeLog("[Log] [AdminPipe]", "Starting admin daemon...")
    iHateGarbageCollectorSoThereIsMutexVariable = ctypes.windll.kernel32.CreateMutexW(None, False, "NinaweAdminMutex")
    if ctypes.windll.kernel32.GetLastError() == 183:  # 183 "already exists"
        MakeLog("[Log] [AdminPipe]", "Daemon is already running.")
        sys.exit()

    if not ctypes.windll.shell32.IsUserAnAdmin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 0)
        sys.exit()

    CreatePipeServer()


if __name__ == "__main__":
    StartPipe()
