import win32com.client
import pythoncom
import win32file
import win32event
import win32con
import urllib.parse
import urllib.request
import win32api
import os
from PyQt6.QtCore import QObject, QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import QApplication
from core.utils import MakeLog

class ExplorerCOMWorker(QObject):
    #
    #   A worker that is subsequently moved to a separate thread.
    #   Its main purpose is to add the path of the open folder to the list and update its contents without stopping the entire shell.
    #
    pathsDiscovered = pyqtSignal(set)

    def SyncFoldersTask(self):
        pythoncom.CoInitializeEx(0)
        try:
            shell = win32com.client.DispatchEx("Shell.Application")
            currentOpenPaths = set()

            windows = shell.Windows()

            for window in windows:
                try:
                    url = window.LocationURL

                    if not url or not url.startswith("file:///"):
                        continue

                    rawPath = urllib.parse.unquote(url[8:])
                    folderPath = urllib.request.url2pathname(rawPath)

                    if folderPath and os.path.isabs(folderPath):
                        currentOpenPaths.add(folderPath)
                except Exception:
                    continue

            self.pathsDiscovered.emit(currentOpenPaths)
        except Exception as e:
            MakeLog("[Log] [COMWorker]", f"Sync error: {e}")
        finally:
            pythoncom.CoUninitialize()

    def RefreshFolderTask(self, changedPath):
        pythoncom.CoInitializeEx(0)
        try:
            shell = win32com.client.DispatchEx("Shell.Application")

            for window in shell.Windows():
                try:
                    url = window.LocationURL
                    if not url or not url.startswith("file:///"):
                        continue

                    rawPath = urllib.parse.unquote(url[8:])
                    folderPath = urllib.request.url2pathname(rawPath)

                    if folderPath and folderPath.lower() == changedPath.lower():
                        window.Refresh()
                except Exception:
                    continue
        except Exception:
            pass
        finally:
            pythoncom.CoUninitialize()

class FolderWatcher(QThread):
    #
    #   The main worker (watcher). It runs in the background, reading changes in open folders and, if any, sending a signal requesting a window refresh.
    #
    folderChanged = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.paths = set()
        self.handles = {}
        self.isRunning = True
        self.pathsChangedFlag = False

        self.updateEvent = win32event.CreateEvent(None, 0, 0, None)

    def UpdatePaths(self, new_paths):
        self.paths = set(new_paths).copy()
        self.pathsChangedFlag = True

        win32event.SetEvent(self.updateEvent)

    def run(self):
        flags = (
            win32con.FILE_NOTIFY_CHANGE_FILE_NAME |
            win32con.FILE_NOTIFY_CHANGE_DIR_NAME |
            win32con.FILE_NOTIFY_CHANGE_LAST_WRITE
        )

        while self.isRunning:
            if self.pathsChangedFlag:
                for h in self.handles.keys():
                    try:
                        win32file.FindCloseChangeNotification(h)
                    except Exception:
                        pass

                self.handles.clear()

                for p in self.paths:
                    try:
                        h = win32file.FindFirstChangeNotification(p, False, flags)
                        if h != win32file.INVALID_HANDLE_VALUE:
                            self.handles[h] = p
                    except Exception:
                        pass
                self.pathsChangedFlag = False

            waitList = [self.updateEvent] + list(self.handles.keys())[:60]

            rc = win32event.WaitForMultipleObjects(waitList, False, win32event.INFINITE)

            if not self.isRunning:
                break

            if rc == win32event.WAIT_OBJECT_0:
                continue

            elif win32event.WAIT_OBJECT_0 < rc < win32event.WAIT_OBJECT_0 + len(waitList):
                index = rc - win32event.WAIT_OBJECT_0
                signaledHandle = waitList[index]
                changedPath = self.handles[signaledHandle]

                self.folderChanged.emit(changedPath)

                try:
                    win32file.FindNextChangeNotification(signaledHandle)
                except Exception:
                    self.pathsChangedFlag = True

        for h in self.handles.keys():
            try:
                win32file.FindCloseChangeNotification(h)
            except Exception:
                pass

        self.handles.clear()
        win32api.CloseHandle(self.updateEvent)

    def stop(self):
        self.isRunning = False
        win32event.SetEvent(self.updateEvent)
        self.wait()

class ExplorerGlobalWatcher(QObject):
    #
    #   Controller object-router between workers. Synchronizes the work of both workers.
    #
    requestSync = pyqtSignal()
    requestRefresh = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.trackedPaths = set()
        self.refreshTimers = {}

        self.nativeWatcher = FolderWatcher()
        self.nativeWatcher.folderChanged.connect(self.OnDirectoryChanged)
        self.nativeWatcher.start()

        self.thread = QThread()
        self.worker = ExplorerCOMWorker()
        self.worker.moveToThread(self.thread)

        self.requestSync.connect(self.worker.SyncFoldersTask)
        self.requestRefresh.connect(self.worker.RefreshFolderTask)
        self.worker.pathsDiscovered.connect(self.UpdateWatcherPaths)

        self.thread.start()

        QApplication.instance().windowManager.windowsStructureChanged.connect(self.requestSync.emit)
        self.requestSync.emit()

    def UpdateWatcherPaths(self, currentOpenPaths):
        added = currentOpenPaths - self.trackedPaths
        removed = self.trackedPaths - currentOpenPaths

        if added or removed:
            for path in added:
                MakeLog("[Log] [ExplorerGlobalWatcher]", f"Spying at {path}")
            for path in removed:
                MakeLog("[Log] [ExplorerGlobalWatcher]", f"Spying on {path} is over")

            self.trackedPaths = currentOpenPaths
            self.nativeWatcher.UpdatePaths(currentOpenPaths)

    def OnDirectoryChanged(self, changedPath):
        if changedPath in self.refreshTimers:
            self.refreshTimers[changedPath].stop()
            self.refreshTimers[changedPath].deleteLater()

        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda p = changedPath: self.TriggerCOMRefresh(p))
        timer.start(25)
        self.refreshTimers[changedPath] = timer

    def TriggerCOMRefresh(self, changedPath):
        if changedPath in self.refreshTimers:
            del self.refreshTimers[changedPath]

        MakeLog("[Log] [ExplorerGlobalWatcher]", f"Changes in {changedPath}")
        self.requestRefresh.emit(changedPath)

    def __del__(self):
        self.nativeWatcher.stop()
        self.thread.quit()
        self.thread.wait()
