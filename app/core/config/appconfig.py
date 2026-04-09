import os
from . import ConfigWrapper, BASE_DIR
from core.utils import MakeLog

# This class covers everything related to the program properties
class AppConfig(ConfigWrapper):
    def __init__(self):
        super().__init__()
        self.configFilePath = os.path.join(BASE_DIR, "userdata", "preferences",  "program", "config.ini")
        self.hashes = {}

    def Load(self):
        if not os.path.exists(self.configFilePath):
            MakeLog(f"[Log] [AppConfig] | Config file on directory {self.configFilePath} not found.")
            return []

        self.parser.read(self.configFilePath)
        changedSections = self.SectionHashCheck(self)
        MakeLog(f"[Log] [AppConfig] | {self.configFilePath} loaded.")
        return changedSections
