from PyQt6.QtCore import QObject, pyqtSignal
from core.utils import MakeLog

class ConfigUpdateChecker(QObject):
    configUpdated = pyqtSignal(str, list)

    def __init__(self, watchSections, config = None):
        super().__init__()
        self.watchSections = watchSections

        if not config:
            from core.config import config
            config.configUpdated.connect(self.OnConfigFileChanged)
        else:
            self.connect()

        MakeLog("[Log] [ConfigUpdateChecker]", f"Connected: {watchSections}")

    def connect(self):
        pass

    def OnConfigFileChanged(self, source = None, changedSections = None):
        if not changedSections:
            return

        needsUpdate = any(section in changedSections for section in self.watchSections)

        if "ALL" in changedSections or source == "init" or needsUpdate:
            self.Updater()
            self.configUpdated.emit(source, self.watchSections)

    def Updater(self):
        pass
