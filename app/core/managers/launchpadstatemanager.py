import json
import os
from core.utils import MakeLog

class LaunchpadStateManager:
    def __init__(self, filepath):
        self.filepath = filepath
        self.state = {"launchpad": []}
        self.Load()

    def Load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding = "utf-8") as f:
                    self.state = json.load(f)
            except Exception as e:
                MakeLog("[LaunchpadManager]", f"Failed to load JSON: {e}")
        return self.state

    def Save(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok = True)
        try:
            with open(self.filepath, "w", encoding = "utf-8") as f:
                json.dump(self.state, f, indent = 4)
        except Exception as e:
            MakeLog("[LaunchpadManager]", f"Failed to save JSON: {e}")

    def PinApp(self, path):
        if path not in self.state:
            self.state["launchpad"].append(path)
            self.Save()

    def UnpinApp(self, path):
        if path in self.state:
            self.state["launchpad"].remove(path)
            self.Save()

    def UpdatePinnedOrder(self, newOrderList):
        self.state = {"launchpad": newOrderList}
        self.Save()
